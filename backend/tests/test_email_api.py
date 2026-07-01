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
from app.providers.base import ProviderEmailBody, ProviderError
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
    subject: str | None = None,
    from_address: str = "sender@example.com",
    snippet: str = "preview",
    body_text: str | None = None,
    body_cache_status: str = "not_cached",
    body_cache_error: str | None = None,
) -> UUID:
    with SessionLocal() as db:
        email = Email(
            user_id=user_id,
            mailbox_id=mailbox_id,
            provider="gmail",
            external_id=external_id,
            external_thread_id=f"thread-{external_id}",
            subject=subject or f"Subject {external_id}",
            from_address=from_address,
            to_addresses=["me@example.com"],
            cc_addresses=[],
            snippet=snippet,
            body_text=body_text,
            body_text_truncated=False,
            body_cache_status=body_cache_status,
            body_cache_error=body_cache_error,
            received_at=received_at or _current_test_received_at(),
            is_read=is_read,
            provider_labels=["INBOX"] if is_read else ["INBOX", "UNREAD"],
        )
        db.add(email)
        db.commit()
        return email.id


class FakeProvider:
    def __init__(self) -> None:
        self.body_calls = 0

    def refresh_access_token(self, refresh_token: str) -> str:
        assert refresh_token == "fake-refresh-token"
        return "fake-access-token"

    def get_message_body(self, access_token: str, message_id: str) -> ProviderEmailBody:
        assert access_token == "fake-access-token"
        self.body_calls += 1
        return ProviderEmailBody(
            body_text=f"Full body for {message_id}",
            body_html=None,
            body_text_truncated=False,
        )

    def mark_as_read(self, access_token: str, message_id: str) -> list[str]:
        assert access_token == "fake-access-token"
        assert message_id
        return ["INBOX"]

    def mark_as_unread(self, access_token: str, message_id: str) -> list[str]:
        assert access_token == "fake-access-token"
        assert message_id
        return ["INBOX", "UNREAD"]


class FailingBodyProvider(FakeProvider):
    def get_message_body(self, access_token: str, message_id: str) -> ProviderEmailBody:
        raise ProviderError("network_timeout", "Provider timed out.", 504)


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


