# Phase 22: REST Retrieval API - Research

**Researched:** 2026-02-01
**Domain:** FastAPI REST endpoints over psycopg3/pgvector hybrid search
**Confidence:** HIGH

## Summary

Phase 22 wraps the existing sync `hybrid_search()` function in FastAPI endpoints with proper async connection pooling, generation filtering, and health/stats capabilities. The existing codebase uses sync `psycopg` (v3.3) with manual connection management. The API layer needs an `AsyncConnectionPool` from `psycopg_pool` to serve concurrent requests efficiently, and the Ollama embedding call (needed to convert query text to a vector) needs its `AsyncClient` counterpart.

The existing `SearchResult` dataclass is missing `context_header` and `deprecated` fields required by API-04. These columns exist in the database schema but are not selected by the current search SQL queries. The search functions and dataclass will need to be extended before the API can expose them.

The architecture is straightforward: FastAPI lifespan initializes the pool and embedder, endpoints use dependency injection to get connections, Pydantic response models serialize results, and the existing health router is extended with readiness semantics.

**Primary recommendation:** Use `psycopg_pool.AsyncConnectionPool` with `configure=register_vector_async` callback, rewrite search SQL to use async cursors (psycopg3 async API mirrors sync exactly), and use `ollama.AsyncClient.embed()` for non-blocking query embedding.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `fastapi` | >=0.115,<1 | ASGI web framework | Already in project, async-native |
| `psycopg[binary]` | >=3.3,<4 | PostgreSQL adapter (sync+async) | Already in project, native async support |
| `psycopg-pool` | >=3.3,<4 | Connection pooling | Official psycopg pool package, `AsyncConnectionPool` with `configure` callback |
| `pgvector` | >=0.4,<0.5 | Vector type registration | Already in project, provides `register_vector_async` |
| `pydantic` | >=2.12,<3 | Response model validation | Already in project |
| `ollama` | >=0.6,<1 | Embedding generation | Already in project, `AsyncClient.embed()` for async |
| `uvicorn[standard]` | >=0.34,<1 | ASGI server | Already in project |
| `httpx` | >=0.28,<1 | HTTP client (health checks) | Already in project |

### New Dependency
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `psycopg-pool` | >=3.3,<4 | Async connection pooling | Required for `AsyncConnectionPool` -- NOT currently in pyproject.toml dependencies |

**Installation (add to pyproject.toml dependencies):**
```toml
"psycopg[binary,pool]>=3.3,<4",
```
This replaces the existing `"psycopg[binary]>=3.3,<4"` line. The `pool` extra pulls in `psycopg-pool`.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `AsyncConnectionPool` | `run_in_threadpool` wrapping sync search | Simpler but wastes threads, doesn't scale |
| `AsyncConnectionPool` | `NullConnectionPool` | No pre-created connections; better for multi-instance/PgBouncer setups but unnecessary for single-container deployment |
| Rewriting search SQL to async | `run_in_threadpool(hybrid_search, ...)` | Avoids touching search.py but adds thread overhead per request |

## Architecture Patterns

### Recommended Project Structure
```
src/bbj_rag/
├── app.py               # FastAPI app + lifespan (EXTEND)
├── health.py            # /health endpoint (EXTEND with readiness)
├── search.py            # Search functions (EXTEND: add context_header, deprecated to queries + dataclass)
├── api/                 # NEW: API layer
│   ├── __init__.py
│   ├── deps.py          # Dependency injection (pool, embedder)
│   ├── routes.py        # /search, /stats endpoints
│   └── schemas.py       # Pydantic request/response models
├── config.py            # Settings (unchanged)
├── embedder.py          # Embedder (unchanged -- sync Embedder still used by ingestion pipeline)
├── db.py                # DB functions (unchanged -- still used by ingestion pipeline)
└── ...
```

**Rationale:** Keep the new API layer in an `api/` subpackage to separate API concerns (routes, schemas, dependencies) from the existing ingestion pipeline code. The existing modules (`search.py`, `health.py`, `app.py`) get minimal extensions.

### Pattern 1: AsyncConnectionPool with Lifespan

**What:** Initialize pool + embedder in FastAPI lifespan, store on `app.state`, tear down on shutdown.

**When to use:** Always -- this is the standard FastAPI resource lifecycle pattern.

