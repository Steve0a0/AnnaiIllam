"""
Field-level encryption using Fernet (AES-128-CBC + HMAC-SHA256).
Used for sensitive PII fields: UPI ID, bank account number, IFSC code.

Key must be a URL-safe base64-encoded 32-byte value.
Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
Store in .env as FIELD_ENCRYPTION_KEY and in production in AWS Secrets Manager / Azure Key Vault.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _get_fernet() -> Fernet:
    key = settings.field_encryption_key
    if not key:
        raise RuntimeError("FIELD_ENCRYPTION_KEY is not configured")
    return Fernet(key.encode())


def encrypt_field(value: str) -> str:
    """Encrypt a plaintext string. Returns a base64-encoded ciphertext string."""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_field(ciphertext: str) -> str:
    """Decrypt a ciphertext string produced by encrypt_field. Raises ValueError on bad data."""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Could not decrypt field — key mismatch or data corrupted") from exc


def encrypt_optional(value: str | None) -> str | None:
    """Encrypt if value is present, otherwise return None."""
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return encrypt_field(stripped)


def decrypt_optional(ciphertext: str | None) -> str | None:
    """Decrypt if value is present, otherwise return None."""
    if ciphertext is None:
        return None
    return decrypt_field(ciphertext)
