"""E2E smoke test: full staffing business flow.

Exercises every major domain boundary in one linear sequence:
  Auth → Profile setup → Requirement → Quote → Payment →
  Assignment → Attendance → Payroll → Disbursement → Rating
"""

from datetime import date, timedelta
from unittest.mock import patch

BASE = "/api/v1"


def _ok(response, step: str) -> dict:
    assert response.status_code == 200, (
        f"[{step}] expected 200, got {response.status_code} — {response.text}"
    )
    body = response.json()
    assert body.get("success") is True, f"[{step}] success=False — {body}"
    return body.get("data", {})


@patch("app.api.admin_disbursements.enqueue_push_to_user")
@patch("app.api.admin_finance.enqueue_push_to_user")
@patch("app.api.admin_attendance.enqueue_push_to_user")
@patch("app.api.worker_attendance.send_push_to_user")
@patch("app.api.worker_attendance._validate_selfie")
@patch("app.api.admin_assignments.send_push_to_user")
@patch("app.api.client_requirements.enqueue_push_to_user")
@patch("app.api.admin_requirements.enqueue_push_to_user")
@patch("app.api.admin_people.enqueue_push_to_user")
def test_full_staffing_flow(
    _mock_people_push,
    _mock_admin_req_push,
    _mock_client_req_push,
    _mock_assign_send,
    mock_selfie,
    _mock_checkin_send,
    _mock_attendance_push,
    _mock_finance_push,
    _mock_disbursement_push,
    client,
    db,
    admin_user,
):
    """Walk the complete staffing lifecycle through live HTTP calls."""
    mock_selfie.return_value = None
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # ── Step 1: Admin authenticates ────────────────────────────────────────
    r = client.post(f"{BASE}/auth/admin/login", json={
        "email": "admin@annai-illam.test",
        "password": "AdminPass123!",
    })
    admin_data = _ok(r, "admin login")
    admin_headers = {"Authorization": f"Bearer {admin_data['access_token']}"}

    # ── Step 2–3: Client authenticates via OTP ─────────────────────────────
    r = client.post(f"{BASE}/auth/client/request-otp", json={"phone": "9100000001"})
    otp_data = _ok(r, "client request-otp")
    client_otp = otp_data["otp"]

    r = client.post(f"{BASE}/auth/client/verify-otp", json={
        "phone": "9100000001",
        "code": client_otp,
    })
    client_auth = _ok(r, "client verify-otp")
    client_headers = {"Authorization": f"Bearer {client_auth['access_token']}"}

    # ── Step 4: Client creates profile ─────────────────────────────────────
    r = client.post(f"{BASE}/client/profile", json={
        "client_type": "company",
        "company_name": "E2E Test Corp",
        "contact_name": "E2E Contact",
        "city": "Chennai",
        "state": "Tamil Nadu",
    }, headers=client_headers)
    _ok(r, "client create profile")

    # ── Step 5–6: Worker authenticates via OTP ─────────────────────────────
    r = client.post(f"{BASE}/auth/worker/request-otp", json={"phone": "9200000001"})
    otp_data = _ok(r, "worker request-otp")
    worker_otp = otp_data["otp"]

    r = client.post(f"{BASE}/auth/worker/verify-otp", json={
        "phone": "9200000001",
        "code": worker_otp,
    })
    worker_auth = _ok(r, "worker verify-otp")
    worker_headers = {"Authorization": f"Bearer {worker_auth['access_token']}"}
    worker_user_id = worker_auth["user"]["id"]

    # ── Step 7: Worker submits identity documents ──────────────────────────
    r = client.post(f"{BASE}/worker/onboarding/identity", json={
        "govt_id_key": "local:e2e_govt_id.jpg",
        "selfie_key": "local:e2e_selfie.jpg",
    }, headers=worker_headers)
    _ok(r, "worker submit identity")

    # ── Step 8: Worker submits profile ─────────────────────────────────────
    r = client.post(f"{BASE}/worker/onboarding/profile", json={
        "full_name": "E2E Worker",
        "skills": ["cleaning"],
        "experience_years": "1\u20132 years",
        "available_days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        "available_shifts": ["morning", "afternoon", "evening", "night"],
        "city": "Chennai",
        "state": "Tamil Nadu",
        "payment": {"upi_id": "e2eworker@upi"},
    }, headers=worker_headers)
    worker_profile_data = _ok(r, "worker submit profile")
    worker_profile_id = worker_profile_data["profile_id"]

    # ── Step 9: Admin approves worker ──────────────────────────────────────
    r = client.post(
        f"{BASE}/admin/people/workers/{worker_user_id}/approve",
        headers=admin_headers,
    )
    _ok(r, "admin approve worker")

    # ── Step 10: Client creates requirement ────────────────────────────────
    r = client.post(f"{BASE}/client/requirements", json={
        "category": "cleaning",
        "number_of_workers": 1,
        "work_location": "123 Test Street",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "start_date": str(today),
        "duration_days": 1,
    }, headers=client_headers)
    req_data = _ok(r, "client create requirement")
    req_id = req_data["id"]

    # ── Step 11: Admin marks requirement under review ──────────────────────
    r = client.post(
        f"{BASE}/admin/requirements/{req_id}/mark-review",
        headers=admin_headers,
    )
    _ok(r, "admin mark-review")

    # ── Step 12: Admin creates quote ───────────────────────────────────────
    r = client.post(f"{BASE}/admin/requirements/{req_id}/quote", json={
        "requirement_id": req_id,
        "quoted_amount": 500000,
        "payment_model": "client_pays_company",
        "advance_amount": 250000,
    }, headers=admin_headers)
    _ok(r, "admin create quote")

    # ── Step 13: Client approves quote ─────────────────────────────────────
    r = client.post(
        f"{BASE}/client/requirements/{req_id}/quote-decision",
        json={"action": "approve"},
        headers=client_headers,
    )
    _ok(r, "client approve quote")

    # ── Step 14: Admin records manual payment (already PAID) ───────────────
    r = client.post(f"{BASE}/admin/finance/client-payments/manual", json={
        "requirement_id": req_id,
        "amount": 250000,
        "payment_model": "client_pays_company",
        "payment_mode": "bank_transfer",
        "payment_status": "paid",
        "reference_note": "E2E-ADVANCE-001",
    }, headers=admin_headers)
    _ok(r, "admin record manual payment")

    # ── Step 15: Admin assigns worker ──────────────────────────────────────
    r = client.post(f"{BASE}/admin/assignments", json={
        "requirement_id": req_id,
        "worker_profile_id": worker_profile_id,
        "salary_amount": 30000,
        "start_date": str(today),
        "end_date": str(today),
    }, headers=admin_headers)
    assign_data = _ok(r, "admin assign worker")
    assignment_id = assign_data["assignment_id"]

    # ── Step 16: Worker lists assignments ──────────────────────────────────
    r = client.get(f"{BASE}/worker/assignments", headers=worker_headers)
    list_data = _ok(r, "worker list assignments")
    assert any(a["assignment_id"] == assignment_id for a in list_data), (
        f"Assignment {assignment_id} not found in worker assignments list"
    )

    # ── Step 17: Worker acknowledges assignment ─────────────────────────────
    r = client.post(
        f"{BASE}/worker/assignments/{assignment_id}/acknowledge",
        headers=worker_headers,
    )
    _ok(r, "worker acknowledge assignment")

    # ── Step 18: Worker checks in ──────────────────────────────────────────
    r = client.post(f"{BASE}/worker/attendance/check-in", json={
        "assignment_id": assignment_id,
    }, headers=worker_headers)
    checkin_data = _ok(r, "worker check-in")
    attendance_id = checkin_data["attendance_id"]

    # ── Step 19: Worker checks out ─────────────────────────────────────────
    r = client.post(f"{BASE}/worker/attendance/check-out", json={
        "assignment_id": assignment_id,
    }, headers=worker_headers)
    _ok(r, "worker check-out")

    # ── Step 20: Admin approves attendance ─────────────────────────────────
    r = client.post(
        f"{BASE}/admin/attendance/{attendance_id}/approve",
        headers=admin_headers,
    )
    _ok(r, "admin approve attendance")

    # ── Step 21: Admin marks assignment completed ───────────────────────────
    r = client.patch(
        f"{BASE}/admin/assignments/{assignment_id}/status",
        json={"status": "completed"},
        headers=admin_headers,
    )
    _ok(r, "admin complete assignment")

    # ── Step 22: Admin completes requirement ───────────────────────────────
    r = client.post(
        f"{BASE}/admin/requirements/{req_id}/complete",
        headers=admin_headers,
    )
    _ok(r, "admin complete requirement")

    # ── Step 23: Admin creates payroll run ─────────────────────────────────
    r = client.post(f"{BASE}/admin/payroll/runs", json={
        "period_start": str(today),
        "period_end": str(today),
        "require_verified_attendance": False,
    }, headers=admin_headers)
    payroll_data = _ok(r, "admin create payroll run")
    payroll_run_id = payroll_data["payroll_run_id"]

    # ── Step 24: Admin generates payroll ───────────────────────────────────
    r = client.post(
        f"{BASE}/admin/payroll/runs/{payroll_run_id}/generate",
        headers=admin_headers,
    )
    _ok(r, "admin generate payroll")

    # ── Step 25: Admin creates disbursement ────────────────────────────────
    r = client.post(f"{BASE}/admin/disbursements", json={
        "assignment_id": assignment_id,
        "amount": 30000,
        "scheduled_date": str(tomorrow),
    }, headers=admin_headers)
    disburse_data = _ok(r, "admin create disbursement")
    disbursement_id = disburse_data["id"]

    # ── Step 26: Admin marks disbursement paid ─────────────────────────────
    r = client.patch(
        f"{BASE}/admin/disbursements/{disbursement_id}/paid",
        json={"payment_reference": "E2E-PAY-REF-001"},
        headers=admin_headers,
    )
    _ok(r, "admin mark disbursement paid")

    # ── Step 27: Client rates the completed requirement ────────────────────
    r = client.post(f"{BASE}/client/ratings", json={
        "requirement_id": req_id,
        "assignment_id": assignment_id,
        "worker_profile_id": worker_profile_id,
        "rating": 5,
        "comments": "Excellent work — E2E smoke test",
    }, headers=client_headers)
    rating_data = _ok(r, "client submit rating")
    assert rating_data["rating"] == 5
