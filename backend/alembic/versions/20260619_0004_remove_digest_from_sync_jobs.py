"""remove digest scope from sync jobs

Revision ID: 20260619_0004
Revises: 20260619_0003
Create Date: 2026-06-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260619_0004"
down_revision: str | None = "20260619_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


OLD_JOB_TYPE_CHECK = (
    "job_type IN ("
    "'sync_today_emails', "
    "'generate_daily_digest', "
    "'refresh_daily_digest', "
    "'check_new_emails_after_digest', "
    "'refresh_access_token'"
    ")"
)
NEW_JOB_TYPE_CHECK = "job_type IN ('sync_today_emails')"


def upgrade() -> None:
    op.drop_index("sync_jobs_digest_created_idx", table_name="sync_jobs")
    op.drop_constraint("sync_jobs_job_type_check", "sync_jobs", type_="check")
    op.create_check_constraint(
        "sync_jobs_job_type_check",
        "sync_jobs",
        NEW_JOB_TYPE_CHECK,
    )
    op.drop_column("sync_jobs", "digest_id")


def downgrade() -> None:
    op.add_column(
        "sync_jobs",
        sa.Column("digest_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.drop_constraint("sync_jobs_job_type_check", "sync_jobs", type_="check")
    op.create_check_constraint(
        "sync_jobs_job_type_check",
        "sync_jobs",
        OLD_JOB_TYPE_CHECK,
    )
    op.create_index(
        "sync_jobs_digest_created_idx",
        "sync_jobs",
        ["digest_id", sa.text("created_at DESC")],
    )
