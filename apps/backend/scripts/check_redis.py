from __future__ import annotations

import argparse
import os
import sys
import uuid
from urllib.parse import urlsplit, urlunsplit

import redis
from redis.exceptions import RedisError


DEFAULT_KEY_PREFIX = "annai:redis-check"


def _redact_redis_url(redis_url: str) -> str:
    try:
        parsed = urlsplit(redis_url)
    except ValueError:
        return "<invalid REDIS_URL>"

    if "@" not in parsed.netloc:
        return redis_url

    host_part = parsed.netloc.rsplit("@", 1)[1]
    return urlunsplit((parsed.scheme, f"***@{host_part}", parsed.path, parsed.query, parsed.fragment))


def _load_redis_url(explicit_url: str | None = None) -> str:
    redis_url = (explicit_url or os.environ.get("REDIS_URL", "")).strip()
    if not redis_url:
        raise ValueError("REDIS_URL must be set")
    return redis_url


def check_redis(redis_url: str, *, key_prefix: str = DEFAULT_KEY_PREFIX, write_check: bool = True) -> None:
    client = redis.Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    try:
        client.ping()

        if write_check:
            key = f"{key_prefix}:{uuid.uuid4().hex}"
            value = "ok"
            client.set(key, value, ex=60)
            observed = client.get(key)
            client.delete(key)
            if observed != value:
                raise RuntimeError("Redis write/read check returned an unexpected value")
    finally:
        client.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify production Redis connectivity.")
    parser.add_argument(
        "--url",
        help="Redis URL to verify. Defaults to REDIS_URL from the environment.",
    )
    parser.add_argument(
        "--ping-only",
        action="store_true",
        help="Only run PING; skip the temporary TTL write/read/delete check.",
    )
    parser.add_argument(
        "--key-prefix",
        default=DEFAULT_KEY_PREFIX,
        help=f"Prefix for the temporary verification key. Default: {DEFAULT_KEY_PREFIX}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        redis_url = _load_redis_url(args.url)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    try:
        check_redis(redis_url, key_prefix=args.key_prefix, write_check=not args.ping_only)
    except (RedisError, RuntimeError, ValueError) as exc:
        print(f"Redis check failed for {_redact_redis_url(redis_url)}: {exc}", file=sys.stderr)
        return 1

    mode = "ping" if args.ping_only else "ping + write/read/delete"
    print(f"Redis check passed for {_redact_redis_url(redis_url)} ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
