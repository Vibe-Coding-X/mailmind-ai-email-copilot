"""add pending dispatch job statuses

Revision ID: 20260624_0008
Revises: 20260620_0007
Create Date: 2026-06-24 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260624_0008"
down_revision: str | None = "20260620_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("sync_jobs_active_job_key_uq", table_name="sync_jobs")
    op.drop_constraint("sync_jobs_status_check", "sync_jobs", type_="check")
    op.create_check_constraint(
        "sync_jobs_status_check",
        "sync_jobs",
        "status IN ("
        "'pending_dispatch', "
        "'queued', "
        "'running', "
        "'succeeded', "
        "'failed', "
        "'dispatch_failed', "
        "'cancelled'"
        ")",
    )
    op.create_index(
        "sync_jobs_active_job_key_uq",
        "sync_jobs",
        ["job_key"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending_dispatch', 'queued', 'running')"),
    )


def downgrade() -> None:
    op.execute(
        "UPDATE sync_jobs "
        "SET status = 'failed' "
        "WHERE status IN ('pending_dispatch', 'dispatch_failed')"
    )
    op.drop_index("sync_jobs_active_job_key_uq", table_name="sync_jobs")
    op.drop_constraint("sync_jobs_status_check", "sync_jobs", type_="check")
    op.create_check_constraint(
        "sync_jobs_status_check",
        "sync_jobs",
        "status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
    )
    op.create_index(
        "sync_jobs_active_job_key_uq",
        "sync_jobs",
        ["job_key"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )
