"""add revoked_access_tokens table

Revision ID: k1l2m3n4o5p6
Revises: j1k2l3m4n5o6
Create Date: 2026-05-15

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "k1l2m3n4o5p6"
down_revision: str | None = "j1k2l3m4n5o6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "revoked_access_tokens",
        sa.Column("jti", sa.String(64), primary_key=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_revoked_access_tokens_jti", "revoked_access_tokens", ["jti"])


def downgrade() -> None:
    op.drop_index("ix_revoked_access_tokens_jti", table_name="revoked_access_tokens")
    op.drop_table("revoked_access_tokens")
