"""add digest scope types

Revision ID: 20260624_0009
Revises: 20260624_0008
Create Date: 2026-06-24 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260624_0009"
down_revision: str | None = "20260624_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "daily_digests",
        sa.Column("scope_type", sa.String(length=20), server_default="mailbox", nullable=False),
    )
    op.execute("UPDATE daily_digests SET scope_type = 'mailbox' WHERE scope_type IS NULL")
    op.alter_column("daily_digests", "scope_type", server_default=None)
    op.alter_column("daily_digests", "mailbox_id", existing_type=sa.UUID(), nullable=True)
    op.alter_column("ai_runs", "mailbox_id", existing_type=sa.UUID(), nullable=True)

    op.drop_index("daily_digests_current_uq", table_name="daily_digests")
    op.drop_index("daily_digests_mailbox_date_idx", table_name="daily_digests")
    op.drop_index("daily_digests_current_lookup_idx", table_name="daily_digests")
    op.drop_constraint(
        "daily_digests_mailbox_date_version_uq",
        "daily_digests",
        type_="unique",
    )

    op.create_check_constraint(
        "daily_digests_scope_type_check",
        "daily_digests",
        "scope_type IN ('all', 'mailbox')",
    )
    op.create_check_constraint(
        "daily_digests_scope_mailbox_check",
        "daily_digests",
        "(scope_type = 'mailbox' AND mailbox_id IS NOT NULL) OR "
        "(scope_type = 'all' AND mailbox_id IS NULL)",
    )

    op.create_index(
        "daily_digests_mailbox_current_uq",
        "daily_digests",
        ["mailbox_id", "digest_date"],
        unique=True,
        postgresql_where=sa.text("scope_type = 'mailbox' AND is_current = true"),
    )
    op.create_index(
        "daily_digests_all_current_uq",
        "daily_digests",
        ["user_id", "digest_date"],
        unique=True,
        postgresql_where=sa.text("scope_type = 'all' AND is_current = true"),
    )
    op.create_index(
        "daily_digests_mailbox_date_version_uq",
        "daily_digests",
        ["mailbox_id", "digest_date", "version"],
        unique=True,
        postgresql_where=sa.text("scope_type = 'mailbox'"),
    )
    op.create_index(
        "daily_digests_all_date_version_uq",
        "daily_digests",
        ["user_id", "digest_date", "version"],
        unique=True,
        postgresql_where=sa.text("scope_type = 'all'"),
    )
    op.create_index(
        "daily_digests_current_lookup_idx",
        "daily_digests",
        ["user_id", "digest_date", "scope_type", "is_current"],
    )
    op.create_index(
        "daily_digests_mailbox_date_idx",
        "daily_digests",
        ["mailbox_id", sa.text("digest_date DESC"), sa.text("version DESC")],
        postgresql_where=sa.text("scope_type = 'mailbox'"),
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM user_actions "
        "WHERE digest_id IN (SELECT id FROM daily_digests WHERE scope_type = 'all')"
    )
    op.execute(
        "DELETE FROM digest_items "
        "WHERE digest_id IN (SELECT id FROM daily_digests WHERE scope_type = 'all')"
    )
    op.execute(
        "DELETE FROM ai_runs "
        "WHERE digest_id IN (SELECT id FROM daily_digests WHERE scope_type = 'all')"
    )
    op.execute(
        "UPDATE sync_jobs SET digest_id = NULL "
        "WHERE digest_id IN (SELECT id FROM daily_digests WHERE scope_type = 'all')"
    )
    op.execute("DELETE FROM daily_digests WHERE scope_type = 'all'")

    op.drop_index("daily_digests_mailbox_date_idx", table_name="daily_digests")
    op.drop_index("daily_digests_current_lookup_idx", table_name="daily_digests")
    op.drop_index("daily_digests_all_date_version_uq", table_name="daily_digests")
    op.drop_index("daily_digests_mailbox_date_version_uq", table_name="daily_digests")
    op.drop_index("daily_digests_all_current_uq", table_name="daily_digests")
    op.drop_index("daily_digests_mailbox_current_uq", table_name="daily_digests")
    op.drop_constraint("daily_digests_scope_mailbox_check", "daily_digests", type_="check")
    op.drop_constraint("daily_digests_scope_type_check", "daily_digests", type_="check")

    op.create_unique_constraint(
        "daily_digests_mailbox_date_version_uq",
        "daily_digests",
        ["mailbox_id", "digest_date", "version"],
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
    op.create_index(
        "daily_digests_current_uq",
        "daily_digests",
        ["mailbox_id", "digest_date"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )

    op.alter_column("ai_runs", "mailbox_id", existing_type=sa.UUID(), nullable=False)
    op.alter_column("daily_digests", "mailbox_id", existing_type=sa.UUID(), nullable=False)
    op.drop_column("daily_digests", "scope_type")
