from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DailyDigest(Base):
    __tablename__ = "daily_digests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('generating', 'fresh', 'stale', 'refreshing', 'failed')",
            name="daily_digests_status_check",
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
            name="daily_digests_trigger_source_check",
        ),
        CheckConstraint("version > 0", name="daily_digests_version_check"),
        CheckConstraint("mail_count >= 0", name="daily_digests_mail_count_check"),
        CheckConstraint(
            "new_mail_count_after_digest >= 0",
            name="daily_digests_new_mail_count_check",
        ),
        CheckConstraint(
            "coverage_end >= coverage_start",
            name="daily_digests_coverage_window_check",
        ),
        CheckConstraint(
            "jsonb_typeof(overview_json) = 'object'",
            name="daily_digests_overview_json_object_check",
        ),
        CheckConstraint(
            "status NOT IN ('fresh', 'stale', 'refreshing') OR generated_at IS NOT NULL",
            name="daily_digests_generated_status_check",
        ),
        UniqueConstraint(
            "mailbox_id",
            "digest_date",
            "version",
            name="daily_digests_mailbox_date_version_uq",
        ),
        Index(
            "daily_digests_current_uq",
            "mailbox_id",
            "digest_date",
            unique=True,
            postgresql_where=text("is_current = true"),
        ),
        Index("daily_digests_current_lookup_idx", "user_id", "digest_date", "is_current"),
        Index(
            "daily_digests_mailbox_date_idx",
            "mailbox_id",
            text("digest_date DESC"),
            text("version DESC"),
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
    digest_date: Mapped[date] = mapped_column(Date, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(20), nullable=False)
    generation_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    coverage_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    coverage_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mail_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    new_mail_count_after_digest: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    overview_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship()
    mailbox: Mapped["Mailbox"] = relationship()
    items: Mapped[list["DigestItem"]] = relationship(
        back_populates="digest", cascade="all, delete-orphan"
    )
    ai_runs: Mapped[list["AIRun"]] = relationship(back_populates="digest")
