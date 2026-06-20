from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime
from email.utils import getaddresses, parseaddr, parsedate_to_datetime
from typing import Any

from app.providers.base import ProviderEmailMessage
from app.utils.text_cleaner import MAX_BODY_TEXT_LENGTH, clean_email_body, html_to_text


def _decode_body(data: str | None) -> str:
    if not data:
        return ""
    padded = data + ("=" * (-len(data) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8", errors="replace")


def _headers(payload: dict[str, Any]) -> dict[str, str]:
    headers = {}
    for header in payload.get("headers", []):
        name = str(header.get("name") or "").lower()
        value = str(header.get("value") or "")
        if name and name not in headers:
            headers[name] = value
    return headers


def _addresses(value: str | None) -> list[str]:
    if not value:
        return []
    addresses = []
    for _, address in getaddresses([value]):
        normalized = address.strip().lower()
        if normalized:
            addresses.append(normalized)
    return addresses


def _plain_and_html_parts(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    plain_parts: list[str] = []
    html_parts: list[str] = []

    def visit(part: dict[str, Any]) -> None:
        filename = str(part.get("filename") or "")
        if filename:
            return

        mime_type = str(part.get("mimeType") or "").lower()
        body_data = (part.get("body") or {}).get("data")
        if body_data and mime_type == "text/plain":
            plain_parts.append(_decode_body(str(body_data)))
        elif body_data and mime_type == "text/html":
            html_parts.append(html_to_text(_decode_body(str(body_data))))

        for child in part.get("parts", []) or []:
            visit(child)

    visit(payload)
    return plain_parts, html_parts


def _received_at(headers: dict[str, str], message: dict[str, Any]) -> datetime:
    internal_date = str(message.get("internalDate") or "")
    if internal_date.isdigit():
        return datetime.fromtimestamp(int(internal_date) / 1000, tz=UTC)

    date_header = headers.get("date")
    if date_header:
        parsed = parsedate_to_datetime(date_header)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    return datetime.now(UTC)


def _raw_payload_hash(message: dict[str, Any]) -> str:
    raw = json.dumps(message, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_gmail_message(
    message: dict[str, Any], *, max_body_length: int = MAX_BODY_TEXT_LENGTH
) -> ProviderEmailMessage:
    payload = message.get("payload") or {}
    headers = _headers(payload)
    from_name, from_address = parseaddr(headers.get("from") or "")
    plain_parts, html_parts = _plain_and_html_parts(payload)
    body_source = "\n".join(part for part in plain_parts if part.strip())
    if not body_source:
        body_source = "\n".join(part for part in html_parts if part.strip())
    if not body_source:
        body_source = str(message.get("snippet") or "")
    body_text, body_text_truncated = clean_email_body(
        body_source, max_length=max_body_length
    )
    labels = [str(label) for label in message.get("labelIds", []) if str(label)]

    return ProviderEmailMessage(
        external_id=str(message.get("id") or ""),
        external_thread_id=str(message.get("threadId") or "") or None,
        internet_message_id=headers.get("message-id"),
        subject=headers.get("subject") or None,
        from_name=from_name or None,
        from_address=from_address.strip().lower() or None,
        to_addresses=_addresses(headers.get("to")),
        cc_addresses=_addresses(headers.get("cc")),
        snippet=str(message.get("snippet") or "") or None,
        body_text=body_text or None,
        body_text_truncated=body_text_truncated,
        received_at=_received_at(headers, message),
        is_read="UNREAD" not in labels,
        provider_labels=labels,
        gmail_history_id=str(message.get("historyId") or "") or None,
        raw_payload_hash=_raw_payload_hash(message),
    )
