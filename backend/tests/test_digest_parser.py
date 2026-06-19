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

    assert parsed.overview == {"mail_count": 1, "summary": "One important email."}
    assert len(parsed.items) == 1
    assert parsed.items[0].email_id == email_id
    assert parsed.items[0].deadline == date(2026, 6, 19)
    assert parsed.items[0].confidence == 0.86


def test_parse_digest_output_rejects_bad_json() -> None:
    with pytest.raises(DigestParseError, match="valid JSON"):
        parse_digest_output("{not json", {})


def test_parse_digest_output_rejects_missing_required_fields() -> None:
    with pytest.raises(DigestParseError, match="overview"):
        parse_digest_output(json.dumps({"items": []}), {})


def test_parse_digest_output_rejects_unknown_email_id() -> None:
    with pytest.raises(DigestParseError, match="Unknown email_id"):
        parse_digest_output(_valid_output("missing-gmail-id"), {"gmail-1": uuid4()})


def test_parse_digest_output_rejects_invalid_confidence() -> None:
    payload = json.loads(_valid_output("gmail-1"))
    payload["items"][0]["confidence"] = 1.5

    with pytest.raises(DigestParseError, match="confidence"):
        parse_digest_output(json.dumps(payload), {"gmail-1": uuid4()})


def test_parse_digest_output_rejects_invalid_enum_values() -> None:
    payload = json.loads(_valid_output("gmail-1"))
    payload["items"][0]["priority"] = "critical"

    with pytest.raises(DigestParseError, match="priority"):
        parse_digest_output(json.dumps(payload), {"gmail-1": uuid4()})
