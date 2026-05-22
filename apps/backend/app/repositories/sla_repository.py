from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.complaint_sla_policy import ComplaintSlaPolicy


DEFAULT_SLA_POLICIES = {
    "low": {"response_hours": 24, "resolution_hours": 96},
    "medium": {"response_hours": 12, "resolution_hours": 48},
    "high": {"response_hours": 4, "resolution_hours": 24},
    "urgent": {"response_hours": 1, "resolution_hours": 8},
}


SEVERITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


def get_sla_policies(db: Session) -> list[ComplaintSlaPolicy]:
    stmt = select(ComplaintSlaPolicy)
    rows = list(db.execute(stmt).scalars().all())

    # Seed defaults on first access if table is empty
    if not rows:
        for severity, hours in DEFAULT_SLA_POLICIES.items():
            policy = ComplaintSlaPolicy(
                severity=severity,
                response_hours=hours["response_hours"],
                resolution_hours=hours["resolution_hours"],
            )
            db.add(policy)
        db.commit()
        rows = list(db.execute(stmt).scalars().all())

    rows.sort(key=lambda p: SEVERITY_ORDER.get(p.severity, 99))
    return rows


def get_sla_policy_map(db: Session) -> dict[str, dict[str, int]]:
    policies = {
        item.severity: {
            "response_hours": item.response_hours,
            "resolution_hours": item.resolution_hours,
        }
        for item in get_sla_policies(db)
    }
    return {**DEFAULT_SLA_POLICIES, **policies}


def upsert_sla_policy(
    db: Session,
    severity: str,
    response_hours: int,
    resolution_hours: int,
) -> ComplaintSlaPolicy:
    stmt = select(ComplaintSlaPolicy).where(ComplaintSlaPolicy.severity == severity)
    policy = db.execute(stmt).scalar_one_or_none()
    if policy:
        policy.response_hours = response_hours
        policy.resolution_hours = resolution_hours
        db.flush()
        return policy

    policy = ComplaintSlaPolicy(
        severity=severity,
        response_hours=response_hours,
        resolution_hours=resolution_hours,
    )
    db.add(policy)
    db.flush()
    return policy
