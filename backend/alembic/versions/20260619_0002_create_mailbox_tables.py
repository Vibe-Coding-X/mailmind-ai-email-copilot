"""create mailbox tables

Revision ID: 20260619_0002
Revises: 20260618_0001
Create Date: 2026-06-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260619_0002"
down_revision: str | None = "20260618_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mailboxes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("provider_account_id", sa.String(length=255), nullable=False),
        sa.Column("email_address", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "permission_mode",
            sa.String(length=20),
            server_default="write_enabled",
            nullable=False,
        ),
        sa.Column(
            "granted_scopes",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_history_id", sa.String(length=128), nullable=True),
        sa.Column(
            "sync_cursor",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
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
            name="mailboxes_provider_check",
        ),
        sa.CheckConstraint(
            "permission_mode IN ('readonly', 'write_enabled')",
            name="mailboxes_permission_mode_check",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'reauth_required', 'disconnected', 'error')",
            name="mailboxes_status_check",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(sync_cursor) = 'object'",
            name="mailboxes_sync_cursor_object_check",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            "provider_account_id",
            name="mailboxes_user_provider_account_uq",
        ),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            "email_address",
            name="mailboxes_user_provider_email_uq",
        ),
    )
    op.create_index("mailboxes_user_status_idx", "mailboxes", ["user_id", "status"])

    op.create_table(
        "mailbox_credentials",
        sa.Column("mailbox_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("credential_type", sa.String(length=20), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("imap_password_encrypted", sa.Text(), nullable=True),
        sa.Column(
            "scopes_snapshot",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "credentials_json",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("encryption_key_version", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "credential_type IN ('oauth2', 'imap_password')",
            name="mailbox_credentials_type_check",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(credentials_json) = 'object'",
            name="mailbox_credentials_json_object_check",
        ),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("mailbox_id"),
    )


def downgrade() -> None:
    op.drop_table("mailbox_credentials")
    op.drop_index("mailboxes_user_status_idx", table_name="mailboxes")
    op.drop_table("mailboxes")
