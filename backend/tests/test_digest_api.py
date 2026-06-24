from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.ai.base import LLMProviderError, LLMResponse
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.sync_job import SyncJob
from app.db.session import SessionLocal
from app.main import app


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _register_client(prefix: str) -> tuple[TestClient, UUID]:
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={"email": _email(prefix), "password": "strong-password"},
    )
    assert response.status_code == 201
    return client, UUID(response.json()["data"]["user"]["id"])


def _create_mailbox_and_email(user_id: UUID, *, prefix: str) -> UUID:
    with SessionLocal() as db:
        mailbox = Mailbox(
            user_id=user_id,
            provider="gmail",
            provider_account_id=f"{prefix}-{uuid4().hex}",
            email_address=_email(f"{prefix}-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
            status="active",
        )
        db.add(mailbox)
        db.flush()
        db.add(
            Email(
                user_id=user_id,
                mailbox_id=mailbox.id,
                provider="gmail",
                external_id=f"{prefix}-gmail-1",
                external_thread_id=f"{prefix}-thread-1",
                subject="Digest API subject",
                from_address="sender@example.com",
                to_addresses=["me@example.com"],
                cc_addresses=[],
                snippet="preview",
                body_text="body",
                body_text_truncated=False,
                received_at=_current_test_received_at(),
                is_read=False,
                provider_labels=["INBOX", "UNREAD"],
            )
        )
        db.commit()
        return mailbox.id


class StaticProvider:
    provider_name = "mock"
    model_name = "mock-digest-v1"

    def generate_digest(self, prompt: str) -> LLMResponse:
        return LLMResponse(
            text=json.dumps(
                {
                    "overview": {"mail_count": 1, "summary": "API digest summary."},
                    "items": [
                        {
                            "email_id": "digest-api-gmail-1",
                            "item_type": "email",
                            "section": "review",
                            "title": "Digest API subject",
                            "summary": "Review this email.",
                            "category": "work",
                            "suggested_action": "review_today",
                            "priority": "medium",
                            "reason": "It asks for review.",
                            "deadline": None,
                            "confidence": 0.8,
                        }
                    ],
                }
            ),
            model_provider="mock",
            model_name="mock-digest-v1",
        )


class FailingProvider:
    provider_id = "primary"
    provider_type = "openai_compatible"
    provider_name = "openai_compatible"
    model_name = "qwen3.6-plus"

    def generate_digest(self, prompt: str) -> LLMResponse:
        raise LLMProviderError(
            "Provider failed with api_key=secret sk-real-looking-secret"
        )


def _current_test_received_at() -> datetime:
    return datetime.now(UTC)


def test_get_today_digest_requires_login() -> None:
    response = TestClient(app).get("/api/digest/today")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_generate_today_digest_api_returns_current_digest(monkeypatch) -> None:
    client, user_id = _register_client("digest-api")
    mailbox_id = _create_mailbox_and_email(user_id, prefix="digest-api")
    monkeypatch.setattr("app.services.digest_service.get_llm_provider", lambda: StaticProvider())

    response = client.post("/api/digest/today/generate", json={"mailbox_id": str(mailbox_id)})

    assert response.status_code == 200
    digest = response.json()["data"]["digest"]
    assert digest["status"] == "fresh"
    assert digest["summary"] == "API digest summary."
    assert len(digest["items"]) == 1
    assert digest["items"][0]["priority"] == "medium"
    assert "raw_ai_output" not in digest

    today = client.get(f"/api/digest/today?mailbox_id={mailbox_id}")
    assert today.status_code == 200
    assert today.json()["data"]["digest"]["id"] == digest["id"]


def test_generate_today_digest_api_supports_all_mailboxes_scope(monkeypatch) -> None:
    client, user_id = _register_client("digest-api-all")
    gmail_mailbox_id = _create_mailbox_and_email(user_id, prefix="digest-api-all-gmail")
    imap_mailbox_id = _create_mailbox_and_email(user_id, prefix="digest-api-all-imap")

    class AllScopeProvider:
        provider_name = "mock"
        model_name = "mock-digest-v1"

        def generate_digest(self, prompt: str) -> LLMResponse:
            return LLMResponse(
                text=json.dumps(
                    {
                        "overview": {
                            "mail_count": 2,
                            "summary": "Two mailboxes contributed to the digest.",
                            "mailbox_summaries": [
                                {
                                    "mailbox_id": str(gmail_mailbox_id),
                                    "provider": "gmail",
                                    "account_email": "gmail@example.com",
                                    "title": "Gmail",
                                    "summary": "One Gmail message.",
                                    "highlights": ["Gmail highlight"],
                                },
                                {
                                    "mailbox_id": str(imap_mailbox_id),
                                    "provider": "imap",
                                    "account_email": "imap@example.com",
                                    "title": "IMAP",
                                    "summary": "One IMAP message.",
                                    "highlights": ["IMAP highlight"],
                                },
                            ],
                        },
                        "items": [
                            {
                                "email_id": "digest-api-all-gmail-gmail-1",
                                "item_type": "email",
                                "section": "review",
                                "title": "Gmail message",
                                "summary": "Review Gmail.",
                                "category": "work",
                                "suggested_action": "review_today",
                                "priority": "medium",
                                "reason": "Gmail reason.",
                                "deadline": None,
                                "confidence": 0.8,
                            },
                            {
                                "email_id": "digest-api-all-imap-gmail-1",
                                "item_type": "email",
                                "section": "urgent",
                                "title": "IMAP message",
                                "summary": "Review IMAP.",
                                "category": "work",
                                "suggested_action": "review_today",
                                "priority": "high",
                                "reason": "IMAP reason.",
                                "deadline": None,
                                "confidence": 0.85,
                            },
                        ],
                    }
                ),
                model_provider="mock",
                model_name="mock-digest-v1",
            )

    monkeypatch.setattr("app.services.digest_service.get_llm_provider", lambda: AllScopeProvider())

    response = client.post("/api/digest/today/generate", json={"scope_type": "all"})

    assert response.status_code == 200
    digest = response.json()["data"]["digest"]
    assert digest["scope_type"] == "all"
    assert digest["mailbox_id"] is None
    assert len(digest["mailbox_summaries"]) == 2


def test_generate_today_digest_job_requires_mailbox_id_for_mailbox_scope() -> None:
    client, _ = _register_client("digest-missing-mailbox-scope")

    response = client.post(
        "/api/digest/today/generate-jobs",
        json={"scope_type": "mailbox"},
    )

    assert response.status_code in {400, 422}


def test_get_digest_blocks_other_users_digest(monkeypatch) -> None:
    owner_client, owner_id = _register_client("digest-owner")
    other_client, _ = _register_client("digest-other")
    mailbox_id = _create_mailbox_and_email(owner_id, prefix="digest-api")
    monkeypatch.setattr("app.services.digest_service.get_llm_provider", lambda: StaticProvider())
    generated = owner_client.post(
        "/api/digest/today/generate",
        json={"mailbox_id": str(mailbox_id)},
    )
    assert generated.status_code == 200
    digest_id = generated.json()["data"]["digest"]["id"]

    response = other_client.get(f"/api/digest/{digest_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DIGEST_NOT_READY"


def test_refresh_today_digest_api_replaces_current_digest(monkeypatch) -> None:
    client, user_id = _register_client("digest-refresh-api")
    mailbox_id = _create_mailbox_and_email(user_id, prefix="digest-api")
    monkeypatch.setattr("app.services.digest_service.get_llm_provider", lambda: StaticProvider())
    first = client.post("/api/digest/today/generate", json={"mailbox_id": str(mailbox_id)})
    assert first.status_code == 200

    second = client.post("/api/digest/today/refresh", json={"mailbox_id": str(mailbox_id)})

    assert second.status_code == 200
    assert second.json()["data"]["digest"]["version"] == 2
    assert second.json()["data"]["digest"]["is_current"] is True


def test_generate_today_digest_async_job_api_returns_queued_job(monkeypatch) -> None:
    client, user_id = _register_client("digest-generate-job-api")
    mailbox_id = _create_mailbox_and_email(user_id, prefix="digest-api")
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-digest-generate-{job_id}"

    monkeypatch.setattr("app.services.digest_service.dispatch_digest_job", fake_dispatch)

    response = client.post(
        "/api/digest/today/generate-jobs",
        json={"mailbox_id": str(mailbox_id)},
    )

    assert response.status_code == 200
    job = response.json()["data"]["job"]
    assert job["job_type"] == "digest_generate"
    assert job["status"] == "queued"
    assert job["progress"] == 0
    assert job["related_resource_type"] == "mailbox"
    assert job["related_resource_id"] == str(mailbox_id)
    assert dispatched == [UUID(job["job_id"])]


def test_refresh_today_digest_async_job_api_returns_queued_job(monkeypatch) -> None:
    client, user_id = _register_client("digest-refresh-job-api")
    mailbox_id = _create_mailbox_and_email(user_id, prefix="digest-api")
    monkeypatch.setattr(
        "app.services.digest_service.dispatch_digest_job",
        lambda job_id: f"celery-digest-refresh-{job_id}",
    )

    response = client.post(
        "/api/digest/today/refresh-jobs",
        json={"mailbox_id": str(mailbox_id)},
    )

    assert response.status_code == 200
    job = response.json()["data"]["job"]
    assert job["job_type"] == "digest_refresh"
    assert job["status"] == "queued"


def test_generate_today_digest_async_job_dispatches_after_job_commit(monkeypatch) -> None:
    client, user_id = _register_client("digest-generate-job-order")
    mailbox_id = _create_mailbox_and_email(user_id, prefix="digest-api")
    checked: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        with SessionLocal() as verify_db:
            stored = verify_db.get(SyncJob, job_id)
            assert stored is not None
            assert stored.status == "pending_dispatch"
        checked.append(job_id)
        return f"celery-digest-generate-{job_id}"

    monkeypatch.setattr("app.services.digest_service.dispatch_digest_job", fake_dispatch)

    response = client.post(
        "/api/digest/today/generate-jobs",
        json={"mailbox_id": str(mailbox_id)},
    )

    assert response.status_code == 200
    job = response.json()["data"]["job"]
    assert checked == [UUID(job["job_id"])]


def test_generate_today_digest_async_job_marks_dispatch_failure(monkeypatch) -> None:
    client, user_id = _register_client("digest-generate-job-dispatch-failure")
    mailbox_id = _create_mailbox_and_email(user_id, prefix="digest-api")

    def fake_dispatch(job_id: UUID) -> str:
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr("app.services.digest_service.dispatch_digest_job", fake_dispatch)

    response = client.post(
        "/api/digest/today/generate-jobs",
        json={"mailbox_id": str(mailbox_id)},
    )

    assert response.status_code == 200
    job_id = UUID(response.json()["data"]["job"]["job_id"])

    with SessionLocal() as db:
        job = db.get(SyncJob, job_id)
        assert job is not None
        assert job.status == "dispatch_failed"
        assert job.celery_task_id is None
        assert job.error_code == "celery_dispatch_failed"


def test_generate_today_digest_api_hides_provider_error_details(monkeypatch) -> None:
    client, user_id = _register_client("digest-error-api")
    mailbox_id = _create_mailbox_and_email(user_id, prefix="digest-api")
    monkeypatch.setattr("app.services.digest_service.get_llm_provider", lambda: FailingProvider())

    response = client.post("/api/digest/today/generate", json={"mailbox_id": str(mailbox_id)})

    assert response.status_code == 502
    body = response.json()
    assert body["error"]["code"] == "DIGEST_GENERATION_FAILED"
    assert body["error"]["message"] == "Daily digest generation failed."
    serialized = json.dumps(body)
    assert "secret" not in serialized
    assert "sk-real-looking-secret" not in serialized


def test_generate_today_digest_job_rejects_mailbox_scope_without_mailbox_id() -> None:
    client, _ = _register_client("digest-missing-mailbox")

    response = client.post(
        "/api/digest/today/generate-jobs",
        json={"scope_type": "mailbox"},
    )

    assert response.status_code == 422
