from __future__ import annotations

from typing import Any

from app.db.models.mailbox import Mailbox
from app.providers.registry import get_mailbox_provider


def mailbox_status_for_api(status: str) -> str:
    if status == "active":
        return "connected"
    return status


def mailbox_payload(mailbox: Mailbox) -> dict[str, Any]:
    sync_cursor = mailbox.sync_cursor or None
    provider = mailbox.provider.strip().lower()
    return {
        "id": mailbox.id,
        "provider": provider,
        "email_address": mailbox.email_address,
        "account_email": mailbox.email_address,
        "display_name": mailbox.display_name,
        "provider_account_id": mailbox.provider_account_id,
        "status": mailbox_status_for_api(mailbox.status),
        "last_successful_sync_at": mailbox.last_successful_sync_at,
        "capabilities": mailbox_capabilities_payload(provider),
        "sync_cursor": sync_cursor,
        "created_at": mailbox.created_at,
        "updated_at": mailbox.updated_at,
    }


def mailbox_capabilities_payload(provider_key: str) -> dict[str, bool]:
    provider = get_mailbox_provider(provider_key)
    return provider.get_capabilities().as_dict()
