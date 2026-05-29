"""Add rejection_reason to requirements.

Revision ID: r1s2t3u4v5w6
Revises: q1r2s3t4u5v6
Create Date: 2026-05-26

Adds a nullable TEXT column to store the reason when an admin rejects
a requirement.  Existing rows receive NULL (no rejection reason).
"""

import sqlalchemy as sa
from alembic import op

revision = "r1s2t3u4v5w6"
down_revision = "q1r2s3t4u5v6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "requirements",
        sa.Column("rejection_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("requirements", "rejection_reason")
