"""add geofence fields to requirements

Revision ID: j1k2l3m4n5o6
Revises: i1j2k3l4m5n6
Create Date: 2026-05-15

Adds three nullable columns to `requirements`:
  - site_latitude  (FLOAT)  — GPS latitude of the job site
  - site_longitude (FLOAT)  — GPS longitude of the job site
  - geofence_radius_meters (INTEGER, default 2000) — allowed check-in radius

When site_latitude and site_longitude are set and geofence_radius_meters > 0,
the backend enforces that a worker's check-in coordinates fall within the
radius before accepting the attendance record.
"""

from alembic import op
import sqlalchemy as sa

revision = "j1k2l3m4n5o6"
down_revision = "i1j2k3l4m5n6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("requirements", sa.Column("site_latitude", sa.Float(), nullable=True))
    op.add_column("requirements", sa.Column("site_longitude", sa.Float(), nullable=True))
    op.add_column(
        "requirements",
        sa.Column("geofence_radius_meters", sa.Integer(), nullable=True, server_default="2000"),
    )


def downgrade() -> None:
    op.drop_column("requirements", "geofence_radius_meters")
    op.drop_column("requirements", "site_longitude")
    op.drop_column("requirements", "site_latitude")
