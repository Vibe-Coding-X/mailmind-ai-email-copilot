from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.session import SessionLocal
from app.main import app
from app.services.credential_encryption_service import CredentialEncryptionService


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _register_client(email: str | None = None) -> tuple[TestClient, str]:
    client = TestClient(app)
    resolved_email = email or _email("gmail-user")
    response = client.post(
        "/api/auth/register",
        json={"email": resolved_email, "password": "strong-password"},
    )
    assert response.status_code == 201
    return client, resolved_email


def _extract_state(authorization_url: str) -> str:
    params = parse_qs(urlparse(authorization_url).query)
    state = params.get("state", [""])[0]
    assert state
    return state


def test_gmail_login_requires_authenticated_user() -> None:
    response = TestClient(app).get("/api/auth/gmail/login")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_gmail_login_returns_authorization_url_with_state() -> None:
    client, _ = _register_client()

    response = client.get("/api/auth/gmail/login")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "meta"}
    assert body["data"]["provider"] == "gmail"
    authorization_url = body["data"]["authorization_url"]
    assert authorization_url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert _extract_state(authorization_url)


def test_gmail_callback_rejects_invalid_state() -> None:
    client, _ = _register_client()

    response = client.get("/api/auth/gmail/callback?code=fake-code&state=invalid-state")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_gmail_callback_uses_mocked_google_clients_and_creates_mailbox(monkeypatch) -> None:
    client, _ = _register_client()
    login_response = client.get("/api/auth/gmail/login")
    state = _extract_state(login_response.json()["data"]["authorization_url"])

    def fake_exchange_code_for_tokens(*, code: str) -> dict[str, object]:
        assert code == "fake-code"
        return {
            "access_token": "fake-access-token",
            "refresh_token": "fake-refresh-token",
            "scope": "https://www.googleapis.com/auth/gmail.modify openid email profile",
        }

    def fake_get_userinfo(*, access_token: str) -> dict[str, str]:
        assert access_token == "fake-access-token"
        return {
            "sub": "google-sub-123",
            "email": "MailboxUser@Example.COM",
            "name": "Mailbox User",
        }

    monkeypatch.setattr(
        "app.services.gmail_oauth_service.exchange_code_for_tokens",
        fake_exchange_code_for_tokens,
    )
    monkeypatch.setattr(
        "app.services.gmail_oauth_service.fetch_google_userinfo",
        fake_get_userinfo,
    )

    response = client.get(f"/api/auth/gmail/callback?code=fake-code&state={state}")

    assert response.status_code == 200
    mailbox = response.json()["data"]["mailbox"]
    assert mailbox["provider"] == "gmail"
    assert mailbox["email_address"] == "mailboxuser@example.com"
    assert mailbox["provider_account_id"] == "google-sub-123"
    assert mailbox["status"] == "connected"
    assert "token" not in response.text.lower()

    with SessionLocal() as db:
        stored_mailbox = db.scalar(
            select(Mailbox).where(Mailbox.provider_account_id == "google-sub-123")
        )
        assert stored_mailbox is not None
        credential = db.get(MailboxCredential, stored_mailbox.id)
        assert credential is not None
        assert credential.refresh_token_encrypted != "fake-refresh-token"
        assert (
            CredentialEncryptionService().decrypt(credential.refresh_token_encrypted or "")
            == "fake-refresh-token"
        )


def test_gmail_callback_updates_existing_mailbox(monkeypatch) -> None:
    client, _ = _register_client()
    first_state = _extract_state(
        client.get("/api/auth/gmail/login").json()["data"]["authorization_url"]
    )
    second_state = _extract_state(
        client.get("/api/auth/gmail/login").json()["data"]["authorization_url"]
    )
    calls = iter(["first-refresh-token", "second-refresh-token"])

    monkeypatch.setattr(
        "app.services.gmail_oauth_service.exchange_code_for_tokens",
        lambda *, code: {
            "access_token": "fake-access-token",
            "refresh_token": next(calls),
            "scope": "https://www.googleapis.com/auth/gmail.modify openid email profile",
        },
    )
    monkeypatch.setattr(
        "app.services.gmail_oauth_service.fetch_google_userinfo",
        lambda *, access_token: {
            "sub": "google-sub-existing",
            "email": "updated@example.com",
            "name": "Updated User",
        },
    )

    first = client.get(f"/api/auth/gmail/callback?code=fake-code&state={first_state}")
    second = client.get(f"/api/auth/gmail/callback?code=fake-code&state={second_state}")

    assert first.status_code == 200
    assert second.status_code == 200

    with SessionLocal() as db:
        mailboxes = db.scalars(
            select(Mailbox).where(Mailbox.provider_account_id == "google-sub-existing")
        ).all()
        assert len(mailboxes) == 1
        credential = db.get(MailboxCredential, mailboxes[0].id)
        assert credential is not None
        assert (
            CredentialEncryptionService().decrypt(credential.refresh_token_encrypted or "")
            == "second-refresh-token"
        )


def test_gmail_disconnect_marks_current_user_mailbox_disconnected(monkeypatch) -> None:
    client, _ = _register_client()
    state = _extract_state(client.get("/api/auth/gmail/login").json()["data"]["authorization_url"])
    monkeypatch.setattr(
        "app.services.gmail_oauth_service.exchange_code_for_tokens",
        lambda *, code: {
            "access_token": "fake-access-token",
            "refresh_token": "fake-refresh-token",
            "scope": "https://www.googleapis.com/auth/gmail.modify openid email profile",
        },
    )
    monkeypatch.setattr(
        "app.services.gmail_oauth_service.fetch_google_userinfo",
        lambda *, access_token: {
            "sub": "google-sub-disconnect",
            "email": "disconnect@example.com",
            "name": "Disconnect User",
        },
    )
    callback = client.get(f"/api/auth/gmail/callback?code=fake-code&state={state}")
    assert callback.status_code == 200

    response = client.post("/api/auth/gmail/disconnect")

    assert response.status_code == 200
    assert "token" not in response.text.lower()
    mailbox_id = callback.json()["data"]["mailbox"]["id"]
    with SessionLocal() as db:
        mailbox = db.get(Mailbox, mailbox_id)
        credential = db.get(MailboxCredential, mailbox_id)
        assert mailbox is not None
        assert mailbox.status == "disconnected"
        assert credential is not None
        assert credential.refresh_token_encrypted is None
