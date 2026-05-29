from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ClientRating(Base):
    __tablename__ = "client_ratings"
    __table_args__ = (
        # One rating per (requirement, worker) — prevents duplicate ratings for the same worker.
        UniqueConstraint("requirement_id", "worker_profile_id", name="uq_client_rating_requirement_worker"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_client_ratings_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id", ondelete="CASCADE"), index=True)
    assignment_id: Mapped[int | None] = mapped_column(ForeignKey("assignments.id", ondelete="SET NULL"), nullable=True, index=True)
    worker_profile_id: Mapped[int | None] = mapped_column(ForeignKey("worker_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    rated_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
