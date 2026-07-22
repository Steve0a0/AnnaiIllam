from sqlalchemy import func, select

from app.models.legal_acceptance import LegalAcceptance
from app.services.legal_document_service import CURRENT_LEGAL_VERSION
from app.services.token_service import build_token_pair


def auth_headers(db, user) -> dict[str, str]:
    token, _ = build_token_pair(
        db,
        user_id=user.id,
        subject=user.email or user.phone or str(user.id),
        role=user.role,
    )
    return {"Authorization": f"Bearer {token}"}


def test_legal_acceptance_status_requires_authentication(client):
    response = client.get("/api/v1/me/legal-acceptances")
    assert response.status_code == 401


def test_client_accepts_complete_current_document_set_idempotently(
    client, db, client_user
):
    headers = auth_headers(db, client_user)
    initial = client.get("/api/v1/me/legal-acceptances", headers=headers)
    assert initial.status_code == 200
    status = initial.json()["data"]
    assert status["version"] == CURRENT_LEGAL_VERSION
    assert status["role"] == "client"
    assert status["is_current"] is False
    slugs = [item["slug"] for item in status["required_documents"]]
    assert slugs == ["privacy", "client-terms", "refund-cancellation", "grievance"]
    assert all(item["url"].endswith(f"/{item['slug']}/{CURRENT_LEGAL_VERSION}") for item in status["required_documents"])

    payload = {
        "version": CURRENT_LEGAL_VERSION,
        "document_slugs": slugs,
        "source": "client_mobile",
    }
    accepted = client.post(
        "/api/v1/me/legal-acceptances", headers=headers, json=payload
    )
    assert accepted.status_code == 200
    accepted_status = accepted.json()["data"]
    assert accepted_status["is_current"] is True
    accepted_times = {
        item["accepted_at"] for item in accepted_status["required_documents"]
    }
    assert len(accepted_times) == 1
    assert None not in accepted_times

    repeated = client.post(
        "/api/v1/me/legal-acceptances", headers=headers, json=payload
    )
    assert repeated.status_code == 200
    assert db.scalar(select(func.count()).select_from(LegalAcceptance)) == 4


def test_worker_has_role_specific_terms(client, db, worker_user):
    response = client.get(
        "/api/v1/me/legal-acceptances",
        headers=auth_headers(db, worker_user),
    )
    assert response.status_code == 200
    assert [
        item["slug"] for item in response.json()["data"]["required_documents"]
    ] == ["privacy", "worker-terms", "grievance"]


def test_stale_version_or_partial_document_set_is_rejected(client, db, client_user):
    headers = auth_headers(db, client_user)
    stale = client.post(
        "/api/v1/me/legal-acceptances",
        headers=headers,
        json={
            "version": "2025-01-01",
            "document_slugs": [
                "privacy",
                "client-terms",
                "refund-cancellation",
                "grievance",
            ],
            "source": "client_mobile",
        },
    )
    assert stale.status_code == 409

    partial = client.post(
        "/api/v1/me/legal-acceptances",
        headers=headers,
        json={
            "version": CURRENT_LEGAL_VERSION,
            "document_slugs": ["privacy", "client-terms"],
            "source": "client_mobile",
        },
    )
    assert partial.status_code == 422
    assert db.scalar(select(func.count()).select_from(LegalAcceptance)) == 0


def test_admin_cannot_use_client_worker_acceptance_endpoint(client, db, admin_user):
    response = client.get(
        "/api/v1/me/legal-acceptances", headers=auth_headers(db, admin_user)
    )
    assert response.status_code == 403

