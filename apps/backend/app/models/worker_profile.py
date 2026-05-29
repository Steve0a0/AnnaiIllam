from datetime import date, datetime
from app.utils.time import utcnow

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkerProfile(Base):
    __tablename__ = "worker_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    full_name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(100), index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    experience_years: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "1–2 years"
    experience_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    available_days: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    available_shifts: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)

    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Payment details — stored encrypted (AES-256 via Fernet)
    # Decrypt only when initiating a payout; never log or return in API responses
    upi_id_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    bank_account_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    bank_ifsc_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    bank_holder_name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # not sensitive

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
