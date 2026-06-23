from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.models.sync_job import SyncJob
from app.db.models.user import User
from app.providers.base import ProviderEmailMessage, ProviderError
from app.providers.gmail import GmailProvider
from app.providers.registry import (
    ProviderRegistryError,
    get_mailbox_provider as registry_get_mailbox_provider,
)
from app.services.credential_encryption_service import CredentialEncryptionService
from app.utils.redaction import safe_error_message


class EmailSyncError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(slots=True)
class SyncTodayResult:
    mailbox_id: UUID
    status: str
    synced_count: int
    job_id: UUID


@dataclass(slots=True)
class QueuedSyncJobResult:
    mailbox_id: UUID
    status: str
    job_id: UUID


ACTIVE_SYNC_STATUSES = {"queued", "running"}
MAILBOX_SYNC_LOCK_TTL_SECONDS = 20 * 60


@dataclass(slots=True)
class MailboxSyncLock:
    client: Redis
    key: str
    value: str

    def release(self) -> None:
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        end
        return 0
        """
        self.client.eval(script, 1, self.key, self.value)


def sync_today_emails(
    db: Session,
    *,
    user_id: UUID | str,
    mailbox_id: UUID | str,
    provider: object | None = None,
    now: datetime | None = None,
) -> SyncTodayResult:
    resolved_user_id = _as_uuid(user_id)
    resolved_mailbox_id = _as_uuid(mailbox_id)
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    user, mailbox = _get_sync_context(
        db,
        user_id=resolved_user_id,
        mailbox_id=resolved_mailbox_id,
    )
    active_job = find_active_email_sync_job(
        db,
        user_id=user.id,
        mailbox_id=mailbox.id,
    )
    if active_job is not None:
        return SyncTodayResult(
            mailbox_id=mailbox.id,
            status=_public_job_status(active_job.status),
            synced_count=0,
            job_id=active_job.id,
        )
    job = SyncJob(
        user_id=user.id,
        mailbox_id=mailbox.id,
        job_type="sync_today_emails",
        trigger_source="manual",
        job_key=f"sync_today_emails:{mailbox.id}:{_target_date(user, resolved_now)}",
        target_date=_target_date(user, resolved_now),
        status="running",
        started_at=resolved_now,
        payload_json={},
    )
    db.add(job)
    mailbox.last_sync_at = resolved_now
    db.flush()
    return _execute_sync_today(
        db,
        user=user,
        mailbox=mailbox,
        job=job,
        provider=provider,
        now=resolved_now,
    )


def enqueue_sync_today_job(
    db: Session,
    *,
    user_id: UUID | str,
    mailbox_id: UUID | str,
    dispatch: bool = True,
    now: datetime | None = None,
    trigger_source: str = "manual",
    job_key: str | None = None,
) -> QueuedSyncJobResult:
    resolved_user_id = _as_uuid(user_id)
    resolved_mailbox_id = _as_uuid(mailbox_id)
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    user, mailbox = _get_sync_context(
        db,
        user_id=resolved_user_id,
        mailbox_id=resolved_mailbox_id,
    )
    active_job = find_active_email_sync_job(
        db,
        user_id=user.id,
        mailbox_id=mailbox.id,
    )
    if active_job is not None:
        return QueuedSyncJobResult(
            mailbox_id=mailbox.id,
            status=active_job.status,
            job_id=active_job.id,
        )
    job = SyncJob(
        user_id=user.id,
        mailbox_id=mailbox.id,
        job_type="sync_today_emails",
        trigger_source=trigger_source,
        job_key=job_key,
        target_date=_target_date(user, resolved_now),
        status="queued",
        payload_json={},
        created_at=resolved_now,
    )
    db.add(job)
    db.flush()
    if dispatch:
        job.celery_task_id = dispatch_email_sync_job(job.id)
        db.flush()
    return QueuedSyncJobResult(mailbox_id=mailbox.id, status="queued", job_id=job.id)


def execute_queued_sync_job(
    db: Session,
    *,
    job_id: UUID | str,
    provider: object | None = None,
    now: datetime | None = None,
) -> SyncTodayResult:
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    job = db.get(SyncJob, _as_uuid(job_id))
    if job is None:
        raise EmailSyncError("INVALID_REQUEST", "Sync job not found.", 404)
    if job.status != "queued":
        raise EmailSyncError("INVALID_REQUEST", "Sync job is not queued.")
    if job.mailbox_id is None:
        raise EmailSyncError("INVALID_REQUEST", "Sync job is missing mailbox.")
    user, mailbox = _get_sync_context(
        db,
        user_id=job.user_id,
        mailbox_id=job.mailbox_id,
    )
    sync_lock = acquire_mailbox_sync_lock(
        mailbox_id=mailbox.id,
        job_id=job.id,
    )
    if sync_lock is None:
        _fail_job(
            db,
            job=job,
            code="worker_lock_conflict",
            message="Another sync is already running for this mailbox.",
            now=resolved_now,
        )
        raise EmailSyncError(
            "worker_lock_conflict",
            "Another sync is already running for this mailbox.",
            409,
        )
    job.status = "running"
    job.started_at = resolved_now
    mailbox.last_sync_at = resolved_now
    db.flush()
    try:
        return _execute_sync_today(
            db,
            user=user,
            mailbox=mailbox,
            job=job,
            provider=provider,
            now=resolved_now,
        )
    finally:
        try:
            sync_lock.release()
        except RedisError:
            pass


def dispatch_email_sync_job(job_id: UUID) -> str:
    from app.jobs.celery_app import celery_app

    result = celery_app.send_task("app.jobs.email_sync", args=[str(job_id)])
    return str(result.id)


def get_mailbox_provider(provider_key: str) -> object:
    normalized = provider_key.strip().lower()
    if normalized == "gmail":
        return GmailProvider()
    return registry_get_mailbox_provider(normalized)


def find_active_email_sync_job(
    db: Session,
    *,
    user_id: UUID,
    mailbox_id: UUID,
) -> SyncJob | None:
    return db.scalar(
        select(SyncJob)
        .where(
            SyncJob.user_id == user_id,
            SyncJob.mailbox_id == mailbox_id,
            SyncJob.job_type == "sync_today_emails",
            SyncJob.status.in_(ACTIVE_SYNC_STATUSES),
        )
        .order_by(SyncJob.created_at.asc(), SyncJob.id.asc())
        .limit(1)
    )


def acquire_mailbox_sync_lock(
    *,
    mailbox_id: UUID,
    job_id: UUID,
    ttl_seconds: int = MAILBOX_SYNC_LOCK_TTL_SECONDS,
) -> MailboxSyncLock | None:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    key = f"sync:mailbox:{mailbox_id}"
    value = str(job_id)
    try:
        acquired = client.set(key, value, nx=True, ex=ttl_seconds)
    except RedisError:
        return None
    if not acquired:
        return None
    return MailboxSyncLock(client=client, key=key, value=value)


def _execute_sync_today(
    db: Session,
    *,
    user: User,
    mailbox: Mailbox,
    job: SyncJob,
    provider: object | None,
    now: datetime,
) -> SyncTodayResult:
    window_start, window_end = calculate_today_window(user.timezone, now=now)

    try:
        refresh_token = _decrypt_refresh_token(db, mailbox_id=mailbox.id)
        mailbox_provider = provider or get_mailbox_provider(mailbox.provider)
        access_token = mailbox_provider.refresh_access_token(refresh_token)
        messages = mailbox_provider.list_messages_for_window(
            access_token,
            window_start=window_start,
            window_end=window_end,
        )
        synced_count = upsert_email_messages(
            db,
            mailbox=mailbox,
            messages=messages,
            window_start=window_start,
            window_end=window_end,
            synced_at=now,
        )
    except ProviderError as exc:
        if exc.code == "MAILBOX_REAUTH_REQUIRED":
            mailbox.status = "reauth_required"
        _fail_job(db, job=job, code=exc.code, message=exc.message, now=now)
        raise EmailSyncError(exc.code, exc.message, exc.status_code) from exc
    except EmailSyncError as exc:
        _fail_job(db, job=job, code=exc.code, message=exc.message, now=now)
        raise
    except ProviderRegistryError as exc:
        _fail_job(db, job=job, code=exc.code, message=exc.message, now=now)
        raise EmailSyncError(exc.code, exc.message, exc.status_code) from exc
    except Exception as exc:
        _fail_job(
            db,
            job=job,
            code="PROVIDER_SYNC_FAILED",
            message="Email sync failed.",
            now=now,
        )
        raise EmailSyncError("PROVIDER_SYNC_FAILED", "Email sync failed.", 502) from exc

    mailbox.last_successful_sync_at = now
    job.status = "succeeded"
    job.finished_at = now
    job.payload_json = {"synced_count": synced_count}
    db.flush()
    return SyncTodayResult(
        mailbox_id=mailbox.id,
        status="completed",
        synced_count=synced_count,
        job_id=job.id,
    )


def calculate_today_window(timezone: str, *, now: datetime) -> tuple[datetime, datetime]:
    user_zone = _user_zone(timezone)
    resolved_now = _ensure_utc(now)
    local_now = resolved_now.astimezone(user_zone)
    local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_start.astimezone(UTC), resolved_now


def upsert_email_messages(
    db: Session,
    *,
    mailbox: Mailbox,
    messages: list[ProviderEmailMessage],
    window_start: datetime,
    window_end: datetime,
    synced_at: datetime,
) -> int:
    synced_count = 0
    for message in messages:
        if not message.external_id:
            continue
        if not window_start <= message.received_at <= window_end:
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
        email.body_text = message.body_text
        email.body_text_truncated = message.body_text_truncated
        email.received_at = message.received_at
        email.is_read = message.is_read
        email.provider_labels = message.provider_labels
        email.gmail_history_id = message.gmail_history_id
        email.last_synced_at = synced_at
        email.updated_at = synced_at
        synced_count += 1

    db.flush()
    return synced_count


def _public_job_status(status: str) -> str:
    if status == "succeeded":
        return "completed"
    return status


def _decrypt_refresh_token(db: Session, *, mailbox_id: UUID) -> str:
    credential = db.get(MailboxCredential, mailbox_id)
    if credential is None or not credential.refresh_token_encrypted:
        raise EmailSyncError(
            "MAILBOX_REAUTH_REQUIRED",
            "Gmail authorization is required.",
            401,
        )

    try:
        return CredentialEncryptionService().decrypt(credential.refresh_token_encrypted)
    except Exception as exc:
        raise EmailSyncError(
            "MAILBOX_REAUTH_REQUIRED",
            "Gmail authorization is required.",
            401,
        ) from exc


def _get_sync_context(
    db: Session,
    *,
    user_id: UUID,
    mailbox_id: UUID,
) -> tuple[User, Mailbox]:
    user = db.get(User, user_id)
    mailbox = db.scalar(
        select(Mailbox).where(
            Mailbox.id == mailbox_id,
            Mailbox.user_id == user_id,
        )
    )
    if user is None or mailbox is None:
        raise EmailSyncError("INVALID_REQUEST", "Mailbox not found.", 404)
    try:
        get_mailbox_provider(mailbox.provider)
    except ProviderRegistryError as exc:
        raise EmailSyncError(exc.code, exc.message, exc.status_code) from exc
    if mailbox.status != "active":
        raise EmailSyncError(
            "MAILBOX_REAUTH_REQUIRED",
            "Mailbox is not connected.",
            401,
        )
    return user, mailbox


def _target_date(user: User, now: datetime) -> object:
    window_start, _ = calculate_today_window(user.timezone, now=now)
    return window_start.astimezone(_user_zone(user.timezone)).date()


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


def _as_uuid(value: UUID | str) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _user_zone(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo(get_settings().default_timezone)
