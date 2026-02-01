# Technology Stack: RAG Deployment Service (v1.4 Milestone)

**Project:** BBj AI Strategy -- RAG Pipeline Docker Deployment
**Researched:** 2026-02-01
**Scope:** Docker Compose, retrieval REST API, MCP server for search_bbj_knowledge tool
**Overall confidence:** HIGH (versions verified via PyPI, Docker Hub, and GitHub as of 2026-02-01)

---

## Context: What This Stack Is For

This stack adds **deployment infrastructure** to the existing bbj-rag ingestion pipeline. The pipeline already works as a CLI tool (`bbj-rag ingest`); this milestone wraps it in Docker Compose and exposes retrieval via two interfaces:

1. **REST API** -- HTTP endpoint for hybrid search queries (consumed by future applications)
2. **MCP Server** -- Model Context Protocol server exposing `search_bbj_knowledge` as a tool (consumed by Claude Desktop, VS Code, and other MCP-compatible hosts)

The existing codebase provides: Python 3.12, psycopg3, pgvector Python bindings, Ollama embedder, Pydantic settings, Click CLI, and a `search.py` module with `hybrid_search()`, `dense_search()`, and `bm25_search()` functions that return `SearchResult` dataclasses. The deployment stack builds on top of these -- it does NOT replace them.

**Key constraint:** Ollama runs on the host macOS machine, not in Docker. Containers must reach it via `host.docker.internal:11434`.

---

## Recommended Stack

### Docker Images

| Image | Tag | Purpose | Why This Tag |
|-------|-----|---------|-------------|
| `pgvector/pgvector` | `0.8.0-pg17` | PostgreSQL 17 with pgvector extension | Version-pinned for reproducibility. PG17 is current stable. pgvector 0.8.0 is the latest version with a confirmed pg17 tag on Docker Hub. The `pg17` floating tag currently resolves to 0.8.0 or newer, but pinning avoids surprise upgrades. |
| `python` | `3.12-slim-bookworm` | Base image for API and MCP containers | Matches project's `requires-python = ">=3.12"`. Slim-bookworm minimizes image size (~150MB vs ~1GB full). Bookworm (Debian 12) is current stable. |
| `ghcr.io/astral-sh/uv` | `0.9.28` | uv binary for Dockerfile COPY --from | Pinned to current latest (2026-01-29). Used as a build-stage source only: `COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /bin/uv`. |

**Why PostgreSQL 17 over 16:** PG17 adds incremental JSON parsing, improved VACUUM performance, and better query planner cost estimates for JIT. Since this is a fresh deployment (not an upgrade of an existing PG16 database), there is no reason to use an older major version.

**Why pgvector 0.8.0 over 0.8.1:** The `0.8.1-pg17` tag does not yet appear as a confirmed published tag on Docker Hub (0.8.1 tags are confirmed only for pg18-trixie). The `0.8.0-pg17` and `0.8.0-pg17-bookworm` tags are confirmed available. If `0.8.1-pg17` becomes available by implementation time, it is safe to use -- pgvector follows semver for point releases.

**Confidence:** HIGH -- Docker Hub tags verified via web search 2026-02-01.

### Python Retrieval API

| Package | Version Constraint | Purpose | Why |
|---------|-------------------|---------|-----|
| `fastapi` | `>=0.115,<1` | REST API framework | Industry standard for Python async APIs. Already in the project's ecosystem (Pydantic models, httpx). Zero new conceptual overhead. The project's Pydantic v2 models serialize directly to FastAPI responses. |
| `uvicorn[standard]` | `>=0.32,<1` | ASGI server | Required to serve FastAPI. The `[standard]` extra includes uvloop and httptools for production performance. |
| `psycopg-pool` | `>=3.2,<4` | Connection pooling | The existing codebase uses raw `psycopg.connect()` per-operation. A connection pool is required for a long-running API server to avoid exhausting PostgreSQL connections. `psycopg-pool` is the official pool for psycopg3. Latest: 3.3.0. |

**Why FastAPI over alternatives:**

