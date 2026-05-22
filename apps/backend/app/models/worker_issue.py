from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkerIssue(Base):
    __tablename__ = "worker_issues"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    worker_profile_id: Mapped[int] = mapped_column(
        ForeignKey("worker_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    assignment_id: Mapped[int | None] = mapped_column(
        ForeignKey("assignments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    issue_type: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="open", index=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
