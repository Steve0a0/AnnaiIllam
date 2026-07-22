from datetime import date

from sqlalchemy import func, select

from app.core.security import hash_password
from app.models.admin_profile import AdminProfile
from app.models.assignment import Assignment
from app.models.audit_log import AuditLog
from app.models.client_profile import ClientProfile
from app.models.invoice import Invoice
from app.models.payroll_item import PayrollItem
from app.models.payroll_run import PayrollRun
from app.models.privacy_request import PrivacyRequest
from app.models.quote import Quote
from app.models.refresh_token import RefreshToken
from app.models.requirement import Requirement
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair


def auth_headers(db, user: User) -> dict[str, str]:
    token, _ = build_token_pair(
        db,
        user_id=user.id,
        subject=user.email or user.phone or str(user.id),
        role=user.role,
    )
    return {"Authorization": f"Bearer {token}"}


def test_privacy_request_requires_authentication(client):
    response = client.post(
        "/api/v1/me/privacy-requests", json={"request_type": "deletion"}
    )
    assert response.status_code == 401


def test_user_can_create_list_and_cannot_duplicate_open_request(
    client, db, client_user
):
    headers = auth_headers(db, client_user)

    created = client.post(
        "/api/v1/me/privacy-requests",
        headers=headers,
        json={"request_type": "deletion", "reason": "No longer needed"},
    )
    assert created.status_code == 201
    assert created.json()["data"]["status"] == "pending"

    duplicate = client.post(
        "/api/v1/me/privacy-requests",
        headers=headers,
        json={"request_type": "deletion"},
    )
    assert duplicate.status_code == 409

    listed = client.get("/api/v1/me/privacy-requests", headers=headers)
    assert listed.status_code == 200
    assert [(item["request_type"], item["status"]) for item in listed.json()["data"]] == [
        ("deletion", "pending")
    ]


def test_export_is_available_only_after_super_admin_completion(
    client, db, client_user, admin_user
):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Example Industries",
        contact_name="Export User",
        city="Chennai",
        state="Tamil Nadu",
        email="export@example.test",
    )
    db.add(profile)
    db.commit()
    user_headers = auth_headers(db, client_user)
    admin_headers = auth_headers(db, admin_user)

    created = client.post(
        "/api/v1/me/privacy-requests",
        headers=user_headers,
        json={"request_type": "export"},
    )
    request_id = created.json()["data"]["id"]

    not_ready = client.get(
        f"/api/v1/me/privacy-requests/{request_id}/export", headers=user_headers
    )
    assert not_ready.status_code == 409

    completed = client.patch(
        f"/api/v1/admin/privacy-requests/{request_id}",
        headers=admin_headers,
        json={
            "status": "completed",
            "resolution_notes": "Identity and request scope verified.",
        },
    )
    assert completed.status_code == 200

    exported = client.get(
        f"/api/v1/me/privacy-requests/{request_id}/export", headers=user_headers
    )
    assert exported.status_code == 200
    payload = exported.json()["data"]
    assert payload["account"]["id"] == client_user.id
    assert payload["profile"]["company_name"] == "Example Industries"
    assert "password_hash" not in payload["account"]


def test_only_super_admin_can_access_privacy_queue(client, db, client_user):
    ops_user = User(
        email="ops-privacy@example.test",
        role="admin",
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
        is_email_verified=True,
    )
    db.add(ops_user)
    db.flush()
    db.add(
        AdminProfile(
            user_id=ops_user.id,
            full_name="Operations Admin",
            permission_group="ops_admin",
        )
    )
    db.commit()

    response = client.get(
        "/api/v1/admin/privacy-requests", headers=auth_headers(db, ops_user)
    )
    assert response.status_code == 403


