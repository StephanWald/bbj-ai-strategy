"""Health check endpoint for the BBJ RAG application.

Reports database and Ollama connectivity status. Returns HTTP 200
when all checks pass (healthy), HTTP 503 when any check fails (degraded).
Docker HEALTHCHECK uses ``curl -f`` which fails on non-2xx responses,
so the 503 status correctly triggers container health failure.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import psycopg
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from bbj_rag.config import Settings

router = APIRouter()


@router.get("/health")
async def health() -> JSONResponse:
    """Check database and Ollama connectivity."""
    checks: dict[str, str] = {}

    # -- Database check (keyword args from Settings) --
    try:
        settings = Settings()
        conn = psycopg.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            dbname=settings.db_name,
        )
        conn.execute("SELECT 1")
        conn.close()
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

    all_ok = all(v == "ok" for v in checks.values())
    status = "healthy" if all_ok else "degraded"
    result: dict[str, Any] = {"status": status, "checks": checks}
    status_code = 200 if all_ok else 503

    return JSONResponse(content=result, status_code=status_code)
