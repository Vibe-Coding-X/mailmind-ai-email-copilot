from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.ai.base import LLMProvider, LLMProviderError, LLMResponse
from app.db.models.ai_run import AIRun
from app.db.models.daily_digest import DailyDigest
from app.db.models.digest_item import DigestItem
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.sync_job import SyncJob
from app.db.session import SessionLocal
from app.services.auth_service import register_user
from app.services.digest_service import (
    DigestServiceError,
    enqueue_generate_today_digest_job,
    enqueue_refresh_today_digest_job,
    execute_queued_digest_job,
    generate_today_digest,
    get_today_digest,
    refresh_today_digest,
)


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _create_user_mailbox_and_email(
    *,
    prefix: str,
    received_at: datetime = datetime(2026, 6, 19, 2, 0, tzinfo=UTC),
) -> tuple[UUID, UUID, UUID]:
    with SessionLocal() as db:
        user = register_user(
            db,
            email=_email(prefix),
            password="strong-password",
            timezone="Asia/Shanghai",
        )
        mailbox = Mailbox(
            user_id=user.id,
            provider="gmail",
            provider_account_id=f"{prefix}-{uuid4().hex}",
            email_address=_email(f"{prefix}-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status="active",
        )
        db.add(mailbox)
        db.flush()
        email = Email(
            user_id=user.id,
            mailbox_id=mailbox.id,
            provider="gmail",
            external_id=f"{prefix}-gmail-1",
            external_thread_id=f"{prefix}-thread-1",
            subject="Needs review",
            from_address="sender@example.com",
            to_addresses=["me@example.com"],
            cc_addresses=[],
            snippet="Please review today.",
            body_text="Please review the attached plan today.",
            body_text_truncated=False,
            received_at=received_at,
            is_read=False,
            provider_labels=["INBOX", "UNREAD"],
        )
        db.add(email)
        db.commit()
        return user.id, mailbox.id, email.id


class StaticProvider(LLMProvider):
    provider_id = "mock"
    provider_type = "mock"
    provider_name = "mock"
    model_name = "mock-digest-v1"

    def __init__(self, external_id: str) -> None:
        self.external_id = external_id
        self.prompt_text: str | None = None

    def generate_digest(self, prompt: str) -> LLMResponse:
        self.prompt_text = prompt
        return LLMResponse(
            text=json.dumps(
                {
                    "overview": {"mail_count": 1, "summary": "One email needs review."},
                    "items": [
                        {
                            "email_id": self.external_id,
                            "item_type": "email",
                            "section": "urgent",
                            "title": "Needs review",
                            "summary": "The sender asked for review today.",
                            "category": "work",
                            "suggested_action": "review_today",
                            "priority": "high",
                            "reason": "Review request due today.",
                            "deadline": "2026-06-19",
                            "confidence": 0.9,
                        }
                    ],
                }
            ),
            model_provider=self.provider_name,
            model_name=self.model_name,
            provider_id=self.provider_id,
            provider_type=self.provider_type,
            prompt_tokens=10,
            completion_tokens=20,
            latency_ms=7,
        )


class FailingProvider(LLMProvider):
    provider_id = "mock"
    provider_type = "mock"
    provider_name = "mock"
    model_name = "mock-digest-v1"

    def generate_digest(self, prompt: str) -> LLMResponse:
        raise RuntimeError("LLM unavailable")


class InvalidOutputProvider(LLMProvider):
    provider_name = "mock"
    model_name = "mock-digest-v1"

    def generate_digest(self, prompt: str) -> LLMResponse:
        return LLMResponse(
            text="{not json",
            model_provider=self.provider_name,
            model_name=self.model_name,
        )


class RawOutputProvider(LLMProvider):
    provider_id = "primary"
    provider_type = "openai_compatible"
    provider_name = "openai_compatible"
    model_name = "qwen3.6-plus"

    def __init__(self, text: str) -> None:
        self.text = text

    def generate_digest(self, prompt: str) -> LLMResponse:
        return LLMResponse(
            text=self.text,
            model_provider=self.provider_name,
            model_name=self.model_name,
            provider_id=self.provider_id,
            provider_type=self.provider_type,
            prompt_tokens=21,
            completion_tokens=34,
            latency_ms=42,
        )


class ProviderErrorProvider(LLMProvider):
    provider_id = "primary"
    provider_type = "openai_compatible"
    provider_name = "openai_compatible"
    model_name = "qwen3.6-plus"

    def generate_digest(self, prompt: str) -> LLMResponse:
        raise LLMProviderError(
            "Provider returned HTTP 500 with Authorization: Bearer secret "
            "api_key=secret sk-real-looking-secret",
            provider_id=self.provider_id,
        )


def _latest_ai_run_for_user(user_id: UUID) -> AIRun:
    with SessionLocal() as db:
        run = db.scalar(
            select(AIRun)
            .where(AIRun.user_id == user_id)
            .order_by(AIRun.created_at.desc())
        )
        assert run is not None
        return run


def test_generate_today_digest_creates_digest_items_ai_run_and_sync_job() -> None:
    user_id, mailbox_id, email_id = _create_user_mailbox_and_email(prefix="digest-service")
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)

    with SessionLocal() as db:
        digest = generate_today_digest(
            db,
            user_id=user_id,
            llm_provider=StaticProvider("digest-service-gmail-1"),
            now=now,
        )
        db.commit()
        digest_id = digest.id

    with SessionLocal() as db:
        stored = db.get(DailyDigest, digest_id)
        item = db.scalar(select(DigestItem).where(DigestItem.digest_id == digest_id))
        ai_run = db.scalar(select(AIRun).where(AIRun.digest_id == digest_id))
        job = db.scalar(select(SyncJob).where(SyncJob.digest_id == digest_id))

        assert stored is not None
        assert stored.user_id == user_id
        assert stored.mailbox_id == mailbox_id
        assert stored.status == "fresh"
        assert stored.is_current is True
        assert stored.mail_count == 1
        assert stored.overview_json["summary"] == "One email needs review."
        assert item is not None
        assert item.email_id == email_id
        assert item.priority == "high"
        assert ai_run is not None
        assert ai_run.status == "succeeded"
        assert ai_run.provider_id == "mock"
        assert ai_run.provider_type == "mock"
        assert ai_run.model_provider == "mock"
        assert ai_run.model_name == "mock-digest-v1"
        assert job is not None
        assert job.job_type == "generate_daily_digest"
        assert job.status == "succeeded"


