from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("requirements.id", ondelete="CASCADE"),
        index=True,
    )
    worker_profile_id: Mapped[int] = mapped_column(
        ForeignKey("worker_profiles.id", ondelete="CASCADE"),
        index=True,
    )

    assigned_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )

    status: Mapped[str] = mapped_column(String(50), default="assigned", index=True)

    assigned_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_shift: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