| Alternative | Why Not |
|-------------|---------|
| Litestar | Smaller ecosystem, less community support for MCP integration. FastAPI has direct ASGI mount support for MCP servers. |
| Flask | Synchronous by default. The embedding step (calling Ollama for query vectors) benefits from async I/O. Flask requires WSGI-to-ASGI bridging. |
| Django/DRF | Massive overhead for a single-endpoint retrieval API. Wrong tool for the job. |
| Starlette (raw) | FastAPI IS Starlette + Pydantic. Using raw Starlette means reimplementing request validation that FastAPI provides for free from the existing Pydantic models. |

**Why the version range `>=0.115,<1`:** FastAPI 0.115+ is the range that requires Python 3.9+ and has full Pydantic v2 compatibility. The `<1` bound is future-safe -- when FastAPI 1.0 ships, it may have breaking changes. Current latest is 0.128.0.

**Confidence:** HIGH -- FastAPI version verified via PyPI (0.128.0 as of 2026-02-01). uvicorn version verified (0.40.0). psycopg-pool version verified (3.3.0).

### MCP Server

| Package | Version Constraint | Purpose | Why |
|---------|-------------------|---------|-----|
| `mcp` | `>=1.25,<2` | Official MCP Python SDK | Provides `FastMCP` class with `@mcp.tool()` decorator and Streamable HTTP transport. The `>=1.25,<2` pin follows the official recommendation for production stability while v2 is in development. |

**What `mcp` brings transitively (DO NOT add these separately):**
- `anyio` (async I/O -- already in the project via httpx)
- `httpx` (already a direct dependency)
- `httpx-sse` (SSE client support)
- `pydantic` (already a direct dependency)
- `pydantic-settings` (already a direct dependency)
- `starlette` (ASGI framework -- also used by FastAPI)
- `sse-starlette` (SSE response support)
- `uvicorn` (ASGI server -- also needed by FastAPI)

This means the `mcp` package and `fastapi` share most of their dependency tree. Installing both adds minimal extra weight.

**Why the official `mcp` SDK, not standalone `fastmcp`:**

The standalone `fastmcp` package (by jlowin) is a superset with features like OpenAPI-to-MCP conversion, server composition, and proxying. For this project, we need exactly one tool (`search_bbj_knowledge`) registered on a single server -- the built-in `FastMCP` class in the official `mcp` SDK handles this perfectly. Adding standalone `fastmcp` would add complexity for features we do not need.

**MCP Transport choice: Streamable HTTP**

| Transport | Status | Fits This Project? |
|-----------|--------|-------------------|
| stdio | Active | No -- requires spawning the server as a child process. Does not work for a Docker-hosted remote service. |
| SSE | Deprecated | No -- superseded by Streamable HTTP in the 2025-11-25 spec. |
| Streamable HTTP | Recommended | Yes -- single HTTP endpoint, works with Docker networking, supports both request-response and streaming. |

The MCP server will be mounted on the same FastAPI ASGI application using `app.mount("/mcp", mcp.streamable_http_app())`. This means a single uvicorn process serves both the REST API and the MCP endpoint. No separate service required.

**Confidence:** HIGH -- MCP SDK v1.26.0 verified on PyPI (2026-01-24). Streamable HTTP transport verified as recommended in official docs. FastAPI ASGI mounting pattern verified in SDK docs and community examples.

### Supporting Configuration

| Package | Version Constraint | Purpose | Why |
|---------|-------------------|---------|-----|
| `pydantic-settings` | (already in project) | Environment-based configuration | Already used for `Settings` class with `BBJ_RAG_` prefix. Docker Compose will pass env vars that the existing Settings class reads automatically. No new config library needed. |

**No new configuration library needed.** The existing `Settings(BaseSettings)` class with `env_prefix="BBJ_RAG_"` works perfectly with Docker Compose `environment:` blocks. Example:

```yaml
environment:
  BBJ_RAG_DATABASE_URL: postgresql://bbj:secret@db:5432/bbj_rag
  OLLAMA_HOST: http://host.docker.internal:11434
```

