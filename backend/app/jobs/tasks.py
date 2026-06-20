from __future__ import annotations

from uuid import UUID

from app.db.session import SessionLocal
from app.jobs.celery_app import celery_app


@celery_app.task(name="app.jobs.health_check")
def health_check() -> dict[str, str]:
    return {"status": "ok", "worker": "mailmind"}


@celery_app.task(name="app.jobs.email_sync")
def run_email_sync_job(job_id: str) -> dict[str, object]:
    from app.services.email_sync_service import execute_queued_sync_job

    with SessionLocal() as db:
        try:
            result = execute_queued_sync_job(db, job_id=UUID(job_id))
            db.commit()
            return {
                "job_id": str(result.job_id),
                "mailbox_id": str(result.mailbox_id),
                "status": result.status,
                "synced_count": result.synced_count,
            }
        except Exception:
            db.rollback()
            raise
