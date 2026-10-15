"""Shared test fixtures for the Tensor Studio backend.

Sets ``DATABASE_URL`` to a temporary SQLite file *before* any app module
is imported, so the module-level ``settings`` and ``engine`` pick up the
test database.
"""

from __future__ import annotations

import os
import tempfile

_test_dir = tempfile.mkdtemp(prefix="tensor_studio_test_")
_test_db = os.path.join(_test_dir, "test_marketplace.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.seed import seed_marketplace  # noqa: E402


@pytest.fixture()
def db():
    """Fresh database with schema and seed data for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_marketplace()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    """TestClient wired to a fresh app instance."""
    app = create_app()
    with TestClient(app) as c:
        yield c