"""
Document storage service.

Production uses private S3 with presigned upload/download URLs. Local
development uses the backend filesystem so worker identity documents can be
reviewed from the admin dashboard without any paid storage service.
"""

from pathlib import Path
import uuid

from app.core.config import settings


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
    expires_in: int = 300,
) -> tuple[str, str]:
    ext_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "application/pdf": "pdf",
    }
    ext = ext_map.get(content_type, "bin")
    s3_key = f"workers/{user_id}/{document_type}/{uuid.uuid4().hex}.{ext}"

    s3 = _get_s3_client(public_endpoint=True)

    put_params: dict = {
        "Bucket": settings.s3_bucket,
        "Key": s3_key,
        "ContentType": content_type,
    }
    if _is_aws():
        put_params["ServerSideEncryption"] = "aws:kms"

    url = s3.generate_presigned_url(
        "put_object",
        Params=put_params,
        ExpiresIn=expires_in,
        HttpMethod="PUT",
    )

    return url, s3_key


def generate_download_url(s3_key: str, expires_in: int = 900) -> str:
    s3 = _get_s3_client(public_endpoint=True)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": s3_key},
        ExpiresIn=expires_in,
    )


def build_public_s3_url(s3_key: str) -> str:
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
    content: bytes,
) -> tuple[str, str]:
    suffix = Path(filename).suffix.lower() or ".bin"
    local_key = f"worker-documents/{user_id}/{document_type}/{uuid.uuid4().hex}{suffix}"
    destination = get_local_upload_root() / local_key
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return f"local:{local_key}", str(destination)


def resolve_local_document_path(local_key_or_url: str) -> Path:
    key = local_key_or_url
    if key.startswith("local:"):
        key = key.removeprefix("local:")

    path = (get_local_upload_root() / key).resolve()
    root = get_local_upload_root()
    if root != path and root not in path.parents:
        raise ValueError("Invalid local document path")
    return path
