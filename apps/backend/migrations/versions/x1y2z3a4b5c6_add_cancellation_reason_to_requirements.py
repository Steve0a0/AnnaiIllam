"""add cancellation_reason to requirements

Revision ID: x1y2z3a4b5c6
Revises: w1x2y3z4a5b6
Create Date: 2026-05-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'x1y2z3a4b5c6'
down_revision = 'w1x2y3z4a5b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('requirements', sa.Column('cancellation_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('requirements', 'cancellation_reason')
