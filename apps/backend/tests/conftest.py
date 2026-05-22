import os

# Must be set before any app imports so Settings() and create_engine() pick up SQLite
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-min-32chars!!")
os.environ.setdefault("APP_ENV", "local")

import pytest
import redis as redis_lib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.models  # noqa: F401 — registers all models on Base.metadata
from app.db.session import Base
from app.main import app
from app.db.deps import get_db
from app.core.security import hash_password
from app.models.user import User

_SQLITE_URL = "sqlite:///:memory:"

_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/15")


@pytest.fixture(scope="session", autouse=True)
def flush_redis():
    """Flush the test Redis database before the test session to clear stale rate-limit keys."""
    try:
        r = redis_lib.Redis.from_url(_REDIS_URL, decode_responses=True)
        r.flushdb()
        r.close()
    except Exception:
        pass  # Redis unavailable — rate limiter will skip gracefully


@pytest.fixture
def engine():
    _engine = create_engine(
        _SQLITE_URL,
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
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def client_user(db):
    user = User(
        phone="9000000002",
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
        phone="9000000003",
        role="worker",
        is_active=True,
        is_phone_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


BASE = "/api/v1"
