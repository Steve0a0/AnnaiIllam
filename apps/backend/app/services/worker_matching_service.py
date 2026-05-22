from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.worker_interest import WorkerInterest
from app.repositories.assignment_repository import get_active_assignments_by_worker_profile_id
from app.repositories.profile_repository import get_all_worker_profiles
from app.repositories.requirement_repository import get_requirement_by_id
from app.repositories.worker_availability_repository import get_worker_availability

ASSIGNABLE_VERIFICATION_STATUSES = {"approved", "verified"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _csv_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def _shift_matches(available_shift: str, requirement_shift: str) -> bool:
    """Match broad worker shift preferences against request shift labels."""
    shift = available_shift.strip().lower()
    required = requirement_shift.strip().lower()

    if not shift or not required:
        return True

    if shift in required:
        return True

    if shift in {"full day", "general", "general shift"} and any(
        token in required for token in {"general", "09:00", "9:00"}
    ):
        return True

    if shift == "morning" and any(token in required for token in {"morning", "06:00", "6:00", "09:00", "9:00"}):
        return True

    if shift == "afternoon" and any(token in required for token in {"afternoon", "evening", "14:00", "2:00"}):
        return True

    if shift == "evening" and any(token in required for token in {"evening", "14:00", "2:00"}):
        return True

    if shift == "night" and any(token in required for token in {"night", "22:00", "10:00"}):
        return True

    return False


def get_worker_schedule_mismatch(worker, requirement) -> str | None:
    available_days = _csv_set(worker.available_days)
    if available_days:
        required_day = DAYS[requirement.start_date.weekday()].lower()
        if required_day not in available_days:
            return "not available on requested day"

    available_shifts = _csv_set(worker.available_shifts)
    shift_details = (requirement.shift_details or "").lower()
    if available_shifts and shift_details:
        if not any(_shift_matches(shift, shift_details) for shift in available_shifts):
            return "not available for requested shift"

    return None


def dates_overlap(start_a, duration_a: int, start_b, duration_b: int) -> bool:
    end_a = start_a + timedelta(days=max(duration_a, 1) - 1)
    end_b = start_b + timedelta(days=max(duration_b, 1) - 1)
    return start_a <= end_b and start_b <= end_a


def detect_worker_conflict(db: Session, worker_profile_id: int, requirement) -> dict | None:
    for assignment in get_active_assignments_by_worker_profile_id(db, worker_profile_id):
        existing_requirement = get_requirement_by_id(db, assignment.requirement_id)
        if not existing_requirement:
            continue
        if dates_overlap(
            requirement.start_date,
            requirement.duration_days,
            existing_requirement.start_date,
            existing_requirement.duration_days,
        ):
            return {
                "assignment_id": assignment.id,
                "requirement_id": existing_requirement.id,
                "start_date": str(existing_requirement.start_date),
                "duration_days": existing_requirement.duration_days,
                "status": assignment.status,
            }
    return None


def _get_interest_map(db: Session, requirement_id: int) -> dict[int, str]:
    """Returns {worker_profile_id: status} for all interest records on this requirement."""
    rows = db.execute(
        select(WorkerInterest).where(WorkerInterest.requirement_id == requirement_id)
    ).scalars().all()
    return {row.worker_profile_id: row.status for row in rows}


def score_worker_for_requirement(
    db: Session, worker, requirement, interest_map: dict[int, str] | None = None
) -> dict:
    score = 0
    reasons = []

    if worker.is_available:
        score += 25
        reasons.append("available")
    if worker.verification_status in ASSIGNABLE_VERIFICATION_STATUSES:
        score += 25
        reasons.append("approved")
    if worker.city.lower() == requirement.city.lower():
        score += 20
        reasons.append("same city")
    elif worker.state.lower() == requirement.state.lower():
        score += 10
        reasons.append("same state")
    if worker.category.lower() == requirement.category.lower():
        score += 20
        reasons.append("category match")
    elif requirement.category.lower() in (worker.skills or "").lower():
        score += 10
        reasons.append("skill match")

    schedule_mismatch = get_worker_schedule_mismatch(worker, requirement)
    if schedule_mismatch:
        score -= 40
        reasons.append(schedule_mismatch)
    else:
        if worker.available_days:
            score += 5
            reasons.append("preferred day")
        if worker.available_shifts and requirement.shift_details:
            score += 5
            reasons.append("preferred shift")

    availability_records = get_worker_availability(
        db,
        worker.id,
        start_date=requirement.start_date,
        end_date=requirement.start_date + timedelta(days=max(requirement.duration_days, 1) - 1),
    )
    unavailable_days = [
        record
        for record in availability_records
        if record.status in {"unavailable", "leave"}
    ]
    if unavailable_days:
        score -= 35
        reasons.append("calendar unavailable")

    conflict = detect_worker_conflict(db, worker.id, requirement)
    if conflict:
        score -= 50
        reasons.append("assignment conflict")

    # Interest boost: worker explicitly said they are available for this job
    has_interest = False
    if interest_map is not None:
        interest_status = interest_map.get(worker.id)
        if interest_status == "interested":
            score += 40
            reasons.append("interested")
            has_interest = True

    return {
        "worker_profile_id": worker.id,
        "full_name": worker.full_name,
        "category": worker.category,
        "city": worker.city,
        "state": worker.state,
        "is_available": worker.is_available,
        "verification_status": worker.verification_status,
        "available_days": worker.available_days,
        "available_shifts": worker.available_shifts,
        "score": max(score, 0),
        "reasons": reasons,
        "conflict": conflict,
        "has_interest": has_interest,
    }


def get_worker_matches(db: Session, requirement) -> list[dict]:
    interest_map = _get_interest_map(db, requirement.id)
    matches = [
        score_worker_for_requirement(db, worker, requirement, interest_map)
        for worker in get_all_worker_profiles(db)
    ]
    return sorted(matches, key=lambda item: item["score"], reverse=True)
