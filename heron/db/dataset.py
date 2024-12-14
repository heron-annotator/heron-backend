import uuid

import asyncpg
from pydantic import BaseModel


class Dataset(BaseModel):
    """
    Represents a dataset in the database.
    """

    id: uuid.UUID
    project_id: uuid.UUID
    filename: str | None
    text: str


async def create(conn: asyncpg.Connection, dataset: Dataset) -> str:
    """
    Creates a new dataset in the database.
    """
    return await conn.execute(
        "INSERT INTO datasets "
        "(id, project_id, filename, text) "
        "VALUES ($1, $2, $3, $4)",
        dataset.id,
        dataset.project_id,
        dataset.filename,
        dataset.text,
    )


async def get_by_project(
    conn: asyncpg.Connection, project_id: uuid.UUID
) -> list[Dataset]:
    """
    Gets a dataset by its id.
    """
    record: list[asyncpg.Record] = await conn.fetch(
        "SELECT id, project_id, filename, text FROM datasets WHERE project_id = $1",
        project_id,
    )
    if record is None:
        return None
    return [Dataset(**r) for r in record]


async def get_by_id(conn: asyncpg.Connection, dataset_id: uuid.UUID) -> Dataset | None:
    """
    Gets a dataset by its id.
    """
    record: asyncpg.Record | None = await conn.fetchrow(
        "SELECT id, project_id, filename, text FROM datasets WHERE id = $1", dataset_id
    )
    if record is None:
        return None

    return Dataset(**record)


async def delete(conn: asyncpg.Connection, dataset_id: uuid.UUID):
    """
    Deletes a dataset from the database.
    """
    await conn.execute("DELETE FROM datasets WHERE id = $1", dataset_id)
