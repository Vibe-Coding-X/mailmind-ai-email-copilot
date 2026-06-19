from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class LLMResponse:
    text: str
    model_provider: str
    model_name: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: int | None = None


class LLMProvider(Protocol):
    provider_name: str
    model_name: str

    def generate_digest(self, prompt: str) -> LLMResponse:
        """Generate a structured Daily Digest JSON string from a safe prompt."""
