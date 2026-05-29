from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ClientWorkerBlacklist(Base):
    __tablename__ = "client_worker_blacklist"
    __table_args__ = (
        UniqueConstraint(
            "client_profile_id",
            "worker_profile_id",
            name="uq_blacklist_client_worker",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_profile_id: Mapped[int] = mapped_column(
        ForeignKey("client_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    worker_profile_id: Mapped[int] = mapped_column(
        ForeignKey("worker_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    reason: Mapped[str] = mapped_column(Text)
    blacklisted_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
