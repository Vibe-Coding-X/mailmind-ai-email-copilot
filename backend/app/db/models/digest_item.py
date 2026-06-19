from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DigestItem(Base):
    __tablename__ = "digest_items"
    __table_args__ = (
        CheckConstraint(
            "item_type IN ('email', 'todo', 'risk')",
            name="digest_items_item_type_check",
        ),
        CheckConstraint(
            "section IN ('urgent', 'review', 'ignore', 'todo', 'risk')",
            name="digest_items_section_check",
        ),
        CheckConstraint(
            "category IS NULL OR category IN "
            "('work', 'notification', 'marketing', 'social', 'other')",
            name="digest_items_category_check",
        ),
        CheckConstraint(
            "suggested_action IS NULL OR suggested_action IN ("
            "'reply_today', "
            "'review_today', "
            "'handle_before_deadline', "
            "'ignore', "
            "'archive_candidate', "
            "'follow_up_later', "
            "'no_action_required'"
            ")",
            name="digest_items_suggested_action_check",
        ),
        CheckConstraint(
            "priority IN ('high', 'medium', 'low')",
            name="digest_items_priority_check",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="digest_items_confidence_check",
        ),
        CheckConstraint("display_order >= 0", name="digest_items_display_order_check"),
        CheckConstraint(
            "item_type <> 'email' OR email_id IS NOT NULL",
            name="digest_items_email_item_email_id_check",
        ),
        CheckConstraint(
            "section <> 'todo' OR item_type = 'todo'",
            name="digest_items_todo_section_check",
        ),
        CheckConstraint(
            "section <> 'risk' OR item_type = 'risk'",
            name="digest_items_risk_section_check",
        ),
        CheckConstraint(
            "section NOT IN ('urgent', 'review', 'ignore') OR item_type = 'email'",
            name="digest_items_email_section_check",
        ),
        Index(
            "digest_items_email_current_uq",
            "digest_id",
            "email_id",
            unique=True,
            postgresql_where=text("item_type = 'email'"),
        ),
        Index(
            "digest_items_digest_section_order_idx",
            "digest_id",
            "section",
            "display_order",
        ),
        Index(
            "digest_items_digest_priority_idx",
            "digest_id",
            "priority",
            "display_order",
        ),
        Index("digest_items_email_id_idx", "email_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    digest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("daily_digests.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="CASCADE"), nullable=False
    )
    email_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emails.id", ondelete="CASCADE"), nullable=True
    )
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    section: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    suggested_action: Mapped[str | None] = mapped_column(String(50), nullable=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    digest: Mapped["DailyDigest"] = relationship(back_populates="items")
    user: Mapped["User"] = relationship()
    mailbox: Mapped["Mailbox"] = relationship()
    email: Mapped["Email"] = relationship()
