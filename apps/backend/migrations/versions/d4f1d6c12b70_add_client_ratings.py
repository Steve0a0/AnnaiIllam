"""add client ratings

Revision ID: d4f1d6c12b70
Revises: c8bcd9828176
Create Date: 2026-04-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4f1d6c12b70"
down_revision: Union[str, None] = "b68be383153e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_ratings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requirement_id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=True),
        sa.Column("worker_profile_id", sa.Integer(), nullable=True),
        sa.Column("rated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rated_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requirement_id"], ["requirements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["worker_profile_id"], ["worker_profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requirement_id", "rated_by_user_id", name="uq_client_rating_requirement_user"),
    )
    op.create_index(op.f("ix_client_ratings_assignment_id"), "client_ratings", ["assignment_id"], unique=False)
    op.create_index(op.f("ix_client_ratings_id"), "client_ratings", ["id"], unique=False)
    op.create_index(op.f("ix_client_ratings_rated_by_user_id"), "client_ratings", ["rated_by_user_id"], unique=False)
    op.create_index(op.f("ix_client_ratings_requirement_id"), "client_ratings", ["requirement_id"], unique=False)
    op.create_index(op.f("ix_client_ratings_worker_profile_id"), "client_ratings", ["worker_profile_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_client_ratings_worker_profile_id"), table_name="client_ratings")
    op.drop_index(op.f("ix_client_ratings_requirement_id"), table_name="client_ratings")
    op.drop_index(op.f("ix_client_ratings_rated_by_user_id"), table_name="client_ratings")
    op.drop_index(op.f("ix_client_ratings_id"), table_name="client_ratings")
    op.drop_index(op.f("ix_client_ratings_assignment_id"), table_name="client_ratings")
    op.drop_table("client_ratings")
