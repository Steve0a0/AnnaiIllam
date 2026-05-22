import logging
import time
from fastapi import Request


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("annai_illam")


async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000, 2)

    logger.info(
        "%s %s | status=%s | duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response