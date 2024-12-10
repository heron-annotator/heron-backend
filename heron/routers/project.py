from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

router = APIRouter()


class Project(BaseModel):
    id: str
    owner: str
    members: list[str]
    title: str
    description: str


# Temp stuff to simulate a DB
_last_id: int = 0
_projects: dict[str, Project] = {}


class ProjectCreateIn(BaseModel):
    members: list[str]
    title: str
    description: str


class ProjectUpdateIn(BaseModel):
    members: list[str] | None = None
    title: str | None = None
    description: str | None = None


# TODO: Should get only the projects for the current user
@router.get("/project/")
def get_projects():
    return _projects


# TODO: Make the current user the owner
@router.post("/project/")
def create_project(project: ProjectCreateIn):
    global _last_id
    id = str(_last_id)
    _projects[id] = Project(
        id=id,
        owner="someone",
        members=project.members,
        title=project.title,
        description=project.description,
    )
    _last_id += 1


# TODO: Check the user has permissions to do this things
@router.put("/project/{project_id}")
def update_project(project_id: str, project: ProjectUpdateIn):
    if project_id not in _projects:
        raise HTTPException(status_code=404)

    data = project.model_dump(exclude_unset=True)
    _projects[project_id] = Project(**_projects[project_id].model_dump(), **data)
