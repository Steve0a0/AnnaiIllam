from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PayrollItem(Base):
    __tablename__ = "payroll_items"
    __table_args__ = (
        UniqueConstraint("payroll_run_id", "assignment_id", name="uq_payroll_item_run_assignment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    payroll_run_id: Mapped[int] = mapped_column(
        ForeignKey("payroll_runs.id", ondelete="CASCADE"),
        index=True,
    )
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"),
        index=True,
    )
    worker_profile_id: Mapped[int] = mapped_column(
        ForeignKey("worker_profiles.id", ondelete="CASCADE"),
        index=True,
    )

    gross_amount: Mapped[int] = mapped_column(Integer, default=0)
    total_deduction_amount: Mapped[int] = mapped_column(Integer, default=0)
    net_amount: Mapped[int] = mapped_column(Integer, default=0)

    attendance_days: Mapped[int] = mapped_column(Integer, default=0)
    half_days: Mapped[int] = mapped_column(Integer, default=0)
    absent_days: Mapped[int] = mapped_column(Integer, default=0)

    payment_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
