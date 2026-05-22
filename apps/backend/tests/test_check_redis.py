import pytest

from scripts.check_redis import _load_redis_url, _redact_redis_url, build_parser


def test_redact_redis_url_masks_password():
    assert _redact_redis_url("rediss://default:secret@redis.example.com:6380/0") == (
        "rediss://***@redis.example.com:6380/0"
    )


def test_redact_redis_url_leaves_url_without_credentials():
    assert _redact_redis_url("redis://redis.example.com:6379/0") == "redis://redis.example.com:6379/0"


def test_load_redis_url_prefers_explicit_url(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://from-env:6379/0")

    assert _load_redis_url("redis://from-arg:6379/0") == "redis://from-arg:6379/0"


def test_load_redis_url_reads_environment(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://from-env:6379/0")

    assert _load_redis_url() == "redis://from-env:6379/0"


def test_load_redis_url_rejects_missing_value(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)

    with pytest.raises(ValueError, match="REDIS_URL must be set"):
        _load_redis_url()


def test_parser_supports_ping_only_and_key_prefix():
    args = build_parser().parse_args(["--ping-only", "--key-prefix", "custom:prefix"])

    assert args.ping_only is True
    assert args.key_prefix == "custom:prefix"


def test_parser_accepts_explicit_url():
    args = build_parser().parse_args(["--url", "rediss://default:secret@redis.example.com:6380/0"])

    assert args.url == "rediss://default:secret@redis.example.com:6380/0"
