from datetime import date, datetime
from app.utils.time import utcnow

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), index=True)

    quoted_amount: Mapped[int] = mapped_column(Integer)
    rate_per_worker: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_worker_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    advance_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_model: Mapped[str] = mapped_column(String(50))
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    terms_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)

    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
