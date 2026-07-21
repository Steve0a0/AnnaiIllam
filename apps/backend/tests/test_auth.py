"""Integration tests for all auth API endpoints via FastAPI TestClient."""
from datetime import timedelta
from unittest.mock import patch

from app.core.config import settings
from app.core.security import decode_token, hash_password
from app.models.refresh_token import RefreshToken
from app.models.otp_code import OtpCode
from app.models.user import User
from app.utils.time import utcnow
from app.utils.validators import normalize_phone

BASE = "/api/v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_otp(db, phone: str, code: str, *, expired=False, used=False, attempts=0):
    """Insert a real OTP record with the given code into the test DB."""
    phone = normalize_phone(phone)
    expires_at = (
        utcnow() - timedelta(minutes=1)
        if expired
        else utcnow() + timedelta(minutes=5)
    )
    otp = OtpCode(
        phone=phone,
        code_hash=hash_password(code),
        purpose="login",
        is_used=used,
        attempts=attempts,
        expires_at=expires_at,
    )
    db.add(otp)
    db.commit()
    return otp


# ---------------------------------------------------------------------------
# Client OTP — request
# ---------------------------------------------------------------------------

class TestClientRequestOtp:
    def test_success_returns_otp_in_local_env(self, client):
        res = client.post(f"{BASE}/auth/client/request-otp", json={"phone": "9111111111"})
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        # OTP is exposed in local env for testing
        assert "otp" in body["data"]
        assert body["data"]["otp"].isdigit()

    def test_invalid_phone_rejected(self, client):
        res = client.post(f"{BASE}/auth/client/request-otp", json={"phone": "abc"})
        assert res.status_code == 422

    def test_too_short_phone_rejected(self, client):
        res = client.post(f"{BASE}/auth/client/request-otp", json={"phone": "12345"})
        assert res.status_code == 422

    def test_missing_phone_rejected(self, client):
        res = client.post(f"{BASE}/auth/client/request-otp", json={})
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# Client OTP — verify (new user creation)
# ---------------------------------------------------------------------------

