"""
Document storage service.

Production uses private S3 with presigned upload/download URLs. Local
development uses the backend filesystem so worker identity documents can be
reviewed from the admin dashboard without any paid storage service.
"""

import os
from pathlib import Path
import re
import uuid

from app.core.config import settings
from app.core.file_upload_constants import (
    ALLOWED_DOCUMENT_EXTENSIONS,
    ALLOWED_DOCUMENT_TYPES,
    DOCUMENT_MIME_TYPES,
    MAGIC_BYTES_READ_LENGTH,
    MIME_TYPE_EXTENSIONS,
    detect_content_type,
    normalize_content_type,
    validate_upload_declaration,
)


_LOCAL_DOCUMENT_TYPE_PATTERN = '|'.join(
    re.escape(value) for value in sorted(ALLOWED_DOCUMENT_TYPES)
)
_LOCAL_DOCUMENT_EXTENSION_PATTERN = '|'.join(
    re.escape(value.removeprefix('.'))
    for value in sorted(ALLOWED_DOCUMENT_EXTENSIONS)
)
_LOCAL_DOCUMENT_KEY_PATTERN = re.compile(
    rf'\Aworker-documents/'
    rf'(?P<user_id>[1-9][0-9]*)/'
    rf'(?P<document_type>{_LOCAL_DOCUMENT_TYPE_PATTERN})/'
    rf'(?P<object_id>[0-9a-f]{{32}})\.'
    rf'(?P<extension>{_LOCAL_DOCUMENT_EXTENSION_PATTERN})\Z'
)


class DocumentUploadValidationError(ValueError):
    """A stored object cannot be activated as a worker document."""


def _expected_key_prefix(user_id: int, document_type: str) -> str:
    return f"workers/{user_id}/{document_type}/"


def _expected_local_key_prefix(user_id: int, document_type: str) -> str:
    return f"worker-documents/{user_id}/{document_type}/"


def _validate_s3_key(key: str, user_id: int, document_type: str) -> None:
    prefix = _expected_key_prefix(user_id, document_type)
    suffixes = "|".join(MIME_TYPE_EXTENSIONS.values())
    pattern = rf"^{re.escape(prefix)}[0-9a-f]{{32}}\.({suffixes})$"
    if not re.fullmatch(pattern, key):
        raise DocumentUploadValidationError(
            "Object key is not owned by this user and document type"
        )


def _get_s3_client(*, public_endpoint: bool = False):
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 is not installed. Add it to requirements.txt.") from exc

    kwargs = dict(
        region_name=settings.s3_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    endpoint_url = settings.s3_endpoint_url
    if public_endpoint and settings.s3_public_endpoint_url:
        endpoint_url = settings.s3_public_endpoint_url
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.client("s3", **kwargs)


def _is_aws() -> bool:
    return not bool(settings.s3_endpoint_url)


def is_s3_configured() -> bool:
    return bool(
        settings.s3_bucket
        and settings.aws_access_key_id
        and settings.aws_secret_access_key
    )


def generate_upload_url(
    user_id: int,
    document_type: str,
    content_type: str,
    content_length: int,
    expires_in: int = 300,
) -> tuple[str, str, dict[str, str]]:
    content_type = validate_upload_declaration(
        document_type, content_type, content_length
    )
    ext = MIME_TYPE_EXTENSIONS[content_type]
    s3_key = f"workers/{user_id}/{document_type}/{uuid.uuid4().hex}.{ext}"

    s3 = _get_s3_client(public_endpoint=True)

    put_params: dict = {
        "Bucket": settings.s3_bucket,
        "Key": s3_key,
        "ContentType": content_type,
        "ContentLength": content_length,
        "Metadata": {
            "user-id": str(user_id),
            "document-type": document_type,
        },
    }
    if _is_aws():
        put_params["ServerSideEncryption"] = "aws:kms"

    url = s3.generate_presigned_url(
        "put_object",
        Params=put_params,
        ExpiresIn=expires_in,
        HttpMethod="PUT",
    )

    return url, s3_key, {
        "Content-Type": content_type,
        "x-amz-meta-user-id": str(user_id),
        "x-amz-meta-document-type": document_type,
    }


def validate_stored_document(
    *, s3_key: str, user_id: int, document_type: str
) -> tuple[int, str]:
    """Validate ownership, metadata, length, declared MIME, and magic bytes."""
    _validate_s3_key(s3_key, user_id, document_type)
    s3 = _get_s3_client()
    try:
        head = s3.head_object(Bucket=settings.s3_bucket, Key=s3_key)
    except Exception as exc:
        response = getattr(exc, "response", {})
        code = str(response.get("Error", {}).get("Code", ""))
        if code in {"404", "NoSuchKey", "NotFound"}:
            raise DocumentUploadValidationError("Uploaded object does not exist") from exc
        raise RuntimeError("Unable to inspect uploaded object") from exc

    size = int(head.get("ContentLength", 0))
    content_type = normalize_content_type(str(head.get("ContentType", "")))
    try:
        validate_upload_declaration(document_type, content_type, size)
    except ValueError as exc:
        raise DocumentUploadValidationError(str(exc)) from exc

    metadata = {str(key).lower(): str(value) for key, value in head.get("Metadata", {}).items()}
    if metadata.get("user-id") != str(user_id) or metadata.get("document-type") != document_type:
        raise DocumentUploadValidationError("Uploaded object metadata does not match its owner and type")

    try:
        response = s3.get_object(
            Bucket=settings.s3_bucket,
            Key=s3_key,
            Range=f"bytes=0-{MAGIC_BYTES_READ_LENGTH - 1}",
        )
        prefix = response["Body"].read(MAGIC_BYTES_READ_LENGTH)
    except Exception as exc:
        raise RuntimeError("Unable to inspect uploaded object content") from exc
    detected = detect_content_type(prefix)
    if detected != content_type:
        raise DocumentUploadValidationError("File content does not match its content type")
    return size, content_type


def generate_download_url(s3_key: str, expires_in: int = 900) -> str:
    s3 = _get_s3_client(public_endpoint=True)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": s3_key},
        ExpiresIn=expires_in,
    )


