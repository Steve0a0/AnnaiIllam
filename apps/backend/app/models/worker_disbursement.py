from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.utils.time import utcnow


class WorkerDisbursement(Base):
    __tablename__ = "worker_disbursements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # One disbursement per assignment (enforced by unique constraint in migration)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="RESTRICT"),
        unique=True,
        index=True,
    )
    worker_profile_id: Mapped[int] = mapped_column(
        ForeignKey("worker_profiles.id", ondelete="RESTRICT"),
        index=True,
    )

    amount: Mapped[int] = mapped_column(Integer)  # stored in paise (1 rupee = 100 paise)
    disbursement_status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True
    )

    scheduled_date: Mapped[date] = mapped_column(Date)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    payment_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