def test_get_emails_requires_login() -> None:
    response = TestClient(app).get("/api/emails")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_get_emails_filters_by_read_state_mailbox_and_owner() -> None:
    client, user_id = _register_client("emails-query-current")
    _, other_user_id = _register_client("emails-query-other")
    mailbox_id = _create_mailbox(user_id, account_prefix="query-owned")
    other_owned_mailbox_id = _create_mailbox(user_id, account_prefix="query-owned-two")
    other_user_mailbox_id = _create_mailbox(other_user_id, account_prefix="query-other")
    unread_id = _create_email(
        user_id,
        mailbox_id,
        external_id="query-unread",
        is_read=False,
        received_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
    )
    _create_email(
        user_id,
        other_owned_mailbox_id,
        external_id="query-read-other-mailbox",
        is_read=True,
        received_at=datetime(2026, 6, 19, 9, 0, tzinfo=UTC),
    )
    _create_email(
        other_user_id,
        other_user_mailbox_id,
        external_id="query-other-user",
        is_read=False,
        received_at=datetime(2026, 6, 19, 8, 0, tzinfo=UTC),
    )

    response = client.get(
        "/api/emails",
        params={"is_read": "false", "mailbox_id": str(mailbox_id)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [email["id"] for email in data["emails"]] == [str(unread_id)]
    assert data["pagination"] == {
        "limit": 50,
        "offset": 0,
        "count": 1,
        "total": 1,
        "has_more": False,
    }
    assert "body_text" not in data["emails"][0]


def test_get_emails_filters_by_date_range_and_keyword() -> None:
    client, user_id = _register_client("emails-query-keyword")
    mailbox_id = _create_mailbox(user_id, account_prefix="query-keyword")
    matching_id = _create_email(
        user_id,
        mailbox_id,
        external_id="query-quarterly",
        is_read=True,
        received_at=datetime(2026, 6, 17, 9, 0, tzinfo=UTC),
        subject="Quarterly planning",
        from_address="alice@example.com",
        snippet="Please review the plan",
    )
    _create_email(
        user_id,
        mailbox_id,
        external_id="query-invoice",
        is_read=True,
        received_at=datetime(2026, 6, 18, 9, 0, tzinfo=UTC),
        subject="Invoice",
        snippet="Quarterly billing note outside the requested day",
    )

    response = client.get(
        "/api/emails",
        params={
            "received_from": "2026-06-17T00:00:00+00:00",
            "received_to": "2026-06-17T23:59:59+00:00",
            "q": "quarterly",
        },
    )

    assert response.status_code == 200
    assert [email["id"] for email in response.json()["data"]["emails"]] == [
        str(matching_id)
    ]


def test_get_emails_paginates_by_received_at_desc() -> None:
    client, user_id = _register_client("emails-query-pagination")
    mailbox_id = _create_mailbox(user_id, account_prefix="query-pagination")
    newest_id = _create_email(
        user_id,
        mailbox_id,
        external_id="query-newest",
        is_read=True,
        received_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    )
    middle_id = _create_email(
        user_id,
        mailbox_id,
        external_id="query-middle",
        is_read=True,
        received_at=datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
    )
    _create_email(
        user_id,
        mailbox_id,
        external_id="query-oldest",
        is_read=True,
        received_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
    )

    response = client.get("/api/emails", params={"limit": 2, "offset": 0})

    assert response.status_code == 200
    data = response.json()["data"]
    assert [email["id"] for email in data["emails"]] == [
        str(newest_id),
        str(middle_id),
    ]
    assert data["pagination"] == {
        "limit": 2,
        "offset": 0,
        "count": 2,
        "total": 3,
        "has_more": True,
    }


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
        user_id,
        mailbox_id,
        external_id="detail-owner",
        is_read=True,
        body_text="Body detail-owner",
        body_cache_status="cached",
    )

    response = client.get(f"/api/emails/{email_id}")

    assert response.status_code == 200
    email = response.json()["data"]["email"]
    assert email["id"] == str(email_id)
    assert email["body_text"] == "Body detail-owner"
    assert email["body_cache_status"] == "cached"


def test_cache_email_body_fetches_provider_when_not_cached(monkeypatch) -> None:
    client, user_id = _register_client("email-body-cache-fetch")
    mailbox_id = _create_mailbox(user_id, account_prefix="body-cache-fetch")
    email_id = _create_email(
        user_id,
        mailbox_id,
        external_id="cache-fetch",
        is_read=True,
        body_text=None,
        body_cache_status="not_cached",
    )
    provider = FakeProvider()
    monkeypatch.setattr("app.services.email_service.get_mailbox_provider", lambda _: provider)

    response = client.post(f"/api/emails/{email_id}/body-cache")

    assert response.status_code == 200
    email = response.json()["data"]["email"]
    assert email["body_text"] == "Full body for cache-fetch"
    assert email["body_cache_status"] == "cached"
    assert email["body_cache_source"] == "opened"
    assert email["body_cache_error"] is None
    assert provider.body_calls == 1
    with SessionLocal() as db:
        stored = db.get(Email, email_id)
        assert stored is not None
        assert stored.body_text == "Full body for cache-fetch"
        assert stored.body_cache_status == "cached"
        assert stored.body_cache_error is None


def test_cache_email_body_returns_cached_body_without_provider(monkeypatch) -> None:
    client, user_id = _register_client("email-body-cache-hit")
    mailbox_id = _create_mailbox(user_id, account_prefix="body-cache-hit")
    email_id = _create_email(
        user_id,
        mailbox_id,
        external_id="cache-hit",
        is_read=True,
        body_text="Already cached",
        body_cache_status="cached",
    )
    monkeypatch.setattr(
        "app.services.email_service.get_mailbox_provider",
        lambda _: (_ for _ in ()).throw(AssertionError("provider should not be called")),
    )

    response = client.post(f"/api/emails/{email_id}/body-cache")

    assert response.status_code == 200
    email = response.json()["data"]["email"]
    assert email["body_text"] == "Already cached"
    assert email["body_cache_status"] == "cached"


def test_cache_email_body_provider_failure_sets_failed_status(monkeypatch) -> None:
    client, user_id = _register_client("email-body-cache-fail")
    mailbox_id = _create_mailbox(user_id, account_prefix="body-cache-fail")
    email_id = _create_email(
        user_id,
        mailbox_id,
        external_id="cache-fail",
        is_read=True,
        body_text=None,
        body_cache_status="not_cached",
    )
    monkeypatch.setattr(
        "app.services.email_service.get_mailbox_provider",
        lambda _: FailingBodyProvider(),
    )

    response = client.post(f"/api/emails/{email_id}/body-cache")

    assert response.status_code == 200
    email = response.json()["data"]["email"]
    assert email["body_text"] is None
    assert email["body_cache_status"] == "failed"
    assert email["body_cache_error"] == "network_timeout"
    with SessionLocal() as db:
        stored = db.get(Email, email_id)
        assert stored is not None
        assert stored.body_cache_status == "failed"
        assert stored.body_cache_error == "network_timeout"


def test_cache_email_body_blocks_other_users_email(monkeypatch) -> None:
    client, _ = _register_client("email-body-cache-current")
    _, other_user_id = _register_client("email-body-cache-other")
    other_mailbox_id = _create_mailbox(other_user_id, account_prefix="body-cache-other")
    other_email_id = _create_email(
        other_user_id,
        other_mailbox_id,
        external_id="body-cache-other",
        is_read=True,
    )
    monkeypatch.setattr("app.services.email_service.get_mailbox_provider", lambda _: FakeProvider())

    response = client.post(f"/api/emails/{other_email_id}/body-cache")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


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
