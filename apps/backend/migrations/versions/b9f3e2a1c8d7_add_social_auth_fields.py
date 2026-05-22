"""add social auth fields to users

Revision ID: b9f3e2a1c8d7
Revises: d8c4f7712a61
Create Date: 2026-04-30 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b9f3e2a1c8d7"
down_revision: Union[str, None] = "d8c4f7712a61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("google_id", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("apple_id", sa.String(length=255), nullable=True))
    op.add_column(
        "users",
        sa.Column("is_email_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.alter_column("users", "is_email_verified", server_default=None)

    # phone is now optional (social users have no phone)
    op.alter_column("users", "phone", existing_type=sa.String(length=20), nullable=True)

    # Email gets a unique constraint (was already in the model but may not have been enforced)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)
    op.create_index(op.f("ix_users_apple_id"), "users", ["apple_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_apple_id"), table_name="users")
    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")

    op.alter_column("users", "phone", existing_type=sa.String(length=20), nullable=False)

    op.drop_column("users", "is_email_verified")
    op.drop_column("users", "apple_id")
    op.drop_column("users", "google_id")
    op.drop_column("users", "name")
