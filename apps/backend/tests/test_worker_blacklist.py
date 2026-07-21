"""Tests for Feature 8: Worker Blacklist.

Covers:
1. Blacklist worker A for client X → GET matches for client X requirement
   → worker A does not appear
2. Same worker A appears normally for client Y requirement
3. Blacklist same worker twice → assert 409
4. Remove from blacklist → worker appears in matches again
5. Blacklist with no reason → assert 422
"""
from datetime import date

import pytest

from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.worker_profile import WorkerProfile
from app.models.user import User
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ──────────────────────────────────────────────────────────────────
# Auth fixture
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


# ──────────────────────────────────────────────────────────────────
# Domain fixtures
# ──────────────────────────────────────────────────────────────────


@pytest.fixture
def client_x_user(db):
    user = User(
        phone="9200000010",
        email="clientx@test.com",
        role="client",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def client_y_user(db):
    user = User(
        phone="9200000011",
        email="clienty@test.com",
        role="client",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def client_x_profile(db, client_x_user):
    profile = ClientProfile(
        user_id=client_x_user.id,
        client_type="company",
        company_name="Client X Corp",
        contact_name="X Contact",
        city="Chennai",
        state="Tamil Nadu",
        address="MRC Nagar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def client_y_profile(db, client_y_user):
    profile = ClientProfile(
        user_id=client_y_user.id,
        client_type="company",
        company_name="Client Y Corp",
        contact_name="Y Contact",
        city="Chennai",
        state="Tamil Nadu",
        address="Adyar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _make_worker(db, phone: str) -> WorkerProfile:
    user = User(
        phone=phone,
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.flush()

    worker = WorkerProfile(
        user_id=user.id,
        full_name="Test Worker",
        city="Chennai",
        state="Tamil Nadu",
        category="Housekeeping",
        date_of_birth=date(1995, 1, 1),
        is_available=True,
        verification_status="approved",
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


def _make_requirement(db, client_profile, admin_user) -> Requirement:
    req = Requirement(
        client_id=client_profile.id,
        category="Housekeeping",
        number_of_workers=2,
        work_location="Site A",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date(2026, 7, 1),
        duration_days=5,
        status="in_progress",
        created_by_user_id=admin_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


# ──────────────────────────────────────────────────────────────────
# Test 1: Blacklisted worker does NOT appear in matches for client X
# ──────────────────────────────────────────────────────────────────


def test_blacklisted_worker_excluded_from_matches(
    client, db, admin_headers, admin_user, client_x_profile
):
    worker_a = _make_worker(db, "9300000001")
    req_x = _make_requirement(db, client_x_profile, admin_user)

    # Confirm worker A appears before blacklisting
    matches_before = client.get(
        f"{BASE}/admin/assignments/requirement/{req_x.id}/matches",
        headers=admin_headers,
    )
    assert matches_before.status_code == 200
    ids_before = [m["worker_profile_id"] for m in matches_before.json()["data"]]
    assert worker_a.id in ids_before

    # Blacklist worker A for client X
    resp = client.post(
        f"{BASE}/admin/blacklist",
        json={
            "client_profile_id": client_x_profile.id,
            "worker_profile_id": worker_a.id,
            "reason": "Misconduct reported on site",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.json()

    # Worker A must NOT appear in matches after blacklisting
    matches_after = client.get(
        f"{BASE}/admin/assignments/requirement/{req_x.id}/matches",
        headers=admin_headers,
    )
    assert matches_after.status_code == 200
    ids_after = [m["worker_profile_id"] for m in matches_after.json()["data"]]
    assert worker_a.id not in ids_after


# ──────────────────────────────────────────────────────────────────
# Test 2: Same worker appears normally for client Y
# ──────────────────────────────────────────────────────────────────


def test_blacklisted_worker_appears_for_different_client(
    client, db, admin_headers, admin_user, client_x_profile, client_y_profile
):
    worker_a = _make_worker(db, "9300000002")
    req_x = _make_requirement(db, client_x_profile, admin_user)
    req_y = _make_requirement(db, client_y_profile, admin_user)

    # Blacklist worker A for client X only
    bl_resp = client.post(
        f"{BASE}/admin/blacklist",
        json={
            "client_profile_id": client_x_profile.id,
            "worker_profile_id": worker_a.id,
            "reason": "Misconduct on client X site",
        },
        headers=admin_headers,
    )
    assert bl_resp.status_code == 200

    # Worker A excluded from client X matches
    matches_x = client.get(
        f"{BASE}/admin/assignments/requirement/{req_x.id}/matches",
        headers=admin_headers,
    )
    ids_x = [m["worker_profile_id"] for m in matches_x.json()["data"]]
    assert worker_a.id not in ids_x

    # Worker A still appears for client Y
    matches_y = client.get(
        f"{BASE}/admin/assignments/requirement/{req_y.id}/matches",
        headers=admin_headers,
    )
    ids_y = [m["worker_profile_id"] for m in matches_y.json()["data"]]
    assert worker_a.id in ids_y


# ──────────────────────────────────────────────────────────────────
# Test 3: Blacklist same worker twice → 409
# ──────────────────────────────────────────────────────────────────


def test_duplicate_blacklist_returns_409(client, db, admin_headers, admin_user, client_x_profile):
    worker_a = _make_worker(db, "9300000003")

    resp1 = client.post(
        f"{BASE}/admin/blacklist",
        json={
            "client_profile_id": client_x_profile.id,
            "worker_profile_id": worker_a.id,
            "reason": "First incident",
        },
        headers=admin_headers,
    )
    assert resp1.status_code == 200

    resp2 = client.post(
        f"{BASE}/admin/blacklist",
        json={
            "client_profile_id": client_x_profile.id,
            "worker_profile_id": worker_a.id,
            "reason": "Second incident",
        },
        headers=admin_headers,
    )
    assert resp2.status_code == 409
    assert "already blacklisted" in resp2.json()["message"].lower()


# ──────────────────────────────────────────────────────────────────
# Test 4: Remove from blacklist → worker appears in matches again
# ──────────────────────────────────────────────────────────────────


def test_remove_from_blacklist_restores_worker_in_matches(
    client, db, admin_headers, admin_user, client_x_profile
):
    worker_a = _make_worker(db, "9300000004")
    req_x = _make_requirement(db, client_x_profile, admin_user)

    # Blacklist
    bl_resp = client.post(
        f"{BASE}/admin/blacklist",
        json={
            "client_profile_id": client_x_profile.id,
            "worker_profile_id": worker_a.id,
            "reason": "Temporary incident",
        },
        headers=admin_headers,
    )
    assert bl_resp.status_code == 200
    blacklist_id = bl_resp.json()["data"]["id"]

    # Confirm excluded
    matches_while_blacklisted = client.get(
        f"{BASE}/admin/assignments/requirement/{req_x.id}/matches",
        headers=admin_headers,
    )
    ids_blacklisted = [m["worker_profile_id"] for m in matches_while_blacklisted.json()["data"]]
    assert worker_a.id not in ids_blacklisted

    # Remove from blacklist
    del_resp = client.delete(
        f"{BASE}/admin/blacklist/{blacklist_id}",
        headers=admin_headers,
    )
    assert del_resp.status_code == 200

    # Worker should appear again
    matches_after_removal = client.get(
        f"{BASE}/admin/assignments/requirement/{req_x.id}/matches",
        headers=admin_headers,
    )
    ids_after = [m["worker_profile_id"] for m in matches_after_removal.json()["data"]]
    assert worker_a.id in ids_after


# ──────────────────────────────────────────────────────────────────
# Test 5: Blacklist with empty reason → 422
# ──────────────────────────────────────────────────────────────────


def test_blacklist_with_empty_reason_returns_422(client, db, admin_headers, admin_user, client_x_profile):
    worker_a = _make_worker(db, "9300000005")

    resp = client.post(
        f"{BASE}/admin/blacklist",
        json={
            "client_profile_id": client_x_profile.id,
            "worker_profile_id": worker_a.id,
            "reason": "",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 422
