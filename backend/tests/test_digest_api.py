from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.ai.base import LLMProviderError, LLMResponse
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
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
    _create_mailbox_and_email(user_id, prefix="digest-api")
    monkeypatch.setattr("app.services.digest_service.get_llm_provider", lambda: StaticProvider())

    response = client.post("/api/digest/today/generate")

    assert response.status_code == 200
    digest = response.json()["data"]["digest"]
    assert digest["status"] == "fresh"
    assert digest["summary"] == "API digest summary."
    assert len(digest["items"]) == 1
    assert digest["items"][0]["priority"] == "medium"
    assert "raw_ai_output" not in digest

    today = client.get("/api/digest/today")
    assert today.status_code == 200
    assert today.json()["data"]["digest"]["id"] == digest["id"]


def test_get_digest_blocks_other_users_digest(monkeypatch) -> None:
    owner_client, owner_id = _register_client("digest-owner")
    other_client, _ = _register_client("digest-other")
    _create_mailbox_and_email(owner_id, prefix="digest-api")
    monkeypatch.setattr("app.services.digest_service.get_llm_provider", lambda: StaticProvider())
    generated = owner_client.post("/api/digest/today/generate")
    assert generated.status_code == 200
    digest_id = generated.json()["data"]["digest"]["id"]

    response = other_client.get(f"/api/digest/{digest_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DIGEST_NOT_READY"


def test_refresh_today_digest_api_replaces_current_digest(monkeypatch) -> None:
    client, user_id = _register_client("digest-refresh-api")
    _create_mailbox_and_email(user_id, prefix="digest-api")
    monkeypatch.setattr("app.services.digest_service.get_llm_provider", lambda: StaticProvider())
    first = client.post("/api/digest/today/generate")
    assert first.status_code == 200

    second = client.post("/api/digest/today/refresh")

    assert second.status_code == 200
    assert second.json()["data"]["digest"]["version"] == 2
    assert second.json()["data"]["digest"]["is_current"] is True


def test_generate_today_digest_async_job_api_returns_queued_job(monkeypatch) -> None:
    client, user_id = _register_client("digest-generate-job-api")
    _create_mailbox_and_email(user_id, prefix="digest-api")
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-digest-generate-{job_id}"

    monkeypatch.setattr("app.services.digest_service.dispatch_digest_job", fake_dispatch)

    response = client.post("/api/digest/today/generate-jobs")

    assert response.status_code == 200
    job = response.json()["data"]["job"]
    assert job["job_type"] == "digest_generate"
    assert job["status"] == "queued"
    assert job["progress"] == 0
    assert job["related_resource_type"] == "mailbox"
    assert dispatched == [UUID(job["job_id"])]


def test_refresh_today_digest_async_job_api_returns_queued_job(monkeypatch) -> None:
    client, user_id = _register_client("digest-refresh-job-api")
    _create_mailbox_and_email(user_id, prefix="digest-api")
    monkeypatch.setattr(
        "app.services.digest_service.dispatch_digest_job",
        lambda job_id: f"celery-digest-refresh-{job_id}",
    )

    response = client.post("/api/digest/today/refresh-jobs")

    assert response.status_code == 200
    job = response.json()["data"]["job"]
    assert job["job_type"] == "digest_refresh"
    assert job["status"] == "queued"


def test_generate_today_digest_api_hides_provider_error_details(monkeypatch) -> None:
    client, user_id = _register_client("digest-error-api")
    _create_mailbox_and_email(user_id, prefix="digest-api")
    monkeypatch.setattr("app.services.digest_service.get_llm_provider", lambda: FailingProvider())

    response = client.post("/api/digest/today/generate")

    assert response.status_code == 502
    body = response.json()
    assert body["error"]["code"] == "DIGEST_GENERATION_FAILED"
    assert body["error"]["message"] == "Daily digest generation failed."
    serialized = json.dumps(body)
    assert "secret" not in serialized
    assert "sk-real-looking-secret" not in serialized
