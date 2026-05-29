"""Dependency for admin client-scoping.

Returns the list of client_profile_ids accessible to the current admin:
- super_admin → None  (no filter; sees everything)
- regular admin  → list of assigned client_profile_ids (may be empty)
"""
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.admin_client_assignment import AdminClientAssignment
from app.models.user import User


def get_accessible_client_ids(
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
) -> list[int] | None:
    """Return accessible client_profile_ids for the current admin.

    Returns None for super_admin (unrestricted), or a possibly-empty list for
    regular admins (empty means no access).
    """
    from app.repositories.profile_repository import get_admin_profile_by_user_id

    profile = get_admin_profile_by_user_id(db, current_user.id)
    if profile and profile.permission_group == "super_admin":
        return None  # unrestricted

    # Regular admin — return only assigned clients
    stmt = select(AdminClientAssignment.client_profile_id).where(
        AdminClientAssignment.admin_user_id == current_user.id
    )
    return list(db.execute(stmt).scalars().all())
