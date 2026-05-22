import logging

import redis
from fastapi import HTTPException
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger("annai_illam_security")
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def check_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    try:
        current = redis_client.get(key)

        if current is None:
            pipe = redis_client.pipeline()
            pipe.set(key, 1, ex=window_seconds)
            pipe.execute()
            return

        if int(current) >= limit:
            logger.warning("Rate limit exceeded | key=%s | limit=%s | window=%s", key, limit, window_seconds)
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

        redis_client.incr(key)
    except HTTPException:
        raise
    except (RedisError, ValueError) as exc:
        logger.warning(
            "Rate limit backend failure — allowing request through | key=%s | error=%s",
            key,
            exc,
        )
