from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.sync_job import SyncJob


class JobServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(slots=True)
class JobQueryResult:
    jobs: list[SyncJob]
    limit: int
    offset: int
    has_more: bool


PUBLIC_STATUS_TO_INTERNAL = {
    "queued": {"queued"},
    "running": {"running"},
    "completed": {"succeeded"},
    "failed": {"failed"},
    "cancelled": {"cancelled"},
}
PUBLIC_JOB_TYPE_TO_INTERNAL = {
    "email_sync": {"sync_today_emails", "refresh_access_token"},
    "digest_generate": {"generate_daily_digest"},
    "digest_refresh": {"refresh_daily_digest"},
    "scheduled_email_sync": {"sync_today_emails", "check_new_emails_after_digest"},
    "scheduled_digest": {"generate_daily_digest", "refresh_daily_digest"},
}


def query_jobs(
    db: Session,
    *,
    user_id: UUID,
    limit: int = 50,
    offset: int = 0,
    job_type: str | None = None,
    status: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> JobQueryResult:
    resolved_limit = max(1, min(limit, 100))
    resolved_offset = max(0, offset)
    statement = select(SyncJob).where(SyncJob.user_id == user_id)
    if job_type is not None:
        internal_types = PUBLIC_JOB_TYPE_TO_INTERNAL.get(job_type)
        if internal_types is None:
            raise JobServiceError("INVALID_REQUEST", "Unsupported job_type.")
        statement = statement.where(SyncJob.job_type.in_(internal_types))
        if job_type == "scheduled_email_sync":
            statement = statement.where(SyncJob.trigger_source == "scheduled")
        elif job_type == "scheduled_digest":
            statement = statement.where(SyncJob.trigger_source == "scheduled")
        elif job_type in {"email_sync", "digest_generate", "digest_refresh"}:
            statement = statement.where(SyncJob.trigger_source != "scheduled")
    if status is not None:
        internal_statuses = PUBLIC_STATUS_TO_INTERNAL.get(status)
        if internal_statuses is None:
            raise JobServiceError("INVALID_REQUEST", "Unsupported status.")
        statement = statement.where(SyncJob.status.in_(internal_statuses))
    if created_from is not None:
        statement = statement.where(SyncJob.created_at >= _ensure_utc(created_from))
    if created_to is not None:
        statement = statement.where(SyncJob.created_at <= _ensure_utc(created_to))

    rows = list(
        db.scalars(
            statement.order_by(SyncJob.created_at.desc(), SyncJob.id.desc())
            .offset(resolved_offset)
            .limit(resolved_limit + 1)
        ).all()
    )
    return JobQueryResult(
        jobs=rows[:resolved_limit],
        limit=resolved_limit,
        offset=resolved_offset,
        has_more=len(rows) > resolved_limit,
    )


def get_job(db: Session, *, user_id: UUID, job_id: UUID) -> SyncJob:
    job = db.scalar(select(SyncJob).where(SyncJob.id == job_id, SyncJob.user_id == user_id))
    if job is None:
        raise JobServiceError("INVALID_REQUEST", "Job not found.", 404)
    return job


def retry_job(
    db: Session,
    *,
    user_id: UUID,
    job_id: UUID,
    now: datetime | None = None,
) -> SyncJob:
    job = get_job(db, user_id=user_id, job_id=job_id)
    if job.status != "failed":
        raise JobServiceError("INVALID_REQUEST", "Only failed jobs can be retried.")
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    retry = SyncJob(
        user_id=job.user_id,
        mailbox_id=job.mailbox_id,
        digest_id=job.digest_id,
        job_type=job.job_type,
        trigger_source=job.trigger_source,
        job_key=None,
        target_date=job.target_date,
        status="queued",
        retry_count=job.retry_count + 1,
        payload_json={"retry_of_job_id": str(job.id)},
        created_at=resolved_now,
    )
    db.add(retry)
    db.flush()
    return retry


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)

