import uuid

import asyncpg
from pydantic import BaseModel


class Project(BaseModel):
    """
    Represents a project in the database.
    """

    id: uuid.UUID
    owner: uuid.UUID
    members: list[uuid.UUID]
    title: str
    description: str


async def create(conn: asyncpg.Connection, project: Project):
    """
    Creates a new project and all members relationships including the owner.
    """
    await conn.execute(
        "INSERT INTO projects "
        "(id, owner, title, description) "
        "VALUES ($1, $2, $3, $4)",
        project.id,
        project.owner,
        project.title,
        project.description,
    )
    # TODO: Delete project if membership transaction fails
    async with conn.transaction():
        await conn.execute(
            "INSERT INTO project_members (project_id, user_id) VALUES ($1, $2)",
            project.id,
            project.owner,
        )
        await conn.executemany(
            "INSERT INTO project_members (project_id, user_id) VALUES ($1, $2)",
            [(project.id, member) for member in project.members],
        )


async def get_by_id(conn: asyncpg.Connection, project_id: uuid.UUID) -> Project | None:
    """
    Finds a project by its id. Returns None if not found.
    """
    record: asyncpg.Record | None = await conn.fetchrow(
        "SELECT "
        "projects.id,"
        "projects.owner, "
        "projects.title, "
        "projects.description, "
        "ARRAY_AGG(project_members.user_id) as members "
        "FROM projects "
        "JOIN project_members ON projects.id = project_members.project_id "
        "WHERE project_members.project_id = $1 "
        "GROUP BY projects.id, projects.owner, projects.title, projects.description",
        project_id,
    )
    if record is not None:
        return Project(**record)
    return None


async def get_by_member(conn: asyncpg.Connection, user_id: uuid.UUID) -> list[Project]:
    """
    Finds all projects this user is member of.
    """
    records: list[asyncpg.Record] = await conn.fetch(
        "SELECT "
        "projects.id, "
        "projects.owner, "
        "projects.title, "
        "projects.description, "
        "ARRAY_AGG(project_members.user_id) as members "
        "FROM projects "
        "JOIN project_members ON projects.id = project_members.project_id "
        "WHERE project_members.user_id = $1 "
        "GROUP BY projects.id, projects.owner, projects.title, projects.description",
        user_id,
    )
    return [Project(**r) for r in records]


async def update_project(conn: asyncpg.Connection, project: Project):
    """
    Updates a project.
    """
    await conn.execute(
        "UPDATE projects "
        "SET owner = $2, title = $3, description = $4 "
        "WHERE id = $1",
        project.id,
        project.owner,
        project.title,
        project.description,
    )
