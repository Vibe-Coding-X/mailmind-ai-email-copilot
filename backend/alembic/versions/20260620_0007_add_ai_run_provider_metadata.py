"""add ai run provider metadata

Revision ID: 20260620_0007
Revises: 20260619_0006
Create Date: 2026-06-20 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260620_0007"
down_revision: str | None = "20260619_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_runs", sa.Column("provider_id", sa.String(length=50), nullable=True))
    op.add_column(
        "ai_runs", sa.Column("provider_type", sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("ai_runs", "provider_type")
    op.drop_column("ai_runs", "provider_id")
