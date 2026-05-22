"""add photo_url to worker_profiles

Revision ID: l1m2n3o4p5q6
Revises: k1l2m3n4o5p6
Create Date: 2026-05-20 00:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "l1m2n3o4p5q6"
down_revision: Union[str, None] = "k1l2m3n4o5p6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "worker_profiles",
        sa.Column("photo_url", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("worker_profiles", "photo_url")
