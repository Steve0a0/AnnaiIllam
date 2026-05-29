"""add sla_hours and sla_breach_notified_at to requirements

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-05-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'g7h8i9j0k1l2'
down_revision = 'f6g7h8i9j0k1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'requirements',
        sa.Column('sla_hours', sa.Integer(), nullable=False, server_default='24'),
    )
    op.add_column(
        'requirements',
        sa.Column('sla_breach_notified_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('requirements', 'sla_breach_notified_at')
    op.drop_column('requirements', 'sla_hours')
