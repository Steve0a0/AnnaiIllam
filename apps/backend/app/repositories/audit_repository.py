from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def get_recent_audit_logs(db: Session, limit: int = 100) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())
