from collections.abc import Callable
from typing import Tuple

import asyncpg
from starlette.testclient import TestClient


async def test_create_label(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
):
    user_id, token = create_user(username="my_user")
    project_id = create_project(
        user_token=token, title="My Project", description="My project description"
    )

    res = test_client.post(
        f"/project/{project_id}/label",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={"name": "My label", "color": "#FF0000"},
    )
    assert res.status_code == 200
    label_id = res.json()["label_id"]

    res = test_client.get(
        f"/project/{project_id}/label/{label_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    labels = await db.fetch("SELECT * FROM labels")
    assert len(labels) == 1
    label = labels[0]
    assert str(label["id"]) == label_id
    assert str(label["project_id"]) == project_id
    assert label["name"] == "My label"
    assert label["color"] == "#FF0000"


async def test_get_label(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
    create_label: Callable[..., str],
):
    user_id, token = create_user(username="my_user")
    project_id = create_project(
        user_token=token, title="My Project", description="My project description"
    )
    label_id = create_label(
        user_token=token, project_id=project_id, name="My label", color="#FF0000"
    )

    res = test_client.get(
        f"/project/{project_id}/label/{label_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200
    label = res.json()
    assert str(label["id"]) == label_id
    assert str(label["project_id"]) == project_id
    assert label["name"] == "My label"
    assert label["color"] == "#FF0000"


async def test_get_project_labels(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
    create_label: Callable[..., str],
):
    user_id, token = create_user(username="my_user")
    project_id = create_project(
        user_token=token, title="My Project", description="My project description"
    )
    create_label(user_token=token, project_id=project_id, name="First", color="#FF0000")
    create_label(
        user_token=token, project_id=project_id, name="Second", color="#00FF00"
    )

    res = test_client.get(
        f"/project/{project_id}/label",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200
    labels = res.json()
    assert len(labels) == 2
    assert labels[0]["name"] == "First"
    assert labels[0]["color"] == "#FF0000"
    assert labels[1]["name"] == "Second"
    assert labels[1]["color"] == "#00FF00"


async def test_update_label(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
    create_label: Callable[..., str],
):
    user_id, token = create_user(username="my_user")
    project_id = create_project(
        user_token=token, title="My Project", description="My project description"
    )
    label_id = create_label(
        user_token=token, project_id=project_id, name="My label", color="#FF0000"
    )

    res = test_client.put(
        f"/project/{project_id}/label/{label_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={"name": "My updated label"},
    )
    assert res.status_code == 200
    label = res.json()
    assert str(label["id"]) == label_id
    assert str(label["project_id"]) == project_id
    assert label["name"] == "My updated label"
    assert label["color"] == "#FF0000"


async def test_delete_label(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
    create_label: Callable[..., str],
):
    user_id, token = create_user(username="my_user")
    project_id = create_project(
        user_token=token, title="My Project", description="My project description"
    )
    label_id = create_label(
        user_token=token, project_id=project_id, name="My label", color="#FF0000"
    )

    labels = await db.fetch("SELECT * FROM labels")
    assert len(labels) == 1

    res = test_client.delete(
        f"/project/{project_id}/label/{label_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200
    labels = await db.fetch("SELECT * FROM labels")
    assert len(labels) == 0

    res = test_client.delete(
        f"/project/{project_id}/label/{label_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200

    labels = await db.fetch("SELECT * FROM labels")
    assert len(labels) == 0
