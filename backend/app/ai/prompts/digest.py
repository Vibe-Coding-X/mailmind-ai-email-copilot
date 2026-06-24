from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence

from app.db.models.email import Email
from app.db.models.mailbox import Mailbox


PROMPT_VERSION = "digest_prompt.v1"
OUTPUT_SCHEMA_VERSION = "digest.v1"
MAX_BODY_CHARS = 1200
DIGEST_SCHEMA_INSTRUCTIONS = """Return ONLY a JSON object. Do not wrap it in markdown. Do not add prose.

Required top-level shape:
{
  "overview": {
    "mail_count": <number>,
    "summary": <string>,
    "overall_summary": <string or null>,
    "mailbox_summaries": [
      {
        "mailbox_id": <one of the provided mailbox_id values>,
        "provider": <string>,
        "account_email": <string>,
        "title": <string>,
        "summary": <string>,
        "highlights": [<string>, ...]
      }
    ]
  },
  "items": [
    {
      "email_id": <one of the provided email_id values or null>,
      "mailbox_id": <one of the provided mailbox_id values or null>,
      "item_type": "email" | "todo" | "risk",
      "section": "urgent" | "review" | "ignore" | "todo" | "risk",
      "title": <string>,
      "summary": <string>,
      "category": "work" | "notification" | "marketing" | "social" | "other",
      "suggested_action": "reply_today" | "review_today" | "handle_before_deadline" | "ignore" | "archive_candidate" | "follow_up_later" | "no_action_required",
      "priority": "high" | "medium" | "low",
      "reason": <string or null>,
      "deadline": <YYYY-MM-DD string or null>,
      "confidence": <number between 0 and 1>
    }
  ]
}

Rules:
- Use provided email_id exactly.
- Use provided mailbox_id exactly when you include mailbox_id.
- Do not invent email_id.
- Use null email_id only for todo or risk items not tied to a specific email.
- For scope_type="all", every mailbox with useful content should appear in overview.mailbox_summaries.
- For scope_type="all", todo or risk items not tied to an email must still include mailbox_id.
- If no item is useful, return "items": [].
- Do not include raw credentials, tokens, secrets, or raw provider payloads.

Minimal example:
{
  "overview": {"mail_count": 1, "summary": "One email may need attention."},
  "items": [
    {
      "email_id": "provided-email-id",
      "mailbox_id": "provided-mailbox-id",
      "item_type": "email",
      "section": "review",
      "title": "Review requested",
      "summary": "The sender asked for review today.",
      "category": "work",
      "suggested_action": "review_today",
      "priority": "medium",
      "reason": "The request needs a human decision.",
      "deadline": null,
      "confidence": 0.8
    }
  ]
}
"""

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
    scope_type: str,
    mailboxes: Sequence[Mailbox],
) -> DigestPrompt:
    mailbox_inputs = [
        {
            "mailbox_id": str(mailbox.id),
            "provider": mailbox.provider.strip().lower(),
            "account_email": mailbox.email_address,
            "display_name": mailbox.display_name,
            "title": mailbox.display_name or mailbox.email_address,
        }
        for mailbox in mailboxes
    ]
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
                "mailbox_id": str(email.mailbox_id),
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
        "scope_type": scope_type,
        "coverage_start": coverage_start.isoformat(),
        "coverage_end": coverage_end.isoformat(),
        "mailboxes": mailbox_inputs,
        "emails": email_inputs,
    }
    text = (
        "You are MailMind's Daily Digest classifier.\n"
        f"{DIGEST_SCHEMA_INSTRUCTIONS}\n"
        "EMAIL_INPUT_JSON:\n"
        f"{json.dumps(payload, ensure_ascii=False, default=str)}"
    )
    return DigestPrompt(
        text=text,
        input_summary={
            "scope_type": scope_type,
            "mailbox_count": len(mailboxes),
            "mail_count": len(emails),
            "truncated_body_count": truncated_body_count,
            "coverage_start": coverage_start.isoformat(),
            "coverage_end": coverage_end.isoformat(),
        },
    )


def _redact_sensitive_text(value: str) -> str:
    redacted = _SECRET_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
    return _OPENAI_KEY_RE.sub("[REDACTED_API_KEY]", redacted)
