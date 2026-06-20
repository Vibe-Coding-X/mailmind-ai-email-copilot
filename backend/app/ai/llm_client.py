from __future__ import annotations

from app.ai.base import LLMProvider
from app.ai.mock_provider import MockLLMProvider
from app.ai.openai_compatible_provider import build_llm_provider_from_env
from app.core.config import get_settings


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.ai_provider_mode == "env" or settings.ai_provider_order:
        return build_llm_provider_from_env()
    provider_name = (settings.llm_provider or "mock").lower()
    if provider_name in {"", "mock"}:
        return MockLLMProvider()
    return build_llm_provider_from_env()
