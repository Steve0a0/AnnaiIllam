"""Add check constraint on client_ratings.rating (1–5 integers only).

Revision ID: t1u2v3w4x5y6
Revises: s1t2u3v4w5x6
Create Date: 2026-05-26

Before applying this migration to production, verify no out-of-range rows exist:
    SELECT id, rating FROM client_ratings WHERE rating < 1 OR rating > 5;
If any rows are returned, correct them before running this migration.
"""

from alembic import op

revision: str = "t1u2v3w4x5y6"
down_revision: str = "s1t2u3v4w5x6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_alter_table provides SQLite compatibility for tests;
    # on PostgreSQL Alembic emits a native ADD CONSTRAINT statement.
    with op.batch_alter_table("client_ratings") as batch_op:
        batch_op.create_check_constraint(
            "ck_client_ratings_rating_range",
            "rating >= 1 AND rating <= 5",
        )


def downgrade() -> None:
    with op.batch_alter_table("client_ratings") as batch_op:
        batch_op.drop_constraint("ck_client_ratings_rating_range", type_="check")
