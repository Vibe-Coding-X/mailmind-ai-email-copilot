from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.ai.base import LLMProvider, LLMProviderError
from app.ai.llm_client import get_llm_provider
from app.ai.parsers.digest_parser import DigestParseError, parse_digest_output
from app.ai.prompts.digest import build_digest_prompt
from app.core.config import get_settings
from app.db.models.ai_run import AIRun
from app.db.models.daily_digest import DailyDigest
from app.db.models.digest_item import DigestItem
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.sync_job import SyncJob
from app.db.models.user import User
from app.services.ai_run_service import (
    create_ai_run,
    mark_ai_run_failed,
    mark_ai_run_succeeded,
)
from app.services.job_dispatch_service import dispatch_pending_job
from app.utils.redaction import safe_error_message


class DigestServiceError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        *,
        retryable: bool = False,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        super().__init__(message)


@dataclass(slots=True)
class DigestWindow:
    start: datetime
    end: datetime
    digest_date: object


@dataclass(slots=True)
class DigestScope:
    scope_type: str
    mailbox_id: UUID | None
    mailboxes: list[Mailbox]


@dataclass(slots=True)
class QueuedDigestJobResult:
    job_id: UUID
    status: str


@dataclass(slots=True)
class DigestExecutionResult:
    job_id: UUID
    digest_id: UUID | None
    mailbox_id: UUID | None
    status: str
    mail_count: int
    error_code: str | None = None
    message: str | None = None


ACTIVE_DIGEST_JOB_STATUSES = {"pending_dispatch", "queued", "running"}


def get_today_digest(
    db: Session,
    *,
    user_id: UUID | str,
    scope_type: str | None = None,
    mailbox_id: UUID | str | None = None,
    now: datetime | None = None,
) -> DailyDigest:
    user = _get_user(db, user_id)
    scope = _resolve_digest_scope(
        db,
        user_id=user.id,
        scope_type=scope_type,
        mailbox_id=mailbox_id,
    )
    window = calculate_digest_window(user.timezone, now=now or datetime.now(UTC))
    query = select(DailyDigest).where(
        DailyDigest.user_id == user.id,
        DailyDigest.scope_type == scope.scope_type,
        DailyDigest.digest_date == window.digest_date,
        DailyDigest.is_current.is_(True),
    )
    if scope.mailbox_id is None:
        query = query.where(DailyDigest.mailbox_id.is_(None))
    else:
        query = query.where(DailyDigest.mailbox_id == scope.mailbox_id)
    digest = db.scalar(query)
    if digest is None:
        raise DigestServiceError(
            "DIGEST_NOT_READY",
            "Today's digest has not been generated.",
            404,
            retryable=True,
        )
    return digest


def get_digest(
    db: Session,
    *,
    user_id: UUID | str,
    digest_id: UUID | str,
) -> DailyDigest:
    digest = db.scalar(
        select(DailyDigest).where(
            DailyDigest.id == _as_uuid(digest_id),
            DailyDigest.user_id == _as_uuid(user_id),
        )
    )
    if digest is None:
        raise DigestServiceError(
            "DIGEST_NOT_READY",
            "Digest not found.",
            404,
            retryable=True,
        )
    return digest


def generate_today_digest(
    db: Session,
    *,
    user_id: UUID | str,
    scope_type: str | None = None,
    mailbox_id: UUID | str | None = None,
    llm_provider: LLMProvider | None = None,
    now: datetime | None = None,
) -> DailyDigest:
    return _generate_digest(
        db,
        user_id=user_id,
        scope_type=scope_type,
        mailbox_id=mailbox_id,
        trigger_source="manual",
        job_type="generate_daily_digest",
        llm_provider=llm_provider,
        now=now,
    )


def refresh_today_digest(
    db: Session,
    *,
    user_id: UUID | str,
    scope_type: str | None = None,
    mailbox_id: UUID | str | None = None,
    llm_provider: LLMProvider | None = None,
    now: datetime | None = None,
) -> DailyDigest:
    return _generate_digest(
        db,
        user_id=user_id,
        scope_type=scope_type,
        mailbox_id=mailbox_id,
        trigger_source="refresh",
        job_type="refresh_daily_digest",
        llm_provider=llm_provider,
        now=now,
    )


