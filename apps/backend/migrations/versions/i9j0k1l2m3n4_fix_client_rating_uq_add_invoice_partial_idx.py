"""Fix client_rating unique constraint; add partial unique index on invoices

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2025-01-01 00:00:00.000000

Changes:
  1. client_ratings: drop (requirement_id, rated_by_user_id) UQ, add (requirement_id, worker_profile_id) UQ
  2. invoices: add partial unique index enforcing one non-cancelled invoice per requirement
"""
from alembic import op

revision = 'i9j0k1l2m3n4'
down_revision = 'h8i9j0k1l2m3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Fix client_ratings unique constraint
    op.drop_constraint('uq_client_rating_requirement_user', 'client_ratings', type_='unique')
    op.create_unique_constraint(
        'uq_client_rating_requirement_worker',
        'client_ratings',
        ['requirement_id', 'worker_profile_id'],
    )

    # 2. Partial unique index on invoices — enforced at DB level on PostgreSQL only.
    #    Ensures at most one non-cancelled invoice per requirement.
    op.execute(
        "CREATE UNIQUE INDEX uq_invoice_active_per_requirement "
        "ON invoices (requirement_id) "
        "WHERE status != 'cancelled'"
    )


def downgrade() -> None:
    # 2. Remove partial unique index on invoices
    op.execute("DROP INDEX IF EXISTS uq_invoice_active_per_requirement")

    # 1. Revert client_ratings unique constraint
    op.drop_constraint('uq_client_rating_requirement_worker', 'client_ratings', type_='unique')
    op.create_unique_constraint(
        'uq_client_rating_requirement_user',
        'client_ratings',
        ['requirement_id', 'rated_by_user_id'],
    )
