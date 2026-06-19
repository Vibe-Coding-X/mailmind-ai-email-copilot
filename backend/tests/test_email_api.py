from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.session import SessionLocal
from app.main import app
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


def _create_mailbox(user_id: UUID, *, account_prefix: str) -> UUID:
    with SessionLocal() as db:
        mailbox = Mailbox(
            user_id=user_id,
            provider="gmail",
            provider_account_id=f"{account_prefix}-{uuid4().hex}",
            email_address=_email(account_prefix),
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


def _create_email(
    user_id: UUID,
    mailbox_id: UUID,
    *,
    external_id: str,
    is_read: bool,
    received_at: datetime | None = None,
) -> UUID:
    with SessionLocal() as db:
        email = Email(
            user_id=user_id,
            mailbox_id=mailbox_id,
            provider="gmail",
            external_id=external_id,
            external_thread_id=f"thread-{external_id}",
            subject=f"Subject {external_id}",
            from_address="sender@example.com",
            to_addresses=["me@example.com"],
            cc_addresses=[],
            snippet="preview",
            body_text=f"Body {external_id}",
            body_text_truncated=False,
            received_at=received_at or _current_test_received_at(),
            is_read=is_read,
            provider_labels=["INBOX"] if is_read else ["INBOX", "UNREAD"],
        )
        db.add(email)
        db.commit()
        return email.id


class FakeProvider:
    def refresh_access_token(self, refresh_token: str) -> str:
        assert refresh_token == "fake-refresh-token"
        return "fake-access-token"

    def mark_as_read(self, access_token: str, message_id: str) -> list[str]:
        assert access_token == "fake-access-token"
        assert message_id
        return ["INBOX"]

    def mark_as_unread(self, access_token: str, message_id: str) -> list[str]:
        assert access_token == "fake-access-token"
        assert message_id
        return ["INBOX", "UNREAD"]


def _current_test_received_at() -> datetime:
    return datetime.now(UTC) - timedelta(minutes=5)


def test_get_today_emails_returns_only_current_user_email_summaries() -> None:
    client, user_id = _register_client("emails-today-current")
    _, other_user_id = _register_client("emails-today-other")
    mailbox_id = _create_mailbox(user_id, account_prefix="today-owned")
    other_mailbox_id = _create_mailbox(other_user_id, account_prefix="today-other")
    owned_email_id = _create_email(
        user_id, mailbox_id, external_id="owned-email", is_read=False
    )
    _create_email(other_user_id, other_mailbox_id, external_id="other-email", is_read=False)

    response = client.get("/api/emails/today")

    assert response.status_code == 200
    emails = response.json()["data"]["emails"]
    assert [email["id"] for email in emails] == [str(owned_email_id)]
    assert emails[0]["thread_id"] == "thread-owned-email"
    assert emails[0]["sender"] == "sender@example.com"
    assert emails[0]["recipients"] == ["me@example.com"]
    assert emails[0]["labels"] == ["INBOX", "UNREAD"]
    assert "body_text" not in emails[0]


def test_get_email_detail_blocks_other_users_email() -> None:
    client, _ = _register_client("email-detail-current")
    _, other_user_id = _register_client("email-detail-other")
    other_mailbox_id = _create_mailbox(other_user_id, account_prefix="detail-other")
    other_email_id = _create_email(
        other_user_id, other_mailbox_id, external_id="detail-other", is_read=True
    )

    response = client.get(f"/api/emails/{other_email_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_get_email_detail_returns_body_for_owner() -> None:
    client, user_id = _register_client("email-detail-owner")
    mailbox_id = _create_mailbox(user_id, account_prefix="detail-owner")
    email_id = _create_email(
        user_id, mailbox_id, external_id="detail-owner", is_read=True
    )

    response = client.get(f"/api/emails/{email_id}")

    assert response.status_code == 200
    email = response.json()["data"]["email"]
    assert email["id"] == str(email_id)
    assert email["body_text"] == "Body detail-owner"


def test_mark_read_and_unread_update_local_state_after_provider_success(monkeypatch) -> None:
    client, user_id = _register_client("email-mark-owner")
    mailbox_id = _create_mailbox(user_id, account_prefix="mark-owner")
    email_id = _create_email(user_id, mailbox_id, external_id="mark-owner", is_read=False)
    monkeypatch.setattr("app.services.email_service.GmailProvider", lambda: FakeProvider())

    mark_read = client.post(f"/api/emails/{email_id}/mark-read")

    assert mark_read.status_code == 200
    assert mark_read.json()["data"]["email"]["is_read"] is True
    assert mark_read.json()["data"]["email"]["labels"] == ["INBOX"]

    mark_unread = client.post(f"/api/emails/{email_id}/mark-unread")

    assert mark_unread.status_code == 200
    assert mark_unread.json()["data"]["email"]["is_read"] is False
    assert mark_unread.json()["data"]["email"]["labels"] == ["INBOX", "UNREAD"]

    with SessionLocal() as db:
        stored = db.get(Email, email_id)
        assert stored is not None
        assert stored.is_read is False


def test_mark_read_blocks_other_users_email(monkeypatch) -> None:
    client, _ = _register_client("email-mark-current")
    _, other_user_id = _register_client("email-mark-other")
    other_mailbox_id = _create_mailbox(other_user_id, account_prefix="mark-other")
    other_email_id = _create_email(
        other_user_id, other_mailbox_id, external_id="mark-other", is_read=False
    )
    monkeypatch.setattr("app.services.email_service.GmailProvider", lambda: FakeProvider())

    response = client.post(f"/api/emails/{other_email_id}/mark-read")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
