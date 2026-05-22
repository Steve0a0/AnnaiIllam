from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    client_type: Mapped[str | None] = mapped_column(String(20), nullable=True, server_default="company")  # 'individual' | 'company'
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    contact_name: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(100), index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    gst_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Extended fields
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_job_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    food_preference: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    accommodation_preference: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    standing_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
