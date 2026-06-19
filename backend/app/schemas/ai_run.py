from __future__ import annotations

from typing import Any

from app.db.models.ai_run import AIRun


def ai_run_metadata_payload(ai_run: AIRun) -> dict[str, Any]:
    return {
        "id": ai_run.id,
        "digest_id": ai_run.digest_id,
        "provider": ai_run.model_provider,
        "model": ai_run.model_name,
        "status": ai_run.status,
        "prompt_version": ai_run.prompt_version,
        "output_schema_version": ai_run.output_schema_version,
        "prompt_tokens": ai_run.prompt_tokens,
        "completion_tokens": ai_run.completion_tokens,
        "total_tokens": ai_run.total_tokens,
        "latency_ms": ai_run.latency_ms,
        "created_at": ai_run.created_at,
        "finished_at": ai_run.finished_at,
    }
