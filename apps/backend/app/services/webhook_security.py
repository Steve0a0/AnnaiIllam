import hashlib
import hmac


def verify_webhook_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
