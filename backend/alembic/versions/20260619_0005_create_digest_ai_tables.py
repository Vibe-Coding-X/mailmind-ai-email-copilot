"""create digest ai tables

Revision ID: 20260619_0005
Revises: 20260619_0004
Create Date: 2026-06-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260619_0005"
down_revision: str | None = "20260619_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


EMAIL_SYNC_JOB_TYPE_CHECK = "job_type IN ('sync_today_emails')"
DIGEST_JOB_TYPE_CHECK = (
    "job_type IN ("
    "'sync_today_emails', "
    "'generate_daily_digest', "
    "'refresh_daily_digest', "
    "'check_new_emails_after_digest', "
    "'refresh_access_token'"
    ")"
)


def upgrade() -> None:
    op.create_table(
        "daily_digests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mailbox_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("digest_date", sa.Date(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("trigger_source", sa.String(length=20), nullable=False),
        sa.Column(
            "generation_started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("coverage_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("coverage_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mail_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "new_mail_count_after_digest",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "overview_json",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('generating', 'fresh', 'stale', 'refreshing', 'failed')",
            name="daily_digests_status_check",
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
            name="daily_digests_trigger_source_check",
        ),
        sa.CheckConstraint("version > 0", name="daily_digests_version_check"),
        sa.CheckConstraint("mail_count >= 0", name="daily_digests_mail_count_check"),
        sa.CheckConstraint(
            "new_mail_count_after_digest >= 0",
            name="daily_digests_new_mail_count_check",
        ),
        sa.CheckConstraint(
            "coverage_end >= coverage_start",
            name="daily_digests_coverage_window_check",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(overview_json) = 'object'",
            name="daily_digests_overview_json_object_check",
        ),
        sa.CheckConstraint(
            "status NOT IN ('fresh', 'stale', 'refreshing') OR generated_at IS NOT NULL",
            name="daily_digests_generated_status_check",
        ),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "mailbox_id",
            "digest_date",
            "version",
            name="daily_digests_mailbox_date_version_uq",
        ),
    )
    op.create_index(
        "daily_digests_current_uq",
        "daily_digests",
        ["mailbox_id", "digest_date"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )
    op.create_index(
        "daily_digests_current_lookup_idx",
        "daily_digests",
        ["user_id", "digest_date", "is_current"],
    )
    op.create_index(
        "daily_digests_mailbox_date_idx",
        "daily_digests",
        ["mailbox_id", sa.text("digest_date DESC"), sa.text("version DESC")],
    )

    op.create_table(
        "digest_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("digest_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mailbox_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("section", sa.String(length=20), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=30), nullable=True),
        sa.Column("suggested_action", sa.String(length=50), nullable=True),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "item_type IN ('email', 'todo', 'risk')",
            name="digest_items_item_type_check",
        ),
        sa.CheckConstraint(
            "section IN ('urgent', 'review', 'ignore', 'todo', 'risk')",
            name="digest_items_section_check",
        ),
        sa.CheckConstraint(
            "category IS NULL OR category IN "
            "('work', 'notification', 'marketing', 'social', 'other')",
            name="digest_items_category_check",
        ),
        sa.CheckConstraint(
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
        sa.CheckConstraint(
            "priority IN ('high', 'medium', 'low')",
            name="digest_items_priority_check",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="digest_items_confidence_check",
        ),
        sa.CheckConstraint("display_order >= 0", name="digest_items_display_order_check"),
        sa.CheckConstraint(
            "item_type <> 'email' OR email_id IS NOT NULL",
            name="digest_items_email_item_email_id_check",
        ),
        sa.CheckConstraint(
            "section <> 'todo' OR item_type = 'todo'",
            name="digest_items_todo_section_check",
        ),
        sa.CheckConstraint(
            "section <> 'risk' OR item_type = 'risk'",
            name="digest_items_risk_section_check",
        ),
        sa.CheckConstraint(
            "section NOT IN ('urgent', 'review', 'ignore') OR item_type = 'email'",
            name="digest_items_email_section_check",
        ),
        sa.ForeignKeyConstraint(["digest_id"], ["daily_digests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "digest_items_email_current_uq",
        "digest_items",
        ["digest_id", "email_id"],
        unique=True,
        postgresql_where=sa.text("item_type = 'email'"),
    )
    op.create_index(
        "digest_items_digest_section_order_idx",
        "digest_items",
        ["digest_id", "section", "display_order"],
    )
    op.create_index(
        "digest_items_digest_priority_idx",
        "digest_items",
        ["digest_id", "priority", "display_order"],
    )
    op.create_index("digest_items_email_id_idx", "digest_items", ["email_id"])

    op.create_table(
        "ai_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mailbox_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("digest_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_type", sa.String(length=30), nullable=False),
        sa.Column("trigger_source", sa.String(length=20), nullable=False),
        sa.Column("model_provider", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("output_schema_version", sa.String(length=50), nullable=False),
        sa.Column("input_hash", sa.CHAR(length=64), nullable=False),
        sa.Column(
            "input_summary_json",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("output_json", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "run_type IN ('daily_digest', 'single_email', 'new_mail_preview')",
            name="ai_runs_run_type_check",
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
            name="ai_runs_trigger_source_check",
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
            name="ai_runs_status_check",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(input_summary_json) = 'object'",
            name="ai_runs_input_summary_json_object_check",
        ),
        sa.CheckConstraint(
            "prompt_tokens IS NULL OR prompt_tokens >= 0",
            name="ai_runs_prompt_tokens_check",
        ),
        sa.CheckConstraint(
            "completion_tokens IS NULL OR completion_tokens >= 0",
            name="ai_runs_completion_tokens_check",
        ),
        sa.CheckConstraint(
            "total_tokens IS NULL OR total_tokens >= 0",
            name="ai_runs_total_tokens_check",
        ),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="ai_runs_latency_ms_check",
        ),
        sa.CheckConstraint(
            "status <> 'succeeded' OR (output_json IS NOT NULL AND finished_at IS NOT NULL)",
            name="ai_runs_succeeded_output_check",
        ),
        sa.ForeignKeyConstraint(["digest_id"], ["daily_digests.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ai_runs_digest_created_idx",
        "ai_runs",
        ["digest_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ai_runs_mailbox_created_idx",
        "ai_runs",
        ["mailbox_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ai_runs_status_created_idx",
        "ai_runs",
        ["status", sa.text("created_at DESC")],
    )

    op.add_column(
        "sync_jobs",
        sa.Column("digest_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "sync_jobs_digest_id_fkey",
        "sync_jobs",
        "daily_digests",
        ["digest_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint("sync_jobs_job_type_check", "sync_jobs", type_="check")
    op.create_check_constraint(
        "sync_jobs_job_type_check",
        "sync_jobs",
        DIGEST_JOB_TYPE_CHECK,
    )
    op.create_index(
        "sync_jobs_digest_created_idx",
        "sync_jobs",
        ["digest_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("sync_jobs_digest_created_idx", table_name="sync_jobs")
    op.drop_constraint("sync_jobs_digest_id_fkey", "sync_jobs", type_="foreignkey")
    op.drop_column("sync_jobs", "digest_id")
    op.execute("DELETE FROM sync_jobs WHERE job_type <> 'sync_today_emails'")
    op.drop_constraint("sync_jobs_job_type_check", "sync_jobs", type_="check")
    op.create_check_constraint(
        "sync_jobs_job_type_check",
        "sync_jobs",
        EMAIL_SYNC_JOB_TYPE_CHECK,
    )

    op.drop_index("ai_runs_status_created_idx", table_name="ai_runs")
    op.drop_index("ai_runs_mailbox_created_idx", table_name="ai_runs")
    op.drop_index("ai_runs_digest_created_idx", table_name="ai_runs")
    op.drop_table("ai_runs")

    op.drop_index("digest_items_email_id_idx", table_name="digest_items")
    op.drop_index("digest_items_digest_priority_idx", table_name="digest_items")
    op.drop_index("digest_items_digest_section_order_idx", table_name="digest_items")
    op.drop_index("digest_items_email_current_uq", table_name="digest_items")
    op.drop_table("digest_items")

    op.drop_index("daily_digests_mailbox_date_idx", table_name="daily_digests")
    op.drop_index("daily_digests_current_lookup_idx", table_name="daily_digests")
    op.drop_index("daily_digests_current_uq", table_name="daily_digests")
    op.drop_table("daily_digests")
