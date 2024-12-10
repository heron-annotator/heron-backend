from fastapi import FastAPI

from heron.routers import project, user

app = FastAPI()

app.include_router(project.router)
app.include_router(user.router)
