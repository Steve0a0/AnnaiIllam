"""Regression coverage for the standalone scheduler deployment."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient
import pytest
import yaml

from app.core.scheduler import run_scheduler_forever
from app.main import app
from app.scheduler_runner import main as run_scheduler_process


def test_two_api_lifespans_start_zero_scheduler_loops():
    """Multiple API workers must never run scheduled jobs."""
    with patch("app.core.scheduler._cleanup_loop", new_callable=AsyncMock) as cleanup_loop:
        with TestClient(app), TestClient(app):
            pass

    cleanup_loop.assert_not_awaited()


def test_standalone_process_starts_scheduler_once():
    scheduler_coroutine = object()
    run_forever = Mock(return_value=scheduler_coroutine)
    with (
        patch(
            "app.scheduler_runner.run_scheduler_forever",
            new=run_forever,
        ),
        patch("app.scheduler_runner.asyncio.run") as asyncio_run,
        patch("app.scheduler_runner.init_sentry"),
        patch("app.scheduler_runner.configure_logging"),
    ):
        run_scheduler_process()

    run_forever.assert_called_once_with()
    asyncio_run.assert_called_once_with(scheduler_coroutine)


@pytest.mark.asyncio
async def test_scheduler_entry_point_runs_one_cleanup_loop():
    with patch("app.core.scheduler._cleanup_loop", new_callable=AsyncMock) as cleanup_loop:
        await run_scheduler_forever()

    cleanup_loop.assert_awaited_once_with()


def test_compose_deploys_exactly_one_scheduler_replica():
    compose_path = Path(__file__).resolve().parents[3] / "docker-compose.yml"
    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))

    backend = compose["services"]["backend"]
    scheduler = compose["services"]["scheduler"]

    assert "--workers ${WEB_CONCURRENCY:-2}" in backend["command"]
    assert "RUN_SCHEDULER" not in backend.get("environment", {})
    assert scheduler["command"] == "python -m app.scheduler_runner"
    assert scheduler["deploy"]["replicas"] == 1


def test_api_readiness_does_not_depend_on_process_local_scheduler(client):
    with (
        patch("app.api.health.engine.connect") as connect,
        patch("app.api.health.redis_lib.Redis.from_url") as redis_from_url,
    ):
        connect.return_value.__enter__.return_value.execute.return_value = None
        redis_from_url.return_value.ping.return_value = True
        response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert "scheduler" not in str(response.json()).lower()
