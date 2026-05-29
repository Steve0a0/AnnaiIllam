from datetime import date, datetime
from app.utils.time import utcnow

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
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

    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)

    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    pdf_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
