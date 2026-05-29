from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.utils.time import utcnow


class AdminClientAssignment(Base):
    __tablename__ = "admin_client_assignments"
    __table_args__ = (
        UniqueConstraint("admin_user_id", "client_profile_id", name="uq_admin_client_assignment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    admin_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    client_profile_id: Mapped[int] = mapped_column(
        ForeignKey("client_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    assigned_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
