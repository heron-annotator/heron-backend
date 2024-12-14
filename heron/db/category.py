import uuid

import asyncpg
from pydantic import BaseModel


class Category(BaseModel):
    """
    Represents a category in the database.
    """

    id: uuid.UUID
    label_id: uuid.UUID
    project_id: uuid.UUID
    dataset_id: uuid.UUID
    start_offset: int
    end_offset: int


async def create(conn: asyncpg.Connection, category: Category):
    """
    Creates a new category.
    """
    await conn.execute(
        "INSERT INTO categories "
        "(id, label_id, project_id, dataset_id, start_offset, end_offset) "
        "VALUES ($1, $2, $3, $4, $5, $6)",
        category.id,
        category.label_id,
        category.project_id,
        category.dataset_id,
        category.start_offset,
        category.end_offset,
    )


async def get_by_id(
    conn: asyncpg.Connection, category_id: uuid.UUID
) -> Category | None:
    """
    Gets a category by its id.
    """
    record: asyncpg.Record | None = await conn.fetchrow(
        "SELECT id, label_id, project_id, dataset_id, start_offset, end_offset "
        "FROM categories WHERE id = $1",
        category_id,
    )
    if record is None:
        return None

    return Category(**record)


async def get_by_dataset(
    conn: asyncpg.Connection, dataset_id: uuid.UUID
) -> list[Category]:
    """
    Gets all categories for a dataset.
    """
    records: list[asyncpg.Record] = await conn.fetch(
        "SELECT id, label_id, project_id, dataset_id, start_offset, end_offset "
        "FROM categories WHERE dataset_id = $1",
        dataset_id,
    )
    return [Category(**r) for r in records]


async def update(conn: asyncpg.Connection, category: Category):
    """
    Updates a category.
    """
    await conn.execute(
        "UPDATE categories SET start_offset = $2, end_offset = $3 WHERE id = $1",
        category.id,
        category.start_offset,
        category.end_offset,
    )


async def delete_category(conn: asyncpg.Connection, category_id: uuid.UUID):
    """
    Deletes a category.
    """
    await conn.execute("DELETE FROM categories WHERE id = $1", category_id)
