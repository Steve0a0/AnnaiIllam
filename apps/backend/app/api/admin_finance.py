from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.roles import require_permission_group, require_role
from app.api.dependencies.scoping import get_accessible_client_ids
from app.core.payment_constants import ClientPaymentStatus, PaymentModel, WorkerPayoutStatus
from app.core.payroll_constants import PayrollItemPaymentStatus
from app.core.roles import UserRole
from app.core.statuses import RequirementStatus, validate_requirement_transition
from app.db.deps import get_db
from app.models.user import User
from app.models.user import User
from app.repositories.payment_repository import (
    create_client_payment,
    create_worker_payout,
    get_client_payment_by_id,
    get_client_payments_by_requirement_id,
    get_client_payments_paginated_stmt,
    get_worker_payout_by_id,
    get_worker_payouts_by_payroll_item_id,
)
from app.utils.pagination import PaginationParams, paginate, pagination_meta
from app.repositories.payroll_repository import (
    get_all_payroll_runs,
    get_deductions_by_payroll_item_id,
    get_payroll_item_by_id,
    get_payroll_items_by_run_id,
)
from app.repositories.profile_repository import get_worker_profile_by_id
from app.repositories.requirement_repository import get_requirement_by_id
from app.models.client_payment import ClientPayment
from app.schemas.payment import (
    CreateWorkerPayoutSchema,
    MarkRunPaidSchema,
    RecordManualClientPaymentSchema,
    UpdateClientPaymentStatusSchema,
    UpdateWorkerPayoutStatusSchema,
)
from app.services.payment_service import build_manual_client_payment, build_worker_payout
from app.services.notification_service import enqueue_push_to_user
from app.utils.audit import audit_event
from app.utils.response import success_response
from app.utils.time import utcnow

router = APIRouter(prefix="/admin/finance", tags=["Admin Finance"])


