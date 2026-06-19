from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.models.user_action import UserAction
from app.db.session import SessionLocal
from app.main import app
from app.providers.base import ProviderError
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
            body_text="Body should not be audited in full",
            body_text_truncated=False,
            received_at=datetime(2026, 6, 19, 2, 0, tzinfo=UTC),
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
        return ["INBOX"]

    def mark_as_unread(self, access_token: str, message_id: str) -> list[str]:
        assert access_token == "fake-access-token"
        return ["INBOX", "UNREAD"]


class FailingProvider:
    def refresh_access_token(self, refresh_token: str) -> str:
        return "fake-access-token"

    def mark_as_read(self, access_token: str, message_id: str) -> list[str]:
        raise ProviderError("PROVIDER_SYNC_FAILED", "Gmail request failed.", 502)

    def mark_as_unread(self, access_token: str, message_id: str) -> list[str]:
        raise ProviderError("PROVIDER_SYNC_FAILED", "Gmail request failed.", 502)


def test_mark_read_and_unread_write_completed_user_actions(monkeypatch) -> None:
    client, user_id = _register_client("email-audit")
    mailbox_id = _create_mailbox(user_id, prefix="email-audit")
    email_id = _create_email(user_id, mailbox_id, external_id="email-audit", is_read=False)
    monkeypatch.setattr("app.services.email_service.GmailProvider", lambda: FakeProvider())

    assert client.post(f"/api/emails/{email_id}/mark-read").status_code == 200
    assert client.post(f"/api/emails/{email_id}/mark-unread").status_code == 200

    with SessionLocal() as db:
        actions = list(
            db.scalars(
                select(UserAction)
                .where(UserAction.email_id == email_id)
                .order_by(UserAction.created_at.asc())
            ).all()
        )
        assert [action.action_type for action in actions] == ["mark_read", "mark_unread"]
        assert [action.action_status for action in actions] == ["executed", "executed"]
        assert all(action.provider_effect == "gmail_synced" for action in actions)
        assert actions[0].before_state == {
            "is_read": False,
            "provider_labels": ["INBOX", "UNREAD"],
        }
        assert actions[0].after_state == {"is_read": True, "provider_labels": ["INBOX"]}
        assert "Body should not be audited in full" not in str(actions[0].after_state)


def test_mark_read_provider_failure_records_failed_action_without_updating_email(
    monkeypatch,
) -> None:
    client, user_id = _register_client("email-audit-fail")
    mailbox_id = _create_mailbox(user_id, prefix="email-audit-fail")
    email_id = _create_email(
        user_id,
        mailbox_id,
        external_id="email-audit-fail",
        is_read=False,
    )
    monkeypatch.setattr("app.services.email_service.GmailProvider", lambda: FailingProvider())

    response = client.post(f"/api/emails/{email_id}/mark-read")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "PROVIDER_SYNC_FAILED"
    with SessionLocal() as db:
        email = db.get(Email, email_id)
        action = db.scalar(select(UserAction).where(UserAction.email_id == email_id))
        assert email is not None
        assert email.is_read is False
        assert action is not None
        assert action.action_type == "mark_read"
        assert action.action_status == "failed"
        assert action.error_code == "PROVIDER_SYNC_FAILED"


def test_mark_read_missing_credential_records_failed_action_without_updating_email() -> None:
    client, user_id = _register_client("email-audit-reauth")
    with SessionLocal() as db:
        mailbox = Mailbox(
            user_id=user_id,
            provider="gmail",
            provider_account_id=f"email-audit-reauth-{uuid4().hex}",
            email_address=_email("email-audit-reauth-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status="active",
        )
        db.add(mailbox)
        db.commit()
        mailbox_id = mailbox.id
    email_id = _create_email(
        user_id,
        mailbox_id,
        external_id="email-audit-reauth",
        is_read=False,
    )

    response = client.post(f"/api/emails/{email_id}/mark-read")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MAILBOX_REAUTH_REQUIRED"
    with SessionLocal() as db:
        email = db.get(Email, email_id)
        action = db.scalar(select(UserAction).where(UserAction.email_id == email_id))
        assert email is not None
        assert email.is_read is False
        assert action is not None
        assert action.action_type == "mark_read"
        assert action.action_status == "failed"
        assert action.error_code == "MAILBOX_REAUTH_REQUIRED"


def test_cross_user_mark_read_does_not_write_action(monkeypatch) -> None:
    client, _ = _register_client("email-audit-cross-current")
    _, other_user_id = _register_client("email-audit-cross-other")
    other_mailbox_id = _create_mailbox(other_user_id, prefix="email-audit-cross")
    other_email_id = _create_email(
        other_user_id,
        other_mailbox_id,
        external_id="email-audit-cross",
        is_read=False,
    )
    monkeypatch.setattr("app.services.email_service.GmailProvider", lambda: FakeProvider())

    response = client.post(f"/api/emails/{other_email_id}/mark-read")

    assert response.status_code == 404
    with SessionLocal() as db:
        assert db.scalar(select(UserAction).where(UserAction.email_id == other_email_id)) is None