class TestClientVerifyOtpNewUser:
    def test_creates_user_and_returns_tokens(self, client, db):
        phone = "9222222222"
        req = client.post(f"{BASE}/auth/client/request-otp", json={"phone": phone})
        otp_code = req.json()["data"]["otp"]

        res = client.post(
            f"{BASE}/auth/client/verify-otp",
            json={"phone": phone, "code": otp_code},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["role"] == "client"
        assert data["user"]["phone"] == "+91" + phone

    def test_existing_client_user_returned(self, client, client_user):
        phone = client_user.phone
        req = client.post(f"{BASE}/auth/client/request-otp", json={"phone": phone})
        otp_code = req.json()["data"]["otp"]

        res = client.post(
            f"{BASE}/auth/client/verify-otp",
            json={"phone": phone, "code": otp_code},
        )
        assert res.status_code == 200
        assert res.json()["data"]["user"]["id"] == client_user.id


# ---------------------------------------------------------------------------
# Client OTP — verify error paths
# ---------------------------------------------------------------------------

class TestClientVerifyOtpErrors:
    def test_wrong_otp_code_rejected(self, client, db):
        phone = "9333333333"
        _seed_otp(db, phone, "123456")
        res = client.post(
            f"{BASE}/auth/client/verify-otp",
            json={"phone": phone, "code": "000000"},
        )
        assert res.status_code == 400
        assert "Invalid OTP" in res.json()["message"]

    def test_expired_otp_rejected(self, client, db):
        phone = "9444444444"
        _seed_otp(db, phone, "999999", expired=True)
        res = client.post(
            f"{BASE}/auth/client/verify-otp",
            json={"phone": phone, "code": "999999"},
        )
        assert res.status_code == 400
        assert "expired" in res.json()["message"].lower()

    def test_used_otp_rejected(self, client, db):
        phone = "9555555555"
        _seed_otp(db, phone, "888888", used=True)
        res = client.post(
            f"{BASE}/auth/client/verify-otp",
            json={"phone": phone, "code": "888888"},
        )
        assert res.status_code == 400
        # used OTPs are filtered out by get_latest_active_otp (is_used=False filter)
        # so the endpoint returns "not found" rather than "already used"
        assert "not found" in res.json()["message"].lower()

    def test_no_otp_record_rejected(self, client):
        res = client.post(
            f"{BASE}/auth/client/verify-otp",
            json={"phone": "9666666666", "code": "123456"},
        )
        assert res.status_code == 400
        assert "not found" in res.json()["message"].lower()

    def test_non_numeric_code_rejected(self, client):
        res = client.post(
            f"{BASE}/auth/client/verify-otp",
            json={"phone": "9777777777", "code": "abcdef"},
        )
        assert res.status_code == 422

    def test_max_attempts_exceeded_rejected(self, client, db):
        phone = "9888888881"
        _seed_otp(db, phone, "111111", attempts=5)
        res = client.post(
            f"{BASE}/auth/client/verify-otp",
            json={"phone": phone, "code": "111111"},
        )
        assert res.status_code == 400
        assert "attempts" in res.json()["message"].lower()


# ---------------------------------------------------------------------------
# Worker OTP
# ---------------------------------------------------------------------------

class TestWorkerOtp:
    def test_request_and_verify_creates_worker(self, client, db):
        phone = "9100000001"
        req = client.post(f"{BASE}/auth/worker/request-otp", json={"phone": phone})
        assert req.status_code == 200
        otp_code = req.json()["data"]["otp"]

        res = client.post(
            f"{BASE}/auth/worker/verify-otp",
            json={"phone": phone, "code": otp_code},
        )
        assert res.status_code == 200
        assert res.json()["data"]["user"]["role"] == "worker"

    def test_existing_worker_returned(self, client, worker_user):
        phone = worker_user.phone
        req = client.post(f"{BASE}/auth/worker/request-otp", json={"phone": phone})
        otp_code = req.json()["data"]["otp"]

        res = client.post(
            f"{BASE}/auth/worker/verify-otp",
            json={"phone": phone, "code": otp_code},
        )
        assert res.status_code == 200
        assert res.json()["data"]["user"]["id"] == worker_user.id


# ---------------------------------------------------------------------------
# Role mismatch
# ---------------------------------------------------------------------------

class TestRoleMismatch:
    def test_client_otp_for_worker_phone_rejected(self, client, db, worker_user):
        """A worker's phone number cannot verify via the client OTP endpoint."""
        phone = worker_user.phone
        # Request OTP via worker endpoint so record is seeded
        req = client.post(f"{BASE}/auth/worker/request-otp", json={"phone": phone})
        otp_code = req.json()["data"]["otp"]

        # Verify as client — role mismatch
        res = client.post(
            f"{BASE}/auth/client/verify-otp",
            json={"phone": phone, "code": otp_code},
        )
        assert res.status_code == 400
        assert "mismatch" in res.json()["message"].lower()


# ---------------------------------------------------------------------------
# Admin login
# ---------------------------------------------------------------------------

@patch("app.api.auth.check_rate_limit")  # test login logic, not rate limiting
class TestAdminLogin:
    def test_valid_credentials_return_browser_session(self, _rl, client, admin_user):
        res = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": admin_user.email, "password": "AdminPass123!"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "access_token" in data
        assert "refresh_token" not in data
        assert "csrf_token" in data
        assert data["user"]["role"] == "admin"
        set_cookie = res.headers.get("set-cookie", "")
        assert "admin_refresh_token=" in set_cookie
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie

        token_payload = decode_token(data["access_token"])
        assert (
            token_payload["exp"] - token_payload["iat"]
            == settings.admin_access_token_expire_minutes * 60
        )

    def test_wrong_password_rejected(self, _rl, client, admin_user):
        res = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": admin_user.email, "password": "WrongPass999!"},
        )
        assert res.status_code == 401
        assert "Invalid credentials" in res.json()["message"]

    def test_unknown_email_rejected(self, _rl, client):
        res = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": "nobody@annai-illam.test", "password": "AdminPass123!"},
        )
        assert res.status_code == 401

    def test_non_admin_user_rejected(self, _rl, client, db, client_user):
        """A client-role user cannot log in via the admin endpoint."""
        client_user.password_hash = hash_password("AdminPass123!")
        db.commit()
        res = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": client_user.email, "password": "AdminPass123!"},
        )
        assert res.status_code == 401

    def test_inactive_admin_rejected(self, _rl, client, db, admin_user):
        admin_user.is_active = False
        db.commit()
        res = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": admin_user.email, "password": "AdminPass123!"},
        )
        assert res.status_code == 403
        assert "disabled" in res.json()["message"].lower()

    def test_admin_without_password_hash_rejected(self, _rl, client, db):
        user = User(phone="9000000099", email="nopw@annai-illam.test", role="admin", is_active=True, password_hash=None)
        db.add(user)
        db.commit()
        res = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": "nopw@annai-illam.test", "password": "AdminPass123!"},
        )
        assert res.status_code == 401

    def test_short_password_schema_rejected(self, _rl, client):
        res = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": "any@annai-illam.test", "password": "short"},
        )
        assert res.status_code == 422

    def test_invalid_email_schema_rejected(self, _rl, client):
        res = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": "not-an-email", "password": "AdminPass123!"},
        )
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# Admin browser session: HttpOnly refresh, CSRF, rotation, reuse detection
# ---------------------------------------------------------------------------