def enqueue_generate_today_digest_job(
    db: Session,
    *,
    user_id: UUID | str,
    scope_type: str | None = None,
    mailbox_id: UUID | str | None = None,
    dispatch: bool = True,
    now: datetime | None = None,
) -> QueuedDigestJobResult:
    return _enqueue_digest_job(
        db,
        user_id=user_id,
        scope_type=scope_type,
        mailbox_id=mailbox_id,
        job_type="generate_daily_digest",
        trigger_source="manual",
        dispatch=dispatch,
        now=now,
    )


def enqueue_refresh_today_digest_job(
    db: Session,
    *,
    user_id: UUID | str,
    scope_type: str | None = None,
    mailbox_id: UUID | str | None = None,
    dispatch: bool = True,
    now: datetime | None = None,
) -> QueuedDigestJobResult:
    return _enqueue_digest_job(
        db,
        user_id=user_id,
        scope_type=scope_type,
        mailbox_id=mailbox_id,
        job_type="refresh_daily_digest",
        trigger_source="refresh",
        dispatch=dispatch,
        now=now,
    )


def execute_queued_digest_job(
    db: Session,
    *,
    job_id: UUID | str,
    llm_provider: LLMProvider | None = None,
    now: datetime | None = None,
) -> DigestExecutionResult:
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    resolved_job_id = _as_uuid(job_id)
    job = db.get(SyncJob, resolved_job_id)
    if job is None:
        return DigestExecutionResult(
            job_id=resolved_job_id,
            digest_id=None,
            mailbox_id=None,
            status="ignored",
            mail_count=0,
            error_code="orphaned_digest_task",
            message="Digest task ignored because the database job no longer exists.",
        )
    if job.status != "queued":
        return DigestExecutionResult(
            job_id=job.id,
            digest_id=job.digest_id,
            mailbox_id=job.mailbox_id,
            status="ignored",
            mail_count=0,
            error_code="stale_or_completed_digest_task",
            message="Digest task ignored because the database job is no longer dispatchable.",
        )
    scope_type = _job_scope_type(job)

    job.status = "running"
    job.started_at = resolved_now
    db.flush()
    try:
        if job.job_type not in {"generate_daily_digest", "refresh_daily_digest"}:
            raise DigestServiceError("INVALID_REQUEST", "Unsupported digest job type.")
        digest = _generate_digest(
            db,
            user_id=job.user_id,
            scope_type=scope_type,
            mailbox_id=job.mailbox_id,
            trigger_source=job.trigger_source,
            job_type=job.job_type,
            llm_provider=llm_provider,
            now=resolved_now,
            existing_job=job,
        )
    except DigestServiceError as exc:
        job.status = "failed"
        job.error_code = exc.code
        job.error_message = safe_error_message(exc.message, max_length=1000) or ""
        job.finished_at = resolved_now
        db.flush()
        raise

    item_count = int(
        db.scalar(select(func.count(DigestItem.id)).where(DigestItem.digest_id == digest.id))
        or 0
    )
    return DigestExecutionResult(
        job_id=job.id,
        digest_id=digest.id,
        mailbox_id=job.mailbox_id,
        status="completed",
        mail_count=digest.mail_count,
    )


def dispatch_digest_job(job_id: UUID) -> str:
    from app.jobs.celery_app import celery_app

    result = celery_app.send_task("app.jobs.digest", args=[str(job_id)])
    return str(result.id)


def calculate_digest_window(timezone: str, *, now: datetime) -> DigestWindow:
    resolved_now = _ensure_utc(now)
    user_zone = _user_zone(timezone)
    local_now = resolved_now.astimezone(user_zone)
    local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return DigestWindow(
        start=local_start.astimezone(UTC),
        end=resolved_now,
        digest_date=local_now.date(),
    )


