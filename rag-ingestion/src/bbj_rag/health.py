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
from fastapi import APIRouter, Response

from bbj_rag.config import Settings

router = APIRouter()


@router.get("/health")
async def health(response: Response) -> dict[str, Any]:
    """Check database and Ollama connectivity."""
    checks: dict[str, str] = {}

    # -- Database check --
    try:
        settings = Settings()
        conn = psycopg.connect(settings.database_url)
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

    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    if status == "degraded":
        response.status_code = 503

    return {"status": status, "checks": checks}
