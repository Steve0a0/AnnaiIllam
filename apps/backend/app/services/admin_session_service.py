import hashlib
import hmac
import secrets
from urllib.parse import urlsplit

from fastapi import HTTPException, Request, Response, status

from app.core.config import settings


ADMIN_REFRESH_COOKIE = "admin_refresh_token"
ADMIN_CSRF_COOKIE = "admin_csrf_token"
ADMIN_CSRF_HEADER = "X-CSRF-Token"


def _cookie_path() -> str:
    return f"{settings.api_v1_prefix}/auth/admin"


def _cookie_secure() -> bool:
    return not settings.is_local


def issue_csrf_token(family_id: str) -> str:
    nonce = secrets.token_urlsafe(32)
    signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        f"{family_id}:{nonce}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{nonce}.{signature}"


def validate_csrf_token(
    *, family_id: str, cookie_token: str | None, header_token: str | None
) -> None:
    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")

    try:
        nonce, supplied_signature = header_token.rsplit(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token") from exc

    expected_signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        f"{family_id}:{nonce}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(supplied_signature, expected_signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")


def require_allowed_admin_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin:
        referer = request.headers.get("referer")
        if referer:
            parsed = urlsplit(referer)
            origin = f"{parsed.scheme}://{parsed.netloc}"

    # Test clients and local non-browser tools do not always send Origin.
    if not origin and settings.is_local:
        return
    if not origin or origin not in settings.backend_cors_origins_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origin not allowed")


def set_admin_session_cookies(
    response: Response,
    *,
    refresh_token: str,
    csrf_token: str,
) -> None:
    max_age = settings.refresh_token_expire_days * 24 * 60 * 60
    common = {
        "secure": _cookie_secure(),
        "samesite": "lax",
        "path": _cookie_path(),
        "max_age": max_age,
    }
    response.set_cookie(
        ADMIN_REFRESH_COOKIE,
        refresh_token,
        httponly=True,
        **common,
    )
    response.set_cookie(
        ADMIN_CSRF_COOKIE,
        csrf_token,
        httponly=False,
        **common,
    )


def clear_admin_session_cookies(response: Response) -> None:
    response.delete_cookie(ADMIN_REFRESH_COOKIE, path=_cookie_path())
    response.delete_cookie(ADMIN_CSRF_COOKIE, path=_cookie_path())
