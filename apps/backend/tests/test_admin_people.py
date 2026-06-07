"""Integration tests for admin people management.

Covers:
  GET  /admin/people/clients           — list clients (pagination, role)
  GET  /admin/people/clients/{id}      — client detail with requirements
  POST /admin/people/clients           — create client (duplicate phone, role)
  PATCH /admin/people/clients/{id}     — update client
  POST /admin/people/clients/{id}/deactivate — deactivate client (double-deactivate)
  GET  /admin/people/workers           — list workers (filters, role)
  GET  /admin/people/workers/{id}      — worker detail
  PATCH /admin/people/workers/{id}     — update worker profile fields
  PATCH /admin/people/workers/{id}/availability — admin availability toggle
  POST /admin/people/workers/import    — bulk import (created, skipped)
  GET  /admin/people/admin-users       — list admin users
  POST /admin/people/admin-users       — create admin user (duplicate email)
"""

import pytest

from app.core.statuses import RequirementStatus
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_profile import WorkerProfile
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
        address="T Nagar",
        gst_number="33ABCDE1234F1Z5",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


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
        skills=["Security", "Night Guard"],
        experience_years="2-4 years",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _client_create_payload(**overrides):
    payload = {
        "phone": "9100200300",
        "client_type": "company",
        "company_name": "Test Corp",
        "contact_name": "Test Manager",
        "city": "Chennai",
        "state": "Tamil Nadu",
    }
    payload.update(overrides)
    return payload


# ──────────────────────────────────────────────────────────────────
# Admin Client List
# ──────────────────────────────────────────────────────────────────


