import uuid
from collections.abc import Callable
from io import BytesIO
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


@pytest.fixture
def create_project(
    test_client: TestClient,
    db: asyncpg.Connection,
) -> Callable[..., str]:
    """
    Returns a function that creates a project and returns its id
    """

    def _create_project(
        user_token: str, title: str, description: str, members: list[uuid.UUID] = []
    ) -> str:
        res = test_client.post(
            "/project",
            json={
                "members": [],
                "title": title,
                "description": description,
            },
            headers={
                "Authorization": f"Bearer {user_token}",
            },
        )
        assert res.status_code == 200
        return res.json()["project_id"]

    return _create_project


@pytest.fixture
def create_dataset(
    test_client: TestClient,
    db: asyncpg.Connection,
) -> Callable[..., str]:
    """
    Returns a function that creates a dataset and returns its id
    """

    def _create_dataset(
        user_token: str, project_id: uuid.UUID, file: Tuple[str, bytes]
    ) -> str:
        res = test_client.post(
            f"/project/{project_id}/dataset",
            headers={
                "Authorization": f"Bearer {user_token}",
            },
            files=[
                ("file", (file[0], BytesIO(file[1]))),
            ],
        )
        assert res.status_code == 200
        return res.json()["dataset_id"]

    return _create_dataset


@pytest.fixture
def create_label(
    test_client: TestClient,
    db: asyncpg.Connection,
) -> Callable[..., str]:
    """
    Returns a function that creates a label and returns its id
    """

    def _create_label(
        user_token: str, project_id: uuid.UUID, name: str, color: str
    ) -> str:
        res = test_client.post(
            f"/project/{project_id}/label",
            headers={
                "Authorization": f"Bearer {user_token}",
            },
            json={"name": name, "color": color},
        )
        assert res.status_code == 200
        return res.json()["label_id"]

    return _create_label


@pytest.fixture
def create_category(
    test_client: TestClient,
    db: asyncpg.Connection,
) -> Callable[..., str]:
    """
    Returns a function that creates a category and returns its id
    """

    def _create_category(
        user_token: str,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        label_id: uuid.UUID,
        start_offset: int,
        end_offset: int,
    ) -> str:
        res = test_client.post(
            f"/project/{project_id}/dataset/{dataset_id}/category",
            headers={
                "Authorization": f"Bearer {user_token}",
            },
            json={
                "label_id": label_id,
                "start_offset": start_offset,
                "end_offset": end_offset,
            },
        )
        assert res.status_code == 200
        return res.json()["category_id"]

    return _create_category