**Example:**
```python
# Source: psycopg official docs + FastAPI lifespan pattern
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool
from pgvector.psycopg import register_vector_async
from ollama import AsyncClient as OllamaAsyncClient

from bbj_rag.config import Settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
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

    # Store on app.state for dependency injection
    app.state.pool = pool
    app.state.settings = settings
    app.state.ollama_client = OllamaAsyncClient()

    yield

    await pool.close()
```

### Pattern 2: Dependency Injection for Connections

**What:** FastAPI `Depends()` yields a connection from the pool per-request, auto-returns on completion.

**When to use:** Every route that needs database access.

**Example:**
```python
# Source: psycopg pool docs + FastAPI dependency pattern
from typing import AsyncIterator

from fastapi import Depends, Request
from psycopg import AsyncConnection


async def get_conn(request: Request) -> AsyncIterator[AsyncConnection]:
    async with request.app.state.pool.connection() as conn:
        yield conn


async def get_embedder(request: Request) -> OllamaAsyncClient:
    return request.app.state.ollama_client
```

### Pattern 3: Async Search with psycopg3 AsyncConnection

**What:** Rewrite search SQL execution to use `AsyncConnection` and `await cursor.execute()`.

**When to use:** All search endpoints. The SQL itself is identical; only the connection/cursor calls change from sync to async.

**Example:**
```python
# Async equivalent of existing hybrid_search
async def async_hybrid_search(
    conn: AsyncConnection,
    query_embedding: list[float],
    query_text: str,
    limit: int = 10,
    generation_filter: str | None = None,
) -> list[SearchResult]:
    # Same SQL construction as existing hybrid_search()
    sql = ...  # identical SQL string
    params = ...  # identical param building

    async with conn.cursor() as cur:
        await cur.execute(sql, tuple(params))
        rows = await cur.fetchall()

    return _rows_to_results(rows)
```

### Pattern 4: Pydantic Response Models

**What:** Define request/response schemas as Pydantic BaseModel classes.

**When to use:** All API endpoints for validation, serialization, and OpenAPI docs.

**Example:**
```python
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    generation: str | None = Field(default=None, description="Filter by generation tag")
    limit: int = Field(default=10, ge=1, le=50, description="Max results to return")


class SearchResultItem(BaseModel):
    content: str
    title: str
    source_url: str
    doc_type: str
    generations: list[str]
    context_header: str
    deprecated: bool
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    count: int
```

### Pattern 5: Generation Normalization at API Layer

**What:** Normalize `bbj-gui` to `bbj_gui` before passing to search functions.

**When to use:** In the `/search` endpoint handler, before calling search.

**Example:**
```python
def normalize_generation(gen: str) -> str:
    return gen.replace("-", "_")
```

### Anti-Patterns to Avoid
- **Creating connections per-request without a pool:** Extremely expensive. Each PostgreSQL connection costs ~10MB RAM and significant CPU. Always use a pool.
- **Calling sync `psycopg.connect()` in an `async def` endpoint:** Blocks the event loop. Use `AsyncConnectionPool` or `run_in_threadpool`.
- **Loading the embedding model on every request:** The Ollama `embed()` call sends text to the Ollama server which keeps the model loaded. No in-process model loading needed. But the first embed call after Ollama starts may be slow (model load). A warm-up call during lifespan startup mitigates this.
- **Initializing pool at module import time:** Causes issues with multiple workers. Always initialize in lifespan.
- **Storing pool as a module-level global:** Use `app.state` instead for proper lifecycle management and testability.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Connection pooling | Manual connection tracking | `psycopg_pool.AsyncConnectionPool` | Handles min/max connections, health checks, connection recycling, configure callbacks |
| Async query embedding | `run_in_threadpool(embedder.embed_batch, ...)` | `ollama.AsyncClient.embed()` | Native async, no thread overhead, same API |
| Request validation | Manual query param parsing | Pydantic `BaseModel` as request body / `Query()` params | Auto-validation, error messages, OpenAPI schema |
| Response serialization | Manual dict building | Pydantic response models with `response_model=` | Type safety, auto-docs, consistent shape |
| Vector type registration | Manual per-connection registration | `configure=register_vector_async` pool callback | Automatically called for every new connection in the pool |
| JSON error responses | Custom error handlers | FastAPI's default `HTTPException` / `RequestValidationError` | Returns `{"detail": "message"}` format by default |

