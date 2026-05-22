"""Unit tests for app.core.security — pure functions, no DB required."""
from unittest.mock import patch

import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_numeric_otp,
    hash_password,
    hash_value,
    verify_password,
)


# ---------------------------------------------------------------------------
# hash_value
# ---------------------------------------------------------------------------

class TestHashValue:
    def test_returns_sha256_hex(self):
        result = hash_value("hello")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        assert hash_value("abc") == hash_value("abc")

    def test_different_inputs_differ(self):
        assert hash_value("abc") != hash_value("xyz")

    def test_empty_string(self):
        result = hash_value("")
        assert len(result) == 64


# ---------------------------------------------------------------------------
# hash_password / verify_password
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        pw = "SecurePass123!"
        assert hash_password(pw) != pw

    def test_verify_correct_password(self):
        pw = "SecurePass123!"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_bcrypt_salts_differ(self):
        pw = "same"
        assert hash_password(pw) != hash_password(pw)

    def test_verify_after_re_hash(self):
        pw = "reused"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert verify_password(pw, h1) is True
        assert verify_password(pw, h2) is True


# ---------------------------------------------------------------------------
# generate_numeric_otp
# ---------------------------------------------------------------------------

class TestGenerateNumericOtp:
    def test_default_length(self):
        otp = generate_numeric_otp()
        assert len(otp) == 6

    def test_custom_length(self):
        assert len(generate_numeric_otp(4)) == 4
        assert len(generate_numeric_otp(8)) == 8

    def test_only_digits(self):
        for _ in range(20):
            assert generate_numeric_otp().isdigit()

    def test_randomness(self):
        otps = {generate_numeric_otp() for _ in range(50)}
        # With 10^6 combinations, 50 draws should almost never all be the same
        assert len(otps) > 1


# ---------------------------------------------------------------------------
# create_access_token / create_refresh_token / decode_token
# ---------------------------------------------------------------------------

class TestTokenCreation:
    def test_access_token_payload(self):
        token = create_access_token("9876543210", "admin", 42)
        payload = decode_token(token)
        assert payload["sub"] == "9876543210"
        assert payload["role"] == "admin"
        assert payload["user_id"] == 42
        assert payload["type"] == "access"

    def test_refresh_token_payload(self):
        token = create_refresh_token("9876543210", "client", 7)
        payload = decode_token(token)
        assert payload["sub"] == "9876543210"
        assert payload["role"] == "client"
        assert payload["user_id"] == 7
        assert payload["type"] == "refresh"
        assert "jti" in payload

    def test_refresh_tokens_have_unique_jti(self):
        t1 = create_refresh_token("1111111111", "worker", 1)
        t2 = create_refresh_token("1111111111", "worker", 1)
        p1 = decode_token(t1)
        p2 = decode_token(t2)
        assert p1["jti"] != p2["jti"]

    def test_access_token_expiry_set(self):
        token = create_access_token("1234567890", "admin", 1)
        payload = decode_token(token)
        assert payload["exp"] > payload["iat"]

    def test_decode_invalid_token_raises(self):
        with pytest.raises(jwt.InvalidTokenError):
            decode_token("not.a.valid.jwt")

    def test_decode_tampered_token_raises(self):
        token = create_access_token("9999999999", "admin", 99)
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(jwt.InvalidTokenError):
            decode_token(tampered)

    def test_expired_token_raises(self):
        with patch("app.core.security.timedelta") as mock_td:
            from datetime import timedelta
            mock_td.return_value = timedelta(seconds=-1)
            token = create_access_token("1234567890", "admin", 1)

        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(token)