def _enqueue_digest_job(
    db: Session,
    *,
    user_id: UUID | str,
    scope_type: str | None,
    mailbox_id: UUID | str | None,
    job_type: str,
    trigger_source: str,
    dispatch: bool,
    now: datetime | None,
) -> QueuedDigestJobResult:
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    user = _get_user(db, user_id)
    scope = _resolve_digest_scope(
        db,
        user_id=user.id,
        scope_type=scope_type,
        mailbox_id=mailbox_id,
    )
    window = calculate_digest_window(user.timezone, now=resolved_now)
    active_job = _find_active_digest_job(
        db,
        user_id=user.id,
        mailbox_id=scope.mailbox_id,
        job_type=job_type,
        target_date=window.digest_date,
    )
    if active_job is not None:
        return QueuedDigestJobResult(job_id=active_job.id, status=active_job.status)
    job = SyncJob(
        user_id=user.id,
        mailbox_id=scope.mailbox_id,
        job_type=job_type,
        trigger_source=trigger_source,
        job_key=_digest_job_key(
            job_type=job_type,
            scope_type=scope.scope_type,
            mailbox_id=scope.mailbox_id,
            target_date=window.digest_date,
        ),
        target_date=window.digest_date,
        status="pending_dispatch",
        payload_json={"scope_type": scope.scope_type},
        created_at=resolved_now,
    )
    db.add(job)
    db.flush()
    if dispatch:
        dispatch_result = dispatch_pending_job(
            db,
            job_id=job.id,
            dispatcher=dispatch_digest_job,
            now=resolved_now,
        )
        return QueuedDigestJobResult(job_id=job.id, status=dispatch_result.status)
    return QueuedDigestJobResult(job_id=job.id, status="pending_dispatch")


def _find_active_digest_job(
    db: Session,
    *,
    user_id: UUID,
    mailbox_id: UUID | None,
    job_type: str,
    target_date: object,
) -> SyncJob | None:
    query = (
        select(SyncJob)
        .where(
            SyncJob.user_id == user_id,
            SyncJob.job_type == job_type,
            SyncJob.target_date == target_date,
            SyncJob.status.in_(ACTIVE_DIGEST_JOB_STATUSES),
        )
        .order_by(SyncJob.created_at.asc(), SyncJob.id.asc())
        .limit(1)
    )
    if mailbox_id is None:
        query = query.where(SyncJob.mailbox_id.is_(None))
    else:
        query = query.where(SyncJob.mailbox_id == mailbox_id)
    return db.scalar(query)


