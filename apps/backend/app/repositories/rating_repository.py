from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client_rating import ClientRating


def get_client_rating_for_requirement(
    db: Session,
    requirement_id: int,
    rated_by_user_id: int,
) -> ClientRating | None:
    stmt = select(ClientRating).where(
        ClientRating.requirement_id == requirement_id,
        ClientRating.rated_by_user_id == rated_by_user_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def upsert_client_rating(
    db: Session,
    *,
    requirement_id: int,
    rated_by_user_id: int,
    rating: int,
    assignment_id: int | None = None,
    worker_profile_id: int | None = None,
    comments: str | None = None,
) -> ClientRating:
    existing = get_client_rating_for_requirement(db, requirement_id, rated_by_user_id)
    if existing:
        existing.assignment_id = assignment_id
        existing.worker_profile_id = worker_profile_id
        existing.rating = rating
        existing.comments = comments
        db.flush()
        return existing

    rating_record = ClientRating(
        requirement_id=requirement_id,
        assignment_id=assignment_id,
        worker_profile_id=worker_profile_id,
        rated_by_user_id=rated_by_user_id,
        rating=rating,
        comments=comments,
    )
    db.add(rating_record)
    db.flush()
    return rating_record
