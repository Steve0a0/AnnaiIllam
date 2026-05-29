from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.client_rating import ClientRating
from app.models.user import User
from app.repositories.client_repository import get_client_profile_by_user_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(tags=["Ratings"])


class ClientRatingCreateSchema(BaseModel):
    requirement_id: int
    assignment_id: int | None = None
    worker_profile_id: int | None = None
    rating: int = Field(ge=1, le=5)
    comments: str | None = Field(default=None, max_length=1000)


@router.post("/client/ratings")
def create_client_rating(
    payload: ClientRatingCreateSchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    """Client submits a rating for a requirement (and optionally a specific worker/assignment)."""
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    requirement = get_requirement_by_id(db, payload.requirement_id)
    if not requirement or requirement.client_id != client_profile.id:
        raise HTTPException(status_code=403, detail="You can only rate your own requirements")

    existing = db.execute(
        select(ClientRating).where(
            ClientRating.requirement_id == payload.requirement_id,
            ClientRating.rated_by_user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if existing:
        # Allow updating the rating instead of raising an error
        existing.rating = payload.rating
        existing.comments = payload.comments
        if payload.assignment_id is not None:
            existing.assignment_id = payload.assignment_id
        if payload.worker_profile_id is not None:
            existing.worker_profile_id = payload.worker_profile_id
        db.commit()
        db.refresh(existing)
        rating = existing
    else:
        rating = ClientRating(
            requirement_id=payload.requirement_id,
            assignment_id=payload.assignment_id,
            worker_profile_id=payload.worker_profile_id,
            rated_by_user_id=current_user.id,
            rating=payload.rating,
            comments=payload.comments,
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)

    audit_event(
        "client_rating_submitted",
        {
            "rating_id": rating.id,
            "requirement_id": rating.requirement_id,
            "rating": rating.rating,
            "rated_by_user_id": current_user.id,
        },
    )

    return success_response(
        "Rating submitted successfully",
        {
            "id": rating.id,
            "requirement_id": rating.requirement_id,
            "assignment_id": rating.assignment_id,
            "worker_profile_id": rating.worker_profile_id,
            "rating": rating.rating,
            "comments": rating.comments,
        },
    )


@router.get("/admin/ratings/{requirement_id}")
def get_ratings_for_requirement(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    """Admin views all ratings for a requirement."""
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    ratings = list(
        db.execute(
            select(ClientRating)
            .where(ClientRating.requirement_id == requirement_id)
            .order_by(ClientRating.created_at.desc())
        ).scalars().all()
    )

    data = [
        {
            "id": r.id,
            "assignment_id": r.assignment_id,
            "worker_profile_id": r.worker_profile_id,
            "rated_by_user_id": r.rated_by_user_id,
            "rating": r.rating,
            "comments": r.comments,
            "created_at": r.created_at.isoformat(),
        }
        for r in ratings
    ]

    average = round(sum(r.rating for r in ratings) / len(ratings), 2) if ratings else None

    return success_response(
        "Ratings fetched successfully",
        {"average_rating": average, "count": len(ratings), "ratings": data},
    )
