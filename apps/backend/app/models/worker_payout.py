from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkerPayout(Base):
    __tablename__ = "worker_payouts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    payroll_item_id: Mapped[int] = mapped_column(
        ForeignKey("payroll_items.id", ondelete="CASCADE"),
        index=True,
    )
    worker_profile_id: Mapped[int] = mapped_column(
        ForeignKey("worker_profiles.id", ondelete="CASCADE"),
        index=True,
    )

    amount: Mapped[int] = mapped_column(Integer)
    payout_mode: Mapped[str] = mapped_column(String(50), index=True)
    payout_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)

    transaction_reference: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    paid_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