**Key insight:** psycopg3's async API is a 1:1 mirror of the sync API -- only `await` keywords are added. The SQL, parameter passing, and result handling are identical. This makes the async rewrite mechanical, not architectural.

## Common Pitfalls

### Pitfall 1: Missing `psycopg-pool` Dependency
**What goes wrong:** `ImportError: No module named 'psycopg_pool'` at startup.
**Why it happens:** `psycopg-pool` is a separate package, not included in `psycopg[binary]`.
**How to avoid:** Change dependency to `"psycopg[binary,pool]>=3.3,<4"` in pyproject.toml.
**Warning signs:** Import fails only at runtime, not at install time.

### Pitfall 2: Forgetting `register_vector_async` on Pool Connections
**What goes wrong:** `can't adapt type 'numpy.ndarray'` or vector type errors when querying.
**Why it happens:** Each new connection from the pool needs pgvector types registered. Without the `configure` callback, new connections won't understand vector types.
**How to avoid:** Pass `configure=register_vector_async` to `AsyncConnectionPool` constructor.
**Warning signs:** Works on first request (if a pre-configured connection), fails intermittently on subsequent requests when pool creates new connections.

### Pitfall 3: Blocking the Event Loop with Sync Ollama Calls
**What goes wrong:** `/search` endpoint blocks all concurrent requests while waiting for embedding.
**Why it happens:** Using `ollama.embed()` (sync) inside an `async def` endpoint.
**How to avoid:** Use `ollama.AsyncClient().embed()` with `await`.
**Warning signs:** High latency under concurrent load, health checks timing out during searches.

### Pitfall 4: Opening AsyncConnectionPool Synchronously
**What goes wrong:** Deprecation warning now, will break in future psycopg-pool versions.
**Why it happens:** Default `open=True` in constructor tries to open connections synchronously.
**How to avoid:** Always pass `open=False` and call `await pool.open()` in the lifespan.
**Warning signs:** Deprecation warnings in logs.

### Pitfall 5: SearchResult Missing context_header and deprecated
**What goes wrong:** API-04 requirement unmet; response lacks `context_header` and `deprecated`.
**Why it happens:** Current `SearchResult` dataclass and SQL queries don't include these columns.
**How to avoid:** Extend `SearchResult` with `context_header: str` and `deprecated: bool` fields, and add these columns to all SELECT statements in `search.py`.
**Warning signs:** Tests pass but API response shape doesn't match requirement API-04.

### Pitfall 6: Cold Ollama Model on First Search
**What goes wrong:** First `/search` request takes 10-30 seconds while Ollama loads the embedding model into memory.
**Why it happens:** Ollama lazy-loads models on first use.
**How to avoid:** Fire a warm-up embedding call during lifespan startup (after pool is open).
**Warning signs:** First request after deploy/restart is dramatically slower than subsequent ones.

### Pitfall 7: conninfo Format for AsyncConnectionPool
**What goes wrong:** Connection fails with parameter parsing errors.
**Why it happens:** `AsyncConnectionPool` takes a `conninfo` string in libpq key=value format, NOT a URL.
**How to avoid:** Use `f"host={h} port={p} dbname={d} user={u} password={pw}"` format, or use `psycopg.conninfo.make_conninfo()` helper.
**Warning signs:** Pool fails to open during startup, cryptic connection errors.

## Code Examples

### Complete /search Endpoint

```python
# Source: Verified pattern combining psycopg pool docs + FastAPI best practices
from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    conn: AsyncConnection = Depends(get_conn),
    ollama_client: OllamaAsyncClient = Depends(get_embedder),
    settings: Settings = Depends(get_settings),
) -> SearchResponse:
    # Normalize generation filter
    gen_filter = None
    if body.generation:
        gen_filter = body.generation.replace("-", "_")

    # Embed query (async, non-blocking)
    try:
        response = await ollama_client.embed(
            model=settings.embedding_model,
            input=body.query,
        )
        query_embedding = response["embeddings"][0]
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ollama embedding failed: {exc}")

    # Execute hybrid search (async)
    results = await async_hybrid_search(
        conn=conn,
        query_embedding=query_embedding,
        query_text=body.query,
        limit=body.limit,
        generation_filter=gen_filter,
    )

    return SearchResponse(
        query=body.query,
        results=[SearchResultItem(**r.__dict__) for r in results],
        count=len(results),
    )
```