The `OLLAMA_HOST` env var is read by the `ollama` Python client library natively -- it does not need to go through pydantic-settings.

---

## Complete New Dependencies

Only these packages need to be added to `pyproject.toml` for the v1.4 milestone:

```toml
[project]
dependencies = [
    # ... existing dependencies unchanged ...
    "fastapi>=0.115,<1",
    "uvicorn[standard]>=0.32,<1",
    "psycopg-pool>=3.2,<4",
    "mcp>=1.25,<2",
]
```

**That is 4 new direct dependencies.** All other needs (starlette, anyio, sse-starlette, etc.) are pulled transitively.

### Installation Command

```bash
cd rag-ingestion
uv add "fastapi>=0.115,<1" "uvicorn[standard]>=0.32,<1" "psycopg-pool>=3.2,<4" "mcp>=1.25,<2"
```

**Confidence:** HIGH -- All version ranges verified against current PyPI releases and existing project constraints.

---

## Docker Compose Architecture

### Service Layout

```yaml
services:
  db:
    image: pgvector/pgvector:0.8.0-pg17
    # PostgreSQL with pgvector. Schema applied via /docker-entrypoint-initdb.d/

  api:
    build: ./rag-ingestion
    # FastAPI + MCP server. Serves REST API on :8000 and MCP on :8000/mcp
    depends_on:
      db:
        condition: service_healthy
    extra_hosts:
      - "host.docker.internal:host-gateway"
    # extra_hosts is technically not needed on macOS Docker Desktop
    # (host.docker.internal is available by default), but including it
    # makes the compose file portable to Linux.
```

### Ollama Host Connectivity

On macOS with Docker Desktop, `host.docker.internal` resolves to the host machine automatically. The `extra_hosts` directive is included for Linux portability.

The existing `OllamaEmbedder` uses the `ollama` Python client which reads the `OLLAMA_HOST` environment variable. Set this in the api service:

```yaml
environment:
  OLLAMA_HOST: http://host.docker.internal:11434
```

No code changes needed in `embedder.py` -- the `ollama` client library handles the host resolution.

**Confidence:** HIGH -- Docker Desktop host.docker.internal behavior verified via multiple sources. The `ollama` Python library's `OLLAMA_HOST` env var is documented in Ollama's official docs.

### Database Initialization

The existing `sql/schema.sql` file can be mounted directly into the pgvector container:

```yaml
volumes:
  - ./sql/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
```

PostgreSQL's official Docker image automatically executes `.sql` files in `/docker-entrypoint-initdb.d/` on first startup. The existing schema uses `IF NOT EXISTS` throughout, making it idempotent.

### Health Checks

```yaml
db:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U bbj -d bbj_rag"]
    interval: 5s
    timeout: 5s
    retries: 5
```

The `api` service uses `depends_on: db: condition: service_healthy` to wait for PostgreSQL to be ready before starting.

---

## Dockerfile Strategy

### Multi-Stage Build with uv

