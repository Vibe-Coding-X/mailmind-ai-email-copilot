from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.models.sync_job import SyncJob
from app.db.session import SessionLocal
from app.main import app
from app.providers.base import ProviderEmailMessage
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


def _create_connected_mailbox(user_id: UUID) -> UUID:
    with SessionLocal() as db:
        mailbox = Mailbox(
            user_id=user_id,
            provider="gmail",
            provider_account_id=f"sync-api-{uuid4().hex}",
            email_address=_email("sync-api-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status="active",
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
