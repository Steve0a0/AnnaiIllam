from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.assignment_constants import AssignmentStatus
from app.models.assignment import Assignment
from app.models.requirement import Requirement
from app.models.worker_availability import WorkerAvailability
from app.models.worker_document import WorkerDocument
from app.models.worker_interest import WorkerInterest
from app.repositories.assignment_repository import get_active_assignments_by_worker_profile_id
from app.repositories.profile_repository import get_all_worker_profiles
from app.repositories.requirement_repository import get_requirement_by_id
from app.repositories.worker_availability_repository import get_worker_availability

ASSIGNABLE_VERIFICATION_STATUSES = {"approved", "verified"}
_ACTIVE_STATUSES = [
    AssignmentStatus.ASSIGNED.value,
    AssignmentStatus.ACCEPTED.value,
    AssignmentStatus.ACTIVE.value,
]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _csv_set(value: list[str] | str | None) -> set[str]:
    if not value:
        return set()
    if isinstance(value, list):
        return {item.strip().lower() for item in value if item.strip()}
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
    if available_days and requirement.start_date is not None:
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
    # Without dates we cannot compute overlap — return no conflict rather than crashing.
    if requirement.start_date is None or requirement.duration_days is None:
        return None
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


def get_expired_documents(db: Session, worker_profile_id: int) -> list[dict]:
    """Returns non-rejected documents whose expiry_date is strictly before today."""
    today = date.today()
    rows = db.execute(
        select(WorkerDocument).where(
            WorkerDocument.worker_profile_id == worker_profile_id,
            WorkerDocument.expiry_date.is_not(None),
            WorkerDocument.expiry_date < today,
            WorkerDocument.verification_status != "rejected",
        )
    ).scalars().all()
    return [
        {"document_type": doc.document_type, "expiry_date": str(doc.expiry_date)}
        for doc in rows
    ]


def _get_interest_map(db: Session, requirement_id: int) -> dict[int, str]:
    """Returns {worker_profile_id: status} for all interest records on this requirement."""
    rows = db.execute(
        select(WorkerInterest).where(WorkerInterest.requirement_id == requirement_id)
    ).scalars().all()
    return {row.worker_profile_id: row.status for row in rows}


def score_worker_for_requirement(
    worker,
    requirement,
    interest_map: dict[int, str] | None = None,
    *,
    # Pre-loaded data supplied by get_worker_matches to avoid N+1 queries.
    # When None the values are treated as empty (no records found).
    availability_records: list | None = None,
    conflict: dict | None = None,
    expired_documents: list[dict] | None = None,
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
    elif worker.skills and any(requirement.category.lower() in s.lower() for s in worker.skills):
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

    if requirement.start_date is not None and requirement.duration_days is not None:
        unavailable_days = [
            record
            for record in (availability_records or [])
            if record.status in {"unavailable", "leave"}
        ]
        if unavailable_days:
            score -= 35
            reasons.append("calendar unavailable")

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

    expired_docs = expired_documents if expired_documents is not None else []
    if expired_docs:
        reasons.append("document_expired")

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
        "expired_documents": expired_docs,
    }


