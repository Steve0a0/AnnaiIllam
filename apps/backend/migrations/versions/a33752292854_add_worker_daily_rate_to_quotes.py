"""add_worker_daily_rate_to_quotes

Revision ID: a33752292854
Revises: i9j0k1l2m3n4
Create Date: 2026-06-05 02:56:53.548668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a33752292854'
down_revision: Union[str, None] = 'i9j0k1l2m3n4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('quotes', sa.Column('worker_daily_rate', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('quotes', 'worker_daily_rate')