class TestAdminClientList:
    def test_admin_lists_clients(self, client, admin_headers, client_profile):
        response = client.get(f"{BASE}/admin/people/clients", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        ids = [c["id"] for c in data["items"]]
        assert client_profile.id in ids

    def test_list_includes_phone_and_is_active(self, client, admin_headers, client_profile, client_user):
        response = client.get(f"{BASE}/admin/people/clients", headers=admin_headers)
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        item = next(c for c in items if c["id"] == client_profile.id)
        assert item["phone"] == client_user.phone
        assert item["is_active"] is True

    def test_non_admin_cannot_list_clients(self, client, client_headers):
        response = client.get(f"{BASE}/admin/people/clients", headers=client_headers)
        assert response.status_code == 403

    def test_unauthenticated_cannot_list_clients(self, client):
        response = client.get(f"{BASE}/admin/people/clients")
        assert response.status_code == 401

    def test_response_includes_pagination_meta(self, client, admin_headers):
        response = client.get(f"{BASE}/admin/people/clients", headers=admin_headers)
        data = response.json()["data"]
        assert "total" in data
        assert "page" in data


# ──────────────────────────────────────────────────────────────────
# Admin Client Detail
# ──────────────────────────────────────────────────────────────────


class TestAdminClientDetail:
    def test_admin_gets_client_detail(self, client, admin_headers, client_profile, client_user):
        response = client.get(
            f"{BASE}/admin/people/clients/{client_profile.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == client_profile.id
        assert data["phone"] == client_user.phone
        assert data["company_name"] == "Annam Textiles"
        assert "requirements" in data
        assert isinstance(data["requirements"], list)

    def test_client_detail_includes_requirements(
        self, client, db, admin_headers, client_profile, client_user
    ):
        req = Requirement(
            client_id=client_profile.id,
            category="Security",
            number_of_workers=2,
            work_location="Gate 1",
            city="Chennai",
            state="Tamil Nadu",
            start_date=__import__("datetime").date.today(),
            duration_days=5,
            shift_details="Day",
            budget_amount=10000,
            status=RequirementStatus.SUBMITTED.value,
            created_by_user_id=client_user.id,
        )
        db.add(req)
        db.commit()

        response = client.get(
            f"{BASE}/admin/people/clients/{client_profile.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        requirements = response.json()["data"]["requirements"]
        assert len(requirements) == 1
        assert requirements[0]["id"] == req.id

    def test_nonexistent_client_returns_404(self, client, admin_headers):
        response = client.get(
            f"{BASE}/admin/people/clients/999999",
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_non_admin_cannot_get_client_detail(self, client, client_headers, client_profile):
        response = client.get(
            f"{BASE}/admin/people/clients/{client_profile.id}",
            headers=client_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Admin Client Create
# ──────────────────────────────────────────────────────────────────


class TestAdminClientCreate:
    def test_admin_creates_client_successfully(self, client, admin_headers):
        response = client.post(
            f"{BASE}/admin/people/clients",
            json=_client_create_payload(),
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "id" in data
        assert "user_id" in data
        assert data["phone"] == "+919100200300"
        assert data["contact_name"] == "Test Manager"
        assert data["company_name"] == "Test Corp"

    def test_duplicate_phone_returns_409(self, client, admin_headers, client_user):
        response = client.post(
            f"{BASE}/admin/people/clients",
            json=_client_create_payload(phone=client_user.phone),
            headers=admin_headers,
        )
        assert response.status_code == 409

    def test_non_admin_cannot_create_client(self, client, client_headers):
        response = client.post(
            f"{BASE}/admin/people/clients",
            json=_client_create_payload(),
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_missing_required_field_returns_422(self, client, admin_headers):
        payload = _client_create_payload()
        del payload["contact_name"]
        response = client.post(
            f"{BASE}/admin/people/clients",
            json=payload,
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_gst_number_is_optional(self, client, admin_headers):
        payload = _client_create_payload()
        payload["gst_number"] = "27AAECN1234A1Z3"
        response = client.post(
            f"{BASE}/admin/people/clients",
            json=payload,
            headers=admin_headers,
        )
        assert response.status_code == 200


# ──────────────────────────────────────────────────────────────────
# Admin Client Update
# ──────────────────────────────────────────────────────────────────


class TestAdminClientUpdate:
    def test_admin_updates_client_successfully(self, client, admin_headers, client_profile):
        response = client.patch(
            f"{BASE}/admin/people/clients/{client_profile.id}",
            json={
                "contact_name": "Updated Manager",
                "city": "Coimbatore",
                "state": "Tamil Nadu",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["contact_name"] == "Updated Manager"
        assert data["city"] == "Coimbatore"

    def test_update_nonexistent_client_returns_404(self, client, admin_headers):
        response = client.patch(
            f"{BASE}/admin/people/clients/999999",
            json={"contact_name": "Nobody", "city": "Madurai", "state": "Tamil Nadu"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_non_admin_cannot_update_client(self, client, client_headers, client_profile):
        response = client.patch(
            f"{BASE}/admin/people/clients/{client_profile.id}",
            json={"contact_name": "Hacker", "city": "Chennai", "state": "Tamil Nadu"},
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_update_clears_gst_when_null(self, client, db, admin_headers, client_profile):
        response = client.patch(
            f"{BASE}/admin/people/clients/{client_profile.id}",
            json={"contact_name": "Priya Raman", "city": "Chennai", "state": "Tamil Nadu", "gst_number": None},
            headers=admin_headers,
        )
        assert response.status_code == 200
        db.refresh(client_profile)
        assert client_profile.gst_number is None


# ──────────────────────────────────────────────────────────────────
# Admin Client Deactivate
# ──────────────────────────────────────────────────────────────────


class TestAdminClientDeactivate:
    def test_admin_deactivates_client(self, client, db, admin_headers, client_profile, client_user):
        response = client.post(
            f"{BASE}/admin/people/clients/{client_profile.id}/deactivate",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["is_active"] is False
        db.refresh(client_user)
        assert client_user.is_active is False

    def test_double_deactivate_returns_422(self, client, db, admin_headers, client_profile, client_user):
        client_user.is_active = False
        db.commit()
        response = client.post(
            f"{BASE}/admin/people/clients/{client_profile.id}/deactivate",
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_deactivate_nonexistent_client_returns_404(self, client, admin_headers):
        response = client.post(
            f"{BASE}/admin/people/clients/999999/deactivate",
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_non_admin_cannot_deactivate_client(self, client, client_headers, client_profile):
        response = client.post(
            f"{BASE}/admin/people/clients/{client_profile.id}/deactivate",
            headers=client_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Admin Worker List
# ──────────────────────────────────────────────────────────────────


class TestAdminWorkerList:
    def test_admin_lists_workers(self, client, admin_headers, worker_profile):
        response = client.get(f"{BASE}/admin/people/workers", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        ids = [w["id"] for w in data["items"]]
        assert worker_profile.id in ids

    def test_list_worker_includes_key_fields(self, client, admin_headers, worker_profile, worker_user):
        response = client.get(f"{BASE}/admin/people/workers", headers=admin_headers)
        items = response.json()["data"]["items"]
        item = next(w for w in items if w["id"] == worker_profile.id)
        assert item["full_name"] == "Ravi Kumar"
        assert item["phone"] == worker_user.phone
        assert item["category"] == "Security"
        assert "documents" in item

    def test_filter_by_verification_status(self, client, admin_headers, worker_profile):
        response = client.get(
            f"{BASE}/admin/people/workers",
            params={"verification_status": "approved"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert all(w["verification_status"] == "approved" for w in items)

    def test_filter_by_city(self, client, admin_headers, worker_profile):
        response = client.get(
            f"{BASE}/admin/people/workers",
            params={"city": "Chennai"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert any(w["id"] == worker_profile.id for w in items)

    def test_filter_by_is_available_true(self, client, admin_headers, worker_profile):
        response = client.get(
            f"{BASE}/admin/people/workers",
            params={"is_available": "true"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert all(w["is_available"] is True for w in items)
        assert any(w["id"] == worker_profile.id for w in items)

    def test_filter_by_is_available_false_excludes_available_worker(
        self, client, admin_headers, worker_profile
    ):
        response = client.get(
            f"{BASE}/admin/people/workers",
            params={"is_available": "false"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        # worker_profile.is_available=True — must not appear
        assert all(w["id"] != worker_profile.id for w in items)

    def test_filter_by_category(self, client, admin_headers, worker_profile):
        response = client.get(
            f"{BASE}/admin/people/workers",
            params={"category": "Security"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert all("security" in w["category"].lower() for w in items)
        assert any(w["id"] == worker_profile.id for w in items)

    def test_filter_by_category_no_match(self, client, admin_headers, worker_profile):
        response = client.get(
            f"{BASE}/admin/people/workers",
            params={"category": "Nursing"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert all(w["id"] != worker_profile.id for w in items)

    def test_pagination_returns_correct_shape(self, client, admin_headers, worker_profile):
        response = client.get(
            f"{BASE}/admin/people/workers",
            params={"page": 1, "page_size": 5},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "items" in data
        assert "total" in data
        assert "total_pages" in data
        assert "page" in data

    def test_non_admin_cannot_list_workers(self, client, worker_headers):
        response = client.get(f"{BASE}/admin/people/workers", headers=worker_headers)
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Admin Worker Detail
# ──────────────────────────────────────────────────────────────────


class TestAdminWorkerDetail:
    def test_admin_gets_worker_detail(self, client, admin_headers, worker_profile):
        response = client.get(
            f"{BASE}/admin/people/workers/{worker_profile.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == worker_profile.id
        assert data["full_name"] == "Ravi Kumar"
        assert "documents" in data
        assert "assignments" in data
        assert "payroll_items" in data

    def test_nonexistent_worker_returns_404(self, client, admin_headers):
        response = client.get(
            f"{BASE}/admin/people/workers/999999",
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_non_admin_cannot_get_worker_detail(self, client, worker_headers, worker_profile):
        response = client.get(
            f"{BASE}/admin/people/workers/{worker_profile.id}",
            headers=worker_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Admin Worker Update
# ──────────────────────────────────────────────────────────────────


class TestAdminWorkerUpdate:
    def test_admin_updates_worker_city(self, client, db, admin_headers, worker_profile):
        response = client.patch(
            f"{BASE}/admin/people/workers/{worker_profile.id}",
            json={"city": "Coimbatore"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        db.refresh(worker_profile)
        assert worker_profile.city == "Coimbatore"

    def test_admin_updates_worker_skills(self, client, db, admin_headers, worker_profile):
        response = client.patch(
            f"{BASE}/admin/people/workers/{worker_profile.id}",
            json={"skills": ["Security", "CCTV Monitoring"]},
            headers=admin_headers,
        )
        assert response.status_code == 200
        db.refresh(worker_profile)
        assert "CCTV Monitoring" in worker_profile.skills

    def test_admin_toggles_worker_availability_via_update(self, client, db, admin_headers, worker_profile):
        response = client.patch(
            f"{BASE}/admin/people/workers/{worker_profile.id}",
            json={"is_available": False},
            headers=admin_headers,
        )
        assert response.status_code == 200
        db.refresh(worker_profile)
        assert worker_profile.is_available is False

    def test_update_nonexistent_worker_returns_404(self, client, admin_headers):
        response = client.patch(
            f"{BASE}/admin/people/workers/999999",
            json={"city": "Madurai"},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_non_admin_cannot_update_worker(self, client, worker_headers, worker_profile):
        response = client.patch(
            f"{BASE}/admin/people/workers/{worker_profile.id}",
            json={"city": "Madurai"},
            headers=worker_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Admin Worker Availability Toggle (dedicated endpoint)
# ──────────────────────────────────────────────────────────────────


class TestAdminWorkerAvailabilityToggle:
    def test_admin_marks_worker_unavailable(self, client, db, admin_headers, worker_profile, worker_user):
        response = client.patch(
            f"{BASE}/admin/people/workers/{worker_user.id}/availability",
            json={"is_available": False},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["is_available"] is False
        db.refresh(worker_profile)
        assert worker_profile.is_available is False

    def test_admin_marks_worker_available(self, client, db, admin_headers, worker_profile, worker_user):
        worker_profile.is_available = False
        db.commit()
        response = client.patch(
            f"{BASE}/admin/people/workers/{worker_user.id}/availability",
            json={"is_available": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        db.refresh(worker_profile)
        assert worker_profile.is_available is True

    def test_availability_toggle_on_nonexistent_worker_returns_404(self, client, admin_headers):
        response = client.patch(
            f"{BASE}/admin/people/workers/999999/availability",
            json={"is_available": False},
            headers=admin_headers,
        )
        assert response.status_code == 404

    def test_non_admin_cannot_toggle_worker_availability(self, client, client_headers, worker_user):
        response = client.patch(
            f"{BASE}/admin/people/workers/{worker_user.id}/availability",
            json={"is_available": False},
            headers=client_headers,
        )
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Admin Worker Bulk Import
# ──────────────────────────────────────────────────────────────────


class TestAdminWorkerBulkImport:
    def _import_payload(self, *workers):
        return {"workers": list(workers)}

    def _worker_entry(self, phone="9200100200", **overrides):
        entry = {
            "phone": phone,
            "full_name": "Import Worker",
            "category": "Housekeeping",
            "city": "Madurai",
            "state": "Tamil Nadu",
        }
        entry.update(overrides)
        return entry

    def test_bulk_import_creates_new_workers(self, client, db, admin_headers):
        response = client.post(
            f"{BASE}/admin/people/workers/import",
            json=self._import_payload(self._worker_entry("9200100201"), self._worker_entry("9200100202")),
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["created_count"] == 2
        assert data["skipped_count"] == 0

    def test_bulk_import_skips_existing_phone(self, client, admin_headers, worker_user):
        response = client.post(
            f"{BASE}/admin/people/workers/import",
            json=self._import_payload(self._worker_entry(phone=worker_user.phone)),
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["created_count"] == 0
        assert data["skipped_count"] == 1
        assert data["skipped"][0]["phone"] == worker_user.phone

    def test_bulk_import_mixed_creates_and_skips(self, client, admin_headers, worker_user):
        response = client.post(
            f"{BASE}/admin/people/workers/import",
            json=self._import_payload(
                self._worker_entry("9200100301"),  # new
                self._worker_entry(phone=worker_user.phone),  # duplicate
            ),
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["created_count"] == 1
        assert data["skipped_count"] == 1

    def test_non_admin_cannot_bulk_import(self, client, worker_headers):
        response = client.post(
            f"{BASE}/admin/people/workers/import",
            json=self._import_payload(self._worker_entry()),
            headers=worker_headers,
        )
        assert response.status_code == 403

    def test_empty_import_list_rejected_by_schema(self, client, admin_headers):
        # Schema enforces min_length=1 on the workers list
        response = client.post(
            f"{BASE}/admin/people/workers/import",
            json={"workers": []},
            headers=admin_headers,
        )
        assert response.status_code == 422


# ──────────────────────────────────────────────────────────────────
# Admin User Management
# ──────────────────────────────────────────────────────────────────


class TestAdminUserManagement:
    def test_admin_lists_admin_users(self, client, admin_headers, admin_user):
        response = client.get(f"{BASE}/admin/people/admin-users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data, list)
        ids = [u["id"] for u in data]
        assert admin_user.id in ids

    def test_admin_users_include_email_and_name(self, client, admin_headers, admin_user):
        response = client.get(f"{BASE}/admin/people/admin-users", headers=admin_headers)
        users = response.json()["data"]
        user = next(u for u in users if u["id"] == admin_user.id)
        assert "email" in user
        assert "is_active" in user
        assert "permission_group" in user

    def test_non_admin_cannot_list_admin_users(self, client, client_headers):
        response = client.get(f"{BASE}/admin/people/admin-users", headers=client_headers)
        assert response.status_code == 403

    def test_admin_creates_new_admin_user(self, client, admin_headers):
        response = client.post(
            f"{BASE}/admin/people/admin-users",
            json={
                "email": "newadmin@annai-illam.test",
                "name": "New Admin",
                "password": "SecureAdminPass123!",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["email"] == "newadmin@annai-illam.test"
        assert data["name"] == "New Admin"
        assert data["permission_group"] == "ops_admin"

    def test_admin_creates_user_with_custom_permission_group(self, client, admin_headers):
        response = client.post(
            f"{BASE}/admin/people/admin-users",
            json={
                "email": "financeadmin@annai-illam.test",
                "name": "Finance Admin",
                "password": "SecureAdminPass123!",
                "permission_group": "finance_admin",
            },
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["permission_group"] == "finance_admin"

    def test_invalid_permission_group_returns_422(self, client, admin_headers):
        response = client.post(
            f"{BASE}/admin/people/admin-users",
            json={
                "email": "badgroup@annai-illam.test",
                "name": "Bad Group",
                "password": "SecureAdminPass123!",
                "permission_group": "god_mode",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_duplicate_email_returns_409(self, client, admin_headers, admin_user):
        response = client.post(
            f"{BASE}/admin/people/admin-users",
            json={
                "email": admin_user.email,
                "name": "Duplicate Admin",
                "password": "SecureAdminPass123!",
            },
            headers=admin_headers,
        )
        assert response.status_code == 409

    def test_non_admin_cannot_create_admin_user(self, client, client_headers):
        response = client.post(
            f"{BASE}/admin/people/admin-users",
            json={
                "email": "fake@annai-illam.test",
                "name": "Fake Admin",
                "password": "SecureAdminPass123!",
            },
            headers=client_headers,
        )
        assert response.status_code == 403

    def test_weak_password_returns_422(self, client, admin_headers):
        response = client.post(
            f"{BASE}/admin/people/admin-users",
            json={
                "email": "weak@annai-illam.test",
                "name": "Weak Admin",
                "password": "short",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422
