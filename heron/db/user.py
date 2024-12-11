import uuid

import asyncpg
from pydantic import BaseModel


class User(BaseModel):
    """
    Represents a user in the database.
    """

    id: uuid.UUID
    name: str
    email: str
    password_hash: str


async def create(conn: asyncpg.Connection, user: User) -> str:
    """
    Creates a new user in the database.
    """
    return await conn.execute(
        "INSERT INTO users "
        "(id, username, email, password_hash) "
        "VALUES ($1, $2, $3, $4)",
        user.id,
        user.name,
        user.email,
        user.password_hash,
    )


async def get_by_id(conn: asyncpg.Connection, user_id: uuid.UUID) -> User | None:
    """
    Finds a user by their id.
    Returns None if the user does not exist.
    """
    record: asyncpg.Record | None = await conn.fetchrow(
        "SELECT * FROM users WHERE id = $1", user_id
    )
    if record is None:
        return None
    return User(
        id=record["id"],
        name=record["username"],
        email=record["email"],
        password_hash=record["password_hash"],
    )


async def get_by_username(conn: asyncpg.Connection, username: str) -> User | None:
    """
    Finds a user by their username.
    Returns None if the user does not exist.
    """

    record: asyncpg.Record | None = await conn.fetchrow(
        "SELECT * FROM users WHERE username = $1",
        username,
    )
    if record is None:
        return None
    return User(
        id=record["id"],
        name=record["username"],
        email=record["email"],
        password_hash=record["password_hash"],
    )


async def get_by_email(conn: asyncpg.Connection, email: str) -> User | None:
    """
    Finds a user by their email.
    Returns None if the user does not exist.
    """
    record: asyncpg.Record | None = await conn.fetchrow(
        "SELECT * FROM users WHERE email = $1", email
    )
    if record is None:
        return None
    return User(
        id=record["id"],
        name=record["username"],
        email=record["email"],
        password_hash=record["password_hash"],
    )


async def username_exists(conn: asyncpg.Connection, username: str) -> bool:
    """
    Checks if a username already exists in the database.
    """
    exists = await conn.fetchval(
        "SELECT 1 FROM users WHERE username = LOWER($1) LIMIT 1", username
    )
    return bool(exists)


async def email_exists(conn: asyncpg.Connection, email: str) -> bool:
    """
    Checks if a email already exists in the database.
    """
    exists = await conn.fetchval(
        "SELECT 1 FROM users WHERE email = LOWER($1) LIMIT 1", email
    )
    return bool(exists)
