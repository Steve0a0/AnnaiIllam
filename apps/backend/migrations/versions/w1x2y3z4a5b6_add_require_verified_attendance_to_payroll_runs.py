"""Add require_verified_attendance to payroll_runs

Revision ID: w1x2y3z4a5b6
Revises: v1w2x3y4z5a6
Create Date: 2026-05-27

"""
from alembic import op
import sqlalchemy as sa

revision = "w1x2y3z4a5b6"
down_revision = "v1w2x3y4z5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("payroll_runs") as batch_op:
        batch_op.add_column(
            sa.Column(
                "require_verified_attendance",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("payroll_runs") as batch_op:
        batch_op.drop_column("require_verified_attendance")
