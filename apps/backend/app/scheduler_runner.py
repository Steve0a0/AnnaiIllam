"""Standalone scheduler process.

Runs the maintenance loop (OTP/token cleanup, quote expiry, no-show flagging,
SLA breach, unclosed-checkin alerts) in its OWN container so exactly one
scheduler runs no matter how many API workers are started.

Start with:  python -m app.scheduler_runner
See the root docker-compose.yml `scheduler` service.
"""

import asyncio
import logging

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.monitoring import init_sentry
from app.core.scheduler import run_scheduler_forever

logger = logging.getLogger(__name__)


def main() -> None:
    init_sentry()
    configure_logging(settings.is_local)
    logger.info("Standalone scheduler process starting")
    try:
        asyncio.run(run_scheduler_forever())
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Standalone scheduler process stopping")


if __name__ == "__main__":
    main()
