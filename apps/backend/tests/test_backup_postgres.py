from datetime import datetime, timezone

import pytest

from scripts.backup_postgres import (
    _backup_object_key,
    _database_label,
    _normalise_prefix,
    _parse_retention_days,
)


def test_normalise_prefix_trims_slashes_and_spaces():
    assert _normalise_prefix(" /prod/postgres/ ") == "prod/postgres"


def test_database_label_uses_database_name_from_url():
    assert _database_label("postgresql+psycopg://user:pass@db.example.com:5432/annai_illam") == "annai_illam"


def test_database_label_sanitises_unsafe_characters():
    assert _database_label("postgresql+psycopg://host/my db?sslmode=require") == "my_db"


def test_backup_object_key_includes_prefix_database_and_utc_timestamp():
    created_at = datetime(2026, 5, 20, 12, 30, 5, tzinfo=timezone.utc)

    key = _backup_object_key(
        "prod/postgres",
        "postgresql+psycopg://user:pass@host:5432/annai_illam",
        created_at,
    )

    assert key == "prod/postgres/annai_illam_20260520T123005Z.dump"


def test_backup_object_key_allows_root_prefix():
    created_at = datetime(2026, 5, 20, 12, 30, 5, tzinfo=timezone.utc)

    key = _backup_object_key(
        "",
        "postgresql+psycopg://user:pass@host:5432/annai_illam",
        created_at,
    )

    assert key == "annai_illam_20260520T123005Z.dump"


def test_parse_retention_days_defaults_to_30():
    assert _parse_retention_days("") == 30


def test_parse_retention_days_rejects_zero():
    with pytest.raises(ValueError, match="at least 1"):
        _parse_retention_days("0")
