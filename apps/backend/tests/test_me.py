"""Integration tests for the /me endpoint group.

Covers:
  GET   /me                  — current user info for each role
  GET   /me/admin-only       — admin role guard
  GET   /me/client-only      — client role guard
  GET   /me/worker-only      — worker role guard
  PATCH /me/password         — password change (correct/wrong current, no password account)
"""

import pytest

from app.core.security import hash_password, verify_password
from app.models.client_profile import ClientProfile
from app.models.user import User
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ──────────────────────────────────────────────────────────────────
# Shared fixtures
# ──────────────────────────────────────────────────────────────────


@pytest.fixture
def admin_headers(db, admin_user):
    access_token, _ = build_token_pair(
        db,
        user_id=admin_user.id,
        subject=admin_user.email,
        role=admin_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def client_headers(db, client_user):
    access_token, _ = build_token_pair(
        db,
        user_id=client_user.id,
        subject=client_user.phone,
        role=client_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def worker_headers(db, worker_user):
    access_token, _ = build_token_pair(
        db,
        user_id=worker_user.id,
        subject=worker_user.phone,
        role=worker_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Annam Textiles",
        contact_name="Priya Raman",
        city="Chennai",
        state="Tamil Nadu",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


# ──────────────────────────────────────────────────────────────────
# GET /me
# ──────────────────────────────────────────────────────────────────


class TestMeEndpoint:
    def test_admin_gets_own_info(self, client, admin_headers, admin_user):
        response = client.get(f"{BASE}/me", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == admin_user.id
        assert data["role"] == "admin"
        assert data["email"] == admin_user.email
        assert "is_active" in data

    def test_client_gets_own_info_and_profile_status(
        self, client, client_headers, client_user, client_profile
    ):
        response = client.get(f"{BASE}/me", headers=client_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == client_user.id
        assert data["role"] == "client"
        assert data["is_profile_complete"] is True

    def test_client_without_profile_shows_incomplete(self, client, client_headers, client_user):
        response = client.get(f"{BASE}/me", headers=client_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["is_profile_complete"] is False

    def test_worker_gets_own_info(self, client, worker_headers, worker_user):
        response = client.get(f"{BASE}/me", headers=worker_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == worker_user.id
        assert data["role"] == "worker"

    def test_unauthenticated_gets_401(self, client):
        response = client.get(f"{BASE}/me")
        assert response.status_code == 401

    def test_invalid_token_gets_401(self, client):
        response = client.get(
            f"{BASE}/me",
            headers={"Authorization": "Bearer not.a.valid.token"},
        )
        assert response.status_code == 401


# ──────────────────────────────────────────────────────────────────
# Role-gated endpoints
# ──────────────────────────────────────────────────────────────────


class TestRoleGatedEndpoints:
    def test_admin_can_access_admin_only(self, client, admin_headers):
        response = client.get(f"{BASE}/me/admin-only", headers=admin_headers)
        assert response.status_code == 200

    def test_client_cannot_access_admin_only(self, client, client_headers):
        response = client.get(f"{BASE}/me/admin-only", headers=client_headers)
        assert response.status_code == 403

    def test_worker_cannot_access_admin_only(self, client, worker_headers):
        response = client.get(f"{BASE}/me/admin-only", headers=worker_headers)
        assert response.status_code == 403

    def test_client_can_access_client_only(self, client, client_headers):
        response = client.get(f"{BASE}/me/client-only", headers=client_headers)
        assert response.status_code == 200

    def test_admin_cannot_access_client_only(self, client, admin_headers):
        response = client.get(f"{BASE}/me/client-only", headers=admin_headers)
        assert response.status_code == 403

    def test_worker_cannot_access_client_only(self, client, worker_headers):
        response = client.get(f"{BASE}/me/client-only", headers=worker_headers)
        assert response.status_code == 403

    def test_worker_can_access_worker_only(self, client, worker_headers):
        response = client.get(f"{BASE}/me/worker-only", headers=worker_headers)
        assert response.status_code == 200

    def test_admin_cannot_access_worker_only(self, client, admin_headers):
        response = client.get(f"{BASE}/me/worker-only", headers=admin_headers)
        assert response.status_code == 403

    def test_client_cannot_access_worker_only(self, client, client_headers):
        response = client.get(f"{BASE}/me/worker-only", headers=client_headers)
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# PATCH /me/password
# ──────────────────────────────────────────────────────────────────


class TestChangePassword:
    def test_admin_changes_password_successfully(self, client, db, admin_headers, admin_user):
        response = client.patch(
            f"{BASE}/me/password",
            json={
                "current_password": "AdminPass123!",
                "new_password": "NewAdminPass456!",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        db.refresh(admin_user)
        assert verify_password("NewAdminPass456!", admin_user.password_hash)

    def test_wrong_current_password_rejected(self, client, admin_headers):
        response = client.patch(
            f"{BASE}/me/password",
            json={
                "current_password": "WrongCurrentPass!",
                "new_password": "NewAdminPass456!",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "incorrect" in response.json()["message"].lower()

    def test_account_without_password_hash_rejected(self, client, db, client_headers, client_user):
        # client_user fixture has no password_hash (OTP-only account)
        response = client.patch(
            f"{BASE}/me/password",
            json={
                "current_password": "anything",
                "new_password": "NewPass456!",
            },
            headers=client_headers,
        )
        assert response.status_code == 400
        assert "not enabled" in response.json()["message"].lower()

    def test_short_new_password_rejected_by_schema(self, client, admin_headers):
        response = client.patch(
            f"{BASE}/me/password",
            json={
                "current_password": "AdminPass123!",
                "new_password": "short",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_unauthenticated_cannot_change_password(self, client):
        response = client.patch(
            f"{BASE}/me/password",
            json={
                "current_password": "AdminPass123!",
                "new_password": "NewAdminPass456!",
            },
        )
        assert response.status_code == 401

    def test_empty_current_password_rejected_by_schema(self, client, admin_headers):
        response = client.patch(
            f"{BASE}/me/password",
            json={
                "current_password": "",
                "new_password": "NewAdminPass456!",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_password_change_is_durable(self, client, db, admin_headers, admin_user):
        """Changed password must work for subsequent admin login."""
        client.patch(
            f"{BASE}/me/password",
            json={
                "current_password": "AdminPass123!",
                "new_password": "UpdatedPass789!",
            },
            headers=admin_headers,
        )
        login = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": admin_user.email, "password": "UpdatedPass789!"},
        )
        assert login.status_code == 200
        assert "access_token" in login.json()["data"]

    def test_old_password_rejected_after_change(self, client, db, admin_headers, admin_user):
        client.patch(
            f"{BASE}/me/password",
            json={
                "current_password": "AdminPass123!",
                "new_password": "UpdatedPass789!",
            },
            headers=admin_headers,
        )
        login = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": admin_user.email, "password": "AdminPass123!"},
        )
        assert login.status_code == 401
