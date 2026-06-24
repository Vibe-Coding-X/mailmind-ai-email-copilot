from app.core.config import Settings
from app.jobs.celery_app import create_celery_app
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.db.models.mailbox import Mailbox
from app.db.models.sync_job import SyncJob
from app.db.session import SessionLocal
from app.jobs.tasks import health_check, run_email_sync_job
from app.services.auth_service import register_user
from app.services.email_sync_service import EmailSyncError


def test_celery_app_uses_eager_mode_for_tests() -> None:
    celery_app = create_celery_app(
        Settings(
            redis_url="redis://localhost:6379/9",
            background_jobs_eager=True,
        )
    )

    assert celery_app.conf.broker_url == "redis://localhost:6379/9"
    assert celery_app.conf.result_backend == "redis://localhost:6379/9"
    assert celery_app.conf.task_always_eager is True
    assert celery_app.conf.task_eager_propagates is True


def test_health_check_task_runs_in_eager_mode() -> None:
    health_check.app.conf.task_always_eager = True
    health_check.app.conf.task_eager_propagates = True

    result = health_check.delay()

    assert result.get(timeout=1) == {"status": "ok", "worker": "mailmind"}


def test_email_sync_task_returns_serializable_ignored_result_for_stale_job() -> None:
    with SessionLocal() as db:
        user = register_user(
            db,
            email=f"task-stale-{uuid4().hex}@example.com",
            password="strong-password",
            timezone="Asia/Shanghai",
        )
        mailbox = Mailbox(
            user_id=user.id,
            provider="gmail",
            provider_account_id=f"task-stale-{uuid4().hex}",
            email_address=f"task-stale-mailbox-{uuid4().hex}@example.com",
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status="active",
        )
        db.add(mailbox)
        db.flush()
        job = SyncJob(
            user_id=user.id,
            mailbox_id=mailbox.id,
            job_type="sync_today_emails",
            trigger_source="manual",
            target_date=datetime(2026, 6, 19, tzinfo=UTC).date(),
            status="failed",
            error_code="stale_sync_job",
            error_message="Previous sync job did not complete and was replaced.",
            created_at=datetime.now(UTC) - timedelta(minutes=10),
            finished_at=datetime.now(UTC),
            payload_json={},
        )
        db.add(job)
        db.commit()
        job_id = job.id
        mailbox_id = mailbox.id

    result = run_email_sync_job.run(str(job_id))

    assert result == {
        "job_id": str(job_id),
        "mailbox_id": str(mailbox_id),
        "status": "ignored",
        "synced_count": 0,
        "error_code": "stale_or_completed_sync_task",
        "message": "Sync task ignored because the database job is no longer queued.",
    }


def test_email_sync_task_returns_serializable_result_for_orphaned_job() -> None:
    job_id = uuid4()

    result = run_email_sync_job.run(str(job_id))

    assert result == {
        "job_id": str(job_id),
        "mailbox_id": None,
        "status": "ignored",
        "synced_count": 0,
        "error_code": "orphaned_sync_task",
        "message": "Sync task ignored because the database job no longer exists.",
    }


def test_email_sync_task_catches_non_retryable_sync_error(monkeypatch) -> None:
    job_id = uuid4()

    def fake_execute(*args, **kwargs):
        raise EmailSyncError("INVALID_REQUEST", "Sync job not found.", 404)

    monkeypatch.setattr(
        "app.services.email_sync_service.execute_queued_sync_job",
        fake_execute,
    )

    result = run_email_sync_job.run(str(job_id))

    assert result == {
        "job_id": str(job_id),
        "mailbox_id": None,
        "status": "failed",
        "synced_count": 0,
        "error_code": "INVALID_REQUEST",
        "message": "Sync job not found.",
    }
