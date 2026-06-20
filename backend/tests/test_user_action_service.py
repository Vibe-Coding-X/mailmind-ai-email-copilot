from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.db.models.mailbox import Mailbox
from app.db.session import SessionLocal
from app.services.auth_service import register_user
from app.services.user_action_service import (
    UserActionServiceError,
    get_user_action,
    list_user_actions,
    record_completed_action,
    record_failed_action,
)


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _create_user_and_mailbox(prefix: str) -> tuple[UUID, UUID]:
    with SessionLocal() as db:
        user = register_user(
            db,
            email=_email(prefix),
            password="strong-password",
            timezone="Asia/Shanghai",
        )
        mailbox = Mailbox(
            user_id=user.id,
            provider="gmail",
            provider_account_id=f"{prefix}-{uuid4().hex}",
            email_address=_email(f"{prefix}-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status="active",
        )
        db.add(mailbox)
        db.commit()
        return user.id, mailbox.id


def test_record_completed_action_sanitizes_payload_and_sets_executed_status() -> None:
    user_id, mailbox_id = _create_user_and_mailbox("action-completed")
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)

    with SessionLocal() as db:
        action = record_completed_action(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            action_type="mark_done",
            source="dashboard",
            provider_effect="none",
            before_state={"token": "secret", "section": "todo"},
            after_state={"status": "done", "access_token": "secret"},
            now=now,
        )
        db.commit()
        action_id = action.id

    with SessionLocal() as db:
        stored = get_user_action(db, user_id=user_id, action_id=action_id)
        assert stored.action_status == "executed"
        assert stored.executed_at == now
        assert stored.before_state == {"section": "todo"}
        assert stored.after_state == {"status": "done"}


def test_record_completed_action_sanitizes_nested_cookies_and_body_text() -> None:
    user_id, mailbox_id = _create_user_and_mailbox("action-nested-redaction")

    with SessionLocal() as db:
        action = record_completed_action(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            action_type="mark_done",
            source="dashboard",
            provider_effect="none",
            before_state={
                "subject": "Keep this",
                "nested": {
                    "Cookie": "sessionid=session-secret-12345",
                    "body_text": "Full private email body",
                    "safe": "visible",
                },
                "items": [
                    {"api_key": "api-secret-12345", "status": "ok"},
                    {"authorization": "Bearer bearer-secret-12345", "count": 1},
                ],
            },
        )
        db.commit()
        action_id = action.id

    with SessionLocal() as db:
        stored = get_user_action(db, user_id=user_id, action_id=action_id)
        assert stored.before_state == {
            "subject": "Keep this",
            "nested": {"safe": "visible"},
            "items": [{"status": "ok"}, {"count": 1}],
        }


def test_record_failed_action_preserves_audit_without_swallowing_business_error() -> None:
    user_id, mailbox_id = _create_user_and_mailbox("action-failed")

    with SessionLocal() as db:
        action = record_failed_action(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            action_type="mark_read",
            source="email_detail",
            provider_effect="gmail_synced",
            error_code="PROVIDER_SYNC_FAILED",
            error_message="Gmail request failed.",
            before_state={"is_read": False},
        )
        db.commit()
        action_id = action.id

    with SessionLocal() as db:
        stored = get_user_action(db, user_id=user_id, action_id=action_id)
        assert stored.action_status == "failed"
        assert stored.error_code == "PROVIDER_SYNC_FAILED"
        assert stored.error_message == "Gmail request failed."
        assert stored.before_state == {"is_read": False}


def test_list_and_get_user_actions_are_limited_to_owner() -> None:
    owner_id, owner_mailbox_id = _create_user_and_mailbox("action-owner")
    other_id, other_mailbox_id = _create_user_and_mailbox("action-other")

    with SessionLocal() as db:
        owner_action = record_completed_action(
            db,
            user_id=owner_id,
            mailbox_id=owner_mailbox_id,
            action_type="mark_done",
            source="dashboard",
        )
        record_completed_action(
            db,
            user_id=other_id,
            mailbox_id=other_mailbox_id,
            action_type="dismiss_item",
            source="dashboard",
        )
        db.commit()
        owner_action_id = owner_action.id

    with SessionLocal() as db:
        actions = list_user_actions(db, user_id=owner_id)
        assert [action.id for action in actions] == [owner_action_id]

        with pytest.raises(UserActionServiceError) as exc_info:
            get_user_action(db, user_id=other_id, action_id=owner_action_id)
        assert exc_info.value.status_code == 404
