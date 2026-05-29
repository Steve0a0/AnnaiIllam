"""Add require_geofence to requirements.

Revision ID: s1t2u3v4w5x6
Revises: r1s2t3u4v5w6
Create Date: 2026-05-26

When True, check-in is blocked unless the job site has GPS coordinates
configured.  Defaults to False so existing jobs are unaffected.
"""

import sqlalchemy as sa
from alembic import op

revision = "s1t2u3v4w5x6"
down_revision = "r1s2t3u4v5w6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "requirements",
        sa.Column(
            "require_geofence",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("requirements", "require_geofence")
