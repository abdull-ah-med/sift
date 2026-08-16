"""HTTP entrypoint for the sift API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sift_api.db import dispose_engine, get_engine
from sift_api.routes.chat import router as chat_router
from sift_api.routes.health import router as health_router
from sift_api.routes.invites import router as invites_router
from sift_api.routes.parse_smoke import router as parse_smoke_router
from sift_api.routes.review import router as review_router
from sift_api.routes.v1 import router as v1_router
from sift_api.settings import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if settings.sift_otel_enabled:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from sift_obs import setup_logging, setup_tracing

        setup_tracing(
            service_name="sift-api",
            otlp_endpoint=settings.sift_otlp_endpoint,
        )
        setup_logging(json_logs=True)
        FastAPIInstrumentor.instrument_app(_app)
    get_engine()
    try:
        yield
    finally:
        from sift_api.checkpointer import close_postgres_checkpointer

        await close_postgres_checkpointer()
        await dispose_engine()


app = FastAPI(title="sift-api", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(parse_smoke_router)
app.include_router(v1_router)
app.include_router(review_router)
app.include_router(chat_router)
app.include_router(invites_router)