```dockerfile
# Stage 1: Build
FROM python:3.12-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev
COPY . .
RUN uv sync --locked --no-dev

# Stage 2: Runtime
FROM python:3.12-slim-bookworm
COPY --from=builder /app /app
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "bbj_rag.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key decisions:**
- `--locked` ensures the uv.lock is respected exactly (reproducible builds)
- `--no-dev` excludes test/lint dependencies from the production image
- `UV_COMPILE_BYTECODE=1` pre-compiles .pyc files for faster startup
- Two-stage `uv sync` exploits Docker layer caching: dependency changes rebuild from the first `RUN`, source-only changes only rebuild the second `RUN`
- No `--mount=type=cache` on the uv cache -- simpler, and the two-stage pattern already provides good caching via Docker layers

**Confidence:** HIGH -- Pattern verified against official uv Docker documentation at docs.astral.sh.

---

## Integration Points with Existing Code

### Search Module (search.py)

The existing `hybrid_search()` function accepts a `psycopg.Connection` and returns `list[SearchResult]`. The API layer will:

1. Obtain a connection from `psycopg_pool.ConnectionPool`
2. Call `hybrid_search(conn, query_embedding, query_text, limit, generation_filter)`
3. Serialize `SearchResult` dataclasses to JSON via Pydantic response models

**No changes to search.py required.** The existing function signature is already clean for reuse.

### Embedder Module (embedder.py)

The API must embed the query text before calling `hybrid_search()`. The existing `OllamaEmbedder.embed_batch()` is synchronous (it calls `ollama.embed()` which is blocking). Two options:

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| Wrap in `asyncio.to_thread()` | No changes to embedder.py. Non-blocking in async context. | Small overhead from thread dispatch. | **Use this.** |
| Add `async def embed_batch_async()` | Native async. | Changes the existing tested interface. The `ollama` client's sync API would still block internally. | Not worth it for query-time single embeddings. |

The `asyncio.to_thread()` approach is correct because the Ollama client is CPU-bound for a single query embedding (sub-100ms). Thread dispatch overhead is negligible.

### Config Module (config.py)

The existing `Settings` class needs one addition for the API service:

```python
api_host: str = Field(default="0.0.0.0")
api_port: int = Field(default=8000)
```

These are optional -- uvicorn can also receive host/port from CLI args. But adding them to Settings allows Docker Compose to override via `BBJ_RAG_API_HOST` / `BBJ_RAG_API_PORT` env vars, maintaining the project's existing configuration pattern.

### Database Module (db.py)

The existing `get_connection()` function creates a single connection. For the API server, we need a connection pool. Add a `get_pool()` function:

```python
from psycopg_pool import ConnectionPool

def get_pool(database_url: str, min_size: int = 2, max_size: int = 10) -> ConnectionPool:
    """Create a psycopg connection pool with pgvector types registered."""
    pool = ConnectionPool(
        conninfo=database_url,
        min_size=min_size,
        max_size=max_size,
        open=False,  # Opened explicitly in FastAPI lifespan
        configure=lambda conn: register_vector(conn),
    )
    return pool
```

The `configure` callback ensures every connection from the pool has pgvector types registered, matching the existing `get_connection()` behavior.

### Models Module (models.py)

The existing `SearchResult` dataclass (in search.py) will need a corresponding Pydantic response model for the API. This can be a thin wrapper:

```python
class SearchResultResponse(BaseModel):
    id: int
    source_url: str
    title: str
    content: str
    doc_type: str
    generations: list[str]
    score: float
```

This mirrors the existing `SearchResult` dataclass fields exactly.

---

## MCP Server Integration Pattern

### Single-Process Architecture

The MCP server and REST API run in the **same uvicorn process** via ASGI mounting:

```python
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

app = FastAPI(title="BBj RAG API")
mcp_server = FastMCP(
    name="bbj-rag",
    stateless_http=True,
)

@mcp_server.tool()
def search_bbj_knowledge(
    query: str,
    generation: str | None = None,
    limit: int = 5,
) -> str:
    """Search BBj documentation using hybrid RAG retrieval."""
    # embed query, call hybrid_search, format results
    ...

# Mount MCP server on the same ASGI app
app.mount("/mcp", mcp_server.streamable_http_app())
```

**Why single-process, not separate services:**
- One tool (`search_bbj_knowledge`) does not justify a separate container
- Shared connection pool and embedder instance
- Simpler deployment and monitoring
- The MCP server and REST API share the same database and Ollama access

**Why `stateless_http=True`:**
- No session state to manage
- Simpler deployment (no session persistence needed)
- Compatible with horizontal scaling if ever needed
- The `search_bbj_knowledge` tool is pure retrieval -- no state between calls

### MCP Server stdio Support (For Local Dev)

For developers who want to use the MCP server locally with Claude Desktop via stdio transport (not Docker), provide a separate entry point:

```python
# bbj_rag/mcp_server.py
if __name__ == "__main__":
    mcp_server.run(transport="stdio")
