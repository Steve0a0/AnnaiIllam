"""Integration coverage for admin payroll generation and lock enforcement."""
from datetime import date, datetime, time, timedelta
from unittest.mock import patch

import pytest

from app.core.assignment_constants import AssignmentStatus
from app.core.attendance_constants import AttendanceStatus
from app.core.payroll_constants import DeductionType, PayrollRunStatus
from app.core.statuses import RequirementStatus
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.client_profile import ClientProfile
from app.models.payroll_run import PayrollRun
from app.models.quote import Quote
from app.models.requirement import Requirement
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair

BASE = "/api/v1"
PERIOD_START = date(2026, 5, 1)
PERIOD_END = date(2026, 5, 31)


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
def assigned_requirement(db, client_profile, client_user):
    requirement = Requirement(
        client_id=client_profile.id,
        category="Security",
        subcategory="Night Guard",
        number_of_workers=1,
        work_location="Warehouse Gate 1",
        city="Chennai",
        state="Tamil Nadu",
        start_date=PERIOD_START,
        duration_days=31,
        shift_details="Night 20:00-06:00",
        food_required=True,
        accommodation_required=False,
        budget_amount=30000,
        notes="Report to the security supervisor.",
        status=RequirementStatus.WORKERS_ASSIGNED.value,
        created_by_user_id=client_user.id,
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


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
        skills="Security,Night Guard",
        available_shifts="Night",
        is_available=True,
        verification_status="approved",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def assignment(db, assigned_requirement, worker_profile, admin_user):
    item = Assignment(
        requirement_id=assigned_requirement.id,
        worker_profile_id=worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.ACCEPTED.value,
        assigned_role="Night Security Guard",
        assigned_shift="Night 20:00-06:00",
        salary_amount=1000,  # daily rate
        notes="Daily salary for payroll tests.",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def cancelled_assignment(db, assigned_requirement, worker_profile, admin_user):
    item = Assignment(
        requirement_id=assigned_requirement.id,
        worker_profile_id=worker_profile.id,
        assigned_by_user_id=admin_user.id,
        status=AssignmentStatus.CANCELLED.value,
        assigned_role="Backup Guard",
        assigned_shift="Night 20:00-06:00",
        salary_amount=1000,  # daily rate
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def attendance_records(db, assignment, worker_profile, worker_user):
    rows = [
        attendance_row(
            assignment.id,
            worker_profile.id,
            worker_user.id,
            PERIOD_START,
            AttendanceStatus.PRESENT.value,
        ),
        attendance_row(
            assignment.id,
            worker_profile.id,
            worker_user.id,
            PERIOD_START + timedelta(days=1),
            AttendanceStatus.APPROVED.value,
        ),
        attendance_row(
            assignment.id,
            worker_profile.id,
            worker_user.id,
            PERIOD_START + timedelta(days=2),
            AttendanceStatus.HALF_DAY.value,
        ),
        attendance_row(
            assignment.id,
            worker_profile.id,
            worker_user.id,
            PERIOD_START + timedelta(days=3),
            AttendanceStatus.ABSENT.value,
        ),
    ]
    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


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


def attendance_row(
    assignment_id: int,
    worker_profile_id: int,
    marked_by_user_id: int,
    attendance_date: date,
    status: str,
) -> Attendance:
    checked_in_at = datetime.combine(attendance_date, time(hour=9))
    return Attendance(
        assignment_id=assignment_id,
        worker_profile_id=worker_profile_id,
        attendance_date=attendance_date,
        status=status,
        check_in_time=checked_in_at,
        check_out_time=checked_in_at + timedelta(hours=8),
        check_in_latitude=13.0827,
        check_in_longitude=80.2707,
        check_out_latitude=13.0828,
        check_out_longitude=80.2708,
        marked_by_user_id=marked_by_user_id,
    )


def payroll_run_payload(**overrides):
    payload = {
        "period_start": PERIOD_START.isoformat(),
        "period_end": PERIOD_END.isoformat(),
        "notes": "May payroll cycle.",
    }
    payload.update(overrides)
    return payload


def create_payroll_run_draft(client, admin_headers):
    """Step 1: create a DRAFT run (no items yet)."""
    response = client.post(
        f"{BASE}/admin/payroll/runs",
        json=payroll_run_payload(),
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == PayrollRunStatus.DRAFT.value
    return data["payroll_run_id"]


def generate_payroll_run(client, admin_headers):
    """Steps 1+2: create a DRAFT run then generate its items."""
    payroll_run_id = create_payroll_run_draft(client, admin_headers)
    gen = client.post(
        f"{BASE}/admin/payroll/runs/{payroll_run_id}/generate",
        headers=admin_headers,
    )
    assert gen.status_code == 200
    return payroll_run_id


def get_first_payroll_item(client, payroll_run_id: int, admin_headers):
    response = client.get(
        f"{BASE}/admin/payroll/runs/{payroll_run_id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 1
    return items[0]


class TestAdminPayrollGeneration:
    def test_create_run_returns_draft_and_generate_produces_items(
        self,
        client,
        admin_headers,
        attendance_records,
        assignment,
        cancelled_assignment,
    ):
        # Step 1 — create a draft run (no items yet)
        payroll_run_id = create_payroll_run_draft(client, admin_headers)

        draft_detail = client.get(
            f"{BASE}/admin/payroll/runs/{payroll_run_id}",
            headers=admin_headers,
        )
        assert draft_detail.json()["data"]["payroll_run"]["status"] == PayrollRunStatus.DRAFT.value
        assert draft_detail.json()["data"]["items"] == []

        # Step 2 — generate items
        gen = client.post(
            f"{BASE}/admin/payroll/runs/{payroll_run_id}/generate",
            headers=admin_headers,
        )
        assert gen.status_code == 200
        gen_data = gen.json()["data"]
        assert gen_data["status"] == PayrollRunStatus.GENERATED.value
        assert gen_data["items_created"] == 1

        detail = client.get(
            f"{BASE}/admin/payroll/runs/{payroll_run_id}",
            headers=admin_headers,
        )
        run_data = detail.json()["data"]
        assert run_data["payroll_run"]["status"] == PayrollRunStatus.GENERATED.value
        assert run_data["payroll_run"]["period_start"] == PERIOD_START.isoformat()

        items = run_data["items"]
        assert len(items) == 1
        item = items[0]
        assert item["assignment_id"] == assignment.id
        assert item["assignment_id"] != cancelled_assignment.id
        assert item["attendance_days"] == 2
        assert item["half_days"] == 1
        assert item["absent_days"] == 1
        assert item["gross_amount"] == 2500
        assert item["total_deduction_amount"] == 0
        assert item["net_amount"] == 2500

    def test_payroll_generation_works_with_zero_attendance(self, client, admin_headers, assignment):
        payroll_run_id = generate_payroll_run(client, admin_headers)

        item = get_first_payroll_item(client, payroll_run_id, admin_headers)
        assert item["assignment_id"] == assignment.id
        assert item["attendance_days"] == 0
        assert item["half_days"] == 0
        assert item["absent_days"] == 0
        assert item["gross_amount"] == 0
        assert item["net_amount"] == 0

    def test_duplicate_generation_for_same_run_is_rejected(
        self,
        client,
        admin_headers,
        attendance_records,
    ):
        payroll_run_id = generate_payroll_run(client, admin_headers)

        response = client.post(
            f"{BASE}/admin/payroll/runs/{payroll_run_id}/generate",
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "already generated" in response.json()["message"].lower()

    def test_payroll_routes_require_admin_role(
        self,
        client,
        client_headers,
        attendance_records,
    ):
        response = client.post(
            f"{BASE}/admin/payroll/runs",
            json=payroll_run_payload(),
            headers=client_headers,
        )
        assert response.status_code == 403


class TestAdminPayrollDeductions:
    def test_admin_can_add_deduction_and_recalculate_net_amount(
        self,
        client,
        admin_headers,
        attendance_records,
    ):
        payroll_run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, payroll_run_id, admin_headers)

        response = client.post(
            f"{BASE}/admin/payroll/deductions",
            json={
                "payroll_item_id": item["id"],
                "deduction_type": DeductionType.FOOD.value,
                "amount": 300,
                "reason": "Food deduction.",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["payroll_item_id"] == item["id"]
        assert data["total_deduction_amount"] == 300
        assert data["net_amount"] == 2200
        assert data["warning"] is None  # deduction < gross — no warning

        updated = get_first_payroll_item(client, payroll_run_id, admin_headers)
        assert updated["deductions"][0]["deduction_type"] == DeductionType.FOOD.value
        assert updated["deductions"][0]["amount"] == 300
        assert updated["total_deduction_amount"] == 300
        assert updated["net_amount"] == 2200

    def test_deductions_do_not_make_net_amount_negative(
        self,
        client,
        admin_headers,
        attendance_records,
    ):
        payroll_run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, payroll_run_id, admin_headers)

        response = client.post(
            f"{BASE}/admin/payroll/deductions",
            json={
                "payroll_item_id": item["id"],
                "deduction_type": DeductionType.MANUAL.value,
                "amount": 3000,
                "reason": "Manual adjustment.",
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["total_deduction_amount"] == 3000
        assert response.json()["data"]["net_amount"] == 0
        # deduction 3000 > gross 2500 → warning must be present
        warning = response.json()["data"]["warning"]
        assert warning is not None
        assert warning["code"] == "deductions_exceed_gross"
        assert "0" in warning["message"] or "exceed" in warning["message"].lower()

    def test_deduction_equal_to_gross_sets_net_to_zero_without_warning(
        self,
        client,
        admin_headers,
        attendance_records,
    ):
        """Exact match: total_deductions == gross_amount → net 0, no warning."""
        payroll_run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, payroll_run_id, admin_headers)
        gross = item["gross_amount"]  # 2500

        response = client.post(
            f"{BASE}/admin/payroll/deductions",
            json={
                "payroll_item_id": item["id"],
                "deduction_type": DeductionType.MANUAL.value,
                "amount": gross,
            },
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["net_amount"] == 0
        assert data["warning"] is None  # equal, not exceeding — no warning

    def test_multiple_deductions_cumulatively_exceeding_gross_triggers_warning(
        self,
        client,
        admin_headers,
        attendance_records,
    ):
        """Warning fires when the running total crosses gross, not just on a single large deduction."""
        payroll_run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, payroll_run_id, admin_headers)
        # gross = 2500; add two deductions: 1500 + 1500 = 3000 > 2500

        resp1 = client.post(
            f"{BASE}/admin/payroll/deductions",
            json={"payroll_item_id": item["id"], "deduction_type": DeductionType.FOOD.value, "amount": 1500},
            headers=admin_headers,
        )
        assert resp1.status_code == 200
        assert resp1.json()["data"]["warning"] is None  # 1500 < 2500 — no warning yet

        resp2 = client.post(
            f"{BASE}/admin/payroll/deductions",
            json={"payroll_item_id": item["id"], "deduction_type": DeductionType.ADVANCE.value, "amount": 1500},
            headers=admin_headers,
        )
        assert resp2.status_code == 200
        data2 = resp2.json()["data"]
        assert data2["net_amount"] == 0  # clamped
        assert data2["warning"] is not None  # cumulative 3000 > 2500
        assert data2["warning"]["code"] == "deductions_exceed_gross"

    def test_invalid_deduction_type_is_rejected(
        self,
        client,
        admin_headers,
        attendance_records,
    ):
        payroll_run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, payroll_run_id, admin_headers)

        response = client.post(
            f"{BASE}/admin/payroll/deductions",
            json={
                "payroll_item_id": item["id"],
                "deduction_type": "unknown",
                "amount": 100,
                "reason": "Invalid type.",
            },
            headers=admin_headers,
        )
        assert response.status_code == 422


class TestAdminPayrollStatusAndLocks:
    @pytest.mark.parametrize(
        "status",
        [
            PayrollRunStatus.DRAFT.value,
            PayrollRunStatus.GENERATED.value,
            PayrollRunStatus.APPROVED.value,
            PayrollRunStatus.PAID.value,
            PayrollRunStatus.LOCKED.value,
        ],
    )
    def test_admin_can_set_each_supported_payroll_status(
        self,
        client,
        admin_headers,
        attendance_records,
        status,
    ):
        payroll_run_id = generate_payroll_run(client, admin_headers)

        response = client.patch(
            f"{BASE}/admin/payroll/runs/{payroll_run_id}/status",
            json={"status": status},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == status

    def test_admin_can_mark_generated_run_paid(self, client, admin_headers, attendance_records):
        payroll_run_id = generate_payroll_run(client, admin_headers)

        response = client.patch(
            f"{BASE}/admin/payroll/runs/{payroll_run_id}/status",
            json={"status": PayrollRunStatus.PAID.value},
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == PayrollRunStatus.PAID.value

        detail = client.get(
            f"{BASE}/admin/payroll/runs/{payroll_run_id}",
            headers=admin_headers,
        )
        assert detail.json()["data"]["payroll_run"]["status"] == PayrollRunStatus.PAID.value

    def test_locked_payroll_run_blocks_deductions_and_status_changes(
        self,
        client,
        admin_headers,
        attendance_records,
    ):
        payroll_run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, payroll_run_id, admin_headers)

        lock_response = client.patch(
            f"{BASE}/admin/payroll/runs/{payroll_run_id}/status",
            json={"status": PayrollRunStatus.LOCKED.value},
            headers=admin_headers,
        )
        assert lock_response.status_code == 200

        deduction = client.post(
            f"{BASE}/admin/payroll/deductions",
            json={
                "payroll_item_id": item["id"],
                "deduction_type": DeductionType.ADVANCE.value,
                "amount": 100,
                "reason": "Should be blocked.",
            },
            headers=admin_headers,
        )
        assert deduction.status_code == 400
        assert "locked" in deduction.json()["message"].lower()

        status_change = client.patch(
            f"{BASE}/admin/payroll/runs/{payroll_run_id}/status",
            json={"status": PayrollRunStatus.PAID.value},
            headers=admin_headers,
        )
        assert status_change.status_code == 400
        assert "locked" in status_change.json()["message"].lower()

    def test_locked_payroll_run_blocks_generation(
        self,
        client,
        db,
        admin_headers,
        admin_user,
        attendance_records,
    ):
        payroll_run = PayrollRun(
            period_start=PERIOD_START,
            period_end=PERIOD_END,
            status=PayrollRunStatus.LOCKED.value,
            notes="Locked draft run.",
            created_by_user_id=admin_user.id,
        )
        db.add(payroll_run)
        db.commit()
        db.refresh(payroll_run)

        response = client.post(
            f"{BASE}/admin/payroll/runs/{payroll_run.id}/generate",
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "locked" in response.json()["message"].lower()


class TestPlatformMarginCalculation:
    """Unit and integration tests for platform_margin = (client_rate - worker_rate) × payable_days."""

    # ── Unit tests for the helper function ───────────────────────────────────

    def test_unit_positive_margin(self):
        from app.services.payroll_service import calculate_platform_margin
        # (1200 - 1000) × (2 + 0.5) = 200 × 2.5 = 500
        assert calculate_platform_margin(1200, 1000, 2, 1) == 500

    def test_unit_zero_margin_when_rates_equal(self):
        from app.services.payroll_service import calculate_platform_margin
        assert calculate_platform_margin(1000, 1000, 2, 1) == 0

    def test_unit_negative_margin_when_worker_rate_exceeds_client(self):
        from app.services.payroll_service import calculate_platform_margin
        # (800 - 1000) × 2.5 = -500
        assert calculate_platform_margin(800, 1000, 2, 1) == -500

    def test_unit_returns_none_when_client_rate_missing(self):
        from app.services.payroll_service import calculate_platform_margin
        assert calculate_platform_margin(None, 1000, 2, 1) is None

    def test_unit_returns_none_when_worker_rate_missing(self):
        from app.services.payroll_service import calculate_platform_margin
        assert calculate_platform_margin(1200, None, 2, 1) is None

    def test_unit_zero_days_yields_zero_margin(self):
        from app.services.payroll_service import calculate_platform_margin
        assert calculate_platform_margin(1200, 1000, 0, 0) == 0

    # ── Integration tests via generate endpoint ───────────────────────────────

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_generate_stores_positive_margin_when_client_rate_exceeds_worker(
        self,
        _mock_rl,
        client,
        db,
        admin_headers,
        attendance_records,
        assigned_requirement,
        admin_user,
    ):
        """client_rate=1200, worker_salary=1000, 2.5 payable days → margin=500."""
        quote = Quote(
            requirement_id=assigned_requirement.id,
            quoted_amount=50000,
            rate_per_worker=1200,
            payment_model="client_pays_company",
            created_by_user_id=admin_user.id,
        )
        db.add(quote)
        db.commit()

        payroll_run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, payroll_run_id, admin_headers)

        assert item["platform_margin"] == 500  # (1200 - 1000) × 2.5

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_generate_stores_negative_margin_when_worker_rate_exceeds_client(
        self,
        _mock_rl,
        client,
        db,
        admin_headers,
        attendance_records,
        assigned_requirement,
        admin_user,
    ):
        """client_rate=800, worker_salary=1000 → negative margin."""
        quote = Quote(
            requirement_id=assigned_requirement.id,
            quoted_amount=30000,
            rate_per_worker=800,
            payment_model="client_pays_company",
            created_by_user_id=admin_user.id,
        )
        db.add(quote)
        db.commit()

        payroll_run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, payroll_run_id, admin_headers)

        assert item["platform_margin"] == -500  # (800 - 1000) × 2.5

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_generate_stores_zero_margin_when_rates_equal(
        self,
        _mock_rl,
        client,
        db,
        admin_headers,
        attendance_records,
        assigned_requirement,
        admin_user,
    ):
        quote = Quote(
            requirement_id=assigned_requirement.id,
            quoted_amount=40000,
            rate_per_worker=1000,  # same as assignment.salary_amount
            payment_model="client_pays_company",
            created_by_user_id=admin_user.id,
        )
        db.add(quote)
        db.commit()

        payroll_run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, payroll_run_id, admin_headers)

        assert item["platform_margin"] == 0

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_generate_stores_null_margin_when_no_quote_exists(
        self,
        _mock_rl,
        client,
        admin_headers,
        attendance_records,
    ):
        """No quote for the requirement → platform_margin is null."""
        payroll_run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, payroll_run_id, admin_headers)

        assert item["platform_margin"] is None

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_generate_stores_null_margin_when_quote_has_no_rate_per_worker(
        self,
        _mock_rl,
        client,
        db,
        admin_headers,
        attendance_records,
        assigned_requirement,
        admin_user,
    ):
        """Quote exists but rate_per_worker is None → platform_margin is null."""
        quote = Quote(
            requirement_id=assigned_requirement.id,
            quoted_amount=40000,
            rate_per_worker=None,
            payment_model="client_pays_company",
            created_by_user_id=admin_user.id,
        )
        db.add(quote)
        db.commit()

        payroll_run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, payroll_run_id, admin_headers)

        assert item["platform_margin"] is None


# ──────────────────────────────────────────────────────────────────
# P2-10 — Strict mode: require_verified_attendance
# ──────────────────────────────────────────────────────────────────


class TestPayrollStrictMode:
    """require_verified_attendance=true counts only approved/corrected records."""

    def _make_attendance(self, db, assignment, worker_profile, worker_user, statuses: list):
        rows = []
        for offset, status in enumerate(statuses):
            rows.append(
                attendance_row(
                    assignment.id,
                    worker_profile.id,
                    worker_user.id,
                    PERIOD_START + timedelta(days=offset),
                    status,
                )
            )
        db.add_all(rows)
        db.commit()
        return rows

    def _create_strict_run(self, client, admin_headers):
        resp = client.post(
            f"{BASE}/admin/payroll/runs",
            json=payroll_run_payload(require_verified_attendance=True),
            headers=admin_headers,
        )
        assert resp.status_code == 200
        run_id = resp.json()["data"]["payroll_run_id"]
        gen = client.post(
            f"{BASE}/admin/payroll/runs/{run_id}/generate",
            headers=admin_headers,
        )
        assert gen.status_code == 200
        return run_id

    # ── unit tests ───────────────────────────────────────────────────

    def test_unit_strict_false_counts_present_and_late(self):
        from app.services.payroll_service import calculate_attendance_summary

        class R:
            def __init__(self, s): self.status = s

        records = [R("present"), R("late"), R("approved"), R("corrected"), R("absent")]
        result = calculate_attendance_summary(records, strict_mode=False)
        assert result["attendance_days"] == 4
        assert result["absent_days"] == 1

    def test_unit_strict_true_excludes_present_and_late(self):
        from app.services.payroll_service import calculate_attendance_summary

        class R:
            def __init__(self, s): self.status = s

        records = [R("present"), R("late"), R("approved"), R("corrected"), R("absent")]
        result = calculate_attendance_summary(records, strict_mode=True)
        assert result["attendance_days"] == 2   # only approved + corrected
        assert result["absent_days"] == 1

    # ── integration tests ─────────────────────────────────────────────

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_lax_mode_counts_present_late_approved_corrected(
        self, _mock_rl, client, admin_headers, assignment, worker_profile, worker_user, db
    ):
        self._make_attendance(db, assignment, worker_profile, worker_user, [
            AttendanceStatus.PRESENT.value,
            AttendanceStatus.LATE.value,
            AttendanceStatus.APPROVED.value,
            AttendanceStatus.CORRECTED.value,
        ])
        run_id = generate_payroll_run(client, admin_headers)
        item = get_first_payroll_item(client, run_id, admin_headers)
        assert item["attendance_days"] == 4
        assert item["gross_amount"] == 4000

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_strict_mode_counts_only_approved_and_corrected(
        self, _mock_rl, client, admin_headers, assignment, worker_profile, worker_user, db
    ):
        self._make_attendance(db, assignment, worker_profile, worker_user, [
            AttendanceStatus.PRESENT.value,    # excluded
            AttendanceStatus.LATE.value,       # excluded
            AttendanceStatus.APPROVED.value,   # counted
            AttendanceStatus.CORRECTED.value,  # counted
        ])
        run_id = self._create_strict_run(client, admin_headers)
        item = get_first_payroll_item(client, run_id, admin_headers)
        assert item["attendance_days"] == 2
        assert item["gross_amount"] == 2000

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_strict_mode_with_only_approved(
        self, _mock_rl, client, admin_headers, assignment, worker_profile, worker_user, db
    ):
        self._make_attendance(db, assignment, worker_profile, worker_user, [
            AttendanceStatus.APPROVED.value,
            AttendanceStatus.APPROVED.value,
        ])
        run_id = self._create_strict_run(client, admin_headers)
        item = get_first_payroll_item(client, run_id, admin_headers)
        assert item["attendance_days"] == 2

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_strict_mode_with_only_corrected(
        self, _mock_rl, client, admin_headers, assignment, worker_profile, worker_user, db
    ):
        self._make_attendance(db, assignment, worker_profile, worker_user, [
            AttendanceStatus.CORRECTED.value,
        ])
        run_id = self._create_strict_run(client, admin_headers)
        item = get_first_payroll_item(client, run_id, admin_headers)
        assert item["attendance_days"] == 1
        assert item["gross_amount"] == 1000

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_strict_mode_all_unverified_yields_zero_gross(
        self, _mock_rl, client, admin_headers, assignment, worker_profile, worker_user, db
    ):
        """All present/late in strict mode → gross=0, no crash."""
        self._make_attendance(db, assignment, worker_profile, worker_user, [
            AttendanceStatus.PRESENT.value,
            AttendanceStatus.LATE.value,
        ])
        run_id = self._create_strict_run(client, admin_headers)
        item = get_first_payroll_item(client, run_id, admin_headers)
        assert item["attendance_days"] == 0
        assert item["gross_amount"] == 0
        assert item["net_amount"] == 0

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_strict_mode_persisted_in_run_detail(self, _mock_rl, client, admin_headers):
        resp = client.post(
            f"{BASE}/admin/payroll/runs",
            json=payroll_run_payload(require_verified_attendance=True),
            headers=admin_headers,
        )
        run_id = resp.json()["data"]["payroll_run_id"]
        detail = client.get(f"{BASE}/admin/payroll/runs/{run_id}", headers=admin_headers)
        assert detail.status_code == 200
        assert detail.json()["data"]["payroll_run"]["require_verified_attendance"] is True

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_default_run_has_strict_mode_false(self, _mock_rl, client, admin_headers):
        resp = client.post(
            f"{BASE}/admin/payroll/runs",
            json=payroll_run_payload(),
            headers=admin_headers,
        )
        run_id = resp.json()["data"]["payroll_run_id"]
        detail = client.get(f"{BASE}/admin/payroll/runs/{run_id}", headers=admin_headers)
        assert detail.json()["data"]["payroll_run"]["require_verified_attendance"] is False

    @patch("app.api.admin_payroll.check_rate_limit")
    def test_list_runs_includes_strict_mode_field(self, _mock_rl, client, admin_headers):
        client.post(
            f"{BASE}/admin/payroll/runs",
            json=payroll_run_payload(require_verified_attendance=True),
            headers=admin_headers,
        )
        resp = client.get(f"{BASE}/admin/payroll/runs", headers=admin_headers)
        assert resp.status_code == 200
        runs = resp.json()["data"]
        assert len(runs) >= 1
        assert "require_verified_attendance" in runs[0]
        assert runs[0]["require_verified_attendance"] is True
