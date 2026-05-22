from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import boto3


_SAFE_LABEL_RE = re.compile(r"[^a-zA-Z0-9_.-]+")


@dataclass(frozen=True)
class BackupConfig:
    database_url: str
    bucket: str
    prefix: str
    region: str
    endpoint_url: str
    retention_days: int
    server_side_encryption: str


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} must be set")
    return value


def _optional_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _normalise_prefix(prefix: str) -> str:
    return prefix.strip().strip("/")


def _database_label(database_url: str) -> str:
    parsed = urlparse(database_url)
    label = Path(parsed.path).name or "database"
    return _SAFE_LABEL_RE.sub("_", label).strip("._-") or "database"


def _backup_object_key(prefix: str, database_url: str, created_at: datetime) -> str:
    timestamp = created_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{_database_label(database_url)}_{timestamp}.dump"
    prefix = _normalise_prefix(prefix)
    return f"{prefix}/{filename}" if prefix else filename


def _parse_retention_days(value: str) -> int:
    if not value:
        return 30
    retention_days = int(value)
    if retention_days < 1:
        raise ValueError("BACKUP_RETENTION_DAYS must be at least 1")
    return retention_days


def _load_config() -> BackupConfig:
    return BackupConfig(
        database_url=_required_env("DATABASE_URL"),
        bucket=_optional_env("BACKUP_S3_BUCKET") or _required_env("S3_BUCKET"),
        prefix=_normalise_prefix(_optional_env("BACKUP_S3_PREFIX", "postgres")),
        region=_optional_env("BACKUP_S3_REGION") or _optional_env("S3_REGION", "ap-south-1"),
        endpoint_url=_optional_env("BACKUP_S3_ENDPOINT_URL") or _optional_env("S3_ENDPOINT_URL"),
        retention_days=_parse_retention_days(_optional_env("BACKUP_RETENTION_DAYS", "30")),
        server_side_encryption=_optional_env("BACKUP_S3_SSE", "AES256"),
    )


def _run_pg_dump(database_url: str, output_path: Path) -> None:
    command = [
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--no-acl",
        "--file",
        str(output_path),
    ]
    env = os.environ.copy()
    env["PGDATABASE"] = database_url
    subprocess.run(command, check=True, env=env)


def _s3_client(config: BackupConfig):
    return boto3.client(
        "s3",
        region_name=config.region or None,
        endpoint_url=config.endpoint_url or None,
    )


def _upload_backup(client, config: BackupConfig, backup_path: Path, key: str) -> None:
    extra_args: dict[str, str] = {}
    if config.server_side_encryption:
        extra_args["ServerSideEncryption"] = config.server_side_encryption

    client.upload_file(
        str(backup_path),
        config.bucket,
        key,
        ExtraArgs=extra_args or None,
    )


def _delete_expired_backups(client, config: BackupConfig, now: datetime) -> int:
    cutoff = now.astimezone(timezone.utc) - timedelta(days=config.retention_days)
    paginator = client.get_paginator("list_objects_v2")
    deleted = 0

    for page in paginator.paginate(Bucket=config.bucket, Prefix=config.prefix):
        for item in page.get("Contents", []):
            last_modified = item.get("LastModified")
            key = item.get("Key")
            if not key or last_modified is None:
                continue
            if last_modified.astimezone(timezone.utc) < cutoff:
                client.delete_object(Bucket=config.bucket, Key=key)
                deleted += 1

    return deleted


def run_backup(config: BackupConfig, *, now: datetime | None = None) -> tuple[str, int]:
    now = now or datetime.now(timezone.utc)
    key = _backup_object_key(config.prefix, config.database_url, now)

    with tempfile.TemporaryDirectory() as tmpdir:
        backup_path = Path(tmpdir) / Path(key).name
        _run_pg_dump(config.database_url, backup_path)

        client = _s3_client(config)
        _upload_backup(client, config, backup_path, key)
        deleted = _delete_expired_backups(client, config, now)

    return key, deleted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Back up PostgreSQL to S3.")
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print non-sensitive backup target settings and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = _load_config()
    except (TypeError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    if args.print_config:
        print(
            "Backup target: "
            f"bucket={config.bucket} prefix={config.prefix or '<root>'} "
            f"region={config.region or '<default>'} retention_days={config.retention_days}"
        )
        return 0

    try:
        key, deleted = run_backup(config)
    except subprocess.CalledProcessError as exc:
        print(f"pg_dump failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode or 1
    except Exception as exc:
        print(f"Backup failed: {exc}", file=sys.stderr)
        return 1

    print(f"Uploaded database backup to s3://{config.bucket}/{key}")
    print(f"Deleted {deleted} expired backup object(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