```

This allows the same tool registration code to serve both Docker (Streamable HTTP via FastAPI mount) and local development (stdio via direct run). The `claude_desktop_config.json` would reference:

```json
{
  "mcpServers": {
    "bbj-rag": {
      "command": "uv",
      "args": ["run", "python", "-m", "bbj_rag.mcp_server"],
      "env": {
        "BBJ_RAG_DATABASE_URL": "postgresql://localhost:5432/bbj_rag"
      }
    }
  }
}
```

**Confidence:** HIGH -- FastMCP ASGI mounting pattern verified in official SDK docs. The `stateless_http` option verified in SDK examples.

---

## What NOT to Add (And Why)

| Temptation | Why Not |
|------------|---------|
| **SQLAlchemy / SQLModel** | The project uses raw psycopg3 SQL with explicit queries. Adding an ORM for 3 search queries and 1 insert operation adds abstraction without value. The existing `search.py` SQL is clean, tested, and performant. |
| **Alembic (migrations)** | The schema is applied via `schema.sql` with `IF NOT EXISTS`. For a single-table schema that changes rarely, a migration framework is overhead. Revisit if schema changes become frequent. |
| **Redis (caching)** | Query caching is premature. The hybrid search is already fast (<100ms with HNSW index). Add caching only when profiling shows it is needed. |
| **Celery / task queue** | Ingestion runs as a batch CLI operation, not as an API-triggered task. No async task queue needed for v1.4. |
| **nginx / reverse proxy** | Uvicorn can serve directly for this use case. The API serves a single internal tool. Add nginx only if you need TLS termination, rate limiting, or static file serving. |
| **Standalone `fastmcp` package** | The official `mcp` SDK's built-in `FastMCP` class is sufficient for a single-tool server. The standalone package adds server composition, proxying, and OpenAPI conversion that are not needed. |
| **`fastapi-mcp` package** | This auto-converts FastAPI endpoints to MCP tools. We want a single curated MCP tool with specific behavior, not an auto-mirror of REST endpoints. Manual `@mcp.tool()` registration gives full control. |
| **Docker Compose `ollama` service** | Ollama runs on the host for GPU access (macOS Metal). Containerizing it loses GPU acceleration and complicates model management. |
| **`pgbouncer`** | `psycopg_pool.ConnectionPool` provides application-level pooling. An external pooler is only needed for multi-service database sharing or very high connection counts. |
| **Gunicorn** | Uvicorn with `--workers` flag provides multi-process serving if needed. Gunicorn as a process manager adds complexity for marginal benefit at this scale. |

---

## Version Matrix (All Verified 2026-02-01)

### New Dependencies

| Package | Constraint | Current Latest | Verified Source |
|---------|-----------|---------------|-----------------|
| `fastapi` | `>=0.115,<1` | 0.128.0 | [PyPI](https://pypi.org/project/fastapi/) |
| `uvicorn[standard]` | `>=0.32,<1` | 0.40.0 | [PyPI](https://pypi.org/project/uvicorn/) |
| `psycopg-pool` | `>=3.2,<4` | 3.3.0 | [PyPI](https://pypi.org/project/psycopg-pool/) |
| `mcp` | `>=1.25,<2` | 1.26.0 | [PyPI](https://pypi.org/project/mcp/) |

### Docker Images

| Image | Tag | Verified Source |
|-------|-----|-----------------|
| `pgvector/pgvector` | `0.8.0-pg17` | [Docker Hub](https://hub.docker.com/r/pgvector/pgvector/tags) |
| `python` | `3.12-slim-bookworm` | [Docker Hub](https://hub.docker.com/_/python) |
| `ghcr.io/astral-sh/uv` | `0.9.28` | [GitHub Releases](https://github.com/astral-sh/uv/releases) |

### Existing Dependencies (Unchanged)

| Package | Current Constraint | Role | Changes for v1.4? |
|---------|--------------------|------|-------------------|
| `psycopg[binary]` | `>=3.3,<4` | Database driver | None. Pool uses same driver. |
| `pgvector` | `>=0.4,<0.5` | Python vector type support | None. |
| `pydantic` | `>=2.12,<3` | Data models | None. API response models extend same base. |
| `pydantic-settings` | `>=2.12,<3` | Configuration | None. Docker env vars work with existing Settings. |
| `ollama` | `>=0.6,<1` | Embedding client | None. OLLAMA_HOST env var configures remote access. |
| `httpx` | `>=0.28,<1` | HTTP client | None. Also a transitive dep of `mcp`. |
| `click` | `>=8.1,<9` | CLI | None. CLI commands remain for batch ingestion. |

---

## Alternatives Considered

### API Framework

| Option | Considered | Decision | Rationale |
|--------|-----------|----------|-----------|
| FastAPI | Yes | **Selected** | Native Pydantic integration, async support, ASGI mount for MCP, massive ecosystem, auto-docs via OpenAPI |
| Litestar | Yes | Rejected | Good framework but smaller ecosystem. No clear advantage over FastAPI for this use case. MCP mounting examples all target Starlette/FastAPI. |
| Flask | Yes | Rejected | WSGI, not ASGI. Would need `asgiref` bridging for async Ollama calls. No native Pydantic support. |
| Raw Starlette | Yes | Rejected | FastAPI adds Pydantic request/response validation for free. The search endpoint benefits from typed query parameters. |

### MCP SDK

| Option | Considered | Decision | Rationale |
|--------|-----------|----------|-----------|
| `mcp` (official SDK) | Yes | **Selected** | Built-in `FastMCP` with `@tool()` decorator. Supports stdio + Streamable HTTP. Maintained by MCP org. Pin `>=1.25,<2` for stability. |
| `fastmcp` (standalone) | Yes | Rejected | Superset of official SDK. Adds server composition, proxying, OpenAPI generation. These features are not needed for a single-tool server. Adds unnecessary dependency. |
| `fastapi-mcp` | Yes | Rejected | Auto-converts FastAPI endpoints to MCP tools. We want a curated tool with specific RAG behavior, not an auto-mirror. |
| Custom JSON-RPC | Yes | Rejected | Reinventing the wheel. The MCP SDK handles protocol compliance, tool schema generation, and transport management. |

### Connection Pooling

| Option | Considered | Decision | Rationale |
|--------|-----------|----------|-----------|
| `psycopg-pool` | Yes | **Selected** | Official pool for psycopg3. Supports sync and async. `configure` callback for pgvector registration. |
| `asyncpg` | Yes | Rejected | Would require rewriting all database code. The existing `search.py` uses psycopg3 SQL syntax. |
| Raw connections per request | Yes | Rejected | Exhausts PostgreSQL connections under load. Connection creation overhead (~50ms) per request is unacceptable. |
| pgbouncer container | Yes | Rejected | External pooler adds deployment complexity. Application-level pooling is sufficient for a single API server. |

### PostgreSQL Version

| Option | Considered | Decision | Rationale |
|--------|-----------|----------|-----------|
| PostgreSQL 17 | Yes | **Selected** | Current stable release. Fresh deployment, no migration concerns. Better VACUUM and planner. |
| PostgreSQL 16 | Yes | Rejected | No reason to use older version for a new deployment. |
| PostgreSQL 18 | Yes | Rejected | Not yet GA. pgvector 0.8.1-pg18-trixie exists but PG18 is pre-release. |

---

## Implications for Roadmap

### Phase 1: Docker Compose + Database

Start with Docker Compose and the pgvector service. Verify the existing `schema.sql` applies correctly in the container. Run the existing CLI `bbj-rag ingest` against the Dockerized database to confirm the full ingestion pipeline works with the containerized PostgreSQL.

- **Risk:** Low. Standard Docker Compose + PostgreSQL setup.
- **Key deliverable:** `docker compose up db` works, schema applied, ingestion succeeds.

### Phase 2: REST API

Add the FastAPI retrieval API with connection pooling. This is the core new code: an API endpoint that embeds a query via Ollama and runs hybrid search.

- **Risk:** Low-medium. The main integration point is `psycopg_pool` with pgvector type registration.
- **Key deliverable:** `POST /search` returns results; Swagger UI at `/docs` works.

### Phase 3: MCP Server

Add the MCP server with `search_bbj_knowledge` tool mounted on the same FastAPI app. This is mostly wiring -- the search logic is identical to the REST API endpoint.

- **Risk:** Medium. MCP SDK v1.x is mature but Streamable HTTP mounting on FastAPI has a known issue (#1367 in the SDK repo) around path handling. May require `streamable_http_path="/"` workaround.
- **Key deliverable:** MCP tool callable via Claude Desktop or MCP inspector.

### Phase Ordering Rationale

Database first because everything depends on it. REST API second because it validates the connection pooling and search integration without MCP protocol complexity. MCP server third because it reuses the search logic from the REST API and adds only MCP protocol wiring.

### Research Flags

- **Phase 3 (MCP):** The SDK's Streamable HTTP mounting on FastAPI may need workarounds. The issue (#1367) involves path prefix handling when mounting via `app.mount()`. Check the v1.x branch for fixes before implementation.
- **Phase 2 (API):** The `psycopg_pool.ConnectionPool.configure` callback for pgvector registration is straightforward but verify it works with the pool's `check_connection` logic.

---

## Sources

- [FastAPI - PyPI](https://pypi.org/project/fastapi/) -- Version 0.128.0, release notes, Python 3.9+ requirement
- [FastAPI Release Notes](https://fastapi.tiangolo.com/release-notes/) -- Pydantic v2 compatibility, Python version support
- [uvicorn - PyPI](https://pypi.org/project/uvicorn/) -- Version 0.40.0, ASGI server
- [MCP Python SDK - PyPI](https://pypi.org/project/mcp/) -- Version 1.26.0, v2 timeline Q1 2026
- [MCP Python SDK - GitHub](https://github.com/modelcontextprotocol/python-sdk) -- FastMCP API, Streamable HTTP transport, ASGI mounting
- [MCP SDK Issue #1367](https://github.com/modelcontextprotocol/python-sdk/issues/1367) -- Streamable HTTP mounting on FastAPI path issue
- [MCP Transport Protocols](https://mcpcat.io/guides/comparing-stdio-sse-streamablehttp/) -- stdio vs SSE vs Streamable HTTP comparison
- [psycopg-pool - PyPI](https://pypi.org/project/psycopg-pool/) -- Version 3.3.0, connection pool for psycopg3
- [psycopg3 Connection Pools](https://www.psycopg.org/psycopg3/docs/advanced/pool.html) -- FastAPI lifespan pattern, configure callback
- [pgvector/pgvector - Docker Hub](https://hub.docker.com/r/pgvector/pgvector/tags) -- Image tags, 0.8.0-pg17 confirmed
- [pgvector - GitHub](https://github.com/pgvector/pgvector) -- Version 0.8.1 source, Dockerfile defaults
- [uv Docker Guide](https://docs.astral.sh/uv/guides/integration/docker/) -- Multi-stage build pattern, version pinning
- [astral/uv - Docker Hub](https://hub.docker.com/r/astral/uv) -- Image tags for COPY --from
- [uv - GitHub Releases](https://github.com/astral-sh/uv/releases) -- Version 0.9.28 (2026-01-29)
- [FastAPI + psycopg3 Connection Pooling](https://spwoodcock.dev/blog/2024-10-fastapi-pydantic-psycopg/) -- Lifespan pattern, pool lifecycle
- [Docker host.docker.internal](https://forums.docker.com/t/how-to-link-my-ollama-with-my-app-in-docker/144682) -- macOS Docker Desktop connectivity
- [Ollama Docker Integration](https://docs.ollama.com/integrations/n8n) -- OLLAMA_HOST env var, host connectivity

---

*Research conducted 2026-02-01 via WebSearch for current package versions, Docker Hub tag verification, and GitHub issue review. All version numbers verified against PyPI and Docker Hub as of research date. Existing codebase analyzed for integration points.*
