"""add client payment purpose

Revision ID: a4c8e91d2f30
Revises: a33752292854
Create Date: 2026-07-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4c8e91d2f30"
down_revision: Union[str, None] = "a33752292854"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "client_payments",
        sa.Column(
            "purpose",
            sa.String(length=50),
            server_default="adjustment",
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_client_payments_purpose"),
        "client_payments",
        ["purpose"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_client_payments_purpose"), table_name="client_payments")
    op.drop_column("client_payments", "purpose")
