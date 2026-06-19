from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from app.db.models.mailbox import Mailbox
from app.db.session import SessionLocal
from app.main import app


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _register_client(prefix: str) -> tuple[TestClient, UUID]:
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={"email": _email(prefix), "password": "strong-password"},
    )
    assert response.status_code == 201
    user_id = UUID(response.json()["data"]["user"]["id"])
    return client, user_id


def _create_mailbox(user_id: UUID, *, email: str, account_id: str) -> UUID:
    with SessionLocal() as db:
        mailbox = Mailbox(
            user_id=user_id,
            provider="gmail",
            provider_account_id=account_id,
            email_address=email,
            display_name="Mailbox User",
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status="active",
        )
        db.add(mailbox)
        db.commit()
        return mailbox.id


def test_list_mailboxes_returns_only_current_user_mailboxes() -> None:
    client, user_id = _register_client("mailbox-list-current")
    _, other_user_id = _register_client("mailbox-list-other")
    owned_mailbox_id = _create_mailbox(
        user_id, email="owned@example.com", account_id="owned-account"
    )
    _create_mailbox(other_user_id, email="other@example.com", account_id="other-account")

    response = client.get("/api/mailboxes")

    assert response.status_code == 200
    mailboxes = response.json()["data"]["mailboxes"]
    assert [mailbox["id"] for mailbox in mailboxes] == [str(owned_mailbox_id)]
    assert mailboxes[0]["email_address"] == "owned@example.com"
    assert mailboxes[0]["status"] == "connected"


def test_get_mailbox_detail_blocks_access_to_other_users_mailbox() -> None:
    client, _ = _register_client("mailbox-detail-current")
    _, other_user_id = _register_client("mailbox-detail-other")
    other_mailbox_id = _create_mailbox(
        other_user_id, email="other-detail@example.com", account_id="other-detail-account"
    )

    response = client.get(f"/api/mailboxes/{other_mailbox_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
