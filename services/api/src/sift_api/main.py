"""HTTP entrypoint for the sift API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sift_api.db import dispose_engine, get_engine
from sift_api.routes.health import router as health_router
from sift_api.routes.parse_smoke import router as parse_smoke_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    get_engine()
    yield
    await dispose_engine()


app = FastAPI(title="sift-api", version="0.0.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(parse_smoke_router)
