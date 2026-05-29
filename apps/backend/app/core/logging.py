import json
import logging
import time
import uuid
from fastapi import Request


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("annai_illam")


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(is_local: bool) -> None:
    """Switch to JSON logging in non-local environments.

    Call once from main.py after settings are loaded.  Subsequent calls are
    idempotent (same formatter is re-applied, which is harmless).
    """
    if is_local:
        return  # keep the human-readable text format for local dev

    json_formatter = _JsonFormatter()
    for handler in logging.root.handlers:
        handler.setFormatter(json_formatter)


async def log_requests(request: Request, call_next):
    # Honour an upstream X-Request-ID (e.g. from a load balancer) or mint a new one.
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000, 2)

    logger.info(
        "%s %s | status=%s | duration_ms=%s | request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration,
        request_id,
    )
    # Propagate the request ID back to the caller so client-side logs can be correlated.
    response.headers["X-Request-ID"] = request_id
    return response