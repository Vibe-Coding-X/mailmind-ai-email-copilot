from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MailboxArchiveState(Base):
    __tablename__ = "mailbox_archive_states"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('gmail', 'outlook', 'imap')",
            name="mailbox_archive_states_provider_check",
        ),
        CheckConstraint(
            "status IN ('not_started', 'running', 'partial', 'complete', 'failed', 'canceled')",
            name="mailbox_archive_states_status_check",
        ),
        CheckConstraint("total_synced_count >= 0", name="mailbox_archive_states_total_check"),
        CheckConstraint("batch_count >= 0", name="mailbox_archive_states_batch_check"),
        CheckConstraint(
            "jsonb_typeof(cursor) = 'object'",
            name="mailbox_archive_states_cursor_object_check",
        ),
        Index("mailbox_archive_states_mailbox_uq", "mailbox_id", unique=True),
        Index("mailbox_archive_states_status_updated_idx", "status", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_started", server_default="not_started"
    )
    cursor: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    newest_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    oldest_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total_synced_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    batch_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    last_batch_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_batch_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    mailbox: Mapped["Mailbox"] = relationship(back_populates="archive_state")
