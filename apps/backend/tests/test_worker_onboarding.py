"""Integration tests for the worker onboarding step machine.

Covered flows:
  GET  /worker/onboarding/status
  POST /worker/onboarding/upload-url
  POST /worker/onboarding/local-upload
  POST /worker/onboarding/identity
  POST /worker/onboarding/profile
  POST /admin/people/workers/{id}/approve
  POST /admin/people/workers/{id}/reject

Happy-path:
  new worker → identity → profile → admin approve → step == "approved"

Edge-cases and guards:
  - status requires worker JWT
  - upload-url rejects invalid content-type
  - identity can be resubmitted (idempotent — old pending docs replaced)
  - profile submission requires identity_uploaded step
  - profile can be updated after profile_submitted (re-submit)
  - approve/reject require admin JWT
  - approve requires profile_submitted step (422 otherwise)
  - reject requires profile_submitted step (422 otherwise)
  - reject rewinds step to identity_uploaded, marks docs rejected
  - approve then re-approve → 422 (already approved)
  - non-worker user cannot call worker onboarding endpoints
  - non-admin cannot call approve/reject
"""

import pytest

from app.core.file_upload_constants import SELFIE_MAX_SIZE_BYTES
from app.models.worker_document import WorkerDocument
from app.models.worker_profile import WorkerProfile
from app.services.token_service import build_token_pair

BASE = "/api/v1"

# A minimal but genuinely valid JPEG (magic bytes 0xFFD8FF …) so uploads pass
# the magic-byte + size checks the way a real photo would.
_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"

# ---------------------------------------------------------------------------
# Minimal valid profile payload
# ---------------------------------------------------------------------------

_PROFILE_PAYLOAD = {
    "full_name": "Rajan Kumar",
    "skills": ["cleaning", "cooking"],
    "experience_years": "1–2 years",
    "available_days": ["Mon", "Tue", "Wed"],
    "available_shifts": ["Morning"],
    "city": "Chennai",
    "state": "Tamil Nadu",
    "payment": {
        "upi_id": "rajan@upi",
        "bank_account_number": None,
        "bank_ifsc": None,
        "bank_holder_name": None,
    },
}


