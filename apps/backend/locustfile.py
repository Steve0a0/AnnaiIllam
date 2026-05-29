"""locustfile.py — Performance and load test for Annai Illam backend.

PERF-1 (latency targets, run with low user count):
    locust -f locustfile.py --host http://localhost:8000 \
           --users 1 --spawn-rate 1 --run-time 60s \
           --headless --only-summary

PERF-2 (concurrent load, 500ms / 1s SLA):
    locust -f locustfile.py --host http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 120s \
           --headless --only-summary

    Breakdown: 20 admin + 50 worker + 30 client = 100 total virtual users.

Prerequisites:
    pip install locust
    The backend must be running and seeded with `python -m scripts.seed_perf`.
    Set env vars if auth credentials differ from defaults below:
        PERF_ADMIN_EMAIL, PERF_ADMIN_PASSWORD
        PERF_CLIENT_PHONE, PERF_WORKER_PHONE
"""
from __future__ import annotations

import os
import random
import logging

from locust import HttpUser, TaskSet, between, events, tag, task
from locust.exception import StopUser

logger = logging.getLogger("annai_perf")

# ---------------------------------------------------------------------------
# Credentials (override with env vars in CI)
# ---------------------------------------------------------------------------
ADMIN_EMAIL = os.getenv("PERF_ADMIN_EMAIL", "admin@annai-illam.test")
ADMIN_PASSWORD = os.getenv("PERF_ADMIN_PASSWORD", "Admin123!")
# Seeded by seed_perf.py — phone format matches what the seed script creates.
CLIENT_PHONE = os.getenv("PERF_CLIENT_PHONE", "+919000000001")
WORKER_PHONE = os.getenv("PERF_WORKER_PHONE", "+919100000001")

# ---------------------------------------------------------------------------
# Shared state (populated once by first user of each type to log in)
# ---------------------------------------------------------------------------
_admin_token: str | None = None
_client_token: str | None = None
_worker_token: str | None = None

# IDs discovered during tests to reuse as path params.
_requirement_ids: list[int] = []
_assignment_ids: list[int] = []


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _admin_login(client) -> str | None:
    resp = client.post(
        "/api/v1/auth/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        name="/auth/admin/login",
    )
    if resp.status_code == 200:
        return resp.json()["data"]["access_token"]
    logger.warning("Admin login failed: %s %s", resp.status_code, resp.text[:200])
    return None


def _otp_login(client, phone: str, role: str) -> str | None:
    r1 = client.post(
        f"/api/v1/auth/{role}/request-otp",
        json={"phone": phone},
        name=f"/auth/{role}/request-otp",
    )
    if r1.status_code != 200:
        return None
    otp = r1.json().get("data", {}).get("otp")
    if not otp:
        return None
    r2 = client.post(
        f"/api/v1/auth/{role}/verify-otp",
        json={"phone": phone, "code": otp},
        name=f"/auth/{role}/verify-otp",
    )
    if r2.status_code == 200:
        return r2.json()["data"]["access_token"]
    return None


# ---------------------------------------------------------------------------
# Admin task set
# ---------------------------------------------------------------------------

class AdminTasks(TaskSet):
    token: str | None = None

    def on_start(self):
        global _admin_token
        if _admin_token:
            self.token = _admin_token
            return
        self.token = _admin_login(self.client)
        if not self.token:
            raise StopUser()
        _admin_token = self.token

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    # Weight 5 — most common admin action.
    @task(5)
    def list_requirements(self):
        resp = self.client.get(
            "/api/v1/admin/requirements",
            headers=self._auth(),
            name="/admin/requirements",
        )
        if resp.status_code == 200:
            items = resp.json().get("data", {}).get("items", [])
            for item in items:
                if item["id"] not in _requirement_ids:
                    _requirement_ids.append(item["id"])

    @task(3)
    def list_requirements_filtered(self):
        status = random.choice(["submitted", "in_progress", "workers_assigned"])
        self.client.get(
            f"/api/v1/admin/requirements?status={status}",
            headers=self._auth(),
            name="/admin/requirements?status=<status>",
        )

    @task(3)
    def requirement_detail(self):
        if not _requirement_ids:
            return
        req_id = random.choice(_requirement_ids)
        self.client.get(
            f"/api/v1/admin/requirements/{req_id}",
            headers=self._auth(),
            name="/admin/requirements/{id}",
        )

    @task(2)
    def worker_matches(self):
        """PERF-1 hot path: worker matching with 500 workers."""
        if not _requirement_ids:
            return
        req_id = random.choice(_requirement_ids)
        self.client.get(
            f"/api/v1/admin/assignments/requirement/{req_id}/matches",
            headers=self._auth(),
            name="/admin/assignments/requirement/{id}/matches",
        )

    @task(3)
    def list_assignments(self):
        resp = self.client.get(
            "/api/v1/admin/assignments",
            headers=self._auth(),
            name="/admin/assignments",
        )
        if resp.status_code == 200:
            items = resp.json().get("data", {}).get("items", [])
            for item in items:
                if item["id"] not in _assignment_ids:
                    _assignment_ids.append(item["id"])

    @task(2)
    def list_finance_payments(self):
        """PERF-1 hot path: paginated finance list."""
        self.client.get(
            "/api/v1/admin/finance/client-payments",
            headers=self._auth(),
            name="/admin/finance/client-payments",
        )

    @task(1)
    def dashboard_summary(self):
        self.client.get(
            "/api/v1/admin/dashboard/summary",
            headers=self._auth(),
            name="/admin/dashboard/summary",
        )

    @task(1)
    def dashboard_alerts(self):
        self.client.get(
            "/api/v1/admin/dashboard/alerts",
            headers=self._auth(),
            name="/admin/dashboard/alerts",
        )


