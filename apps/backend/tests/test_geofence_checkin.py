"""Tests for P1 Item 11 — Strict Geofence Handling When Coordinates Are Missing."""
from datetime import date

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.statuses import RequirementStatus
from app.models.assignment import Assignment
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair

BASE = "/api/v1"

# Chennai city centre — used as the canonical "inside" location
SITE_LAT = 13.0827
SITE_LON = 80.2707
RADIUS = 500  # metres

# Far away — ~150 km south of Chennai
OUTSIDE_LAT = 11.9416
OUTSIDE_LON = 79.8083


# ── shared fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def geo_client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="GeoTest Corp",
        contact_name="Test Client",
        city="Chennai",
        state="Tamil Nadu",
        address="Test Address",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def geo_worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Geo Worker",
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


def _make_requirement(db, client_profile, client_user, *, require_geofence, with_coords):
    """Create a Requirement with configurable geofence settings."""
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Gate 1",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=5,
        status=RequirementStatus.WORKERS_ASSIGNED.value,
        created_by_user_id=client_user.id,
        require_geofence=require_geofence,
        site_latitude=SITE_LAT if with_coords else None,
        site_longitude=SITE_LON if with_coords else None,
        geofence_radius_meters=RADIUS if with_coords else None,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def _make_assignment(db, requirement, worker_profile, admin_user):
    item = Assignment(
        requirement_id=requirement.id,
        worker_profile_id=worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ACCEPTED.value,
        assigned_role="Security Guard",
        salary_amount=1000,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def worker_headers(db, worker_user):
    access_token, _ = build_token_pair(
        db,
        user_id=worker_user.id,
        subject=worker_user.phone,
        role=worker_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


# ── test class ──────────────────────────────────────────────────────────────


class TestGeofenceCheckin:
    def test_require_geofence_coords_set_inside_radius_allows_checkin(
        self, client, db, worker_headers, geo_client_profile, geo_worker_profile,
        client_user, admin_user,
    ):
        """require_geofence=True, coords set, worker inside radius → 200."""
        req = _make_requirement(
            db, geo_client_profile, client_user,
            require_geofence=True, with_coords=True,
        )
        asgn = _make_assignment(db, req, geo_worker_profile, admin_user)

        resp = client.post(
            f"{BASE}/worker/attendance/check-in",
            json={
                "assignment_id": asgn.id,
                "latitude": SITE_LAT + 0.001,   # ~110 m away — well inside 500 m
                "longitude": SITE_LON + 0.001,
            },
            headers=worker_headers,
        )
        assert resp.status_code == 200

    def test_require_geofence_coords_set_outside_radius_blocks_checkin(
        self, client, db, worker_headers, geo_client_profile, geo_worker_profile,
        client_user, admin_user,
    ):
        """require_geofence=True, coords set, worker outside radius → 422."""
        req = _make_requirement(
            db, geo_client_profile, client_user,
            require_geofence=True, with_coords=True,
        )
        asgn = _make_assignment(db, req, geo_worker_profile, admin_user)

        resp = client.post(
            f"{BASE}/worker/attendance/check-in",
            json={
                "assignment_id": asgn.id,
                "latitude": OUTSIDE_LAT,
                "longitude": OUTSIDE_LON,
            },
            headers=worker_headers,
        )
        assert resp.status_code == 422
        assert "job site" in resp.json()["message"].lower()

    def test_require_geofence_coords_missing_blocks_checkin(
        self, client, db, worker_headers, geo_client_profile, geo_worker_profile,
        client_user, admin_user,
    ):
        """require_geofence=True, no site coordinates → 400 configuration error."""
        req = _make_requirement(
            db, geo_client_profile, client_user,
            require_geofence=True, with_coords=False,
        )
        asgn = _make_assignment(db, req, geo_worker_profile, admin_user)

        resp = client.post(
            f"{BASE}/worker/attendance/check-in",
            json={
                "assignment_id": asgn.id,
                "latitude": SITE_LAT,
                "longitude": SITE_LON,
            },
            headers=worker_headers,
        )
        assert resp.status_code == 400
        assert "coordinates not configured" in resp.json()["message"].lower()

    def test_no_geofence_coords_missing_allows_checkin(
        self, client, db, worker_headers, geo_client_profile, geo_worker_profile,
        client_user, admin_user,
    ):
        """require_geofence=False, no site coordinates → 200 (old behaviour preserved)."""
        req = _make_requirement(
            db, geo_client_profile, client_user,
            require_geofence=False, with_coords=False,
        )
        asgn = _make_assignment(db, req, geo_worker_profile, admin_user)

        resp = client.post(
            f"{BASE}/worker/attendance/check-in",
            json={
                "assignment_id": asgn.id,
                "latitude": None,
                "longitude": None,
            },
            headers=worker_headers,
        )
        assert resp.status_code == 200

    def test_existing_requirements_have_require_geofence_false(
        self, db, geo_client_profile, client_user,
    ):
        """Verify that the default for require_geofence is False (migration compatibility)."""
        req = Requirement(
            client_id=geo_client_profile.id,
            category="Security",
            number_of_workers=1,
            work_location="Gate",
            city="Chennai",
            state="Tamil Nadu",
            start_date=date.today(),
            duration_days=3,
            status=RequirementStatus.APPROVED.value,
            created_by_user_id=client_user.id,
            # require_geofence intentionally omitted — tests the column default
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        assert req.require_geofence is False
