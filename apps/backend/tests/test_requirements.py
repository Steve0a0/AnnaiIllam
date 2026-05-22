"""Integration coverage for client requirements and admin quote flow."""
from datetime import date, timedelta

import pytest

from app.core.statuses import QuoteStatus, RequirementStatus
from app.models.client_profile import ClientProfile
from app.models.user import User
from app.services.token_service import build_token_pair

BASE = "/api/v1"


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
        gst_number="33ABCDE1234F1Z5",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def other_client_user(db):
    user = User(
        phone="9000000044",
        email="other-client@annai-illam.test",
        role="client",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = ClientProfile(
        user_id=user.id,
        client_type="company",
        company_name="Kaveri Logistics",
        contact_name="Meena Iyer",
        city="Coimbatore",
        state="Tamil Nadu",
    )
    db.add(profile)
    db.commit()
    return user


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
def other_client_headers(db, other_client_user):
    access_token, _ = build_token_pair(
        db,
        user_id=other_client_user.id,
        subject=other_client_user.phone,
        role=other_client_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


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
def worker_headers(db, worker_user):
    access_token, _ = build_token_pair(
        db,
        user_id=worker_user.id,
        subject=worker_user.phone,
        role=worker_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


def requirement_payload(**overrides):
    payload = {
        "category": "Security",
        "subcategory": "Night Guard",
        "number_of_workers": 3,
        "work_location": "Warehouse Gate 1",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "start_date": str(date.today() + timedelta(days=7)),
        "duration_days": 10,
        "shift_details": "20:00-06:00",
        "food_required": True,
        "accommodation_required": False,
        "budget_amount": 45000,
        "notes": "Bring ID proof at reporting time.",
        "site_latitude": 13.0827,
        "site_longitude": 80.2707,
        "geofence_radius_meters": 500,
    }
    payload.update(overrides)
    return payload


def quote_payload(requirement_id: int, **overrides):
    payload = {
        "requirement_id": requirement_id,
        "quoted_amount": 39000,
        "rate_per_worker": 1300,
        "total_worker_days": 30,
        "advance_amount": 10000,
        "payment_model": "advance",
        "valid_until": str(date.today() + timedelta(days=14)),
        "terms_notes": "Advance required before assignment.",
        "internal_notes": "Preferred client.",
    }
    payload.update(overrides)
    return payload


def create_requirement(client, headers, **overrides):
    response = client.post(
        f"{BASE}/client/requirements",
        json=requirement_payload(**overrides),
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["data"]["id"]


def mark_under_review(client, requirement_id: int, headers):
    response = client.post(
        f"{BASE}/admin/requirements/{requirement_id}/mark-review",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == RequirementStatus.UNDER_REVIEW.value


def create_quote(client, requirement_id: int, headers):
    response = client.post(
        f"{BASE}/admin/requirements/{requirement_id}/quote",
        json=quote_payload(requirement_id),
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["data"]


class TestClientRequirementCreation:
    def test_client_can_create_list_and_view_own_requirement(
        self,
        client,
        client_headers,
        client_profile,
    ):
        requirement_id = create_requirement(client, client_headers)

        detail = client.get(
            f"{BASE}/client/requirements/{requirement_id}",
            headers=client_headers,
        )
        assert detail.status_code == 200
        detail_data = detail.json()["data"]
        assert detail_data["id"] == requirement_id
        assert detail_data["category"] == "Security"
        assert detail_data["status"] == RequirementStatus.SUBMITTED.value
        assert detail_data["quote"] is None

        listing = client.get(f"{BASE}/client/requirements", headers=client_headers)
        assert listing.status_code == 200
        rows = listing.json()["data"]
        assert len(rows) == 1
        assert rows[0]["id"] == requirement_id
        assert rows[0]["status"] == RequirementStatus.SUBMITTED.value

    def test_create_requirement_requires_client_profile(self, client, client_headers):
        response = client.post(
            f"{BASE}/client/requirements",
            json=requirement_payload(),
            headers=client_headers,
        )
        assert response.status_code == 400
        assert "Client profile not found" in response.json()["message"]

    def test_create_requirement_requires_client_role(self, client, worker_headers):
        response = client.post(
            f"{BASE}/client/requirements",
            json=requirement_payload(),
            headers=worker_headers,
        )
        assert response.status_code == 403

    def test_other_client_cannot_view_requirement(
        self,
        client,
        client_headers,
        client_profile,
        other_client_headers,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.get(
            f"{BASE}/client/requirements/{requirement_id}",
            headers=other_client_headers,
        )
        assert response.status_code == 404


class TestAdminRequirementReview:
    def test_admin_can_list_filter_view_and_mark_requirement_under_review(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)

        listing = client.get(f"{BASE}/admin/requirements", headers=admin_headers)
        assert listing.status_code == 200
        assert listing.json()["data"]["total"] == 1

        filtered = client.get(
            f"{BASE}/admin/requirements",
            params={"status": RequirementStatus.SUBMITTED.value},
            headers=admin_headers,
        )
        assert filtered.status_code == 200
        assert filtered.json()["data"]["items"][0]["id"] == requirement_id

        detail = client.get(
            f"{BASE}/admin/requirements/{requirement_id}",
            headers=admin_headers,
        )
        assert detail.status_code == 200
        assert detail.json()["data"]["status"] == RequirementStatus.SUBMITTED.value

        mark_under_review(client, requirement_id, admin_headers)

        updated = client.get(
            f"{BASE}/admin/requirements/{requirement_id}",
            headers=admin_headers,
        )
        assert updated.json()["data"]["status"] == RequirementStatus.UNDER_REVIEW.value

    def test_mark_review_rejects_wrong_status(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/mark-review",
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Only submitted requirements" in response.json()["message"]

    def test_admin_requirement_endpoints_require_admin_role(
        self,
        client,
        client_headers,
        client_profile,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/mark-review",
            headers=client_headers,
        )
        assert response.status_code == 403


class TestQuoteFlow:
    def test_admin_creates_quote_and_client_approves_it(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)

        quote_data = create_quote(client, requirement_id, admin_headers)
        assert quote_data["quote_status"] == QuoteStatus.SENT.value
        assert quote_data["requirement_status"] == RequirementStatus.QUOTED.value

        client_detail = client.get(
            f"{BASE}/client/requirements/{requirement_id}",
            headers=client_headers,
        )
        quote = client_detail.json()["data"]["quote"]
        assert quote["quoted_amount"] == 39000
        assert quote["status"] == QuoteStatus.SENT.value

        decision = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert decision.status_code == 200
        decision_data = decision.json()["data"]
        assert decision_data["requirement_status"] == RequirementStatus.APPROVED.value
        assert decision_data["quote_status"] == QuoteStatus.APPROVED.value

    def test_client_can_reject_quote(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)
        create_quote(client, requirement_id, admin_headers)

        decision = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "reject"},
            headers=client_headers,
        )
        assert decision.status_code == 200
        assert decision.json()["data"]["requirement_status"] == RequirementStatus.REJECTED.value
        assert decision.json()["data"]["quote_status"] == QuoteStatus.REJECTED.value

    def test_quote_creation_requires_under_review_status(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/quote",
            json=quote_payload(requirement_id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "under review" in response.json()["message"].lower()

    def test_quote_creation_rejects_requirement_id_mismatch(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/quote",
            json=quote_payload(requirement_id + 1),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "mismatch" in response.json()["message"].lower()

    def test_duplicate_quote_is_rejected(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)
        create_quote(client, requirement_id, admin_headers)

        response = client.post(
            f"{BASE}/admin/requirements/{requirement_id}/quote",
            json=quote_payload(requirement_id),
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["message"]

    def test_quote_decision_requires_own_client_requirement(
        self,
        client,
        client_headers,
        client_profile,
        other_client_headers,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)
        create_quote(client, requirement_id, admin_headers)

        response = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "approve"},
            headers=other_client_headers,
        )
        assert response.status_code == 404

    def test_quote_decision_is_single_use(
        self,
        client,
        client_headers,
        client_profile,
        admin_headers,
    ):
        requirement_id = create_requirement(client, client_headers)
        mark_under_review(client, requirement_id, admin_headers)
        create_quote(client, requirement_id, admin_headers)

        first = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert first.status_code == 200

        second = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert second.status_code == 400
        assert "not in decision state" in second.json()["message"]

    def test_quote_decision_requires_existing_quote(
        self,
        client,
        client_headers,
        client_profile,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "approve"},
            headers=client_headers,
        )
        assert response.status_code == 400
        assert "Quote not found" in response.json()["message"]

    def test_invalid_quote_decision_action_is_rejected(
        self,
        client,
        client_headers,
        client_profile,
    ):
        requirement_id = create_requirement(client, client_headers)

        response = client.post(
            f"{BASE}/client/requirements/{requirement_id}/quote-decision",
            json={"action": "maybe"},
            headers=client_headers,
        )
        assert response.status_code == 422
