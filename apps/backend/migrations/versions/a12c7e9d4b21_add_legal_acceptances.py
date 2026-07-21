"""Add immutable, versioned legal acceptance records.

Revision ID: a12c7e9d4b21
Revises: f4b2c7d91a30
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a12c7e9d4b21"
down_revision: str | None = "f4b2c7d91a30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "legal_acceptances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("document_slug", sa.String(50), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "user_id",
            "document_slug",
            "version",
            name="uq_legal_acceptances_user_document_version",
        ),
    )
    op.create_index("ix_legal_acceptances_id", "legal_acceptances", ["id"])
    op.create_index("ix_legal_acceptances_user_id", "legal_acceptances", ["user_id"])
    op.create_index("ix_legal_acceptances_role", "legal_acceptances", ["role"])
    op.create_index(
        "ix_legal_acceptances_document_slug", "legal_acceptances", ["document_slug"]
    )
    op.create_index("ix_legal_acceptances_version", "legal_acceptances", ["version"])
    op.create_index(
        "ix_legal_acceptances_accepted_at", "legal_acceptances", ["accepted_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_legal_acceptances_accepted_at", table_name="legal_acceptances")
    op.drop_index("ix_legal_acceptances_version", table_name="legal_acceptances")
    op.drop_index("ix_legal_acceptances_document_slug", table_name="legal_acceptances")
    op.drop_index("ix_legal_acceptances_role", table_name="legal_acceptances")
    op.drop_index("ix_legal_acceptances_user_id", table_name="legal_acceptances")
    op.drop_index("ix_legal_acceptances_id", table_name="legal_acceptances")
    op.drop_table("legal_acceptances")

