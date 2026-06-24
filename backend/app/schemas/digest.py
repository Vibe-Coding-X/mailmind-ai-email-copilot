from __future__ import annotations

from typing import Any

from app.db.models.daily_digest import DailyDigest
from app.db.models.digest_item import DigestItem
from app.db.models.mailbox import Mailbox


def digest_mailbox_source_payload(mailbox: Mailbox | None) -> dict[str, Any] | None:
    if mailbox is None:
        return None
    provider = mailbox.provider.strip().lower()
    title = mailbox.display_name or mailbox.email_address
    return {
        "id": mailbox.id,
        "provider": provider,
        "account_email": mailbox.email_address,
        "display_name": mailbox.display_name,
        "title": title,
    }


def digest_item_payload(item: DigestItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "digest_id": item.digest_id,
        "mailbox_id": item.mailbox_id,
        "email_id": item.email_id,
        "item_type": item.item_type,
        "section": item.section,
        "title": item.title,
        "summary": item.summary,
        "category": item.category,
        "suggested_action": item.suggested_action,
        "priority": item.priority,
        "reason": item.reason,
        "deadline": item.deadline,
        "confidence": float(item.confidence),
        "display_order": item.display_order,
        "source_mailbox": digest_mailbox_source_payload(item.mailbox),
    }


def digest_payload(digest: DailyDigest) -> dict[str, Any]:
    overview = digest.overview_json or {}
    items = sorted(digest.items, key=lambda item: (item.section, item.display_order))
    return {
        "id": digest.id,
        "scope_type": digest.scope_type,
        "mailbox_id": digest.mailbox_id,
        "digest_date": digest.digest_date,
        "version": digest.version,
        "is_current": digest.is_current,
        "status": digest.status,
        "trigger_source": digest.trigger_source,
        "coverage_start": digest.coverage_start,
        "coverage_end": digest.coverage_end,
        "generated_at": digest.generated_at,
        "mail_count": digest.mail_count,
        "new_mail_count_after_digest": digest.new_mail_count_after_digest,
        "overview": overview,
        "summary": overview.get("overall_summary") or overview.get("summary"),
        "mailbox_summaries": overview.get("mailbox_summaries") or [],
        "items": [digest_item_payload(item) for item in items],
    }
