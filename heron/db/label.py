import uuid

import asyncpg
from pydantic import BaseModel


class Label(BaseModel):
    """
    Represents a label in the database.
    """

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    color: str


async def create(conn: asyncpg.Connection, label: Label) -> str:
    """
    Creates a new label in the database.
    """
    return await conn.execute(
        "INSERT INTO labels "
        "(id, project_id, name, color) "
        "VALUES ($1, $2, $3, $4)",
        label.id,
        label.project_id,
        label.name,
        label.color,
    )


async def get_by_id(conn: asyncpg.Connection, label_id: uuid.UUID) -> Label | None:
    """
    Gets a label by its id.
    """
    record: asyncpg.Record | None = await conn.fetchrow(
        "SELECT id, project_id, name, color FROM labels WHERE id = $1", label_id
    )
    if record is None:
        return None

    return Label(**record)


async def get_by_project(
    conn: asyncpg.Connection, project_id: uuid.UUID
) -> list[Label]:
    """
    Gets all labels for a project.
    """
    records: list[asyncpg.Record] = await conn.fetch(
        "SELECT id, project_id, name, color FROM labels WHERE project_id = $1",
        project_id,
    )
    return [Label(**r) for r in records]


async def update(conn: asyncpg.Connection, label: Label):
    """
    Updates a label.
    """
    await conn.execute(
        "UPDATE labels SET name = $2, color = $3 WHERE id = $1",
        label.id,
        label.name,
        label.color,
    )


async def delete(conn: asyncpg.Connection, label_id: uuid.UUID):
    """
    Deletes a label from the database.
    """
    await conn.execute("DELETE FROM labels WHERE id = $1", label_id)
