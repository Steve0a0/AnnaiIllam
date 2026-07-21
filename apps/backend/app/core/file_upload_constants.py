"""Authoritative worker KYC upload rules shared by API and storage code."""

MIB = 1024 * 1024
MIN_DOCUMENT_SIZE_BYTES = 16
MAGIC_BYTES_READ_LENGTH = 16

GOVT_ID_MAX_SIZE_BYTES = 10 * MIB
SELFIE_MAX_SIZE_BYTES = 5 * MIB

IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
ALLOWED_DOCUMENT_MIME_TYPES = frozenset({*IMAGE_MIME_TYPES, "application/pdf"})
ALLOWED_DOCUMENT_EXTENSIONS = frozenset({".pdf", ".jpg", ".jpeg", ".png", ".webp"})
ALLOWED_DOCUMENT_TYPES = frozenset({"govt_id", "selfie"})

DOCUMENT_MIME_TYPES = {
    "govt_id": ALLOWED_DOCUMENT_MIME_TYPES,
    "selfie": IMAGE_MIME_TYPES,
}
DOCUMENT_MAX_SIZE_BYTES = {
    "govt_id": GOVT_ID_MAX_SIZE_BYTES,
    "selfie": SELFIE_MAX_SIZE_BYTES,
}
MIME_TYPE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "application/pdf": "pdf",
}


def normalize_content_type(content_type: str) -> str:
    return content_type.split(";", 1)[0].strip().lower()


def detect_content_type(prefix: bytes) -> str | None:
    """Detect the supported format from its signature, never its filename."""
    if prefix.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if prefix.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(prefix) >= 12 and prefix.startswith(b"RIFF") and prefix[8:12] == b"WEBP":
        return "image/webp"
    if prefix.startswith(b"%PDF-"):
        return "application/pdf"
    return None


def validate_upload_declaration(document_type: str, content_type: str, size: int) -> str:
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValueError("Unsupported document type")
    normalized = normalize_content_type(content_type)
    if normalized not in DOCUMENT_MIME_TYPES[document_type]:
        raise ValueError(f"Unsupported content type for {document_type}")
    if size < MIN_DOCUMENT_SIZE_BYTES:
        raise ValueError("Uploaded document is empty or too small")
    if size > DOCUMENT_MAX_SIZE_BYTES[document_type]:
        raise ValueError(f"{document_type} exceeds the maximum allowed size")
    return normalized
