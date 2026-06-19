from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('gmail', 'outlook', 'imap')",
            name="emails_provider_check",
        ),
        CheckConstraint(
            "jsonb_typeof(to_addresses) = 'array'",
            name="emails_to_addresses_array_check",
        ),
        CheckConstraint(
            "jsonb_typeof(cc_addresses) = 'array'",
            name="emails_cc_addresses_array_check",
        ),
        UniqueConstraint(
            "mailbox_id",
            "external_id",
            name="emails_mailbox_external_id_uq",
        ),
        Index("emails_mailbox_received_idx", "mailbox_id", text("received_at DESC")),
        Index("emails_user_received_idx", "user_id", text("received_at DESC")),
        Index("emails_mailbox_thread_idx", "mailbox_id", "external_thread_id"),
        Index(
            "emails_mailbox_read_received_idx",
            "mailbox_id",
            "is_read",
            text("received_at DESC"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    internet_message_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    from_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    from_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_addresses: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    cc_addresses: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_text_truncated: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="false"
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_read: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    provider_labels: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default="{}"
    )
    gmail_history_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    first_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship()
    mailbox: Mapped["Mailbox"] = relationship()