def _generate_digest(
    db: Session,
    *,
    user_id: UUID | str,
    scope_type: str | None,
    mailbox_id: UUID | str | None,
    trigger_source: str,
    job_type: str,
    llm_provider: LLMProvider | None,
    now: datetime | None,
    existing_job: SyncJob | None = None,
) -> DailyDigest:
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    user = _get_user(db, user_id)
    scope = _resolve_digest_scope(
        db,
        user_id=user.id,
        scope_type=scope_type,
        mailbox_id=mailbox_id,
    )
    window = calculate_digest_window(user.timezone, now=resolved_now)
    version = _next_digest_version(
        db,
        user_id=user.id,
        scope_type=scope.scope_type,
        mailbox_id=scope.mailbox_id,
        digest_date=window.digest_date,
    )

    digest = DailyDigest(
        user_id=user.id,
        scope_type=scope.scope_type,
        mailbox_id=scope.mailbox_id,
        digest_date=window.digest_date,
        version=version,
        is_current=False,
        status="generating",
        trigger_source=trigger_source,
        generation_started_at=resolved_now,
        coverage_start=window.start,
        coverage_end=window.end,
        mail_count=0,
        overview_json={},
        created_at=resolved_now,
        updated_at=resolved_now,
    )
    db.add(digest)
    db.flush()

    job = existing_job or _create_digest_job(
        db,
        user_id=user.id,
        scope_type=scope.scope_type,
        mailbox_id=scope.mailbox_id,
        digest_id=digest.id,
        job_type=job_type,
        trigger_source=trigger_source,
        target_date=window.digest_date,
        now=resolved_now,
    )
    if existing_job is not None:
        job.digest_id = digest.id
        job.mailbox_id = scope.mailbox_id
        job.payload_json = {**(job.payload_json or {}), "scope_type": scope.scope_type}
    ai_run: AIRun | None = None

    try:
        emails = _list_digest_emails(
            db,
            user_id=user.id,
            mailbox_ids=[mailbox.id for mailbox in scope.mailboxes],
            window_start=window.start,
            window_end=window.end,
        )
        prompt = build_digest_prompt(
            emails,
            coverage_start=window.start,
            coverage_end=window.end,
            scope_type=scope.scope_type,
            mailboxes=scope.mailboxes,
        )
        provider = llm_provider or get_llm_provider()
        ai_run = create_ai_run(
            db,
            user_id=user.id,
            mailbox_id=scope.mailbox_id,
            digest_id=digest.id,
            trigger_source=trigger_source,
            provider_id=getattr(provider, "provider_id", None),
            provider_type=getattr(provider, "provider_type", None),
            model_provider=provider.provider_name,
            model_name=provider.model_name,
            prompt_version=prompt.prompt_version,
            output_schema_version=prompt.output_schema_version,
            input_text=prompt.text,
            input_summary=prompt.input_summary,
            now=resolved_now,
        )

        started = time.perf_counter()
        response = provider.generate_digest(prompt.text)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        ai_run.provider_id = response.provider_id or ai_run.provider_id
        ai_run.provider_type = response.provider_type or ai_run.provider_type
        ai_run.model_provider = response.model_provider
        ai_run.model_name = response.model_name
        parsed = parse_digest_output(
            response.text,
            {email.external_id: email for email in emails},
            default_mailbox_id=scope.mailbox_id,
            allowed_mailboxes={mailbox.id: mailbox for mailbox in scope.mailboxes},
        )
        _create_digest_items(
            db,
            digest=digest,
            parsed_items=parsed.items,
            now=resolved_now,
        )
        digest.mail_count = parsed.overview["mail_count"]
        digest.overview_json = parsed.overview
        digest.generated_at = resolved_now
        digest.status = "fresh"
        digest.updated_at = resolved_now
        _switch_current_digest(
            db,
            digest=digest,
            user_id=user.id,
            scope_type=scope.scope_type,
            mailbox_id=scope.mailbox_id,
            digest_date=window.digest_date,
            now=resolved_now,
        )
        mark_ai_run_succeeded(
            ai_run,
            output_json=parsed.output_json,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            latency_ms=response.latency_ms if response.latency_ms is not None else elapsed_ms,
            now=resolved_now,
        )
        _succeed_job(
            job,
            payload={
                "digest_id": str(digest.id),
                "item_count": len(parsed.items),
                "mail_count": digest.mail_count,
                "scope_type": scope.scope_type,
            },
            now=resolved_now,
        )
    except LLMProviderError as exc:
        _fail_generation(
            digest=digest,
            job=job,
            ai_run=ai_run,
            error_message="Provider request failed.",
            now=resolved_now,
        )
        raise DigestServiceError(
            "DIGEST_GENERATION_FAILED",
            "Daily digest generation failed.",
            502,
        ) from exc
    except DigestParseError as exc:
        _fail_generation(
            digest=digest,
            job=job,
            ai_run=ai_run,
            error_message=_diagnostic_for_parse_error(exc),
            now=resolved_now,
        )
        raise DigestServiceError(
            "DIGEST_GENERATION_FAILED",
            "Daily digest generation failed.",
            502,
        ) from exc
    except Exception as exc:
        _fail_digest_job(
            digest=digest,
            job=job,
            ai_run=ai_run,
            error_code="DIGEST_GENERATION_FAILED",
            error_message="Daily digest generation failed.",
            now=resolved_now,
        )
        raise DigestServiceError(
            "DIGEST_GENERATION_FAILED",
            "Daily digest generation failed.",
            502,
        ) from exc

    db.flush()
    return digest


