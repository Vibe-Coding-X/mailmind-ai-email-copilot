from __future__ import annotations

from app.ai.base import LLMProvider
from app.ai.mock_provider import MockLLMProvider
from app.core.config import get_settings


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider_name = (settings.llm_provider or "mock").lower()
    if provider_name in {"", "mock"}:
        return MockLLMProvider()
    raise ValueError("Only the mock LLM provider is available in this phase.")
