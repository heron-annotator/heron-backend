import uuid
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from heron.db import category as db_category
from heron.db import dataset as db_dataset
from heron.db import label as db_label
from heron.db import project as db_project
from heron.db import user as db_user
from heron.db.db import get_connection

from .user import get_current_user

router = APIRouter()


class CategoryCreateIn(BaseModel):
    label_id: uuid.UUID
    start_offset: int
    end_offset: int


class CategoryUpdateIn(BaseModel):
    id: uuid.UUID
    label_id: uuid.UUID | None = None
    start_offset: int | None = None
    end_offset: int | None = None


@router.post("/project/{project_id}/dataset/{dataset_id}/category")
async def create_category(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
    category: CategoryCreateIn,
):
    project = await db_project.get_by_id(conn, project_id)
    if project is None:
        # Project doesn't exist at all
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.id not in project.members:
        # The project exists but the current user is not a member
        raise HTTPException(status_code=404, detail="Project not found")

    stored_dataset = await db_dataset.get_by_id(conn, dataset_id)
    if stored_dataset is None:
        # Dataset doesn't exist at all
        raise HTTPException(status_code=404, detail="Dataset not found")

    stored_label = await db_label.get_by_id(conn, category.label_id)
    if stored_label is None:
        # Label doesn't exist at all
        raise HTTPException(status_code=404, detail="Label not found")

    category_id = uuid.uuid4()
    await db_category.create(
        conn,
        db_category.Category(
            id=category_id,
            label_id=category.label_id,
            project_id=project_id,
            dataset_id=dataset_id,
            start_offset=category.start_offset,
            end_offset=category.end_offset,
        ),
    )
    return {"category_id": category_id}


@router.get("/project/{project_id}/dataset/{dataset_id}/category")
async def get_dataset_categories(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
) -> list[db_category.Category]:
    project = await db_project.get_by_id(conn, project_id)
    if project is None:
        # Project doesn't exist at all
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.id not in project.members:
        # The project exists but the current user is not a member
        raise HTTPException(status_code=404, detail="Project not found")

    stored_dataset = await db_dataset.get_by_id(conn, dataset_id)
    if stored_dataset is None:
        # Dataset doesn't exist at all
        raise HTTPException(status_code=404, detail="Dataset not found")

    return await db_category.get_by_dataset(conn, dataset_id)


@router.put("/project/{project_id}/dataset/{dataset_id}/category/{category_id}")
async def update_category(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    category_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
    category: CategoryUpdateIn,
) -> db_category.Category:
    project = await db_project.get_by_id(conn, project_id)
    if project is None:
        # Project doesn't exist at all
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.id not in project.members:
        # The project exists but the current user is not a member
        raise HTTPException(status_code=404, detail="Project not found")

    stored_dataset = await db_dataset.get_by_id(conn, dataset_id)
    if stored_dataset is None:
        # Dataset doesn't exist at all
        raise HTTPException(status_code=404, detail="Dataset not found")

    stored_category = await db_category.get_by_id(conn, category_id)
    if stored_category is None:
        # Category doesn't exist at all
        raise HTTPException(status_code=404, detail="Category not found")

    updated_category = db_category.Category(
        **{
            **stored_category.model_dump(),
            **category.model_dump(exclude_unset=True),
        }
    )
    await db_category.update(
        conn,
        updated_category,
    )
    return updated_category


@router.get("/project/{project_id}/dataset/{dataset_id}/category/{category_id}")
async def get_category(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    category_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
) -> db_category.Category:
    project = await db_project.get_by_id(conn, project_id)
    if project is None:
        # Project doesn't exist at all
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.id not in project.members:
        # The project exists but the current user is not a member
        raise HTTPException(status_code=404, detail="Project not found")

    stored_dataset = await db_dataset.get_by_id(conn, dataset_id)
    if stored_dataset is None:
        # Dataset doesn't exist at all
        raise HTTPException(status_code=404, detail="Dataset not found")

    stored_category = await db_category.get_by_id(conn, category_id)
    if stored_category is None:
        # Category doesn't exist
        raise HTTPException(status_code=404, detail="Category not found")
    return stored_category


@router.delete("/project/{project_id}/dataset/{dataset_id}/category/{category_id}")
async def delete_category(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    category_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
):
    project = await db_project.get_by_id(conn, project_id)
    if project is None:
        # Project doesn't exist at all
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.id not in project.members:
        # The project exists but the current user is not a member
        raise HTTPException(status_code=404, detail="Project not found")

    stored_dataset = await db_dataset.get_by_id(conn, dataset_id)
    if stored_dataset is None:
        # Dataset doesn't exist at all
        raise HTTPException(status_code=404, detail="Dataset not found")

    await db_category.delete_category(conn, category_id)
