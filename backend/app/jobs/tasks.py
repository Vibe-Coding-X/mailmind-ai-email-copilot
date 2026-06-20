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


@celery_app.task(name="app.jobs.digest")
def run_digest_job(job_id: str) -> dict[str, object]:
    from app.services.digest_service import execute_queued_digest_job

    with SessionLocal() as db:
        try:
            digest = execute_queued_digest_job(db, job_id=UUID(job_id))
            db.commit()
            return {
                "job_id": job_id,
                "digest_id": str(digest.id),
                "status": digest.status,
                "mail_count": digest.mail_count,
            }
        except Exception:
            db.rollback()
            raise


@celery_app.task(name="app.jobs.scheduled_email_sync")
def run_scheduled_email_sync_jobs() -> dict[str, object]:
    from app.services.scheduled_job_service import enqueue_due_scheduled_email_sync_jobs

    with SessionLocal() as db:
        try:
            result = enqueue_due_scheduled_email_sync_jobs(db)
            db.commit()
            return {
                "job_ids": [str(job_id) for job_id in result.job_ids],
                "created_count": result.created_count,
                "skipped_count": result.skipped_count,
            }
        except Exception:
            db.rollback()
            raise


@celery_app.task(name="app.jobs.scheduled_digest")
def run_scheduled_digest_jobs() -> dict[str, object]:
    from app.services.scheduled_job_service import enqueue_due_scheduled_digest_jobs

    with SessionLocal() as db:
        try:
            result = enqueue_due_scheduled_digest_jobs(db)
            db.commit()
            return {
                "job_ids": [str(job_id) for job_id in result.job_ids],
                "created_count": result.created_count,
                "skipped_count": result.skipped_count,
            }
        except Exception:
            db.rollback()
            raise
