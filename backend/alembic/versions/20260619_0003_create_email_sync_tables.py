"""create email sync tables

Revision ID: 20260619_0003
Revises: 20260619_0002
Create Date: 2026-06-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260619_0003"
down_revision: str | None = "20260619_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "emails",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mailbox_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("external_thread_id", sa.String(length=255), nullable=True),
        sa.Column("internet_message_id", sa.String(length=500), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("from_name", sa.String(length=255), nullable=True),
        sa.Column("from_address", sa.String(length=255), nullable=True),
        sa.Column(
            "to_addresses",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "cc_addresses",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column(
            "body_text_truncated",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "provider_labels",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("gmail_history_id", sa.String(length=128), nullable=True),
        sa.Column(
            "first_synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "provider IN ('gmail', 'outlook', 'imap')",
            name="emails_provider_check",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(to_addresses) = 'array'",
            name="emails_to_addresses_array_check",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(cc_addresses) = 'array'",
            name="emails_cc_addresses_array_check",
        ),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "mailbox_id",
            "external_id",
            name="emails_mailbox_external_id_uq",
        ),
    )
    op.create_index("emails_mailbox_received_idx", "emails", ["mailbox_id", sa.text("received_at DESC")])
    op.create_index("emails_user_received_idx", "emails", ["user_id", sa.text("received_at DESC")])
    op.create_index("emails_mailbox_thread_idx", "emails", ["mailbox_id", "external_thread_id"])
    op.create_index(
        "emails_mailbox_read_received_idx",
        "emails",
        ["mailbox_id", "is_read", sa.text("received_at DESC")],
    )

    op.create_table(
        "sync_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mailbox_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("digest_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("trigger_source", sa.String(length=20), nullable=False),
        sa.Column("job_key", sa.String(length=255), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "payload_json",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "job_type IN ("
            "'sync_today_emails', "
            "'generate_daily_digest', "
            "'refresh_daily_digest', "
            "'check_new_emails_after_digest', "
            "'refresh_access_token'"
            ")",
            name="sync_jobs_job_type_check",
        ),
        sa.CheckConstraint(
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
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
            name="sync_jobs_status_check",
        ),
        sa.CheckConstraint("retry_count >= 0", name="sync_jobs_retry_count_check"),
        sa.CheckConstraint(
            "jsonb_typeof(payload_json) = 'object'",
            name="sync_jobs_payload_json_object_check",
        ),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("celery_task_id", name="sync_jobs_celery_task_id_uq"),
    )
    op.create_index(
        "sync_jobs_active_job_key_uq",
        "sync_jobs",
        ["job_key"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )
    op.create_index(
        "sync_jobs_mailbox_created_idx",
        "sync_jobs",
        ["mailbox_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "sync_jobs_digest_created_idx",
        "sync_jobs",
        ["digest_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "sync_jobs_status_created_idx",
        "sync_jobs",
        ["status", sa.text("created_at DESC")],
    )
    op.create_index(
        "sync_jobs_target_date_idx",
        "sync_jobs",
        ["mailbox_id", "target_date", "job_type"],
    )


def downgrade() -> None:
    op.drop_index("sync_jobs_target_date_idx", table_name="sync_jobs")
    op.drop_index("sync_jobs_status_created_idx", table_name="sync_jobs")
    op.drop_index("sync_jobs_digest_created_idx", table_name="sync_jobs")
    op.drop_index("sync_jobs_mailbox_created_idx", table_name="sync_jobs")
    op.drop_index("sync_jobs_active_job_key_uq", table_name="sync_jobs")
    op.drop_table("sync_jobs")

    op.drop_index("emails_mailbox_read_received_idx", table_name="emails")
    op.drop_index("emails_mailbox_thread_idx", table_name="emails")
    op.drop_index("emails_user_received_idx", table_name="emails")
    op.drop_index("emails_mailbox_received_idx", table_name="emails")
    op.drop_table("emails")
