from __future__ import annotations

from typing import Any

from app.db.models.sync_job import SyncJob
from app.utils.redaction import safe_error_message, sanitize_sensitive_data


PUBLIC_JOB_TYPE_BY_INTERNAL = {
    "sync_today_emails": "email_sync",
    "refresh_access_token": "email_sync",
    "generate_daily_digest": "digest_generate",
    "refresh_daily_digest": "digest_refresh",
    "check_new_emails_after_digest": "scheduled_email_sync",
}
PUBLIC_STATUS_BY_INTERNAL = {
    "queued": "queued",
    "running": "running",
    "succeeded": "completed",
    "failed": "failed",
    "cancelled": "cancelled",
}


def job_payload(job: SyncJob) -> dict[str, Any]:
    status = public_job_status(job.status)
    related_resource_type, related_resource_id = _related_resource(job)
    return {
        "job_id": job.id,
        "job_type": public_job_type(job),
        "status": status,
        "progress": _progress_for_status(status),
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "error_code": job.error_code,
        "error_message": safe_error_message(job.error_message, max_length=500),
        "related_resource_type": related_resource_type,
        "related_resource_id": related_resource_id,
        "result": _safe_result(job.payload_json),
    }


def public_job_type(job: SyncJob) -> str:
    if job.trigger_source == "scheduled":
        if job.job_type == "sync_today_emails":
            return "scheduled_email_sync"
        if job.job_type in {"generate_daily_digest", "refresh_daily_digest"}:
            return "scheduled_digest"
    return PUBLIC_JOB_TYPE_BY_INTERNAL.get(job.job_type, job.job_type)


def public_job_status(status: str) -> str:
    return PUBLIC_STATUS_BY_INTERNAL.get(status, status)


def _progress_for_status(status: str) -> int:
    if status == "queued":
        return 0
    if status == "running":
        return 50
    return 100


def _related_resource(job: SyncJob) -> tuple[str | None, object | None]:
    if job.digest_id is not None:
        return "digest", job.digest_id
    if job.mailbox_id is not None:
        return "mailbox", job.mailbox_id
    return None, None


def _safe_result(value: object) -> dict[str, object]:
    sanitized = sanitize_sensitive_data(value or {})
    return sanitized if isinstance(sanitized, dict) else {}

