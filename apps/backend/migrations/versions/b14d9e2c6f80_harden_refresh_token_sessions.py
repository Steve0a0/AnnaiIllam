"""Harden refresh-token rotation with session-family reuse detection.

Revision ID: b14d9e2c6f80
Revises: a12c7e9d4b21
"""

from collections.abc import Sequence
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = "b14d9e2c6f80"
down_revision: str | None = "a12c7e9d4b21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("refresh_tokens", sa.Column("family_id", sa.String(64), nullable=True))
    op.add_column(
        "refresh_tokens",
        sa.Column("replaced_by_token_id", sa.Integer(), nullable=True),
    )
    op.add_column("refresh_tokens", sa.Column("revoked_at", sa.DateTime(), nullable=True))
    op.add_column("refresh_tokens", sa.Column("revoke_reason", sa.String(50), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id FROM refresh_tokens")).fetchall()
    for (token_id,) in rows:
        connection.execute(
            sa.text("UPDATE refresh_tokens SET family_id = :family_id WHERE id = :token_id"),
            {"family_id": uuid4().hex, "token_id": token_id},
        )

    op.alter_column("refresh_tokens", "family_id", existing_type=sa.String(64), nullable=False)
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])
    op.create_foreign_key(
        "fk_refresh_tokens_replaced_by_token_id",
        "refresh_tokens",
        "refresh_tokens",
        ["replaced_by_token_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_refresh_tokens_replaced_by_token_id",
        "refresh_tokens",
        type_="foreignkey",
    )
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "revoke_reason")
    op.drop_column("refresh_tokens", "revoked_at")
    op.drop_column("refresh_tokens", "replaced_by_token_id")
    op.drop_column("refresh_tokens", "family_id")
