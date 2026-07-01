"""add email body cache error

Revision ID: 20260702_0011
Revises: 20260629_0010
Create Date: 2026-07-02 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260702_0011"
down_revision: str | None = "20260629_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("emails", sa.Column("body_cache_error", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("emails", "body_cache_error")
