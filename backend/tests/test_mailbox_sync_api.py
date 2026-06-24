from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.models.sync_job import SyncJob
from app.db.session import SessionLocal
from app.main import app
from app.providers.base import ProviderEmailMessage, ProviderError
from app.providers.gmail import GmailProvider
from app.services.credential_encryption_service import CredentialEncryptionService


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


def _create_connected_mailbox(user_id: UUID, *, status: str = "active") -> UUID:
    with SessionLocal() as db:
        mailbox = Mailbox(
            user_id=user_id,
            provider="gmail",
            provider_account_id=f"sync-api-{uuid4().hex}",
            email_address=_email("sync-api-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status=status,
        )
        db.add(mailbox)
        db.flush()
        db.add(
            MailboxCredential(
                mailbox_id=mailbox.id,
                credential_type="oauth2",
                refresh_token_encrypted=CredentialEncryptionService().encrypt(
                    "fake-refresh-token"
                ),
                scopes_snapshot=mailbox.granted_scopes,
                credentials_json={},
            )
        )
        db.commit()
        return mailbox.id


class FakeProvider:
    def refresh_access_token(self, refresh_token: str) -> str:
        assert refresh_token == "fake-refresh-token"
        return "fake-access-token"

    def list_messages_for_window(
        self,
        access_token: str,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[ProviderEmailMessage]:
        assert access_token == "fake-access-token"
        return [
            ProviderEmailMessage(
                external_id="sync-api-message",
                external_thread_id="sync-api-thread",
                internet_message_id="<sync-api@example.com>",
                subject="Sync API subject",
                from_name=None,
                from_address="sender@example.com",
                to_addresses=["me@example.com"],
                cc_addresses=[],
                snippet="preview",
                body_text="body",
                body_text_truncated=False,
                received_at=datetime.now(UTC) - timedelta(minutes=5),
                is_read=False,
                provider_labels=["INBOX", "UNREAD"],
                gmail_history_id="history-1",
                raw_payload_hash="b" * 64,
            )
        ]


class FailingProvider:
    def refresh_access_token(self, refresh_token: str) -> str:
        assert refresh_token == "fake-refresh-token"
        return "fake-access-token"

    def list_messages_for_window(
        self,
        access_token: str,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[ProviderEmailMessage]:
        raise ProviderError("PROVIDER_SYNC_FAILED", "Gmail request failed.", 502)


class GmailHttpResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class AccessNotConfiguredHttpClient:
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: int,
    ) -> GmailHttpResponse:
        assert data is not None
        assert data["refresh_token"] == "fake-refresh-token"
        return GmailHttpResponse(200, {"access_token": "fake-access-token"})

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        timeout: int,
    ) -> GmailHttpResponse:
        assert headers["Authorization"] == "Bearer fake-access-token"
        return GmailHttpResponse(
            403,
            {
                "error": {
                    "code": 403,
                    "message": (
                        "Gmail API has not been used in project 660896633151 "
                        "before or it is disabled."
                    ),
                    "status": "PERMISSION_DENIED",
                    "errors": [
                        {
                            "domain": "usageLimits",
                            "reason": "accessNotConfigured",
                            "message": "Access Not Configured.",
                        }
                    ],
                }
            },
        )


class InvalidGrantHttpClient:
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: int,
    ) -> GmailHttpResponse:
        assert data is not None
        assert data["refresh_token"] == "fake-refresh-token"
        return GmailHttpResponse(400, {"error": "invalid_grant"})

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        timeout: int,
    ) -> GmailHttpResponse:
        raise AssertionError("Gmail API should not be called when token refresh fails")


def test_trigger_mailbox_sync_runs_sync_and_returns_job(monkeypatch) -> None:
    client, user_id = _register_client("mailbox-sync-api")
    mailbox_id = _create_connected_mailbox(user_id)
    monkeypatch.setattr("app.services.email_sync_service.GmailProvider", lambda: FakeProvider())

    response = client.post(f"/api/mailboxes/{mailbox_id}/sync")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["mailbox_id"] == str(mailbox_id)
    assert body["status"] == "completed"
    assert body["synced_count"] == 1
    assert UUID(body["job_id"])

    with SessionLocal() as db:
        email = db.scalar(select(Email).where(Email.external_id == "sync-api-message"))
        job = db.get(SyncJob, body["job_id"])
        assert email is not None
        assert job is not None
        assert job.status == "succeeded"


