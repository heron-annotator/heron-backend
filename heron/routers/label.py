import uuid
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from heron.db import get_connection
from heron.db import label as db_label
from heron.db import project as db_project
from heron.db import user as db_user

from .user import get_current_user

router = APIRouter()


class LabelCreateIn(BaseModel):
    name: str
    color: str


class LabelUpdateIn(BaseModel):
    name: str | None = None
    color: str | None = None


@router.post("/project/{project_id}/label")
async def create_label(
    project_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
    label: LabelCreateIn,
):
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

    label_id = uuid.uuid4()
    await db_label.create(
        conn,
        db_label.Label(
            id=label_id,
            project_id=project_id,
            name=label.name,
            color=label.color,
        ),
    )
    return {"label_id": label_id}


@router.get("/project/{project_id}/label/{label_id}")
async def get_label(
    project_id: uuid.UUID,
    label_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
) -> db_label.Label:
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

    label = await db_label.get_by_id(conn, label_id)
    if label is None:
        raise HTTPException(status_code=404, detail="Label not found")
    return label


@router.get("/project/{project_id}/label")
async def get_project_labels(
    project_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
) -> list[db_label.Label]:
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

    return await db_label.get_by_project(conn, project_id)


@router.put("/project/{project_id}/label/{label_id}")
async def update_label(
    project_id: uuid.UUID,
    label_id: uuid.UUID,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
    label: LabelUpdateIn,
) -> db_label.Label:
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

    stored_label = await db_label.get_by_id(conn, label_id)
    if stored_label is None:
        raise HTTPException(status_code=404, detail="Label not found")

    updated_label = db_label.Label(
        **{**stored_label.model_dump(), **label.model_dump(exclude_unset=True)}
    )
    await db_label.update(
        conn,
        updated_label,
    )
    return updated_label


@router.delete("/project/{project_id}/label/{label_id}")
async def delete_label(
    project_id: uuid.UUID,
    label_id: uuid.UUID,
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
            status_code=401, detail="Not enough permissions to delete label"
        )

    await db_label.delete(conn, label_id)
