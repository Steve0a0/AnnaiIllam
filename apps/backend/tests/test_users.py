"""Security regression tests for the privileged user directory and router authentication."""

from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordBearer
import pytest

from app.core.security import hash_password
from app.main import app
from app.models.admin_profile import AdminProfile
from app.models.user import User
from app.services.token_service import build_token_pair

BASE = "/api/v1"


def _headers(db, user: User) -> dict[str, str]:
    access_token, _ = build_token_pair(
        db,
        user_id=user.id,
        subject=user.email or user.phone,
        role=user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


def _make_admin(db, permission_group: str) -> User:
    user = User(
        phone="+919100000099",
        email=f"{permission_group}@users.test",
        role="admin",
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.flush()
    db.add(
        AdminProfile(
            user_id=user.id,
            full_name=f"{permission_group} user",
            permission_group=permission_group,
        )
    )
    db.commit()
    db.refresh(user)
    return user


def test_user_directory_requires_authentication(client):
    response = client.get(f"{BASE}/users")
    assert response.status_code == 401


def test_user_directory_rejects_invalid_token(client):
    response = client.get(
        f"{BASE}/users",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_client_cannot_access_user_directory(client, db, client_user):
    response = client.get(f"{BASE}/users", headers=_headers(db, client_user))
    assert response.status_code == 403


def test_worker_cannot_access_user_directory(client, db, worker_user):
    response = client.get(f"{BASE}/users", headers=_headers(db, worker_user))
    assert response.status_code == 403


@pytest.mark.parametrize("permission_group", ["ops_admin", "finance_admin", "viewer"])
def test_non_super_admin_cannot_access_user_directory(client, db, permission_group):
    regular_admin = _make_admin(db, permission_group)
    response = client.get(f"{BASE}/users", headers=_headers(db, regular_admin))
    assert response.status_code == 403


def test_super_admin_gets_paginated_minimal_directory(
    client,
    db,
    admin_user,
    client_user,
    worker_user,
):
    response = client.get(
        f"{BASE}/users",
        params={"page": 1, "page_size": 2},
        headers=_headers(db, admin_user),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Users fetched successfully"

    data = payload["data"]
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] == 3
    assert data["total_pages"] == 2
    assert len(data["items"]) == 2

    allowed_fields = {"id", "role", "is_active", "created_at"}
    for item in data["items"]:
        assert set(item) == allowed_fields
        assert "phone" not in item
        assert "email" not in item
        assert "name" not in item


def _dependency_calls(dependant):
    if dependant.call is not None:
        yield dependant.call
    for dependency in dependant.dependencies:
        yield from _dependency_calls(dependency)


def _has_authentication_guard(dependant) -> bool:
    for call in _dependency_calls(dependant):
        if call is None:
            continue
        if getattr(call, "__name__", None) == "get_current_user":
            return True
        if getattr(call, "__name__", None) == "get_admin_session_refresh_token":
            return True
        if isinstance(call, OAuth2PasswordBearer):
            return True
    return False


def _api_route_contexts():
    """Yield effective API routes across eager and lazy FastAPI router layouts."""
    for route in app.routes:
        if isinstance(route, APIRoute):
            yield route.path, route.methods or set(), route.dependant
            continue

        effective_route_contexts = getattr(route, "effective_route_contexts", None)
        if effective_route_contexts is None:
            continue
        for context in effective_route_contexts():
            dependant = getattr(context, "dependant", None)
            if dependant is not None:
                yield context.path, context.methods or set(), dependant


def test_every_non_public_api_route_has_authentication_guard():
    intentionally_public = {
        ("GET", f"{BASE}/health"),
        ("GET", f"{BASE}/ready"),
        ("POST", f"{BASE}/auth/client/request-otp"),
        ("POST", f"{BASE}/auth/client/verify-otp"),
        ("POST", f"{BASE}/auth/worker/request-otp"),
        ("POST", f"{BASE}/auth/worker/verify-otp"),
        ("POST", f"{BASE}/auth/request-otp"),
        ("POST", f"{BASE}/auth/verify-otp"),
        ("POST", f"{BASE}/auth/admin/login"),
        ("POST", f"{BASE}/auth/refresh"),
        ("POST", f"{BASE}/auth/client/social"),
        ("POST", f"{BASE}/payments/webhook"),
        ("POST", f"{BASE}/payments/webhook/razorpay"),
    }

    unprotected_routes: set[tuple[str, str]] = set()
    for path, methods, dependant in _api_route_contexts():
        if not path.startswith(BASE):
            continue
        if _has_authentication_guard(dependant):
            continue
        for method in methods:
            unprotected_routes.add((method, path))

    assert unprotected_routes == intentionally_public
