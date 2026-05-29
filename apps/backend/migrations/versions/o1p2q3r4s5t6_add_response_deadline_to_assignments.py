"""Add response_deadline to assignments.

Revision ID: o1p2q3r4s5t6
Revises: n1o2p3q4r5s6
Create Date: 2026-05-25

Adds a nullable response_deadline (DateTime) to assignments. When set, the admin
dashboard surfaces an overdue badge if the worker hasn't responded by this time.
"""

import sqlalchemy as sa
from alembic import op

revision = "o1p2q3r4s5t6"
down_revision = "n1o2p3q4r5s6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("assignments") as batch_op:
        batch_op.add_column(sa.Column("response_deadline", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("assignments") as batch_op:
        batch_op.drop_column("response_deadline")
