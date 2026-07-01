from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_archive_state import MailboxArchiveState
from app.db.models.sync_job import SyncJob
from app.providers.base import ProviderArchiveBatch, ProviderEmailMessage, ProviderError
from app.providers.registry import ProviderRegistryError
from app.services.email_sync_service import (
    _as_uuid,
    _configure_mailbox_provider,
    _decrypt_provider_secret,
    _ensure_utc,
    _get_sync_context,
    acquire_mailbox_sync_lock,
    get_mailbox_provider,
)
from app.services.job_dispatch_service import dispatch_pending_job
from app.utils.redaction import safe_error_message


class EmailArchiveError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(slots=True)
class ArchiveJobResult:
    mailbox_id: UUID | None
    status: str
    synced_count: int
    job_id: UUID
    error_code: str | None = None
    message: str | None = None


@dataclass(slots=True)
class QueuedArchiveJobResult:
    mailbox_id: UUID
    status: str
    job_id: UUID


ACTIVE_ARCHIVE_STATUSES = {"pending_dispatch", "queued", "running"}
DEFAULT_ARCHIVE_BATCH_SIZE = 100
DEFAULT_ARCHIVE_MAX_BATCHES = 100


def enqueue_archive_backfill_job(
    db: Session,
    *,
    user_id: UUID | str,
    mailbox_id: UUID | str,
    dispatch: bool = True,
    batch_size: int = DEFAULT_ARCHIVE_BATCH_SIZE,
    max_batches: int = DEFAULT_ARCHIVE_MAX_BATCHES,
    now: datetime | None = None,
) -> QueuedArchiveJobResult:
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    user, mailbox = _get_sync_context(
        db,
        user_id=_as_uuid(user_id),
        mailbox_id=_as_uuid(mailbox_id),
    )
    state = get_or_create_archive_state(db, mailbox=mailbox, now=resolved_now)
    active_job = find_active_archive_job(db, user_id=user.id, mailbox_id=mailbox.id)
    if active_job is not None:
        return QueuedArchiveJobResult(
            mailbox_id=mailbox.id,
            status=active_job.status,
            job_id=active_job.id,
        )

    job = SyncJob(
        user_id=user.id,
        mailbox_id=mailbox.id,
        job_type="email_archive_backfill",
        trigger_source="manual",
        job_key=f"email_archive_backfill:{mailbox.id}",
        status="pending_dispatch",
        payload_json={
            "sync_mode": "full_history",
            "batch_size": max(1, min(batch_size, 500)),
            "max_batches": max(1, min(max_batches, 500)),
            "archive_state_id": str(state.id),
        },
        created_at=resolved_now,
    )
    db.add(job)
    db.flush()
    if dispatch:
        dispatch_result = dispatch_pending_job(
            db,
            job_id=job.id,
            dispatcher=dispatch_archive_backfill_job,
            now=resolved_now,
        )
        return QueuedArchiveJobResult(
            mailbox_id=mailbox.id,
            status=dispatch_result.status,
            job_id=job.id,
        )
    return QueuedArchiveJobResult(
        mailbox_id=mailbox.id,
        status="pending_dispatch",
        job_id=job.id,
    )


def execute_queued_archive_job(
    db: Session,
    *,
    job_id: UUID | str,
    provider: object | None = None,
    now: datetime | None = None,
) -> ArchiveJobResult:
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    resolved_job_id = _as_uuid(job_id)
    job = db.get(SyncJob, resolved_job_id)
    if job is None:
        return ignored_archive_task_result(
            job_id=resolved_job_id,
            mailbox_id=None,
            error_code="orphaned_archive_task",
            message="Archive task ignored because the database job no longer exists.",
        )
    if job.status != "queued":
        return ignored_archive_task_result(
            job_id=job.id,
            mailbox_id=job.mailbox_id,
            error_code="stale_or_completed_archive_task",
            message="Archive task ignored because the database job is no longer dispatchable.",
        )
    if job.mailbox_id is None:
        raise EmailArchiveError("INVALID_REQUEST", "Archive job is missing mailbox.")
    user, mailbox = _get_sync_context(db, user_id=job.user_id, mailbox_id=job.mailbox_id)
    archive_lock = acquire_archive_lock(mailbox_id=mailbox.id, job_id=job.id)
    if archive_lock is None:
        _fail_job(
            db,
            job=job,
            code="worker_lock_conflict",
            message="Another sync is already running for this mailbox.",
            now=resolved_now,
        )
        raise EmailArchiveError(
            "worker_lock_conflict",
            "Another sync is already running for this mailbox.",
            409,
        )
    job.status = "running"
    job.started_at = resolved_now
    state = get_or_create_archive_state(db, mailbox=mailbox, now=resolved_now)
    state.status = "running"
    state.started_at = state.started_at or resolved_now
    state.completed_at = None
    state.last_error_code = None
    state.last_error_message = None
    state.updated_at = resolved_now
    db.flush()
    try:
        return _execute_archive_backfill(
            db,
            mailbox=mailbox,
            job=job,
            state=state,
            provider=provider,
            now=resolved_now,
        )
    finally:
        try:
            archive_lock.release()
        except RedisError:
            pass


