from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models.daily_digest import DailyDigest
from app.db.models.digest_item import DigestItem
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.user_action import UserAction
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
    return client, UUID(response.json()["data"]["user"]["id"])


def _create_digest_item(user_id: UUID, *, prefix: str) -> UUID:
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)
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
        email = Email(
            user_id=user_id,
            mailbox_id=mailbox.id,
            provider="gmail",
            external_id=f"{prefix}-gmail",
            external_thread_id=f"{prefix}-thread",
            subject="Digest action email",
            from_address="sender@example.com",
            to_addresses=["me@example.com"],
            cc_addresses=[],
            snippet="preview",
            body_text="body",
            body_text_truncated=False,
            received_at=now,
            is_read=False,
            provider_labels=["INBOX", "UNREAD"],
        )
        db.add(email)
        db.flush()
        digest = DailyDigest(
            user_id=user_id,
            mailbox_id=mailbox.id,
            digest_date=date(2026, 6, 19),
            version=1,
            is_current=True,
            status="fresh",
            trigger_source="manual",
            generation_started_at=now,
            generated_at=now,
            coverage_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
            coverage_end=now,
            mail_count=1,
            overview_json={"summary": "summary"},
        )
        db.add(digest)
        db.flush()
        item = DigestItem(
            digest_id=digest.id,
            user_id=user_id,
            mailbox_id=mailbox.id,
            email_id=email.id,
            item_type="email",
            section="review",
            title="Digest action email",
            summary="Review this email.",
            category="work",
            suggested_action="review_today",
            priority="medium",
            reason="Needs review.",
            confidence=Decimal("0.800"),
            display_order=0,
        )
        db.add(item)
        db.commit()
        return item.id


def test_digest_item_mark_done_dismiss_and_snooze_write_user_actions() -> None:
    client, user_id = _register_client("digest-action")
    item_id = _create_digest_item(user_id, prefix="digest-action")

    mark_done = client.post(f"/api/digest/items/{item_id}/mark-done")
    dismiss = client.post(f"/api/digest/items/{item_id}/dismiss")
    snooze = client.post(
        f"/api/digest/items/{item_id}/snooze",
        json={"snoozed_until": "2026-06-20T09:00:00Z"},
    )

    assert mark_done.status_code == 200
    assert dismiss.status_code == 200
    assert snooze.status_code == 200
    assert mark_done.json()["data"]["action"]["action_type"] == "mark_done"
    assert dismiss.json()["data"]["action"]["action_type"] == "dismiss_item"
    assert snooze.json()["data"]["action"]["action_type"] == "snooze_item"
    assert snooze.json()["data"]["action"]["after_state"] == {
        "snoozed_until": "2026-06-20T09:00:00Z"
    }

    with SessionLocal() as db:
        item = db.get(DigestItem, item_id)
        actions = list(
            db.scalars(
                select(UserAction)
                .where(UserAction.digest_item_id == item_id)
                .order_by(UserAction.created_at.asc())
            ).all()
        )
        assert item is not None
        assert item.section == "review"
        assert [action.action_type for action in actions] == [
            "mark_done",
            "dismiss_item",
            "snooze_item",
        ]


def test_digest_item_action_blocks_cross_user_access() -> None:
    client, _ = _register_client("digest-action-current")
    _, other_user_id = _register_client("digest-action-other")
    other_item_id = _create_digest_item(other_user_id, prefix="digest-action-other")

    response = client.post(f"/api/digest/items/{other_item_id}/mark-done")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    with SessionLocal() as db:
        assert (
            db.scalar(select(UserAction).where(UserAction.digest_item_id == other_item_id))
            is None
        )