def test_trigger_mailbox_sync_calls_email_sync_service(monkeypatch) -> None:
    client, user_id = _register_client("mailbox-sync-wiring")
    mailbox_id = _create_connected_mailbox(user_id)
    job_id = uuid4()
    calls: list[dict[str, object]] = []

    @dataclass(slots=True)
    class Result:
        mailbox_id: UUID
        status: str
        synced_count: int
        job_id: UUID

    def fake_sync_today_emails(db, *, user_id, mailbox_id):
        calls.append({"user_id": user_id, "mailbox_id": mailbox_id})
        return Result(
            mailbox_id=mailbox_id,
            status="completed",
            synced_count=3,
            job_id=job_id,
        )

    monkeypatch.setattr(
        "app.services.email_sync_service.sync_today_emails",
        fake_sync_today_emails,
    )

    response = client.post(f"/api/mailboxes/{mailbox_id}/sync")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body == {
        "mailbox_id": str(mailbox_id),
        "status": "completed",
        "synced_count": 3,
        "job_id": str(job_id),
    }
    assert calls == [{"user_id": user_id, "mailbox_id": mailbox_id}]
    assert "not implemented" not in response.text.lower()


def test_trigger_async_mailbox_sync_creates_queued_job(monkeypatch) -> None:
    client, user_id = _register_client("mailbox-async-sync")
    mailbox_id = _create_connected_mailbox(user_id)
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-job-async-{job_id}"

    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        fake_dispatch,
    )

    response = client.post(f"/api/mailboxes/{mailbox_id}/sync-jobs")

    assert response.status_code == 200
    job = response.json()["data"]["job"]
    assert job["job_type"] == "email_sync"
    assert job["status"] == "queued"
    assert job["progress"] == 0
    assert job["related_resource_type"] == "mailbox"
    assert job["related_resource_id"] == str(mailbox_id)
    assert dispatched == [UUID(job["job_id"])]

    with SessionLocal() as db:
        stored = db.get(SyncJob, job["job_id"])
        assert stored is not None
        assert stored.user_id == user_id
        assert stored.status == "queued"
        assert stored.celery_task_id == f"celery-job-async-{stored.id}"


def test_trigger_async_mailbox_sync_dispatches_after_job_commit(monkeypatch) -> None:
    client, user_id = _register_client("mailbox-async-sync-commit-order")
    mailbox_id = _create_connected_mailbox(user_id)
    checked: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        with SessionLocal() as verify_db:
            stored = verify_db.get(SyncJob, job_id)
            assert stored is not None
            assert stored.status == "pending_dispatch"
        checked.append(job_id)
        return f"celery-job-async-{job_id}"

    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        fake_dispatch,
    )

    response = client.post(f"/api/mailboxes/{mailbox_id}/sync-jobs")

    assert response.status_code == 200
    job = response.json()["data"]["job"]
    assert checked == [UUID(job["job_id"])]


def test_trigger_async_mailbox_sync_marks_dispatch_failure(monkeypatch) -> None:
    client, user_id = _register_client("mailbox-async-sync-dispatch-failure")
    mailbox_id = _create_connected_mailbox(user_id)

    def fake_dispatch(job_id: UUID) -> str:
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        fake_dispatch,
    )

    response = client.post(f"/api/mailboxes/{mailbox_id}/sync-jobs")

    assert response.status_code == 200
    job = response.json()["data"]["job"]
    assert job["status"] == "dispatch_failed"
    assert job["celery_task_id"] is None

    with SessionLocal() as db:
        stored = db.get(SyncJob, job["job_id"])
        assert stored is not None
        assert stored.status == "dispatch_failed"
        assert stored.error_code == "celery_dispatch_failed"


