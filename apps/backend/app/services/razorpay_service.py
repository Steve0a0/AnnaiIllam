"""
Razorpay payment gateway integration.

Uses httpx (already a project dependency) to call the Razorpay REST API
directly, avoiding the official razorpay Python SDK which requires
pkg_resources and is incompatible with Python 3.13 + setuptools ≥ 80.

Responsibilities:
- Create a Razorpay order (called when client initiates a gateway payment)
- Verify the payment signature from the frontend callback (key_secret based)
- Verify the webhook signature from Razorpay server events (webhook_secret based)

Environment variables required (staging/production):
  RAZORPAY_KEY_ID      — Razorpay API key ID  (starts with rzp_live_ or rzp_test_)
  RAZORPAY_KEY_SECRET  — Razorpay API key secret
  PAYMENT_WEBHOOK_SECRET — Razorpay webhook secret (set in Razorpay Dashboard → Webhooks)
"""

import hashlib
import hmac
import logging
from urllib.parse import quote

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_RAZORPAY_API_BASE = "https://api.razorpay.com/v1"
_REQUEST_TIMEOUT = 15.0  # seconds


def create_order(amount_rupees: int, receipt: str, notes: dict | None = None) -> dict:
    """Create a Razorpay order via the REST API.

    Args:
        amount_rupees: Amount in whole rupees (converted to paise internally).
        receipt:       Our internal reference (≤ 40 chars; truncated if longer).
        notes:         Optional key-value metadata attached to the Razorpay order.

    Returns:
        Razorpay order dict — ``{"id": "order_xxx", "amount": ..., ...}``

    Raises:
        httpx.HTTPStatusError: Non-2xx response from Razorpay (e.g. bad credentials).
        httpx.RequestError:    Network-level failure (timeout, DNS, etc.).
    """
    response = httpx.post(
        f"{_RAZORPAY_API_BASE}/orders",
        auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
        json={
            "amount": amount_rupees * 100,  # paise
            "currency": "INR",
            "receipt": receipt[:40],  # Razorpay max receipt length is 40 chars
            "notes": notes or {},
        },
        timeout=_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    order = response.json()
    logger.info("Razorpay order created | order_id=%s receipt=%s", order.get("id"), receipt)
    return order


def fetch_payment(razorpay_payment_id: str) -> dict:
    """Fetch authoritative payment facts used by the checkout callback."""
    payment_id = quote(razorpay_payment_id, safe="")
    response = httpx.get(
        f"{_RAZORPAY_API_BASE}/payments/{payment_id}",
        auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
        timeout=_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def verify_payment_signature(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> bool:
    """Verify the signature sent to the frontend after a successful checkout.

    Razorpay generates: HMAC-SHA256(order_id + "|" + payment_id, key_secret)
    """
    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected = hmac.new(
        settings.razorpay_key_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, razorpay_signature)


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify the X-Razorpay-Signature header on inbound webhook events.

    Uses PAYMENT_WEBHOOK_SECRET (configured in Razorpay Dashboard → Webhooks).
    Returns False rather than raising if the webhook secret is not configured.
    """
    if not settings.payment_webhook_secret:
        return False
    expected = hmac.new(
        settings.payment_webhook_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
