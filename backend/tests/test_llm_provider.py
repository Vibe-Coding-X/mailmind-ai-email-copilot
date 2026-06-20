from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.ai.base import LLMProviderError
from app.ai.llm_client import get_llm_provider
from app.ai.openai_compatible_provider import (
    OpenAICompatibleProvider,
    ProviderProfile,
    build_llm_provider_from_env,
)


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeHttpClient:
    def __init__(self, responses: list[FakeResponse | Exception]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> FakeResponse:
        self.calls.append(
            {"url": url, "headers": headers, "json": json, "timeout": timeout}
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _success_response(content: str = '{"overview":{"mail_count":0,"summary":"ok"},"items":[]}') -> FakeResponse:
    return FakeResponse(
        200,
        {
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
        },
    )


def test_openai_compatible_provider_posts_chat_completion_without_leaking_key() -> None:
    client = FakeHttpClient([_success_response()])
    provider = OpenAICompatibleProvider(
        ProviderProfile(
            provider_id="primary",
            provider_type="openai_compatible",
            base_url="https://provider.example/v1",
            api_key="test-key-123",
            model="model-a",
            timeout_seconds=12,
            max_retries=0,
        ),
        client=client,
    )

    response = provider.generate_digest("safe prompt")

    assert response.provider_id == "primary"
    assert response.provider_type == "openai_compatible"
    assert response.model_provider == "openai_compatible"
    assert response.model_name == "model-a"
    assert response.prompt_tokens == 11
    assert response.completion_tokens == 7
    assert client.calls[0]["url"] == "https://provider.example/v1/chat/completions"
    assert client.calls[0]["headers"]["Authorization"] == "Bearer test-key-123"
    assert client.calls[0]["json"]["model"] == "model-a"
    assert client.calls[0]["json"]["messages"][-1]["content"] == "safe prompt"


def test_provider_order_uses_primary_without_calling_backup() -> None:
    primary_client = FakeHttpClient([_success_response()])
    backup_client = FakeHttpClient([_success_response()])

    provider = build_llm_provider_from_env(
        {
            "AI_PROVIDER_ORDER": "primary,backup",
            "AI_PROVIDER_PRIMARY_TYPE": "openai_compatible",
            "AI_PROVIDER_PRIMARY_BASE_URL": "https://primary.example/v1",
            "AI_PROVIDER_PRIMARY_API_KEY": "primary-key",
            "AI_PROVIDER_PRIMARY_MODEL": "primary-model",
            "AI_PROVIDER_PRIMARY_MAX_RETRIES": "0",
            "AI_PROVIDER_BACKUP_TYPE": "openai_compatible",
            "AI_PROVIDER_BACKUP_BASE_URL": "https://backup.example/v1",
            "AI_PROVIDER_BACKUP_API_KEY": "backup-key",
            "AI_PROVIDER_BACKUP_MODEL": "backup-model",
        },
        client_factory=lambda profile: primary_client
        if profile.provider_id == "primary"
        else backup_client,
    )

    response = provider.generate_digest("prompt")

    assert response.provider_id == "primary"
    assert len(primary_client.calls) == 1
    assert backup_client.calls == []


def test_provider_fallback_uses_backup_after_primary_timeout() -> None:
    primary_client = FakeHttpClient([httpx.TimeoutException("timeout primary-key")])
    backup_client = FakeHttpClient([_success_response()])
    provider = build_llm_provider_from_env(
        {
            "AI_PROVIDER_ORDER": "primary,backup",
            "AI_PROVIDER_PRIMARY_TYPE": "openai_compatible",
            "AI_PROVIDER_PRIMARY_BASE_URL": "https://primary.example/v1",
            "AI_PROVIDER_PRIMARY_API_KEY": "primary-key",
            "AI_PROVIDER_PRIMARY_MODEL": "primary-model",
            "AI_PROVIDER_PRIMARY_MAX_RETRIES": "0",
            "AI_PROVIDER_BACKUP_TYPE": "openai_compatible",
            "AI_PROVIDER_BACKUP_BASE_URL": "https://backup.example/v1",
            "AI_PROVIDER_BACKUP_API_KEY": "backup-key",
            "AI_PROVIDER_BACKUP_MODEL": "backup-model",
        },
        client_factory=lambda profile: primary_client
        if profile.provider_id == "primary"
        else backup_client,
    )

    response = provider.generate_digest("prompt")

    assert response.provider_id == "backup"
    assert len(primary_client.calls) == 1
    assert len(backup_client.calls) == 1


def test_provider_fallback_uses_backup_after_primary_http_error() -> None:
    primary_client = FakeHttpClient(
        [FakeResponse(500, {"error": {"message": "server failed primary-key"}})]
    )
    backup_client = FakeHttpClient([_success_response()])
    provider = build_llm_provider_from_env(
        {
            "AI_PROVIDER_ORDER": "primary,backup",
            "AI_PROVIDER_PRIMARY_TYPE": "openai_compatible",
            "AI_PROVIDER_PRIMARY_BASE_URL": "https://primary.example/v1",
            "AI_PROVIDER_PRIMARY_API_KEY": "primary-key",
            "AI_PROVIDER_PRIMARY_MODEL": "primary-model",
            "AI_PROVIDER_BACKUP_TYPE": "openai_compatible",
            "AI_PROVIDER_BACKUP_BASE_URL": "https://backup.example/v1",
            "AI_PROVIDER_BACKUP_API_KEY": "backup-key",
            "AI_PROVIDER_BACKUP_MODEL": "backup-model",
        },
        client_factory=lambda profile: primary_client
        if profile.provider_id == "primary"
        else backup_client,
    )

    response = provider.generate_digest("prompt")

    assert response.provider_id == "backup"


def test_all_provider_failures_are_sanitized() -> None:
    provider = build_llm_provider_from_env(
        {
            "AI_PROVIDER_ORDER": "primary",
            "AI_PROVIDER_PRIMARY_TYPE": "openai_compatible",
            "AI_PROVIDER_PRIMARY_BASE_URL": "https://primary.example/v1",
            "AI_PROVIDER_PRIMARY_API_KEY": "sk-test-secret",
            "AI_PROVIDER_PRIMARY_MODEL": "primary-model",
            "AI_PROVIDER_PRIMARY_MAX_RETRIES": "0",
        },
        client_factory=lambda profile: FakeHttpClient(
            [FakeResponse(500, {"error": {"message": "bad sk-test-secret"}})]
        ),
    )

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate_digest("prompt")

    assert "sk-test-secret" not in str(exc_info.value)
    assert "[REDACTED]" in str(exc_info.value)


def test_provider_failures_redact_headers_cookies_and_tokens() -> None:
    provider = build_llm_provider_from_env(
        {
            "AI_PROVIDER_ORDER": "primary",
            "AI_PROVIDER_PRIMARY_TYPE": "openai_compatible",
            "AI_PROVIDER_PRIMARY_BASE_URL": "https://primary.example/v1",
            "AI_PROVIDER_PRIMARY_API_KEY": "provider-secret-12345",
            "AI_PROVIDER_PRIMARY_MODEL": "primary-model",
            "AI_PROVIDER_PRIMARY_MAX_RETRIES": "0",
        },
        client_factory=lambda profile: FakeHttpClient(
            [
                FakeResponse(
                    500,
                    {
                        "error": {
                            "message": (
                                "Authorization: Bearer bearer-secret-12345 "
                                "Cookie: sessionid=session-secret-12345; "
                                "access_token=access-secret-12345"
                            )
                        }
                    },
                )
            ]
        ),
    )

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate_digest("prompt")

    error_text = str(exc_info.value)
    assert "provider-secret-12345" not in error_text
    assert "bearer-secret-12345" not in error_text
    assert "session-secret-12345" not in error_text
    assert "access-secret-12345" not in error_text
    assert "[REDACTED]" in error_text


def test_missing_api_key_fails_fast() -> None:
    with pytest.raises(LLMProviderError, match="API key is required"):
        build_llm_provider_from_env(
            {
                "AI_PROVIDER_ORDER": "primary",
                "AI_PROVIDER_PRIMARY_TYPE": "openai_compatible",
                "AI_PROVIDER_PRIMARY_BASE_URL": "https://primary.example/v1",
                "AI_PROVIDER_PRIMARY_MODEL": "primary-model",
            }
        )


def test_provider_factory_honors_explicit_empty_environment(monkeypatch) -> None:
    monkeypatch.setenv("AI_PROVIDER_ORDER", "primary")
    monkeypatch.setenv("AI_PROVIDER_PRIMARY_TYPE", "openai_compatible")
    monkeypatch.setenv("AI_PROVIDER_PRIMARY_BASE_URL", "https://primary.example/v1")
    monkeypatch.setenv("AI_PROVIDER_PRIMARY_API_KEY", "primary-key")
    monkeypatch.setenv("AI_PROVIDER_PRIMARY_MODEL", "primary-model")

    provider = build_llm_provider_from_env({})

    assert provider.provider_id == "mock"
    assert provider.provider_type == "mock"


def test_get_llm_provider_returns_mock_without_env_configuration(monkeypatch) -> None:
    monkeypatch.delenv("AI_PROVIDER_ORDER", raising=False)
    monkeypatch.delenv("AI_DEFAULT_PROVIDER", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    provider = get_llm_provider()

    assert provider.provider_id == "mock"
    assert provider.provider_type == "mock"