def test_trigger_async_mailbox_sync_reuses_active_job(monkeypatch) -> None:
    client, user_id = _register_client("mailbox-async-sync-reuse")
    mailbox_id = _create_connected_mailbox(user_id)
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-job-async-{job_id}"

    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        fake_dispatch,
    )

    first_response = client.post(f"/api/mailboxes/{mailbox_id}/sync-jobs")
    second_response = client.post(f"/api/mailboxes/{mailbox_id}/sync-jobs")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_job = first_response.json()["data"]["job"]
    second_job = second_response.json()["data"]["job"]
    assert second_job["job_id"] == first_job["job_id"]
    assert second_job["status"] == "queued"
    assert dispatched == [UUID(first_job["job_id"])]

    with SessionLocal() as db:
        jobs = db.scalars(
            select(SyncJob).where(
                SyncJob.user_id == user_id,
                SyncJob.mailbox_id == mailbox_id,
                SyncJob.job_type == "sync_today_emails",
            )
        ).all()
        assert len(jobs) == 1


def test_trigger_async_mailbox_sync_creates_separate_active_jobs_per_mailbox(
    monkeypatch,
) -> None:
    client, user_id = _register_client("mailbox-async-sync-independent")
    first_mailbox_id = _create_connected_mailbox(user_id)
    second_mailbox_id = _create_connected_mailbox(user_id)
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-job-async-{job_id}"

    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        fake_dispatch,
    )

    first_response = client.post(f"/api/mailboxes/{first_mailbox_id}/sync-jobs")
    second_response = client.post(f"/api/mailboxes/{second_mailbox_id}/sync-jobs")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_job = first_response.json()["data"]["job"]
    second_job = second_response.json()["data"]["job"]
    assert first_job["job_id"] != second_job["job_id"]
    assert first_job["related_resource_id"] == str(first_mailbox_id)
    assert second_job["related_resource_id"] == str(second_mailbox_id)
    assert dispatched == [UUID(first_job["job_id"]), UUID(second_job["job_id"])]

    with SessionLocal() as db:
        jobs = db.scalars(
            select(SyncJob)
            .where(
                SyncJob.user_id == user_id,
                SyncJob.job_type == "sync_today_emails",
                SyncJob.status == "queued",
            )
            .order_by(SyncJob.created_at.asc())
        ).all()
        assert [job.mailbox_id for job in jobs] == [first_mailbox_id, second_mailbox_id]


def test_trigger_async_mailbox_sync_blocks_other_users_mailbox() -> None:
    client, _ = _register_client("mailbox-async-current-user")
    _, other_user_id = _register_client("mailbox-async-other-user")
    other_mailbox_id = _create_connected_mailbox(other_user_id)

    response = client.post(f"/api/mailboxes/{other_mailbox_id}/sync-jobs")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_sync_status_returns_latest_sync_job(monkeypatch) -> None:
    client, user_id = _register_client("mailbox-sync-status-api")
    mailbox_id = _create_connected_mailbox(user_id)
    monkeypatch.setattr("app.services.email_sync_service.GmailProvider", lambda: FakeProvider())
    sync_response = client.post(f"/api/mailboxes/{mailbox_id}/sync")
    assert sync_response.status_code == 200
    job_id = sync_response.json()["data"]["job_id"]

    response = client.get(f"/api/mailboxes/{mailbox_id}/sync-status")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["mailbox_id"] == str(mailbox_id)
    assert body["status"] == "completed"
    assert body["last_successful_sync_at"] is not None
    assert body["last_job"]["id"] == job_id
    assert body["last_job"]["job_type"] == "sync_today_emails"
    assert body["last_job"]["status"] == "completed"


def test_sync_status_recovers_stale_queued_job() -> None:
    client, user_id = _register_client("mailbox-sync-status-stale")
    mailbox_id = _create_connected_mailbox(user_id)
    stale_created_at = datetime.now(UTC) - timedelta(minutes=10)

    with SessionLocal() as db:
        stale_job = SyncJob(
            user_id=user_id,
            mailbox_id=mailbox_id,
            job_type="sync_today_emails",
            trigger_source="manual",
            target_date=stale_created_at.date(),
            status="queued",
            celery_task_id=f"lost-task-{uuid4()}",
            created_at=stale_created_at,
            payload_json={},
        )
        db.add(stale_job)
        db.commit()
        stale_job_id = stale_job.id

    response = client.get(f"/api/mailboxes/{mailbox_id}/sync-status")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["mailbox_id"] == str(mailbox_id)
    assert body["status"] == "failed"
    assert body["last_job"]["id"] == str(stale_job_id)
    assert body["last_job"]["status"] == "failed"
    assert (
        body["last_job"]["error_message"]
        == "Previous sync job did not complete and was replaced."
    )

    with SessionLocal() as db:
        recovered = db.get(SyncJob, stale_job_id)
        assert recovered is not None
        assert recovered.status == "failed"
        assert recovered.error_code == "stale_sync_job"