def get_or_create_archive_state(
    db: Session, *, mailbox: Mailbox, now: datetime | None = None
) -> MailboxArchiveState:
    state = db.scalar(
        select(MailboxArchiveState).where(MailboxArchiveState.mailbox_id == mailbox.id)
    )
    if state is not None:
        return state
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    state = MailboxArchiveState(
        mailbox_id=mailbox.id,
        provider=mailbox.provider,
        status="not_started",
        cursor={},
        total_synced_count=0,
        batch_count=0,
        created_at=resolved_now,
        updated_at=resolved_now,
    )
    db.add(state)
    db.flush()
    return state


def find_active_archive_job(
    db: Session, *, user_id: UUID, mailbox_id: UUID
) -> SyncJob | None:
    return db.scalar(
        select(SyncJob)
        .where(
            SyncJob.user_id == user_id,
            SyncJob.mailbox_id == mailbox_id,
            SyncJob.job_type == "email_archive_backfill",
            SyncJob.status.in_(ACTIVE_ARCHIVE_STATUSES),
        )
        .order_by(SyncJob.created_at.asc(), SyncJob.id.asc())
        .limit(1)
    )


def dispatch_archive_backfill_job(job_id: UUID) -> str:
    from app.jobs.celery_app import celery_app

    result = celery_app.send_task("app.jobs.email_archive_backfill", args=[str(job_id)])
    return str(result.id)


def acquire_archive_lock(*, mailbox_id: UUID, job_id: UUID):
    return acquire_mailbox_sync_lock(mailbox_id=mailbox_id, job_id=job_id)


def ignored_archive_task_result(
    *,
    job_id: UUID,
    mailbox_id: UUID | None,
    error_code: str,
    message: str,
) -> ArchiveJobResult:
    return ArchiveJobResult(
        mailbox_id=mailbox_id,
        status="ignored",
        synced_count=0,
        job_id=job_id,
        error_code=error_code,
        message=message,
    )


def _execute_archive_backfill(
    db: Session,
    *,
    mailbox: Mailbox,
    job: SyncJob,
    state: MailboxArchiveState,
    provider: object | None,
    now: datetime,
) -> ArchiveJobResult:
    try:
        mailbox_provider = provider or get_mailbox_provider(mailbox.provider)
        mailbox_provider = _configure_mailbox_provider(
            db,
            mailbox=mailbox,
            provider=mailbox_provider,
        )
        provider_secret = _decrypt_provider_secret(db, mailbox=mailbox)
        access_token = mailbox_provider.refresh_access_token(provider_secret)
        batch_size = int((job.payload_json or {}).get("batch_size") or DEFAULT_ARCHIVE_BATCH_SIZE)
        max_batches = int((job.payload_json or {}).get("max_batches") or DEFAULT_ARCHIVE_MAX_BATCHES)
        synced_count = 0
        is_complete = False
        for _ in range(max(1, max_batches)):
            state.last_batch_started_at = now
            batch = mailbox_provider.list_archive_batch(
                access_token,
                cursor=state.cursor or None,
                batch_size=batch_size,
            )
            synced_count += upsert_archive_messages(
                db,
                mailbox=mailbox,
                messages=batch.messages,
                synced_at=now,
            )
            _update_state_after_batch(state=state, batch=batch, now=now)
            db.flush()
            is_complete = batch.is_complete
            if is_complete:
                break
    except ProviderError as exc:
        if exc.code == "MAILBOX_REAUTH_REQUIRED":
            mailbox.status = "reauth_required"
        _fail_archive(db, job=job, state=state, code=exc.code, message=exc.message, now=now)
        raise EmailArchiveError(exc.code, exc.message, exc.status_code) from exc
    except ProviderRegistryError as exc:
        _fail_archive(db, job=job, state=state, code=exc.code, message=exc.message, now=now)
        raise EmailArchiveError(exc.code, exc.message, exc.status_code) from exc
    except EmailArchiveError as exc:
        _fail_archive(db, job=job, state=state, code=exc.code, message=exc.message, now=now)
        raise
    except Exception as exc:
        _fail_archive(
            db,
            job=job,
            state=state,
            code="PROVIDER_ARCHIVE_FAILED",
            message="Email archive backfill failed.",
            now=now,
        )
        raise EmailArchiveError(
            "PROVIDER_ARCHIVE_FAILED",
            "Email archive backfill failed.",
            502,
        ) from exc

    job.status = "succeeded"
    job.finished_at = now
    job.payload_json = {
        **(job.payload_json or {}),
        "synced_count": synced_count,
        "archive_status": "complete" if is_complete else "partial",
    }
    state.status = "complete" if is_complete else "partial"
    state.completed_at = now if is_complete else None
    state.updated_at = now
    db.flush()
    return ArchiveJobResult(
        mailbox_id=mailbox.id,
        status="completed" if is_complete else "partial",
        synced_count=synced_count,
        job_id=job.id,
    )


