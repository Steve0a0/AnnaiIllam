from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client_profile import ClientProfile


def get_client_profile_by_user_id(db: Session, user_id: int) -> ClientProfile | None:
    stmt = select(ClientProfile).where(ClientProfile.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()
