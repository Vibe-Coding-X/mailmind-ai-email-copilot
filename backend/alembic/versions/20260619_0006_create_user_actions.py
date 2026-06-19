"""create user actions

Revision ID: 20260619_0006
Revises: 20260619_0005
Create Date: 2026-06-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260619_0006"
down_revision: str | None = "20260619_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mailbox_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("digest_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("digest_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("action_status", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column(
            "provider_effect",
            sa.String(length=30),
            server_default="none",
            nullable=False,
        ),
        sa.Column(
            "before_state",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "after_state",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
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
        sa.CheckConstraint(
            "action_status IN ('pending', 'executed', 'failed', 'cancelled')",
            name="user_actions_action_status_check",
        ),
        sa.CheckConstraint(
            "source IN ('dashboard', 'email_detail', 'settings', 'system')",
            name="user_actions_source_check",
        ),
        sa.CheckConstraint(
            "provider_effect IN ("
            "'none', "
            "'local_only', "
            "'gmail_synced', "
            "'outlook_synced', "
            "'imap_synced'"
            ")",
            name="user_actions_provider_effect_check",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(before_state) = 'object'",
            name="user_actions_before_state_object_check",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(after_state) = 'object'",
            name="user_actions_after_state_object_check",
        ),
        sa.ForeignKeyConstraint(["digest_id"], ["daily_digests.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["digest_item_id"], ["digest_items.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "user_actions_user_created_idx",
        "user_actions",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "user_actions_digest_item_created_idx",
        "user_actions",
        ["digest_item_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "user_actions_email_created_idx",
        "user_actions",
        ["email_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "user_actions_status_created_idx",
        "user_actions",
        ["action_status", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("user_actions_status_created_idx", table_name="user_actions")
    op.drop_index("user_actions_email_created_idx", table_name="user_actions")
    op.drop_index("user_actions_digest_item_created_idx", table_name="user_actions")
    op.drop_index("user_actions_user_created_idx", table_name="user_actions")
    op.drop_table("user_actions")
