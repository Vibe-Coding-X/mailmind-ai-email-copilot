from __future__ import annotations

from typing import Any

from app.db.models.sync_job import SyncJob


def sync_status_for_api(status: str) -> str:
    if status == "succeeded":
        return "completed"
    return status


def sync_job_payload(job: SyncJob | None) -> dict[str, Any] | None:
    if job is None:
        return None
    return {
        "id": job.id,
        "job_type": job.job_type,
        "status": sync_status_for_api(job.status),
        "mailbox_id": job.mailbox_id,
        "digest_id": job.digest_id,
        "celery_task_id": job.celery_task_id,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "error_message": job.error_message,
    }
