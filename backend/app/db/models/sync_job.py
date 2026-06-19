from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SyncJob(Base):
    __tablename__ = "sync_jobs"
    __table_args__ = (
        CheckConstraint(
            "job_type IN ('sync_today_emails')",
            name="sync_jobs_job_type_check",
        ),
        CheckConstraint(
            "trigger_source IN ("
            "'manual', "
            "'scheduled', "
            "'refresh', "
            "'initial_sync', "
            "'oauth_callback', "
            "'system', "
            "'detail_view'"
            ")",
            name="sync_jobs_trigger_source_check",
        ),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
            name="sync_jobs_status_check",
        ),
        CheckConstraint("retry_count >= 0", name="sync_jobs_retry_count_check"),
        CheckConstraint(
            "jsonb_typeof(payload_json) = 'object'",
            name="sync_jobs_payload_json_object_check",
        ),
        UniqueConstraint("celery_task_id", name="sync_jobs_celery_task_id_uq"),
        Index("sync_jobs_mailbox_created_idx", "mailbox_id", text("created_at DESC")),
        Index("sync_jobs_status_created_idx", "status", text("created_at DESC")),
        Index("sync_jobs_target_date_idx", "mailbox_id", "target_date", "job_type"),
        Index(
            "sync_jobs_active_job_key_uq",
            "job_key",
            unique=True,
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    mailbox_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="CASCADE"), nullable=True
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(20), nullable=False)
    job_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()
    mailbox: Mapped["Mailbox"] = relationship()
