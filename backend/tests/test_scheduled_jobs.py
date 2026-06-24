from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select

from app.ai.mock_provider import MockLLMProvider
from app.db.models.daily_digest import DailyDigest
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.sync_job import SyncJob
from app.db.session import SessionLocal
from app.schemas.job import job_payload
from app.services.auth_service import register_user
from app.services.digest_service import execute_queued_digest_job
from app.services.email_sync_service import enqueue_sync_today_job
from app.services.scheduled_job_service import (
    enqueue_due_scheduled_digest_jobs,
    enqueue_due_scheduled_email_sync_jobs,
)


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _create_user_mailbox(
    *,
    prefix: str,
    timezone: str = "Asia/Shanghai",
    mailbox_status: str = "active",
) -> tuple[UUID, UUID]:
    with SessionLocal() as db:
        user = register_user(
            db,
            email=_email(prefix),
            password="strong-password",
            timezone=timezone,
        )
        mailbox = Mailbox(
            user_id=user.id,
            provider="gmail",
            provider_account_id=f"{prefix}-{uuid4().hex}",
            email_address=_email(f"{prefix}-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status=mailbox_status,
        )
        db.add(mailbox)
        db.commit()
        return user.id, mailbox.id


def _add_email(user_id: UUID, mailbox_id: UUID, *, prefix: str, received_at: datetime) -> None:
    with SessionLocal() as db:
        db.add(
            Email(
                user_id=user_id,
                mailbox_id=mailbox_id,
                provider="gmail",
                external_id=f"{prefix}-gmail-1",
                external_thread_id=f"{prefix}-thread-1",
                subject="Scheduled digest input",
                from_address="sender@example.com",
                to_addresses=["me@example.com"],
                cc_addresses=[],
                snippet="Please review this scheduled digest item.",
                body_text="Please review this scheduled digest item today.",
                body_text_truncated=False,
                received_at=received_at,
                is_read=False,
                provider_labels=["INBOX", "UNREAD"],
            )
        )
        db.commit()


def test_scheduled_email_sync_enqueues_active_mailboxes_once_per_local_day(
    monkeypatch,
) -> None:
    _, mailbox_id = _create_user_mailbox(prefix="scheduled-sync")
    _, reauth_mailbox_id = _create_user_mailbox(
        prefix="scheduled-sync-reauth",
        mailbox_status="reauth_required",
    )
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-scheduled-sync-{job_id}"

    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        fake_dispatch,
    )

    now = datetime(2026, 6, 20, 0, 30, tzinfo=UTC)
    with SessionLocal() as db:
        first = enqueue_due_scheduled_email_sync_jobs(db, now=now)
        second = enqueue_due_scheduled_email_sync_jobs(db, now=now)
        db.commit()

    assert first.created_count >= 1
    assert second.created_count == 0
    assert dispatched == first.job_ids

    with SessionLocal() as db:
        job = db.scalar(
            select(SyncJob).where(
                SyncJob.mailbox_id == mailbox_id,
                SyncJob.job_key == f"scheduled_email_sync:{mailbox_id}:2026-06-20",
            )
        )
        assert job is not None
        assert job.mailbox_id == mailbox_id
        assert job.job_type == "sync_today_emails"
        assert job.trigger_source == "scheduled"
        assert job.target_date.isoformat() == "2026-06-20"
        assert job.status == "queued"
        assert job.celery_task_id == f"celery-scheduled-sync-{job.id}"
        assert job_payload(job)["job_type"] == "scheduled_email_sync"
        assert (
            db.scalar(
                select(func.count(SyncJob.id)).where(
                    SyncJob.job_key
                    == f"scheduled_email_sync:{reauth_mailbox_id}:2026-06-20",
                )
            )
            == 0
        )


