from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping
from uuid import UUID

from app.db.models.email import Email
from app.db.models.mailbox import Mailbox


ALLOWED_ITEM_TYPES = {"email", "todo", "risk"}
ALLOWED_SECTIONS = {"urgent", "review", "ignore", "todo", "risk"}
ALLOWED_CATEGORIES = {"work", "notification", "marketing", "social", "other"}
ALLOWED_ACTIONS = {
    "reply_today",
    "review_today",
    "handle_before_deadline",
    "ignore",
    "archive_candidate",
    "follow_up_later",
    "no_action_required",
}
ALLOWED_PRIORITIES = {"high", "medium", "low"}
DEFAULT_SUMMARY = "No digest items were returned."
DEFAULT_CONFIDENCE = 0.5
LABEL_SEPARATOR_RE = re.compile(r"[^a-z0-9]+")
FENCED_JSON_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.IGNORECASE | re.DOTALL)
PRIORITY_ALIASES = {
    "critical": "high",
    "urgent": "high",
    "important": "high",
    "high": "high",
    "normal": "medium",
    "moderate": "medium",
    "medium": "medium",
    "minor": "low",
    "low": "low",
}
ACTION_ALIASES = {
    "reply": "reply_today",
    "reply_today": "reply_today",
    "review": "review_today",
    "review_today": "review_today",
    "handle_before_deadline": "handle_before_deadline",
    "ignore": "ignore",
    "archive": "archive_candidate",
    "archive_candidate": "archive_candidate",
    "follow_up": "follow_up_later",
    "follow_up_later": "follow_up_later",
    "none": "no_action_required",
    "no_action": "no_action_required",
    "no_action_required": "no_action_required",
}
SECTION_ALIASES = {
    "urgent": "urgent",
    "important": "urgent",
    "review": "review",
    "needs_review": "review",
    "ignore": "ignore",
    "low_value": "ignore",
    "todo": "todo",
    "task": "todo",
    "risk": "risk",
}
ITEM_TYPE_ALIASES = {
    "email": "email",
    "mail": "email",
    "message": "email",
    "todo": "todo",
    "task": "todo",
    "risk": "risk",
}
CATEGORY_ALIASES = {
    "work": "work",
    "business": "work",
    "notification": "notification",
    "update": "notification",
    "marketing": "marketing",
    "promo": "marketing",
    "social": "social",
    "personal": "social",
    "other": "other",
}
FIELD_ALIASES = {
    "email_id": ("emailId", "emailID"),
    "mailbox_id": ("mailboxId", "mailboxID"),
    "item_type": ("type", "itemType"),
    "suggested_action": ("action", "suggestedAction"),
    "priority": ("priority_level", "priorityLevel"),
}


class DigestParseError(ValueError):
    pass


@dataclass(slots=True)
class ParsedDigestItem:
    mailbox_id: UUID | None
    email_id: UUID | None
    item_type: str
    section: str
    title: str
    summary: str | None
    category: str | None
    suggested_action: str | None
    priority: str
    reason: str | None
    deadline: date | None
    confidence: float


@dataclass(slots=True)
class ParsedDigestOutput:
    overview: dict[str, Any]
    items: list[ParsedDigestItem]
    output_json: dict[str, Any]


def parse_digest_output(
    raw_text: str,
    emails_by_external_id: Mapping[str, Email | UUID],
    *,
    default_mailbox_id: UUID | None = None,
    allowed_mailboxes: Mapping[UUID, Mailbox] | None = None,
) -> ParsedDigestOutput:
    payload = _load_payload(raw_text, emails_by_external_id)
    if not isinstance(payload, dict):
        raise DigestParseError("Digest output must be a JSON object.")

    mailboxes_by_id = allowed_mailboxes or {}
    overview = _parse_overview(
        payload.get("overview"),
        len(emails_by_external_id),
        mailboxes_by_id=mailboxes_by_id,
    )
    raw_items = payload.get("items", [])
    if raw_items is None:
        raw_items = []
    if not isinstance(raw_items, list):
        raise DigestParseError("Digest items must be an array.")

    items = [
        _parse_item(
            index,
            item,
            emails_by_external_id,
            default_mailbox_id=default_mailbox_id,
            allowed_mailboxes=mailboxes_by_id,
        )
        for index, item in enumerate(raw_items)
    ]
    normalized_output = {
        "overview": overview,
        "items": [_item_to_output_json(item) for item in items],
    }
    return ParsedDigestOutput(
        overview=overview,
        items=items,
        output_json=normalized_output,
    )


def _load_payload(
    raw_text: str,
    emails_by_external_id: Mapping[str, Email | UUID],
) -> dict[str, Any]:
    json_text = _extract_json_text(raw_text)
    if json_text is None:
        return {
            "overview": {
                "mail_count": len(emails_by_external_id),
                "summary": DEFAULT_SUMMARY,
            },
            "items": [],
        }
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise DigestParseError("Digest output must be valid JSON.") from exc


