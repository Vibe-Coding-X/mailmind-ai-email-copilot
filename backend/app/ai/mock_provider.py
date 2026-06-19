from __future__ import annotations

import json

from app.ai.base import LLMResponse


class MockLLMProvider:
    provider_name = "mock"
    model_name = "mock-digest-v1"

    def generate_digest(self, prompt: str) -> LLMResponse:
        payload = _extract_prompt_payload(prompt)
        emails = payload.get("emails", []) if isinstance(payload, dict) else []
        items = [
            {
                "email_id": email["email_id"],
                "item_type": "email",
                "section": "review",
                "title": email.get("subject") or "(no subject)",
                "summary": email.get("snippet") or "Review this email.",
                "category": "other",
                "suggested_action": "review_today",
                "priority": "medium",
                "reason": "Mock provider generated a deterministic review item.",
                "deadline": None,
                "confidence": 0.75,
            }
            for email in emails
            if isinstance(email, dict) and email.get("email_id")
        ]
        output = {
            "overview": {
                "mail_count": len(emails),
                "summary": (
                    "No emails in the selected window."
                    if not emails
                    else f"{len(emails)} email(s) in today's digest window."
                ),
            },
            "items": items,
        }
        return LLMResponse(
            text=json.dumps(output),
            model_provider=self.provider_name,
            model_name=self.model_name,
        )


def _extract_prompt_payload(prompt: str) -> dict[str, object]:
    marker = "EMAIL_INPUT_JSON:"
    if marker not in prompt:
        return {}
    raw_json = prompt.split(marker, 1)[1].strip()
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
