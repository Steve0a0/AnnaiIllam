"""add worker onboarding fields

Adds:
  - users.onboarding_step (nullable String)
  - worker_profiles: experience_years, available_days, available_shifts,
                     upi_id_enc, bank_account_enc, bank_ifsc_enc, bank_holder_name
  - worker_documents: user_id (nullable FK), s3_key (nullable Text),
                      worker_profile_id made nullable

Revision ID: a3f7b2c9d1e0
Revises: f6a1d00b622a
Create Date: 2026-05-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3f7b2c9d1e0"
down_revision: Union[str, None] = "b9f3e2a1c8d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users — onboarding progress tracking
    op.add_column("users", sa.Column("onboarding_step", sa.String(length=50), nullable=True))
    op.create_index(op.f("ix_users_onboarding_step"), "users", ["onboarding_step"], unique=False)

    # worker_profiles — extended fields
    op.add_column("worker_profiles", sa.Column("experience_years", sa.String(length=50), nullable=True))
    op.add_column("worker_profiles", sa.Column("available_days", sa.String(length=100), nullable=True))
    op.add_column("worker_profiles", sa.Column("available_shifts", sa.String(length=100), nullable=True))
    op.add_column("worker_profiles", sa.Column("upi_id_enc", sa.Text(), nullable=True))
    op.add_column("worker_profiles", sa.Column("bank_account_enc", sa.Text(), nullable=True))
    op.add_column("worker_profiles", sa.Column("bank_ifsc_enc", sa.Text(), nullable=True))
    op.add_column("worker_profiles", sa.Column("bank_holder_name", sa.String(length=255), nullable=True))

    # worker_documents — allow docs before profile exists
    # Make worker_profile_id nullable
    op.alter_column("worker_documents", "worker_profile_id", nullable=True)
    # Add user_id FK
    op.add_column("worker_documents", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_worker_documents_user_id",
        "worker_documents",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_worker_documents_user_id"), "worker_documents", ["user_id"], unique=False)
    # Add s3_key column
    op.add_column("worker_documents", sa.Column("s3_key", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_index(op.f("ix_worker_documents_user_id"), table_name="worker_documents")
    op.drop_constraint("fk_worker_documents_user_id", "worker_documents", type_="foreignkey")
    op.drop_column("worker_documents", "user_id")
    op.drop_column("worker_documents", "s3_key")
    op.alter_column("worker_documents", "worker_profile_id", nullable=False)

    op.drop_column("worker_profiles", "bank_holder_name")
    op.drop_column("worker_profiles", "bank_ifsc_enc")
    op.drop_column("worker_profiles", "bank_account_enc")
    op.drop_column("worker_profiles", "upi_id_enc")
    op.drop_column("worker_profiles", "available_shifts")
    op.drop_column("worker_profiles", "available_days")
    op.drop_column("worker_profiles", "experience_years")

    op.drop_index(op.f("ix_users_onboarding_step"), table_name="users")
    op.drop_column("users", "onboarding_step")
