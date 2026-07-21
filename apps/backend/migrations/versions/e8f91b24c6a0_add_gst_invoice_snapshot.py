"""Add immutable GST tax-invoice snapshots and FY sequence.

Revision ID: e8f91b24c6a0
Revises: c2d8f4a91b73
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e8f91b24c6a0"
down_revision: str | None = "c2d8f4a91b73"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "invoice_number_sequences",
        sa.Column("financial_year", sa.String(7), primary_key=True),
        sa.Column("last_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    columns = [
        sa.Column("financial_year", sa.String(7), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=True),
        sa.Column("invoice_date", sa.Date(), nullable=True),
        sa.Column("supplier_legal_name", sa.String(255), nullable=True),
        sa.Column("supplier_address", sa.Text(), nullable=True),
        sa.Column("supplier_gstin", sa.String(15), nullable=True),
        sa.Column("supplier_state", sa.String(100), nullable=True),
        sa.Column("supplier_state_code", sa.String(2), nullable=True),
        sa.Column("recipient_legal_name", sa.String(255), nullable=True),
        sa.Column("recipient_address", sa.Text(), nullable=True),
        sa.Column("recipient_gstin", sa.String(15), nullable=True),
        sa.Column("recipient_state", sa.String(100), nullable=True),
        sa.Column("recipient_state_code", sa.String(2), nullable=True),
        sa.Column("place_of_supply", sa.String(100), nullable=True),
        sa.Column("place_of_supply_state_code", sa.String(2), nullable=True),
        sa.Column("sac_code", sa.String(8), nullable=True),
        sa.Column("service_description", sa.Text(), nullable=True),
        sa.Column("cgst_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("cgst_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sgst_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sgst_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("igst_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("igst_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reverse_charge", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("authorised_signatory", sa.String(255), nullable=True),
        sa.Column("rendered_html", sa.Text(), nullable=True),
        sa.Column("content_sha256", sa.String(64), nullable=True),
        sa.Column("issued_by_user_id", sa.Integer(), nullable=True),
    ]
    with op.batch_alter_table("invoices") as batch_op:
        for column in columns:
            batch_op.add_column(column)
        batch_op.create_foreign_key(
            "fk_invoices_issued_by_user_id", "users", ["issued_by_user_id"], ["id"], ondelete="RESTRICT"
        )
        batch_op.create_index("ix_invoices_financial_year", ["financial_year"])
        batch_op.create_index("ix_invoices_issued_by_user_id", ["issued_by_user_id"])
        batch_op.create_unique_constraint(
            "uq_invoices_financial_year_sequence", ["financial_year", "sequence_number"]
        )

    # Defence in depth: even SQL or a future endpoint cannot alter an issued row.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_issued_invoice_mutation()
        RETURNS trigger AS $$
        BEGIN
          IF OLD.status = 'issued' THEN
            RAISE EXCEPTION 'Issued invoices are immutable';
          END IF;
          IF TG_OP = 'DELETE' THEN
            RETURN OLD;
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_invoices_immutable
        BEFORE UPDATE OR DELETE ON invoices
        FOR EACH ROW EXECUTE FUNCTION prevent_issued_invoice_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_invoices_immutable ON invoices")
    op.execute("DROP FUNCTION IF EXISTS prevent_issued_invoice_mutation()")
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_constraint("uq_invoices_financial_year_sequence", type_="unique")
        batch_op.drop_index("ix_invoices_issued_by_user_id")
        batch_op.drop_index("ix_invoices_financial_year")
        batch_op.drop_constraint("fk_invoices_issued_by_user_id", type_="foreignkey")
        for name in [
            "issued_by_user_id", "content_sha256", "rendered_html", "authorised_signatory",
            "reverse_charge", "igst_amount", "igst_rate", "sgst_amount", "sgst_rate",
            "cgst_amount", "cgst_rate", "service_description", "sac_code",
            "place_of_supply_state_code", "place_of_supply", "recipient_state_code",
            "recipient_state", "recipient_gstin", "recipient_address", "recipient_legal_name",
            "supplier_state_code", "supplier_state", "supplier_gstin", "supplier_address",
            "supplier_legal_name", "invoice_date", "sequence_number", "financial_year",
        ]:
            batch_op.drop_column(name)
    op.drop_table("invoice_number_sequences")
