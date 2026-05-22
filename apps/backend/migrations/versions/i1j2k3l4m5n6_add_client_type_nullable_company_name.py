"""add client_type and make company_name nullable

Revision ID: i1j2k3l4m5n6
Revises: h1i2j3k4l5m6
Create Date: 2026-05-15

"""

from alembic import op
import sqlalchemy as sa

revision = "i1j2k3l4m5n6"
down_revision = "h1i2j3k4l5m6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add client_type column (default 'company' for all existing rows)
    op.add_column(
        "client_profiles",
        sa.Column("client_type", sa.String(20), nullable=True, server_default="company"),
    )
    # Make company_name nullable (existing rows keep their values)
    op.alter_column("client_profiles", "company_name", nullable=True)


def downgrade() -> None:
    # Fill nulls before making non-nullable again
    op.execute(
        "UPDATE client_profiles SET company_name = contact_name WHERE company_name IS NULL"
    )
    op.alter_column("client_profiles", "company_name", nullable=False)
    op.drop_column("client_profiles", "client_type")