# ---------------------------------------------------------------------------
# Module-level fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def worker_headers(db, worker_user):
    access_token, _ = build_token_pair(
        db,
        user_id=worker_user.id,
        subject=worker_user.phone,
        role=worker_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_headers(db, admin_user):
    access_token, _ = build_token_pair(
        db,
        user_id=admin_user.id,
        subject=admin_user.email,
        role=admin_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def client_headers(db, client_user):
    access_token, _ = build_token_pair(
        db,
        user_id=client_user.id,
        subject=client_user.phone,
        role=client_user.role,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(autouse=True)
def _local_storage_mode(monkeypatch, tmp_path):
    """Force local-filesystem storage (no S3) so onboarding tests are
    deterministic regardless of the developer's .env — this matches CI, which
    configures no S3. is_s3_configured() reads settings.s3_bucket."""
    from app.core.config import settings
    monkeypatch.setattr(settings, 'local_upload_dir', str(tmp_path / 'uploads'))
    monkeypatch.setattr(settings, "s3_bucket", "")


# ---------------------------------------------------------------------------
# Helper — advance a worker user to identity_uploaded via the API
# ---------------------------------------------------------------------------

def _upload_local(test_client, headers, document_type, content=_JPEG, content_type="image/jpeg"):
    """Upload a real document via the local-upload endpoint; returns the response."""
    return test_client.post(
        f"{BASE}/worker/onboarding/local-upload",
        params={"document_type": document_type},
        files={"file": (f"{document_type}.jpg", content, content_type)},
        headers=headers,
    )


def _submit_identity(test_client, headers):
    """Upload real govt_id + selfie, then submit their validated keys."""
    govt_key = _upload_local(test_client, headers, "govt_id").json()["data"]["local_key"]
    selfie_key = _upload_local(test_client, headers, "selfie").json()["data"]["local_key"]
    return test_client.post(
        f"{BASE}/worker/onboarding/identity",
        json={"govt_id_key": govt_key, "selfie_key": selfie_key},
        headers=headers,
    )


# ---------------------------------------------------------------------------
# GET /worker/onboarding/status
# ---------------------------------------------------------------------------

class TestOnboardingStatus:
    def test_unauthenticated_returns_401(self, client):
        r = client.get(f"{BASE}/worker/onboarding/status")
        assert r.status_code == 401

    def test_non_worker_returns_403(self, client, client_headers):
        r = client.get(f"{BASE}/worker/onboarding/status", headers=client_headers)
        assert r.status_code == 403

    def test_new_worker_step_is_none(self, client, worker_headers):
        r = client.get(f"{BASE}/worker/onboarding/status", headers=worker_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["onboarding_step"] is None
        assert data["has_profile"] is False
        assert data["verification_status"] is None

    def test_step_reflects_identity_upload(self, client, db, worker_user, worker_headers):
        _submit_identity(client, worker_headers)
        db.refresh(worker_user)
        r = client.get(f"{BASE}/worker/onboarding/status", headers=worker_headers)
        assert r.status_code == 200
        assert r.json()["data"]["onboarding_step"] == "identity_uploaded"

    def test_step_reflects_profile_submitted(self, client, db, worker_user, worker_headers):
        _submit_identity(client, worker_headers)
        client.post(f"{BASE}/worker/onboarding/profile", json=_PROFILE_PAYLOAD, headers=worker_headers)
        db.refresh(worker_user)
        r = client.get(f"{BASE}/worker/onboarding/status", headers=worker_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["onboarding_step"] == "profile_submitted"
        assert data["has_profile"] is True
        assert data["verification_status"] == "under_review"


# ---------------------------------------------------------------------------
# POST /worker/onboarding/upload-url
# ---------------------------------------------------------------------------

class TestUploadUrl:
    def test_unauthenticated_returns_401(self, client):
        r = client.post(f"{BASE}/worker/onboarding/upload-url", json={
            "document_type": "govt_id", "content_type": "image/jpeg"
        })
        assert r.status_code == 401

    def test_invalid_content_type_returns_422(self, client, worker_headers):
        r = client.post(f"{BASE}/worker/onboarding/upload-url", json={
            "document_type": "govt_id",
            "content_type": "application/exe",
            "file_size": 1024,
        }, headers=worker_headers)
        assert r.status_code == 422

    def test_invalid_document_type_returns_422(self, client, worker_headers):
        r = client.post(f"{BASE}/worker/onboarding/upload-url", json={
            "document_type": "passport",  # not in allowed set
            "content_type": "image/jpeg",
            "file_size": 1024,
        }, headers=worker_headers)
        assert r.status_code == 422

    def test_dev_mode_returns_dev_flag(self, client, worker_headers, monkeypatch):
        """When S3 is not configured the endpoint must return dev_mode=True."""
        monkeypatch.setattr(
            "app.api.worker_onboarding.is_s3_configured",
            lambda: False,
        )
        r = client.post(f"{BASE}/worker/onboarding/upload-url", json={
            "document_type": "govt_id",
            "content_type": "image/jpeg",
            "file_size": 1024,
        }, headers=worker_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["dev_mode"] is True
        assert data["upload_url"] is None

    def test_valid_selfie_request(self, client, worker_headers):
        r = client.post(f"{BASE}/worker/onboarding/upload-url", json={
            "document_type": "selfie",
            "content_type": "image/png",
            "file_size": 1024,
        }, headers=worker_headers)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# POST /worker/onboarding/identity
# ---------------------------------------------------------------------------

class TestSubmitIdentity:
    def test_unauthenticated_returns_401(self, client):
        r = client.post(f"{BASE}/worker/onboarding/identity", json={
            "govt_id_key": "local:/a.jpg", "selfie_key": "local:/b.jpg"
        })
        assert r.status_code == 401

    def test_non_worker_returns_403(self, client, client_headers):
        r = client.post(f"{BASE}/worker/onboarding/identity", json={
            "govt_id_key": "local:/a.jpg", "selfie_key": "local:/b.jpg"
        }, headers=client_headers)
        assert r.status_code == 403

    def test_missing_field_returns_422(self, client, worker_headers):
        r = client.post(f"{BASE}/worker/onboarding/identity",
                        json={"govt_id_key": "local:/a.jpg"},
                        headers=worker_headers)
        assert r.status_code == 422

    def test_successful_identity_submission(self, client, db, worker_user, worker_headers):
        r = _submit_identity(client, worker_headers)
        assert r.status_code == 200
        db.refresh(worker_user)
        assert worker_user.onboarding_step == "identity_uploaded"

    def test_creates_two_worker_documents(self, client, db, worker_user, worker_headers):
        _submit_identity(client, worker_headers)
        docs = db.query(WorkerDocument).filter(
            WorkerDocument.user_id == worker_user.id
        ).all()
        assert len(docs) == 2
        types = {d.document_type for d in docs}
        assert types == {"govt_id", "selfie"}

    def test_resubmit_replaces_previous_docs(self, client, db, worker_user, worker_headers):
        """Calling identity twice should replace, not accumulate, pending docs."""
        _submit_identity(client, worker_headers)
        _submit_identity(client, worker_headers)  # second submission
        docs = db.query(WorkerDocument).filter(
            WorkerDocument.user_id == worker_user.id
        ).all()
        assert len(docs) == 2  # not 4

    def test_documents_are_pending_after_submission(self, client, db, worker_user, worker_headers):
        _submit_identity(client, worker_headers)
        docs = db.query(WorkerDocument).filter(
            WorkerDocument.user_id == worker_user.id
        ).all()
        assert all(d.verification_status == "pending" for d in docs)


# ---------------------------------------------------------------------------
# ANNAI-9 — KYC upload validation: bad objects rejected before activation
# ---------------------------------------------------------------------------

class TestIdentityUploadValidation:
    def test_oversized_document_rejected(self, client, worker_headers):
        oversized = _JPEG + b"\x00" * (SELFIE_MAX_SIZE_BYTES + 1)
        r = _upload_local(client, worker_headers, "selfie", content=oversized)
        assert r.status_code == 422

    def test_content_not_matching_type_rejected(self, client, worker_headers):
        # Declares JPEG but the bytes are not any supported image/pdf format.
        r = _upload_local(
            client, worker_headers, "govt_id",
            content=b"this is plain text, not an image",
            content_type="image/jpeg",
        )
        assert r.status_code == 422

    def test_cross_user_key_rejected(self, client, worker_headers):
        # A well-formed key owned by a DIFFERENT user must not be accepted.
        other_key = "local:worker-documents/999999/{}/{}.jpg"
        r = client.post(
            f"{BASE}/worker/onboarding/identity",
            json={
                "govt_id_key": other_key.format("govt_id", "a" * 32),
                "selfie_key": other_key.format("selfie", "b" * 32),
            },
            headers=worker_headers,
        )
        assert r.status_code == 422

    def test_nonexistent_object_rejected(self, client, worker_headers, worker_user):
        # Correct owner + prefix, but no file was ever uploaded.
        key = f"local:worker-documents/{worker_user.id}/govt_id/{'a' * 32}.jpg"
        r = client.post(
            f"{BASE}/worker/onboarding/identity",
            json={"govt_id_key": key, "selfie_key": key},
            headers=worker_headers,
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /worker/onboarding/profile
# ---------------------------------------------------------------------------

class TestSubmitProfile:
    def test_unauthenticated_returns_401(self, client):
        r = client.post(f"{BASE}/worker/onboarding/profile", json=_PROFILE_PAYLOAD)
        assert r.status_code == 401

    def test_non_worker_returns_403(self, client, client_headers):
        r = client.post(f"{BASE}/worker/onboarding/profile",
                        json=_PROFILE_PAYLOAD,
                        headers=client_headers)
        assert r.status_code == 403

    def test_profile_without_identity_returns_400(self, client, worker_headers):
        """Worker must complete identity step before submitting profile."""
        r = client.post(f"{BASE}/worker/onboarding/profile",
                        json=_PROFILE_PAYLOAD,
                        headers=worker_headers)
        assert r.status_code == 400

    def test_invalid_experience_years_returns_422(self, client, worker_headers):
        _submit_identity(client, worker_headers)
        bad_payload = {**_PROFILE_PAYLOAD, "experience_years": "10 years"}
        r = client.post(f"{BASE}/worker/onboarding/profile",
                        json=bad_payload,
                        headers=worker_headers)
        assert r.status_code == 422

    def test_missing_required_field_returns_422(self, client, worker_headers):
        _submit_identity(client, worker_headers)
        bad_payload = {k: v for k, v in _PROFILE_PAYLOAD.items() if k != "full_name"}
        r = client.post(f"{BASE}/worker/onboarding/profile",
                        json=bad_payload,
                        headers=worker_headers)
        assert r.status_code == 422

    def test_successful_profile_submission(self, client, db, worker_user, worker_headers):
        _submit_identity(client, worker_headers)
        r = client.post(f"{BASE}/worker/onboarding/profile",
                        json=_PROFILE_PAYLOAD,
                        headers=worker_headers)
        assert r.status_code == 200
        db.refresh(worker_user)
        assert worker_user.onboarding_step == "profile_submitted"

    def test_profile_record_created(self, client, db, worker_user, worker_headers):
        _submit_identity(client, worker_headers)
        client.post(f"{BASE}/worker/onboarding/profile",
                    json=_PROFILE_PAYLOAD,
                    headers=worker_headers)
        profile = db.query(WorkerProfile).filter(
            WorkerProfile.user_id == worker_user.id
        ).first()
        assert profile is not None
        assert profile.full_name == "Rajan Kumar"
        assert profile.city == "Chennai"
        assert profile.verification_status == "under_review"

    def test_documents_linked_to_profile(self, client, db, worker_user, worker_headers):
        _submit_identity(client, worker_headers)
        r = client.post(f"{BASE}/worker/onboarding/profile",
                        json=_PROFILE_PAYLOAD,
                        headers=worker_headers)
        profile_id = r.json()["data"]["profile_id"]
        docs = db.query(WorkerDocument).filter(
            WorkerDocument.worker_profile_id == profile_id
        ).all()
        assert len(docs) == 2

    def test_profile_resubmission_updates_existing(self, client, db, worker_user, worker_headers):
        """Calling profile twice must update the same record, not create a duplicate."""
        _submit_identity(client, worker_headers)
        client.post(f"{BASE}/worker/onboarding/profile",
                    json=_PROFILE_PAYLOAD,
                    headers=worker_headers)
        updated_payload = {**_PROFILE_PAYLOAD, "full_name": "Rajan Kumar Updated", "city": "Coimbatore"}
        client.post(f"{BASE}/worker/onboarding/profile",
                    json=updated_payload,
                    headers=worker_headers)
        profiles = db.query(WorkerProfile).filter(
            WorkerProfile.user_id == worker_user.id
        ).all()
        assert len(profiles) == 1
        db.refresh(profiles[0])
        assert profiles[0].full_name == "Rajan Kumar Updated"
        assert profiles[0].city == "Coimbatore"

    def test_payment_details_encrypted(self, client, db, worker_user, worker_headers):
        """upi_id must be stored encrypted (not plain text) in the DB."""
        _submit_identity(client, worker_headers)
        client.post(f"{BASE}/worker/onboarding/profile",
                    json=_PROFILE_PAYLOAD,
                    headers=worker_headers)
        profile = db.query(WorkerProfile).filter(
            WorkerProfile.user_id == worker_user.id
        ).first()
        # The stored value should not equal the plain text
        assert profile.upi_id_enc is not None
        assert profile.upi_id_enc != "rajan@upi"

    def test_selfie_sets_photo_url(self, client, db, worker_user, worker_headers):
        _submit_identity(client, worker_headers)
        client.post(f"{BASE}/worker/onboarding/profile",
                    json=_PROFILE_PAYLOAD,
                    headers=worker_headers)
        profile = db.query(WorkerProfile).filter(
            WorkerProfile.user_id == worker_user.id
        ).first()
        assert profile.photo_url is not None


# ---------------------------------------------------------------------------
# POST /admin/people/workers/{id}/approve
# ---------------------------------------------------------------------------

class TestApproveWorker:
    def _full_onboarding(self, test_client, headers):
        _submit_identity(test_client, headers)
        test_client.post(
            f"{BASE}/worker/onboarding/profile",
            json=_PROFILE_PAYLOAD,
            headers=headers,
        )

    def test_unauthenticated_returns_401(self, client, worker_user):
        r = client.post(f"{BASE}/admin/people/workers/{worker_user.id}/approve")
        assert r.status_code == 401

    def test_non_admin_returns_403(self, client, worker_user, worker_headers):
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/approve",
            headers=worker_headers,
        )
        assert r.status_code == 403

    def test_approve_nonexistent_worker_returns_404(self, client, admin_headers):
        r = client.post(f"{BASE}/admin/people/workers/999999/approve", headers=admin_headers)
        assert r.status_code == 404

    def test_approve_worker_without_profile_submitted_returns_422(
        self, client, worker_user, admin_headers, worker_headers
    ):
        """Worker is still at identity_uploaded — approve should reject."""
        _submit_identity(client, worker_headers)  # step = identity_uploaded, not profile_submitted
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/approve",
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_approve_new_worker_no_step_returns_422(
        self, client, worker_user, admin_headers
    ):
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/approve",
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_successful_approval_sets_step_approved(
        self, client, db, worker_user, admin_headers, worker_headers
    ):
        self._full_onboarding(client, worker_headers)
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/approve",
            headers=admin_headers,
        )
        assert r.status_code == 200
        db.refresh(worker_user)
        assert worker_user.onboarding_step == "approved"

    def test_approval_sets_profile_verification_status(
        self, client, db, worker_user, admin_headers, worker_headers
    ):
        self._full_onboarding(client, worker_headers)
        client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/approve",
            headers=admin_headers,
        )
        profile = db.query(WorkerProfile).filter(
            WorkerProfile.user_id == worker_user.id
        ).first()
        assert profile.verification_status == "approved"

    def test_approval_marks_documents_verified(
        self, client, db, worker_user, admin_headers, worker_headers
    ):
        self._full_onboarding(client, worker_headers)
        client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/approve",
            headers=admin_headers,
        )
        docs = db.query(WorkerDocument).filter(
            WorkerDocument.user_id == worker_user.id
        ).all()
        assert all(d.verification_status == "verified" for d in docs)

    def test_double_approve_returns_422(
        self, client, worker_user, admin_headers, worker_headers
    ):
        self._full_onboarding(client, worker_headers)
        client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/approve",
            headers=admin_headers,
        )
        # Second approve attempt
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/approve",
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_approval_response_contains_step(
        self, client, worker_user, admin_headers, worker_headers
    ):
        self._full_onboarding(client, worker_headers)
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/approve",
            headers=admin_headers,
        )
        assert r.json()["data"]["onboarding_step"] == "approved"


# ---------------------------------------------------------------------------
# POST /admin/people/workers/{id}/reject
# ---------------------------------------------------------------------------

class TestRejectWorker:
    _REJECT_BODY = {"reason": "Documents are not clearly visible and need to be resubmitted."}

    def _full_onboarding(self, test_client, headers):
        _submit_identity(test_client, headers)
        test_client.post(
            f"{BASE}/worker/onboarding/profile",
            json=_PROFILE_PAYLOAD,
            headers=headers,
        )

    def test_unauthenticated_returns_401(self, client, worker_user):
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/reject",
            json=self._REJECT_BODY,
        )
        assert r.status_code == 401

    def test_non_admin_returns_403(self, client, worker_user, worker_headers):
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/reject",
            json=self._REJECT_BODY,
            headers=worker_headers,
        )
        assert r.status_code == 403

    def test_reject_nonexistent_worker_returns_404(self, client, admin_headers):
        r = client.post(
            f"{BASE}/admin/people/workers/999999/reject",
            json=self._REJECT_BODY,
            headers=admin_headers,
        )
        assert r.status_code == 404

    def test_reject_without_profile_submitted_returns_422(
        self, client, worker_user, admin_headers, worker_headers
    ):
        _submit_identity(client, worker_headers)  # step = identity_uploaded only
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/reject",
            json=self._REJECT_BODY,
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_reject_missing_reason_returns_422(
        self, client, worker_user, admin_headers, worker_headers
    ):
        self._full_onboarding(client, worker_headers)
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/reject",
            json={},
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_reject_short_reason_returns_422(
        self, client, worker_user, admin_headers, worker_headers
    ):
        self._full_onboarding(client, worker_headers)
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/reject",
            json={"reason": "Bad"},  # less than 10 chars
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_successful_rejection_rewinds_step(
        self, client, db, worker_user, admin_headers, worker_headers
    ):
        self._full_onboarding(client, worker_headers)
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/reject",
            json=self._REJECT_BODY,
            headers=admin_headers,
        )
        assert r.status_code == 200
        db.refresh(worker_user)
        assert worker_user.onboarding_step == "identity_uploaded"

    def test_rejection_sets_profile_verification_rejected(
        self, client, db, worker_user, admin_headers, worker_headers
    ):
        self._full_onboarding(client, worker_headers)
        client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/reject",
            json=self._REJECT_BODY,
            headers=admin_headers,
        )
        profile = db.query(WorkerProfile).filter(
            WorkerProfile.user_id == worker_user.id
        ).first()
        assert profile.verification_status == "rejected"

    def test_rejection_marks_documents_rejected_with_reason(
        self, client, db, worker_user, admin_headers, worker_headers
    ):
        self._full_onboarding(client, worker_headers)
        client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/reject",
            json=self._REJECT_BODY,
            headers=admin_headers,
        )
        docs = db.query(WorkerDocument).filter(
            WorkerDocument.user_id == worker_user.id
        ).all()
        assert all(d.verification_status == "rejected" for d in docs)
        assert all(d.remarks is not None for d in docs)

    def test_worker_can_resubmit_profile_after_rejection(
        self, client, db, worker_user, admin_headers, worker_headers
    ):
        """After rejection, the worker is at identity_uploaded and can re-submit profile."""
        self._full_onboarding(client, worker_headers)
        client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/reject",
            json=self._REJECT_BODY,
            headers=admin_headers,
        )
        # Worker resubmits profile
        r = client.post(
            f"{BASE}/worker/onboarding/profile",
            json=_PROFILE_PAYLOAD,
            headers=worker_headers,
        )
        assert r.status_code == 200
        db.refresh(worker_user)
        assert worker_user.onboarding_step == "profile_submitted"


