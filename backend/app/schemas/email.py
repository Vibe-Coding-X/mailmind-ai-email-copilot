from __future__ import annotations

from typing import Any

from app.db.models.email import Email


def email_summary_payload(email: Email) -> dict[str, Any]:
    return {
        "id": email.id,
        "mailbox_id": email.mailbox_id,
        "provider": email.provider,
        "external_id": email.external_id,
        "thread_id": email.external_thread_id,
        "subject": email.subject,
        "sender": email.from_address,
        "recipients": email.to_addresses,
        "snippet": email.snippet,
        "received_at": email.received_at,
        "is_read": email.is_read,
        "labels": email.provider_labels,
    }


def email_detail_payload(email: Email) -> dict[str, Any]:
    payload = email_summary_payload(email)
    payload["body_text"] = email.body_text
    return payload
