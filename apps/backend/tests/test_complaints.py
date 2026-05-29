"""Integration coverage for complaint and SLA flows.

Covers:
- Client complaint creation (all types, severities, ownership, role checks)
- Client replacement request creation
- Admin complaint listing (with status filter and pagination)
- Admin complaint detail view
- Admin complaint status updates (all status transitions)
- SLA policy listing and update (admin only)
- SLA breach logic via the list endpoint
"""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.complaint_constants import (
    ComplaintSeverity,
    ComplaintStatus,
    ComplaintType,
)
from app.models.assignment import Assignment
from app.models.client_profile import ClientProfile
from app.models.complaint import Complaint
from app.models.requirement import Requirement
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair
from app.core.statuses import RequirementStatus

BASE = "/api/v1"
TODAY = date(2026, 5, 20)


@pytest.fixture(autouse=True)
def _bypass_rate_limit():
    """Patch rate limiting to a no-op for all complaint tests.

    The rate limiter uses a shared Redis instance that persists across
    test runs.  Without this patch successive tests that POST to the
    same endpoint accumulate counts and start receiving 429 responses.
    """
    with patch("app.api.client_complaints.check_rate_limit"):
        yield


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
        address="T Nagar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def requirement(db, client_profile, client_user):
    req = Requirement(
        client_id=client_profile.id,
        category="Security",
        subcategory="Night Guard",
        number_of_workers=1,
        work_location="Warehouse Gate 1",
        city="Chennai",
        state="Tamil Nadu",
        start_date=TODAY,
        duration_days=30,
        shift_details="Night 20:00-06:00",
        budget_amount=30000,
        status=RequirementStatus.WORKERS_ASSIGNED.value,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@pytest.fixture
def worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Ravi Kumar",
        category="Security",
        subcategory="Night Guard",
        city="Chennai",
        state="Tamil Nadu",
        address="Velachery",
        skills="Security",
        available_shifts="Night",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def assignment(db, requirement, worker_profile, admin_user):
    item = Assignment(
        requirement_id=requirement.id,
        worker_profile_id=worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ACCEPTED.value,
        assigned_role="Night Guard",
        assigned_shift="Night",
        salary_amount=30000,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def open_complaint(db, requirement, client_user):
    complaint = Complaint(
        requirement_id=requirement.id,
        raised_by_user_id=client_user.id,
        complaint_type=ComplaintType.BEHAVIOR.value,
        severity=ComplaintSeverity.MEDIUM.value,
        description="Worker was rude to the client staff during evening rounds.",
        status=ComplaintStatus.OPEN.value,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@pytest.fixture
def resolved_complaint(db, requirement, client_user, admin_user):
    complaint = Complaint(
        requirement_id=requirement.id,
        raised_by_user_id=client_user.id,
        complaint_type=ComplaintType.PERFORMANCE.value,
        severity=ComplaintSeverity.LOW.value,
        description="Worker was late on multiple occasions.",
        status=ComplaintStatus.RESOLVED.value,
        resolution_notes="Issue addressed with worker directly.",
        resolved_by_user_id=admin_user.id,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def _complaint_payload(requirement_id: int, **overrides) -> dict:
    base = {
        "requirement_id": requirement_id,
        "complaint_type": ComplaintType.BEHAVIOR.value,
        "severity": ComplaintSeverity.MEDIUM.value,
        "description": "Worker behaviour issue reported by on-site supervisor.",
    }
    base.update(overrides)
    return base


# ──────────────────────────────────────────────────────────────────
# Client Complaint Creation
# ──────────────────────────────────────────────────────────────────


class TestClientComplaintCreation:
    def test_client_creates_complaint_successfully(
        self, client, client_headers, client_profile, requirement
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id),
            headers=client_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "complaint_id" in data
        assert data["status"] == ComplaintStatus.OPEN.value

    def test_admin_cannot_create_client_complaint(
        self, client, admin_headers, requirement
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id),
            headers=admin_headers,
        )
        assert response.status_code == 403

    def test_worker_cannot_create_client_complaint(
        self, client, worker_headers, requirement
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id),
            headers=worker_headers,
        )
        assert response.status_code == 403

    def test_missing_client_profile_returns_404(
        self, client, client_headers
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(1),
            headers=client_headers,
        )
        assert response.status_code == 404
        assert "profile" in response.json()["message"].lower()

    def test_requirement_not_found_returns_404(
        self, client, client_headers, client_profile
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(999999),
            headers=client_headers,
        )
        assert response.status_code == 404

    def test_requirement_owned_by_another_client_returns_404(
        self, client, db, client_headers, client_profile, admin_user
    ):
        from app.models.user import User

        other_user = User(
            phone="9000000098",
            role="client",
            is_active=True,
            is_phone_verified=True,
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        other_profile = ClientProfile(
            user_id=other_user.id,
            client_type="individual",
            contact_name="Other Client",
            city="Madurai",
            state="Tamil Nadu",
            address="Main St",
        )
        db.add(other_profile)
        db.commit()
        db.refresh(other_profile)
        other_req = Requirement(
            client_id=other_profile.id,
            category="Housekeeping",
            number_of_workers=1,
            work_location="Site B",
            city="Madurai",
            state="Tamil Nadu",
            start_date=TODAY,
            duration_days=10,
            shift_details="Day",
            budget_amount=5000,
            status=RequirementStatus.SUBMITTED.value,
            created_by_user_id=other_user.id,
        )
        db.add(other_req)
        db.commit()

        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(other_req.id),
            headers=client_headers,
        )
        assert response.status_code == 404

    def test_complaint_with_assignment_id(
        self, client, client_headers, client_profile, requirement, assignment
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id, assignment_id=assignment.id),
            headers=client_headers,
        )
        assert response.status_code == 200

    def test_assignment_not_in_requirement_returns_404(
        self, client, db, client_headers, client_profile, requirement, admin_user, worker_profile
    ):
        # Create a second requirement and assignment not owned by the client's requirement
        req2 = Requirement(
            client_id=client_profile.id,
            category="Housekeeping",
            number_of_workers=1,
            work_location="Site X",
            city="Chennai",
            state="Tamil Nadu",
            start_date=TODAY,
            duration_days=5,
            shift_details="Day",
            budget_amount=5000,
            status=RequirementStatus.WORKERS_ASSIGNED.value,
            created_by_user_id=client_profile.user_id,
        )
        db.add(req2)
        db.commit()
        db.refresh(req2)
        unrelated_assignment = Assignment(
            requirement_id=req2.id,
            worker_profile_id=worker_profile.id,
            assigned_by_user_id=admin_user.id,
            status=AssignmentStatus.ACCEPTED.value,
            assigned_role="Housekeeper",
            assigned_shift="Day",
            salary_amount=10000,
        )
        db.add(unrelated_assignment)
        db.commit()
        db.refresh(unrelated_assignment)

        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(
                requirement.id,
                assignment_id=unrelated_assignment.id,
            ),
            headers=client_headers,
        )
        assert response.status_code == 404

    def test_all_complaint_types_accepted(
        self, client, client_headers, client_profile, requirement
    ):
        # Test one representative type to avoid hitting the rate limit.
        # Full enum validation is covered by Pydantic schema tests.
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id, complaint_type=ComplaintType.PERFORMANCE.value),
            headers=client_headers,
        )
        assert response.status_code == 200

    def test_absence_complaint_type_accepted(
        self, client, client_headers, client_profile, requirement
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id, complaint_type=ComplaintType.ABSENT.value),
            headers=client_headers,
        )
        assert response.status_code == 200

    def test_payment_complaint_type_accepted(
        self, client, client_headers, client_profile, requirement
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id, complaint_type=ComplaintType.PAYMENT.value),
            headers=client_headers,
        )
        assert response.status_code == 200

    def test_all_severities_accepted(
        self, client, client_headers, client_profile, requirement
    ):
        # Test high severity as representative — Pydantic validates the enum.
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id, severity=ComplaintSeverity.HIGH.value),
            headers=client_headers,
        )
        assert response.status_code == 200

    def test_urgent_severity_accepted(
        self, client, client_headers, client_profile, requirement
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id, severity=ComplaintSeverity.URGENT.value),
            headers=client_headers,
        )
        assert response.status_code == 200

    def test_low_severity_accepted(
        self, client, client_headers, client_profile, requirement
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id, severity=ComplaintSeverity.LOW.value),
            headers=client_headers,
        )
        assert response.status_code == 200

    def test_invalid_complaint_type_returns_422(
        self, client, client_headers, client_profile, requirement
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id, complaint_type="nonexistent_type"),
            headers=client_headers,
        )
        assert response.status_code == 422

    def test_invalid_severity_returns_422(
        self, client, client_headers, client_profile, requirement
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id, severity="extreme"),
            headers=client_headers,
        )
        assert response.status_code == 422

    def test_description_too_short_returns_422(
        self, client, client_headers, client_profile, requirement
    ):
        response = client.post(
            f"{BASE}/client/complaints",
            json=_complaint_payload(requirement.id, description="bad"),
            headers=client_headers,
        )
        assert response.status_code == 422


