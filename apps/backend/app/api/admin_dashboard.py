from datetime import timedelta
from app.utils.time import utcnow

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_role
from app.core.roles import UserRole
from app.db.deps import get_db
from app.models.user import User
from app.repositories.assignment_repository import count_active_assignments, count_assignments, get_active_assignments
from app.repositories.attendance_repository import (
    count_absent_attendance,
    count_attendance_records,
    count_present_attendance,
    get_attendance_for_assignment_on_date,
)
from app.repositories.complaint_repository import count_all_complaints, count_open_complaints, get_all_complaints
from app.repositories.payment_repository import (
    count_client_payments,
    count_worker_payouts,
    sum_client_payments_paid,
    sum_worker_payouts_paid,
    get_client_payments_by_client_id,
)
from app.repositories.payroll_repository import count_payroll_items, count_payroll_runs
from app.repositories.profile_repository import count_available_workers, count_workers
from app.repositories.requirement_repository import count_open_requirements, count_requirements, get_all_requirements
from app.repositories.sla_repository import get_sla_policy_map
from app.utils.response import success_response

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    data = {
        "requirements": {
            "total": count_requirements(db),
            "open": count_open_requirements(db),
        },
        "assignments": {
            "total": count_assignments(db),
            "active": count_active_assignments(db),
        },
        "workers": {
            "total": count_workers(db),
            "available": count_available_workers(db),
        },
        "complaints": {
            "total": count_all_complaints(db),
            "open": count_open_complaints(db),
        },
        "attendance": {
            "total_records": count_attendance_records(db),
            "present": count_present_attendance(db),
            "absent": count_absent_attendance(db),
        },
        "payroll": {
            "runs": count_payroll_runs(db),
            "items": count_payroll_items(db),
        },
        "finance": {
            "client_payments_count": count_client_payments(db),
            "worker_payouts_count": count_worker_payouts(db),
            "client_paid_total": sum_client_payments_paid(db),
            "worker_paid_total": sum_worker_payouts_paid(db),
        },
    }

    return success_response("Dashboard summary fetched successfully", data)


@router.get("/alerts")
def get_dashboard_alerts(
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    now = utcnow()
    today = now.date()
    complaints = get_all_complaints(db)
    sla_policy_map = get_sla_policy_map(db)
    active_assignments = get_active_assignments(db)
    requirements = get_all_requirements(db)

    overdue_complaints = [
        {
            "id": item.id,
            "requirement_id": item.requirement_id,
            "severity": item.severity,
            "status": item.status,
            "created_at": item.created_at.isoformat(),
            "age_hours": int((now - item.created_at).total_seconds() // 3600),
        }
        for item in complaints
        if item.status in {"open", "under_review"}
        and item.created_at
        <= now - timedelta(hours=sla_policy_map.get(item.severity, sla_policy_map["medium"])["resolution_hours"])
    ]

    missing_attendance = []
    for assignment in active_assignments:
        if not get_attendance_for_assignment_on_date(db, assignment.id, today):
            missing_attendance.append(
                {
                    "assignment_id": assignment.id,
                    "worker_profile_id": assignment.worker_profile_id,
                    "requirement_id": assignment.requirement_id,
                    "status": assignment.status,
                }
            )

    unpaid_requirements = []
    for requirement in requirements:
        payments = get_client_payments_by_client_id(db, requirement.client_id)
        pending = sum(
            payment.amount
            for payment in payments
            if payment.requirement_id == requirement.id and payment.payment_status != "paid"
        )
        if pending > 0:
            unpaid_requirements.append(
                {
                    "requirement_id": requirement.id,
                    "client_id": requirement.client_id,
                    "pending_amount": pending,
                    "status": requirement.status,
                }
            )

    return success_response(
        "Dashboard alerts fetched successfully",
        {
            "overdue_complaints": overdue_complaints,
            "missing_attendance": missing_attendance,
            "unpaid_invoices": unpaid_requirements,
        },
    )
