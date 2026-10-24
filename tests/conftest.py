import os

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient

from quantum_app.api import app
from quantum_app.db import connect, get_conn, get_optional_conn
from scripts.migrate import migrate

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or dotenv_values(".env").get(
    "TEST_DATABASE_URL"
)


def _no_db():
    yield None


@pytest.fixture
def client():
    """API client with no database configured."""
    app.dependency_overrides[get_optional_conn] = _no_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def migrated_url():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set")
    migrate(TEST_DATABASE_URL)
    return TEST_DATABASE_URL


@pytest.fixture
def conn(migrated_url):
    with connect(migrated_url) as conn:
        conn.execute("TRUNCATE circuit_runs RESTART IDENTITY")
        conn.commit()
        yield conn


@pytest.fixture
def db_client(migrated_url):
    """API client backed by the (truncated) test database."""
    with connect(migrated_url) as conn:
        conn.execute("TRUNCATE circuit_runs RESTART IDENTITY")

    def override():
        with connect(migrated_url) as conn:
            yield conn

    app.dependency_overrides[get_conn] = override
    app.dependency_overrides[get_optional_conn] = override
    yield TestClient(app)
    app.dependency_overrides.clear()
