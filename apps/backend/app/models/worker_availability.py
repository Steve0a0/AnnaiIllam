from datetime import date, datetime
from app.utils.time import utcnow

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkerAvailability(Base):
    __tablename__ = "worker_availability"
    __table_args__ = (
        UniqueConstraint("worker_profile_id", "availability_date", name="uq_worker_availability_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    worker_profile_id: Mapped[int] = mapped_column(ForeignKey("worker_profiles.id", ondelete="CASCADE"), index=True)

    availability_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(50), default="available", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
