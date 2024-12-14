from collections.abc import Callable
from io import BytesIO
from typing import Tuple

import asyncpg
from starlette.testclient import TestClient


async def test_upload_dataset(
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
        f"/project/{project_id}/dataset",
        headers={
            "Authorization": f"Bearer {token}",
        },
        files=[
            ("file", ("hello.txt", BytesIO(b"Hello world"))),
        ],
    )
    assert res.status_code == 200
    dataset_id = res.json()["dataset_id"]

    datasets = await db.fetch("SELECT * FROM datasets")
    assert len(datasets) == 1
    assert str(datasets[0]["id"]) == dataset_id
    assert str(datasets[0]["project_id"]) == project_id
    assert datasets[0]["filename"] == "hello.txt"
    assert datasets[0]["text"] == "Hello world"


async def test_get_dataset(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
    create_dataset: Callable[..., str],
):
    user_id, token = create_user(username="my_user")
    project_id = create_project(
        user_token=token, title="My Project", description="My project description"
    )
    first_dataset_id = create_dataset(
        user_token=token, project_id=project_id, file=("hello1.txt", b"Hello first")
    )
    second_dataset_id = create_dataset(
        user_token=token, project_id=project_id, file=("hello2.txt", b"Hello second")
    )
    res = test_client.get(
        f"/project/{project_id}/dataset/{first_dataset_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200
    dataset = res.json()
    assert dataset["id"] == first_dataset_id
    assert dataset["project_id"] == project_id
    assert dataset["filename"] == "hello1.txt"
    assert dataset["text"] == "Hello first"

    res = test_client.get(
        f"/project/{project_id}/dataset/{second_dataset_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200
    dataset = res.json()
    assert dataset["id"] == second_dataset_id
    assert dataset["project_id"] == project_id
    assert dataset["filename"] == "hello2.txt"
    assert dataset["text"] == "Hello second"


async def test_get_project_dataset(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
    create_dataset: Callable[..., str],
):
    user_id, token = create_user(username="my_user")
    project_id = create_project(
        user_token=token, title="My Project", description="My project description"
    )
    another_project_id = create_project(
        user_token=token,
        title="Another Project",
        description="Another project description",
    )
    first_dataset_id = create_dataset(
        user_token=token, project_id=project_id, file=("hello1.txt", b"Hello first")
    )
    second_dataset_id = create_dataset(
        user_token=token, project_id=project_id, file=("hello2.txt", b"Hello second")
    )
    create_dataset(
        user_token=token,
        project_id=another_project_id,
        file=("hello3.txt", b"Hello third"),
    )

    res = test_client.get(
        f"/project/{project_id}/dataset",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200
    datasets = res.json()
    assert len(datasets) == 2
    assert datasets[0]["id"] == first_dataset_id
    assert datasets[0]["project_id"] == project_id
    assert datasets[0]["filename"] == "hello1.txt"
    assert datasets[0]["text"] == "Hello first"

    assert datasets[1]["id"] == second_dataset_id
    assert datasets[1]["project_id"] == project_id
    assert datasets[1]["filename"] == "hello2.txt"
    assert datasets[1]["text"] == "Hello second"


async def test_delete_dataset(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
    create_dataset: Callable[..., str],
):
    user_id, token = create_user(username="my_user")
    project_id = create_project(
        user_token=token, title="My Project", description="My project description"
    )
    dataset_id = create_dataset(
        user_token=token, project_id=project_id, file=("hello1.txt", b"Hello first")
    )

    datasets = await db.fetch("SELECT * FROM datasets")
    assert len(datasets) == 1

    res = test_client.delete(
        f"/project/{project_id}/dataset/{dataset_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200

    datasets = await db.fetch("SELECT * FROM datasets")
    assert len(datasets) == 0

    res = test_client.delete(
        f"/project/{project_id}/dataset/{dataset_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )
    assert res.status_code == 200

    datasets = await db.fetch("SELECT * FROM datasets")
    assert len(datasets) == 0