# ---------------------------------------------------------------------------
# Full happy-path end-to-end
# ---------------------------------------------------------------------------

class TestFullOnboardingFlow:
    def test_complete_flow(self, client, db, worker_user, admin_headers, worker_headers):
        """
        Step 0: new worker — onboarding_step is None
        Step 1: submit identity → identity_uploaded
        Step 2: submit profile → profile_submitted, profile under_review
        Step 3: admin approve → approved, profile approved, docs verified
        """
        # 0. Initial state
        r = client.get(f"{BASE}/worker/onboarding/status", headers=worker_headers)
        assert r.json()["data"]["onboarding_step"] is None

        # 1. Identity
        r = _submit_identity(client, worker_headers)
        assert r.status_code == 200
        db.refresh(worker_user)
        assert worker_user.onboarding_step == "identity_uploaded"

        # 2. Profile
        r = client.post(
            f"{BASE}/worker/onboarding/profile",
            json=_PROFILE_PAYLOAD,
            headers=worker_headers,
        )
        assert r.status_code == 200
        db.refresh(worker_user)
        assert worker_user.onboarding_step == "profile_submitted"

        profile = db.query(WorkerProfile).filter(
            WorkerProfile.user_id == worker_user.id
        ).first()
        assert profile is not None
        assert profile.verification_status == "under_review"

        # 3. Admin approve
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/approve",
            headers=admin_headers,
        )
        assert r.status_code == 200
        db.refresh(worker_user)
        assert worker_user.onboarding_step == "approved"

        db.refresh(profile)
        assert profile.verification_status == "approved"

        docs = db.query(WorkerDocument).filter(
            WorkerDocument.user_id == worker_user.id
        ).all()
        assert len(docs) == 2
        assert all(d.verification_status == "verified" for d in docs)

    def test_reject_then_resubmit_then_approve(
        self, client, db, worker_user, admin_headers, worker_headers
    ):
        """Rejection → re-profile → re-approve succeeds."""
        _submit_identity(client, worker_headers)
        client.post(
            f"{BASE}/worker/onboarding/profile",
            json=_PROFILE_PAYLOAD,
            headers=worker_headers,
        )
        # Admin rejects
        client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/reject",
            json={"reason": "Please upload a clearer government ID document."},
            headers=admin_headers,
        )
        db.refresh(worker_user)
        assert worker_user.onboarding_step == "identity_uploaded"

        # Worker resubmits profile without re-uploading identity (already stored)
        client.post(
            f"{BASE}/worker/onboarding/profile",
            json=_PROFILE_PAYLOAD,
            headers=worker_headers,
        )
        db.refresh(worker_user)
        assert worker_user.onboarding_step == "profile_submitted"

        # Admin approves on second attempt
        r = client.post(
            f"{BASE}/admin/people/workers/{worker_user.id}/approve",
            headers=admin_headers,
        )
        assert r.status_code == 200
        db.refresh(worker_user)
        assert worker_user.onboarding_step == "approved"