def test_generate_today_digest_uses_only_current_users_emails() -> None:
    user_id, _, _ = _create_user_mailbox_and_email(prefix="digest-owned")
    _create_user_mailbox_and_email(prefix="digest-other")

    with SessionLocal() as db:
        digest = generate_today_digest(
            db,
            user_id=user_id,
            llm_provider=StaticProvider("digest-owned-gmail-1"),
            now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )
        db.commit()
        digest_id = digest.id

    with SessionLocal() as db:
        item = db.scalar(select(DigestItem).where(DigestItem.digest_id == digest_id))
        assert item is not None
        assert item.user_id == user_id


def test_refresh_today_digest_replaces_current_version_only_after_success() -> None:
    user_id, mailbox_id, _ = _create_user_mailbox_and_email(prefix="digest-refresh")
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)

    with SessionLocal() as db:
        first = generate_today_digest(
            db,
            user_id=user_id,
            llm_provider=StaticProvider("digest-refresh-gmail-1"),
            now=now,
        )
        db.commit()
        first_id = first.id

    with SessionLocal() as db:
        second = refresh_today_digest(
            db,
            user_id=user_id,
            llm_provider=StaticProvider("digest-refresh-gmail-1"),
            now=now,
        )
        db.commit()
        second_id = second.id

    with SessionLocal() as db:
        first = db.get(DailyDigest, first_id)
        second = db.get(DailyDigest, second_id)
        current = get_today_digest(db, user_id=user_id, now=now)
        assert first is not None
        assert second is not None
        assert first.mailbox_id == mailbox_id
        assert first.is_current is False
        assert second.is_current is True
        assert second.version == 2
        assert current.id == second_id


def test_failed_refresh_preserves_previous_current_digest() -> None:
    user_id, _, _ = _create_user_mailbox_and_email(prefix="digest-failure")
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)

    with SessionLocal() as db:
        first = generate_today_digest(
            db,
            user_id=user_id,
            llm_provider=StaticProvider("digest-failure-gmail-1"),
            now=now,
        )
        db.commit()
        first_id = first.id

    with SessionLocal() as db:
        with pytest.raises(DigestServiceError, match="Daily digest generation failed"):
            refresh_today_digest(
                db,
                user_id=user_id,
                llm_provider=FailingProvider(),
                now=now,
            )
        db.commit()

    with SessionLocal() as db:
        current = get_today_digest(db, user_id=user_id, now=now)
        failed = db.scalar(
            select(DailyDigest)
            .where(DailyDigest.user_id == user_id, DailyDigest.status == "failed")
            .order_by(DailyDigest.version.desc())
        )
        assert current.id == first_id
        assert failed is not None
        assert failed.is_current is False


