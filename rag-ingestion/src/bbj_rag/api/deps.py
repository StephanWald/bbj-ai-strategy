"""FastAPI dependency injection functions for the BBJ RAG API.

Provides request-scoped database connections from the async pool,
and access to shared application state (settings, Ollama client).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Request
from ollama import AsyncClient as OllamaAsyncClient
from psycopg import AsyncConnection

from bbj_rag.config import Settings


async def get_conn(request: Request) -> AsyncIterator[AsyncConnection[object]]:
    """Yield a connection from the async pool, returning it on completion."""
    pool = request.app.state.pool
    async with pool.connection() as conn:
        yield conn


def get_settings(request: Request) -> Settings:
    """Return the application-wide Settings instance."""
    return request.app.state.settings  # type: ignore[no-any-return]


def get_ollama_client(request: Request) -> OllamaAsyncClient:
    """Return the shared OllamaAsyncClient instance."""
    return request.app.state.ollama_client  # type: ignore[no-any-return]