def _fail_generation(
    *,
    digest: DailyDigest,
    job: SyncJob,
    ai_run: AIRun | None,
    error_message: str,
    now: datetime,
) -> None:
    _fail_digest_job(
        digest=digest,
        job=job,
        ai_run=ai_run,
        error_code="DIGEST_GENERATION_FAILED",
        error_message=error_message,
        now=now,
    )


def _diagnostic_for_parse_error(error: DigestParseError) -> str:
    message = str(error)
    if "valid JSON" in message:
        return "Provider response was not valid JSON."
    if "Unknown email_id" in message:
        return "Provider response referenced unknown email_id."
    return "Provider response did not match digest.v1."


def _get_user(db: Session, user_id: UUID | str) -> User:
    user = db.get(User, _as_uuid(user_id))
    if user is None:
        raise DigestServiceError("UNAUTHORIZED", "Authentication required.", 401)
    return user


def _get_mailbox_scope(
    db: Session,
    *,
    user_id: UUID,
    mailbox_id: UUID | str,
) -> Mailbox:
    mailbox = db.scalar(
        select(Mailbox)
        .where(
            Mailbox.user_id == user_id,
            Mailbox.id == _as_uuid(mailbox_id),
            Mailbox.status == "active",
        )
        .order_by(Mailbox.created_at.asc())
    )
    if mailbox is None:
        raise DigestServiceError(
            "MAILBOX_REAUTH_REQUIRED",
            "An active mailbox selection is required.",
            404,
        )
    return mailbox


def _list_active_mailboxes(db: Session, *, user_id: UUID) -> list[Mailbox]:
    return list(
        db.scalars(
            select(Mailbox)
            .where(
                Mailbox.user_id == user_id,
                Mailbox.status == "active",
            )
            .order_by(Mailbox.created_at.asc(), Mailbox.id.asc())
        ).all()
    )


def _resolve_scope_type(scope_type: str | None, mailbox_id: UUID | str | None) -> str:
    if scope_type is None:
        return "mailbox" if mailbox_id is not None else "all"
    normalized = scope_type.strip().lower()
    if normalized not in {"all", "mailbox"}:
        raise DigestServiceError("INVALID_REQUEST", "scope_type must be all or mailbox.", 422)
    if normalized == "mailbox" and mailbox_id is None:
        raise DigestServiceError(
            "INVALID_REQUEST",
            "mailbox_id is required when scope_type is mailbox.",
            422,
        )
    return normalized


def _resolve_digest_scope(
    db: Session,
    *,
    user_id: UUID,
    scope_type: str | None,
    mailbox_id: UUID | str | None,
) -> DigestScope:
    resolved_scope_type = _resolve_scope_type(scope_type, mailbox_id)
    if resolved_scope_type == "mailbox":
        mailbox = _get_mailbox_scope(db, user_id=user_id, mailbox_id=mailbox_id)
        return DigestScope(
            scope_type="mailbox",
            mailbox_id=mailbox.id,
            mailboxes=[mailbox],
        )
    mailboxes = _list_active_mailboxes(db, user_id=user_id)
    if not mailboxes:
        raise DigestServiceError(
            "INVALID_REQUEST",
            "No connected mailboxes are available for digest generation.",
            400,
        )
    return DigestScope(scope_type="all", mailbox_id=None, mailboxes=mailboxes)


def _next_digest_version(
    db: Session,
    *,
    user_id: UUID,
    scope_type: str,
    mailbox_id: UUID | None,
    digest_date: object,
) -> int:
    query = select(func.max(DailyDigest.version)).where(
        DailyDigest.user_id == user_id,
        DailyDigest.scope_type == scope_type,
        DailyDigest.digest_date == digest_date,
    )
    if mailbox_id is None:
        query = query.where(DailyDigest.mailbox_id.is_(None))
    else:
        query = query.where(DailyDigest.mailbox_id == mailbox_id)
    current_max = db.scalar(query)
    return int(current_max or 0) + 1


