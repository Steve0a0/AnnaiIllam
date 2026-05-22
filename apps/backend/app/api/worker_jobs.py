from app.utils.time import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.core.statuses import RequirementStatus
from app.db.deps import get_db
from app.models.assignment import Assignment
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_interest import WorkerInterest
from app.repositories.profile_repository import get_worker_profile_by_user_id
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/worker/jobs", tags=["Worker Jobs"])

# Statuses that mean this job is open and accepting worker interest
_OPEN_STATUSES = {
    RequirementStatus.APPROVED.value,
    RequirementStatus.ASSIGNED.value,
}

# Statuses that mean the worker already has an active assignment on this job
_ACTIVE_ASSIGNMENT_STATUSES = {"assigned", "accepted", "active"}


def _score_job_for_worker(requirement: Requirement, worker) -> tuple[int, list[str]]:
    """
    Score a job requirement against a worker's profile.
    Returns (score, match_reasons).
    Higher score = better match.
    """
    score = 0
    reasons: list[str] = []

    if worker.category and requirement.category:
        if worker.category.lower() == requirement.category.lower():
            score += 30
            reasons.append("category match")

    if worker.subcategory and requirement.subcategory:
        if worker.subcategory.lower() == requirement.subcategory.lower():
            score += 20
            reasons.append("subcategory match")

    if worker.city and requirement.city:
        if worker.city.lower() == requirement.city.lower():
            score += 25
            reasons.append("same city")
        elif worker.state and requirement.state:
            if worker.state.lower() == requirement.state.lower():
                score += 10
                reasons.append("same state")

    worker_skills = (worker.skills or "").lower()
    if requirement.category and requirement.category.lower() in worker_skills:
        score += 10
        reasons.append("skill match")
    if requirement.subcategory and requirement.subcategory.lower() in worker_skills:
        score += 5

    return score, reasons


def _tier(score: int) -> str:
    if score >= 50:
        return "best"
    if score >= 10:
        return "nearby"
    return "other"


@router.get("/open")
def list_open_jobs(
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    """
    Returns all open (approved) job requirements scored and ranked for this worker.
    Jobs the worker is already actively assigned to are excluded.
    Each result includes match_tier: 'best' | 'nearby' | 'other' for grouped display.
    """
    worker = get_worker_profile_by_user_id(db, current_user.id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    # Requirements that are open for assignment
    open_reqs = db.execute(
        select(Requirement).where(Requirement.status.in_(_OPEN_STATUSES))
    ).scalars().all()

    # Requirements where this worker already has an active assignment
    already_assigned_req_ids: set[int] = set(
        db.execute(
            select(Assignment.requirement_id).where(
                Assignment.worker_profile_id == worker.id,
                Assignment.status.in_(_ACTIVE_ASSIGNMENT_STATUSES),
            )
        ).scalars().all()
    )

    # Current interests by this worker (requirement_id → status)
    interest_rows = db.execute(
        select(WorkerInterest).where(WorkerInterest.worker_profile_id == worker.id)
    ).scalars().all()
    interest_map: dict[int, str] = {row.requirement_id: row.status for row in interest_rows}

    results = []
    for req in open_reqs:
        if req.id in already_assigned_req_ids:
            continue

        score, reasons = _score_job_for_worker(req, worker)
        my_interest = interest_map.get(req.id)

        results.append({
            "requirement_id": req.id,
            "category": req.category,
            "subcategory": req.subcategory,
            "work_location": req.work_location,
            "city": req.city,
            "state": req.state,
            "start_date": str(req.start_date),
            "duration_days": req.duration_days,
            "number_of_workers": req.number_of_workers,
            "shift_details": req.shift_details,
            "food_required": req.food_required,
            "accommodation_required": req.accommodation_required,
            "score": score,
            "match_reasons": reasons,
            "match_tier": _tier(score),
            "my_interest": my_interest,  # "interested" | "withdrawn" | None
        })

    # Sort: best-scoring first within each tier
    results.sort(key=lambda x: x["score"], reverse=True)

    return success_response("Open jobs fetched successfully", results)


@router.post("/{requirement_id}/interest")
def express_interest(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    """
    Worker signals they are available for a specific job.
    Creates or updates a WorkerInterest record to status='interested'.
    """
    worker = get_worker_profile_by_user_id(db, current_user.id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    req = db.get(Requirement, requirement_id)
    if not req or req.status not in _OPEN_STATUSES:
        raise HTTPException(status_code=404, detail="Job not found or no longer open")

    # Check not already actively assigned
    existing_assignment = db.execute(
        select(Assignment).where(
            Assignment.worker_profile_id == worker.id,
            Assignment.requirement_id == requirement_id,
            Assignment.status.in_(_ACTIVE_ASSIGNMENT_STATUSES),
        )
    ).scalar_one_or_none()
    if existing_assignment:
        raise HTTPException(status_code=400, detail="You are already assigned to this job")

    existing = db.execute(
        select(WorkerInterest).where(
            WorkerInterest.worker_profile_id == worker.id,
            WorkerInterest.requirement_id == requirement_id,
        )
    ).scalar_one_or_none()

    if existing:
        existing.status = "interested"
        existing.updated_at = utcnow()
    else:
        db.add(
            WorkerInterest(
                worker_profile_id=worker.id,
                requirement_id=requirement_id,
                status="interested",
            )
        )

    db.commit()

    audit_event(
        "worker_interest_expressed",
        {
            "worker_profile_id": worker.id,
            "requirement_id": requirement_id,
            "user_id": current_user.id,
        },
    )

    return success_response(
        "Interest expressed successfully",
        {"requirement_id": requirement_id, "status": "interested"},
    )


@router.post("/{requirement_id}/withdraw")
def withdraw_interest(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    """
    Worker withdraws their previously expressed interest in a job.
    """
    worker = get_worker_profile_by_user_id(db, current_user.id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    existing = db.execute(
        select(WorkerInterest).where(
            WorkerInterest.worker_profile_id == worker.id,
            WorkerInterest.requirement_id == requirement_id,
        )
    ).scalar_one_or_none()

    if not existing:
        raise HTTPException(status_code=404, detail="No interest record found for this job")

    existing.status = "withdrawn"
    existing.updated_at = utcnow()
    db.commit()

    audit_event(
        "worker_interest_withdrawn",
        {
            "worker_profile_id": worker.id,
            "requirement_id": requirement_id,
            "user_id": current_user.id,
        },
    )

    return success_response(
        "Interest withdrawn successfully",
        {"requirement_id": requirement_id, "status": "withdrawn"},
    )
