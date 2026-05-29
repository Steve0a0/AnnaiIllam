"""Add permission_group to admin_profiles.

Revision ID: q1r2s3t4u5v6
Revises: p1q2r3s4t5u6
Create Date: 2026-05-26

Adds a non-nullable permission_group VARCHAR column to admin_profiles.
Existing rows default to 'ops_admin' so no operational access is lost.
Allowed values enforced at application layer:
  super_admin | ops_admin | finance_admin | viewer
"""

import sqlalchemy as sa
from alembic import op

revision = "q1r2s3t4u5v6"
down_revision = "p1q2r3s4t5u6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='admin_profiles' AND column_name='permission_group'"
        )
    ).fetchone()
    if result is None:
        op.add_column(
            "admin_profiles",
            sa.Column(
                "permission_group",
                sa.String(length=50),
                nullable=False,
                server_default="ops_admin",
            ),
        )


def downgrade() -> None:
    op.drop_column("admin_profiles", "permission_group")
