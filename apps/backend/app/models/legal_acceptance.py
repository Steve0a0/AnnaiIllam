from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.utils.time import utcnow


class LegalAcceptance(Base):
    __tablename__ = "legal_acceptances"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "document_slug",
            "version",
            name="uq_legal_acceptances_user_document_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    role: Mapped[str] = mapped_column(String(20), index=True)
    document_slug: Mapped[str] = mapped_column(String(50), index=True)
    version: Mapped[str] = mapped_column(String(20), index=True)
    source: Mapped[str] = mapped_column(String(50))
    accepted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

