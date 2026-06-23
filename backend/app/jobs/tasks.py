from __future__ import annotations

import random
from uuid import UUID

from app.db.session import SessionLocal
from app.jobs.celery_app import celery_app


MAX_TASK_RETRIES = 3
RETRYABLE_SYNC_ERROR_CODES = {
    "network_tls",
    "network_timeout",
    "gmail_rate_limited",
    "gmail_quota_exceeded",
    "gmail_api_error",
    "PROVIDER_RATE_LIMITED",
    "PROVIDER_SYNC_FAILED",
}
NON_RETRYABLE_SYNC_ERROR_CODES = {
    "oauth_invalid_grant",
    "gmail_permission_denied",
    "MAILBOX_REAUTH_REQUIRED",
    "worker_lock_conflict",
    "duplicate_job",
}


@celery_app.task(name="app.jobs.health_check")
def health_check() -> dict[str, str]:
    return {"status": "ok", "worker": "mailmind"}


@celery_app.task(
    bind=True,
    name="app.jobs.email_sync",
    max_retries=MAX_TASK_RETRIES,
)
def run_email_sync_job(self, job_id: str) -> dict[str, object]:
    from app.services.email_sync_service import EmailSyncError, execute_queued_sync_job

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
        except EmailSyncError as exc:
            should_retry = (
                _is_retryable_sync_error(exc.code)
                and self.request.retries < MAX_TASK_RETRIES
            )
            if should_retry:
                from app.db.models.sync_job import SyncJob

                job = db.get(SyncJob, UUID(job_id))
                if job is not None:
                    job.status = "queued"
                    job.retry_count = self.request.retries + 1
                db.commit()
                raise self.retry(
                    exc=exc,
                    countdown=_retry_countdown(exc.code, self.request.retries),
                )
            db.commit()
            raise
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


def _is_retryable_sync_error(code: str) -> bool:
    if code in NON_RETRYABLE_SYNC_ERROR_CODES:
        return False
    return code in RETRYABLE_SYNC_ERROR_CODES


def _retry_countdown(code: str, retries: int) -> int:
    rate_limit_codes = {
        "gmail_rate_limited",
        "gmail_quota_exceeded",
        "PROVIDER_RATE_LIMITED",
    }
    base = 60 if code in rate_limit_codes else 10
    return base * (2**retries) + random.randint(0, 10)


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
