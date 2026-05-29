"""add last_alert_sent_at to attendance

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-05-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'h8i9j0k1l2m3'
down_revision = 'g7h8i9j0k1l2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'attendance',
        sa.Column('last_alert_sent_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('attendance', 'last_alert_sent_at')
