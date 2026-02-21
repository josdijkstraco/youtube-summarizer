"""Shared fixtures for integration tests.

Provides a default get_db override so that tests which do not care about DB
behaviour still work without a real database connection.  Individual tests that
need specific DB behaviour can set their own override and clean it up with
app.dependency_overrides.pop / a dedicated fixture.
"""
from unittest.mock import AsyncMock, MagicMock

import asyncpg
import pytest

from app.db import get_db
from app.main import app


def _make_default_conn() -> AsyncMock:
    """Return a mock asyncpg.Connection suitable for a no-op DB interaction."""
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    # save_record calls conn.execute then conn.fetchrow
    mock_record = MagicMock()
    mock_record.__iter__ = MagicMock(return_value=iter([]))
    # Return a row-like mapping so VideoRecord(**dict(row)) works
    mock_conn.fetchrow.return_value = None
    mock_conn.execute.return_value = None
    # list_recent calls conn.fetch
    mock_conn.fetch.return_value = []
    return mock_conn


@pytest.fixture(autouse=True)
def default_get_db_override():
    """Override get_db with a no-op mock for every integration test.

    Tests that need a specific DB behaviour should set their own override
    *after* this fixture runs and clean it up themselves.
    """
    mock_conn = _make_default_conn()

    async def _override_get_db():
        yield mock_conn

    app.dependency_overrides[get_db] = _override_get_db
    yield mock_conn
    app.dependency_overrides.pop(get_db, None)
