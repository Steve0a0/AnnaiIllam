"""Fail-closed social authentication regression tests."""

import time

import jwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.services import social_auth_service


class _Response:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload


class _AsyncClient:
    def __init__(self, response: _Response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def get(self, *_args, **_kwargs):
        return self.response


def _settings(**overrides) -> Settings:
    values = {
        "database_url": "sqlite:///:memory:",
        "redis_url": "redis://localhost:6379/15",
        "jwt_secret_key": "test-secret-key-for-testing-only-min-32chars",
        "app_env": "local",
        "google_auth_enabled": False,
        "google_client_id": "",
        "google_ios_client_id": "",
        "google_android_client_id": "",
        "apple_auth_enabled": False,
        "apple_app_bundle_id": "",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_enabled_google_without_any_audience_refuses_startup():
    with pytest.raises(ValidationError, match="GOOGLE_AUTH_ENABLED"):
        _settings(google_auth_enabled=True)


def test_enabled_apple_without_audience_refuses_startup():
    with pytest.raises(ValidationError, match="APPLE_AUTH_ENABLED"):
        _settings(apple_auth_enabled=True)


@pytest.mark.parametrize("provider", ["google", "apple"])
def test_disabled_provider_route_rejects_without_verification(
    provider, client, monkeypatch
):
    monkeypatch.setattr(settings, "google_auth_enabled", False)
    monkeypatch.setattr(settings, "apple_auth_enabled", False)
    monkeypatch.setattr("app.api.auth_social.check_rate_limit", lambda *_args, **_kwargs: None)
    response = client.post(
        "/api/v1/auth/client/social",
        json={"provider": provider, "id_token": "disabled-provider-token"},
    )
    assert response.status_code == 400
    assert "disabled" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_disabled_google_rejects_before_network(monkeypatch):
    monkeypatch.setattr(settings, "google_auth_enabled", False)

    class _UnexpectedClient:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("disabled provider must not make a network request")

    monkeypatch.setattr(social_auth_service.httpx, "AsyncClient", _UnexpectedClient)
    with pytest.raises(ValueError, match="disabled"):
        await social_auth_service.verify_google_token("unused-token")


@pytest.mark.asyncio
async def test_google_token_for_another_app_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "google_auth_enabled", True)
    monkeypatch.setattr(settings, "google_client_id", "our-web-client.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_ios_client_id", "")
    monkeypatch.setattr(settings, "google_android_client_id", "")
    response = _Response(
        {
            "sub": "google-user-1",
            "aud": "attacker-app.apps.googleusercontent.com",
            "exp": str(int(time.time()) + 300),
            "email": "worker@example.test",
            "email_verified": "true",
        }
    )
    monkeypatch.setattr(
        social_auth_service.httpx,
        "AsyncClient",
        lambda **_kwargs: _AsyncClient(response),
    )

    with pytest.raises(ValueError, match="audience mismatch"):
        await social_auth_service.verify_google_token("token-for-another-app")


@pytest.mark.asyncio
async def test_google_token_for_registered_app_is_accepted(monkeypatch):
    audience = "our-ios-client.apps.googleusercontent.com"
    monkeypatch.setattr(settings, "google_auth_enabled", True)
    monkeypatch.setattr(settings, "google_client_id", "")
    monkeypatch.setattr(settings, "google_ios_client_id", audience)
    monkeypatch.setattr(settings, "google_android_client_id", "")
    response = _Response(
        {
            "sub": "google-user-2",
            "aud": audience,
            "exp": str(int(time.time()) + 300),
            "email": "Client@Example.Test",
            "email_verified": True,
            "name": "Test Client",
        }
    )
    monkeypatch.setattr(
        social_auth_service.httpx,
        "AsyncClient",
        lambda **_kwargs: _AsyncClient(response),
    )

    identity = await social_auth_service.verify_google_token("valid-token")
    assert identity.provider_id == "google-user-2"
    assert identity.email == "client@example.test"


@pytest.mark.asyncio
async def test_disabled_apple_rejects_before_network(monkeypatch):
    monkeypatch.setattr(settings, "apple_auth_enabled", False)

    class _UnexpectedClient:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("disabled provider must not make a network request")

    monkeypatch.setattr(social_auth_service.httpx, "AsyncClient", _UnexpectedClient)
    with pytest.raises(ValueError, match="disabled"):
        await social_auth_service.verify_apple_token("unused-token")


@pytest.mark.asyncio
async def test_apple_token_for_another_app_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "apple_auth_enabled", True)
    monkeypatch.setattr(settings, "apple_app_bundle_id", "com.annaiillam.client")
    monkeypatch.setattr(
        social_auth_service.httpx,
        "AsyncClient",
        lambda **_kwargs: _AsyncClient(_Response({"keys": [{"kid": "key-1"}]})),
    )
    monkeypatch.setattr(jwt, "get_unverified_header", lambda _token: {"kid": "key-1"})
    monkeypatch.setattr(jwt.algorithms.RSAAlgorithm, "from_jwk", lambda _key: object())

    def _reject_wrong_audience(*_args, **kwargs):
        assert kwargs["audience"] == "com.annaiillam.client"
        raise jwt.InvalidAudienceError("Audience doesn't match")

    monkeypatch.setattr(jwt, "decode", _reject_wrong_audience)
    with pytest.raises(ValueError, match="validation failed"):
        await social_auth_service.verify_apple_token("token-for-another-app")
