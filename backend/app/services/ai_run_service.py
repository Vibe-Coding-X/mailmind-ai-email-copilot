from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.ai_run import AIRun


def create_ai_run(
    db: Session,
    *,
    user_id: UUID,
    mailbox_id: UUID,
    digest_id: UUID | None,
    trigger_source: str,
    model_provider: str,
    model_name: str,
    prompt_version: str,
    output_schema_version: str,
    input_text: str,
    input_summary: dict[str, Any],
    now: datetime | None = None,
) -> AIRun:
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    run = AIRun(
        user_id=user_id,
        mailbox_id=mailbox_id,
        digest_id=digest_id,
        run_type="daily_digest",
        trigger_source=trigger_source,
        model_provider=model_provider,
        model_name=model_name,
        prompt_version=prompt_version,
        output_schema_version=output_schema_version,
        input_hash=hashlib.sha256(input_text.encode("utf-8")).hexdigest(),
        input_summary_json=input_summary,
        status="running",
        created_at=resolved_now,
        started_at=resolved_now,
    )
    db.add(run)
    db.flush()
    return run


def mark_ai_run_succeeded(
    run: AIRun,
    *,
    output_json: dict[str, Any],
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    latency_ms: int | None = None,
    now: datetime | None = None,
) -> AIRun:
    run.status = "succeeded"
    run.output_json = output_json
    run.error_code = None
    run.error_message = None
    run.prompt_tokens = prompt_tokens
    run.completion_tokens = completion_tokens
    if prompt_tokens is not None and completion_tokens is not None:
        run.total_tokens = prompt_tokens + completion_tokens
    run.latency_ms = latency_ms
    run.finished_at = _ensure_utc(now or datetime.now(UTC))
    return run


def mark_ai_run_failed(
    run: AIRun,
    *,
    error_code: str,
    error_message: str,
    now: datetime | None = None,
) -> AIRun:
    run.status = "failed"
    run.error_code = error_code
    run.error_message = error_message[:1000]
    run.finished_at = _ensure_utc(now or datetime.now(UTC))
    return run


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
