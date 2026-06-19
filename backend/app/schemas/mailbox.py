from __future__ import annotations

from typing import Any

from app.db.models.mailbox import Mailbox


def mailbox_status_for_api(status: str) -> str:
    if status == "active":
        return "connected"
    return status


def mailbox_payload(mailbox: Mailbox) -> dict[str, Any]:
    sync_cursor = mailbox.sync_cursor or None
    return {
        "id": mailbox.id,
        "provider": mailbox.provider,
        "email_address": mailbox.email_address,
        "provider_account_id": mailbox.provider_account_id,
        "status": mailbox_status_for_api(mailbox.status),
        "last_successful_sync_at": mailbox.last_successful_sync_at,
        "sync_cursor": sync_cursor,
        "created_at": mailbox.created_at,
        "updated_at": mailbox.updated_at,
    }
