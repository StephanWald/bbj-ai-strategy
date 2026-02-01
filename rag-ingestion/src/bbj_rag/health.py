"""Health check endpoint for the BBJ RAG application.

Reports database and Ollama connectivity status with three-tier
readiness semantics:

- **healthy** (200): all checks pass
- **degraded** (503): some checks pass, some fail
- **unhealthy** (503): all checks fail

The database check uses the async connection pool from ``app.state``
when available, falling back to a standalone ``psycopg.connect()`` if
the pool is not yet initialised (early startup race).

Docker HEALTHCHECK uses ``curl -f`` which fails on non-2xx responses,
so the 503 status correctly triggers container health failure.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import psycopg
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from bbj_rag.config import Settings

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> JSONResponse:
    """Check database and Ollama connectivity."""
    checks: dict[str, str] = {}

    # -- Database check (prefer pool, fallback to standalone connect) --
    try:
        pool = getattr(request.app.state, "pool", None)
        if pool is not None:
            async with pool.connection() as conn:
                await conn.execute("SELECT 1")
        else:
            # Fallback for early startup before pool initialisation
            settings = Settings()
            sync_conn = psycopg.connect(
                host=settings.db_host,
                port=settings.db_port,
                user=settings.db_user,
                password=settings.db_password,
                dbname=settings.db_name,
            )
            sync_conn.execute("SELECT 1")
            sync_conn.close()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # -- Ollama check --
    ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ollama_host}/api/tags", timeout=5.0)
            resp.raise_for_status()
        checks["ollama"] = "ok"
    except Exception as exc:
        checks["ollama"] = f"error: {exc}"

    # -- Three-tier readiness semantics --
    ok_count = sum(1 for v in checks.values() if v == "ok")
    if ok_count == len(checks):
        status, status_code = "healthy", 200
    elif ok_count > 0:
        status, status_code = "degraded", 503
    else:
        status, status_code = "unhealthy", 503

    result: dict[str, Any] = {"status": status, "checks": checks}
    return JSONResponse(content=result, status_code=status_code)
