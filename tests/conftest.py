"""
pytest configuration: fresh in-memory SQLite database per test, isolated TestClient.

Why this design:
- Real app uses Postgres in prod / file SQLite in dev. Tests use in-memory SQLite —
  ~10x faster, zero filesystem cleanup, totally isolated per test.
- `StaticPool` keeps a single connection alive across the engine so that the same
  in-memory database is visible to every operation in one test (in-memory SQLite
  is otherwise per-connection and would disappear).
- We override FastAPI's `get_db` dependency so every request inside a test reuses
  the same test session — meaning a POST followed by a GET in the same test sees
  the same data.

Three fixtures, each builds on the previous:
    db_engine   → fresh in-memory engine + all tables created
    db_session  → SQLAlchemy session bound to that engine
    client      → FastAPI TestClient with get_db overridden to use db_session
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


@pytest.fixture
def db_engine():
    """Fresh in-memory SQLite engine with all tables created. One per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """SQLAlchemy session bound to the test engine."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_engine, db_session):
    """
    FastAPI TestClient with the production `get_db` dependency overridden
    to use the test database. Every API call in a test runs against the
    same in-memory DB.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # actual close handled by db_session fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
