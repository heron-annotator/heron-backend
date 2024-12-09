from fastapi import FastAPI

from heron.routers import project

app = FastAPI()

app.include_router(project.router)
