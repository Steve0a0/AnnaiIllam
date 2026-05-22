"""add quote breakdown fields

Revision ID: c4e15d7b9a20
Revises: a3f7b2c9d1e0
Create Date: 2026-05-06 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c4e15d7b9a20"
down_revision: Union[str, None] = "a3f7b2c9d1e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("quotes", sa.Column("rate_per_worker", sa.Integer(), nullable=True))
    op.add_column("quotes", sa.Column("total_worker_days", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("quotes", "total_worker_days")
    op.drop_column("quotes", "rate_per_worker")
