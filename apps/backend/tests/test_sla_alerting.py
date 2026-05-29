"""Tests for Polish 5: SLA Alerting on Admin Review.

Covers:
1. Requirement submitted 25 hours ago with sla_hours=24 → scheduler flags it, admin notified
2. Requirement submitted 23 hours ago → not flagged
3. Scheduler runs twice → second run does not re-notify (sla_breach_notified_at already set)
4. Admin marks under review → badge disappears (sla_breach no longer fires)
"""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app.core.scheduler import check_sla_breaches
from app.core.statuses import RequirementStatus
from app.models.client_profile import ClientProfile
from app.models.requirement import Requirement
from app.utils.time import utcnow


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────


def make_submitted_requirement(db, client_user, age_hours: float, sla_hours: int = 24) -> Requirement:
    """Create a submitted requirement whose created_at is backdated by age_hours."""
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="individual",
        contact_name="SLA Test Client",
        city="Chennai",
        state="Tamil Nadu",
        address="Anna Nagar",
    )
    db.add(profile)
    db.flush()

    req = Requirement(
        client_id=profile.id,
        category="Security",
        number_of_workers=1,
        work_location="Gate",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date.today(),
        duration_days=3,
        status=RequirementStatus.SUBMITTED.value,
        created_by_user_id=client_user.id,
        sla_hours=sla_hours,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    # Backdate created_at to simulate an old requirement
    req.created_at = utcnow() - timedelta(hours=age_hours)
    db.commit()
    db.refresh(req)
    return req


# ──────────────────────────────────────────────────────────────────
# Test 1: 25-hour-old requirement with sla_hours=24 → flagged, admin notified
# ──────────────────────────────────────────────────────────────────


@patch("app.core.scheduler.send_push_to_user")
def test_sla_breach_flagged_and_admin_notified(mock_push, db, client_user, admin_user):
    req = make_submitted_requirement(db, client_user, age_hours=25, sla_hours=24)

    result = check_sla_breaches(db)

    assert result["sla_breaches"] >= 1
    db.refresh(req)
    assert req.sla_breach_notified_at is not None

    # Super admin (admin_user has permission_group="super_admin") was notified
    assert mock_push.called
    notified_user_ids = [c.kwargs.get("user_id") for c in mock_push.call_args_list]
    assert admin_user.id in notified_user_ids


# ──────────────────────────────────────────────────────────────────
# Test 2: 23-hour-old requirement → not flagged
# ──────────────────────────────────────────────────────────────────


@patch("app.core.scheduler.send_push_to_user")
def test_within_sla_not_flagged(mock_push, db, client_user):
    req = make_submitted_requirement(db, client_user, age_hours=23, sla_hours=24)

    result = check_sla_breaches(db)

    # This requirement should NOT be flagged
    db.refresh(req)
    assert req.sla_breach_notified_at is None
    # No push about this requirement
    for call in mock_push.call_args_list:
        body = call.kwargs.get("body", "")
        assert str(req.id) not in body


# ──────────────────────────────────────────────────────────────────
# Test 3: Scheduler runs twice → second run does not re-notify
# ──────────────────────────────────────────────────────────────────


@patch("app.core.scheduler.send_push_to_user")
def test_second_run_does_not_re_notify(mock_push, db, client_user, admin_user):
    req = make_submitted_requirement(db, client_user, age_hours=26, sla_hours=24)

    # First run — should flag
    result1 = check_sla_breaches(db)
    assert result1["sla_breaches"] >= 1
    first_call_count = mock_push.call_count

    # Second run — should NOT flag again
    result2 = check_sla_breaches(db)
    assert result2["sla_breaches"] == 0
    # Call count must not have increased
    assert mock_push.call_count == first_call_count


# ──────────────────────────────────────────────────────────────────
# Test 4: Requirement moved to under_review → scheduler ignores it
# ──────────────────────────────────────────────────────────────────


@patch("app.core.scheduler.send_push_to_user")
def test_under_review_requirement_not_flagged(mock_push, db, client_user):
    req = make_submitted_requirement(db, client_user, age_hours=30, sla_hours=24)
    # Admin marks it under_review before scheduler runs
    req.status = RequirementStatus.UNDER_REVIEW.value
    db.commit()

    result = check_sla_breaches(db)

    db.refresh(req)
    assert req.sla_breach_notified_at is None
    for call in mock_push.call_args_list:
        body = call.kwargs.get("body", "")
        assert str(req.id) not in body
