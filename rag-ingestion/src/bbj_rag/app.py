"""FastAPI application entrypoint for the BBJ RAG service.

Lifespan handler validates the environment, logs a startup summary,
and applies the pgvector schema idempotently on every startup.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from bbj_rag.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup tasks: validate env, log config, apply schema."""
    # Imports inside lifespan to avoid circular imports and keep module
    # importable without side effects (important for testing).
    from bbj_rag.config import Settings
    from bbj_rag.db import get_connection_from_settings
    from bbj_rag.schema import apply_schema
    from bbj_rag.startup import log_startup_summary, validate_environment

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    startup_logger = logging.getLogger("bbj_rag.startup")

    validate_environment()
    settings = Settings()
    log_startup_summary(settings)

    # Apply schema idempotently
    conn = get_connection_from_settings(settings)
    try:
        apply_schema(conn)
        startup_logger.info("Schema applied successfully")
    finally:
        conn.close()

    yield
    # Shutdown (nothing to clean up yet)


app = FastAPI(title="BBJ RAG", lifespan=lifespan)
app.include_router(health_router)
