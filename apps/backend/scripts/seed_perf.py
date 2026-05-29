"""seed_perf.py — Populate the database with realistic data for performance testing.

Volumes:
  - 50 client profiles
  - 500 worker profiles
  - 200 requirements (various statuses)
  - 1 000 assignments
  - 5 000 attendance records
  - 100 quotes
  - 50 invoices (linked to quotes)
  - 200 client payments

Usage:
    cd apps/backend
    python -m scripts.seed_perf            # idempotent — skips if data already present
    python -m scripts.seed_perf --wipe     # drop existing perf data first

Prerequisites: DATABASE_URL must point to a running PostgreSQL instance.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

# Add project root to sys.path so app.* imports work when called directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.assignment import Assignment
from app.models.attendance import Attendance
from app.models.client_payment import ClientPayment
from app.models.client_profile import ClientProfile
from app.models.invoice import Invoice
from app.models.quote import Quote
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.utils.time import utcnow

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

N_CLIENTS = 50
N_WORKERS = 500
N_REQUIREMENTS = 200
N_ASSIGNMENTS = 1_000
N_ATTENDANCE = 5_000
N_QUOTES = 100
N_INVOICES = 50
N_PAYMENTS = 200

CITIES = ["Chennai", "Coimbatore", "Madurai", "Salem", "Trichy", "Tirunelveli", "Vellore", "Erode"]
STATES = ["Tamil Nadu"]
CATEGORIES = ["Cook", "Housekeeping", "Caretaker", "Driver", "Security", "Gardener", "Laundry", "Nanny"]
REQ_STATUSES = ["submitted", "under_review", "quoted", "approved", "workers_assigned", "in_progress", "completed"]
ASS_STATUSES = ["assigned", "accepted", "active", "completed", "cancelled"]
ATT_STATUSES = ["present", "absent", "half_day"]
QUOTE_STATUSES = ["draft", "sent", "approved", "rejected"]
PAYMENT_STATUSES = ["pending", "paid", "failed"]
PAYMENT_MODELS = ["daily", "weekly", "monthly", "fixed"]
PAYMENT_MODES = ["cash", "upi", "bank_transfer", "cheque"]
INVOICE_STATUSES = ["draft", "sent", "paid", "cancelled"]

_SEED_TAG = "perf_seed"  # stored in User.name prefix to identify perf records


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _rand_date(days_back: int = 180, days_forward: int = 90) -> date:
    offset = random.randint(-days_back, days_forward)
    return date.today() + timedelta(days=offset)


def _rand_past_dt(days_back: int = 90) -> datetime:
    offset = random.randint(0, days_back * 24 * 60)
    return _utcnow() - timedelta(minutes=offset)


# ---------------------------------------------------------------------------
# Wipe helpers
# ---------------------------------------------------------------------------

def _wipe(db: Session) -> None:
    """Remove all rows created by this seed script (tagged by name prefix)."""
    print("Wiping existing perf seed data…")
    user_ids = [
        row[0]
        for row in db.execute(
            select(User.id).where(User.name.like(f"{_SEED_TAG}%"))
        ).all()
    ]
    if not user_ids:
        print("  Nothing to wipe.")
        return

    client_profile_ids = [
        row[0]
        for row in db.execute(
            select(ClientProfile.id).where(ClientProfile.user_id.in_(user_ids))
        ).all()
    ]
    worker_profile_ids = [
        row[0]
        for row in db.execute(
            select(WorkerProfile.id).where(WorkerProfile.user_id.in_(user_ids))
        ).all()
    ]

    # Delete in reverse FK dependency order.
    if client_profile_ids or worker_profile_ids:
        req_ids = [
            row[0]
            for row in db.execute(
                select(Requirement.id).where(Requirement.client_id.in_(client_profile_ids))
            ).all()
        ]
        if req_ids:
            assignment_ids = [
                row[0]
                for row in db.execute(
                    select(Assignment.id).where(Assignment.requirement_id.in_(req_ids))
                ).all()
            ]
            if assignment_ids:
                db.execute(
                    text("DELETE FROM attendance WHERE assignment_id = ANY(:ids)"),
                    {"ids": assignment_ids},
                )
            db.execute(text("DELETE FROM quotes WHERE requirement_id = ANY(:ids)"), {"ids": req_ids})
            db.execute(text("DELETE FROM invoices WHERE requirement_id = ANY(:ids)"), {"ids": req_ids})
            db.execute(
                text("DELETE FROM client_payments WHERE requirement_id = ANY(:ids)"),
                {"ids": req_ids},
            )
            db.execute(text("DELETE FROM assignments WHERE requirement_id = ANY(:ids)"), {"ids": req_ids})
            db.execute(text("DELETE FROM requirements WHERE id = ANY(:ids)"), {"ids": req_ids})

    db.execute(text("DELETE FROM client_profiles WHERE user_id = ANY(:ids)"), {"ids": user_ids})
    db.execute(text("DELETE FROM worker_profiles WHERE user_id = ANY(:ids)"), {"ids": user_ids})
    db.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": user_ids})
    db.commit()
    print(f"  Wiped data for {len(user_ids)} seed users.")


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _already_seeded(db: Session) -> bool:
    count = db.execute(
        select(User).where(User.name.like(f"{_SEED_TAG}%")).limit(1)
    ).scalar_one_or_none()
    return count is not None


def _bulk_insert(db: Session, objects: list) -> None:
    db.add_all(objects)
    db.flush()


def _seed_clients(db: Session, admin_user: User) -> list[ClientProfile]:
    print(f"  Creating {N_CLIENTS} client users + profiles…")
    users = []
    for i in range(N_CLIENTS):
        u = User(
            phone=f"+9190000{i:05d}",
            name=f"{_SEED_TAG}_client_{i}",
            role=UserRole.CLIENT.value,
            is_active=True,
            is_phone_verified=True,
        )
        users.append(u)
    _bulk_insert(db, users)

    profiles = []
    for i, u in enumerate(users):
        city = random.choice(CITIES)
        p = ClientProfile(
            user_id=u.id,
            client_type=random.choice(["company", "individual"]),
            company_name=f"PerfCo {i}" if i % 3 != 0 else None,
            contact_name=f"Contact {i}",
            city=city,
            state="Tamil Nadu",
        )
        profiles.append(p)
    _bulk_insert(db, profiles)
    return profiles


def _seed_workers(db: Session) -> list[WorkerProfile]:
    print(f"  Creating {N_WORKERS} worker users + profiles…")
    users = []
    for i in range(N_WORKERS):
        u = User(
            phone=f"+9191000{i:05d}",
            name=f"{_SEED_TAG}_worker_{i}",
            role=UserRole.WORKER.value,
            is_active=True,
            is_phone_verified=True,
        )
        users.append(u)
    _bulk_insert(db, users)

    profiles = []
    for i, u in enumerate(users):
        city = random.choice(CITIES)
        cat = random.choice(CATEGORIES)
        p = WorkerProfile(
            user_id=u.id,
            full_name=f"Worker {i}",
            category=cat,
            city=city,
            state="Tamil Nadu",
            is_available=random.random() > 0.2,
            verification_status=random.choice(["approved", "approved", "pending", "verified"]),
            skills=[cat, random.choice(CATEGORIES)],
            available_days=random.sample(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], k=random.randint(3, 6)),
            available_shifts=random.sample(["morning", "afternoon", "evening"], k=random.randint(1, 2)),
        )
        profiles.append(p)
    _bulk_insert(db, profiles)
    return profiles


def _seed_requirements(db: Session, client_profiles: list[ClientProfile], admin_user: User) -> list[Requirement]:
    print(f"  Creating {N_REQUIREMENTS} requirements…")
    reqs = []
    statuses = REQ_STATUSES * (N_REQUIREMENTS // len(REQ_STATUSES) + 1)
    random.shuffle(statuses)
    for i in range(N_REQUIREMENTS):
        client = random.choice(client_profiles)
        city = random.choice(CITIES)
        start = _rand_date(days_back=90, days_forward=60)
        r = Requirement(
            client_id=client.id,
            category=random.choice(CATEGORIES),
            number_of_workers=random.randint(1, 10),
            work_location=f"{city} Site {i}",
            city=city,
            state="Tamil Nadu",
            start_date=start,
            duration_days=random.randint(7, 90),
            shift_details=random.choice(["morning 09:00-17:00", "night 22:00-06:00", "general shift"]),
            food_required=random.random() > 0.5,
            accommodation_required=random.random() > 0.5,
            budget_amount=random.randint(5000, 100000),
            status=statuses[i],
            created_by_user_id=admin_user.id,
        )
        reqs.append(r)
    _bulk_insert(db, reqs)
    return reqs


def _seed_assignments(
    db: Session,
    requirements: list[Requirement],
    worker_profiles: list[WorkerProfile],
    admin_user: User,
) -> list[Assignment]:
    print(f"  Creating {N_ASSIGNMENTS} assignments…")
    # Only assign to requirements in assignable statuses.
    assignable = [r for r in requirements if r.status in {"workers_assigned", "in_progress", "approved"}]
    if not assignable:
        assignable = requirements  # fallback: use all

    statuses = ASS_STATUSES * (N_ASSIGNMENTS // len(ASS_STATUSES) + 1)
    random.shuffle(statuses)

    # Track (req_id, worker_id) pairs to avoid duplicates.
    seen: set[tuple[int, int]] = set()
    assignments = []
    attempts = 0
    while len(assignments) < N_ASSIGNMENTS and attempts < N_ASSIGNMENTS * 5:
        attempts += 1
        req = random.choice(assignable)
        worker = random.choice(worker_profiles)
        key = (req.id, worker.id)
        if key in seen:
            continue
        seen.add(key)
        a = Assignment(
            requirement_id=req.id,
            worker_profile_id=worker.id,
            assigned_by_user_id=admin_user.id,
            status=statuses[len(assignments)],
            assigned_role=req.category,
            assigned_shift=random.choice(["morning", "afternoon", "night"]),
            salary_amount=random.randint(300, 800),
            start_date=req.start_date,
            end_date=req.start_date + timedelta(days=req.duration_days) if req.start_date else None,
            assigned_at=_rand_past_dt(60),
        )
        assignments.append(a)
    _bulk_insert(db, assignments)
    return assignments


def _seed_attendance(db: Session, assignments: list[Assignment], worker_profiles: list[WorkerProfile]) -> None:
    print(f"  Creating {N_ATTENDANCE} attendance records…")
    worker_map = {wp.id: wp for wp in worker_profiles}
    active_assignments = [a for a in assignments if a.status in {"active", "completed"}]
    if not active_assignments:
        active_assignments = assignments

    # Track (assignment_id, date) uniqueness.
    seen: set[tuple[int, date]] = set()
    records = []
    attempts = 0
    while len(records) < N_ATTENDANCE and attempts < N_ATTENDANCE * 10:
        attempts += 1
        assignment = random.choice(active_assignments)
        att_date = date.today() - timedelta(days=random.randint(0, 60))
        key = (assignment.id, att_date)
        if key in seen:
            continue
        seen.add(key)
        check_in = datetime.combine(att_date, datetime.min.time()) + timedelta(hours=random.randint(7, 9))
        r = Attendance(
            assignment_id=assignment.id,
            worker_profile_id=assignment.worker_profile_id,
            attendance_date=att_date,
            status=random.choice(ATT_STATUSES),
            check_in_time=check_in,
            check_out_time=check_in + timedelta(hours=random.randint(6, 10)),
            approval_status=random.choice(["pending", "approved", "approved"]),
        )
        records.append(r)
    _bulk_insert(db, records)
    print(f"    Inserted {len(records)} attendance records.")


def _seed_quotes(db: Session, requirements: list[Requirement], admin_user: User) -> list[Quote]:
    print(f"  Creating {N_QUOTES} quotes…")
    # Prefer requirements with quoted/approved status.
    quoted_reqs = [r for r in requirements if r.status in {"quoted", "approved", "in_progress", "workers_assigned"}]
    if len(quoted_reqs) < N_QUOTES:
        quoted_reqs = requirements

    statuses = QUOTE_STATUSES * (N_QUOTES // len(QUOTE_STATUSES) + 1)
    random.shuffle(statuses)
    seen_req_ids: set[int] = set()
    quotes = []
    for i in range(min(N_QUOTES, len(quoted_reqs))):
        req = quoted_reqs[i % len(quoted_reqs)]
        if req.id in seen_req_ids:
            continue
        seen_req_ids.add(req.id)
        amount = random.randint(10000, 500000)
        q = Quote(
            requirement_id=req.id,
            quoted_amount=amount,
            rate_per_worker=amount // req.number_of_workers,
            total_worker_days=req.number_of_workers * req.duration_days,
            advance_amount=amount // 4,
            payment_model=random.choice(PAYMENT_MODELS),
            valid_until=date.today() + timedelta(days=30),
            status=statuses[i],
            created_by_user_id=admin_user.id,
        )
        quotes.append(q)
    _bulk_insert(db, quotes)
    return quotes


def _seed_invoices(db: Session, quotes: list[Quote], admin_user: User) -> list[Invoice]:
    print(f"  Creating {N_INVOICES} invoices…")
    approved_quotes = [q for q in quotes if q.status == "approved"]
    if len(approved_quotes) < N_INVOICES:
        approved_quotes = quotes

    # Track requirement_id uniqueness (only one non-cancelled invoice per requirement).
    seen_req: set[int] = set()
    invoices = []
    for i, q in enumerate(approved_quotes):
        if len(invoices) >= N_INVOICES:
            break
        if q.requirement_id in seen_req:
            continue
        seen_req.add(q.requirement_id)
        subtotal = q.quoted_amount
        gst_rate = 18.0
        gst_amount = int(subtotal * gst_rate / 100)
        inv = Invoice(
            invoice_number=f"PERF-INV-{i+1:04d}",
            requirement_id=q.requirement_id,
            client_id=db.execute(
                select(Requirement.client_id).where(Requirement.id == q.requirement_id)
            ).scalar_one(),
            quote_id=q.id,
            subtotal=subtotal,
            gst_rate=gst_rate,
            gst_amount=gst_amount,
            total_amount=subtotal + gst_amount,
            status=random.choice(INVOICE_STATUSES),
            issued_at=_rand_past_dt(30),
            due_date=date.today() + timedelta(days=random.randint(7, 30)),
            created_by_user_id=admin_user.id,
        )
        invoices.append(inv)
    _bulk_insert(db, invoices)
    return invoices


def _seed_payments(
    db: Session,
    requirements: list[Requirement],
    client_profiles: list[ClientProfile],
    admin_user: User,
) -> None:
    print(f"  Creating {N_PAYMENTS} client payments…")
    client_map = {cp.id: cp for cp in client_profiles}
    payable_reqs = [r for r in requirements if r.status in {"quoted", "approved", "workers_assigned", "in_progress", "completed"}]
    if not payable_reqs:
        payable_reqs = requirements

    statuses = PAYMENT_STATUSES * (N_PAYMENTS // len(PAYMENT_STATUSES) + 1)
    random.shuffle(statuses)

    payments = []
    for i in range(N_PAYMENTS):
        req = random.choice(payable_reqs)
        status = statuses[i]
        p = ClientPayment(
            client_id=req.client_id,
            requirement_id=req.id,
            amount=random.randint(5000, 200000),
            payment_model=random.choice(PAYMENT_MODELS),
            payment_mode=random.choice(PAYMENT_MODES),
            payment_status=status,
            reference_note=f"Perf payment {i}",
            recorded_by_user_id=admin_user.id,
            paid_at=_rand_past_dt(30) if status == "paid" else None,
        )
        payments.append(p)
    _bulk_insert(db, payments)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _get_or_create_admin(db: Session) -> User:
    admin = db.execute(
        select(User).where(User.role == UserRole.ADMIN.value).limit(1)
    ).scalar_one_or_none()
    if not admin:
        admin = User(
            email="perf-admin@annai-illam.test",
            name="Perf Admin",
            role=UserRole.ADMIN.value,
            password_hash=hash_password("PerfAdmin123!"),
            is_active=True,
            is_email_verified=True,
        )
        db.add(admin)
        db.flush()
    return admin


def seed(db: Session, *, wipe: bool = False) -> None:
    if wipe:
        _wipe(db)
    elif _already_seeded(db):
        print("Perf seed data already present. Use --wipe to re-seed.")
        return

    print("Seeding performance test data…")
    admin = _get_or_create_admin(db)
    clients = _seed_clients(db, admin)
    workers = _seed_workers(db)
    requirements = _seed_requirements(db, clients, admin)
    assignments = _seed_assignments(db, requirements, workers, admin)
    _seed_attendance(db, assignments, workers)
    quotes = _seed_quotes(db, requirements, admin)
    _seed_invoices(db, quotes, admin)
    _seed_payments(db, requirements, clients, admin)

    db.commit()
    print("Done.")
    print(f"  Clients:     {len(clients)}")
    print(f"  Workers:     {len(workers)}")
    print(f"  Requirements:{len(requirements)}")
    print(f"  Assignments: {len(assignments)}")
    print(f"  Quotes:      {len(quotes)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed performance test data.")
    parser.add_argument("--wipe", action="store_true", help="Remove existing perf data before seeding")
    args = parser.parse_args(argv)

    db: Session = SessionLocal()
    try:
        seed(db, wipe=args.wipe)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
