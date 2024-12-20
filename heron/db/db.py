from typing import AsyncGenerator

import asyncpg
from fastapi import Request

from heron.config import settings


async def create_connection_pool() -> asyncpg.Pool:
    """
    Creates a connection pool, doesn't handle closing.
    """
    _settings = settings()
    user = _settings.postgres_user
    password = _settings.postgres_password
    db = _settings.postgres_db
    host = _settings.postgres_host
    port = _settings.postgres_port
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return await asyncpg.create_pool(connection_string)


async def create_tables(conn: asyncpg.Pool):
    """
    Well, this creates the tables.
    """
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id UUID PRIMARY KEY, "
        "username TEXT NOT NULL UNIQUE, "
        "email TEXT NOT NULL UNIQUE, "
        "password_hash TEXT NOT NULL"
        ")"
    )
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS projects ("
        "id UUID PRIMARY KEY, "
        "owner UUID references users(id), "
        "title TEXT NOT NULL, "
        "description TEXT NOT NULL"
        ")"
    )
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS project_members ("
        "project_id UUID references projects(id), "
        "user_id UUID references users(id), "
        "PRIMARY KEY (project_id, user_id))"
    )
    await conn.execute(
        "CREATE TABlE IF NOT EXISTS datasets ("
        "id UUID PRIMARY KEY, "
        "project_id UUID references projects(id), "
        "filename TEXT, "
        "text TEXT NOT NULL"
        ")"
    )
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS labels ("
        "id UUID PRIMARY KEY, "
        "project_id UUID references projects(id), "
        "name TEXT NOT NULL, "
        "color VARCHAR(7) NOT NULL"
        ")"
    )
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS categories ("
        "id UUID PRIMARY KEY, "
        "label_id UUID references labels(id) ON DELETE CASCADE, "
        "project_id UUID references projects(id), "
        "dataset_id UUID references datasets(id) ON DELETE CASCADE, "
        "start_offset INTEGER NOT NULL, "
        "end_offset INTEGER NOT NULL"
        ")"
    )


async def get_connection(request: Request) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Dependency used to get a connection from the global connection pool.
    """
    async with request.state.db_pool.acquire() as conn:
        yield conn
