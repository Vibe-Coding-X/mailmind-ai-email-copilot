from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.sync_job import SyncJob
from app.utils.redaction import safe_error_message


@dataclass(slots=True)
class DispatchResult:
    job_id: UUID
    status: str
    celery_task_id: str | None
    error_code: str | None = None
    error_message: str | None = None


def dispatch_pending_job(
    db: Session,
    *,
    job_id: UUID,
    dispatcher,
    now: datetime | None = None,
) -> DispatchResult:
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    db.commit()
    job = db.get(SyncJob, job_id)
    if job is None:
        return DispatchResult(
            job_id=job_id,
            status="dispatch_failed",
            celery_task_id=None,
            error_code="missing_job_before_dispatch",
            error_message="Background job disappeared before Celery dispatch.",
        )
    if job.status == "queued" and job.celery_task_id:
        return DispatchResult(
            job_id=job.id,
            status=job.status,
            celery_task_id=job.celery_task_id,
        )
    if job.status != "pending_dispatch":
        return DispatchResult(
            job_id=job.id,
            status=job.status,
            celery_task_id=job.celery_task_id,
            error_code=job.error_code,
            error_message=job.error_message,
        )

    try:
        celery_task_id = dispatcher(job.id)
    except Exception as exc:
        job.status = "dispatch_failed"
        job.finished_at = resolved_now
        job.error_code = "celery_dispatch_failed"
        job.error_message = (
            safe_error_message(str(exc), max_length=1000) or "Celery dispatch failed."
        )
        db.commit()
        return DispatchResult(
            job_id=job.id,
            status=job.status,
            celery_task_id=None,
            error_code=job.error_code,
            error_message=job.error_message,
        )

    job.status = "queued"
    job.celery_task_id = celery_task_id
    job.error_code = None
    job.error_message = None
    job.finished_at = None
    db.commit()
    return DispatchResult(
        job_id=job.id,
        status=job.status,
        celery_task_id=job.celery_task_id,
    )


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
