import redis as redis_lib
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette import status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.scheduler import get_scheduler_status
from app.db.session import engine
from app.utils.response import error_response, success_response

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return success_response("API is running")


@router.get("/ready")
def readiness():
    errors: list[str] = []

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        errors.append("database")

    try:
        r = redis_lib.Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        r.ping()
        r.close()
    except Exception:
        errors.append("redis")

    scheduler = get_scheduler_status()
    if not scheduler["alive"]:
        errors.append("scheduler")

    if errors:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response(f"Dependencies not ready: {', '.join(errors)}"),
        )

    return success_response(
        "API, database, Redis, and scheduler are ready",
        data={"scheduler": scheduler},
    )