def test_trigger_mailbox_sync_blocks_other_users_mailbox() -> None:
    client, _ = _register_client("mailbox-sync-current-user")
    _, other_user_id = _register_client("mailbox-sync-other-user")
    other_mailbox_id = _create_connected_mailbox(other_user_id)

    response = client.post(f"/api/mailboxes/{other_mailbox_id}/sync")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_trigger_mailbox_sync_rejects_disconnected_mailbox() -> None:
    client, user_id = _register_client("mailbox-sync-disconnected")
    mailbox_id = _create_connected_mailbox(user_id, status="disconnected")

    response = client.post(f"/api/mailboxes/{mailbox_id}/sync")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MAILBOX_REAUTH_REQUIRED"
    assert "not implemented" not in response.text.lower()


def test_trigger_mailbox_sync_returns_provider_error_and_records_failed_job(
    monkeypatch,
) -> None:
    client, user_id = _register_client("mailbox-sync-provider-fail")
    mailbox_id = _create_connected_mailbox(user_id)
    monkeypatch.setattr(
        "app.services.email_sync_service.GmailProvider",
        lambda: FailingProvider(),
    )

    response = client.post(f"/api/mailboxes/{mailbox_id}/sync")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "PROVIDER_SYNC_FAILED"
    assert "not implemented" not in response.text.lower()

    with SessionLocal() as db:
        job = db.scalar(
            select(SyncJob)
            .where(SyncJob.mailbox_id == mailbox_id, SyncJob.user_id == user_id)
            .order_by(SyncJob.created_at.desc())
        )
        assert job is not None
        assert job.status == "failed"
        assert job.error_code == "PROVIDER_SYNC_FAILED"
        assert job.error_message == "Gmail request failed."


def test_trigger_mailbox_sync_access_not_configured_does_not_mark_reauth(
    monkeypatch,
) -> None:
    client, user_id = _register_client("mailbox-sync-api-disabled")
    mailbox_id = _create_connected_mailbox(user_id)
    monkeypatch.setattr(
        "app.services.email_sync_service.GmailProvider",
        lambda: GmailProvider(client=AccessNotConfiguredHttpClient()),
    )

    response = client.post(f"/api/mailboxes/{mailbox_id}/sync")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "PROVIDER_SYNC_FAILED"
    assert (
        response.json()["error"]["message"]
        == "Gmail API is disabled for the Google Cloud project."
    )

    with SessionLocal() as db:
        mailbox = db.get(Mailbox, mailbox_id)
        job = db.scalar(
            select(SyncJob)
            .where(SyncJob.mailbox_id == mailbox_id, SyncJob.user_id == user_id)
            .order_by(SyncJob.created_at.desc())
        )
        assert mailbox is not None
        assert mailbox.status == "active"
        assert job is not None
        assert job.status == "failed"
        assert job.error_code == "PROVIDER_SYNC_FAILED"
        assert job.error_message == "Gmail API is disabled for the Google Cloud project."


def test_trigger_mailbox_sync_invalid_grant_marks_mailbox_reauth(
    monkeypatch,
) -> None:
    client, user_id = _register_client("mailbox-sync-invalid-grant")
    mailbox_id = _create_connected_mailbox(user_id)
    monkeypatch.setattr(
        "app.services.email_sync_service.GmailProvider",
        lambda: GmailProvider(client=InvalidGrantHttpClient()),
    )

    response = client.post(f"/api/mailboxes/{mailbox_id}/sync")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MAILBOX_REAUTH_REQUIRED"

    with SessionLocal() as db:
        mailbox = db.get(Mailbox, mailbox_id)
        job = db.scalar(
            select(SyncJob)
            .where(SyncJob.mailbox_id == mailbox_id, SyncJob.user_id == user_id)
            .order_by(SyncJob.created_at.desc())
        )
        assert mailbox is not None
        assert mailbox.status == "reauth_required"
        assert job is not None
        assert job.status == "failed"
        assert job.error_code == "MAILBOX_REAUTH_REQUIRED"
