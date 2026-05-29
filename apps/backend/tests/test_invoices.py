"""Tests for Feature 6: Invoice Generation.

Covers:
1. Generate invoice for completed requirement → correct GST calculation
2. Generate invoice for in_progress requirement → 400
3. Duplicate invoice for same requirement → 400
4. Issue invoice → client receives push notification
5. Client GET /client/invoices → sees only their own, not other clients
"""
from datetime import date
from unittest.mock import patch

import pytest

from app.core.statuses import RequirementStatus
from app.core.payment_constants import PaymentModel
from app.models.client_profile import ClientProfile
from app.models.invoice import Invoice
from app.models.quote import Quote
from app.models.requirement import Requirement
from app.services.token_service import build_token_pair

BASE = "/api/v1"


# ──────────────────────────────────────────────────────────────────
# Auth header fixtures
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


# ──────────────────────────────────────────────────────────────────
# Domain fixtures
# ──────────────────────────────────────────────────────────────────


@pytest.fixture
def client_profile(db, client_user):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Annai Textiles",
        contact_name="Priya Raman",
        city="Chennai",
        state="Tamil Nadu",
        address="T Nagar",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _make_requirement(db, client_profile, client_user, status: str) -> Requirement:
    req = Requirement(
        client_id=client_profile.id,
        category="Housekeeping",
        subcategory="Sweeping",
        number_of_workers=2,
        work_location="Site A",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date(2026, 6, 1),
        duration_days=30,
        shift_details="Morning 08:00-16:00",
        budget_amount=50000,
        status=status,
        created_by_user_id=client_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def _make_quote(db, requirement, admin_user, quoted_amount: int) -> Quote:
    quote = Quote(
        requirement_id=requirement.id,
        quoted_amount=quoted_amount,
        payment_model=PaymentModel.CLIENT_PAYS_COMPANY.value,
        status="approved",
        created_by_user_id=admin_user.id,
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


# ──────────────────────────────────────────────────────────────────
# Test 1: Generate invoice for completed requirement — correct GST
# ──────────────────────────────────────────────────────────────────


def test_generate_invoice_for_completed_requirement(
    client, db, admin_headers, admin_user, client_user, client_profile
):
    req = _make_requirement(db, client_profile, client_user, RequirementStatus.COMPLETED.value)
    _make_quote(db, req, admin_user, quoted_amount=10000)

    resp = client.post(
        f"{BASE}/admin/invoices/generate",
        json={"requirement_id": req.id},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.json()
    data = resp.json()["data"]

    assert data["status"] == "draft"
    assert data["subtotal"] == 10000
    assert data["gst_rate"] == 18.0
    assert data["gst_amount"] == 1800          # 10000 * 18 / 100
    assert data["total_amount"] == 11800        # 10000 + 1800
    assert data["requirement_id"] == req.id
    assert data["client_id"] == client_profile.id
    assert data["invoice_number"].startswith("INV-")


# ──────────────────────────────────────────────────────────────────
# Test 2: Generate invoice for in_progress requirement → 400
# ──────────────────────────────────────────────────────────────────


def test_generate_invoice_in_progress_requirement(
    client, db, admin_headers, admin_user, client_user, client_profile
):
    req = _make_requirement(db, client_profile, client_user, RequirementStatus.IN_PROGRESS.value)
    _make_quote(db, req, admin_user, quoted_amount=10000)

    resp = client.post(
        f"{BASE}/admin/invoices/generate",
        json={"requirement_id": req.id},
        headers=admin_headers,
    )
    assert resp.status_code == 400
    assert "completed" in resp.json()["message"].lower()


# ──────────────────────────────────────────────────────────────────
# Test 3: Duplicate invoice for same requirement → 400
# ──────────────────────────────────────────────────────────────────


def test_generate_duplicate_invoice_blocked(
    client, db, admin_headers, admin_user, client_user, client_profile
):
    req = _make_requirement(db, client_profile, client_user, RequirementStatus.COMPLETED.value)
    _make_quote(db, req, admin_user, quoted_amount=10000)

    resp1 = client.post(
        f"{BASE}/admin/invoices/generate",
        json={"requirement_id": req.id},
        headers=admin_headers,
    )
    assert resp1.status_code == 200

    resp2 = client.post(
        f"{BASE}/admin/invoices/generate",
        json={"requirement_id": req.id},
        headers=admin_headers,
    )
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["message"].lower()


# ──────────────────────────────────────────────────────────────────
# Test 4: Issue invoice → status=issued, client gets notification
# ──────────────────────────────────────────────────────────────────


def test_issue_invoice_sends_notification(
    client, db, admin_headers, admin_user, client_user, client_profile
):
    req = _make_requirement(db, client_profile, client_user, RequirementStatus.COMPLETED.value)
    _make_quote(db, req, admin_user, quoted_amount=20000)

    gen_resp = client.post(
        f"{BASE}/admin/invoices/generate",
        json={"requirement_id": req.id},
        headers=admin_headers,
    )
    assert gen_resp.status_code == 200
    invoice_id = gen_resp.json()["data"]["id"]

    with patch(
        "app.api.admin_invoice.enqueue_push_to_user"
    ) as mock_push:
        issue_resp = client.post(
            f"{BASE}/admin/invoices/{invoice_id}/issue",
            headers=admin_headers,
        )
        assert issue_resp.status_code == 200, issue_resp.json()
        data = issue_resp.json()["data"]
        assert data["status"] == "issued"
        assert data["issued_at"] is not None
        mock_push.assert_called_once()
        call_kwargs = mock_push.call_args.kwargs
        assert call_kwargs["user_id"] == client_user.id


# ──────────────────────────────────────────────────────────────────
# Test 5: Client sees only their own invoices, not other clients'
# ──────────────────────────────────────────────────────────────────


def test_client_sees_only_own_invoices(
    client, db, admin_headers, admin_user, client_user, client_profile
):
    from app.models.user import User
    from app.core.roles import UserRole

    # Create a second client user & profile
    other_user = User(
        phone="+919888888888",
        email="other@annai-illam.test",
        role=UserRole.CLIENT.value,
        is_active=True,
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    other_profile = ClientProfile(
        user_id=other_user.id,
        client_type="individual",
        contact_name="Another Client",
        city="Coimbatore",
        state="Tamil Nadu",
        address="RS Puram",
    )
    db.add(other_profile)
    db.commit()
    db.refresh(other_profile)

    # Requirement + invoice for the primary client
    req1 = _make_requirement(db, client_profile, client_user, RequirementStatus.COMPLETED.value)
    _make_quote(db, req1, admin_user, quoted_amount=15000)
    gen1 = client.post(
        f"{BASE}/admin/invoices/generate",
        json={"requirement_id": req1.id},
        headers=admin_headers,
    )
    assert gen1.status_code == 200

    # Requirement + invoice for the other client
    req2 = Requirement(
        client_id=other_profile.id,
        category="Security",
        subcategory="Guard",
        number_of_workers=1,
        work_location="Gate 1",
        city="Coimbatore",
        state="Tamil Nadu",
        start_date=date(2026, 6, 1),
        duration_days=15,
        shift_details="Day shift",
        budget_amount=20000,
        status=RequirementStatus.COMPLETED.value,
        created_by_user_id=other_user.id,
    )
    db.add(req2)
    db.commit()
    db.refresh(req2)
    _make_quote(db, req2, admin_user, quoted_amount=20000)
    gen2 = client.post(
        f"{BASE}/admin/invoices/generate",
        json={"requirement_id": req2.id},
        headers=admin_headers,
    )
    assert gen2.status_code == 200

    # Primary client should see only their invoice
    access_token, _ = build_token_pair(
        db,
        user_id=client_user.id,
        subject=client_user.phone,
        role=client_user.role,
    )
    primary_headers = {"Authorization": f"Bearer {access_token}"}

    list_resp = client.get(f"{BASE}/client/invoices", headers=primary_headers)
    assert list_resp.status_code == 200
    invoices = list_resp.json()["data"]["invoices"]
    assert len(invoices) == 1
    assert invoices[0]["requirement_id"] == req1.id


# ──────────────────────────────────────────────────────────────────
# Test 6: Non-admin cannot generate invoice
# ──────────────────────────────────────────────────────────────────


def test_generate_invoice_requires_admin(
    client, db, client_headers, admin_user, client_user, client_profile
):
    req = _make_requirement(db, client_profile, client_user, RequirementStatus.COMPLETED.value)
    _make_quote(db, req, admin_user, quoted_amount=10000)

    resp = client.post(
        f"{BASE}/admin/invoices/generate",
        json={"requirement_id": req.id},
        headers=client_headers,
    )
    assert resp.status_code == 403


# ──────────────────────────────────────────────────────────────────
# Test 7: Client can GET their own invoice by ID
# ──────────────────────────────────────────────────────────────────


def test_client_get_invoice_by_id(
    client, db, admin_headers, admin_user, client_user, client_profile
):
    req = _make_requirement(db, client_profile, client_user, RequirementStatus.COMPLETED.value)
    _make_quote(db, req, admin_user, quoted_amount=5000)

    gen_resp = client.post(
        f"{BASE}/admin/invoices/generate",
        json={"requirement_id": req.id},
        headers=admin_headers,
    )
    assert gen_resp.status_code == 200
    invoice_id = gen_resp.json()["data"]["id"]

    access_token, _ = build_token_pair(
        db,
        user_id=client_user.id,
        subject=client_user.phone,
        role=client_user.role,
    )
    headers = {"Authorization": f"Bearer {access_token}"}

    detail_resp = client.get(f"{BASE}/client/invoices/{invoice_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["data"]["id"] == invoice_id
