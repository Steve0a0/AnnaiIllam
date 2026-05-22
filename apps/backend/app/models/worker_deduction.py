from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkerDeduction(Base):
    __tablename__ = "worker_deductions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    payroll_item_id: Mapped[int] = mapped_column(
        ForeignKey("payroll_items.id", ondelete="CASCADE"),
        index=True,
    )

    deduction_type: Mapped[str] = mapped_column(String(50), index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