def _create_digest_job(
    db: Session,
    *,
    user_id: UUID,
    scope_type: str,
    mailbox_id: UUID | None,
    digest_id: UUID,
    job_type: str,
    trigger_source: str,
    target_date: object,
    now: datetime,
) -> SyncJob:
    job = SyncJob(
        user_id=user_id,
        mailbox_id=mailbox_id,
        digest_id=digest_id,
        job_type=job_type,
        trigger_source=trigger_source,
        job_key=None,
        target_date=target_date,
        status="running",
        started_at=now,
        payload_json={"scope_type": scope_type},
    )
    db.add(job)
    db.flush()
    return job


def _list_digest_emails(
    db: Session,
    *,
    user_id: UUID,
    mailbox_ids: list[UUID],
    window_start: datetime,
    window_end: datetime,
) -> list[Email]:
    if not mailbox_ids:
        return []
    return list(
        db.scalars(
            select(Email)
            .where(
                Email.user_id == user_id,
                Email.mailbox_id.in_(mailbox_ids),
                Email.received_at >= window_start,
                Email.received_at <= window_end,
            )
            .order_by(Email.received_at.desc())
        ).all()
    )


def _create_digest_items(
    db: Session,
    *,
    digest: DailyDigest,
    parsed_items: object,
    now: datetime,
) -> None:
    for display_order, item in enumerate(parsed_items):
        if item.mailbox_id is None:
            raise DigestParseError("Digest item mailbox_id could not be resolved.")
        db.add(
            DigestItem(
                digest_id=digest.id,
                user_id=digest.user_id,
                mailbox_id=item.mailbox_id,
                email_id=item.email_id,
                item_type=item.item_type,
                section=item.section,
                title=item.title,
                summary=item.summary,
                category=item.category,
                suggested_action=item.suggested_action,
                priority=item.priority,
                reason=item.reason,
                deadline=item.deadline,
                confidence=item.confidence,
                display_order=display_order,
                created_at=now,
                updated_at=now,
            )
        )
    db.flush()


def _switch_current_digest(
    db: Session,
    *,
    digest: DailyDigest,
    user_id: UUID,
    scope_type: str,
    mailbox_id: UUID | None,
    digest_date: object,
    now: datetime,
) -> None:
    query = (
        update(DailyDigest)
        .where(
            DailyDigest.user_id == user_id,
            DailyDigest.scope_type == scope_type,
            DailyDigest.digest_date == digest_date,
            DailyDigest.id != digest.id,
            DailyDigest.is_current.is_(True),
        )
        .values(is_current=False, updated_at=now)
    )
    if mailbox_id is None:
        query = query.where(DailyDigest.mailbox_id.is_(None))
    else:
        query = query.where(DailyDigest.mailbox_id == mailbox_id)
    db.execute(query)
    digest.is_current = True
    digest.updated_at = now


def _digest_job_key(
    *,
    job_type: str,
    scope_type: str,
    mailbox_id: UUID | None,
    target_date: object,
) -> str:
    if scope_type == "all":
        return f"{job_type}:all:{target_date}"
    return f"{job_type}:{mailbox_id}:{target_date}"


def _job_scope_type(job: SyncJob) -> str:
    payload = job.payload_json if isinstance(job.payload_json, dict) else {}
    scope_type = str(payload.get("scope_type") or "").strip().lower()
    if scope_type in {"all", "mailbox"}:
        return scope_type
    return "mailbox" if job.mailbox_id is not None else "all"


def _succeed_job(job: SyncJob, *, payload: dict[str, object], now: datetime) -> None:
    job.status = "succeeded"
    job.payload_json = payload
    job.finished_at = now
    job.error_code = None
    job.error_message = None


def _fail_digest_job(
    *,
    digest: DailyDigest,
    job: SyncJob,
    ai_run: AIRun | None,
    error_code: str,
    error_message: str,
    now: datetime,
) -> None:
    digest.status = "failed"
    digest.updated_at = now
    job.status = "failed"
    job.error_code = error_code
    job.error_message = safe_error_message(error_message, max_length=1000) or ""
    job.finished_at = now
    if ai_run is not None:
        mark_ai_run_failed(
            ai_run,
            error_code=error_code,
            error_message=error_message,
            now=now,
        )


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
