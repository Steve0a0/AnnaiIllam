from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_permission_group
from app.db.deps import get_db
from app.models.admin_client_assignment import AdminClientAssignment
from app.models.client_profile import ClientProfile
from app.models.user import User
from app.utils.audit import audit_event
from app.utils.response import success_response

router = APIRouter(prefix="/admin/scoping", tags=["Admin Scoping"])


class AssignClientSchema(BaseModel):
    admin_user_id: int
    client_profile_id: int


@router.post("/assign")
def assign_client_to_admin(
    payload: AssignClientSchema,
    current_user: User = Depends(require_permission_group("super_admin")),
    db: Session = Depends(get_db),
):
    """Super admin assigns a client to a regular admin."""
    # Verify the target admin user exists
    target_admin = db.execute(
        select(User).where(User.id == payload.admin_user_id, User.role == "admin")
    ).scalar_one_or_none()
    if not target_admin:
        raise HTTPException(status_code=404, detail="Admin user not found")

    # Verify client profile exists
    client_profile = db.get(ClientProfile, payload.client_profile_id)
    if not client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    # Check for duplicate
    existing = db.execute(
        select(AdminClientAssignment).where(
            AdminClientAssignment.admin_user_id == payload.admin_user_id,
            AdminClientAssignment.client_profile_id == payload.client_profile_id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Client already assigned to this admin")

    assignment = AdminClientAssignment(
        admin_user_id=payload.admin_user_id,
        client_profile_id=payload.client_profile_id,
        assigned_by_user_id=current_user.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    audit_event(
        "admin_client_assigned",
        {
            "assignment_id": assignment.id,
            "admin_user_id": payload.admin_user_id,
            "client_profile_id": payload.client_profile_id,
            "assigned_by_user_id": current_user.id,
        },
    )

    return success_response(
        "Client assigned to admin successfully",
        {
            "id": assignment.id,
            "admin_user_id": assignment.admin_user_id,
            "client_profile_id": assignment.client_profile_id,
        },
    )


@router.delete("/assign/{assignment_id}")
def remove_client_from_admin(
    assignment_id: int,
    current_user: User = Depends(require_permission_group("super_admin")),
    db: Session = Depends(get_db),
):
    """Super admin removes a client assignment from a regular admin."""
    assignment = db.get(AdminClientAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    audit_event(
        "admin_client_unassigned",
        {
            "assignment_id": assignment.id,
            "admin_user_id": assignment.admin_user_id,
            "client_profile_id": assignment.client_profile_id,
            "removed_by_user_id": current_user.id,
        },
    )

    db.delete(assignment)
    db.commit()

    return success_response("Client assignment removed successfully", {})


@router.get("/admin/{admin_user_id}")
def list_admin_assigned_clients(
    admin_user_id: int,
    current_user: User = Depends(require_permission_group("super_admin")),
    db: Session = Depends(get_db),
):
    """Super admin views the clients assigned to a given admin."""
    assignments = db.execute(
        select(AdminClientAssignment).where(
            AdminClientAssignment.admin_user_id == admin_user_id
        )
    ).scalars().all()

    client_ids = [a.client_profile_id for a in assignments]
    clients = {}
    if client_ids:
        for cp in db.execute(
            select(ClientProfile).where(ClientProfile.id.in_(client_ids))
        ).scalars().all():
            clients[cp.id] = cp

    data = [
        {
            "assignment_id": a.id,
            "client_profile_id": a.client_profile_id,
            "client_name": (
                clients[a.client_profile_id].company_name
                or clients[a.client_profile_id].contact_name
            )
            if a.client_profile_id in clients
            else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in assignments
    ]

    return success_response(
        f"Assigned clients for admin {admin_user_id}",
        {"admin_user_id": admin_user_id, "assigned_clients": data, "total": len(data)},
    )
