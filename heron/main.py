from contextlib import asynccontextmanager

from fastapi import FastAPI

from heron.db import create_connection_pool, create_tables
from heron.routers import category, dataset, label, project, user


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection_pool = await create_connection_pool()
    await create_tables(connection_pool)
    yield {
        "db_pool": connection_pool,
    }
    await connection_pool.close()


app = FastAPI(lifespan=lifespan)

app.include_router(project.router)
app.include_router(user.router)
app.include_router(dataset.router)
app.include_router(label.router)
app.include_router(category.router)
