"""add client profile preferences

Revision ID: h1i2j3k4l5m6
Revises: g1h2i3j4k5l6
Create Date: 2026-05-15 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h1i2j3k4l5m6"
down_revision: Union[str, None] = "g1h2i3j4k5l6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("client_profiles", sa.Column("industry", sa.String(length=100), nullable=True))
    op.add_column("client_profiles", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("client_profiles", sa.Column("default_job_category", sa.String(length=100), nullable=True))
    op.add_column(
        "client_profiles",
        sa.Column("food_preference", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "client_profiles",
        sa.Column("accommodation_preference", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("client_profiles", sa.Column("standing_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("client_profiles", "standing_notes")
    op.drop_column("client_profiles", "accommodation_preference")
    op.drop_column("client_profiles", "food_preference")
    op.drop_column("client_profiles", "default_job_category")
    op.drop_column("client_profiles", "email")
    op.drop_column("client_profiles", "industry")