@router.post("/client-payments/manual")
def record_manual_client_payment(
    payload: RecordManualClientPaymentSchema,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, payload.requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    allowed_models = {item.value for item in PaymentModel}
    if payload.payment_model not in allowed_models:
        raise HTTPException(status_code=400, detail="Invalid payment model")

    allowed_statuses = {
        ClientPaymentStatus.PENDING.value,
        ClientPaymentStatus.PAID.value,
        ClientPaymentStatus.FAILED.value,
        ClientPaymentStatus.REFUNDED.value,
    }
    if payload.payment_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid payment status")

    payment = build_manual_client_payment(
        client_id=requirement.client_id,
        requirement_id=requirement.id,
        amount=payload.amount,
        payment_model=payload.payment_model,
        payment_mode=payload.payment_mode,
        payment_status=payload.payment_status,
        recorded_by_user_id=current_user.id,
        reference_note=payload.reference_note,
    )
    create_client_payment(db, payment)
    db.commit()
    db.refresh(payment)

    audit_event(
        "manual_client_payment_recorded",
        {
            "payment_id": payment.id,
            "requirement_id": payment.requirement_id,
            "admin_user_id": current_user.id,
            "amount": payment.amount,
        },
    )

    return success_response(
        "Manual client payment recorded successfully",
        {
            "payment_id": payment.id,
            "status": payment.payment_status,
        },
    )


@router.get("/client-payments")
def list_all_client_payments(
    status: str | None = None,
    pg: PaginationParams = Depends(),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    accessible_client_ids: list[int] | None = Depends(get_accessible_client_ids),
    db: Session = Depends(get_db),
):
    """List all client payments, optionally filtered by status.
    Joins Requirement and ClientProfile to return rich context for the finance dashboard."""
    from app.models.requirement import Requirement
    from app.models.client_profile import ClientProfile

    # Fix 20: paginate the payments list instead of fetching up to 200 at a time
    stmt = get_client_payments_paginated_stmt(status=status)
    if accessible_client_ids is not None:
        if not accessible_client_ids:
            return success_response(
                "Client payments fetched successfully",
                {"items": [], **pagination_meta(pg, 0)},
            )
        stmt = stmt.where(ClientPayment.client_id.in_(accessible_client_ids))
    payments, total = paginate(stmt, db, pg)

    # Build lookup maps to avoid N+1
    req_ids = {p.requirement_id for p in payments}
    client_ids = {p.client_id for p in payments}

    from sqlalchemy import select as sa_select
    from app.models.quote import Quote

    reqs = {}
    if req_ids:
        for r in db.execute(
            sa_select(Requirement).where(Requirement.id.in_(req_ids))
        ).scalars().all():
            reqs[r.id] = r

    quotes = {}
    if req_ids:
        for q in db.execute(
            sa_select(Quote).where(Quote.requirement_id.in_(req_ids))
        ).scalars().all():
            quotes[q.requirement_id] = q

    profiles = {}
    if client_ids:
        for cp in db.execute(
            sa_select(ClientProfile).where(ClientProfile.id.in_(client_ids))
        ).scalars().all():
            profiles[cp.id] = cp

    data = []
    for p in payments:
        req = reqs.get(p.requirement_id)
        profile = profiles.get(p.client_id)
        quote = quotes.get(p.requirement_id)
        client_name = (
            (profile.company_name or profile.contact_name) if profile else f"Client #{p.client_id}"
        )
        is_advance = bool(quote and (quote.advance_amount or 0) > 0)
        data.append({
            "id": p.id,
            "client_id": p.client_id,
            "client_name": client_name,
            "requirement_id": p.requirement_id,
            "requirement_category": req.category if req else None,
            "requirement_city": req.city if req else None,
            "requirement_state": req.state if req else None,
            "amount": p.amount,
            "payment_model": p.payment_model,
            "payment_mode": p.payment_mode,
            "payment_status": p.payment_status,
            "is_advance": is_advance,
            "gateway_order_id": p.gateway_order_id,
            "gateway_payment_id": p.gateway_payment_id,
            "reference_note": p.reference_note,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })

    return success_response("Client payments fetched successfully", {"items": data, **pagination_meta(pg, total)})


@router.get("/client-payments/requirement/{requirement_id}")
def list_admin_client_payments_for_requirement(
    requirement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    requirement = get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    payments = get_client_payments_by_requirement_id(db, requirement_id)
    data = [
        {
            "id": item.id,
            "client_id": item.client_id,
            "requirement_id": item.requirement_id,
            "amount": item.amount,
            "payment_model": item.payment_model,
            "payment_mode": item.payment_mode,
            "payment_status": item.payment_status,
            "gateway_order_id": item.gateway_order_id,
            "gateway_payment_id": item.gateway_payment_id,
            "reference_note": item.reference_note,
            "paid_at": item.paid_at.isoformat() if item.paid_at else None,
        }
        for item in payments
    ]
    return success_response("Client payments fetched successfully", data)


@router.patch("/client-payments/{payment_id}/status")
def update_client_payment_status(
    payment_id: int,
    payload: UpdateClientPaymentStatusSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    """Admin verifies a reference (UTR) payment and marks it paid or failed.
    When marking paid: if the linked requirement is 'approved' and its quote has an
    advance_amount, the requirement is auto-transitioned to 'assigned'."""
    payment = get_client_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    old_status = payment.payment_status
    new_status = payload.payment_status

    if old_status == new_status:
        return success_response("No change", {"payment_id": payment.id, "status": new_status})

    payment.payment_status = new_status
    if new_status == ClientPaymentStatus.PAID.value and not payment.paid_at:
        payment.paid_at = utcnow()

    requirement_transitioned = False
    new_requirement_status = None

    # Auto-advance requirement: approved → assigned when advance is confirmed
    # Also: in_progress → completed when full balance is collected
    if new_status == ClientPaymentStatus.PAID.value:
        requirement = get_requirement_by_id(db, payment.requirement_id)
        if requirement:
            from app.models.quote import Quote
            from sqlalchemy import select as sa_select
            quote_stmt = sa_select(Quote).where(Quote.requirement_id == requirement.id)
            quote = db.execute(quote_stmt).scalar_one_or_none()

            if requirement.status == RequirementStatus.APPROVED.value:
                if quote and (quote.advance_amount or 0) > 0:
                    # Validate payment covers the advance amount before unlocking assignment
                    if payment.amount < quote.advance_amount:
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                f"Payment amount ({payment.amount}) does not cover "
                                f"the required advance ({quote.advance_amount}). "
                                "Record the correct amount or split payments to reach the advance threshold."
                            ),
                        )
                    try:
                        validate_requirement_transition(
                            requirement.status, RequirementStatus.WORKERS_ASSIGNED.value
                        )
                    except ValueError as exc:
                        raise HTTPException(status_code=400, detail=str(exc)) from exc
                    requirement.status = RequirementStatus.WORKERS_ASSIGNED.value
                    requirement_transitioned = True
                    new_requirement_status = RequirementStatus.WORKERS_ASSIGNED.value

            elif requirement.status == RequirementStatus.IN_PROGRESS.value:
                if quote and (quote.quoted_amount or 0) > 0:
                    all_payments = get_client_payments_by_requirement_id(db, requirement.id)
                    total_paid = sum(
                        p.amount for p in all_payments
                        if p.payment_status == ClientPaymentStatus.PAID.value
                    )
                    if total_paid >= quote.quoted_amount:
                        try:
                            validate_requirement_transition(
                                requirement.status, RequirementStatus.COMPLETED.value
                            )
                        except ValueError as exc:
                            raise HTTPException(status_code=400, detail=str(exc)) from exc
                        requirement.status = RequirementStatus.COMPLETED.value
                        requirement_transitioned = True
                        new_requirement_status = RequirementStatus.COMPLETED.value

    db.commit()

    audit_event(
        "admin_client_payment_status_updated",
        {
            "payment_id": payment.id,
            "requirement_id": payment.requirement_id,
            "old_status": old_status,
            "new_status": new_status,
            "admin_user_id": current_user.id,
            "requirement_auto_transitioned": requirement_transitioned,
        },
    )

    # Notify all admins when a payment is confirmed paid
    if new_status == ClientPaymentStatus.PAID.value:
        from sqlalchemy import select as _select
        _admin_users = db.execute(
            _select(User).where(User.role == "admin", User.is_active.is_(True))
        ).scalars().all()
        for _admin in _admin_users:
            enqueue_push_to_user(
                background_tasks,
                db,
                user_id=_admin.id,
                title="Payment received",
                body=f"Payment confirmed for requirement #{payment.requirement_id}.",
                data={"type": "payment_received", "requirement_id": str(payment.requirement_id)},
            )

        # Send invoice email to client
        _send_invoice_in_background(background_tasks, db, payment)

    return success_response(
        "Payment status updated",
        {
            "payment_id": payment.id,
            "status": payment.payment_status,
            "requirement_auto_transitioned": requirement_transitioned,
            "new_requirement_status": new_requirement_status,
        },
    )


@router.post("/worker-payouts")
def create_admin_worker_payout(
    payload: CreateWorkerPayoutSchema,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    payroll_item = get_payroll_item_by_id(db, payload.payroll_item_id)
    if not payroll_item:
        raise HTTPException(status_code=404, detail="Payroll item not found")

    worker_profile = get_worker_profile_by_id(db, payroll_item.worker_profile_id)
    if not worker_profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    if payload.amount > payroll_item.net_amount:
        raise HTTPException(status_code=400, detail="Payout amount cannot exceed payroll net amount")

    payout = build_worker_payout(
        payroll_item_id=payroll_item.id,
        worker_profile_id=payroll_item.worker_profile_id,
        amount=payload.amount,
        payout_mode=payload.payout_mode,
        paid_by_user_id=current_user.id,
        transaction_reference=payload.transaction_reference,
        notes=payload.notes,
    )
    create_worker_payout(db, payout)
    db.commit()
    db.refresh(payout)

    audit_event(
        "worker_payout_created",
        {
            "payout_id": payout.id,
            "payroll_item_id": payout.payroll_item_id,
            "worker_profile_id": payout.worker_profile_id,
            "amount": payout.amount,
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Worker payout created successfully",
        {
            "payout_id": payout.id,
            "status": payout.payout_status,
        },
    )


@router.get("/worker-payouts/payroll-item/{payroll_item_id}")
def list_worker_payouts_for_payroll_item(
    payroll_item_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    payroll_item = get_payroll_item_by_id(db, payroll_item_id)
    if not payroll_item:
        raise HTTPException(status_code=404, detail="Payroll item not found")

    payouts = get_worker_payouts_by_payroll_item_id(db, payroll_item_id)
    data = [
        {
            "id": item.id,
            "payroll_item_id": item.payroll_item_id,
            "worker_profile_id": item.worker_profile_id,
            "amount": item.amount,
            "payout_mode": item.payout_mode,
            "payout_status": item.payout_status,
            "transaction_reference": item.transaction_reference,
            "paid_at": item.paid_at.isoformat() if item.paid_at else None,
            "notes": item.notes,
        }
        for item in payouts
    ]
    return success_response("Worker payouts fetched successfully", data)


@router.patch("/worker-payouts/{payout_id}/status")
def update_worker_payout_status(
    payout_id: int,
    payload: UpdateWorkerPayoutStatusSchema,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    payout = get_worker_payout_by_id(db, payout_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Worker payout not found")

    allowed_statuses = {item.value for item in WorkerPayoutStatus}
    if payload.payout_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid payout status")

    old_status = payout.payout_status
    payout.payout_status = payload.payout_status
    if payload.payout_status == WorkerPayoutStatus.PAID.value and not payout.paid_at:
        payout.paid_at = utcnow()

    payroll_item = get_payroll_item_by_id(db, payout.payroll_item_id)
    if payroll_item and payload.payout_status == WorkerPayoutStatus.PAID.value:
        payroll_item.payment_status = PayrollItemPaymentStatus.PAID.value

    db.commit()

    audit_event(
        "worker_payout_status_updated",
        {
            "payout_id": payout.id,
            "old_status": old_status,
            "new_status": payout.payout_status,
            "admin_user_id": current_user.id,
        },
    )

    return success_response(
        "Worker payout status updated successfully",
        {
            "payout_id": payout.id,
            "status": payout.payout_status,
        },
    )


# ─── Payroll Queue (Finance tab) ──────────────────────────────────────────────

@router.get("/payroll-queue")
def get_payroll_queue(
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
):
    """Return all non-draft payroll runs with their items enriched with worker name + deductions.
    Used by the Finance tab → Payroll Queue."""
    from app.models.worker_profile import WorkerProfile
    from sqlalchemy import select as sa_select

    runs = [r for r in get_all_payroll_runs(db) if r.status != "draft"]

    if not runs:
        return success_response("Payroll queue fetched successfully", [])

    # Collect all worker_profile_ids across all items in one query
    all_items_map: dict[int, list] = {}  # run_id → items
    all_item_ids: list[int] = []
    for run in runs:
        items = get_payroll_items_by_run_id(db, run.id)
        all_items_map[run.id] = items
        all_item_ids.extend(item.id for item in items)

    worker_profile_ids = {
        item.worker_profile_id
        for items in all_items_map.values()
        for item in items
    }

    worker_names: dict[int, str] = {}
    if worker_profile_ids:
        for wp in db.execute(
            sa_select(WorkerProfile).where(WorkerProfile.id.in_(worker_profile_ids))
        ).scalars().all():
            worker_names[wp.id] = wp.full_name

    data = []
    for run in runs:
        items = all_items_map.get(run.id, [])
        serialized_items = []
        for item in items:
            deductions = get_deductions_by_payroll_item_id(db, item.id)
            serialized_items.append({
                "payroll_item_id": item.id,
                "assignment_id": item.assignment_id,
                "worker_profile_id": item.worker_profile_id,
                "worker_name": worker_names.get(item.worker_profile_id, f"Worker #{item.worker_profile_id}"),
                "gross_amount": item.gross_amount,
                "total_deduction_amount": item.total_deduction_amount,
                "net_amount": item.net_amount,
                "attendance_days": item.attendance_days,
                "half_days": item.half_days,
                "payment_status": item.payment_status,
                "platform_margin": item.platform_margin,
                "is_stale": item.is_stale,
                "deductions": [
                    {
                        "deduction_type": d.deduction_type,
                        "amount": d.amount,
                        "reason": d.reason,
                    }
                    for d in deductions
                ],
            })

        data.append({
            "payroll_run_id": run.id,
            "period_start": str(run.period_start),
            "period_end": str(run.period_end),
            "status": run.status,
            "notes": run.notes,
            "items": serialized_items,
        })

    return success_response("Payroll queue fetched successfully", data)


@router.post("/payroll-queue/{payroll_run_id}/mark-paid")
def mark_payroll_run_paid(
    payroll_run_id: int,
    payload: MarkRunPaidSchema,
    current_user: User = Depends(require_permission_group("finance_admin")),
    db: Session = Depends(get_db),
):
    """Bulk-transfer: create WorkerPayout records for all pending items in a run,
    mark items as paid, and advance run status to 'paid'."""
    from app.repositories.payroll_repository import get_payroll_run_by_id as get_run

    payroll_run = get_run(db, payroll_run_id)
    if not payroll_run:
        raise HTTPException(status_code=404, detail="Payroll run not found")

    if payroll_run.status == "paid":
        raise HTTPException(status_code=400, detail="Payroll run is already paid")

    items = get_payroll_items_by_run_id(db, payroll_run_id)
    if not items:
        raise HTTPException(status_code=400, detail="No payroll items found for this run")

    payouts_created = 0
    for item in items:
        if item.payment_status == PayrollItemPaymentStatus.PAID.value:
            continue  # Already paid, skip

        payout = build_worker_payout(
            payroll_item_id=item.id,
            worker_profile_id=item.worker_profile_id,
            amount=item.net_amount,
            payout_mode=payload.payout_mode,
            paid_by_user_id=current_user.id,
        )
        payout.payout_status = WorkerPayoutStatus.PAID.value
        payout.paid_at = utcnow()
        create_worker_payout(db, payout)

        item.payment_status = PayrollItemPaymentStatus.PAID.value
        payouts_created += 1

    payroll_run.status = "paid"
    payroll_run.updated_by_user_id = current_user.id
    db.commit()

    audit_event(
        "payroll_run_marked_paid",
        {
            "payroll_run_id": payroll_run.id,
            "admin_user_id": current_user.id,
            "payout_mode": payload.payout_mode,
            "payouts_created": payouts_created,
        },
    )

    return success_response(
        "Payroll run marked as paid",
        {
            "payroll_run_id": payroll_run.id,
            "status": payroll_run.status,
            "payouts_created": payouts_created,
        },
    )


# ---------------------------------------------------------------------------
# Internal helper — invoice email via background task
# ---------------------------------------------------------------------------

def _send_invoice_in_background(
    background_tasks: "BackgroundTasks",
    db: "Session",
    payment: "ClientPayment",
) -> None:
    """Resolve client email + requirement details, then enqueue the invoice send."""
    try:
        from app.models.client_profile import ClientProfile
        from app.models.requirement import Requirement
        from app.services.email_service import send_payment_invoice
        from sqlalchemy import select as _sa_select

        # Resolve client profile and email
        client_profile = db.execute(
            _sa_select(ClientProfile).where(ClientProfile.id == payment.client_id)
        ).scalar_one_or_none()

        if not client_profile:
            return

        # Email priority: ClientProfile.email > User.email
        client_user = db.execute(
            _sa_select(User).where(User.id == client_profile.user_id)
        ).scalar_one_or_none()

        to_email = client_profile.email or (client_user.email if client_user else None)
        if not to_email:
            return  # No email on record — skip silently

        # Resolve requirement
        requirement = db.execute(
            _sa_select(Requirement).where(Requirement.id == payment.requirement_id)
        ).scalar_one_or_none()

        if not requirement:
            return

        client_name = (
            client_profile.company_name or client_profile.contact_name or "Valued Client"
        )

        background_tasks.add_task(
            send_payment_invoice,
            to_email=to_email,
            client_name=client_name,
            payment_id=payment.id,
            payment_date=payment.paid_at or payment.updated_at,
            payment_model=payment.payment_model,
            amount=payment.amount,
            reference_note=payment.reference_note,
            requirement_category=requirement.category,
            requirement_subcategory=requirement.subcategory,
            work_location=requirement.work_location,
            city=requirement.city,
            state=requirement.state,
            start_date=str(requirement.start_date) if requirement.start_date else "",
            duration_days=requirement.duration_days or 1,
        )
    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "Failed to enqueue invoice email for payment #%s", payment.id
        )
