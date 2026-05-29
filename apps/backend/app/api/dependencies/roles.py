from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.db.deps import get_db
from app.models.user import User


def require_role(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this resource",
            )
        return current_user

    return role_checker


def require_permission_group(*allowed_groups: str):
    """Dependency that enforces AdminProfile.permission_group.

    - The caller must be an admin (checked via require_role first).
    - super_admin always passes regardless of allowed_groups.
    - Returns 403 if the admin has no profile or the group is not in allowed_groups.
    """
    from app.core.roles import UserRole
    from app.repositories.profile_repository import get_admin_profile_by_user_id

    def checker(
        current_user: User = Depends(require_role(UserRole.ADMIN.value)),
        db: Session = Depends(get_db),
    ) -> User:
        profile = get_admin_profile_by_user_id(db, current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin profile not found. Contact a super admin to set up your profile.",
            )
        if profile.permission_group == "super_admin":
            return current_user
        if profile.permission_group not in allowed_groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return checker
