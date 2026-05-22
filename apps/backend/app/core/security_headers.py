from fastapi import Request

from app.core.config import settings


async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store"

    # Content-Security-Policy — tight default; docs UI is restricted to local only.
    csp_parts = [
        "default-src 'none'",
        "connect-src 'self'",
        "frame-ancestors 'none'",
    ]
    if settings.is_local:
        # Allow Swagger/ReDoc assets in local dev
        csp_parts += [
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net",
            "img-src 'self' data:",
        ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_parts)

    # HSTS — only meaningful over HTTPS; skip in local HTTP dev to avoid browser caching
    if not settings.is_local:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

    return response
