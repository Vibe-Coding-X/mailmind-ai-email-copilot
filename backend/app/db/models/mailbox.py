from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Mailbox(Base):
    __tablename__ = "mailboxes"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('gmail', 'outlook', 'imap')",
            name="mailboxes_provider_check",
        ),
        CheckConstraint(
            "permission_mode IN ('readonly', 'write_enabled')",
            name="mailboxes_permission_mode_check",
        ),
        CheckConstraint(
            "status IN ('active', 'reauth_required', 'disconnected', 'error')",
            name="mailboxes_status_check",
        ),
        CheckConstraint(
            "jsonb_typeof(sync_cursor) = 'object'",
            name="mailboxes_sync_cursor_object_check",
        ),
        Index("mailboxes_user_status_idx", "user_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    email_address: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    permission_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="write_enabled", server_default="write_enabled"
    )
    granted_scopes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default="{}"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_history_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sync_cursor: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="mailboxes")
    credential: Mapped["MailboxCredential"] = relationship(
        back_populates="mailbox", cascade="all, delete-orphan", uselist=False
    )
