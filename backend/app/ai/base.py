from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class LLMResponse:
    text: str
    model_provider: str
    model_name: str
    provider_id: str | None = None
    provider_type: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: int | None = None


class LLMProviderError(Exception):
    def __init__(self, message: str, *, provider_id: str | None = None) -> None:
        self.provider_id = provider_id
        super().__init__(message)


class LLMProvider(Protocol):
    provider_id: str
    provider_type: str
    provider_name: str
    model_name: str

    def generate_digest(self, prompt: str) -> LLMResponse:
        """Generate a structured Daily Digest JSON string from a safe prompt."""
