from datetime import date, datetime
from app.utils.time import utcnow

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    inspect,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text as sa_text

from app.db.session import Base


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        # Partial unique index — at most one non-cancelled invoice per requirement.
        # Uses postgresql_where so it is enforced at the DB level on PostgreSQL
        # and is a no-op on SQLite (used in tests) where partial indexes are unsupported.
        Index(
            "uq_invoice_active_per_requirement",
            "requirement_id",
            unique=True,
            postgresql_where=sa_text("status != 'cancelled'"),
        ),
        UniqueConstraint(
            "financial_year",
            "sequence_number",
            name="uq_invoices_financial_year_sequence",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("requirements.id", ondelete="RESTRICT"),
        index=True,
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("client_profiles.id", ondelete="RESTRICT"),
        index=True,
    )
    quote_id: Mapped[int] = mapped_column(
        ForeignKey("quotes.id", ondelete="RESTRICT"),
        index=True,
    )

    subtotal: Mapped[int] = mapped_column(Integer)
    gst_rate: Mapped[float] = mapped_column(Float, default=18.0)
    gst_amount: Mapped[int] = mapped_column(Integer)
    total_amount: Mapped[int] = mapped_column(Integer)

    # GST tax-invoice snapshot. These values are copied from configuration and
    # the client/requirement when the draft is created; issued rows are immutable.
    financial_year: Mapped[str | None] = mapped_column(String(7), nullable=True, index=True)
    sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    supplier_legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supplier_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplier_gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    supplier_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    supplier_state_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    recipient_legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipient_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipient_gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    recipient_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recipient_state_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    place_of_supply: Mapped[str | None] = mapped_column(String(100), nullable=True)
    place_of_supply_state_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    sac_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    service_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cgst_rate: Mapped[float] = mapped_column(Float, default=0.0)
    cgst_amount: Mapped[int] = mapped_column(Integer, default=0)
    sgst_rate: Mapped[float] = mapped_column(Float, default=0.0)
    sgst_amount: Mapped[int] = mapped_column(Integer, default=0)
    igst_rate: Mapped[float] = mapped_column(Float, default=0.0)
    igst_amount: Mapped[int] = mapped_column(Integer, default=0)
    reverse_charge: Mapped[bool] = mapped_column(Boolean, default=False)
    authorised_signatory: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rendered_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)

    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    pdf_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    issued_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class InvoiceNumberSequence(Base):
    """Transactionally allocated, per-financial-year invoice counter."""

    __tablename__ = "invoice_number_sequences"

    financial_year: Mapped[str] = mapped_column(String(7), primary_key=True)
    last_value: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


@event.listens_for(Invoice, "before_update")
def _prevent_issued_invoice_update(_mapper, _connection, invoice: Invoice) -> None:
    history = inspect(invoice).attrs.status.history
    prior_status = history.deleted[0] if history.deleted else invoice.status
    if prior_status == "issued":
        raise ValueError("Issued invoices are immutable")


@event.listens_for(Invoice, "before_delete")
def _prevent_issued_invoice_delete(_mapper, _connection, invoice: Invoice) -> None:
    if invoice.status == "issued":
        raise ValueError("Issued invoices are immutable")