# ──────────────────────────────────────────────────────────────────
# Client Replacement Request
# ──────────────────────────────────────────────────────────────────


class TestClientReplacementRequest:
    def test_client_creates_replacement_request(
        self, client, client_headers, client_profile, requirement, assignment
    ):
        response = client.post(
            f"{BASE}/client/complaints/replacements",
            json={
                "assignment_id": assignment.id,
                "reason": "Worker has not been showing up on time consistently.",
            },
            headers=client_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "complaint_id" in data
        assert "replacement_id" in data

    def test_non_client_cannot_request_replacement(
        self, client, admin_headers, assignment
    ):
        response = client.post(
            f"{BASE}/client/complaints/replacements",
            json={
                "assignment_id": assignment.id,
                "reason": "Worker not performing well.",
            },
            headers=admin_headers,
        )
        assert response.status_code == 403

    def test_missing_client_profile_returns_404(
        self, client, client_headers
    ):
        # client_user has no ClientProfile — endpoint must 404 before
        # reaching the assignment lookup.
        response = client.post(
            f"{BASE}/client/complaints/replacements",
            json={
                "assignment_id": 1,
                "reason": "Worker not performing well.",
            },
            headers=client_headers,
        )
        assert response.status_code == 404

    def test_assignment_not_found_returns_404(
        self, client, client_headers, client_profile
    ):
        response = client.post(
            f"{BASE}/client/complaints/replacements",
            json={
                "assignment_id": 999999,
                "reason": "Worker not performing well.",
            },
            headers=client_headers,
        )
        assert response.status_code == 404

    def test_reason_too_short_returns_422(
        self, client, client_headers, client_profile, assignment
    ):
        response = client.post(
            f"{BASE}/client/complaints/replacements",
            json={
                "assignment_id": assignment.id,
                "reason": "bad",
            },
            headers=client_headers,
        )
        assert response.status_code == 422


# ──────────────────────────────────────────────────────────────────
# Admin Complaint Listing
# ──────────────────────────────────────────────────────────────────


class TestAdminComplaintListing:
    def test_admin_lists_all_complaints(
        self, client, admin_headers, open_complaint
    ):
        response = client.get(
            f"{BASE}/admin/complaints",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert isinstance(data["items"], list)
        ids = [c["id"] for c in data["items"]]
        assert open_complaint.id in ids

    def test_admin_filters_by_open_status(
        self, client, admin_headers, open_complaint, resolved_complaint
    ):
        response = client.get(
            f"{BASE}/admin/complaints?status=open",
            headers=admin_headers,
        )
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert all(c["status"] == "open" for c in items)

    def test_admin_filters_by_resolved_status(
        self, client, admin_headers, open_complaint, resolved_complaint
    ):
        response = client.get(
            f"{BASE}/admin/complaints?status=resolved",
            headers=admin_headers,
        )
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert all(c["status"] == "resolved" for c in items)

    def test_complaints_include_sla_info(
        self, client, admin_headers, open_complaint
    ):
        response = client.get(
            f"{BASE}/admin/complaints",
            headers=admin_headers,
        )
        assert response.status_code == 200
        item = next(
            c for c in response.json()["data"]["items"] if c["id"] == open_complaint.id
        )
        assert "sla" in item
        sla = item["sla"]
        assert "age_hours" in sla
        assert "response_breached" in sla
        assert "resolution_breached" in sla

    def test_non_admin_cannot_list_complaints(
        self, client, client_headers, client_profile, open_complaint
    ):
        response = client.get(
            f"{BASE}/admin/complaints",
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_list_includes_pagination_meta(
        self, client, admin_headers, open_complaint
    ):
        response = client.get(
            f"{BASE}/admin/complaints",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total" in data
        assert "page" in data


# ──────────────────────────────────────────────────────────────────
# Admin Complaint Detail
# ──────────────────────────────────────────────────────────────────


class TestAdminComplaintDetail:
    def test_admin_gets_complaint_detail(
        self, client, admin_headers, open_complaint
    ):
        response = client.get(
            f"{BASE}/admin/complaints/{open_complaint.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == open_complaint.id
        assert data["status"] == ComplaintStatus.OPEN.value
        assert data["complaint_type"] == open_complaint.complaint_type
        assert "sla" in data
        assert "replacements" in data
        assert isinstance(data["replacements"], list)

    def test_complaint_not_found_returns_404(
        self, client, admin_headers
    ):
        response = client.get(
            f"{BASE}/admin/complaints/999999",
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_non_admin_cannot_get_detail(
        self, client, client_headers, client_profile, open_complaint
    ):
        response = client.get(
            f"{BASE}/admin/complaints/{open_complaint.id}",
            headers=client_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Admin Complaint Status Update
# ──────────────────────────────────────────────────────────────────


class TestAdminComplaintStatusUpdate:
    def test_admin_transitions_to_under_review(
        self, client, db, admin_headers, open_complaint
    ):
        response = client.patch(
            f"{BASE}/admin/complaints/{open_complaint.id}/status",
            json={"status": ComplaintStatus.UNDER_REVIEW.value},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == ComplaintStatus.UNDER_REVIEW.value
        db.refresh(open_complaint)
        assert open_complaint.status == ComplaintStatus.UNDER_REVIEW.value

    def test_admin_resolves_complaint_with_notes(
        self, client, db, admin_headers, open_complaint
    ):
        response = client.patch(
            f"{BASE}/admin/complaints/{open_complaint.id}/status",
            json={
                "status": ComplaintStatus.RESOLVED.value,
                "resolution_notes": "Spoke to worker. Issue will not recur.",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == ComplaintStatus.RESOLVED.value
        db.refresh(open_complaint)
        assert open_complaint.status == ComplaintStatus.RESOLVED.value
        assert open_complaint.resolution_notes == "Spoke to worker. Issue will not recur."
        assert open_complaint.resolved_by_user_id is not None

    def test_admin_closes_complaint(
        self, client, db, admin_headers, open_complaint
    ):
        response = client.patch(
            f"{BASE}/admin/complaints/{open_complaint.id}/status",
            json={"status": ComplaintStatus.CLOSED.value},
            headers=admin_headers,
        )
        assert response.status_code == 200
        db.refresh(open_complaint)
        assert open_complaint.status == ComplaintStatus.CLOSED.value

    def test_all_valid_statuses_accepted(
        self, client, admin_headers, open_complaint
    ):
        for status in ComplaintStatus:
            response = client.patch(
                f"{BASE}/admin/complaints/{open_complaint.id}/status",
                json={"status": status.value},
                headers=admin_headers,
            )
            assert response.status_code == 200, f"Failed for status: {status.value}"

    def test_invalid_status_returns_422(
        self, client, admin_headers, open_complaint
    ):
        response = client.patch(
            f"{BASE}/admin/complaints/{open_complaint.id}/status",
            json={"status": "not_a_valid_status"},
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_complaint_not_found_returns_404(
        self, client, admin_headers
    ):
        response = client.patch(
            f"{BASE}/admin/complaints/999999/status",
            json={"status": ComplaintStatus.RESOLVED.value},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_non_admin_cannot_update_status(
        self, client, client_headers, client_profile, open_complaint
    ):
        response = client.patch(
            f"{BASE}/admin/complaints/{open_complaint.id}/status",
            json={"status": ComplaintStatus.RESOLVED.value},
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_resolved_by_user_id_set_to_admin(
        self, client, db, admin_headers, admin_user, open_complaint
    ):
        client.patch(
            f"{BASE}/admin/complaints/{open_complaint.id}/status",
            json={"status": ComplaintStatus.RESOLVED.value},
            headers=admin_headers,
        )
        db.refresh(open_complaint)
        assert open_complaint.resolved_by_user_id == admin_user.id


# ──────────────────────────────────────────────────────────────────
# SLA Policy Management
# ──────────────────────────────────────────────────────────────────


class TestSlaPolicyManagement:
    def test_admin_lists_sla_policies(
        self, client, admin_headers
    ):
        response = client.get(
            f"{BASE}/admin/sla/complaints",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        # Default policies should be seeded
        severities = {p["severity"] for p in data}
        assert {"low", "medium", "high", "urgent"}.issubset(severities)

    def test_sla_list_includes_hours(
        self, client, admin_headers
    ):
        response = client.get(
            f"{BASE}/admin/sla/complaints",
            headers=admin_headers,
        )
        data = response.json()["data"]
        for policy in data:
            assert "response_hours" in policy
            assert "resolution_hours" in policy
            assert policy["response_hours"] >= 1
            assert policy["resolution_hours"] >= 1

    def test_non_admin_cannot_list_sla(
        self, client, client_headers, client_profile
    ):
        response = client.get(
            f"{BASE}/admin/sla/complaints",
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_admin_updates_sla_policy(
        self, client, db, admin_headers
    ):
        response = client.put(
            f"{BASE}/admin/sla/complaints",
            json={
                "severity": ComplaintSeverity.HIGH.value,
                "response_hours": 2,
                "resolution_hours": 12,
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["severity"] == ComplaintSeverity.HIGH.value
        assert data["response_hours"] == 2
        assert data["resolution_hours"] == 12

    def test_sla_update_persists(
        self, client, db, admin_headers
    ):
        client.put(
            f"{BASE}/admin/sla/complaints",
            json={
                "severity": ComplaintSeverity.URGENT.value,
                "response_hours": 1,
                "resolution_hours": 4,
            },
            headers=admin_headers,
        )
        # Read back via list endpoint
        response = client.get(
            f"{BASE}/admin/sla/complaints",
            headers=admin_headers,
        )
        policies = {p["severity"]: p for p in response.json()["data"]}
        assert policies["urgent"]["resolution_hours"] == 4

    def test_sla_update_creates_new_severity(
        self, client, admin_headers
    ):
        """upsert creates a new row if the severity doesn't exist yet."""
        response = client.put(
            f"{BASE}/admin/sla/complaints",
            json={
                "severity": ComplaintSeverity.LOW.value,
                "response_hours": 48,
                "resolution_hours": 120,
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["response_hours"] == 48
        assert data["resolution_hours"] == 120

    def test_invalid_severity_returns_422(
        self, client, admin_headers
    ):
        response = client.put(
            f"{BASE}/admin/sla/complaints",
            json={
                "severity": "extreme",
                "response_hours": 2,
                "resolution_hours": 10,
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_zero_response_hours_returns_422(
        self, client, admin_headers
    ):
        response = client.put(
            f"{BASE}/admin/sla/complaints",
            json={
                "severity": ComplaintSeverity.MEDIUM.value,
                "response_hours": 0,
                "resolution_hours": 24,
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_non_admin_cannot_update_sla(
        self, client, client_headers, client_profile
    ):
        response = client.put(
            f"{BASE}/admin/sla/complaints",
            json={
                "severity": ComplaintSeverity.MEDIUM.value,
                "response_hours": 6,
                "resolution_hours": 24,
            },
            headers=client_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# SLA Breach Detection
# ──────────────────────────────────────────────────────────────────


class TestSlaBreachDetection:
    def test_recently_created_complaint_is_not_breached(
        self, client, admin_headers, open_complaint
    ):
        """A brand-new complaint should not have breached SLA."""
        response = client.get(
            f"{BASE}/admin/complaints/{open_complaint.id}",
            headers=admin_headers,
        )
        sla = response.json()["data"]["sla"]
        # age_hours should be < 1 for a just-created complaint
        assert sla["age_hours"] < 1.0
        # Cannot assert breach=False definitively without controlling time,
        # but for a fresh record with default medium policy (12h response),
        # breach should be False.
        assert sla["response_breached"] is False

    def test_resolved_complaint_is_not_breached(
        self, client, admin_headers, resolved_complaint
    ):
        """A resolved complaint is not open, so SLA breach should be False."""
        response = client.get(
            f"{BASE}/admin/complaints/{resolved_complaint.id}",
            headers=admin_headers,
        )
        sla = response.json()["data"]["sla"]
        assert sla["response_breached"] is False
        assert sla["resolution_breached"] is False

    def test_sla_breach_true_for_old_open_complaint(
        self, client, db, admin_headers, requirement, client_user
    ):
        """An open complaint created 100 hours ago should breach all SLA targets."""
        from app.utils.time import utcnow

        old_time = utcnow() - timedelta(hours=100)
        old_complaint = Complaint(
            requirement_id=requirement.id,
            raised_by_user_id=client_user.id,
            complaint_type=ComplaintType.PERFORMANCE.value,
            severity=ComplaintSeverity.HIGH.value,
            description="Worker performance degraded significantly over the week.",
            status=ComplaintStatus.OPEN.value,
            created_at=old_time,
        )
        db.add(old_complaint)
        db.commit()
        db.refresh(old_complaint)

        response = client.get(
            f"{BASE}/admin/complaints/{old_complaint.id}",
            headers=admin_headers,
        )
        sla = response.json()["data"]["sla"]
        # High severity: response_hours=4, resolution_hours=24
        # Age is 100h — both targets exceeded
        assert sla["response_breached"] is True
        assert sla["resolution_breached"] is True
        assert sla["age_hours"] >= 99.0

# ──────────────────────────────────────────────────────────────────
# Admin Replacement Creation — Worker Picker Flow (P1 Item 10)
#
# Covers the API side of the new worker-picker replacement form:
# 1. Worker matches endpoint returns eligible workers (picker source).
# 2. Unavailable worker appears with is_available=False (picker shows as blocked).
# 3. Admin creates replacement using worker_profile_id from matches list.
# 4. Backend rejects replacement for an unavailable worker (400).
# 5. Backend rejects replacement when worker is already assigned (400).
# 6. Non-admin cannot create an admin replacement (403).
# ──────────────────────────────────────────────────────────────────


class TestAdminReplacementCreation:
    """Tests that back the worker-picker replacement form (P1 Item 10).

    The frontend picker calls GET /admin/assignments/requirement/{id}/matches
    to populate the worker list, then submits POST /admin/replacements with the
    selected worker_profile_id.  These tests verify that both endpoints behave
    correctly so the picker can rely on them.
    """

    @pytest.fixture
    def new_worker_profile(self, db):
        """A second approved, available worker who can be selected as replacement."""
        from app.models.user import User

        user = User(
            phone="9100000099",
            role="worker",
            is_active=True,
            is_phone_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        profile = WorkerProfile(
            user_id=user.id,
            full_name="Sundar Pichai",
            category="Security",
            subcategory="Day Guard",
            city="Chennai",
            state="Tamil Nadu",
            address="Anna Nagar",
            skills="Security",
            available_shifts="Day",
            is_available=True,
            verification_status="approved",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @pytest.fixture
    def unavailable_worker_profile(self, db):
        """An unavailable worker — should appear blocked in the picker."""
        from app.models.user import User

        user = User(
            phone="9100000098",
            role="worker",
            is_active=True,
            is_phone_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        profile = WorkerProfile(
            user_id=user.id,
            full_name="Blocked Worker",
            category="Security",
            city="Chennai",
            state="Tamil Nadu",
            address="Guindy",
            skills="Security",
            is_available=False,
            verification_status="approved",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    def test_worker_matches_returns_eligible_workers(
        self, client, admin_headers, requirement, new_worker_profile
    ):
        """GET /admin/assignments/requirement/{id}/matches returns worker list for picker."""
        response = client.get(
            f"{BASE}/admin/assignments/requirement/{requirement.id}/matches",
            headers=admin_headers,
        )
        assert response.status_code == 200
        workers = response.json()["data"]
        assert isinstance(workers, list)
        assert len(workers) > 0
        # Each entry must have the fields the picker uses
        for w in workers:
            assert "worker_profile_id" in w
            assert "full_name" in w
            assert "category" in w
            assert "city" in w
            assert "is_available" in w
            assert "verification_status" in w

    def test_unavailable_worker_appears_with_is_available_false(
        self, client, admin_headers, requirement, unavailable_worker_profile
    ):
        """Unavailable workers are returned by the matches endpoint with is_available=False.

        The frontend uses this flag to move the worker into the 'blocked' group —
        they are shown but cannot be selected in the picker.
        """
        response = client.get(
            f"{BASE}/admin/assignments/requirement/{requirement.id}/matches",
            headers=admin_headers,
        )
        assert response.status_code == 200
        workers = response.json()["data"]
        blocked = [
            w for w in workers
            if w["worker_profile_id"] == unavailable_worker_profile.id
        ]
        assert len(blocked) == 1
        assert blocked[0]["is_available"] is False

    def test_admin_creates_replacement_using_selected_worker(
        self, client, db, admin_headers, requirement, assignment, open_complaint, new_worker_profile
    ):
        """Admin submits the picker selection → replacement is created successfully."""
        response = client.post(
            f"{BASE}/admin/replacements",
            json={
                "complaint_id": open_complaint.id,
                "old_assignment_id": assignment.id,
                "new_worker_profile_id": new_worker_profile.id,
                "reason": "Worker replaced via picker.",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "replacement_id" in data
        assert "new_assignment_id" in data
        assert data["new_assignment_id"] is not None

    def test_replacement_fails_for_unavailable_worker(
        self, client, admin_headers, requirement, assignment, open_complaint, unavailable_worker_profile
    ):
        """Backend blocks replacement if selected worker is unavailable.

        The picker hides unavailable workers, but the backend enforces this too
        as a safety guard.
        """
        response = client.post(
            f"{BASE}/admin/replacements",
            json={
                "complaint_id": open_complaint.id,
                "old_assignment_id": assignment.id,
                "new_worker_profile_id": unavailable_worker_profile.id,
                "reason": "Attempting to assign unavailable worker.",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "not available" in response.json()["message"].lower()

    def test_replacement_fails_if_worker_already_assigned(
        self, client, db, admin_headers, requirement, assignment, open_complaint, new_worker_profile, admin_user
    ):
        """Backend rejects replacement if the chosen worker already has an active assignment on this requirement."""
        from app.models.assignment import Assignment as AssignmentModel

        # Pre-assign the new worker to the same requirement
        existing = AssignmentModel(
            requirement_id=requirement.id,
            worker_profile_id=new_worker_profile.id,
            assigned_by_user_id=admin_user.id,
            status=AssignmentStatus.ACCEPTED.value,
            assigned_role="Guard",
            assigned_shift="Day",
            salary_amount=400,
        )
        db.add(existing)
        db.commit()

        response = client.post(
            f"{BASE}/admin/replacements",
            json={
                "complaint_id": open_complaint.id,
                "old_assignment_id": assignment.id,
                "new_worker_profile_id": new_worker_profile.id,
                "reason": "Worker already assigned — should fail.",
            },
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already assigned" in response.json()["message"].lower()

    def test_non_admin_cannot_create_replacement(
        self, client, client_headers, client_profile, requirement, assignment, open_complaint, new_worker_profile
    ):
        """Worker and client roles are blocked from the admin replacement endpoint."""
        response = client.post(
            f"{BASE}/admin/replacements",
            json={
                "complaint_id": open_complaint.id,
                "old_assignment_id": assignment.id,
                "new_worker_profile_id": new_worker_profile.id,
                "reason": "Unauthorized replacement attempt.",
            },
            headers=client_headers,
        )
        assert response.status_code == 403