def test_scheduled_email_sync_reuses_manual_active_job(monkeypatch) -> None:
    user_id, mailbox_id = _create_user_mailbox(prefix="scheduled-sync-manual-active")
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-sync-{job_id}"

    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        fake_dispatch,
    )

    now = datetime(2026, 6, 20, 0, 30, tzinfo=UTC)
    with SessionLocal() as db:
        manual = enqueue_sync_today_job(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            now=now,
        )
        scheduled = enqueue_due_scheduled_email_sync_jobs(db, now=now)
        db.commit()

    assert scheduled.skipped_count >= 1
    assert manual.job_id in dispatched

    with SessionLocal() as db:
        jobs = db.scalars(
            select(SyncJob).where(
                SyncJob.user_id == user_id,
                SyncJob.mailbox_id == mailbox_id,
                SyncJob.job_type == "sync_today_emails",
            )
        ).all()
        assert len(jobs) == 1
        assert jobs[0].id == manual.job_id
        assert (
            db.scalar(
                select(func.count(SyncJob.id)).where(
                    SyncJob.job_key
                    == f"scheduled_email_sync:{mailbox_id}:2026-06-20",
                )
            )
            == 0
        )


def test_scheduled_digest_respects_local_generate_time_and_dedupes(
    monkeypatch,
) -> None:
    _, mailbox_id = _create_user_mailbox(prefix="scheduled-digest")
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-scheduled-digest-{job_id}"

    monkeypatch.setattr(
        "app.services.scheduled_job_service.dispatch_digest_job",
        fake_dispatch,
    )

    before_digest_time = datetime(2026, 6, 19, 23, 30, tzinfo=UTC)
    after_digest_time = datetime(2026, 6, 20, 0, 30, tzinfo=UTC)
    with SessionLocal() as db:
        before = enqueue_due_scheduled_digest_jobs(
            db,
            now=before_digest_time,
            generate_time="08:00",
        )
        first = enqueue_due_scheduled_digest_jobs(
            db,
            now=after_digest_time,
            generate_time="08:00",
        )
        second = enqueue_due_scheduled_digest_jobs(
            db,
            now=after_digest_time,
            generate_time="08:00",
        )
        db.commit()

    assert before.created_count == 0
    assert first.created_count >= 1
    assert second.created_count == 0
    assert dispatched == first.job_ids

    with SessionLocal() as db:
        job = db.scalar(
            select(SyncJob).where(
                SyncJob.mailbox_id == mailbox_id,
                SyncJob.job_key == f"scheduled_digest:{mailbox_id}:2026-06-20",
            )
        )
        assert job is not None
        assert job.mailbox_id == mailbox_id
        assert job.job_type == "generate_daily_digest"
        assert job.trigger_source == "scheduled"
        assert job.target_date.isoformat() == "2026-06-20"
        assert job.status == "queued"
        assert job.celery_task_id == f"celery-scheduled-digest-{job.id}"
        assert job_payload(job)["job_type"] == "scheduled_digest"


def test_scheduled_digest_generation_worker_preserves_scheduled_trigger() -> None:
    user_id, mailbox_id = _create_user_mailbox(prefix="scheduled-digest-worker")
    now = datetime(2026, 6, 20, 0, 30, tzinfo=UTC)
    _add_email(
        user_id,
        mailbox_id,
        prefix="scheduled-digest-worker",
        received_at=datetime(2026, 6, 20, 0, 0, tzinfo=UTC),
    )

    with SessionLocal() as db:
        result = enqueue_due_scheduled_digest_jobs(
            db,
            now=now,
            dispatch=False,
            generate_time="08:00",
        )
        queued_job = db.get(SyncJob, result.job_ids[0])
        assert queued_job is not None
        queued_job.status = "queued"
        queued_job.celery_task_id = f"manual-dispatch-{queued_job.id}"
        db.flush()
        result = execute_queued_digest_job(
            db,
            job_id=result.job_ids[0],
            llm_provider=MockLLMProvider(),
            now=now,
        )
        db.commit()
        digest_id = result.digest_id

    with SessionLocal() as db:
        stored = db.get(DailyDigest, digest_id)
        scheduled_jobs = list(
            db.scalars(
                select(SyncJob).where(
                    SyncJob.digest_id == digest_id,
                    SyncJob.trigger_source == "scheduled",
                )
            )
        )
        assert stored is not None
        assert stored.trigger_source == "scheduled"
        assert stored.status == "fresh"
        assert len(scheduled_jobs) >= 1
        assert (
            db.scalar(
                select(func.count(SyncJob.id)).where(
                    SyncJob.job_key
                    == f"scheduled_digest:{mailbox_id}:2026-06-20",
                )
            )
            == 1
        )
