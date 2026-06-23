from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.session import SessionLocal
from app.main import app
from app.services.credential_encryption_service import CredentialEncryptionService


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _register_client() -> tuple[TestClient, UUID]:
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={"email": _email("imap-user"), "password": "strong-password"},
    )
    assert response.status_code == 201
    return client, UUID(response.json()["data"]["user"]["id"])


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "account_email": "InboxUser@Example.COM",
        "display_name": "Inbox User",
        "host": "IMAP.EXAMPLE.COM",
        "port": 993,
        "username": "imap-user@example.com",
        "password": "fake-imap-password",
        "folder": "INBOX",
        "use_ssl": True,
    }
    payload.update(overrides)
    return payload


def test_imap_connect_requires_authenticated_user() -> None:
    response = TestClient(app).post("/api/auth/imap/connect", json=_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_imap_connect_creates_mailbox_and_encrypted_credential(monkeypatch) -> None:
    client, user_id = _register_client()
    checked_passwords: list[str] = []

    def fake_check_connection(self, password: str) -> None:
        checked_passwords.append(password)

    monkeypatch.setattr(
        "app.services.imap_mailbox_service.ImapProvider.check_connection",
        fake_check_connection,
    )

    response = client.post("/api/auth/imap/connect", json=_payload())

    assert response.status_code == 201
    assert checked_passwords == ["fake-imap-password"]
    assert "fake-imap-password" not in response.text
    mailbox_payload = response.json()["data"]["mailbox"]
    assert mailbox_payload["provider"] == "imap"
    assert mailbox_payload["account_email"] == "inboxuser@example.com"
    assert mailbox_payload["display_name"] == "Inbox User"
    assert mailbox_payload["provider_preset"] == "custom"
    assert mailbox_payload["credential_status"] == "present"
    assert mailbox_payload["provider_config"] == {
        "host": "imap.example.com",
        "port": 993,
        "use_ssl": True,
        "default_folder": "INBOX",
        "username": "imap-user@example.com",
    }
    assert mailbox_payload["capabilities"]["supports_password_auth"] is True

    with SessionLocal() as db:
        mailbox = db.scalar(
            select(Mailbox).where(Mailbox.user_id == user_id, Mailbox.provider == "imap")
        )
        assert mailbox is not None
        assert mailbox.provider_account_id == "imap.example.com:993:imap-user@example.com"
        assert mailbox.status == "active"
        credential = db.get(MailboxCredential, mailbox.id)
        assert credential is not None
        assert credential.credential_type == "imap_password"
        assert credential.refresh_token_encrypted is None
        assert credential.imap_password_encrypted != "fake-imap-password"
        assert (
            CredentialEncryptionService().decrypt(credential.imap_password_encrypted or "")
            == "fake-imap-password"
        )
        assert credential.credentials_json == {
            "provider_preset": "custom",
            "host": "imap.example.com",
            "port": 993,
            "username": "imap-user@example.com",
            "folder": "INBOX",
            "use_ssl": True,
        }


def test_imap_connect_updates_existing_mailbox_without_duplicate(monkeypatch) -> None:
    client, user_id = _register_client()

    monkeypatch.setattr(
        "app.services.imap_mailbox_service.ImapProvider.check_connection",
        lambda self, password: None,
    )

    first = client.post("/api/auth/imap/connect", json=_payload(password="first-password"))
    second = client.post(
        "/api/auth/imap/connect",
        json=_payload(password="second-password", display_name="Updated Inbox"),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    with SessionLocal() as db:
        mailboxes = db.scalars(
            select(Mailbox).where(Mailbox.user_id == user_id, Mailbox.provider == "imap")
        ).all()
        assert len(mailboxes) == 1
        assert mailboxes[0].display_name == "Updated Inbox"
        credential = db.get(MailboxCredential, mailboxes[0].id)
        assert credential is not None
        assert (
            CredentialEncryptionService().decrypt(credential.imap_password_encrypted or "")
            == "second-password"
        )


def test_imap_connect_creates_distinct_mailboxes_for_distinct_usernames(
    monkeypatch,
) -> None:
    client, user_id = _register_client()

    monkeypatch.setattr(
        "app.services.imap_mailbox_service.ImapProvider.check_connection",
        lambda self, password: None,
    )

    first = client.post(
        "/api/auth/imap/connect",
        json=_payload(
            account_email="first@example.com",
            username="first@example.com",
            display_name="First Inbox",
        ),
    )
    second = client.post(
        "/api/auth/imap/connect",
        json=_payload(
            account_email="second@example.com",
            username="second@example.com",
            display_name="Second Inbox",
        ),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    with SessionLocal() as db:
        mailboxes = db.scalars(
            select(Mailbox)
            .where(Mailbox.user_id == user_id, Mailbox.provider == "imap")
            .order_by(Mailbox.email_address.asc())
        ).all()
        assert [mailbox.email_address for mailbox in mailboxes] == [
            "first@example.com",
            "second@example.com",
        ]
        assert [mailbox.provider_account_id for mailbox in mailboxes] == [
            "imap.example.com:993:first@example.com",
            "imap.example.com:993:second@example.com",
        ]
