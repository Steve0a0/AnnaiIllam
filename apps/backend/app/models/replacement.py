from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Replacement(Base):
    __tablename__ = "replacements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id", ondelete="CASCADE"),
        index=True,
    )

    old_assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"),
        index=True,
    )
    new_assignment_id: Mapped[int | None] = mapped_column(
        ForeignKey("assignments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    old_worker_profile_id: Mapped[int] = mapped_column(
        ForeignKey("worker_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    new_worker_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("worker_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="created", index=True)

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
