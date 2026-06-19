from __future__ import annotations

from typing import Any

from app.db.models.user_action import UserAction


def user_action_payload(action: UserAction, *, detail: bool = False) -> dict[str, Any]:
    payload = {
        "id": action.id,
        "user_id": action.user_id,
        "mailbox_id": action.mailbox_id,
        "digest_id": action.digest_id,
        "digest_item_id": action.digest_item_id,
        "email_id": action.email_id,
        "action_type": action.action_type,
        "action_status": action.action_status,
        "source": action.source,
        "provider_effect": action.provider_effect,
        "created_at": action.created_at,
        "executed_at": action.executed_at,
    }
    if detail:
        payload.update(
            {
                "before_state": action.before_state,
                "after_state": action.after_state,
                "error_code": action.error_code,
                "error_message": action.error_message,
            }
        )
    return payload
