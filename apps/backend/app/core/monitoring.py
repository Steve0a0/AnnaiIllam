from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.core.logging import logger

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
except ImportError:  # pragma: no cover - exercised only when optional dep is absent
    sentry_sdk = None
    FastApiIntegration = None
    SqlalchemyIntegration = None
    StarletteIntegration = None


_SENSITIVE_HEADER_NAMES = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "x-csrf-token",
}


def _scrub_sensitive_request_data(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    request = event.get("request")
    if isinstance(request, dict):
        headers = request.get("headers")
        if isinstance(headers, dict):
            for key in list(headers):
                if key.lower() in _SENSITIVE_HEADER_NAMES:
                    headers[key] = "[Filtered]"

        if "cookies" in request:
            request["cookies"] = "[Filtered]"

    return event


def init_sentry() -> None:
    if not settings.sentry_dsn:
        return

    if sentry_sdk is None:
        logger.warning("SENTRY_DSN is configured but sentry-sdk is not installed")
        return

    integrations = []
    if FastApiIntegration is not None:
        integrations.append(FastApiIntegration())
    if StarletteIntegration is not None:
        integrations.append(StarletteIntegration())
    if SqlalchemyIntegration is not None:
        integrations.append(SqlalchemyIntegration())

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment or settings.app_env,
        release=settings.sentry_release or None,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        send_default_pii=False,
        before_send=_scrub_sensitive_request_data,
        integrations=integrations,
    )


def capture_exception(exc: BaseException) -> None:
    if sentry_sdk is None or not settings.sentry_dsn:
        return
    sentry_sdk.capture_exception(exc)
