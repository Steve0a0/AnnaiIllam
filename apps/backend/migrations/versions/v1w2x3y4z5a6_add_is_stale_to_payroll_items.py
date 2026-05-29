"""Add is_stale to payroll_items

Revision ID: v1w2x3y4z5a6
Revises: u1v2w3x4y5z6
Create Date: 2026-05-27

"""
from alembic import op
import sqlalchemy as sa

revision = "v1w2x3y4z5a6"
down_revision = "u1v2w3x4y5z6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("payroll_items") as batch_op:
        batch_op.add_column(
            sa.Column("is_stale", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade() -> None:
    with op.batch_alter_table("payroll_items") as batch_op:
        batch_op.drop_column("is_stale")
