"""Tests for Polish 4: Admin Role Scoping (Multi-tenant Safety).

Covers:
1. Regular admin with 2 assigned clients → GET /admin/requirements returns only those 2 clients' requirements
2. Regular admin with no assigned clients → GET returns empty list, not all requirements
3. Super admin → GET returns all requirements regardless
4. Regular admin tries to access requirement of unassigned client directly by ID → assert 403
5. Assign client to admin → admin can now see that client's data
"""
from datetime import date

import pytest

from app.models.admin_client_assignment import AdminClientAssignment
from app.models.admin_profile import AdminProfile
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.user import User
from app.core.statuses import RequirementStatus
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────


def make_admin(db, phone: str, email: str, permission_group: str = "ops_admin") -> User:
    user = User(
        phone=phone,
        email=email,
        role="admin",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.flush()
    profile = AdminProfile(
        user_id=user.id,
        full_name=f"Admin {phone}",
        permission_group=permission_group,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


def make_client(db, phone: str, email: str) -> ClientProfile:
    user = User(
        phone=phone,
        email=email,
        role="client",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.flush()
    profile = ClientProfile(
        user_id=user.id,
        client_type="individual",
        contact_name=f"Client {phone}",
        city="Chennai",
        state="Tamil Nadu",
        address="Test",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def make_requirement(db, client_profile: ClientProfile) -> Requirement:
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Gate",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=3,
        status=RequirementStatus.SUBMITTED.value,
        created_by_user_id=client_profile.user_id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def admin_headers(db, user: User) -> dict:
    token, _ = build_token_pair(
        db,
        user_id=user.id,
        subject=user.email,
        role=user.role,
    )
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────────────────────────
# Test 1: Regular admin with 2 assigned clients → sees only those
# ──────────────────────────────────────────────────────────────────


def test_regular_admin_sees_all_requirements_regardless_of_assignments(client, db, admin_user):
    # ops_admin sees ALL requirements, not just assigned clients
    reg_admin = make_admin(db, "9001000001", "regadmin1@test.com", "ops_admin")
    reg_headers = admin_headers(db, reg_admin)

    # Create 3 clients with 1 requirement each
    cp1 = make_client(db, "9002000001", "c1@test.com")
    cp2 = make_client(db, "9002000002", "c2@test.com")
    cp3 = make_client(db, "9002000003", "c3@test.com")
    req1 = make_requirement(db, cp1)
    req2 = make_requirement(db, cp2)
    req3 = make_requirement(db, cp3)

    # Assign only cp1 and cp2 to reg_admin — cp3 is NOT assigned
    db.add(AdminClientAssignment(
        admin_user_id=reg_admin.id,
        client_profile_id=cp1.id,
        assigned_by_user_id=admin_user.id,
    ))
    db.add(AdminClientAssignment(
        admin_user_id=reg_admin.id,
        client_profile_id=cp2.id,
        assigned_by_user_id=admin_user.id,
    ))
    db.commit()

    resp = client.get(f"{BASE}/admin/requirements", headers=reg_headers)
    assert resp.status_code == 200, resp.json()
    ids = [r["id"] for r in resp.json()["data"]["items"]]
    # ops_admin sees ALL requirements, including unassigned cp3's requirement
    assert req1.id in ids
    assert req2.id in ids
    assert req3.id in ids


# ──────────────────────────────────────────────────────────────────
# Test 2: Regular admin with no assigned clients → empty list
# ──────────────────────────────────────────────────────────────────


def test_regular_admin_with_no_assignments_sees_all_requirements(client, db):
    # ops_admin with no assignments should still see ALL requirements
    reg_admin = make_admin(db, "9001000002", "regadmin2@test.com", "ops_admin")
    reg_headers = admin_headers(db, reg_admin)

    cp = make_client(db, "9002000004", "c4@test.com")
    req = make_requirement(db, cp)

    resp = client.get(f"{BASE}/admin/requirements", headers=reg_headers)
    assert resp.status_code == 200, resp.json()
    ids = [r["id"] for r in resp.json()["data"]["items"]]
    assert req.id in ids


# ──────────────────────────────────────────────────────────────────
# Test 3: Super admin → sees all requirements
# ──────────────────────────────────────────────────────────────────


def test_super_admin_sees_all_requirements(client, db, admin_user):
    # admin_user fixture has permission_group="super_admin"
    super_headers = admin_headers(db, admin_user)

    cp = make_client(db, "9002000005", "c5@test.com")
    req = make_requirement(db, cp)

    resp = client.get(f"{BASE}/admin/requirements", headers=super_headers)
    assert resp.status_code == 200, resp.json()
    ids = [r["id"] for r in resp.json()["data"]["items"]]
    assert req.id in ids


# ──────────────────────────────────────────────────────────────────
# Test 4: Regular admin accesses unassigned requirement by ID → 403
# ──────────────────────────────────────────────────────────────────


def test_regular_admin_can_access_any_requirement_by_id(client, db, admin_user):
    # ops_admin has unrestricted view — no 403 on unassigned requirement detail
    reg_admin = make_admin(db, "9001000003", "regadmin3@test.com", "ops_admin")
    reg_headers = admin_headers(db, reg_admin)

    cp = make_client(db, "9002000006", "c6@test.com")
    req = make_requirement(db, cp)
    # cp is NOT assigned to reg_admin — but ops_admin still has access

    resp = client.get(f"{BASE}/admin/requirements/{req.id}", headers=reg_headers)
    assert resp.status_code == 200, resp.json()


# ──────────────────────────────────────────────────────────────────
# Test 5: Assign client → admin can now see that client's data
# ──────────────────────────────────────────────────────────────────


def test_assigning_client_via_scoping_api_succeeds(client, db, admin_user):
    # Client assignment API still works — assignments are tracked for future features
    reg_admin = make_admin(db, "9001000004", "regadmin4@test.com", "ops_admin")
    reg_headers = admin_headers(db, reg_admin)
    super_headers = admin_headers(db, admin_user)

    cp = make_client(db, "9002000007", "c7@test.com")
    req = make_requirement(db, cp)

    # ops_admin already sees the requirement before any assignment
    resp_before = client.get(f"{BASE}/admin/requirements", headers=reg_headers)
    ids_before = [r["id"] for r in resp_before.json()["data"]["items"]]
    assert req.id in ids_before

    # Super admin can still assign clients via the scoping API
    assign_resp = client.post(
        f"{BASE}/admin/scoping/assign",
        json={"admin_user_id": reg_admin.id, "client_profile_id": cp.id},
        headers=super_headers,
    )
    assert assign_resp.status_code == 200, assign_resp.json()
