from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping
from uuid import UUID

from app.db.models.email import Email


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
ALLOWED_TOP_LEVEL_KEYS = {"overview", "items"}
ALLOWED_ITEM_KEYS = {
    "email_id",
    "item_type",
    "section",
    "title",
    "summary",
    "category",
    "suggested_action",
    "priority",
    "reason",
    "deadline",
    "confidence",
}


class DigestParseError(ValueError):
    pass


@dataclass(slots=True)
class ParsedDigestItem:
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
) -> ParsedDigestOutput:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise DigestParseError("Digest output must be valid JSON.") from exc
    if not isinstance(payload, dict):
        raise DigestParseError("Digest output must be a JSON object.")
    unknown_top_level = set(payload) - ALLOWED_TOP_LEVEL_KEYS
    if unknown_top_level:
        raise DigestParseError(f"Unexpected digest fields: {sorted(unknown_top_level)}")

    overview = _parse_overview(payload.get("overview"))
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise DigestParseError("Digest items must be an array.")

    items = [
        _parse_item(index, item, emails_by_external_id)
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


def _parse_overview(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DigestParseError("Digest overview is required.")
    mail_count = value.get("mail_count")
    summary = value.get("summary")
    if not isinstance(mail_count, int) or mail_count < 0:
        raise DigestParseError("overview.mail_count must be a non-negative integer.")
    if not isinstance(summary, str) or not summary.strip():
        raise DigestParseError("overview.summary is required.")
    return {"mail_count": mail_count, "summary": summary}


def _parse_item(
    index: int,
    value: object,
    emails_by_external_id: Mapping[str, Email | UUID],
) -> ParsedDigestItem:
    if not isinstance(value, dict):
        raise DigestParseError(f"items[{index}] must be an object.")
    unknown_keys = set(value) - ALLOWED_ITEM_KEYS
    if unknown_keys:
        raise DigestParseError(f"items[{index}] has unexpected fields: {sorted(unknown_keys)}")

    item_type = _required_enum(value, "item_type", ALLOWED_ITEM_TYPES, index)
    section = _required_enum(value, "section", ALLOWED_SECTIONS, index)
    _validate_section_item_type(section=section, item_type=item_type, index=index)
    title = _required_string(value, "title", index)
    priority = _required_enum(value, "priority", ALLOWED_PRIORITIES, index)
    confidence = _required_confidence(value, index)
    email_id = _resolve_email_id(value.get("email_id"), item_type, emails_by_external_id, index)

    category = _optional_enum(value, "category", ALLOWED_CATEGORIES, index)
    suggested_action = _optional_enum(value, "suggested_action", ALLOWED_ACTIONS, index)
    return ParsedDigestItem(
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


def _required_string(value: dict[str, Any], key: str, index: int) -> str:
    raw_value = value.get(key)
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise DigestParseError(f"items[{index}].{key} is required.")
    return raw_value


def _optional_string(value: dict[str, Any], key: str, index: int) -> str | None:
    raw_value = value.get(key)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raise DigestParseError(f"items[{index}].{key} must be a string or null.")
    return raw_value


def _required_enum(
    value: dict[str, Any],
    key: str,
    allowed: set[str],
    index: int,
) -> str:
    raw_value = value.get(key)
    if not isinstance(raw_value, str) or raw_value not in allowed:
        raise DigestParseError(f"items[{index}].{key} has an unsupported value.")
    return raw_value


def _optional_enum(
    value: dict[str, Any],
    key: str,
    allowed: set[str],
    index: int,
) -> str | None:
    raw_value = value.get(key)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str) or raw_value not in allowed:
        raise DigestParseError(f"items[{index}].{key} has an unsupported value.")
    return raw_value


def _required_confidence(value: dict[str, Any], index: int) -> float:
    confidence = value.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        raise DigestParseError(f"items[{index}].confidence must be between 0 and 1.")
    return float(confidence)


def _optional_date(value: dict[str, Any], key: str, index: int) -> date | None:
    raw_value = value.get(key)
    if raw_value is None:
        return None
    if not isinstance(raw_value, str):
        raise DigestParseError(f"items[{index}].{key} must be YYYY-MM-DD or null.")
    try:
        return date.fromisoformat(raw_value)
    except ValueError as exc:
        raise DigestParseError(f"items[{index}].{key} must be YYYY-MM-DD or null.") from exc


def _resolve_email_id(
    external_id: object,
    item_type: str,
    emails_by_external_id: Mapping[str, Email | UUID],
    index: int,
) -> UUID | None:
    if external_id is None:
        if item_type == "email":
            raise DigestParseError(f"items[{index}].email_id is required for email items.")
        return None
    if not isinstance(external_id, str) or not external_id:
        raise DigestParseError(f"items[{index}].email_id must be a string or null.")
    email = emails_by_external_id.get(external_id)
    if email is None:
        raise DigestParseError(f"Unknown email_id: {external_id}")
    return email.id if isinstance(email, Email) else email


def _validate_section_item_type(*, section: str, item_type: str, index: int) -> None:
    if section == "todo" and item_type != "todo":
        raise DigestParseError(f"items[{index}].section todo requires item_type todo.")
    if section == "risk" and item_type != "risk":
        raise DigestParseError(f"items[{index}].section risk requires item_type risk.")
    if section in {"urgent", "review", "ignore"} and item_type != "email":
        raise DigestParseError(f"items[{index}].section {section} requires item_type email.")


def _item_to_output_json(item: ParsedDigestItem) -> dict[str, Any]:
    return {
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
