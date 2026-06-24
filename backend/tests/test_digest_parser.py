from __future__ import annotations

import json
from datetime import date
from uuid import uuid4

import pytest

from app.ai.parsers.digest_parser import DigestParseError, parse_digest_output


def _valid_output(external_id: str) -> str:
    return json.dumps(
        {
            "overview": {"mail_count": 1, "summary": "One important email."},
            "items": [
                {
                    "email_id": external_id,
                    "item_type": "email",
                    "section": "urgent",
                    "title": "Project timeline update",
                    "summary": "Alice needs confirmation today.",
                    "category": "work",
                    "suggested_action": "reply_today",
                    "priority": "high",
                    "reason": "The sender asked for confirmation.",
                    "deadline": "2026-06-19",
                    "confidence": 0.86,
                }
            ],
        }
    )


def test_parse_digest_output_maps_known_email_external_id() -> None:
    email_id = uuid4()

    parsed = parse_digest_output(_valid_output("gmail-1"), {"gmail-1": email_id})

    assert parsed.overview == {
        "mail_count": 1,
        "summary": "One important email.",
        "overall_summary": "One important email.",
        "mailbox_summaries": [],
    }
    assert len(parsed.items) == 1
    assert parsed.items[0].email_id == email_id
    assert parsed.items[0].deadline == date(2026, 6, 19)
    assert parsed.items[0].confidence == 0.86


def test_parse_digest_output_accepts_markdown_fenced_json() -> None:
    email_id = uuid4()
    raw_output = f"```json\n{_valid_output('gmail-1')}\n```"

    parsed = parse_digest_output(raw_output, {"gmail-1": email_id})

    assert parsed.items[0].email_id == email_id
    assert parsed.output_json["overview"]["mail_count"] == 1


def test_parse_digest_output_accepts_json_surrounded_by_short_prose() -> None:
    email_id = uuid4()
    raw_output = f"Here is the digest JSON:\n{_valid_output('gmail-1')}\nDone."

    parsed = parse_digest_output(raw_output, {"gmail-1": email_id})

    assert parsed.items[0].email_id == email_id
    assert parsed.overview["summary"] == "One important email."


def test_parse_digest_output_falls_back_for_empty_output() -> None:
    parsed = parse_digest_output("   ", {"gmail-1": uuid4(), "gmail-2": uuid4()})

    assert parsed.overview == {
        "mail_count": 2,
        "summary": "No digest items were returned.",
        "overall_summary": "No digest items were returned.",
        "mailbox_summaries": [],
    }
    assert parsed.items == []


def test_parse_digest_output_treats_missing_or_null_items_as_empty_list() -> None:
    missing_items = parse_digest_output(
        json.dumps({"overview": {"mail_count": 1, "summary": "No actions."}}),
        {"gmail-1": uuid4()},
    )
    null_items = parse_digest_output(
        json.dumps(
            {
                "overview": {"mail_count": 1, "summary": "No actions."},
                "items": None,
            }
        ),
        {"gmail-1": uuid4()},
    )

    assert missing_items.items == []
    assert null_items.items == []


def test_parse_digest_output_fills_missing_item_fields() -> None:
    email_id = uuid4()
    payload = {
        "items": [
            {
                "email_id": "gmail-1",
                "summary": "Alice asked for a planning review.",
            }
        ]
    }

    parsed = parse_digest_output(json.dumps(payload), {"gmail-1": email_id})
    item = parsed.items[0]

    assert parsed.overview["mail_count"] == 1
    assert item.email_id == email_id
    assert item.item_type == "email"
    assert item.section == "review"
    assert item.title == "Alice asked for a planning review."
    assert item.category == "other"
    assert item.suggested_action == "no_action_required"
    assert item.priority == "medium"
    assert item.confidence == 0.5


def test_parse_digest_output_normalizes_enum_values_and_confidence() -> None:
    payload = json.loads(_valid_output("gmail-1"))
    payload["items"][0]["priority"] = "CRITICAL"
    payload["items"][0]["suggested_action"] = "Reply Today"
    payload["items"][0]["confidence"] = 1.5

    parsed = parse_digest_output(json.dumps(payload), {"gmail-1": uuid4()})

    assert parsed.items[0].priority == "high"
    assert parsed.items[0].suggested_action == "reply_today"
    assert parsed.items[0].confidence == 1.0


def test_parse_digest_output_maps_low_risk_field_aliases() -> None:
    email_id = uuid4()
    payload = {
        "overview": {"mail_count": 1, "summary": "One item."},
        "items": [
            {
                "emailId": "gmail-1",
                "type": "email",
                "section": "Needs Review",
                "title": "Planning review",
                "summary": "Alice asked for review.",
                "category": "business",
                "action": "review",
                "priority_level": "critical",
                "confidence": "0.88",
            }
        ],
    }

    parsed = parse_digest_output(json.dumps(payload), {"gmail-1": email_id})
    item = parsed.items[0]

    assert item.email_id == email_id
    assert item.item_type == "email"
    assert item.section == "review"
    assert item.category == "work"
    assert item.suggested_action == "review_today"
    assert item.priority == "high"
    assert item.confidence == 0.88


def test_parse_digest_output_rejects_non_object_item() -> None:
    payload = {"overview": {"mail_count": 1, "summary": "Bad item."}, "items": ["bad"]}

    with pytest.raises(DigestParseError, match="items\\[0\\] must be an object"):
        parse_digest_output(json.dumps(payload), {"gmail-1": uuid4()})


def test_parse_digest_output_rejects_bad_json() -> None:
    with pytest.raises(DigestParseError, match="valid JSON"):
        parse_digest_output("{not json", {})


def test_parse_digest_output_falls_back_for_missing_overview() -> None:
    parsed = parse_digest_output(json.dumps({"items": []}), {})

    assert parsed.overview == {
        "mail_count": 0,
        "summary": "No digest items were returned.",
        "overall_summary": "No digest items were returned.",
        "mailbox_summaries": [],
    }
    assert parsed.items == []


def test_parse_digest_output_rejects_unknown_email_id() -> None:
    with pytest.raises(DigestParseError, match="Unknown email_id"):
        parse_digest_output(_valid_output("missing-gmail-id"), {"gmail-1": uuid4()})


def test_parse_digest_output_defaults_non_numeric_confidence() -> None:
    payload = json.loads(_valid_output("gmail-1"))
    payload["items"][0]["confidence"] = "unknown"

    parsed = parse_digest_output(json.dumps(payload), {"gmail-1": uuid4()})

    assert parsed.items[0].confidence == 0.5


def test_parse_digest_output_defaults_unknown_enum_values() -> None:
    payload = json.loads(_valid_output("gmail-1"))
    payload["items"][0]["priority"] = "critical"

    parsed = parse_digest_output(json.dumps(payload), {"gmail-1": uuid4()})

    assert parsed.items[0].priority == "high"
