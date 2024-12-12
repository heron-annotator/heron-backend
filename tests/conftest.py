from collections.abc import Callable
from typing import Tuple

import asyncpg
import pytest
import pytest_asyncio
from starlette.testclient import TestClient

from heron.config import settings
from heron.main import app


@pytest_asyncio.fixture
async def db():
    _settings = settings()
    user = _settings.postgres_user
    password = _settings.postgres_password
    db = _settings.postgres_db
    host = _settings.postgres_host
    port = _settings.postgres_port
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    pool = await asyncpg.create_pool(connection_string)
    async with pool.acquire() as conn:
        yield conn
    await pool.close()


@pytest_asyncio.fixture
async def test_client(db: asyncpg.Connection):
    with TestClient(app=app) as client:
        yield client
        await db.execute("DROP SCHEMA public CASCADE")
        await db.execute("CREATE SCHEMA public")


@pytest.fixture
def create_user(
    test_client: TestClient, db: asyncpg.Connection
) -> Callable[..., Tuple[str, str]]:
    """
    Returns a function that creates a user and returns its id and token.
    """

    def _create_user(
        username: str, email: str | None = None, password: str = "password"
    ) -> Tuple[str, str]:
        email = email or f"{username}@example.com"
        res = test_client.post(
            "/register",
            json={
                "username": username,
                "email": email,
                "password": password,
            },
        )
        assert res.status_code == 200
        user_id = res.json()["user_id"]
        res = test_client.post(
            "/token", data={"username": username, "password": password}
        )
        assert res.status_code == 200
        token = res.json()["access_token"]
        return user_id, token

    return _create_user
