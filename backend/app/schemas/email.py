from __future__ import annotations

from typing import Any

from app.db.models.email import Email
from app.db.models.mailbox_archive_state import MailboxArchiveState


def email_summary_payload(email: Email) -> dict[str, Any]:
    mailbox = email.mailbox
    return {
        "id": email.id,
        "mailbox_id": email.mailbox_id,
        "provider": email.provider,
        "mailbox_email": mailbox.email_address if mailbox is not None else None,
        "mailbox_display_name": mailbox.display_name if mailbox is not None else None,
        "external_id": email.external_id,
        "thread_id": email.external_thread_id,
        "subject": email.subject,
        "sender_name": email.from_name,
        "sender": email.from_address,
        "sender_email": email.from_address,
        "recipients": email.to_addresses,
        "cc": email.cc_addresses,
        "snippet": email.snippet,
        "received_at": email.received_at,
        "sent_at": email.sent_at,
        "is_read": email.is_read,
        "is_starred": email.is_starred,
        "has_attachments": email.has_attachments,
        "labels": email.provider_labels,
        "body_cache_status": email.body_cache_status,
        "body_cache_error": email.body_cache_error,
    }


def email_detail_payload(email: Email) -> dict[str, Any]:
    payload = email_summary_payload(email)
    payload["body_text"] = email.body_text
    payload["body_html"] = email.body_html
    payload["body_cached_at"] = email.body_cached_at
    payload["body_cache_source"] = email.body_cache_source
    return payload


def archive_state_payload(state: MailboxArchiveState | None) -> dict[str, Any]:
    if state is None:
        return {
            "status": "not_started",
            "is_complete": False,
            "total_synced_count": 0,
            "batch_count": 0,
            "newest_synced_at": None,
            "oldest_synced_at": None,
            "last_error_code": None,
            "last_error_message": None,
            "started_at": None,
            "completed_at": None,
            "message": "Local archive has not started.",
        }
    return {
        "mailbox_id": state.mailbox_id,
        "status": state.status,
        "is_complete": state.status == "complete",
        "total_synced_count": state.total_synced_count,
        "batch_count": state.batch_count,
        "newest_synced_at": state.newest_synced_at,
        "oldest_synced_at": state.oldest_synced_at,
        "last_error_code": state.last_error_code,
        "last_error_message": state.last_error_message,
        "started_at": state.started_at,
        "completed_at": state.completed_at,
        "message": archive_state_message(state),
    }


def archive_state_message(state: MailboxArchiveState) -> str:
    if state.status == "running":
        return "Local archive is still syncing. Results may be incomplete."
    if state.status == "partial":
        return "Local archive is partially synced. Resume to continue backfilling older mail."
    if state.status == "failed":
        return "Local archive sync failed. Retry to continue from the saved checkpoint."
    if state.status == "complete":
        return "Local archive sync is complete."
    return "Local archive has not started."
