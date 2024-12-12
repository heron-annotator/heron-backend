from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from heron.db.db import create_connection_pool, create_tables


@pytest.mark.asyncio
@patch("heron.db.db.asyncpg.create_pool")
@patch("heron.db.db.settings")
async def test_create_connection_pool(
    mock_settings: MagicMock, mock_create_pool: AsyncMock
):
    mock_create_pool.side_effect = AsyncMock()
    mock_settings.return_value.postgres_user = "user"
    mock_settings.return_value.postgres_password = "password"
    mock_settings.return_value.postgres_db = "db"
    mock_settings.return_value.postgres_host = "host"
    mock_settings.return_value.postgres_port = 5432
    await create_connection_pool()
    mock_create_pool.assert_called_once_with("postgresql://user:password@host:5432/db")


@pytest.mark.asyncio
async def test_create_tables():
    mock_connection = AsyncMock()
    await create_tables(mock_connection)
    mock_connection.execute.assert_has_calls(
        [
            call(
                "CREATE TABLE IF NOT EXISTS users ("
                "id UUID PRIMARY KEY, "
                "username TEXT NOT NULL UNIQUE, "
                "email TEXT NOT NULL UNIQUE, "
                "password_hash TEXT NOT NULL"
                ")"
            ),
            call(
                "CREATE TABLE IF NOT EXISTS projects ("
                "id UUID PRIMARY KEY, "
                "owner UUID references users(id), "
                "title TEXT NOT NULL, "
                "description TEXT NOT NULL"
                ")"
            ),
            call(
                "CREATE TABLE IF NOT EXISTS project_members ("
                "project_id UUID references projects(id), "
                "user_id UUID references users(id), "
                "PRIMARY KEY (project_id, user_id))"
            ),
        ]
    )
