"""Add durable gateway refund tracking to client payments.

Revision ID: c2d8f4a91b73
Revises: b7e1c42d9a60
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c2d8f4a91b73"
down_revision: str | None = "b7e1c42d9a60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("client_payments") as batch_op:
        batch_op.add_column(sa.Column("parent_payment_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("gateway_refund_id", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("refund_idempotency_key", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("gateway_refund_status", sa.String(50), nullable=True))
        batch_op.create_foreign_key(
            "fk_client_payments_parent_payment_id",
            "client_payments",
            ["parent_payment_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_unique_constraint(
            "uq_client_payments_gateway_refund_id",
            ["gateway_refund_id"],
        )
        batch_op.create_unique_constraint(
            "uq_client_payments_refund_idempotency_key",
            ["refund_idempotency_key"],
        )
        batch_op.create_index(
            "ix_client_payments_parent_payment_id",
            ["parent_payment_id"],
        )
        batch_op.create_index(
            "ix_client_payments_gateway_refund_id",
            ["gateway_refund_id"],
        )
        batch_op.create_index(
            "ix_client_payments_refund_idempotency_key",
            ["refund_idempotency_key"],
        )
        batch_op.create_index(
            "ix_client_payments_gateway_refund_status",
            ["gateway_refund_status"],
        )


def downgrade() -> None:
    with op.batch_alter_table("client_payments") as batch_op:
        batch_op.drop_index("ix_client_payments_gateway_refund_status")
        batch_op.drop_index("ix_client_payments_refund_idempotency_key")
        batch_op.drop_index("ix_client_payments_gateway_refund_id")
        batch_op.drop_index("ix_client_payments_parent_payment_id")
        batch_op.drop_constraint(
            "uq_client_payments_refund_idempotency_key",
            type_="unique",
        )
        batch_op.drop_constraint(
            "uq_client_payments_gateway_refund_id",
            type_="unique",
        )
        batch_op.drop_constraint(
            "fk_client_payments_parent_payment_id",
            type_="foreignkey",
        )
        batch_op.drop_column("gateway_refund_status")
        batch_op.drop_column("refund_idempotency_key")
        batch_op.drop_column("gateway_refund_id")
        batch_op.drop_column("parent_payment_id")
