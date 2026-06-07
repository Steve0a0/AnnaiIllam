from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.admin_profile import AdminProfile
from app.models.user import User


@dataclass(frozen=True)
class SeedAdminResult:
    action: str
    user_id: int
    email: str


def _normalise_email(email: str) -> str:
    normalised = email.strip().lower()
    if "@" not in normalised or normalised.startswith("@") or normalised.endswith("@"):
        raise ValueError("EMAIL must be a valid email address")
    return normalised


def _validate_password(password: str) -> str:
    if not 8 <= len(password) <= 128:
        raise ValueError("PASSWORD must be between 8 and 128 characters")
    return password


def _upsert_super_admin_profile(db: Session, user: User) -> None:
    """Ensure the seeded admin has a super_admin AdminProfile."""
    from sqlalchemy import select as _select
    profile = db.execute(
        _select(AdminProfile).where(AdminProfile.user_id == user.id)
    ).scalar_one_or_none()
    if profile:
        profile.full_name = user.name or "Admin"
        profile.permission_group = "super_admin"
    else:
        db.add(AdminProfile(
            user_id=user.id,
            full_name=user.name or "Admin",
            permission_group="super_admin",
        ))
    db.commit()


def seed_admin(db: Session, *, email: str, password: str, name: str = "Admin") -> SeedAdminResult:
    email = _normalise_email(email)
    password = _validate_password(password)
    name = name.strip() or "Admin"

    user = db.execute(select(User).where(func.lower(User.email) == email)).scalar_one_or_none()
    password_hash = hash_password(password)

    if user:
        if user.role != UserRole.ADMIN.value:
            raise ValueError(f"User with email {email} already exists with role {user.role!r}")

        user.name = name
        user.password_hash = password_hash
        user.is_active = True
        user.is_email_verified = True
        db.commit()
        db.refresh(user)
        _upsert_super_admin_profile(db, user)
        return SeedAdminResult(action="updated", user_id=user.id, email=user.email or email)

    user = User(
        email=email,
        name=name,
        role=UserRole.ADMIN.value,
        password_hash=password_hash,
        is_active=True,
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _upsert_super_admin_profile(db, user)
    return SeedAdminResult(action="created", user_id=user.id, email=user.email or email)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create or update an admin user.")
    parser.add_argument("--email", required=True, help="Admin login email address")
    parser.add_argument("--password", required=True, help="Admin login password")
    parser.add_argument("--name", default="Admin", help="Admin display name")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        result = seed_admin(db, email=args.email, password=args.password, name=args.name)
    except ValueError as exc:
        db.rollback()
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(f"Admin user {result.action}: id={result.user_id} email={result.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
