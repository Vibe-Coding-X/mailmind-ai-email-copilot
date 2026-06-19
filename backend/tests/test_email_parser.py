from __future__ import annotations

import base64
from datetime import UTC, datetime

from app.utils.email_parser import parse_gmail_message
from app.utils.text_cleaner import clean_email_body


def _b64url(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def test_parse_gmail_message_extracts_headers_body_labels_and_read_state() -> None:
    message = {
        "id": "gmail-message-1",
        "threadId": "gmail-thread-1",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "Preview text",
        "internalDate": "1781834400000",
        "historyId": "12345",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Subject line"},
                {"name": "From", "value": "Alice Example <alice@example.com>"},
                {"name": "To", "value": "Me <me@example.com>, ops@example.com"},
                {"name": "Cc", "value": "Team <team@example.com>"},
                {"name": "Message-ID", "value": "<msg-1@example.com>"},
            ],
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/html",
                    "body": {"data": _b64url("<p>HTML fallback</p>")},
                },
                {
                    "mimeType": "text/plain",
                    "body": {"data": _b64url("Plain body wins")},
                },
            ],
        },
    }

    parsed = parse_gmail_message(message)

    assert parsed.external_id == "gmail-message-1"
    assert parsed.external_thread_id == "gmail-thread-1"
    assert parsed.subject == "Subject line"
    assert parsed.from_name == "Alice Example"
    assert parsed.from_address == "alice@example.com"
    assert parsed.to_addresses == ["me@example.com", "ops@example.com"]
    assert parsed.cc_addresses == ["team@example.com"]
    assert parsed.snippet == "Preview text"
    assert parsed.body_text == "Plain body wins"
    assert parsed.received_at == datetime(2026, 6, 19, 2, 0, tzinfo=UTC)
    assert parsed.is_read is False
    assert parsed.provider_labels == ["INBOX", "UNREAD"]
    assert parsed.gmail_history_id == "12345"
    assert len(parsed.raw_payload_hash) == 64


def test_parse_gmail_message_cleans_html_when_plain_text_is_missing() -> None:
    message = {
        "id": "gmail-message-html",
        "threadId": "gmail-thread-html",
        "labelIds": ["INBOX"],
        "internalDate": "1781834400000",
        "payload": {
            "headers": [{"name": "From", "value": "sender@example.com"}],
            "mimeType": "text/html",
            "body": {
                "data": _b64url(
                    "<html><body><p>Hello&nbsp;there</p><br><div>Line two</div></body></html>"
                )
            },
        },
    }

    parsed = parse_gmail_message(message)

    assert parsed.body_text == "Hello there Line two"
    assert parsed.is_read is True


def test_parse_gmail_message_uses_snippet_when_body_is_missing() -> None:
    message = {
        "id": "gmail-message-snippet",
        "threadId": "gmail-thread-snippet",
        "labelIds": ["INBOX"],
        "snippet": "Snippet fallback text",
        "internalDate": "1781834400000",
        "payload": {
            "headers": [{"name": "From", "value": "sender@example.com"}],
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "filename": "report.pdf",
                    "mimeType": "application/pdf",
                    "body": {"attachmentId": "attachment-1"},
                }
            ],
        },
    }

    parsed = parse_gmail_message(message)

    assert parsed.body_text == "Snippet fallback text"
    assert parsed.body_text_truncated is False


def test_clean_email_body_truncates_long_text() -> None:
    cleaned, truncated = clean_email_body("x" * 25, max_length=10)

    assert cleaned == "x" * 10
    assert truncated is True
