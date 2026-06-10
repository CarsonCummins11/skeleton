import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

import lib.config
import routes.item_routes
import routes.user_routes
from internal.routes import router as internal_router
from lib import db
from lib.test_util import insert_test_data

logging.basicConfig(level=logging.INFO)
logging.getLogger("passlib").setLevel(logging.ERROR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.open_db_connection_pool()
    if lib.config.is_dev():
        async with await db.open_db_connection() as connection:
            with open("../api/schema.sql") as f:
                await connection.execute(f.read())
        await insert_test_data()
    yield
    await db.close_db_connection_pool()


app = FastAPI(lifespan=lifespan)

origins = [os.environ.get("FRONTEND_URL", "")]
if not origins[0]:
    raise ValueError("FRONTEND_URL environment variable is not set")

logging.info(f"origins: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_secret = os.environ.get("SESSION_SECRET_KEY")
if not session_secret:
    raise ValueError("SESSION_SECRET_KEY environment variable is not set")
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    max_age=3600 * 24 * 7,
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


internal_static_dir = Path(__file__).parent / "internal" / "static"
app.mount(
    "/internal/static",
    StaticFiles(directory=internal_static_dir),
    name="internal_static",
)

app.include_router(internal_router, prefix="/internal", tags=["internal"])
app.include_router(routes.user_routes.router, prefix="/u", tags=["user"])
app.include_router(routes.item_routes.router, prefix="/items", tags=["items"])
