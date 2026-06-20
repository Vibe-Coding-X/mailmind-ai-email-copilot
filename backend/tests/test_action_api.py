from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.db.models.daily_digest import DailyDigest
from app.db.models.digest_item import DigestItem
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.session import SessionLocal
from app.main import app
from app.services.user_action_service import record_completed_action


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


def _create_digest_item(user_id: UUID, mailbox_id: UUID, *, prefix: str) -> UUID:
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)
    with SessionLocal() as db:
        digest = DailyDigest(
            user_id=user_id,
            mailbox_id=mailbox_id,
            digest_date=date(2026, 6, 19),
            version=1,
            is_current=True,
            status="fresh",
            trigger_source="manual",
            generation_started_at=now,
            generated_at=now,
            coverage_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
            coverage_end=now,
            mail_count=0,
            overview_json={"summary": "summary"},
        )
        db.add(digest)
        db.flush()
        item = DigestItem(
            digest_id=digest.id,
            user_id=user_id,
            mailbox_id=mailbox_id,
            item_type="todo",
            section="todo",
            title=f"{prefix} todo",
            priority="medium",
            confidence=Decimal("0.800"),
            display_order=0,
        )
        db.add(item)
        db.commit()
        return item.id


def _create_email(user_id: UUID, mailbox_id: UUID, *, prefix: str) -> UUID:
    with SessionLocal() as db:
        email = Email(
            user_id=user_id,
            mailbox_id=mailbox_id,
            provider="gmail",
            external_id=f"{prefix}-gmail",
            external_thread_id=f"{prefix}-thread",
            subject=f"{prefix} subject",
            from_address="sender@example.com",
            to_addresses=["me@example.com"],
            cc_addresses=[],
            snippet="preview",
            body_text="body",
            body_text_truncated=False,
            received_at=datetime.now(UTC),
            is_read=False,
            provider_labels=["INBOX", "UNREAD"],
        )
        db.add(email)
        db.commit()
        return email.id


def test_list_actions_requires_login() -> None:
    response = TestClient(app).get("/api/actions")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_create_action_records_sanitized_current_user_action() -> None:
    client, user_id = _register_client("action-create")
    mailbox_id = _create_mailbox(user_id, prefix="action-create")

    response = client.post(
        "/api/actions",
        json={
            "mailbox_id": str(mailbox_id),
            "action_type": "open_email_detail",
            "source": "email_detail",
            "provider_effect": "none",
            "before_state": {"access_token": "secret", "view": "summary"},
        },
    )

    assert response.status_code == 200
    action = response.json()["data"]["action"]
    assert action["user_id"] == str(user_id)
    assert action["action_type"] == "open_email_detail"
    assert action["before_state"] == {"view": "summary"}


