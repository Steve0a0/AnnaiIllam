import os

# Choose the test database, in priority order (set before any app import so
# Settings() / create_engine() pick up the right URL):
#   1. TEST_DATABASE_URL if explicitly set — CI points this at its Postgres
#      service; a developer can also force SQLite with TEST_DATABASE_URL=sqlite://.
#   2. The local Docker Postgres (docker compose) when it's reachable — so local
#      runs match CI and avoid SQLite-vs-Postgres differences (audit sessions,
#      SELECT FOR UPDATE, partial indexes). The test DB is auto-created if absent.
#   3. In-memory SQLite fallback when no Postgres is available (fast, zero-setup).
_DOCKER_PG = "postgresql+psycopg://postgres:postgres@localhost:5433/annai_illam_test"


def _ensure_postgres(url: str) -> bool:
    """True if the Postgres server is reachable; creates the test DB if missing."""
    try:
        import psycopg
    except ImportError:
        return False
    raw = url.replace("+psycopg", "")
    base, _, db_name = raw.rpartition("/")
    try:
        conn = psycopg.connect(f"{base}/postgres", connect_timeout=2)
    except Exception:
        return False  # server not up → caller falls back to SQLite
    try:
        conn.autocommit = True
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)
        ).fetchone()
        if not exists:
            conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        conn.close()
    return True


_TEST_DB_URL = os.environ.get("TEST_DATABASE_URL")
if not _TEST_DB_URL and _ensure_postgres(_DOCKER_PG):
    _TEST_DB_URL = _DOCKER_PG

_USE_POSTGRES = bool(_TEST_DB_URL and not _TEST_DB_URL.startswith("sqlite"))

if _USE_POSTGRES:
    os.environ["DATABASE_URL"] = _TEST_DB_URL
else:
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-min-32chars!!")
os.environ.setdefault("APP_ENV", "local")

import pytest
import redis as redis_lib
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.models  # noqa: F401 — registers all models on Base.metadata
from app.db.session import Base
from app.main import app
from app.db.deps import get_db
from app.core.security import hash_password
from app.models.admin_profile import AdminProfile
from app.models.user import User

_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/15")


@pytest.fixture(autouse=True)
def flush_redis():
    """Flush the test Redis database before EACH test.

    Function-scoped (not session) so rate-limit counters from one test never
    bleed into the next — otherwise later auth/OTP tests hit 429 and fail only
    in a full run while passing in isolation.
    """
    try:
        r = redis_lib.Redis.from_url(_REDIS_URL, decode_responses=True)
        r.flushdb()
        r.close()
    except Exception:
        pass  # Redis unavailable — rate limiter will skip gracefully


if _USE_POSTGRES:
    # Tables are created once for the whole session; each test wraps its operations
    # in an outer transaction that is always rolled back, keeping tests isolated
    # without the overhead of dropping and recreating 27 tables per test.
    @pytest.fixture(scope="session")
    def engine():
        _engine = create_engine(_TEST_DB_URL)
        Base.metadata.create_all(bind=_engine)
        yield _engine
        Base.metadata.drop_all(bind=_engine)
        _engine.dispose()

    @pytest.fixture
    def db(engine):
        """Each test gets its own connection wrapped in an outer transaction.
        join_transaction_mode='create_savepoint' means session.commit() flushes to
        a SAVEPOINT rather than the real database — the outer trans.rollback() at
        the end of each test undoes all changes."""
        connection = engine.connect()
        trans = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            trans.rollback()
            connection.close()

else:
    @pytest.fixture
    def engine():
        _engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=_engine)
        yield _engine
        Base.metadata.drop_all(bind=_engine)
        _engine.dispose()

    @pytest.fixture
    def db(engine):
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = _SessionLocal()
        try:
            yield session
        finally:
            session.rollback()
            session.close()


@pytest.fixture
def client(db):
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db):
    user = User(
        phone="9000000001",
        email="admin@annai-illam.test",
        role="admin",
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.flush()
    profile = AdminProfile(
        user_id=user.id,
        full_name="Test Super Admin",
        permission_group="super_admin",
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def client_user(db):
    user = User(
        phone="+919000000002",
        email="client@annai-illam.test",
        role="client",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def worker_user(db):
    user = User(
        phone="+919000000003",
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


BASE = "/api/v1"