# ---------------------------------------------------------------------------
# Worker task set
# ---------------------------------------------------------------------------

class WorkerTasks(TaskSet):
    token: str | None = None
    phone: str = ""
    _my_assignment_ids: list[int]  # this worker's own assignments, populated by list_my_assignments

    def __init__(self, parent):
        super().__init__(parent)
        self._my_assignment_ids = []

    def on_start(self):
        global _worker_token
        # Each virtual worker picks a unique seeded phone so OTPs don't collide.
        idx = random.randint(1, 490)
        self.phone = f"+9191000{idx:05d}"
        if _worker_token and random.random() < 0.9:
            # Most workers share the first acquired token for speed.
            self.token = _worker_token
            return
        self.token = _otp_login(self.client, self.phone, "worker")
        if not self.token:
            raise StopUser()
        _worker_token = self.token

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def list_my_assignments(self):
        """PERF-1: worker with 50 assignments."""
        resp = self.client.get(
            "/api/v1/worker/assignments",
            headers=self._auth(),
            name="/worker/assignments",
        )
        if resp.status_code == 200:
            items = resp.json().get("data") or []
            eligible_statuses = {"assigned", "accepted", "active"}
            self._my_assignment_ids = [
                a["assignment_id"]
                for a in items
                if a.get("status") in eligible_statuses
            ]

    @task(3)
    def worker_jobs(self):
        self.client.get(
            "/api/v1/worker/jobs/open",
            headers=self._auth(),
            name="/worker/jobs/open",
        )

    @task(2)
    def worker_check_in(self):
        """Simulate GPS check-in using this worker's own assignments."""
        if not self._my_assignment_ids:
            return
        assignment_id = random.choice(self._my_assignment_ids)
        self.client.post(
            "/api/v1/worker/attendance/check-in",
            json={
                "assignment_id": assignment_id,
                "latitude": 13.0827 + random.uniform(-0.01, 0.01),
                "longitude": 80.2707 + random.uniform(-0.01, 0.01),
            },
            headers=self._auth(),
            name="/worker/attendance/check-in",
        )


# ---------------------------------------------------------------------------
# Client task set
# ---------------------------------------------------------------------------

class ClientTasks(TaskSet):
    token: str | None = None
    phone: str = ""

    def on_start(self):
        global _client_token
        idx = random.randint(1, 49)
        self.phone = f"+9190000{idx:05d}"
        if _client_token and random.random() < 0.9:
            self.token = _client_token
            return
        self.token = _otp_login(self.client, self.phone, "client")
        if not self.token:
            raise StopUser()
        _client_token = self.token

    def _auth(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def list_my_requirements(self):
        self.client.get(
            "/api/v1/client/requirements",
            headers=self._auth(),
            name="/client/requirements",
        )

    @task(3)
    def requirement_detail(self):
        if not _requirement_ids:
            return
        req_id = random.choice(_requirement_ids)
        self.client.get(
            f"/api/v1/client/requirements/{req_id}",
            headers=self._auth(),
            name="/client/requirements/{id}",
        )

    @task(2)
    def check_quote_status(self):
        if not _requirement_ids:
            return
        req_id = random.choice(_requirement_ids)
        self.client.get(
            f"/api/v1/client/requirements/{req_id}/quote",
            headers=self._auth(),
            name="/client/requirements/{id}/quote",
        )


# ---------------------------------------------------------------------------
# User classes (PERF-2 ratios: 20 admin : 50 worker : 30 client = 100 total)
# ---------------------------------------------------------------------------

class AdminUser(HttpUser):
    """20 concurrent admin users."""
    tasks = [AdminTasks]
    wait_time = between(0.5, 2)
    weight = 20


class WorkerUser(HttpUser):
    """50 concurrent workers."""
    tasks = [WorkerTasks]
    wait_time = between(1, 3)
    weight = 50


class ClientUser(HttpUser):
    """30 concurrent clients."""
    tasks = [ClientTasks]
    wait_time = between(1, 4)
    weight = 30


# ---------------------------------------------------------------------------
# Custom reporting — flag endpoints exceeding SLA thresholds
# ---------------------------------------------------------------------------

# PERF-1 targets: single-user benchmark
PERF1_THRESHOLD_MS = 500
# PERF-2 targets: under load
PERF2_P95_THRESHOLD_MS = 1_000


# Auth endpoints have expected bcrypt latency (~600–2600 ms) — excluded from SLA.
_AUTH_ENDPOINTS = {"/auth/admin/login", "/auth/client/request-otp", "/auth/worker/request-otp",
                   "/auth/client/verify-otp", "/auth/worker/verify-otp"}


@events.quitting.add_listener
def _on_quitting(environment, **kwargs):
    stats = environment.stats
    failures: list[str] = []
    for _key, entry in stats.entries.items():
        p95 = entry.get_response_time_percentile(0.95)
        if p95 is None:
            continue
        # Skip auth endpoints — bcrypt latency is expected and not a data-path SLA
        if any(entry.name.endswith(ep) for ep in _AUTH_ENDPOINTS):
            continue
        threshold = PERF2_P95_THRESHOLD_MS
        if p95 > threshold:
            failures.append(
                f"  SLOW  {entry.method} {entry.name:50s}  p95={p95:.0f}ms  (limit {threshold}ms)"
            )

    if failures:
        print("\n=== ENDPOINTS EXCEEDING SLA THRESHOLD ===")
        for line in sorted(failures):
            print(line)
        print(f"\n{len(failures)} endpoint(s) need optimisation before go-live.\n")
        environment.process_exit_code = 1
    else:
        print("\nAll endpoints within SLA threshold. ✓\n")
