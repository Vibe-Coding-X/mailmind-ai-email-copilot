from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

import httpx

from app.ai.base import LLMProvider, LLMProviderError, LLMResponse
from app.ai.mock_provider import MockLLMProvider
from app.utils.redaction import redact_text


DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 2


@dataclass(frozen=True, slots=True)
class ProviderProfile:
    provider_id: str
    provider_type: str
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES


class OpenAICompatibleProvider:
    provider_name = "openai_compatible"

    def __init__(self, profile: ProviderProfile, *, client: Any | None = None) -> None:
        self.profile = profile
        self.client = client or httpx
        self.provider_id = profile.provider_id
        self.provider_type = profile.provider_type
        self.model_name = profile.model

    def generate_digest(self, prompt: str) -> LLMResponse:
        url = f"{self.profile.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.profile.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.profile.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return ONLY a JSON object matching the MailMind digest.v1 "
                        "schema. Do not wrap it in markdown. Do not add prose."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        attempts = self.profile.max_retries + 1
        last_error: Exception | None = None
        started = time.perf_counter()
        for _ in range(attempts):
            try:
                response = self.client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.profile.timeout_seconds,
                )
                status_code = int(getattr(response, "status_code", 500))
                if status_code >= 400:
                    raise LLMProviderError(
                        redact_text(
                            f"Provider returned HTTP {status_code}: "
                            f"{_response_error_message(response)}",
                            extra_secrets=[self.profile.api_key],
                        ),
                        provider_id=self.profile.provider_id,
                    )
                return self._parse_response(response, started=started)
            except LLMProviderError as exc:
                last_error = exc
            except (httpx.TimeoutException, TimeoutError) as exc:
                last_error = LLMProviderError(
                    redact_text(
                        "Provider request timed out.",
                        extra_secrets=[self.profile.api_key],
                    ),
                    provider_id=self.profile.provider_id,
                )
            except Exception as exc:
                last_error = LLMProviderError(
                    redact_text(
                        f"Provider request failed: {exc}",
                        extra_secrets=[self.profile.api_key],
                    ),
                    provider_id=self.profile.provider_id,
                )
        if isinstance(last_error, LLMProviderError):
            raise last_error
        raise LLMProviderError("Provider request failed.", provider_id=self.profile.provider_id)

    def _parse_response(self, response: Any, *, started: float) -> LLMResponse:
        try:
            payload = response.json()
        except Exception as exc:
            raise LLMProviderError(
                "Provider returned invalid JSON.",
                provider_id=self.profile.provider_id,
            ) from exc
        choices = payload.get("choices") if isinstance(payload, dict) else None
        if not isinstance(choices, list) or not choices:
            raise LLMProviderError(
                "Provider response did not include choices.",
                provider_id=self.profile.provider_id,
            )
        first_choice = choices[0]
        message = first_choice.get("message") if isinstance(first_choice, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError(
                "Provider response did not include content.",
                provider_id=self.profile.provider_id,
            )
        usage = payload.get("usage") if isinstance(payload, dict) else {}
        return LLMResponse(
            text=content,
            model_provider=self.profile.provider_type,
            model_name=self.profile.model,
            provider_id=self.profile.provider_id,
            provider_type=self.profile.provider_type,
            prompt_tokens=_optional_int(usage, "prompt_tokens"),
            completion_tokens=_optional_int(usage, "completion_tokens"),
            latency_ms=int((time.perf_counter() - started) * 1000),
        )


class FallbackLLMProvider:
    provider_id = "fallback"
    provider_type = "fallback"
    provider_name = "fallback"
    model_name = "fallback"

    def __init__(self, providers: list[LLMProvider]) -> None:
        if not providers:
            raise LLMProviderError("At least one AI provider profile is required.")
        self.providers = providers

    def generate_digest(self, prompt: str) -> LLMResponse:
        failures: list[str] = []
        for provider in self.providers:
            try:
                return provider.generate_digest(prompt)
            except LLMProviderError as exc:
                provider_id = getattr(provider, "provider_id", "unknown")
                failures.append(redact_text(f"{provider_id}: {exc}"))
        raise LLMProviderError(redact_text(f"All AI providers failed: {'; '.join(failures)}"))


def build_llm_provider_from_env(
    environ: Mapping[str, str] | None = None,
    *,
    client_factory: Callable[[ProviderProfile], Any] | None = None,
) -> LLMProvider:
    env = os.environ if environ is None else environ
    provider_order = _provider_order(env)
    if not provider_order:
        return MockLLMProvider()

    providers: list[LLMProvider] = []
    for provider_id in provider_order:
        provider_type = _env_value(env, provider_id, "TYPE", default="openai_compatible")
        if provider_type == "mock":
            providers.append(MockLLMProvider())
            continue
        if provider_type != "openai_compatible":
            raise LLMProviderError(f"Unsupported AI provider type: {provider_type}")
        profile = _profile_from_env(env, provider_id, provider_type)
        providers.append(
            OpenAICompatibleProvider(
                profile,
                client=client_factory(profile) if client_factory else None,
            )
        )
    return providers[0] if len(providers) == 1 else FallbackLLMProvider(providers)


def _provider_order(env: Mapping[str, str]) -> list[str]:
    order = env.get("AI_PROVIDER_ORDER", "")
    if order.strip():
        return [item.strip() for item in order.split(",") if item.strip()]
    default_provider = env.get("AI_DEFAULT_PROVIDER", "")
    if default_provider.strip():
        return [default_provider.strip()]
    legacy_provider = env.get("LLM_PROVIDER", "")
    if legacy_provider.lower() in {"", "mock"}:
        return []
    return ["legacy"]


def _profile_from_env(
    env: Mapping[str, str],
    provider_id: str,
    provider_type: str,
) -> ProviderProfile:
    base_url = _env_value(env, provider_id, "BASE_URL")
    api_key = _env_value(env, provider_id, "API_KEY")
    model = _env_value(env, provider_id, "MODEL")
    if not base_url:
        raise LLMProviderError(f"AI provider {provider_id} base URL is required.")
    if not api_key:
        raise LLMProviderError(f"AI provider {provider_id} API key is required.")
    if not model:
        raise LLMProviderError(f"AI provider {provider_id} model is required.")
    return ProviderProfile(
        provider_id=provider_id,
        provider_type=provider_type,
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout_seconds=_optional_float(
            _env_value(env, provider_id, "TIMEOUT_SECONDS"),
            DEFAULT_TIMEOUT_SECONDS,
        ),
        max_retries=_optional_nonnegative_int(
            _env_value(env, provider_id, "MAX_RETRIES"),
            DEFAULT_MAX_RETRIES,
        ),
    )


def _env_value(
    env: Mapping[str, str],
    provider_id: str,
    suffix: str,
    default: str = "",
) -> str:
    if provider_id == "legacy":
        legacy_key = {
            "TYPE": "LLM_PROVIDER",
            "API_KEY": "LLM_API_KEY",
            "MODEL": "LLM_MODEL",
            "BASE_URL": "LLM_BASE_URL",
            "TIMEOUT_SECONDS": "LLM_TIMEOUT_SECONDS",
            "MAX_RETRIES": "LLM_MAX_RETRIES",
        }.get(suffix)
        if legacy_key:
            return env.get(legacy_key, default)
    normalized_id = provider_id.upper().replace("-", "_")
    return env.get(f"AI_PROVIDER_{normalized_id}_{suffix}", default)


def _response_error_message(response: Any) -> str:
    try:
        payload = response.json()
    except Exception:
        return "request failed"
    if not isinstance(payload, dict):
        return "request failed"
    error = payload.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or "request failed")
    if isinstance(error, str):
        return error
    return "request failed"


def _optional_int(payload: object, key: str) -> int | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get(key)
    return value if isinstance(value, int) and value >= 0 else None


def _optional_float(value: str, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _optional_nonnegative_int(value: str, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default
