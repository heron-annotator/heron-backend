import uuid
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from heron.db import dataset as db_dataset
from heron.db import project as db_project
from heron.db import user as db_user
from heron.db.db import get_connection

from .user import get_current_user

router = APIRouter()


@router.post("/project/{project_id}/dataset")
async def upload_dataset(
    project_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
    file: UploadFile,
):
    project = await db_project.get_by_id(conn, project_id)
    if project is None:
        # Project doesn't exist at all
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.id not in project.members:
        # The project exists but the current user is not a member
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner != current_user.id:
        # Current user doesn't own this project, they can't add files
        raise HTTPException(
            status_code=401, detail="Not enough permissions to upload files"
        )

    if file.content_type is None:
        raise HTTPException(status_code=400, detail="Missing content type")
    if file.content_type != "text/plain":
        raise HTTPException(status_code=400, detail="Invalid content type")
    try:
        text = (await file.read()).decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Encoding not supported")

    dataset_id = uuid.uuid4()
    await db_dataset.create(
        conn,
        db_dataset.Dataset(
            id=dataset_id, project_id=project_id, filename=file.filename, text=text
        ),
    )
    return {"dataset_id": dataset_id}


@router.get("/project/{project_id}/dataset/{dataset_id}")
async def get_dataset(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
) -> db_dataset.Dataset:
    project = await db_project.get_by_id(conn, project_id)
    if project is None:
        # Project doesn't exist at all
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.id not in project.members:
        # The project exists but the current user is not a member
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.id != project.owner:
        # The project exists but the current user is not the owner
        raise HTTPException(status_code=403, detail="Not enough permissions")

    dataset = await db_dataset.get_by_id(conn, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.get("/project/{project_id}/dataset")
async def get_project_dataset(
    project_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
) -> list[db_dataset.Dataset]:
    project = await db_project.get_by_id(conn, project_id)
    if project is None:
        # Project doesn't exist at all
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.id not in project.members:
        # The project exists but the current user is not a member
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.id != project.owner:
        # The project exists but the current user is not the owner
        raise HTTPException(status_code=403, detail="Not enough permissions")

    datasets = await db_dataset.get_by_project(conn, project_id)
    return datasets


@router.delete("/project/{project_id}/dataset/{dataset_id}")
async def delete_dataset(
    project_id: uuid.UUID,
    dataset_id: uuid.UUID,
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

    if project.owner != current_user.id:
        # Current user doesn't own this project, they can't delete it
        raise HTTPException(
            status_code=401, detail="Not enough permissions to delete dataset"
        )

    await db_dataset.delete(conn, dataset_id)
