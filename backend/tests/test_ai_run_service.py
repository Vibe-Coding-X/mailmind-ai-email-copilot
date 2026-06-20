from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.db.models.ai_run import AIRun
from app.db.models.mailbox import Mailbox
from app.db.session import SessionLocal
from app.services.ai_run_service import create_ai_run, mark_ai_run_failed, mark_ai_run_succeeded
from app.services.auth_service import register_user


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _create_user_and_mailbox() -> tuple[object, Mailbox]:
    with SessionLocal() as db:
        user = register_user(
            db,
            email=_email("ai-run-user"),
            password="strong-password",
            timezone="Asia/Shanghai",
        )
        mailbox = Mailbox(
            user_id=user.id,
            provider="gmail",
            provider_account_id=f"ai-run-{uuid4().hex}",
            email_address=_email("ai-run-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status="active",
        )
        db.add(mailbox)
        db.commit()
        db.refresh(user)
        db.refresh(mailbox)
        return user, mailbox


def test_ai_run_service_records_metadata_without_prompt_or_body() -> None:
    user, mailbox = _create_user_and_mailbox()
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)

    with SessionLocal() as db:
        run = create_ai_run(
            db,
            user_id=user.id,
            mailbox_id=mailbox.id,
            digest_id=None,
            trigger_source="manual",
            provider_id="primary",
            provider_type="openai_compatible",
            model_provider="mock",
            model_name="mock-digest-v1",
            prompt_version="digest_prompt.v1",
            output_schema_version="digest.v1",
            input_text="Prompt with email body that must not be stored",
            input_summary={"mail_count": 1},
            now=now,
        )
        mark_ai_run_succeeded(
            run,
            output_json={"overview": {"mail_count": 1, "summary": "Done"}, "items": []},
            prompt_tokens=12,
            completion_tokens=8,
            latency_ms=5,
            now=now,
        )
        db.commit()
        run_id = run.id

    with SessionLocal() as db:
        stored = db.get(AIRun, run_id)
        assert stored is not None
        assert stored.status == "succeeded"
        assert stored.provider_id == "primary"
        assert stored.provider_type == "openai_compatible"
        assert stored.input_hash
        assert stored.input_summary_json == {"mail_count": 1}
        assert stored.output_json["overview"]["summary"] == "Done"
        assert not hasattr(stored, "prompt_text")
        assert not hasattr(stored, "body_text")


def test_ai_run_service_records_failed_run() -> None:
    user, mailbox = _create_user_and_mailbox()
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)

    with SessionLocal() as db:
        run = create_ai_run(
            db,
            user_id=user.id,
            mailbox_id=mailbox.id,
            digest_id=None,
            trigger_source="manual",
            provider_id="primary",
            provider_type="openai_compatible",
            model_provider="mock",
            model_name="mock-digest-v1",
            prompt_version="digest_prompt.v1",
            output_schema_version="digest.v1",
            input_text="safe prompt",
            input_summary={"mail_count": 0},
            now=now,
        )
        mark_ai_run_failed(
            run,
            error_code="DIGEST_GENERATION_FAILED",
            error_message="Mock provider failed.",
            now=now,
        )
        db.commit()
        run_id = run.id

    with SessionLocal() as db:
        stored = db.get(AIRun, run_id)
        assert stored is not None
        assert stored.status == "failed"
        assert stored.error_code == "DIGEST_GENERATION_FAILED"
        assert stored.error_message == "Mock provider failed."


def test_ai_run_service_redacts_failed_run_error_message() -> None:
    user, mailbox = _create_user_and_mailbox()
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)

    with SessionLocal() as db:
        run = create_ai_run(
            db,
            user_id=user.id,
            mailbox_id=mailbox.id,
            digest_id=None,
            trigger_source="manual",
            provider_id="primary",
            provider_type="openai_compatible",
            model_provider="mock",
            model_name="mock-digest-v1",
            prompt_version="digest_prompt.v1",
            output_schema_version="digest.v1",
            input_text="safe prompt",
            input_summary={"mail_count": 0},
            now=now,
        )
        mark_ai_run_failed(
            run,
            error_code="DIGEST_GENERATION_FAILED",
            error_message=(
                "Provider failed with Authorization: Bearer bearer-secret-12345 "
                "and refresh_token=refresh-secret-12345"
            ),
            now=now,
        )
        db.commit()
        run_id = run.id

    with SessionLocal() as db:
        stored = db.get(AIRun, run_id)
        assert stored is not None
        assert stored.error_message is not None
        assert "bearer-secret-12345" not in stored.error_message
        assert "refresh-secret-12345" not in stored.error_message
        assert "[REDACTED]" in stored.error_message
