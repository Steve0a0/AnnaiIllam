"""
SMS gateway abstraction.

In `local` mode (APP_ENV=local) the OTP is returned in the API response and
printed at DEBUG level — no external service is called.

In `staging` / `production` the OTP is sent via Fast2SMS (SMS_PROVIDER=fast2sms,
FAST2SMS_API_KEY) or MSG91 (SMS_PROVIDER=msg91, MSG91_AUTH_KEY).
A stub that raises at WARNING level is used if no provider is configured.

To add another provider implement a new class that inherits `BaseSmsProvider`
and register it in `_get_provider()`.
"""

import logging
from abc import ABC, abstractmethod

import httpx
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger("annai_illam")


# ──────────────────────────────────────────────────────────────────────────────
# Provider interface
# ──────────────────────────────────────────────────────────────────────────────


class BaseSmsProvider(ABC):
    @abstractmethod
    def send_otp(self, phone: str, otp: str) -> None: ...


# ──────────────────────────────────────────────────────────────────────────────
# Concrete providers
# ──────────────────────────────────────────────────────────────────────────────


class Msg91Provider(BaseSmsProvider):
    """
    MSG91 Flow-based OTP send.
    Required env vars: MSG91_AUTH_KEY, MSG91_TEMPLATE_ID
    """

    _API_URL = "https://control.msg91.com/api/v5/otp"

    def send_otp(self, phone: str, otp: str) -> None:
        params = {
            "template_id": settings.msg91_template_id,
            "mobile": f"91{phone}",  # India country code
            "authkey": settings.msg91_auth_key,
            "otp": otp,
        }
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(self._API_URL, params=params)
                resp.raise_for_status()
                logger.info("MSG91 OTP sent | phone=%s | status=%s", phone, resp.status_code)
        except httpx.HTTPStatusError as exc:
            logger.error(
                "MSG91 OTP send failed | phone=%s | status=%s",
                phone,
                exc.response.status_code,
            )
            raise HTTPException(
                status_code=503,
                detail="SMS service temporarily unavailable. Please try again shortly.",
            ) from exc
        except Exception:
            logger.exception("MSG91 OTP send failed | phone=%s", phone)
            raise HTTPException(
                status_code=503,
                detail="SMS service temporarily unavailable. Please try again shortly.",
            )


class Fast2SmsProvider(BaseSmsProvider):
    """
    Fast2SMS Developer/OTP route — no DLT registration required for testing.
    Required env var: FAST2SMS_API_KEY
    Docs: https://www.fast2sms.com/dev/bulkV2 (route=otp)
    """

    _API_URL = "https://www.fast2sms.com/dev/bulkV2"

    def send_otp(self, phone: str, otp: str) -> None:
        headers = {"authorization": settings.fast2sms_api_key}
        params = {
            "variables_values": otp,
            "route": "otp",
            "numbers": phone,
        }
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(self._API_URL, headers=headers, params=params)
                resp.raise_for_status()
                body = resp.json()
                if not body.get("return", False):
                    raise RuntimeError(f"Fast2SMS error: {body.get('message', body)}")
                logger.info("Fast2SMS OTP sent | phone=%s", phone)
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Fast2SMS OTP send failed | phone=%s | status=%s",
                phone,
                exc.response.status_code,
            )
            raise HTTPException(
                status_code=503,
                detail="SMS service temporarily unavailable. Please try again shortly.",
            ) from exc
        except Exception:
            logger.exception("Fast2SMS OTP send failed | phone=%s", phone)
            raise HTTPException(
                status_code=503,
                detail="SMS service temporarily unavailable. Please try again shortly.",
            )


class ConsoleProvider(BaseSmsProvider):
    """
    Development / fallback provider — never sends a real SMS.
    Only enabled in local mode; in any other env this signals a misconfiguration.
    """

    def send_otp(self, phone: str, otp: str) -> None:
        if settings.is_local:
            logger.debug("[DEV] OTP for %s: %s", phone, otp)
        else:
            # In staging/prod with no real provider configured this is a hard error.
            logger.error(
                "SMS_PROVIDER is not configured — OTP NOT delivered | phone=%s", phone
            )
            raise RuntimeError(
                "SMS_PROVIDER is not configured. Set SMS_PROVIDER=msg91 and "
                "MSG91_AUTH_KEY / MSG91_TEMPLATE_ID in your environment."
            )


# ──────────────────────────────────────────────────────────────────────────────
# Provider factory
# ──────────────────────────────────────────────────────────────────────────────


def _get_provider() -> BaseSmsProvider:
    provider = settings.sms_provider.strip().lower()
    if provider == "fast2sms":
        if not settings.fast2sms_api_key:
            raise RuntimeError("SMS_PROVIDER=fast2sms but FAST2SMS_API_KEY is missing.")
        return Fast2SmsProvider()
    if provider == "msg91":
        if not settings.msg91_auth_key or not settings.msg91_template_id:
            raise RuntimeError(
                "SMS_PROVIDER=msg91 but MSG91_AUTH_KEY or MSG91_TEMPLATE_ID is missing."
            )
        return Msg91Provider()
    # 'console' or blank — allowed only in local env
    return ConsoleProvider()


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────


def send_otp_sms(phone: str, otp: str) -> None:
    """
    Send an OTP to `phone`.  Never exposes the OTP in non-local environments.
    Raises on send failure so the caller can return an appropriate error.
    """
    _get_provider().send_otp(phone, otp)