def test_failed_refresh_from_invalid_ai_output_preserves_previous_current_digest() -> None:
    user_id, _, _ = _create_user_mailbox_and_email(prefix="digest-invalid-output")
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)

    with SessionLocal() as db:
        first = generate_today_digest(
            db,
            user_id=user_id,
            llm_provider=StaticProvider("digest-invalid-output-gmail-1"),
            now=now,
        )
        db.commit()
        first_id = first.id

    with SessionLocal() as db:
        with pytest.raises(DigestServiceError, match="Daily digest generation failed"):
            refresh_today_digest(
                db,
                user_id=user_id,
                llm_provider=InvalidOutputProvider(),
                now=now,
            )
        db.commit()

    with SessionLocal() as db:
        current = get_today_digest(db, user_id=user_id, now=now)
        failed = db.scalar(
            select(DailyDigest)
            .where(DailyDigest.user_id == user_id, DailyDigest.status == "failed")
            .order_by(DailyDigest.version.desc())
        )

        assert current.id == first_id
        assert failed is not None
        assert failed.is_current is False


def test_generate_today_digest_handles_no_emails_with_empty_digest() -> None:
    with SessionLocal() as db:
        user = register_user(
            db,
            email=_email("digest-empty"),
            password="strong-password",
            timezone="Asia/Shanghai",
        )
        mailbox = Mailbox(
            user_id=user.id,
            provider="gmail",
            provider_account_id=f"digest-empty-{uuid4().hex}",
            email_address=_email("digest-empty-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status="active",
        )
        db.add(mailbox)
        db.commit()
        user_id = user.id

    with SessionLocal() as db:
        digest = generate_today_digest(
            db,
            user_id=user_id,
            now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )
        db.commit()
        digest_id = digest.id

    with SessionLocal() as db:
        stored = db.get(DailyDigest, digest_id)
        assert stored is not None
        assert stored.status == "fresh"
        assert stored.mail_count == 0
        assert stored.overview_json["mail_count"] == 0


def test_generate_today_digest_accepts_real_provider_like_alias_output() -> None:
    user_id, _, email_id = _create_user_mailbox_and_email(prefix="digest-real-like")
    output = json.dumps(
        {
            "overview": {"mail_count": 1, "summary": "One email needs review."},
            "items": [
                {
                    "emailId": "digest-real-like-gmail-1",
                    "type": "email",
                    "section": "Needs Review",
                    "title": "Review requested",
                    "summary": "The sender asked for review today.",
                    "category": "business",
                    "action": "review",
                    "priority_level": "critical",
                    "reason": "The request is time sensitive.",
                    "deadline": None,
                    "confidence": "0.91",
                }
            ],
        }
    )

    with SessionLocal() as db:
        digest = generate_today_digest(
            db,
            user_id=user_id,
            llm_provider=RawOutputProvider(output),
            now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )
        db.commit()
        digest_id = digest.id

    with SessionLocal() as db:
        item = db.scalar(select(DigestItem).where(DigestItem.digest_id == digest_id))
        ai_run = db.scalar(select(AIRun).where(AIRun.digest_id == digest_id))

        assert item is not None
        assert item.email_id == email_id
        assert item.priority == "high"
        assert item.suggested_action == "review_today"
        assert ai_run is not None
        assert ai_run.status == "succeeded"
        assert ai_run.provider_id == "primary"
        assert ai_run.provider_type == "openai_compatible"
        assert ai_run.model_name == "qwen3.6-plus"


def test_malformed_provider_output_records_safe_diagnostic() -> None:
    user_id, _, _ = _create_user_mailbox_and_email(prefix="digest-bad-json")

    with SessionLocal() as db:
        with pytest.raises(DigestServiceError) as exc_info:
            generate_today_digest(
                db,
                user_id=user_id,
                llm_provider=RawOutputProvider(
                    "{not json access_token=secret sk-real-looking-secret"
                ),
                now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
            )
        db.commit()

    assert exc_info.value.message == "Daily digest generation failed."
    run = _latest_ai_run_for_user(user_id)
    assert run.status == "failed"
    assert run.error_message == "Provider response was not valid JSON."
    assert "secret" not in (run.error_message or "")
    assert "sk-real-looking-secret" not in (run.error_message or "")


def test_unknown_email_id_records_safe_diagnostic() -> None:
    user_id, _, _ = _create_user_mailbox_and_email(prefix="digest-unknown-email")
    output = json.dumps(
        {
            "overview": {"mail_count": 1, "summary": "Unknown reference."},
            "items": [{"email_id": "not-owned-or-input", "summary": "Bad reference."}],
        }
    )

    with SessionLocal() as db:
        with pytest.raises(DigestServiceError):
            generate_today_digest(
                db,
                user_id=user_id,
                llm_provider=RawOutputProvider(output),
                now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
            )
        db.commit()

    run = _latest_ai_run_for_user(user_id)
    assert run.status == "failed"
    assert run.error_message == "Provider response referenced unknown email_id."
    assert "not-owned-or-input" not in (run.error_message or "")


def test_provider_error_records_safe_diagnostic_without_secret() -> None:
    user_id, _, _ = _create_user_mailbox_and_email(prefix="digest-provider-error")

    with SessionLocal() as db:
        with pytest.raises(DigestServiceError) as exc_info:
            generate_today_digest(
                db,
                user_id=user_id,
                llm_provider=ProviderErrorProvider(),
                now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
            )
        db.commit()

    assert exc_info.value.message == "Daily digest generation failed."
    run = _latest_ai_run_for_user(user_id)
    assert run.status == "failed"
    assert run.error_message == "Provider request failed."
    for secret in ["secret", "sk-real-looking-secret", "Authorization: Bearer"]:
        assert secret not in (run.error_message or "")


def test_enqueue_generate_today_digest_job_creates_queued_job_and_dispatches(
    monkeypatch,
) -> None:
    user_id, mailbox_id, _ = _create_user_mailbox_and_email(prefix="digest-queue")
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-digest-{job_id}"

    monkeypatch.setattr(
        "app.services.digest_service.dispatch_digest_job",
        fake_dispatch,
    )

    with SessionLocal() as db:
        result = enqueue_generate_today_digest_job(
            db,
            user_id=user_id,
            now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )
        db.commit()
        job_id = result.job_id

    assert dispatched == [job_id]
    assert result.status == "queued"
    with SessionLocal() as db:
        job = db.get(SyncJob, job_id)
        assert job is not None
        assert job.user_id == user_id
        assert job.mailbox_id == mailbox_id
        assert job.job_type == "generate_daily_digest"
        assert job.status == "queued"
        assert job.celery_task_id == f"celery-digest-{job_id}"


def test_execute_queued_digest_job_generates_digest_and_updates_job() -> None:
    user_id, _, _ = _create_user_mailbox_and_email(prefix="digest-worker")
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)

    with SessionLocal() as db:
        queued = enqueue_generate_today_digest_job(
            db,
            user_id=user_id,
            dispatch=False,
            now=now,
        )
        digest = execute_queued_digest_job(
            db,
            job_id=queued.job_id,
            llm_provider=StaticProvider("digest-worker-gmail-1"),
            now=now,
        )
        db.commit()
        digest_id = digest.id
        job_id = queued.job_id

    with SessionLocal() as db:
        job = db.get(SyncJob, job_id)
        stored = db.get(DailyDigest, digest_id)
        item = db.scalar(select(DigestItem).where(DigestItem.digest_id == digest_id))
        ai_run = db.scalar(select(AIRun).where(AIRun.digest_id == digest_id))

        assert job is not None
        assert job.status == "succeeded"
        assert job.payload_json["digest_id"] == str(digest_id)
        assert job.payload_json["item_count"] == 1
        assert stored is not None
        assert stored.is_current is True
        assert item is not None
        assert ai_run is not None
        assert ai_run.status == "succeeded"


def test_enqueue_refresh_today_digest_job_uses_refresh_job_type(monkeypatch) -> None:
    user_id, _, _ = _create_user_mailbox_and_email(prefix="digest-refresh-queue")
    monkeypatch.setattr(
        "app.services.digest_service.dispatch_digest_job",
        lambda job_id: f"celery-digest-refresh-{job_id}",
    )

    with SessionLocal() as db:
        result = enqueue_refresh_today_digest_job(
            db,
            user_id=user_id,
            now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )
        db.commit()
        job_id = result.job_id

    with SessionLocal() as db:
        job = db.get(SyncJob, job_id)
        assert job is not None
        assert job.job_type == "refresh_daily_digest"
        assert job.status == "queued"
        assert job.celery_task_id == f"celery-digest-refresh-{job_id}"