@patch("app.api.auth.check_rate_limit")
class TestAdminBrowserSession:
    def _login(self, client, admin_user):
        response = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": admin_user.email, "password": "AdminPass123!"},
        )
        assert response.status_code == 200
        return response.json()["data"]

    def test_refresh_requires_csrf_header(self, _rl, client, admin_user):
        self._login(client, admin_user)
        response = client.post(f"{BASE}/auth/admin/refresh")
        assert response.status_code == 403

    def test_csrf_bootstrap_rejects_untrusted_origin(self, _rl, client, admin_user):
        self._login(client, admin_user)
        response = client.get(
            f"{BASE}/auth/admin/csrf",
            headers={"Origin": "https://attacker.example"},
        )
        assert response.status_code == 403

    def test_refresh_rotates_cookie_without_exposing_it(self, _rl, client, admin_user):
        login = self._login(client, admin_user)
        first_refresh = client.cookies.get("admin_refresh_token")

        response = client.post(
            f"{BASE}/auth/admin/refresh",
            headers={"X-CSRF-Token": login["csrf_token"]},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert "refresh_token" not in data
        assert data["access_token"]
        assert data["user"]["role"] == "admin"
        assert client.cookies.get("admin_refresh_token") != first_refresh

    def test_rotated_token_reuse_revokes_entire_family(self, _rl, client, db, admin_user):
        login = self._login(client, admin_user)
        old_refresh = client.cookies.get("admin_refresh_token")
        response = client.post(
            f"{BASE}/auth/admin/refresh",
            headers={"X-CSRF-Token": login["csrf_token"]},
        )
        assert response.status_code == 200
        newest_refresh = client.cookies.get("admin_refresh_token")
        newest_csrf = response.json()["data"]["csrf_token"]

        client.cookies.set(
            "admin_refresh_token",
            old_refresh,
            domain="testserver.local",
            path=f"{BASE}/auth/admin",
        )
        replay = client.post(
            f"{BASE}/auth/admin/refresh",
            headers={"X-CSRF-Token": newest_csrf},
        )
        assert replay.status_code == 401

        records = list(db.query(RefreshToken).all())
        assert records
        assert all(record.is_revoked for record in records)

        client.cookies.set(
            "admin_refresh_token",
            newest_refresh,
            domain="testserver.local",
            path=f"{BASE}/auth/admin",
        )
        client.cookies.set(
            "admin_csrf_token",
            newest_csrf,
            domain="testserver.local",
            path=f"{BASE}/auth/admin",
        )
        assert client.get(f"{BASE}/auth/admin/csrf").status_code == 401

    def test_logout_clears_cookie_and_revokes_access(self, _rl, client, admin_user):
        login = self._login(client, admin_user)
        response = client.post(
            f"{BASE}/auth/admin/logout",
            headers={
                "Authorization": f"Bearer {login['access_token']}",
                "X-CSRF-Token": login["csrf_token"],
            },
        )
        assert response.status_code == 200
        assert client.cookies.get("admin_refresh_token") is None
        me = client.get(
            f"{BASE}/me",
            headers={"Authorization": f"Bearer {login['access_token']}"},
        )
        assert me.status_code == 401

    def test_untrusted_origin_is_rejected(self, _rl, client, admin_user):
        response = client.post(
            f"{BASE}/auth/admin/login",
            json={"email": admin_user.email, "password": "AdminPass123!"},
            headers={"Origin": "https://attacker.example"},
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Mobile/body token refresh
# ---------------------------------------------------------------------------

@patch("app.api.auth.check_rate_limit")  # test refresh logic, not rate limiting
class TestTokenRefresh:
    def _login(self, client, _admin_user):
        phone = "9555555555"
        request = client.post(f"{BASE}/auth/client/request-otp", json={"phone": phone})
        res = client.post(
            f"{BASE}/auth/client/verify-otp",
            json={"phone": phone, "code": request.json()["data"]["otp"]},
        )
        return res.json()["data"]

    def test_valid_refresh_returns_new_tokens(self, _rl, client, admin_user):
        tokens = self._login(client, admin_user)
        res = client.post(
            f"{BASE}/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert res.status_code == 200
        new_data = res.json()["data"]
        assert "access_token" in new_data
        assert "refresh_token" in new_data
        # Token rotation — new refresh token must differ
        assert new_data["refresh_token"] != tokens["refresh_token"]

    def test_garbage_token_rejected(self, _rl, client):
        res = client.post(
            f"{BASE}/auth/refresh",
            json={"refresh_token": "not.a.real.token"},
        )
        assert res.status_code == 401

    def test_revoked_token_rejected(self, _rl, client, admin_user):
        tokens = self._login(client, admin_user)
        refresh = tokens["refresh_token"]
        # First refresh rotates and revokes the original token
        client.post(f"{BASE}/auth/refresh", json={"refresh_token": refresh})
        # Second use of the same (now-revoked) token must fail
        res = client.post(f"{BASE}/auth/refresh", json={"refresh_token": refresh})
        assert res.status_code == 401

    def test_missing_token_field_rejected(self, _rl, client):
        res = client.post(f"{BASE}/auth/refresh", json={})
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# Logout

class TestLogout:
    def _login(self, client, _admin_user):
        phone = "9666666666"
        # Bypass rate limit — this class is testing logout, not login rate limiting.
        request = client.post(f"{BASE}/auth/client/request-otp", json={"phone": phone})
        res = client.post(
            f"{BASE}/auth/client/verify-otp",
            json={"phone": phone, "code": request.json()["data"]["otp"]},
        )
        return res.json()["data"]

    def test_logout_success(self, client, admin_user):
        tokens = self._login(client, admin_user)
        res = client.post(
            f"{BASE}/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

    def test_logout_twice_is_idempotent(self, client, admin_user):
        tokens = self._login(client, admin_user)
        token = tokens["refresh_token"]
        client.post(f"{BASE}/auth/logout", json={"refresh_token": token})
        res = client.post(f"{BASE}/auth/logout", json={"refresh_token": token})
        assert res.status_code == 200

    def test_refresh_after_logout_rejected(self, client, admin_user):
        tokens = self._login(client, admin_user)
        token = tokens["refresh_token"]
        client.post(f"{BASE}/auth/logout", json={"refresh_token": token})
        res = client.post(f"{BASE}/auth/refresh", json={"refresh_token": token})
        assert res.status_code == 401

    def test_missing_token_rejected(self, client):
        res = client.post(f"{BASE}/auth/logout", json={})
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# Generic OTP endpoints (role in body)
# ---------------------------------------------------------------------------

class TestGenericOtpEndpoints:
    def test_request_otp_with_client_role(self, client):
        res = client.post(
            f"{BASE}/auth/request-otp",
            json={"phone": "9200000001", "role": "client"},
        )
        assert res.status_code == 200

    def test_request_otp_with_worker_role(self, client):
        res = client.post(
            f"{BASE}/auth/request-otp",
            json={"phone": "9200000002", "role": "worker"},
        )
        assert res.status_code == 200

    def test_request_otp_with_admin_role_rejected(self, client):
        res = client.post(
            f"{BASE}/auth/request-otp",
            json={"phone": "9200000003", "role": "admin"},
        )
        # Admin role is not in PUBLIC_OTP_ROLES — endpoint returns 403
        assert res.status_code == 403

    def test_verify_otp_with_role_in_body(self, client):
        phone = "9200000004"
        req = client.post(
            f"{BASE}/auth/request-otp",
            json={"phone": phone, "role": "client"},
        )
        otp_code = req.json()["data"]["otp"]
        res = client.post(
            f"{BASE}/auth/verify-otp",
            json={"phone": phone, "code": otp_code, "role": "client"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["user"]["role"] == "client"


# ---------------------------------------------------------------------------
# Access token blocklist — logout invalidates the access token immediately
# ---------------------------------------------------------------------------

class TestAccessTokenBlocklist:
    """Verify that logout revokes the access token in addition to the refresh token."""

    def _otp_login(self, client, phone: str, role: str = "client") -> dict:
        req = client.post(f"{BASE}/auth/{role}/request-otp", json={"phone": phone})
        otp_code = req.json()["data"]["otp"]
        res = client.post(
            f"{BASE}/auth/{role}/verify-otp",
            json={"phone": phone, "code": otp_code},
        )
        assert res.status_code == 200
        return res.json()["data"]

    def test_access_token_rejected_after_logout(self, client):
        """After logout, the access token must return 401 even within its TTL."""
        phone = "9300000001"
        tokens = self._otp_login(client, phone)
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Confirm the token works before logout
        me_before = client.get(
            f"{BASE}/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_before.status_code == 200

        # Logout — pass both the refresh token body AND the access token header
        logout_res = client.post(
            f"{BASE}/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_res.status_code == 200

        # The same access token must now be rejected
        me_after = client.get(
            f"{BASE}/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_after.status_code == 401

    def test_logout_without_access_token_still_works(self, client):
        """Logout without an Authorization header still revokes the refresh token."""
        phone = "9300000002"
        tokens = self._otp_login(client, phone)

        res = client.post(
            f"{BASE}/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            # No Authorization header
        )
        assert res.status_code == 200

        # Refresh token should now be revoked
        refresh_res = client.post(
            f"{BASE}/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_res.status_code == 401
