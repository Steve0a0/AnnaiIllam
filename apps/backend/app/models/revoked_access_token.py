from datetime import datetime
from app.utils.time import utcnow

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RevokedAccessToken(Base):
    """Blocklist for revoked access tokens identified by their JTI claim.

    Entries are safe to purge once expires_at has passed because an expired
    token is already rejected by JWT validation before the blocklist is checked.
    """

    __tablename__ = "revoked_access_tokens"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
