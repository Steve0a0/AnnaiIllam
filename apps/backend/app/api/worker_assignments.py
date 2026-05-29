from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.assignment_constants import AssignmentStatus
from app.core.roles import UserRole
from app.core.statuses import RequirementStatus, validate_requirement_transition
from app.db.deps import get_db
from app.models.requirement import Requirement
from app.models.user import User
from app.repositories.assignment_repository import (
    count_open_assignments_for_requirement,
    get_assignment_by_id,
    get_assignments_by_worker_profile_id,
)
from app.repositories.profile_repository import get_worker_profile_by_user_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.services.notification_service import enqueue_push_to_user
from app.utils.response import success_response

router = APIRouter(prefix="/worker/assignments", tags=["Worker Assignments"])


@router.get("")
def list_my_assignments(
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    assignments = get_assignments_by_worker_profile_id(db, worker_profile.id)

    # Fix 17: batch-fetch all requirements in one query to avoid N+1
    _req_ids = [a.requirement_id for a in assignments]
    _requirements_map: dict = {}
    if _req_ids:
        for r in db.execute(
            select(Requirement).where(Requirement.id.in_(_req_ids))
        ).scalars().all():
            _requirements_map[r.id] = r

    data = []
    for assignment in assignments:
        requirement = _requirements_map.get(assignment.requirement_id)

        data.append(
            {
                "assignment_id": assignment.id,
                "status": assignment.status,
                "assigned_role": assignment.assigned_role,
                "assigned_shift": assignment.assigned_shift,
                "salary_amount": assignment.salary_amount,
                "notes": assignment.notes,
                "start_date": str(assignment.start_date) if assignment.start_date else None,
                "end_date": str(assignment.end_date) if assignment.end_date else None,
                "requirement": None
                if not requirement
                else {
                    "id": requirement.id,
                    "category": requirement.category,
                    "subcategory": requirement.subcategory,
                    "work_location": requirement.work_location,
                    "city": requirement.city,
                    "state": requirement.state,
                    "start_date": str(requirement.start_date),
                    "duration_days": requirement.duration_days,
                    "food_required": requirement.food_required,
                    "accommodation_required": requirement.accommodation_required,
                },
            }
        )

    return success_response("Worker assignments fetched successfully", data)


@router.post("/{assignment_id}/acknowledge")
def acknowledge_assignment(
    assignment_id: int,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    assignment = get_assignment_by_id(db, assignment_id)
    if not assignment or assignment.worker_profile_id != worker_profile.id:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.status != AssignmentStatus.ASSIGNED.value:
        raise HTTPException(status_code=400, detail="Only assigned jobs can be acknowledged")

    assignment.status = AssignmentStatus.ACCEPTED.value
    db.commit()

    return success_response(
        "Assignment acknowledged successfully",
        {
            "assignment_id": assignment.id,
            "status": assignment.status,
        },
    )


@router.post("/{assignment_id}/decline")
def decline_assignment(
    assignment_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    assignment = get_assignment_by_id(db, assignment_id)
    if not assignment or assignment.worker_profile_id != worker_profile.id:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.status != AssignmentStatus.ASSIGNED.value:
        raise HTTPException(status_code=400, detail="Only assigned jobs can be declined")

    assignment.status = AssignmentStatus.DECLINED.value
    db.flush()

    requirement = get_requirement_by_id(db, assignment.requirement_id)
    if requirement and count_open_assignments_for_requirement(db, requirement.id) == 0:
        try:
            validate_requirement_transition(
                requirement.status, RequirementStatus.APPROVED.value
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        requirement.status = RequirementStatus.APPROVED.value

    db.commit()

    # Notify all admins that the worker declined
    _admin_users = db.execute(
        select(User).where(User.role == UserRole.ADMIN.value, User.is_active.is_(True))
    ).scalars().all()
    for _admin in _admin_users:
        enqueue_push_to_user(
            background_tasks,
            db,
            user_id=_admin.id,
            title="Worker declined assignment",
            body=f"Worker {worker_profile.full_name} declined assignment for requirement #{assignment.requirement_id}.",
            data={"type": "assignment_declined", "requirement_id": str(assignment.requirement_id)},
        )

    return success_response(
        "Assignment declined successfully",
        {
            "assignment_id": assignment.id,
            "status": assignment.status,
        },
    )
