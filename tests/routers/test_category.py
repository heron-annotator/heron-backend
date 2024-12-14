from collections.abc import Callable
from typing import Tuple

import asyncpg
from starlette.testclient import TestClient


async def test_create_category(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
    create_dataset: Callable[..., str],
    create_label: Callable[..., str],
):
    user_id, token = create_user(username="test_user")
    project_id = create_project(
        user_token=token, title="Test Project", description="Test Description"
    )
    dataset_id = create_dataset(
        user_token=token, project_id=project_id, file=("test.txt", b"Test content")
    )
    label_id = create_label(
        user_token=token, project_id=project_id, name="Test Label", color="#FF0000"
    )

    res = test_client.post(
        f"/project/{project_id}/dataset/{dataset_id}/category",
        headers={"Authorization": f"Bearer {token}"},
        json={"label_id": label_id, "start_offset": 0, "end_offset": 5},
    )
    assert res.status_code == 200
    category_id = res.json()["category_id"]

    categories = await db.fetch("SELECT * FROM categories")
    assert len(categories) == 1
    category = categories[0]
    assert str(category["id"]) == category_id
    assert str(category["project_id"]) == project_id
    assert str(category["dataset_id"]) == dataset_id
    assert str(category["label_id"]) == label_id
    assert category["start_offset"] == 0
    assert category["end_offset"] == 5


async def test_get_dataset_categories(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
    create_dataset: Callable[..., str],
    create_label: Callable[..., str],
    create_category: Callable[..., str],
):
    user_id, token = create_user(username="test_user")
    project_id = create_project(
        user_token=token, title="Test Project", description="Test Description"
    )
    dataset_id = create_dataset(
        user_token=token, project_id=project_id, file=("test.txt", b"Test content")
    )
    label_id = create_label(
        user_token=token, project_id=project_id, name="Test Label", color="#FF0000"
    )

    category_id_1 = create_category(
        user_token=token,
        project_id=project_id,
        dataset_id=dataset_id,
        label_id=label_id,
        start_offset=0,
        end_offset=5,
    )
    category_id_2 = create_category(
        user_token=token,
        project_id=project_id,
        dataset_id=dataset_id,
        label_id=label_id,
        start_offset=6,
        end_offset=10,
    )

    res = test_client.get(
        f"/project/{project_id}/dataset/{dataset_id}/category",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    categories = res.json()
    assert len(categories) == 2

    assert str(categories[0]["id"]) == category_id_1
    assert str(categories[0]["project_id"]) == project_id
    assert str(categories[0]["dataset_id"]) == dataset_id
    assert str(categories[0]["label_id"]) == label_id
    assert categories[0]["start_offset"] == 0
    assert categories[0]["end_offset"] == 5

    assert str(categories[1]["id"]) == category_id_2
    assert str(categories[1]["project_id"]) == project_id
    assert str(categories[1]["dataset_id"]) == dataset_id
    assert str(categories[1]["label_id"]) == label_id
    assert categories[1]["start_offset"] == 6
    assert categories[1]["end_offset"] == 10


async def test_update_category(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
    create_dataset: Callable[..., str],
    create_label: Callable[..., str],
    create_category: Callable[..., str],
):
    user_id, token = create_user(username="test_user")
    project_id = create_project(
        user_token=token, title="Test Project", description="Test Description"
    )
    dataset_id = create_dataset(
        user_token=token, project_id=project_id, file=("test.txt", b"Test content")
    )
    label_id = create_label(
        user_token=token, project_id=project_id, name="Test Label", color="#FF0000"
    )
    category_id = create_category(
        user_token=token,
        project_id=project_id,
        dataset_id=dataset_id,
        label_id=label_id,
        start_offset=0,
        end_offset=5,
    )

    res = test_client.put(
        f"/project/{project_id}/dataset/{dataset_id}/category/{category_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"id": category_id, "start_offset": 1, "end_offset": 6},
    )
    assert res.status_code == 200
    updated_category = res.json()
    assert str(updated_category["id"]) == category_id
    assert str(updated_category["project_id"]) == project_id
    assert str(updated_category["dataset_id"]) == dataset_id
    assert str(updated_category["label_id"]) == label_id
    assert updated_category["start_offset"] == 1
    assert updated_category["end_offset"] == 6


async def test_delete_category(
    test_client: TestClient,
    db: asyncpg.Connection,
    create_user: Callable[..., Tuple[str, str]],
    create_project: Callable[..., str],
    create_dataset: Callable[..., str],
    create_label: Callable[..., str],
    create_category: Callable[..., str],
):
    user_id, token = create_user(username="test_user")
    project_id = create_project(
        user_token=token, title="Test Project", description="Test Description"
    )
    dataset_id = create_dataset(
        user_token=token, project_id=project_id, file=("test.txt", b"Test content")
    )
    label_id = create_label(
        user_token=token, project_id=project_id, name="Test Label", color="#FF0000"
    )
    category_id = create_category(
        user_token=token,
        project_id=project_id,
        dataset_id=dataset_id,
        label_id=label_id,
        start_offset=0,
        end_offset=5,
    )
    categories = await db.fetch("SELECT * FROM categories")
    assert len(categories) == 1

    res = test_client.delete(
        f"/project/{project_id}/dataset/{dataset_id}/category/{category_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

    categories = await db.fetch("SELECT * FROM categories")
    assert len(categories) == 0

    res = test_client.delete(
        f"/project/{project_id}/dataset/{dataset_id}/category/{category_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

    categories = await db.fetch("SELECT * FROM categories")
    assert len(categories) == 0
