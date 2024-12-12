import asyncpg
from starlette.testclient import TestClient


async def test_create(test_client: TestClient, db: asyncpg.Connection):
    users = await db.fetch("SELECT * FROM users")
    assert users == []
    res = test_client.post(
        "/register",
        json={
            "username": "John Doe",
            "email": "john@example.com",
            "password": "password",
        },
    )

    assert res.status_code == 200
    users = await db.fetch("SELECT * FROM users")
    assert len(users) == 1
    assert str(users[0]["id"]) == res.json()["user_id"]
    assert users[0]["username"] == "John Doe"
    assert users[0]["email"] == "john@example.com"
    assert users[0]["password_hash"] is not None


async def test_create_duplicate_username(
    test_client: TestClient, db: asyncpg.Connection
):
    users = await db.fetch("SELECT * FROM users")
    assert users == []
    res = test_client.post(
        "/register",
        json={
            "username": "John Doe",
            "email": "john@example.com",
            "password": "password",
        },
    )
    assert res.status_code == 200
    users = await db.fetch("SELECT * FROM users")
    assert len(users) == 1

    res = test_client.post(
        "/register",
        json={
            "username": "John Doe",
            "email": "john@example.com",
            "password": "password",
        },
    )
    assert res.status_code == 400
    users = await db.fetch("SELECT * FROM users")
    assert len(users) == 1


async def test_create_duplicate_email(test_client: TestClient, db: asyncpg.Connection):
    users = await db.fetch("SELECT * FROM users")
    assert users == []
    res = test_client.post(
        "/register",
        json={
            "username": "John Doe",
            "email": "john@example.com",
            "password": "password",
        },
    )
    assert res.status_code == 200
    users = await db.fetch("SELECT * FROM users")
    assert len(users) == 1

    res = test_client.post(
        "/register",
        json={
            "username": "John Doe",
            "email": "john@example.com",
            "password": "password",
        },
    )
    assert res.status_code == 400
    users = await db.fetch("SELECT * FROM users")
    assert len(users) == 1
