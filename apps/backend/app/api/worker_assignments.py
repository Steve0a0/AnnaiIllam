from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.assignment_constants import AssignmentStatus
from app.core.roles import UserRole
from app.core.statuses import RequirementStatus
from app.db.deps import get_db
from app.models.user import User
from app.repositories.assignment_repository import (
    count_open_assignments_for_requirement,
    get_assignment_by_id,
    get_assignments_by_worker_profile_id,
)
from app.repositories.profile_repository import get_worker_profile_by_user_id
from app.repositories.requirement_repository import get_requirement_by_id
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

    data = []
    for assignment in assignments:
        requirement = get_requirement_by_id(db, assignment.requirement_id)

        data.append(
            {
                "assignment_id": assignment.id,
                "status": assignment.status,
                "assigned_role": assignment.assigned_role,
                "assigned_shift": assignment.assigned_shift,
                "salary_amount": assignment.salary_amount,
                "notes": assignment.notes,
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
        requirement.status = RequirementStatus.APPROVED.value

    db.commit()

    return success_response(
        "Assignment declined successfully",
        {
            "assignment_id": assignment.id,
            "status": assignment.status,
        },
    )