### Complete /stats Endpoint

```python
# Source: Verified PostgreSQL aggregation pattern
@router.get("/stats", response_model=StatsResponse)
async def stats(conn: AsyncConnection = Depends(get_conn)) -> StatsResponse:
    async with conn.cursor() as cur:
        # Total count
        await cur.execute("SELECT count(*) FROM chunks")
        row = await cur.fetchone()
        total = row[0] if row else 0

        # By source (doc_type)
        await cur.execute(
            "SELECT doc_type, count(*) FROM chunks GROUP BY doc_type ORDER BY count(*) DESC"
        )
        by_source = {r[0]: r[1] for r in await cur.fetchall()}

        # By generation (unnest the array)
        await cur.execute(
            "SELECT g, count(*) FROM chunks, unnest(generations) AS g "
            "GROUP BY g ORDER BY count(*) DESC"
        )
        by_generation = {r[0]: r[1] for r in await cur.fetchall()}

    return StatsResponse(
        total_chunks=total,
        by_source=by_source,
        by_generation=by_generation,
    )
```

### Extended Health Endpoint

```python
# Source: Existing health.py pattern + readiness semantics from CONTEXT.md
@router.get("/health")
async def health(request: Request) -> JSONResponse:
    checks: dict[str, str] = {}
    pool = request.app.state.pool

    # Database check via pool
    try:
        async with pool.connection() as conn:
            await conn.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Ollama check
    ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ollama_host}/api/tags", timeout=5.0)
            resp.raise_for_status()
        checks["ollama"] = "ok"
    except Exception as exc:
        checks["ollama"] = f"error: {exc}"

    # Readiness: healthy / degraded / unhealthy
    ok_count = sum(1 for v in checks.values() if v == "ok")
    if ok_count == len(checks):
        status = "healthy"
        status_code = 200
    elif ok_count > 0:
        status = "degraded"
        status_code = 503
    else:
        status = "unhealthy"
        status_code = 503

    return JSONResponse(
        content={"status": status, "checks": checks},
        status_code=status_code,
    )
```

### Embedding Warm-Up in Lifespan

