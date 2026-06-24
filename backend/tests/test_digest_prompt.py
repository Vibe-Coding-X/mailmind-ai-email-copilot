from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.ai.prompts.digest import build_digest_prompt
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox


def _email(body_text: str) -> Email:
    mailbox_id = uuid4()
    return Email(
        id=uuid4(),
        user_id=uuid4(),
        mailbox_id=mailbox_id,
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


def _mailbox(*, mailbox_id, email_address: str = "me@example.com") -> Mailbox:
    return Mailbox(
        id=mailbox_id,
        user_id=uuid4(),
        provider="gmail",
        provider_account_id=f"acct-{mailbox_id}",
        email_address=email_address,
        display_name=f"Gmail - {email_address}",
        permission_mode="write_enabled",
        granted_scopes=[],
        status="active",
        sync_cursor={},
    )


def test_digest_prompt_uses_safe_email_fields_and_redacts_tokens() -> None:
    email = _email(
        "access_token=secret-token refresh_token=secret-refresh "
        "api_key=secret-api-key sk-testsecret123"
    )
    prompt = build_digest_prompt(
        [email],
        coverage_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
        coverage_end=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        scope_type="mailbox",
        mailboxes=[_mailbox(mailbox_id=email.mailbox_id)],
    )

    assert "Quarterly planning" in prompt.text
    assert "alice@example.com" in prompt.text
    assert "secret-token" not in prompt.text
    assert "secret-refresh" not in prompt.text
    assert "secret-api-key" not in prompt.text
    assert "sk-testsecret123" not in prompt.text
    assert prompt.input_summary["mail_count"] == 1


def test_digest_prompt_includes_digest_v1_schema_contract() -> None:
    email = _email("Please review the plan.")
    prompt = build_digest_prompt(
        [email],
        coverage_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
        coverage_end=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        scope_type="all",
        mailboxes=[_mailbox(mailbox_id=email.mailbox_id)],
    )

    required_fragments = [
        "Return ONLY a JSON object",
        "Do not wrap it in markdown",
        '"overview"',
        '"mail_count"',
        '"summary"',
        '"items"',
        '"email_id"',
        '"item_type"',
        '"section"',
        '"suggested_action"',
        '"priority"',
        '"confidence"',
        '"work" | "notification" | "marketing" | "social" | "other"',
        '"reply_today" | "review_today" | "handle_before_deadline"',
        '"high" | "medium" | "low"',
        "Use provided email_id exactly",
        "Do not invent email_id",
    ]

    for fragment in required_fragments:
        assert fragment in prompt.text


def test_digest_prompt_truncates_email_body_before_llm_input() -> None:
    long_body = "A" * 3000
    email = _email(long_body)

    prompt = build_digest_prompt(
        [email],
        coverage_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
        coverage_end=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        scope_type="mailbox",
        mailboxes=[_mailbox(mailbox_id=email.mailbox_id)],
    )

    assert "A" * 1500 not in prompt.text
    assert prompt.input_summary["truncated_body_count"] == 1
