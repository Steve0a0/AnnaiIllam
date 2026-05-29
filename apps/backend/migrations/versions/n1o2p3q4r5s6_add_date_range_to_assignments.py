"""add date range to assignments

Revision ID: n1o2p3q4r5s6
Revises: m1n2o3p4q5r6
Create Date: 2026-05-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'n1o2p3q4r5s6'
down_revision: Union[str, None] = 'm1n2o3p4q5r6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('assignments', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('assignments', sa.Column('end_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('assignments', 'end_date')
    op.drop_column('assignments', 'start_date')
