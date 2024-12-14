import uuid
from collections.abc import Callable
from typing import Tuple

import asyncpg
import pytest
from starlette.testclient import TestClient


async def test_create(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
):
    projects = await db.fetch("SELECT * FROM projects")
    assert projects == []

    user_id, token = create_user(username="my_user")
    res = test_client.post(
        "/project",
        json={
            "members": [],
            "title": "My Project",
            "description": "My project description",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200

    projects = await db.fetch("SELECT * FROM projects")
    assert len(projects) == 1
    assert str(projects[0]["id"]) == res.json()["project_id"]
    assert projects[0]["title"] == "My Project"
    assert projects[0]["description"] == "My project description"
    assert str(projects[0]["owner"]) == user_id

    memberships = await db.fetch("SELECT * FROM project_members")
    assert len(memberships) == 1
    assert memberships[0]["project_id"] == projects[0]["id"]
    assert str(memberships[0]["user_id"]) == user_id


async def test_create_with_members(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
):
    projects = await db.fetch("SELECT * FROM projects")
    assert projects == []
    first_user_id, token = create_user(username="user1")
    second_user_id, _ = create_user(username="user2")
    third_user_id, _ = create_user(username="user3")
    res = test_client.post(
        "/project",
        json={
            "members": [str(second_user_id), str(third_user_id)],
            "title": "My Project",
            "description": "My project description",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200

    projects = await db.fetch("SELECT * FROM projects")
    assert len(projects) == 1
    assert str(projects[0]["id"]) == res.json()["project_id"]
    assert projects[0]["title"] == "My Project"
    assert projects[0]["description"] == "My project description"
    assert str(projects[0]["owner"]) == first_user_id

    memberships = await db.fetch("SELECT * FROM project_members")
    assert len(memberships) == 3
    assert memberships[0]["project_id"] == projects[0]["id"]
    assert str(memberships[0]["user_id"]) == first_user_id
    assert memberships[1]["project_id"] == projects[0]["id"]
    assert str(memberships[1]["user_id"]) == second_user_id
    assert memberships[2]["project_id"] == projects[0]["id"]
    assert str(memberships[2]["user_id"]) == third_user_id


@pytest.mark.skip(
    reason="Need to implement some other checks before this can be enabled"
)
async def test_create_with_nonexisting_member(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
):
    projects = await db.fetch("SELECT * FROM projects")
    assert projects == []

    user_id, token = create_user(username="my_user")
    res = test_client.post(
        "/project",
        json={
            "members": [str(uuid.uuid4())],
            "title": "My Project",
            "description": "My project description",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 404


async def test_get_projects(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
):
    projects = await db.fetch("SELECT * FROM projects")
    assert projects == []

    user_id, token = create_user(username="my_user")
    res = test_client.post(
        "/project",
        json={
            "members": [],
            "title": "My first project",
            "description": "My amazing description",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200
    res = test_client.post(
        "/project",
        json={
            "members": [],
            "title": "My second project",
            "description": "My beautiful description",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200

    res = test_client.get(
        "/project",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) == 2
    projects = sorted(projects, key=lambda p: p["title"])
    assert projects[0]["title"] == "My first project"
    assert projects[0]["description"] == "My amazing description"
    assert projects[0]["owner"] == user_id
    assert projects[0]["members"] == [user_id]

    assert projects[1]["title"] == "My second project"
    assert projects[1]["description"] == "My beautiful description"
    assert projects[1]["owner"] == user_id
    assert projects[1]["members"] == [user_id]


async def test_update_project(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
):
    projects = await db.fetch("SELECT * FROM projects")
    assert projects == []

    user_id, token = create_user(username="my_user")
    res = test_client.post(
        "/project",
        json={
            "members": [],
            "title": "My first project",
            "description": "My amazing description",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200

    project_id = res.json()["project_id"]

    res = test_client.put(
        "/project",
        json={
            "id": project_id,
            "members": [],
            "title": "My first project",
            "description": "My beautiful description",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200
    updated_project = res.json()
    assert updated_project["title"] == "My first project"
    assert updated_project["description"] == "My beautiful description"
    assert str(updated_project["owner"]) == user_id


async def test_update_project_as_non_owner(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
):
    projects = await db.fetch("SELECT * FROM projects")
    assert projects == []

    owner_user_id, owner_token = create_user(username="user1")
    non_owner_user_id, non_owner_token = create_user(username="user2")
    res = test_client.post(
        "/project",
        json={
            "members": [str(non_owner_user_id)],
            "title": "My first project",
            "description": "My amazing description",
        },
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
    )
    assert res.status_code == 200

    project_id = res.json()["project_id"]

    res = test_client.put(
        "/project",
        json={
            "id": project_id,
            "members": [],
            "title": "My evil project",
            "description": "My evil plan",
        },
        headers={
            "Authorization": f"Bearer {non_owner_token}",
        },
    )
    assert res.status_code == 401


async def test_update_project_as_non_member(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
):
    projects = await db.fetch("SELECT * FROM projects")
    assert projects == []

    owner_user_id, owner_token = create_user(username="user1")
    non_owner_user_id, non_owner_token = create_user(username="user2")
    res = test_client.post(
        "/project",
        json={
            "members": [],
            "title": "My first project",
            "description": "My amazing description",
        },
        headers={
            "Authorization": f"Bearer {owner_token}",
        },
    )
    assert res.status_code == 200

    project_id = res.json()["project_id"]

    res = test_client.put(
        "/project",
        json={
            "id": project_id,
            "members": [],
            "title": "My evil project",
            "description": "My evil plan",
        },
        headers={
            "Authorization": f"Bearer {non_owner_token}",
        },
    )
    assert res.status_code == 404
