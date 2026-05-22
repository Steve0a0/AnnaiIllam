import pytest
from sqlalchemy import select

from app.core.security import verify_password
from app.models.user import User
from scripts.seed_admin import seed_admin


def test_seed_admin_creates_admin_user(db):
    result = seed_admin(
        db,
        email="OWNER@ANNAI-ILLAM.TEST",
        password="AdminPass123!",
        name="Owner",
    )

    user = db.get(User, result.user_id)

    assert result.action == "created"
    assert user is not None
    assert user.email == "owner@annai-illam.test"
    assert user.name == "Owner"
    assert user.role == "admin"
    assert user.is_active is True
    assert user.is_email_verified is True
    assert verify_password("AdminPass123!", user.password_hash)


def test_seed_admin_updates_existing_admin_without_duplicate(db):
    first = seed_admin(
        db,
        email="Admin@Annai-Illam.Test",
        password="FirstPass123!",
        name="First Admin",
    )
    second = seed_admin(
        db,
        email="admin@annai-illam.test",
        password="SecondPass123!",
        name="Second Admin",
    )

    users = db.execute(select(User).where(User.email == "admin@annai-illam.test")).scalars().all()
    user = users[0]

    assert first.user_id == second.user_id
    assert second.action == "updated"
    assert len(users) == 1
    assert user.name == "Second Admin"
    assert verify_password("SecondPass123!", user.password_hash)


def test_seed_admin_rejects_existing_non_admin_email(db, client_user):
    with pytest.raises(ValueError, match="already exists with role"):
        seed_admin(
            db,
            email=client_user.email,
            password="AdminPass123!",
            name="Admin",
        )
