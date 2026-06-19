from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence

from app.db.models.email import Email


PROMPT_VERSION = "digest_prompt.v1"
OUTPUT_SCHEMA_VERSION = "digest.v1"
MAX_BODY_CHARS = 1200

_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(access_token|refresh_token|api[_ -]?key|authorization)\s*[:=]\s*[^\s,;]+"
)
_OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")


@dataclass(slots=True)
class DigestPrompt:
    text: str
    input_summary: dict[str, Any]
    prompt_version: str = PROMPT_VERSION
    output_schema_version: str = OUTPUT_SCHEMA_VERSION


def build_digest_prompt(
    emails: Sequence[Email],
    *,
    coverage_start: datetime,
    coverage_end: datetime,
) -> DigestPrompt:
    email_inputs: list[dict[str, Any]] = []
    truncated_body_count = 0
    for email in emails:
        body_text = _redact_sensitive_text(email.body_text or "")
        if len(body_text) > MAX_BODY_CHARS:
            truncated_body_count += 1
            body_text = f"{body_text[:MAX_BODY_CHARS]}...[truncated]"
        email_inputs.append(
            {
                "email_id": email.external_id,
                "subject": _redact_sensitive_text(email.subject or ""),
                "sender": _redact_sensitive_text(email.from_address or ""),
                "recipients": email.to_addresses,
                "snippet": _redact_sensitive_text(email.snippet or ""),
                "body_text": body_text,
                "received_at": email.received_at.isoformat(),
                "is_read": email.is_read,
                "labels": email.provider_labels,
            }
        )

    payload = {
        "coverage_start": coverage_start.isoformat(),
        "coverage_end": coverage_end.isoformat(),
        "emails": email_inputs,
    }
    text = (
        "You are MailMind's Daily Digest classifier. Return only valid JSON matching "
        "the digest.v1 schema. Use the provided email_id values exactly when creating "
        "email items. Do not include secrets, credentials, or raw payloads.\n"
        "EMAIL_INPUT_JSON:\n"
        f"{json.dumps(payload, ensure_ascii=False, default=str)}"
    )
    return DigestPrompt(
        text=text,
        input_summary={
            "mail_count": len(emails),
            "truncated_body_count": truncated_body_count,
            "coverage_start": coverage_start.isoformat(),
            "coverage_end": coverage_end.isoformat(),
        },
    )


def _redact_sensitive_text(value: str) -> str:
    redacted = _SECRET_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
    return _OPENAI_KEY_RE.sub("[REDACTED_API_KEY]", redacted)
