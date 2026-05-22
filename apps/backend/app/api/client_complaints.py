from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.complaint_constants import ComplaintSeverity, ComplaintType, ReplacementStatus
from app.core.rate_limit import check_rate_limit
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.assignment_repository import get_assignment_by_id
from app.repositories.client_repository import get_client_profile_by_user_id
from app.models.replacement import Replacement
from app.repositories.complaint_repository import create_complaint, create_replacement, get_complaints_by_requirement_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.schemas.complaint import ClientReplacementRequestSchema, ComplaintCreateSchema
from app.services.complaint_service import build_complaint_entity
from app.services.notification_service import queue_notification
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/client/complaints", tags=["Client Complaints"])


@router.post("")
def create_client_complaint(
    payload: ComplaintCreateSchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    check_rate_limit(f"complaint_create:{current_user.id}", limit=10, window_seconds=300)

    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    requirement = get_requirement_by_id(db, payload.requirement_id)
    if not requirement or requirement.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if payload.assignment_id is not None:
        assignment = get_assignment_by_id(db, payload.assignment_id)
        if not assignment or assignment.requirement_id != requirement.id:
            raise HTTPException(status_code=404, detail="Assignment not found")

    allowed_types = {item.value for item in ComplaintType}
    if payload.complaint_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid complaint type")

    allowed_severity = {item.value for item in ComplaintSeverity}
    if payload.severity not in allowed_severity:
        raise HTTPException(status_code=400, detail="Invalid complaint severity")

    complaint = build_complaint_entity(payload, current_user.id)
    create_complaint(db, complaint)
    db.commit()
    db.refresh(complaint)

    audit_event(
        "complaint_created",
        {
            "complaint_id": complaint.id,
            "requirement_id": complaint.requirement_id,
            "client_user_id": current_user.id,
        },
    )
    queue_notification(
        channel="sms",
        recipient=current_user.phone,
        template="complaint_created",
        context={"complaint_id": complaint.id, "requirement_id": complaint.requirement_id},
    )

    return success_response(
        "Complaint created successfully",
        {
            "complaint_id": complaint.id,
            "status": complaint.status,
        },
    )


@router.post("/replacements")
def create_client_replacement_request(
    payload: ClientReplacementRequestSchema,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    check_rate_limit(f"replacement_request:{current_user.id}", limit=5, window_seconds=300)

    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    assignment = get_assignment_by_id(db, payload.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    requirement = get_requirement_by_id(db, assignment.requirement_id)
    if not requirement or requirement.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    complaint = build_complaint_entity(
        ComplaintCreateSchema(
            requirement_id=requirement.id,
            assignment_id=assignment.id,
            complaint_type=ComplaintType.REPLACEMENT_REQUEST.value,
            severity=ComplaintSeverity.HIGH.value,
            description=payload.reason,
        ),
        current_user.id,
    )
    create_complaint(db, complaint)
    db.flush()

    replacement = Replacement(
        complaint_id=complaint.id,
        old_assignment_id=assignment.id,
        old_worker_profile_id=assignment.worker_profile_id,
        reason=payload.reason,
        status=ReplacementStatus.CREATED.value,
        created_by_user_id=current_user.id,
    )
    create_replacement(db, replacement)
    db.commit()
    db.refresh(replacement)

    audit_event(
        "client_replacement_requested",
        {
            "replacement_id": replacement.id,
            "complaint_id": complaint.id,
            "requirement_id": requirement.id,
            "assignment_id": assignment.id,
            "client_user_id": current_user.id,
        },
    )
    queue_notification(
        channel="sms",
        recipient=current_user.phone,
        template="replacement_requested",
        context={
            "replacement_id": replacement.id,
            "complaint_id": complaint.id,
            "requirement_id": requirement.id,
        },
    )

    return success_response(
        "Replacement request created successfully",
        {
            "replacement_id": replacement.id,
            "complaint_id": complaint.id,
            "status": replacement.status,
        },
    )


@router.get("")
def list_all_client_complaints(
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    from app.repositories.requirement_repository import get_requirements_by_client_id
    requirements = get_requirements_by_client_id(db, client_profile.id)
    all_complaints = []
    for req in requirements:
        complaints = get_complaints_by_requirement_id(db, req.id)
        for item in complaints:
            all_complaints.append({
                "id": item.id,
                "requirement_id": req.id,
                "requirement_category": req.category,
                "assignment_id": item.assignment_id,
                "complaint_type": item.complaint_type,
                "severity": item.severity,
                "description": item.description,
                "status": item.status,
                "resolution_notes": item.resolution_notes,
                "created_at": item.created_at.isoformat(),
            })

    all_complaints.sort(key=lambda x: x["created_at"], reverse=True)
    return success_response("Complaints fetched successfully", all_complaints)


@router.get("/requirement/{requirement_id}")
def list_client_complaints(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.CLIENT.value)),
    db: Session = Depends(get_db),
):
    client_profile = get_client_profile_by_user_id(db, current_user.id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement or requirement.client_id != client_profile.id:
        raise HTTPException(status_code=404, detail="Requirement not found")

    complaints = get_complaints_by_requirement_id(db, requirement_id)

    data = [
        {
            "id": item.id,
            "assignment_id": item.assignment_id,
            "complaint_type": item.complaint_type,
            "severity": item.severity,
            "description": item.description,
            "status": item.status,
            "resolution_notes": item.resolution_notes,
            "created_at": item.created_at.isoformat(),
        }
        for item in complaints
    ]

    return success_response("Complaints fetched successfully", data)