def upsert_archive_messages(
    db: Session,
    *,
    mailbox: Mailbox,
    messages: list[ProviderEmailMessage],
    synced_at: datetime,
) -> int:
    synced_count = 0
    for message in messages:
        if not message.external_id:
            continue
        email = db.scalar(
            select(Email).where(
                Email.mailbox_id == mailbox.id,
                Email.external_id == message.external_id,
            )
        )
        if email is None:
            email = Email(
                user_id=mailbox.user_id,
                mailbox_id=mailbox.id,
                provider=mailbox.provider,
                external_id=message.external_id,
                body_text=None,
                body_text_truncated=False,
                body_html=None,
                body_cache_status="not_cached",
                body_cached_at=None,
                body_cache_source=None,
                body_cache_error=None,
                first_synced_at=synced_at,
                created_at=synced_at,
            )
            db.add(email)
        email.external_thread_id = message.external_thread_id
        email.internet_message_id = message.internet_message_id
        email.subject = message.subject
        email.from_name = message.from_name
        email.from_address = message.from_address
        email.to_addresses = message.to_addresses
        email.cc_addresses = message.cc_addresses
        email.snippet = message.snippet
        email.received_at = message.received_at
        email.sent_at = message.received_at
        email.is_read = message.is_read
        email.is_starred = "STARRED" in (message.provider_labels or [])
        email.has_attachments = False
        email.provider_labels = message.provider_labels
        email.provider_metadata_json = {"raw_payload_hash": message.raw_payload_hash}
        email.gmail_history_id = message.gmail_history_id
        email.last_synced_at = synced_at
        email.updated_at = synced_at
        synced_count += 1
    db.flush()
    return synced_count


def _update_state_after_batch(
    *, state: MailboxArchiveState, batch: ProviderArchiveBatch, now: datetime
) -> None:
    state.batch_count += 1
    state.total_synced_count += len(batch.messages)
    state.cursor = batch.cursor or {}
    state.last_batch_completed_at = now
    state.updated_at = now
    for message in batch.messages:
        if state.newest_synced_at is None or message.received_at > state.newest_synced_at:
            state.newest_synced_at = message.received_at
        if state.oldest_synced_at is None or message.received_at < state.oldest_synced_at:
            state.oldest_synced_at = message.received_at


def _fail_archive(
    db: Session,
    *,
    job: SyncJob,
    state: MailboxArchiveState,
    code: str,
    message: str,
    now: datetime,
) -> None:
    _fail_job(db, job=job, code=code, message=message, now=now)
    state.status = "failed"
    state.last_error_code = code
    state.last_error_message = safe_error_message(message, max_length=1000) or ""
    state.updated_at = now
    db.flush()


def _fail_job(
    db: Session,
    *,
    job: SyncJob,
    code: str,
    message: str,
    now: datetime,
) -> None:
    job.status = "failed"
    job.error_code = code
    job.error_message = safe_error_message(message, max_length=1000) or ""
    job.finished_at = now
    db.flush()
