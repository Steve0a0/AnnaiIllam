from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkerInterest(Base):
    """
    Records a worker's self-expressed availability for a specific job requirement.
    This is NOT an assignment — it is a pre-assignment signal used to rank workers
    in the admin assignment panel.

    Status values:
        interested  — worker said "I'm available for this job"
        withdrawn   — worker changed their mind
    """

    __tablename__ = "worker_interests"
    __table_args__ = (
        UniqueConstraint(
            "worker_profile_id",
            "requirement_id",
            name="uq_worker_interest_requirement",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    worker_profile_id: Mapped[int] = mapped_column(
        ForeignKey("worker_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("requirements.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), default="interested", index=True)
    expressed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )
