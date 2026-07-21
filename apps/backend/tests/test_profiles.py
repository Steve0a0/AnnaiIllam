"""Integration tests for client and worker self-profile management.

Covers:
  POST   /client/profile              — create client profile (duplicate, role)
  GET    /client/profile              — get own profile (404 when missing)
  PATCH  /client/profile              — update own profile

  POST   /worker/profile              — create worker profile (duplicate, role)
  GET    /worker/profile              — get own profile (404 when missing)
  PATCH  /worker/profile              — update own profile
  POST   /worker/profile/documents    — add document
  GET    /worker/profile/documents    — list documents
  GET    /worker/profile/documents/reminders — expiring documents
"""
from datetime import date, timedelta

import pytest

from app.models.client_profile import ClientProfile
from app.models.worker_document import WorkerDocument
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair

BASE = "/api/v1"
TODAY = date.today()


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
def existing_client_profile(db, client_user):
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
def existing_worker_profile(db, worker_user):
    profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Ravi Kumar",
        category="Security",
        subcategory="Night Guard",
        city="Chennai",
        state="Tamil Nadu",
        address="Velachery",
        skills=["Security"],
        experience_years="2-4 years",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _client_profile_payload(**overrides):
    payload = {
        "client_type": "company",
        "company_name": "New Company",
        "contact_name": "Contact Person",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "address": "Anna Nagar",
    }
    payload.update(overrides)
    return payload


def _worker_profile_payload(**overrides):
    payload = {
        "full_name": "New Worker",
        "category": "Housekeeping",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "address": "Velachery",
    }
    payload.update(overrides)
    return payload


# ══════════════════════════════════════════════════════════════════
# Client Profile
# ══════════════════════════════════════════════════════════════════


class TestClientProfileCreate:
    def test_client_creates_profile_successfully(self, client, client_headers):
        response = client.post(
            f"{BASE}/client/profile",
            json=_client_profile_payload(),
            headers=client_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_duplicate_profile_returns_400(self, client, client_headers, existing_client_profile):
        response = client.post(
            f"{BASE}/client/profile",
            json=_client_profile_payload(),
            headers=client_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["message"].lower()

    def test_worker_cannot_create_client_profile(self, client, worker_headers):
        response = client.post(
            f"{BASE}/client/profile",
            json=_client_profile_payload(),
            headers=worker_headers,
        )
        assert response.status_code == 403

    def test_admin_cannot_create_client_profile(self, client, admin_headers):
        response = client.post(
            f"{BASE}/client/profile",
            json=_client_profile_payload(),
            headers=admin_headers,
        )
        assert response.status_code == 403

    def test_unauthenticated_cannot_create_profile(self, client):
        response = client.post(f"{BASE}/client/profile", json=_client_profile_payload())
        assert response.status_code == 401


class TestClientProfileGet:
    def test_client_gets_own_profile(self, client, client_headers, existing_client_profile):
        response = client.get(f"{BASE}/client/profile", headers=client_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == existing_client_profile.id
        assert data["company_name"] == "Annam Textiles"
        assert data["contact_name"] == "Priya Raman"
        assert data["city"] == "Chennai"
        assert "phone" in data

    def test_client_without_profile_gets_404(self, client, client_headers):
        response = client.get(f"{BASE}/client/profile", headers=client_headers)
        assert response.status_code == 404

    def test_worker_cannot_get_client_profile(self, client, worker_headers):
        response = client.get(f"{BASE}/client/profile", headers=worker_headers)
        assert response.status_code == 403

    def test_unauthenticated_cannot_get_profile(self, client):
        response = client.get(f"{BASE}/client/profile")
        assert response.status_code == 401


class TestClientProfileUpdate:
    def test_client_updates_own_profile(self, client, db, client_headers, existing_client_profile):
        response = client.patch(
            f"{BASE}/client/profile",
            json={"city": "Coimbatore"},
            headers=client_headers,
        )
        assert response.status_code == 200
        db.refresh(existing_client_profile)
        assert existing_client_profile.city == "Coimbatore"

    def test_client_updates_preference_fields(self, client, db, client_headers, existing_client_profile):
        response = client.patch(
            f"{BASE}/client/profile",
            json={"food_preference": True, "accommodation_preference": False},
            headers=client_headers,
        )
        assert response.status_code == 200
        db.refresh(existing_client_profile)
        assert existing_client_profile.food_preference is True

    def test_client_without_profile_cannot_update(self, client, client_headers):
        response = client.patch(
            f"{BASE}/client/profile",
            json={"city": "Madurai"},
            headers=client_headers,
        )
        assert response.status_code == 404

    def test_worker_cannot_update_client_profile(self, client, worker_headers):
        response = client.patch(
            f"{BASE}/client/profile",
            json={"city": "Madurai"},
            headers=worker_headers,
        )
        assert response.status_code == 403


# ══════════════════════════════════════════════════════════════════
# Worker Profile
# ══════════════════════════════════════════════════════════════════


class TestWorkerProfileCreate:
    def test_worker_creates_profile_successfully(self, client, worker_headers):
        response = client.post(
            f"{BASE}/worker/profile",
            json=_worker_profile_payload(),
            headers=worker_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data

    def test_duplicate_worker_profile_returns_400(self, client, worker_headers, existing_worker_profile):
        response = client.post(
            f"{BASE}/worker/profile",
            json=_worker_profile_payload(),
            headers=worker_headers,
        )
        assert response.status_code == 400

    def test_client_cannot_create_worker_profile(self, client, client_headers):
        response = client.post(
            f"{BASE}/worker/profile",
            json=_worker_profile_payload(),
            headers=client_headers,
        )
        assert response.status_code == 403


class TestWorkerProfileGet:
    def test_worker_gets_own_profile(self, client, worker_headers, existing_worker_profile):
        response = client.get(f"{BASE}/worker/profile", headers=worker_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == existing_worker_profile.id
        assert data["full_name"] == "Ravi Kumar"
        assert data["city"] == "Chennai"
        assert "documents" in data

    def test_worker_without_profile_gets_404(self, client, worker_headers):
        response = client.get(f"{BASE}/worker/profile", headers=worker_headers)
        assert response.status_code == 404

    def test_client_cannot_get_worker_profile_endpoint(self, client, client_headers):
        response = client.get(f"{BASE}/worker/profile", headers=client_headers)
        assert response.status_code == 403


class TestWorkerProfileUpdate:
    def test_worker_updates_availability(self, client, db, worker_headers, existing_worker_profile):
        response = client.patch(
            f"{BASE}/worker/profile",
            json={"is_available": False},
            headers=worker_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["is_available"] is False
        db.refresh(existing_worker_profile)
        assert existing_worker_profile.is_available is False

    def test_worker_updates_available_shifts(self, client, db, worker_headers, existing_worker_profile):
        response = client.patch(
            f"{BASE}/worker/profile",
            json={"available_shifts": ["Morning", "Afternoon"]},
            headers=worker_headers,
        )
        assert response.status_code == 200
        db.refresh(existing_worker_profile)
        assert "Morning" in existing_worker_profile.available_shifts

    def test_worker_without_profile_cannot_update(self, client, worker_headers):
        response = client.patch(
            f"{BASE}/worker/profile",
            json={"is_available": True},
            headers=worker_headers,
        )
        assert response.status_code == 404

    def test_client_cannot_update_worker_profile(self, client, client_headers):
        response = client.patch(
            f"{BASE}/worker/profile",
            json={"is_available": True},
            headers=client_headers,
        )
        assert response.status_code == 403


# ══════════════════════════════════════════════════════════════════
# Worker Documents
# ══════════════════════════════════════════════════════════════════


class TestWorkerDocuments:
    def test_worker_adds_document(self, client, worker_headers, existing_worker_profile):
        response = client.post(
            f"{BASE}/worker/profile/documents",
            json={
                "document_type": "id_proof",
                "file_url": "local:/uploads/id.jpg",
            },
            headers=worker_headers,
        )
        assert response.status_code == 200
        assert "id" in response.json()["data"]

    def test_worker_lists_own_documents(self, client, db, worker_headers, existing_worker_profile):
        doc = WorkerDocument(
            worker_profile_id=existing_worker_profile.id,
            user_id=existing_worker_profile.user_id,
            document_type="id_proof",
            file_url="local:/uploads/id.jpg",
            verification_status="pending",
        )
        db.add(doc)
        db.commit()

        response = client.get(f"{BASE}/worker/profile/documents", headers=worker_headers)
        assert response.status_code == 200
        docs = response.json()["data"]
        assert isinstance(docs, list)
        assert len(docs) >= 1

    def test_worker_without_profile_cannot_add_document(self, client, worker_headers):
        response = client.post(
            f"{BASE}/worker/profile/documents",
            json={"document_type": "id_proof", "file_url": "local:/uploads/id.jpg"},
            headers=worker_headers,
        )
        assert response.status_code == 404

    def test_client_cannot_add_worker_document(self, client, client_headers):
        response = client.post(
            f"{BASE}/worker/profile/documents",
            json={"document_type": "id_proof", "file_url": "local:/uploads/id.jpg"},
            headers=client_headers,
        )
        assert response.status_code == 403


class TestWorkerDocumentReminders:
    def test_no_reminders_when_no_documents(self, client, worker_headers, existing_worker_profile):
        response = client.get(
            f"{BASE}/worker/profile/documents/reminders",
            headers=worker_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_expiring_document_appears_in_reminders(self, client, db, worker_headers, existing_worker_profile):
        expiry = TODAY + timedelta(days=10)
        doc = WorkerDocument(
            worker_profile_id=existing_worker_profile.id,
            user_id=existing_worker_profile.user_id,
            document_type="id_proof",
            file_url="local:/uploads/id.jpg",
            verification_status="verified",
            expiry_date=expiry,
        )
        db.add(doc)
        db.commit()

        response = client.get(
            f"{BASE}/worker/profile/documents/reminders",
            params={"days": 30},
            headers=worker_headers,
        )
        assert response.status_code == 200
        reminders = response.json()["data"]
        assert len(reminders) >= 1
        assert reminders[0]["state"] == "expiring_soon"
        assert reminders[0]["days_remaining"] <= 30

    def test_expired_document_appears_as_expired_state(self, client, db, worker_headers, existing_worker_profile):
        expiry = TODAY - timedelta(days=5)
        doc = WorkerDocument(
            worker_profile_id=existing_worker_profile.id,
            user_id=existing_worker_profile.user_id,
            document_type="id_proof",
            file_url="local:/uploads/id_old.jpg",
            verification_status="verified",
            expiry_date=expiry,
        )
        db.add(doc)
        db.commit()

        response = client.get(
            f"{BASE}/worker/profile/documents/reminders",
            headers=worker_headers,
        )
        assert response.status_code == 200
        reminders = response.json()["data"]
        expired = [r for r in reminders if r["state"] == "expired"]
        assert len(expired) >= 1

    def test_far_future_document_not_in_reminders(self, client, db, worker_headers, existing_worker_profile):
        expiry = TODAY + timedelta(days=365)
        doc = WorkerDocument(
            worker_profile_id=existing_worker_profile.id,
            user_id=existing_worker_profile.user_id,
            document_type="id_proof",
            file_url="local:/uploads/id_future.jpg",
            verification_status="verified",
            expiry_date=expiry,
        )
        db.add(doc)
        db.commit()

        response = client.get(
            f"{BASE}/worker/profile/documents/reminders",
            params={"days": 30},
            headers=worker_headers,
        )
        reminders = response.json()["data"]
        assert all(r["days_remaining"] <= 30 for r in reminders)

    def test_worker_without_profile_gets_404(self, client, worker_headers):
        response = client.get(
            f"{BASE}/worker/profile/documents/reminders",
            headers=worker_headers,
        )
        assert response.status_code == 404