def get_worker_matches(db: Session, requirement) -> list[dict]:
    """Return all workers scored for the given requirement.

    Uses 7 batched queries total regardless of worker count, replacing the
    previous O(N) pattern that fired ~4 queries per worker.
    """
    from app.models.client_worker_blacklist import ClientWorkerBlacklist

    # 1. Blacklist — exclude workers banned by this client.
    blacklisted_ids: set[int] = {
        row[0]
        for row in db.execute(
            select(ClientWorkerBlacklist.worker_profile_id).where(
                ClientWorkerBlacklist.client_profile_id == requirement.client_id
            )
        ).all()
    }

    # 2. Interest map — boost workers who expressed interest.
    interest_map = _get_interest_map(db, requirement.id)

    # 3. All candidate workers (single query).
    workers = [w for w in get_all_worker_profiles(db) if w.id not in blacklisted_ids]
    if not workers:
        return []
    worker_ids = [w.id for w in workers]

    # 4. Batch-load availability records for the requirement date range (single query).
    availability_map: dict[int, list] = {}
    if requirement.start_date and requirement.duration_days:
        end_date = requirement.start_date + timedelta(days=max(requirement.duration_days, 1) - 1)
        for record in db.execute(
            select(WorkerAvailability).where(
                WorkerAvailability.worker_profile_id.in_(worker_ids),
                WorkerAvailability.availability_date >= requirement.start_date,
                WorkerAvailability.availability_date <= end_date,
            )
        ).scalars().all():
            availability_map.setdefault(record.worker_profile_id, []).append(record)

    # 5. Batch-load active assignments for all workers (single query).
    assignments_by_worker: dict[int, list] = {}
    req_ids_for_conflicts: set[int] = set()
    for assignment in db.execute(
        select(Assignment).where(
            Assignment.worker_profile_id.in_(worker_ids),
            Assignment.status.in_(_ACTIVE_STATUSES),
        )
    ).scalars().all():
        assignments_by_worker.setdefault(assignment.worker_profile_id, []).append(assignment)
        req_ids_for_conflicts.add(assignment.requirement_id)

    # 6. Batch-load requirements for those assignments (single query).
    reqs_for_conflicts: dict[int, Requirement] = {}
    if req_ids_for_conflicts:
        for req in db.execute(
            select(Requirement).where(Requirement.id.in_(req_ids_for_conflicts))
        ).scalars().all():
            reqs_for_conflicts[req.id] = req

    # Pre-compute per-worker conflict (pure Python, no DB).
    conflict_map: dict[int, dict | None] = {}
    if requirement.start_date is not None and requirement.duration_days is not None:
        for worker_id, worker_assignments in assignments_by_worker.items():
            conflict_map[worker_id] = None
            for a in worker_assignments:
                existing_req = reqs_for_conflicts.get(a.requirement_id)
                if not existing_req:
                    continue
                if dates_overlap(
                    requirement.start_date,
                    requirement.duration_days,
                    existing_req.start_date,
                    existing_req.duration_days,
                ):
                    conflict_map[worker_id] = {
                        "assignment_id": a.id,
                        "requirement_id": existing_req.id,
                        "start_date": str(existing_req.start_date),
                        "duration_days": existing_req.duration_days,
                        "status": a.status,
                    }
                    break

    # 7. Batch-load expired documents for all workers (single query).
    docs_map: dict[int, list[dict]] = {}
    today = date.today()
    for doc in db.execute(
        select(WorkerDocument).where(
            WorkerDocument.worker_profile_id.in_(worker_ids),
            WorkerDocument.expiry_date.is_not(None),
            WorkerDocument.expiry_date < today,
            WorkerDocument.verification_status != "rejected",
        )
    ).scalars().all():
        docs_map.setdefault(doc.worker_profile_id, []).append(
            {"document_type": doc.document_type, "expiry_date": str(doc.expiry_date)}
        )

    matches = [
        score_worker_for_requirement(
            worker,
            requirement,
            interest_map,
            availability_records=availability_map.get(worker.id, []),
            conflict=conflict_map.get(worker.id),
            expired_documents=docs_map.get(worker.id, []),
        )
        for worker in workers
    ]
    return sorted(matches, key=lambda item: item["score"], reverse=True)


ASSIGNABLE_VERIFICATION_STATUSES = {"approved", "verified"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _csv_set(value: list[str] | str | None) -> set[str]:
    if not value:
        return set()
    if isinstance(value, list):
        return {item.strip().lower() for item in value if item.strip()}
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
    if available_days and requirement.start_date is not None:
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
    # Without dates we cannot compute overlap — return no conflict rather than crashing.
    if requirement.start_date is None or requirement.duration_days is None:
        return None
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


def get_expired_documents(db: Session, worker_profile_id: int) -> list[dict]:
    """Returns non-rejected documents whose expiry_date is strictly before today."""
    today = date.today()
    rows = db.execute(
        select(WorkerDocument).where(
            WorkerDocument.worker_profile_id == worker_profile_id,
            WorkerDocument.expiry_date.is_not(None),
            WorkerDocument.expiry_date < today,
            WorkerDocument.verification_status != "rejected",
        )
    ).scalars().all()
    return [
        {"document_type": doc.document_type, "expiry_date": str(doc.expiry_date)}
        for doc in rows
    ]
