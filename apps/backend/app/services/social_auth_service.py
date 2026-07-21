import time
from dataclasses import dataclass
from typing import Literal

import httpx
import jwt

from app.core.config import settings

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"


@dataclass
class SocialIdentity:
    provider: Literal["google", "apple"]
    provider_id: str
    email: str
    name: str | None


async def verify_google_token(id_token: str) -> SocialIdentity:
    if not settings.google_auth_enabled:
        raise ValueError("Google sign-in is disabled")
    valid_audiences = settings.google_audiences
    if not valid_audiences:
        raise ValueError("Google sign-in audience is not configured")

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})

    if resp.status_code != 200:
        raise ValueError("Google token verification failed")

    claims = resp.json()

    if "error" in claims:
        raise ValueError(f"Invalid Google token: {claims.get('error_description', 'unknown error')}")

    # Validate audience is one of our registered client IDs (web, iOS, or Android).
    # The 'aud' claim equals whichever client ID was used on the device.
    if claims.get("aud") not in valid_audiences:
        raise ValueError("Google token audience mismatch")

    exp = int(claims.get("exp", 0))
    if exp < int(time.time()):
        raise ValueError("Google token has expired")

    email = claims.get("email")
    if not email:
        raise ValueError("Google token missing email claim")

    email_verified = claims.get("email_verified") in ("true", True)
    if not email_verified:
        raise ValueError("Google account email is not verified")

    name = claims.get("name") or claims.get("given_name")

    return SocialIdentity(
        provider="google",
        provider_id=claims["sub"],
        email=email.lower().strip(),
        name=name,
    )


async def verify_apple_token(identity_token: str) -> SocialIdentity:
    if not settings.apple_auth_enabled:
        raise ValueError("Apple sign-in is disabled")
    audience = settings.apple_app_bundle_id.strip()
    if not audience:
        raise ValueError("Apple sign-in audience is not configured")

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(APPLE_KEYS_URL)

    if resp.status_code != 200:
        raise ValueError("Failed to fetch Apple public keys")

    jwks = resp.json()

    # Decode the header without verification to get the key ID
    try:
        header = jwt.get_unverified_header(identity_token)
    except jwt.DecodeError as exc:
        raise ValueError("Invalid Apple identity token format") from exc

    kid = header.get("kid")
    if not kid:
        raise ValueError("Apple token missing key ID")

    # Find the matching key
    matching_key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if not matching_key:
        raise ValueError("Apple public key not found for kid")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(matching_key)

    try:
        claims = jwt.decode(
            identity_token,
            public_key,
            algorithms=["RS256"],
            audience=audience,
            issuer=APPLE_ISSUER,
        )
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Apple identity token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Apple identity token validation failed: {exc}") from exc

    email = claims.get("email")
    if not email:
        raise ValueError("Apple token missing email claim")

    return SocialIdentity(
        provider="apple",
        provider_id=claims["sub"],
        email=email.lower().strip(),
        name=None,  # Apple only provides name on the very first sign-in (handled on client)
    )
