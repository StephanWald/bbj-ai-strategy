"""FastAPI application entrypoint for the BBJ RAG service.

Lifespan handler validates the environment, logs a startup summary,
applies the pgvector schema idempotently, initialises an async connection
pool with pgvector type registration, and warms up the Ollama embedding
model on every startup.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from bbj_rag.api.routes import router as api_router
from bbj_rag.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup tasks: validate env, log config, apply schema, init pool."""
    # Imports inside lifespan to avoid circular imports and keep module
    # importable without side effects (important for testing).
    from ollama import AsyncClient as OllamaAsyncClient
    from pgvector.psycopg import register_vector_async  # type: ignore[import-untyped]
    from psycopg_pool import AsyncConnectionPool

    from bbj_rag.config import Settings
    from bbj_rag.db import get_connection_from_settings
    from bbj_rag.schema import apply_schema
    from bbj_rag.startup import log_startup_summary, validate_environment

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    startup_logger = logging.getLogger("bbj_rag.startup")

    validate_environment()
    settings = Settings()
    log_startup_summary(settings)

    # Apply schema idempotently (sync connection, used once)
    conn = get_connection_from_settings(settings)
    try:
        apply_schema(conn)
        startup_logger.info("Schema applied successfully")
    finally:
        conn.close()

    # Build async connection pool with pgvector type registration
    conninfo = (
        f"host={settings.db_host} port={settings.db_port} "
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password}"
    )
    pool = AsyncConnectionPool(
        conninfo=conninfo,
        min_size=2,
        max_size=5,
        open=False,
        configure=register_vector_async,
    )
    await pool.open()
    startup_logger.info("Async connection pool opened (min=2, max=5)")

    # Create Ollama async client and warm up embedding model
    ollama_client = OllamaAsyncClient()
    try:
        await ollama_client.embed(model=settings.embedding_model, input="warm-up")
        startup_logger.info("Embedding model warmed up: %s", settings.embedding_model)
    except Exception:
        startup_logger.warning("Embedding warm-up failed (non-fatal)")

    # Store shared state for dependency injection
    app.state.pool = pool
    app.state.settings = settings
    app.state.ollama_client = ollama_client

    yield

    # Shutdown: close pool connections
    await pool.close()
    startup_logger.info("Async connection pool closed")


app = FastAPI(title="BBJ RAG", lifespan=lifespan)
app.include_router(health_router)
app.include_router(api_router)
