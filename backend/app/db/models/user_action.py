from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserAction(Base):
    __tablename__ = "user_actions"
    __table_args__ = (
        CheckConstraint(
            "action_type IN ("
            "'open_email_detail', "
            "'open_provider_message', "
            "'mark_read', "
            "'mark_unread', "
            "'dismiss_item', "
            "'snooze_item', "
            "'mark_done', "
            "'generate_digest', "
            "'refresh_digest', "
            "'disconnect_mailbox'"
            ")",
            name="user_actions_action_type_check",
        ),
        CheckConstraint(
            "action_status IN ('pending', 'executed', 'failed', 'cancelled')",
            name="user_actions_action_status_check",
        ),
        CheckConstraint(
            "source IN ('dashboard', 'email_detail', 'settings', 'system')",
            name="user_actions_source_check",
        ),
        CheckConstraint(
            "provider_effect IN ("
            "'none', "
            "'local_only', "
            "'gmail_synced', "
            "'outlook_synced', "
            "'imap_synced'"
            ")",
            name="user_actions_provider_effect_check",
        ),
        CheckConstraint(
            "jsonb_typeof(before_state) = 'object'",
            name="user_actions_before_state_object_check",
        ),
        CheckConstraint(
            "jsonb_typeof(after_state) = 'object'",
            name="user_actions_after_state_object_check",
        ),
        Index("user_actions_user_created_idx", "user_id", text("created_at DESC")),
        Index(
            "user_actions_digest_item_created_idx",
            "digest_item_id",
            text("created_at DESC"),
        ),
        Index("user_actions_email_created_idx", "email_id", text("created_at DESC")),
        Index(
            "user_actions_status_created_idx",
            "action_status",
            text("created_at DESC"),
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
    digest_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("daily_digests.id", ondelete="SET NULL"),
        nullable=True,
    )
    digest_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("digest_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    email_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emails.id", ondelete="SET NULL"), nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action_status: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_effect: Mapped[str] = mapped_column(
        String(30), nullable=False, default="none", server_default="none"
    )
    before_state: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    after_state: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship()
    mailbox: Mapped["Mailbox"] = relationship()
    digest: Mapped["DailyDigest"] = relationship()
    digest_item: Mapped["DigestItem"] = relationship()
    email: Mapped["Email"] = relationship()
