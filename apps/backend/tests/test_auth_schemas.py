"""Unit tests for auth Pydantic schemas — no DB, no HTTP."""
import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    AdminLoginSchema,
    OtpRequestSchema,
    OtpVerifySchema,
    PhoneOtpRequestSchema,
    PhoneOtpVerifySchema,
    RefreshTokenSchema,
)


# ---------------------------------------------------------------------------
# PhoneOtpRequestSchema
# ---------------------------------------------------------------------------

class TestPhoneOtpRequestSchema:
    def test_valid_phone(self):
        schema = PhoneOtpRequestSchema(phone="9876543210")
        assert schema.phone == "+919876543210"

    def test_strips_spaces(self):
        schema = PhoneOtpRequestSchema(phone=" 9876543210 ")
        assert schema.phone == "+919876543210"

    def test_too_short_raises(self):
        with pytest.raises(ValidationError):
            PhoneOtpRequestSchema(phone="123")

    def test_non_digits_raises(self):
        with pytest.raises(ValidationError):
            PhoneOtpRequestSchema(phone="98765abcde")

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            PhoneOtpRequestSchema(phone="9876543210", extra_field="bad")


# ---------------------------------------------------------------------------
# PhoneOtpVerifySchema
# ---------------------------------------------------------------------------

class TestPhoneOtpVerifySchema:
    def test_valid(self):
        schema = PhoneOtpVerifySchema(phone="9876543210", code="123456")
        assert schema.code == "123456"

    def test_strips_code_whitespace(self):
        schema = PhoneOtpVerifySchema(phone="9876543210", code=" 123456 ")
        assert schema.code == "123456"

    def test_non_numeric_code_raises(self):
        with pytest.raises(ValidationError):
            PhoneOtpVerifySchema(phone="9876543210", code="12ab56")

    def test_code_too_short_raises(self):
        with pytest.raises(ValidationError):
            PhoneOtpVerifySchema(phone="9876543210", code="123")

    def test_code_too_long_raises(self):
        with pytest.raises(ValidationError):
            PhoneOtpVerifySchema(phone="9876543210", code="12345678901")


# ---------------------------------------------------------------------------
# OtpRequestSchema (with role)
# ---------------------------------------------------------------------------

class TestOtpRequestSchema:
    def test_valid_client_role(self):
        schema = OtpRequestSchema(phone="9876543210", role="client")
        assert schema.role == "client"

    def test_valid_worker_role(self):
        schema = OtpRequestSchema(phone="9876543210", role="worker")
        assert schema.role == "worker"

    def test_role_normalised_lowercase(self):
        schema = OtpRequestSchema(phone="9876543210", role="CLIENT")
        assert schema.role == "client"

    def test_invalid_role_raises(self):
        with pytest.raises(ValidationError):
            OtpRequestSchema(phone="9876543210", role="superuser")

    def test_admin_role_is_schema_valid_but_endpoint_restricted(self):
        schema = OtpRequestSchema(phone="9876543210", role="admin")
        assert schema.role == "admin"


# ---------------------------------------------------------------------------
# OtpVerifySchema (with role)
# ---------------------------------------------------------------------------

class TestOtpVerifySchema:
    def test_valid(self):
        schema = OtpVerifySchema(phone="9876543210", code="654321", role="worker")
        assert schema.role == "worker"

    def test_invalid_role_raises(self):
        with pytest.raises(ValidationError):
            OtpVerifySchema(phone="9876543210", code="654321", role="ghost")


# ---------------------------------------------------------------------------
# AdminLoginSchema
# ---------------------------------------------------------------------------

class TestAdminLoginSchema:
    def test_valid(self):
        schema = AdminLoginSchema(email="admin@example.com", password="SecurePass123!")
        assert schema.email == "admin@example.com"

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError):
            AdminLoginSchema(email="admin@example.com", password="short")

    def test_password_too_long_raises(self):
        with pytest.raises(ValidationError):
            AdminLoginSchema(email="admin@example.com", password="x" * 129)

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            AdminLoginSchema(email="not-an-email", password="SecurePass123!")

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            AdminLoginSchema(email="admin@example.com", password="SecurePass123!", role="admin")


# ---------------------------------------------------------------------------
# RefreshTokenSchema
# ---------------------------------------------------------------------------

class TestRefreshTokenSchema:
    def test_valid(self):
        schema = RefreshTokenSchema(refresh_token="some.jwt.token")
        assert schema.refresh_token == "some.jwt.token"

    def test_missing_token_raises(self):
        with pytest.raises(ValidationError):
            RefreshTokenSchema()

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            RefreshTokenSchema(refresh_token="tok", extra="bad")
