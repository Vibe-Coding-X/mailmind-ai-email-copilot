from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.ai.prompts.digest import build_digest_prompt
from app.db.models.email import Email


def _email(body_text: str) -> Email:
    return Email(
        id=uuid4(),
        user_id=uuid4(),
        mailbox_id=uuid4(),
        provider="gmail",
        external_id="gmail-safe-1",
        external_thread_id="thread-1",
        subject="Quarterly planning",
        from_name="Alice",
        from_address="alice@example.com",
        to_addresses=["me@example.com"],
        cc_addresses=[],
        snippet="Please review the plan.",
        body_text=body_text,
        body_text_truncated=False,
        received_at=datetime(2026, 6, 19, 2, 0, tzinfo=UTC),
        is_read=False,
        provider_labels=["INBOX", "UNREAD"],
    )


def test_digest_prompt_uses_safe_email_fields_and_redacts_tokens() -> None:
    prompt = build_digest_prompt(
        [_email("access_token=secret-token refresh_token=secret-refresh sk-testsecret123")],
        coverage_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
        coverage_end=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
    )

    assert "Quarterly planning" in prompt.text
    assert "alice@example.com" in prompt.text
    assert "secret-token" not in prompt.text
    assert "secret-refresh" not in prompt.text
    assert "sk-testsecret123" not in prompt.text
    assert prompt.input_summary["mail_count"] == 1


def test_digest_prompt_truncates_email_body_before_llm_input() -> None:
    long_body = "A" * 3000

    prompt = build_digest_prompt(
        [_email(long_body)],
        coverage_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
        coverage_end=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
    )

    assert "A" * 1500 not in prompt.text
    assert prompt.input_summary["truncated_body_count"] == 1