```python
# Source: Common pattern for Ollama model preloading
async def warm_up_embedder(client: OllamaAsyncClient, model: str) -> None:
    """Fire a dummy embedding call to ensure the model is loaded in Ollama."""
    try:
        await client.embed(model=model, input="warm-up")
        logger.info("Embedding model warm-up complete")
    except Exception as exc:
        logger.warning(f"Embedding warm-up failed (non-fatal): {exc}")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `psycopg.connect()` per request | `AsyncConnectionPool` with lifespan | psycopg-pool 3.1+ (2023) | Connection reuse, async native |
| `@app.on_event("startup")` | `@asynccontextmanager` lifespan | FastAPI 0.95 (2023) | Proper resource cleanup, context manager pattern |
| Sync `ollama.embed()` | `AsyncClient().embed()` | ollama-python 0.4+ (2024) | Non-blocking embedding, event loop friendly |
| Manual Settings per-call | `app.state` + dependency injection | FastAPI best practice | Single initialization, testable |
| `open=True` in pool constructor | `open=False` + `await pool.open()` | psycopg-pool deprecation notice | Future-proof, explicit lifecycle |

**Deprecated/outdated:**
- `@app.on_event("startup"/"shutdown")`: Still functional but deprecated in favor of lifespan context manager
- `psycopg_pool.AsyncConnectionPool(open=True)`: Deprecated, will be removed in future versions
- `register_vector(conn)` for async connections: Use `register_vector_async` instead

## Codebase Gap Analysis

Critical gaps between the current code and Phase 22 requirements:

### Gap 1: SearchResult Missing Fields (API-04)
- **Current:** `SearchResult` has `id, source_url, title, content, doc_type, generations, score`
- **Required:** Must also include `context_header` and `deprecated`
- **SQL impact:** All three search functions (`dense_search`, `bm25_search`, `hybrid_search`) need `context_header` and `deprecated` added to their SELECT column lists
- **Dataclass impact:** `SearchResult` needs two new fields
- **Row index impact:** `_rows_to_results` indexes into rows by position -- new columns shift indexes

### Gap 2: No Async Search Functions
- **Current:** `search.py` uses sync `psycopg.Connection` and `conn.cursor()`
- **Required:** Async versions for API endpoints
- **Approach:** Add new async functions alongside existing sync ones (don't break ingestion pipeline which still uses sync)

### Gap 3: No Connection Pool
- **Current:** Manual `psycopg.connect()` calls, caller manages lifecycle
- **Required:** `AsyncConnectionPool` for concurrent API requests
- **Approach:** Initialize pool in lifespan, pass via `app.state`

### Gap 4: No Async Embedder
- **Current:** `OllamaEmbedder.embed_batch()` uses sync `ollama.embed()`
- **Required:** Async embedding for non-blocking `/search`
- **Approach:** Use `ollama.AsyncClient.embed()` directly in API layer (don't modify existing `Embedder` class which is used by sync ingestion pipeline)

### Gap 5: psycopg-pool Not in Dependencies
- **Current:** `"psycopg[binary]>=3.3,<4"` in pyproject.toml
- **Required:** `"psycopg[binary,pool]>=3.3,<4"`

## Open Questions

1. **Pool sizing for single-container deployment**
   - What we know: Default `min_size=4`, `max_size` defaults to `None` (matches min_size, so fixed at 4). Single uvicorn worker per container.
   - What's unclear: Optimal pool size for the expected load pattern (MCP server + occasional curl)
   - Recommendation: Start with `min_size=2, max_size=5`. Low traffic expected; 2 idle connections is plenty, 5 handles burst from concurrent MCP requests. Easily tunable later.

2. **Whether to modify search.py or create new async versions**
   - What we know: The sync functions are used by the ingestion pipeline and search validation tests. The async API needs `AsyncConnection`.
   - What's unclear: Whether to add async versions to `search.py` or put them in `api/` module.
   - Recommendation: Add async functions to `search.py` alongside sync ones. Keeps all search logic in one place. The SQL is identical; only cursor/execute calls differ. Alternatively, create thin async wrappers in `api/` that call the same SQL.

3. **Ollama AsyncClient embed response shape**
   - What we know: Sync `ollama.embed()` returns `response.embeddings` (list of lists). Async should match.
   - What's unclear: Whether `AsyncClient.embed()` returns the same typed response object or a raw dict.
   - Recommendation: Validate during implementation. The async API should mirror sync, but verify the return type.

## Sources

### Primary (HIGH confidence)
- psycopg official pool docs: https://www.psycopg.org/psycopg3/docs/advanced/pool.html
- psycopg_pool API reference: https://www.psycopg.org/psycopg3/docs/api/pool.html
- pgvector-python GitHub: https://github.com/pgvector/pgvector-python
- FastAPI lifespan docs: https://fastapi.tiangolo.com/advanced/events/
- ollama-python GitHub: https://github.com/ollama/ollama-python
- Existing codebase: `rag-ingestion/src/bbj_rag/` (app.py, search.py, health.py, db.py, config.py, embedder.py, models.py, schema.py)

### Secondary (MEDIUM confidence)
- FastAPI + psycopg3 community patterns: https://spwoodcock.dev/blog/2024-10-fastapi-pydantic-psycopg/
- FastAPI best practices (zhanymkanov): https://github.com/zhanymkanov/fastapi-best-practices
- psycopg-pool PyPI (v3.3.0 confirmed): https://pypi.org/project/psycopg-pool/
- FastAPI async/sync guide: https://fastapi.tiangolo.com/async/

### Tertiary (LOW confidence)
- Ollama AsyncClient.embed() return type -- inferred from sync API, needs runtime verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in project except psycopg-pool (verified on PyPI)
- Architecture: HIGH - patterns verified against official psycopg and FastAPI docs
- Pitfalls: HIGH - identified from both docs and codebase gap analysis
- Code examples: MEDIUM - patterns verified but exact Ollama async response shape needs validation

**Research date:** 2026-02-01
**Valid until:** 2026-03-01 (stable ecosystem, 30-day validity)
