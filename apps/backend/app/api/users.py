from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_permission_group
from app.db.deps import get_db
from app.models.user import User
from app.schemas.user import UserDirectoryItem, UserDirectoryPage, UserDirectoryResponse
from app.utils.pagination import PaginationParams, paginate, pagination_meta

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserDirectoryResponse)
def list_users(
    pg: PaginationParams = Depends(),
    _current_user: User = Depends(require_permission_group("super_admin")),
    db: Session = Depends(get_db),
) -> UserDirectoryResponse:
    users, total = paginate(select(User).order_by(User.id), db, pg)
    page = UserDirectoryPage(
        items=[UserDirectoryItem.model_validate(user) for user in users],
        **pagination_meta(pg, total),
    )
    return UserDirectoryResponse(
        message="Users fetched successfully",
        data=page,
    )