def test_completed_deletion_anonymizes_identity_but_preserves_invoice(
    client, db, client_user, admin_user, monkeypatch
):
    profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Delete Me Industries",
        contact_name="Delete Me",
        city="Chennai",
        state="Tamil Nadu",
        address="Personal address",
        gst_number="33ABCDE1234F1Z5",
        email="billing@example.test",
    )
    db.add(profile)
    db.flush()
    requirement = Requirement(
        client_id=profile.id,
        category="General Labour",
        number_of_workers=1,
        work_location="Factory",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date(2026, 8, 1),
        duration_days=1,
        created_by_user_id=client_user.id,
    )
    db.add(requirement)
    db.flush()
    quote = Quote(
        requirement_id=requirement.id,
        quoted_amount=118000,
        payment_model="full",
        created_by_user_id=admin_user.id,
    )
    db.add(quote)
    db.flush()
    invoice = Invoice(
        invoice_number="TEST-PRIVACY-0001",
        requirement_id=requirement.id,
        client_id=profile.id,
        quote_id=quote.id,
        subtotal=100000,
        gst_rate=18,
        gst_amount=18000,
        total_amount=118000,
        status="issued",
        recipient_legal_name="Delete Me Industries",
        recipient_gstin="33ABCDE1234F1Z5",
        created_by_user_id=admin_user.id,
    )
    db.add(invoice)
    db.add(
        AuditLog(
            action="historical_login",
            details={"phone": client_user.phone, "email": client_user.email},
        )
    )
    db.commit()

    captured_audits = []
    monkeypatch.setattr(
        "app.api.admin_privacy.audit_event",
        lambda action, details, **kwargs: captured_audits.append(
            (action, details, kwargs)
        ),
    )
    user_headers = auth_headers(db, client_user)
    admin_headers = auth_headers(db, admin_user)
    created = client.post(
        "/api/v1/me/privacy-requests",
        headers=user_headers,
        json={"request_type": "deletion"},
    )
    request_id = created.json()["data"]["id"]

    completed = client.patch(
        f"/api/v1/admin/privacy-requests/{request_id}",
        headers=admin_headers,
        json={
            "status": "completed",
            "resolution_notes": "Identity verified and statutory records retained.",
        },
    )
    assert completed.status_code == 200

    db.expire_all()
    anonymized_user = db.get(User, client_user.id)
    anonymized_profile = db.get(ClientProfile, profile.id)
    assert anonymized_user is not None
    assert anonymized_user.is_active is False
    assert anonymized_user.phone is None
    assert anonymized_user.email is None
    assert anonymized_profile is not None
    assert anonymized_profile.contact_name == f"Deleted client {profile.id}"
    assert anonymized_profile.address is None
    assert anonymized_profile.gst_number is None
    assert db.get(Invoice, invoice.id) is not None
    assert db.get(Invoice, invoice.id).recipient_legal_name == "Delete Me Industries"
    assert db.scalar(
        select(func.count()).select_from(RefreshToken).where(
            RefreshToken.user_id == client_user.id
        )
    ) == 0
    privacy_request = db.get(PrivacyRequest, request_id)
    assert privacy_request.status == "completed"
    assert privacy_request.resolved_by_user_id == admin_user.id
    assert captured_audits[0][0] == "privacy_request_resolved"
    assert captured_audits[0][1]["outcome"] == "completed"
    historical_log = db.scalar(
        select(AuditLog).where(AuditLog.action == "historical_login")
    )
    assert historical_log.details == {
        "phone": "[ANONYMIZED]",
        "email": "[ANONYMIZED]",
    }

    repeated = client.patch(
        f"/api/v1/admin/privacy-requests/{request_id}",
        headers=admin_headers,
        json={
            "status": "completed",
            "resolution_notes": "Repeated click",
        },
    )
    assert repeated.status_code == 200


def test_completed_worker_deletion_preserves_payroll(
    client, db, client_user, worker_user, admin_user
):
    client_profile = ClientProfile(
        user_id=client_user.id,
        client_type="company",
        company_name="Payroll Client",
        contact_name="Payroll Contact",
        city="Chennai",
        state="Tamil Nadu",
    )
    worker_profile = WorkerProfile(
        user_id=worker_user.id,
        full_name="Payroll Worker",
        category="General Labour",
        city="Chennai",
        state="Tamil Nadu",
        address="Private address",
    )
    db.add_all([client_profile, worker_profile])
    db.flush()
    requirement = Requirement(
        client_id=client_profile.id,
        category="General Labour",
        number_of_workers=1,
        work_location="Factory",
        city="Chennai",
        state="Tamil Nadu",
        start_date=date(2026, 8, 1),
        duration_days=1,
        created_by_user_id=client_user.id,
    )
    db.add(requirement)
    db.flush()
    assignment = Assignment(
        requirement_id=requirement.id,
        worker_profile_id=worker_profile.id,
        assigned_by_user_id=admin_user.id,
        salary_amount=100000,
    )
    payroll_run = PayrollRun(
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        created_by_user_id=admin_user.id,
    )
    db.add_all([assignment, payroll_run])
    db.flush()
    payroll_item = PayrollItem(
        payroll_run_id=payroll_run.id,
        assignment_id=assignment.id,
        worker_profile_id=worker_profile.id,
        gross_amount=100000,
        net_amount=100000,
        attendance_days=1,
    )
    db.add(payroll_item)
    db.commit()

    created = client.post(
        "/api/v1/me/privacy-requests",
        headers=auth_headers(db, worker_user),
        json={"request_type": "deletion"},
    )
    request_id = created.json()["data"]["id"]
    completed = client.patch(
        f"/api/v1/admin/privacy-requests/{request_id}",
        headers=auth_headers(db, admin_user),
        json={
            "status": "completed",
            "resolution_notes": "Identity erased; payroll retained.",
        },
    )
    assert completed.status_code == 200

    db.expire_all()
    assert db.get(PayrollItem, payroll_item.id) is not None
    assert db.get(PayrollItem, payroll_item.id).net_amount == 100000
    retained_profile = db.get(WorkerProfile, worker_profile.id)
    assert retained_profile.full_name == f"Deleted worker {worker_profile.id}"
    assert retained_profile.address is None
    assert db.get(User, worker_user.id).is_active is False
