"""Tests for Fix 10 (P1-6): admin update_admin_worker must reject duplicate phone numbers."""
from datetime import date, timedelta

import pytest

from app.models.client_profile import ClientProfile
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ─────────────────────────────── fixtures ───────────────────────────────


@pytest.fixture
def worker_a_user(db):
    user = User(
        phone="9200000001",
        email="worker-a@annai-illam.test",
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def worker_a_profile(db, worker_a_user):
    profile = WorkerProfile(
        user_id=worker_a_user.id,
        full_name="Worker A",
        category="Security",
        city="Chennai",
        state="Tamil Nadu",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def worker_b_user(db):
    user = User(
        phone="9200000002",
        email="worker-b@annai-illam.test",
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def worker_b_profile(db, worker_b_user):
    profile = WorkerProfile(
        user_id=worker_b_user.id,
        full_name="Worker B",
        category="Security",
        city="Chennai",
        state="Tamil Nadu",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def admin_headers(db, admin_user):
    access_token, _ = build_token_pair(
        db,
        user_id=admin_user.id,
        subject=admin_user.email,
        role=admin_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


# ─────────────────────────────── tests ───────────────────────────────────


class TestWorkerPhoneUniqueness:
    """Fix 10: update_admin_worker must reject duplicate phone numbers with HTTP 409."""

    def test_updating_to_another_workers_phone_returns_409(
        self,
        client,
        db,
        admin_headers,
        worker_a_profile,
        worker_b_user,
    ):
        """Assigning worker B's phone to worker A must return 409 Conflict."""
        response = client.patch(
            f"{BASE}/admin/people/workers/{worker_a_profile.id}",
            json={"phone": worker_b_user.phone},
            headers=admin_headers,
        )

        assert response.status_code == 409
        assert "already in use" in response.json()["message"].lower()

    def test_updating_to_own_phone_returns_200(
        self,
        client,
        db,
        admin_headers,
        worker_a_profile,
        worker_a_user,
    ):
        """Re-submitting worker A's own phone must succeed (no false conflict)."""
        response = client.patch(
            f"{BASE}/admin/people/workers/{worker_a_profile.id}",
            json={"phone": worker_a_user.phone},
            headers=admin_headers,
        )

        assert response.status_code == 200

    def test_updating_to_new_unique_phone_returns_200(
        self,
        client,
        db,
        admin_headers,
        worker_a_profile,
        worker_a_user,
    ):
        """Updating to a brand-new, unused phone number must succeed."""
        response = client.patch(
            f"{BASE}/admin/people/workers/{worker_a_profile.id}",
            json={"phone": "9299999999"},
            headers=admin_headers,
        )

        assert response.status_code == 200

        db.refresh(worker_a_user)
        assert worker_a_user.phone == "9299999999"

    def test_phone_with_leading_whitespace_is_normalised_before_check(
        self,
        client,
        db,
        admin_headers,
        worker_a_profile,
        worker_b_user,
    ):
        """A phone with surrounding whitespace that matches worker B's phone must still be rejected."""
        response = client.patch(
            f"{BASE}/admin/people/workers/{worker_a_profile.id}",
            json={"phone": f"  {worker_b_user.phone}  "},
            headers=admin_headers,
        )

        assert response.status_code == 409
