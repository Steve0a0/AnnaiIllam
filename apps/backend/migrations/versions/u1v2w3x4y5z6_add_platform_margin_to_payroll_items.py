"""add platform_margin to payroll_items

Revision ID: u1v2w3x4y5z6
Revises: t1u2v3w4x5y6
Create Date: 2025-07-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "u1v2w3x4y5z6"
down_revision: Union[str, None] = "t1u2v3w4x5y6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("payroll_items") as batch_op:
        batch_op.add_column(sa.Column("platform_margin", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("payroll_items") as batch_op:
        batch_op.drop_column("platform_margin")
