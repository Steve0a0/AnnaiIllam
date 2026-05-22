from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.models.worker_issue import WorkerIssue
from app.repositories.assignment_repository import get_assignment_by_id
from app.repositories.profile_repository import get_worker_profile_by_user_id
from app.repositories.worker_issue_repository import create_worker_issue, get_worker_issues_by_worker_profile_id
from app.schemas.worker_issue import WorkerIssueCreateSchema
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/worker/issues", tags=["Worker Issues"])


@router.post("")
def create_my_worker_issue(
    payload: WorkerIssueCreateSchema,
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    if payload.assignment_id is not None:
        assignment = get_assignment_by_id(db, payload.assignment_id)
        if not assignment or assignment.worker_profile_id != worker_profile.id:
            raise HTTPException(status_code=404, detail="Assignment not found")

    issue = WorkerIssue(
        worker_profile_id=worker_profile.id,
        assignment_id=payload.assignment_id,
        issue_type=payload.issue_type.lower(),
        description=payload.description,
        status="open",
    )
    create_worker_issue(db, issue)
    db.commit()
    db.refresh(issue)

    audit_event(
        "worker_issue_created",
        {
            "worker_issue_id": issue.id,
            "worker_profile_id": worker_profile.id,
            "assignment_id": issue.assignment_id,
            "user_id": current_user.id,
        },
    )

    return success_response("Worker issue created successfully", {"id": issue.id, "status": issue.status})


@router.get("")
def list_my_worker_issues(
    current_user: User = Depends(require_role(UserRole.WORKER.value)),
    db: Session = Depends(get_db),
):
    worker_profile = get_worker_profile_by_user_id(db, current_user.id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    issues = get_worker_issues_by_worker_profile_id(db, worker_profile.id)
    data = [
        {
            "id": item.id,
            "assignment_id": item.assignment_id,
            "issue_type": item.issue_type,
            "description": item.description,
            "status": item.status,
            "resolution_notes": item.resolution_notes,
            "created_at": item.created_at.isoformat(),
        }
        for item in issues
    ]
    return success_response("Worker issues fetched successfully", data)
