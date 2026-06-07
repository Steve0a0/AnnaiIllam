"""Seed 5 workers for REQ-4 testing.

3 matching  — general_labour, Chennai, approved, available
2 non-matching — wrong category / unavailable

Usage:
    cd apps/backend
    python -m scripts.seed_workers_req4
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User
from app.models.worker_profile import WorkerProfile

WORKERS = [
    # 3 matching — correct category, city, approved, available
    dict(phone="+919001000101", name="Rajan Murugan",    category="general_labour", city="Chennai", state="Tamil Nadu", available=True,  status="approved"),
    dict(phone="+919001000102", name="Selvam Krishnan",  category="general_labour", city="Chennai", state="Tamil Nadu", available=True,  status="approved"),
    dict(phone="+919001000103", name="Babu Arumugam",    category="general_labour", city="Chennai", state="Tamil Nadu", available=True,  status="approved"),
    # 2 non-matching
    dict(phone="+919001000104", name="Priya Devi",       category="cook",           city="Chennai", state="Tamil Nadu", available=True,  status="approved"),   # wrong category
    dict(phone="+919001000105", name="Suresh Pillai",    category="general_labour", city="Chennai", state="Tamil Nadu", available=False, status="approved"),   # unavailable
]


def main() -> None:
    db = SessionLocal()
    created: list[str] = []
    skipped: list[str] = []

    try:
        for w in WORKERS:
            existing = db.execute(
                select(User).where(User.phone == w["phone"])
            ).scalar_one_or_none()

            if existing:
                skipped.append(w["name"])
                continue

            user = User(
                phone=w["phone"],
                name=w["name"],
                role="worker",
                password_hash=hash_password("Worker@123"),
            )
            db.add(user)
            db.flush()

            profile = WorkerProfile(
                user_id=user.id,
                full_name=w["name"],
                category=w["category"],
                city=w["city"],
                state=w["state"],
                is_available=w["available"],
                verification_status=w["status"],
                experience_years="1-2 years",
                available_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                available_shifts=["Morning", "Full Day"],
            )
            db.add(profile)
            created.append(w["name"])

        db.commit()
    finally:
        db.close()

    print()
    if created:
        print(f"Created {len(created)} workers: {', '.join(created)}")
    if skipped:
        print(f"Skipped (already exist): {', '.join(skipped)}")

    print()
    print("Matching workers (should appear in Ready tab for REQ-4):")
    print("  1. Rajan Murugan   - general_labour, Chennai, approved, available=True")
    print("  2. Selvam Krishnan - general_labour, Chennai, approved, available=True")
    print("  3. Babu Arumugam   - general_labour, Chennai, approved, available=True")
    print()
    print("Non-matching workers (will appear in Blocked tab):")
    print("  4. Priya Devi    - category=cook (wrong category)")
    print("  5. Suresh Pillai - general_labour but available=False")


if __name__ == "__main__":
    main()
