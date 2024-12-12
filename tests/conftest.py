import asyncpg
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