def _extract_json_text(raw_text: str) -> str | None:
    text = raw_text.strip()
    if not text:
        return None
    fenced_match = FENCED_JSON_RE.match(text)
    if fenced_match:
        return fenced_match.group(1).strip()
    if text.startswith("{"):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def _parse_overview(
    value: object,
    fallback_mail_count: int,
    *,
    mailboxes_by_id: Mapping[UUID, Mailbox],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {
            "mail_count": fallback_mail_count,
            "summary": DEFAULT_SUMMARY,
            "overall_summary": DEFAULT_SUMMARY,
            "mailbox_summaries": [],
        }
    mail_count = _nonnegative_int(value.get("mail_count"), fallback_mail_count)
    summary = value.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        summary = DEFAULT_SUMMARY
    overall_summary = value.get("overall_summary")
    if not isinstance(overall_summary, str) or not overall_summary.strip():
        overall_summary = summary
    return {
        "mail_count": mail_count,
        "summary": summary,
        "overall_summary": overall_summary,
        "mailbox_summaries": _parse_mailbox_summaries(
            value.get("mailbox_summaries"),
            mailboxes_by_id=mailboxes_by_id,
        ),
    }


def _parse_item(
    index: int,
    value: object,
    emails_by_external_id: Mapping[str, Email | UUID],
    *,
    default_mailbox_id: UUID | None,
    allowed_mailboxes: Mapping[UUID, Mailbox],
) -> ParsedDigestItem:
    if not isinstance(value, dict):
        raise DigestParseError(f"items[{index}] must be an object.")

    raw_email_id = _field_value(value, "email_id")
    item_type = _enum_value(
        value,
        "item_type",
        ALLOWED_ITEM_TYPES,
        index,
        default="email" if raw_email_id is not None else "todo",
        aliases=ITEM_TYPE_ALIASES,
    )
    section = _enum_value(
        value,
        "section",
        ALLOWED_SECTIONS,
        index,
        default=_default_section(item_type),
        aliases=SECTION_ALIASES,
    )
    section = _coerce_section_item_type(section=section, item_type=item_type)
    title = _string_with_default(
        value,
        "title",
        _first_nonblank(
            value.get("summary"),
            value.get("reason"),
            "Digest item",
        ),
    )
    priority = _enum_value(
        value,
        "priority",
        ALLOWED_PRIORITIES,
        index,
        default="medium",
        aliases=PRIORITY_ALIASES,
    )
    confidence = _confidence(value)
    email_id, email_mailbox_id = _resolve_email_id(
        raw_email_id,
        item_type,
        emails_by_external_id,
        index,
    )
    mailbox_id = _resolve_mailbox_id(
        raw_mailbox_id=_field_value(value, "mailbox_id"),
        email_mailbox_id=email_mailbox_id,
        default_mailbox_id=default_mailbox_id,
        allowed_mailboxes=allowed_mailboxes,
        index=index,
    )

    category = _enum_value(
        value,
        "category",
        ALLOWED_CATEGORIES,
        index,
        default="other",
        aliases=CATEGORY_ALIASES,
    )
    suggested_action = _enum_value(
        value,
        "suggested_action",
        ALLOWED_ACTIONS,
        index,
        default="no_action_required",
        aliases=ACTION_ALIASES,
    )
    return ParsedDigestItem(
        mailbox_id=mailbox_id,
        email_id=email_id,
        item_type=item_type,
        section=section,
        title=title,
        summary=_optional_string(value, "summary", index),
        category=category,
        suggested_action=suggested_action,
        priority=priority,
        reason=_optional_string(value, "reason", index),
        deadline=_optional_date(value, "deadline", index),
        confidence=confidence,
    )


def _string_with_default(value: dict[str, Any], key: str, default: str) -> str:
    raw_value = value.get(key)
    if not isinstance(raw_value, str) or not raw_value.strip():
        return default
    return raw_value.strip()


def _optional_string(value: dict[str, Any], key: str, index: int) -> str | None:
    raw_value = value.get(key)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raise DigestParseError(f"items[{index}].{key} must be a string or null.")
    return raw_value


def _enum_value(
    value: dict[str, Any],
    key: str,
    allowed: set[str],
    index: int,
    *,
    default: str,
    aliases: Mapping[str, str] | None = None,
) -> str:
    raw_value = _field_value(value, key)
    if not isinstance(raw_value, str) or not raw_value.strip():
        return default
    normalized = _normalize_label(raw_value)
    if aliases and normalized in aliases:
        normalized = aliases[normalized]
    if normalized in allowed:
        return normalized
    return default


def _field_value(value: dict[str, Any], key: str) -> object:
    if key in value:
        return value[key]
    for alias in FIELD_ALIASES.get(key, ()):
        if alias in value:
            return value[alias]
    return None


def _confidence(value: dict[str, Any]) -> float:
    raw_confidence = value.get("confidence")
    if isinstance(raw_confidence, str):
        try:
            confidence = float(raw_confidence)
        except ValueError:
            return DEFAULT_CONFIDENCE
    elif isinstance(raw_confidence, (int, float)):
        confidence = float(raw_confidence)
    else:
        return DEFAULT_CONFIDENCE
    return min(max(confidence, 0.0), 1.0)


def _optional_date(value: dict[str, Any], key: str, index: int) -> date | None:
    raw_value = value.get(key)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raise DigestParseError(f"items[{index}].{key} must be YYYY-MM-DD or null.")
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        return None


def _resolve_email_id(
    external_id: object,
    item_type: str,
    emails_by_external_id: Mapping[str, Email | UUID],
    index: int,
) -> tuple[UUID | None, UUID | None]:
    if external_id is None:
        if item_type == "email":
            raise DigestParseError(f"items[{index}].email_id is required for email items.")
        return None, None
    if not isinstance(external_id, str) or not external_id:
        raise DigestParseError(f"items[{index}].email_id must be a string or null.")
    email = emails_by_external_id.get(external_id)
    if email is None:
        raise DigestParseError(f"Unknown email_id: {external_id}")
    if isinstance(email, Email):
        return email.id, email.mailbox_id
    return email, None


def _resolve_mailbox_id(
    *,
    raw_mailbox_id: object,
    email_mailbox_id: UUID | None,
    default_mailbox_id: UUID | None,
    allowed_mailboxes: Mapping[UUID, Mailbox],
    index: int,
) -> UUID | None:
    if email_mailbox_id is not None:
        return email_mailbox_id
    if raw_mailbox_id is not None:
        try:
            mailbox_id = UUID(str(raw_mailbox_id))
        except ValueError as exc:
            raise DigestParseError(f"items[{index}].mailbox_id must be a UUID or null.") from exc
        if allowed_mailboxes and mailbox_id not in allowed_mailboxes:
            raise DigestParseError(f"items[{index}].mailbox_id was not provided as input.")
        return mailbox_id
    if default_mailbox_id is not None:
        return default_mailbox_id
    if not allowed_mailboxes:
        return None
    raise DigestParseError(f"items[{index}].mailbox_id is required for all-mailbox items.")


def _parse_mailbox_summaries(
    value: object,
    *,
    mailboxes_by_id: Mapping[UUID, Mailbox],
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    summaries: list[dict[str, Any]] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        raw_mailbox_id = _field_value(entry, "mailbox_id")
        if not isinstance(raw_mailbox_id, str):
            continue
        try:
            mailbox_id = UUID(raw_mailbox_id)
        except ValueError:
            continue
        mailbox = mailboxes_by_id.get(mailbox_id)
        provider = _optional_summary_text(entry.get("provider")) or (
            mailbox.provider.strip().lower() if mailbox is not None else None
        )
        account_email = _optional_summary_text(entry.get("account_email")) or (
            mailbox.email_address if mailbox is not None else None
        )
        title = _optional_summary_text(entry.get("title")) or (
            mailbox.display_name or mailbox.email_address if mailbox is not None else None
        )
        summary = _optional_summary_text(entry.get("summary")) or DEFAULT_SUMMARY
        highlights = entry.get("highlights")
        normalized_highlights = [
            highlight.strip()
            for highlight in highlights
            if isinstance(highlight, str) and highlight.strip()
        ] if isinstance(highlights, list) else []
        summaries.append(
            {
                "mailbox_id": str(mailbox_id),
                "provider": provider,
                "account_email": account_email,
                "title": title,
                "summary": summary,
                "highlights": normalized_highlights,
            }
        )
    return summaries


def _optional_summary_text(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _coerce_section_item_type(*, section: str, item_type: str) -> str:
    if section == "todo" and item_type != "todo":
        return _default_section(item_type)
    if section == "risk" and item_type != "risk":
        return _default_section(item_type)
    if section in {"urgent", "review", "ignore"} and item_type != "email":
        return _default_section(item_type)
    return section


def _default_section(item_type: str) -> str:
    if item_type == "todo":
        return "todo"
    if item_type == "risk":
        return "risk"
    return "review"


def _normalize_label(value: str) -> str:
    return LABEL_SEPARATOR_RE.sub("_", value.strip().lower()).strip("_")


def _nonnegative_int(value: object, default: int) -> int:
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, str):
        try:
            parsed = int(value)
        except ValueError:
            return default
        return parsed if parsed >= 0 else default
    return default


def _first_nonblank(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Digest item"


def _item_to_output_json(item: ParsedDigestItem) -> dict[str, Any]:
    return {
        "mailbox_id": str(item.mailbox_id) if item.mailbox_id else None,
        "email_id": str(item.email_id) if item.email_id else None,
        "item_type": item.item_type,
        "section": item.section,
        "title": item.title,
        "summary": item.summary,
        "category": item.category,
        "suggested_action": item.suggested_action,
        "priority": item.priority,
        "reason": item.reason,
        "deadline": item.deadline.isoformat() if item.deadline else None,
        "confidence": item.confidence,
    }
