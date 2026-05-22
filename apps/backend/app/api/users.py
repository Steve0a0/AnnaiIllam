from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.user import User
from app.utils.response import success_response

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
def list_users(db: Session = Depends(get_db)):
    users = db.execute(select(User)).scalars().all()
    data = [
        {
            "id": user.id,
            "phone": user.phone,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        }
        for user in users
    ]
    return success_response("Users fetched successfully", data)