def build_public_s3_url(s3_key: str) -> str:
    if settings.s3_public_endpoint_url:
        return (
            f"{settings.s3_public_endpoint_url.rstrip('/')}/"
            f"{settings.s3_bucket}/{s3_key}"
        )
    return f"https://{settings.s3_bucket}.s3.{settings.s3_region}.amazonaws.com/{s3_key}"


def get_local_upload_root() -> Path:
    root = Path(settings.local_upload_dir)
    if not root.is_absolute():
        root = Path.cwd() / root
    return root.resolve()


def save_local_document(
    *,
    user_id: int,
    document_type: str,
    filename: str,
    content_type: str,
    content: bytes,
) -> tuple[str, str]:
    del filename  # the key extension is derived from verified bytes, not client input
    content_type = validate_upload_declaration(document_type, content_type, len(content))
    detected = detect_content_type(content[:MAGIC_BYTES_READ_LENGTH])
    if detected != content_type:
        raise DocumentUploadValidationError("File content does not match its content type")
    suffix = MIME_TYPE_EXTENSIONS[content_type]
    local_key = f"worker-documents/{user_id}/{document_type}/{uuid.uuid4().hex}.{suffix}"
    destination = get_local_upload_root() / local_key
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return f"local:{local_key}", str(destination)


def validate_local_document(
    *, local_key: str, user_id: int, document_type: str
) -> tuple[int, str]:
    if not local_key.startswith("local:"):
        raise DocumentUploadValidationError("Local document reference is invalid")
    relative_key = local_key.removeprefix("local:")
    if not relative_key.startswith(_expected_local_key_prefix(user_id, document_type)):
        raise DocumentUploadValidationError(
            "Local object key is not owned by this user and document type"
        )
    path = resolve_local_document_path(local_key)
    if not path.is_file():
        raise DocumentUploadValidationError("Uploaded object does not exist")
    size = path.stat().st_size
    with path.open("rb") as source:
        prefix = source.read(MAGIC_BYTES_READ_LENGTH)
    detected = detect_content_type(prefix)
    if detected is None:
        raise DocumentUploadValidationError("Unsupported file content")
    try:
        validate_upload_declaration(document_type, detected, size)
    except ValueError as exc:
        raise DocumentUploadValidationError(str(exc)) from exc
    expected_extension = MIME_TYPE_EXTENSIONS[detected]
    if path.suffix.lower() != f".{expected_extension}":
        raise DocumentUploadValidationError("File extension does not match its content")
    return size, detected


def validate_document_reference(
    *, key: str, user_id: int, document_type: str
) -> tuple[int, str]:
    if is_s3_configured():
        if key.startswith("local:"):
            raise DocumentUploadValidationError("Local document keys are disabled")
        return validate_stored_document(
            s3_key=key, user_id=user_id, document_type=document_type
        )
    return validate_local_document(
        local_key=key, user_id=user_id, document_type=document_type
    )


def resolve_local_document_path(local_key_or_url: str) -> Path:
    key = local_key_or_url
    if key.startswith("local:"):
        key = key.removeprefix("local:")

    match = _LOCAL_DOCUMENT_KEY_PATTERN.fullmatch(key)
    if match is None:
        raise DocumentUploadValidationError('Invalid local document path')

    document_type = match.group('document_type')
    extension = match.group('extension')
    allowed_extensions = {
        MIME_TYPE_EXTENSIONS[mime_type]
        for mime_type in DOCUMENT_MIME_TYPES[document_type]
    }
    if extension not in allowed_extensions:
        raise DocumentUploadValidationError('Invalid local document path')

    root = os.path.realpath(os.fspath(get_local_upload_root()))
    path = os.path.realpath(os.path.join(root, key))
    safe_prefix = root + os.sep
    if not path.startswith(safe_prefix):
        raise DocumentUploadValidationError('Invalid local document path')
    return Path(path)
