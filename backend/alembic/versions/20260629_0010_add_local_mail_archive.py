"""add local mail archive

Revision ID: 20260629_0010
Revises: 20260624_0009
Create Date: 2026-06-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260629_0010"
down_revision: str | None = "20260624_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("emails", sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "emails",
        sa.Column("is_starred", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "emails",
        sa.Column("has_attachments", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "emails",
        sa.Column(
            "provider_metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column("emails", sa.Column("body_html", sa.Text(), nullable=True))
    op.add_column(
        "emails",
        sa.Column(
            "body_cache_status",
            sa.String(length=20),
            server_default="not_cached",
            nullable=False,
        ),
    )
    op.add_column(
        "emails", sa.Column("body_cached_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("emails", sa.Column("body_cache_source", sa.String(length=50), nullable=True))
    op.alter_column("emails", "is_starred", server_default=None)
    op.alter_column("emails", "has_attachments", server_default=None)
    op.alter_column("emails", "provider_metadata_json", server_default=None)
    op.alter_column("emails", "body_cache_status", server_default=None)

    op.drop_constraint("sync_jobs_job_type_check", "sync_jobs", type_="check")
    op.create_check_constraint(
        "sync_jobs_job_type_check",
        "sync_jobs",
        "job_type IN ("
        "'sync_today_emails', "
        "'email_archive_backfill', "
        "'generate_daily_digest', "
        "'refresh_daily_digest', "
        "'check_new_emails_after_digest', "
        "'refresh_access_token'"
        ")",
    )

    op.create_table(
        "mailbox_archive_states",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("mailbox_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="not_started", nullable=False),
        sa.Column(
            "cursor",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("newest_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("oldest_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_synced_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("batch_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_batch_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_batch_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=100), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "provider IN ('gmail', 'outlook', 'imap')",
            name="mailbox_archive_states_provider_check",
        ),
        sa.CheckConstraint(
            "status IN ('not_started', 'running', 'partial', 'complete', 'failed', 'canceled')",
            name="mailbox_archive_states_status_check",
        ),
        sa.CheckConstraint("total_synced_count >= 0", name="mailbox_archive_states_total_check"),
        sa.CheckConstraint("batch_count >= 0", name="mailbox_archive_states_batch_check"),
        sa.CheckConstraint(
            "jsonb_typeof(cursor) = 'object'",
            name="mailbox_archive_states_cursor_object_check",
        ),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "mailbox_archive_states_mailbox_uq",
        "mailbox_archive_states",
        ["mailbox_id"],
        unique=True,
    )
    op.create_index(
        "mailbox_archive_states_status_updated_idx",
        "mailbox_archive_states",
        ["status", "updated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "mailbox_archive_states_status_updated_idx",
        table_name="mailbox_archive_states",
    )
    op.drop_index("mailbox_archive_states_mailbox_uq", table_name="mailbox_archive_states")
    op.drop_table("mailbox_archive_states")

    op.drop_constraint("sync_jobs_job_type_check", "sync_jobs", type_="check")
    op.create_check_constraint(
        "sync_jobs_job_type_check",
        "sync_jobs",
        "job_type IN ("
        "'sync_today_emails', "
        "'generate_daily_digest', "
        "'refresh_daily_digest', "
        "'check_new_emails_after_digest', "
        "'refresh_access_token'"
        ")",
    )

    op.drop_column("emails", "body_cache_source")
    op.drop_column("emails", "body_cached_at")
    op.drop_column("emails", "body_cache_status")
    op.drop_column("emails", "body_html")
    op.drop_column("emails", "provider_metadata_json")
    op.drop_column("emails", "has_attachments")
    op.drop_column("emails", "is_starred")
    op.drop_column("emails", "sent_at")
