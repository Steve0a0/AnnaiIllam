"""align workflow status values

Revision ID: d8c4f7712a61
Revises: a1b2c3d4e5f6
Create Date: 2026-04-30 04:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d8c4f7712a61"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE quotes SET status = 'draft' WHERE status = 'pending'")
    op.execute("UPDATE assignments SET status = 'active' WHERE status = 'in_progress'")
    op.execute("UPDATE attendance SET status = 'corrected' WHERE status = 'missed_checkout'")
    op.execute("UPDATE attendance SET status = 'absent' WHERE status = 'leave'")
    op.execute("UPDATE client_payments SET payment_status = 'pending' WHERE payment_status = 'partially_paid'")


def downgrade() -> None:
    op.execute("UPDATE quotes SET status = 'pending' WHERE status = 'draft'")
    op.execute("UPDATE assignments SET status = 'in_progress' WHERE status = 'active'")
    op.execute("UPDATE attendance SET status = 'missed_checkout' WHERE status = 'corrected'")