def test_create_action_rejects_cross_user_email_id() -> None:
    client, user_id = _register_client("action-create-cross-owner")
    _, other_user_id = _register_client("action-create-cross-other")
    mailbox_id = _create_mailbox(user_id, prefix="action-create-cross-owner")
    other_mailbox_id = _create_mailbox(
        other_user_id,
        prefix="action-create-cross-other",
    )
    other_email_id = _create_email(
        other_user_id,
        other_mailbox_id,
        prefix="action-create-cross-other",
    )

    response = client.post(
        "/api/actions",
        json={
            "mailbox_id": str(mailbox_id),
            "email_id": str(other_email_id),
            "action_type": "open_email_detail",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_list_actions_returns_current_user_actions_with_filters() -> None:
    client, user_id = _register_client("action-api-owner")
    _, other_user_id = _register_client("action-api-other")
    mailbox_id = _create_mailbox(user_id, prefix="action-api-owner")
    other_mailbox_id = _create_mailbox(other_user_id, prefix="action-api-other")

    with SessionLocal() as db:
        expected = record_completed_action(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            action_type="mark_done",
            source="dashboard",
        )
        record_completed_action(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            action_type="dismiss_item",
            source="dashboard",
        )
        record_completed_action(
            db,
            user_id=other_user_id,
            mailbox_id=other_mailbox_id,
            action_type="mark_done",
            source="dashboard",
        )
        db.commit()
        expected_id = expected.id

    response = client.get("/api/actions?action_type=mark_done&status=executed&limit=10")

    assert response.status_code == 200
    actions = response.json()["data"]["actions"]
    assert [action["id"] for action in actions] == [str(expected_id)]
    assert actions[0]["action_type"] == "mark_done"
    assert actions[0]["action_status"] == "executed"


def test_list_actions_paginates_and_filters_by_provider_effect_and_date() -> None:
    client, user_id = _register_client("action-api-page")
    mailbox_id = _create_mailbox(user_id, prefix="action-api-page")

    with SessionLocal() as db:
        newest = record_completed_action(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            action_type="mark_read",
            source="email_detail",
            provider_effect="gmail_synced",
            now=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
        )
        record_completed_action(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            action_type="mark_unread",
            source="email_detail",
            provider_effect="gmail_synced",
            now=datetime(2026, 6, 19, 11, 0, tzinfo=UTC),
        )
        record_completed_action(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            action_type="mark_done",
            source="dashboard",
            provider_effect="local_only",
            now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )
        db.commit()
        newest_id = newest.id

    response = client.get(
        "/api/actions",
        params={
            "provider_effect": "gmail_synced",
            "created_from": "2026-06-19T00:00:00+00:00",
            "created_to": "2026-06-19T23:59:59+00:00",
            "limit": 1,
            "offset": 0,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [action["id"] for action in data["actions"]] == [str(newest_id)]
    assert data["pagination"] == {
        "limit": 1,
        "offset": 0,
        "count": 1,
        "has_more": True,
    }


def test_list_actions_filters_by_related_email_resource() -> None:
    client, user_id = _register_client("action-api-related")
    mailbox_id = _create_mailbox(user_id, prefix="action-api-related")
    email_id = _create_email(user_id, mailbox_id, prefix="action-api-related")

    with SessionLocal() as db:
        expected = record_completed_action(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            email_id=email_id,
            action_type="open_email_detail",
            source="email_detail",
            provider_effect="none",
        )
        record_completed_action(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            action_type="mark_done",
            source="dashboard",
            provider_effect="local_only",
        )
        db.commit()
        expected_id = expected.id

    response = client.get(
        "/api/actions",
        params={
            "related_resource_type": "email",
            "related_resource_id": str(email_id),
        },
    )

    assert response.status_code == 200
    actions = response.json()["data"]["actions"]
    assert [action["id"] for action in actions] == [str(expected_id)]


def test_get_action_detail_blocks_other_users_action() -> None:
    owner_client, owner_id = _register_client("action-detail-owner")
    other_client, _ = _register_client("action-detail-other")
    mailbox_id = _create_mailbox(owner_id, prefix="action-detail-owner")

    with SessionLocal() as db:
        action = record_completed_action(
            db,
            user_id=owner_id,
            mailbox_id=mailbox_id,
            action_type="mark_done",
            source="dashboard",
        )
        db.commit()
        action_id = action.id

    owner_response = owner_client.get(f"/api/actions/{action_id}")
    assert owner_response.status_code == 200
    assert owner_response.json()["data"]["action"]["id"] == str(action_id)

    other_response = other_client.get(f"/api/actions/{action_id}")
    assert other_response.status_code == 404
    assert other_response.json()["error"]["code"] == "INVALID_REQUEST"


def test_get_digest_item_actions_returns_current_user_item_actions() -> None:
    client, user_id = _register_client("action-item-list")
    mailbox_id = _create_mailbox(user_id, prefix="action-item-list")
    item_id = _create_digest_item(user_id, mailbox_id, prefix="action-item-list")

    with SessionLocal() as db:
        action = record_completed_action(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            digest_item_id=item_id,
            action_type="mark_done",
            source="dashboard",
        )
        db.commit()
        action_id = action.id

    response = client.get(f"/api/actions/digest-items/{item_id}")

    assert response.status_code == 200
    actions = response.json()["data"]["actions"]
    assert [action["id"] for action in actions] == [str(action_id)]
