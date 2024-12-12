import uuid
from logging import getLogger
from typing import Annotated

import asyncpg
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from heron.db import get_connection
from heron.db import project as db_project
from heron.db import user as db_user

from .user import get_current_user

logger = getLogger(__name__)

router = APIRouter()


class ProjectCreateIn(BaseModel):
    members: list[uuid.UUID]
    title: str
    description: str


class ProjectUpdateIn(BaseModel):
    id: uuid.UUID
    members: list[uuid.UUID] | None = None
    title: str | None = None
    description: str | None = None


@router.post("/project")
async def create_project(
    project: ProjectCreateIn,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
):
    """
    Creates a new project, returns its id.
    """
    project_id = uuid.uuid4()
    try:
        await db_project.create(
            conn,
            db_project.Project(
                id=project_id,
                owner=current_user.id,
                members=project.members,
                title=project.title,
                description=project.description,
            ),
        )
    except Exception as exc:
        logger.exception(exc)
        raise HTTPException(status_code=500, detail="Failed to create project")

    return {"project_id": project_id}


@router.get("/project")
async def get_projects(
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
):
    """
    Returns all the projects the current user is a member of.
    """
    projects = await db_project.get_by_member(conn, current_user.id)
    return projects


@router.put("/project")
async def update_project(
    project: ProjectUpdateIn,
    conn: Annotated[asyncpg.Connection, Depends(get_connection)],
    current_user: Annotated[db_user.User, Depends(get_current_user)],
):
    stored_project = await db_project.get_by_id(conn, project.id)
    if stored_project is None:
        # Project doesn't exist at all
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.id not in stored_project.members:
        # The project exists but the current user is not a member
        raise HTTPException(status_code=404, detail="Project not found")

    if stored_project.owner != current_user.id:
        # Current user doesn't own this project, they can't edit it
        raise HTTPException(
            status_code=401, detail="Not enough permissions to update project"
        )

    await db_project.update_project(
        conn,
        db_project.Project(
            **{**stored_project.model_dump(), **project.model_dump(exclude_unset=True)}
        ),
    )
