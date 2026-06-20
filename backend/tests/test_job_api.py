from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models.mailbox import Mailbox
from app.db.models.sync_job import SyncJob
from app.db.session import SessionLocal
from app.main import app
from app.services.job_service import MAX_JOB_RETRIES


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _register_client(prefix: str) -> tuple[TestClient, UUID]:
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={"email": _email(prefix), "password": "strong-password"},
    )
    assert response.status_code == 201
    return client, UUID(response.json()["data"]["user"]["id"])


def _create_mailbox(user_id: UUID, *, prefix: str) -> UUID:
    with SessionLocal() as db:
        mailbox = Mailbox(
            user_id=user_id,
            provider="gmail",
            provider_account_id=f"{prefix}-{uuid4().hex}",
            email_address=_email(f"{prefix}-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status="active",
        )
        db.add(mailbox)
        db.commit()
        return mailbox.id


def _create_job(
    user_id: UUID,
    *,
    mailbox_id: UUID | None = None,
    job_type: str = "sync_today_emails",
    status: str = "succeeded",
    retry_count: int = 0,
    created_at: datetime = datetime(2026, 6, 20, 1, 0, tzinfo=UTC),
    error_message: str | None = None,
    payload_json: dict[str, object] | None = None,
) -> UUID:
    with SessionLocal() as db:
        job = SyncJob(
            user_id=user_id,
            mailbox_id=mailbox_id,
            job_type=job_type,
            trigger_source="manual",
            status=status,
            retry_count=retry_count,
            payload_json=payload_json or {},
            error_code="TEST_ERROR" if error_message else None,
            error_message=error_message,
            created_at=created_at,
            started_at=created_at if status != "queued" else None,
            finished_at=created_at + timedelta(seconds=5)
            if status in {"succeeded", "failed", "cancelled"}
            else None,
        )
        db.add(job)
        db.commit()
        return job.id


def test_list_jobs_requires_login() -> None:
    response = TestClient(app).get("/api/jobs")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_list_jobs_returns_only_current_user_jobs_with_public_shape() -> None:
    client, user_id = _register_client("jobs-owner")
    mailbox_id = _create_mailbox(user_id, prefix="jobs-owner")
    other_client, other_user_id = _register_client("jobs-other")
    other_mailbox_id = _create_mailbox(other_user_id, prefix="jobs-other")
    _create_job(
        user_id,
        mailbox_id=mailbox_id,
        status="succeeded",
        payload_json={"synced_count": 3, "access_token": "secret"},
    )
    _create_job(other_user_id, mailbox_id=other_mailbox_id, status="failed")

    response = client.get("/api/jobs")

    assert other_client.get("/api/jobs").status_code == 200
    assert response.status_code == 200
    body = response.json()
    jobs = body["data"]["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["job_type"] == "email_sync"
    assert jobs[0]["status"] == "completed"
    assert jobs[0]["progress"] == 100
    assert jobs[0]["related_resource_type"] == "mailbox"
    assert jobs[0]["related_resource_id"] == str(mailbox_id)
    assert jobs[0]["result"] == {"synced_count": 3}
    assert body["data"]["pagination"]["count"] == 1


def test_list_jobs_filters_by_public_job_type_status_and_date_range() -> None:
    client, user_id = _register_client("jobs-filter")
    mailbox_id = _create_mailbox(user_id, prefix="jobs-filter")
    target = datetime(2026, 6, 20, 1, 0, tzinfo=UTC)
    _create_job(
        user_id,
        mailbox_id=mailbox_id,
        job_type="sync_today_emails",
        status="succeeded",
        created_at=target,
    )
    _create_job(
        user_id,
        mailbox_id=mailbox_id,
        job_type="generate_daily_digest",
        status="failed",
        created_at=target + timedelta(hours=1),
    )

    response = client.get(
        "/api/jobs",
        params={
            "job_type": "email_sync",
            "status": "completed",
            "created_from": "2026-06-20T00:00:00Z",
            "created_to": "2026-06-20T01:30:00Z",
        },
    )

    assert response.status_code == 200
    jobs = response.json()["data"]["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["job_type"] == "email_sync"
    assert jobs[0]["status"] == "completed"


def test_get_job_blocks_other_users_job() -> None:
    client, _ = _register_client("jobs-reader")
    _, other_user_id = _register_client("jobs-owner-detail")
    other_mailbox_id = _create_mailbox(other_user_id, prefix="jobs-owner-detail")
    job_id = _create_job(other_user_id, mailbox_id=other_mailbox_id)

    response = client.get(f"/api/jobs/{job_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_get_job_redacts_error_message() -> None:
    client, user_id = _register_client("jobs-redact")
    mailbox_id = _create_mailbox(user_id, prefix="jobs-redact")
    job_id = _create_job(
        user_id,
        mailbox_id=mailbox_id,
        status="failed",
        error_message=(
            "Provider failed with Authorization: Bearer bearer-secret "
            "access_token=access-secret sk-real-looking-secret"
        ),
    )

    response = client.get(f"/api/jobs/{job_id}")

    assert response.status_code == 200
    serialized = response.text
    assert "bearer-secret" not in serialized
    assert "access-secret" not in serialized
    assert "sk-real-looking-secret" not in serialized
    assert "[REDACTED]" in serialized


def test_retry_failed_job_creates_queued_retry_for_current_user(monkeypatch) -> None:
    client, user_id = _register_client("jobs-retry")
    mailbox_id = _create_mailbox(user_id, prefix="jobs-retry")
    failed_job_id = _create_job(
        user_id,
        mailbox_id=mailbox_id,
        status="failed",
        error_message="Provider failed.",
    )
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-retry-email-{job_id}"

    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        fake_dispatch,
    )

    response = client.post(f"/api/jobs/{failed_job_id}/retry")

    assert response.status_code == 200
    retried = response.json()["data"]["job"]
    assert retried["job_id"] != str(failed_job_id)
    assert retried["job_type"] == "email_sync"
    assert retried["status"] == "queued"
    assert retried["progress"] == 0
    assert retried["retry_count"] == 1
    assert retried["max_retries"] == MAX_JOB_RETRIES

    with SessionLocal() as db:
        retry_job = db.scalar(
            select(SyncJob).where(SyncJob.id == UUID(retried["job_id"]))
        )
        assert retry_job is not None
        assert retry_job.user_id == user_id
        assert retry_job.mailbox_id == mailbox_id
        assert retry_job.retry_count == 1
        assert retry_job.status == "queued"
        assert retry_job.celery_task_id == f"celery-retry-email-{retry_job.id}"
        assert retry_job.payload_json == {"retry_of_job_id": str(failed_job_id)}
    assert dispatched == [UUID(retried["job_id"])]


def test_retry_failed_digest_job_dispatches_digest_worker(monkeypatch) -> None:
    client, user_id = _register_client("jobs-retry-digest")
    mailbox_id = _create_mailbox(user_id, prefix="jobs-retry-digest")
    failed_job_id = _create_job(
        user_id,
        mailbox_id=mailbox_id,
        job_type="refresh_daily_digest",
        status="failed",
        error_message="Provider response was not valid JSON.",
    )
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-retry-digest-{job_id}"

    monkeypatch.setattr("app.services.digest_service.dispatch_digest_job", fake_dispatch)

    response = client.post(f"/api/jobs/{failed_job_id}/retry")

    assert response.status_code == 200
    retried = response.json()["data"]["job"]
    assert retried["job_type"] == "digest_refresh"
    assert retried["status"] == "queued"
    assert retried["retry_count"] == 1

    with SessionLocal() as db:
        retry_job = db.get(SyncJob, UUID(retried["job_id"]))
        assert retry_job is not None
        assert retry_job.job_type == "refresh_daily_digest"
        assert retry_job.celery_task_id == f"celery-retry-digest-{retry_job.id}"
    assert dispatched == [UUID(retried["job_id"])]


def test_retry_failed_job_rejects_when_retry_limit_reached(monkeypatch) -> None:
    client, user_id = _register_client("jobs-retry-limit")
    mailbox_id = _create_mailbox(user_id, prefix="jobs-retry-limit")
    failed_job_id = _create_job(
        user_id,
        mailbox_id=mailbox_id,
        status="failed",
        retry_count=MAX_JOB_RETRIES,
        error_message="Provider failed.",
    )
    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        lambda job_id: f"celery-should-not-run-{job_id}",
    )

    response = client.post(f"/api/jobs/{failed_job_id}/retry")

    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "JOB_RETRY_LIMIT_EXCEEDED"
    assert body["error"]["message"] == "Job has reached the retry limit."

    with SessionLocal() as db:
        retry_count = db.scalar(
            select(func.count(SyncJob.id)).where(
                SyncJob.payload_json["retry_of_job_id"].astext == str(failed_job_id)
            )
        )
        assert retry_count == 0
