"""Tests for AdminProfile.permission_group enforcement on protected admin routes.

Covered scenarios:
  - super_admin can access finance/payroll write routes
  - super_admin can create admin users
  - finance_admin can access finance/payroll write routes
  - ops_admin is blocked from finance/payroll write routes (403)
  - viewer is blocked from finance/payroll write routes (403)
  - admin without a profile is blocked (403)
  - non-admin cannot access admin routes (403)
  - ops_admin can still read operational data (workers list, requirements)
"""

import pytest

from app.models.admin_profile import AdminProfile
from app.models.user import User
from app.core.security import hash_password
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ──────────────────────────────────────────────────────────────────
# Helper: build an admin user with a given permission_group
# ──────────────────────────────────────────────────────────────────


def _make_admin(db, phone: str, email: str, permission_group: str | None) -> User:
    user = User(
        phone=phone,
        email=email,
        role="admin",
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.flush()
    if permission_group is not None:
        profile = AdminProfile(
            user_id=user.id,
            full_name=f"{permission_group} user",
            permission_group=permission_group,
        )
        db.add(profile)
    db.commit()
    db.refresh(user)
    return user


def _headers(db, user: User) -> dict:
    access_token, _ = build_token_pair(
        db,
        user_id=user.id,
        subject=user.email or user.phone,
        role=user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


# ──────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────


@pytest.fixture
def super_admin(db):
    return _make_admin(db, "9100000001", "superadmin@test.com", "super_admin")


@pytest.fixture
def finance_admin(db):
    return _make_admin(db, "9100000002", "financeadmin@test.com", "finance_admin")


@pytest.fixture
def ops_admin(db):
    return _make_admin(db, "9100000003", "opsadmin@test.com", "ops_admin")


@pytest.fixture
def viewer_admin(db):
    return _make_admin(db, "9100000004", "viewer@test.com", "viewer")


@pytest.fixture
def profileless_admin(db):
    """Admin user with no AdminProfile."""
    return _make_admin(db, "9100000005", "noprofile@test.com", None)


@pytest.fixture
def super_headers(db, super_admin):
    return _headers(db, super_admin)


@pytest.fixture
def finance_headers(db, finance_admin):
    return _headers(db, finance_admin)


@pytest.fixture
def ops_headers(db, ops_admin):
    return _headers(db, ops_admin)


@pytest.fixture
def viewer_headers(db, viewer_admin):
    return _headers(db, viewer_admin)


@pytest.fixture
def profileless_headers(db, profileless_admin):
    return _headers(db, profileless_admin)


@pytest.fixture
def client_headers(db):
    """A non-admin (client-role) user — should be blocked from all admin routes."""
    user = User(
        phone="9100000007",
        email="clientrole@test.com",
        role="client",
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _headers(db, user)


# Minimal valid payroll run payload
PAYROLL_RUN_PAYLOAD = {
    "period_start": "2026-05-01",
    "period_end": "2026-05-31",
    "notes": "May 2026",
}


# ──────────────────────────────────────────────────────────────────
# Tests: POST /admin/payroll/runs
# ──────────────────────────────────────────────────────────────────


class TestPayrollRunCreation:
    def test_super_admin_can_create_payroll_run(self, client, super_headers):
        resp = client.post(
            f"{BASE}/admin/payroll/runs",
            json=PAYROLL_RUN_PAYLOAD,
            headers=super_headers,
        )
        assert resp.status_code == 200

    def test_finance_admin_can_create_payroll_run(self, client, finance_headers):
        resp = client.post(
            f"{BASE}/admin/payroll/runs",
            json=PAYROLL_RUN_PAYLOAD,
            headers=finance_headers,
        )
        assert resp.status_code == 200

    def test_ops_admin_cannot_create_payroll_run(self, client, ops_headers):
        resp = client.post(
            f"{BASE}/admin/payroll/runs",
            json=PAYROLL_RUN_PAYLOAD,
            headers=ops_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_payroll_run(self, client, viewer_headers):
        resp = client.post(
            f"{BASE}/admin/payroll/runs",
            json=PAYROLL_RUN_PAYLOAD,
            headers=viewer_headers,
        )
        assert resp.status_code == 403

    def test_admin_without_profile_blocked(self, client, profileless_headers):
        resp = client.post(
            f"{BASE}/admin/payroll/runs",
            json=PAYROLL_RUN_PAYLOAD,
            headers=profileless_headers,
        )
        assert resp.status_code == 403

    def test_non_admin_cannot_create_payroll_run(self, client, client_headers):
        resp = client.post(
            f"{BASE}/admin/payroll/runs",
            json=PAYROLL_RUN_PAYLOAD,
            headers=client_headers,
        )
        assert resp.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Tests: GET /admin/payroll/runs (read-only — all admins allowed)
# ──────────────────────────────────────────────────────────────────


class TestPayrollRunRead:
    def test_ops_admin_can_list_payroll_runs(self, client, ops_headers):
        resp = client.get(f"{BASE}/admin/payroll/runs", headers=ops_headers)
        assert resp.status_code == 200

    def test_viewer_can_list_payroll_runs(self, client, viewer_headers):
        resp = client.get(f"{BASE}/admin/payroll/runs", headers=viewer_headers)
        assert resp.status_code == 200

    def test_finance_admin_can_list_payroll_runs(self, client, finance_headers):
        resp = client.get(f"{BASE}/admin/payroll/runs", headers=finance_headers)
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────
# Tests: POST /admin/finance/client-payments/manual
# ──────────────────────────────────────────────────────────────────


class TestManualClientPayment:
    def test_super_admin_can_record_manual_payment(self, client, super_headers):
        # Will get 404/422 for unknown requirement — that's fine, auth passed.
        resp = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json={
                "requirement_id": 99999,
                "amount": 5000,
                "payment_model": "monthly",
                "payment_mode": "bank_transfer",
                "payment_status": "paid",
            },
            headers=super_headers,
        )
        assert resp.status_code in (200, 400, 404, 422)  # not 403

    def test_finance_admin_can_record_manual_payment(self, client, finance_headers):
        resp = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json={
                "requirement_id": 99999,
                "amount": 5000,
                "payment_model": "monthly",
                "payment_mode": "bank_transfer",
                "payment_status": "paid",
            },
            headers=finance_headers,
        )
        assert resp.status_code in (200, 400, 404, 422)  # not 403

    def test_ops_admin_cannot_record_manual_payment(self, client, ops_headers):
        resp = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json={
                "requirement_id": 99999,
                "amount": 5000,
                "payment_model": "monthly",
                "payment_mode": "bank_transfer",
                "payment_status": "paid",
            },
            headers=ops_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_record_manual_payment(self, client, viewer_headers):
        resp = client.post(
            f"{BASE}/admin/finance/client-payments/manual",
            json={
                "requirement_id": 99999,
                "amount": 5000,
                "payment_model": "monthly",
                "payment_mode": "bank_transfer",
                "payment_status": "paid",
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Tests: POST /admin/people/admin-users (super_admin only)
# ──────────────────────────────────────────────────────────────────


class TestAdminUserCreation:
    def test_super_admin_can_create_admin_user(self, client, super_headers):
        resp = client.post(
            f"{BASE}/admin/people/admin-users",
            json={
                "email": "newadmin2@test.com",
                "name": "New Admin",
                "password": "SecureAdminPass123!",
                "permission_group": "ops_admin",
            },
            headers=super_headers,
        )
        assert resp.status_code == 201

    def test_finance_admin_cannot_create_admin_user(self, client, finance_headers):
        resp = client.post(
            f"{BASE}/admin/people/admin-users",
            json={
                "email": "shouldfail@test.com",
                "name": "Should Fail",
                "password": "SecureAdminPass123!",
            },
            headers=finance_headers,
        )
        assert resp.status_code == 403

    def test_ops_admin_cannot_create_admin_user(self, client, ops_headers):
        resp = client.post(
            f"{BASE}/admin/people/admin-users",
            json={
                "email": "shouldfail2@test.com",
                "name": "Should Fail",
                "password": "SecureAdminPass123!",
            },
            headers=ops_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_admin_user(self, client, viewer_headers):
        resp = client.post(
            f"{BASE}/admin/people/admin-users",
            json={
                "email": "shouldfail3@test.com",
                "name": "Should Fail",
                "password": "SecureAdminPass123!",
            },
            headers=viewer_headers,
        )
        assert resp.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Tests: ops_admin can still read operational data
# ──────────────────────────────────────────────────────────────────


class TestOpsAdminReadAccess:
    def test_ops_admin_can_list_workers(self, client, ops_headers):
        resp = client.get(f"{BASE}/admin/people/workers", headers=ops_headers)
        assert resp.status_code == 200

    def test_ops_admin_can_list_clients(self, client, ops_headers):
        resp = client.get(f"{BASE}/admin/people/clients", headers=ops_headers)
        assert resp.status_code == 200

    def test_viewer_can_list_workers(self, client, viewer_headers):
        resp = client.get(f"{BASE}/admin/people/workers", headers=viewer_headers)
        assert resp.status_code == 200
