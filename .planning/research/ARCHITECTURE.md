# Architecture: RAG Deployment (Docker + REST API + MCP Server)

**Milestone:** RAG Service Deployment
**Researched:** 2026-02-01
**Confidence:** HIGH (existing codebase analysis, Docker patterns, MCP SDK docs)

> **Context:** The bbj_rag package is a working src-layout Python 3.12 CLI application with 6 parsers, an intelligence pipeline, chunker, embedder, and hybrid search module. This document defines how Docker Compose, a REST retrieval API, and an MCP server integrate with that existing codebase -- not a rewrite.

---

## 1. Service Topology

```
                         macOS Host
                    +------------------+
                    |   Ollama :11434  |
                    +--------+---------+
                             |
               host.docker.internal:11434
                             |
        Docker Compose Network (bbj-rag-net)
   +-----------------------------+---------------------------+
   |                             |                           |
   |  +------------------+      |  +-----------------------+ |
   |  | pgvector (db)    |      |  | bbj-rag-app           | |
   |  | pg17 + pgvector  |      |  |                       | |
   |  | :5432            |      |  |  bbj-rag ingest ...   | |
   |  |                  |<---->|  |  uvicorn (REST :8000)  | |
   |  | volume:          |      |  |  mcp stdio server     | |
   |  |   pgdata:/var/   |      |  |                       | |
   |  |   lib/postgresql |      |  | volumes:              | |
   |  +------------------+      |  |   /data/flare (ro)    | |
   |                             |  |   /data/pdf   (ro)   | |
   |                             |  |   /data/mdx   (ro)   | |
   |                             |  |   /data/bbj   (ro)   | |
   |                             |  +-----------------------+ |
   +-----------------------------+---------------------------+
```

### Three containers, one network

| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| `db` | `pgvector/pgvector:0.8.1-pg17` | `5432:5432` | PostgreSQL 17 + pgvector 0.8.1 |
| `app` | Custom Dockerfile (bbj-rag) | `8000:8000` | CLI ingestion, REST API, MCP server |
| Ollama | **Not in Compose** -- runs on macOS host | `11434` (host) | Embedding model (accessed via `host.docker.internal`) |

**Why Ollama stays on the host:** Ollama uses macOS Metal GPU acceleration. Running it in a Linux Docker container on macOS loses GPU access entirely. The app container reaches it at `http://host.docker.internal:11434`.

**Why a single app container (not separate API + MCP):** The REST API and MCP server share the exact same search functions (`search.py`), the same database connection logic (`db.py`), and the same config (`config.py`). Running them as separate containers would double the image size and deployment complexity for zero architectural benefit. The MCP server runs via stdio (spawned by Claude Desktop per-session) and the REST API runs as a long-lived uvicorn process -- they do not conflict.

---

## 2. Integration with Existing Modules

### What Stays Unchanged

These modules require **zero modification** for deployment:

| Module | Why Unchanged |
|--------|---------------|
| `search.py` | Already accepts `conn` + query params, returns `SearchResult` dataclass. API/MCP just call these functions. |
| `db.py` | `get_connection(database_url)` is the only entry point. Just pass a different URL. |
| `models.py` | `Document`, `Chunk`, `SearchResult` data models are transport-agnostic. |
| `chunker.py` | Pure function, no I/O dependencies. |
| `pipeline.py` | `run_pipeline()` takes injected dependencies. Works from CLI or programmatically. |
| `embedder.py` | `OllamaEmbedder` uses the `ollama` Python client which reads `OLLAMA_HOST` env var. Set it in Docker and it just works. |
| `intelligence/` | Pure classification logic, no external dependencies. |
| `parsers/` | Read from filesystem paths or HTTP URLs. Paths change via config; code unchanged. |

### What Gets Modified

| Module | Change | Reason |
|--------|--------|--------|
| `config.py` | Add `ollama_host` field (default `http://localhost:11434`) | Explicit Ollama URL config for Docker; the `ollama` client reads `OLLAMA_HOST` env var, but we also need it for the API health check. |
| `schema.py` | Fix `_SQL_DIR` path resolution for installed packages | Currently uses `Path(__file__).resolve().parent.parent.parent / "sql"` which breaks when installed via pip in a container. Use `importlib.resources` or bundle sql in package data. |

### What Gets Added

| New Module | Location | Purpose |
|------------|----------|---------|
| `src/bbj_rag/api.py` | New file | FastAPI app wrapping `search.py` functions |
| `src/bbj_rag/mcp_server.py` | New file | FastMCP server exposing `search_bbj_knowledge` tool |
| `Dockerfile` | `rag-ingestion/Dockerfile` | Multi-stage build for the bbj-rag package |
| `compose.yaml` | `rag-ingestion/compose.yaml` | Service definitions for db + app |
| `sql/init.sql` | New or rename | Entrypoint script for pgvector container initialization |

---

## 3. REST Retrieval API (`api.py`)

### Framework Choice: FastAPI

**Use FastAPI** because:
1. The project already depends on Pydantic (v2.12+) -- FastAPI uses it natively for request/response validation.
2. Auto-generated OpenAPI docs (`/docs`) provide immediate testing UI for the search endpoint.
3. Async support is native -- the search functions use synchronous psycopg3, but FastAPI handles them cleanly via threadpool execution for sync endpoints.
4. Adding FastAPI is one dependency (`fastapi[standard]`) which includes uvicorn.

**Architecture:**

```python
# src/bbj_rag/api.py (conceptual structure)

from fastapi import FastAPI, Depends
from bbj_rag.config import Settings
from bbj_rag.db import get_connection
from bbj_rag.embedder import create_embedder
from bbj_rag.search import hybrid_search, SearchResult

app = FastAPI(title="BBj RAG Search API")

# Singleton settings + embedder (created once at startup)
# Connection pool or per-request connection via dependency injection

@app.get("/health")
def health():
    """Liveness check -- verifies DB and Ollama connectivity."""
    ...

@app.post("/search")
def search(query: str, limit: int = 5, generation: str | None = None):
    """Hybrid search: embed query via Ollama, then RRF over dense+BM25."""
    # 1. Embed the query text using the embedder
    # 2. Call hybrid_search(conn, embedding, query, limit, generation)
    # 3. Return list of SearchResult as JSON
    ...
```

### Key Design Decisions

**Connection management:** Use psycopg3's `ConnectionPool` (from `psycopg_pool`) rather than creating a new connection per request. The existing `get_connection()` function opens a bare connection -- the API layer adds pooling on top. This is a new dependency (`psycopg-pool`) but it is the official psycopg3 companion library.

**Embedder lifecycle:** Create one `OllamaEmbedder` instance at startup via FastAPI's lifespan context. The embedder is stateless (just holds model name + dimensions), so a single instance is safe for concurrent use.

**Response model:** Convert `SearchResult` dataclass to a Pydantic model for the API response, or use `dataclasses.asdict()`. Since `SearchResult` is a frozen dataclass with simple types, serialization is trivial.

**Single endpoint to start:** `/search` is the only retrieval endpoint needed. `/health` for operational monitoring. Expand later if needed.

---

## 4. MCP Server (`mcp_server.py`)

### SDK Choice: Official MCP Python SDK (FastMCP)

Use `mcp` package (the official SDK, which includes FastMCP). Currently at v1.26.0, stable for production. v2 anticipated Q1 2026 but v1.x will be maintained.

**Architecture:**

```python
# src/bbj_rag/mcp_server.py (conceptual structure)

from mcp.server.fastmcp import FastMCP
from bbj_rag.config import Settings
from bbj_rag.db import get_connection
from bbj_rag.embedder import create_embedder
from bbj_rag.search import hybrid_search

mcp = FastMCP("bbj-knowledge")

@mcp.tool()
def search_bbj_knowledge(
    query: str,
    generation: str | None = None,
    limit: int = 5,
) -> str:
    """Search the BBj documentation knowledge base.

    Returns relevant documentation chunks ranked by hybrid
    (dense vector + BM25 keyword) search with RRF fusion.

    Args:
        query: Natural language search query about BBj programming.
        generation: Optional BBj generation filter (e.g. "BBj", "Visual PRO/5").
        limit: Maximum number of results to return (default 5).
    """
    # 1. Embed query
    # 2. hybrid_search(conn, embedding, query, limit, generation)
    # 3. Format results as readable text for LLM consumption
    ...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Key Design Decisions

**Transport: stdio only (for now).** The MCP server is spawned by Claude Desktop or Claude Code as a child process. stdio is the correct transport for local desktop usage. Streamable HTTP would be needed for web-based multi-user access, but that is a future concern -- not this milestone.

**Separate process, not separate container.** The MCP server runs as `uv run python -m bbj_rag.mcp_server` on the host machine (not inside Docker). Reason: Claude Desktop spawns MCP servers as local child processes via stdio. It cannot connect to a process running inside a Docker container via stdio. The MCP server needs direct access to the database (via the Docker-exposed port 5432) and Ollama (localhost:11434).

**Return format: formatted text, not JSON.** MCP tool results are consumed by LLMs, not APIs. Return human-readable formatted text with source URLs, titles, and content excerpts. The LLM does not need structured JSON -- it needs readable context.

**Single tool.** `search_bbj_knowledge` is the only tool for this milestone. The project context mentions this explicitly. Additional tools (code generation, compile check) are future milestones.

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "bbj-knowledge": {
      "command": "uv",
      "args": [
        "--directory", "/Users/beff/_workspace/bbj-ai-strategy/rag-ingestion",
        "run", "python", "-m", "bbj_rag.mcp_server"
      ],
      "env": {
        "BBJ_RAG_DATABASE_URL": "postgresql://bbj_rag:bbj_rag@localhost:5432/bbj_rag"
      }
    }
  }
}
```

The MCP server runs on the host, connects to pgvector via the Docker-exposed port (localhost:5432), and to Ollama at localhost:11434. No `host.docker.internal` needed from the MCP server's perspective.

---

## 5. Docker Compose Design

### compose.yaml Structure

```yaml
# rag-ingestion/compose.yaml
services:
  db:
    image: pgvector/pgvector:0.8.1-pg17
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: bbj_rag
      POSTGRES_USER: bbj_rag
      POSTGRES_PASSWORD: bbj_rag
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./sql/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bbj_rag"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
    environment:
      BBJ_RAG_DATABASE_URL: "postgresql://bbj_rag:bbj_rag@db:5432/bbj_rag"
      OLLAMA_HOST: "http://host.docker.internal:11434"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      # Source data (read-only bind mounts from host)
      - /Users/beff/bbjdocs:/data/flare:ro
      - ./GuideToGuiProgrammingInBBj.pdf:/data/pdf/guide.pdf:ro
      # MDX and BBj source dirs configured via env vars
    command: >
      uvicorn bbj_rag.api:app --host 0.0.0.0 --port 8000

volumes:
  pgdata:
```

### Docker Networking Details

| From | To | Address | Mechanism |
|------|----|---------|-----------|
| app container | db container | `db:5432` | Docker Compose DNS (same network) |
| app container | Ollama on host | `host.docker.internal:11434` | `extra_hosts` mapping + Docker gateway |
| MCP server (host) | db container | `localhost:5432` | Port mapping (`5432:5432`) |
| MCP server (host) | Ollama on host | `localhost:11434` | Direct localhost |
| REST clients | app container | `localhost:8000` | Port mapping (`8000:8000`) |

**Critical: `extra_hosts` directive.** On Docker Desktop for macOS, `host.docker.internal` resolves automatically. On Linux Docker, you need `extra_hosts: ["host.docker.internal:host-gateway"]`. Include it always for portability.

**Critical: Ollama Python client env var.** The `ollama` Python package reads `OLLAMA_HOST` to determine the server address. Setting `OLLAMA_HOST=http://host.docker.internal:11434` in the container environment makes `ollama.embed()` calls work without code changes to `embedder.py`.

### Volume Mounts for Source Data

Source data lives on the macOS host filesystem. The app container reads it via bind mounts.

| Source | Host Path | Container Path | Config Var |
|--------|-----------|----------------|------------|
| Flare XHTML | `/Users/beff/bbjdocs` | `/data/flare` | `BBJ_RAG_FLARE_SOURCE_PATH=/data/flare` |
| PDF Guide | `./GuideToGuiProgrammingInBBj.pdf` | `/data/pdf/guide.pdf` | `BBJ_RAG_PDF_SOURCE_PATH=/data/pdf/guide.pdf` |
| MDX tutorials | `/Users/beff/_workspace/<sites>` | `/data/mdx/<site>` | `BBJ_RAG_MDX_SOURCE_PATH=/data/mdx` |
| BBj source code | SVN checkout paths | `/data/bbj/<dir>` | `BBJ_RAG_BBJ_SOURCE_DIRS=["/data/bbj/src",...]` |
| WordPress | N/A (HTTP) | N/A | Already URL-based, no mount needed |
| Web crawl | N/A (HTTP) | N/A | Already URL-based, no mount needed |

All bind mounts are `:ro` (read-only). Parsers only read; they never write to source directories.

### Database Initialization

PostgreSQL's `docker-entrypoint-initdb.d/` mechanism runs SQL files on first container startup. Mount `sql/schema.sql` as `01-schema.sql` to auto-create the pgvector extension, chunks table, indexes, and the `rrf_score()` function. This replaces the need to run `schema.py` manually.

The schema is idempotent (`CREATE IF NOT EXISTS` throughout), so it is safe to re-run.

---

## 6. Dockerfile Design

### Multi-stage Build

```dockerfile
# rag-ingestion/Dockerfile
FROM python:3.12-slim AS base

# Install system dependencies for psycopg binary and lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder

RUN pip install --no-cache-dir uv

WORKDIR /build
COPY pyproject.toml .
COPY src/ src/
COPY sql/ sql/

# Install the package and its dependencies
RUN uv pip install --system --no-cache ".[standard]"

FROM base AS runtime

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy sql directory for schema.py (if still needed for CLI apply-schema)
COPY sql/ /app/sql/
WORKDIR /app

# Non-root user
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Default: run the REST API
CMD ["uvicorn", "bbj_rag.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key decisions:**
- `python:3.12-slim` as base (not alpine) because psycopg binary wheels and lxml need glibc.
- Multi-stage to keep the final image small (no build tools in runtime).
- `uv pip install --system` to install into the system Python (no virtualenv needed in container).
- SQL files copied into image for any programmatic schema application.
- Non-root user for security.

### Running Ingestion vs API

The same image supports both use cases via command override:

```bash
# Run REST API (default)
docker compose up app

# Run ingestion for a specific source
docker compose run --rm app bbj-rag ingest --source flare

# Run quality report
docker compose run --rm app bbj-rag report
```

---

## 7. Component Dependency Graph

```
                    config.py (Settings)
                   /     |      \       \
                  /      |       \       \
           db.py    embedder.py  parsers/  api.py (NEW)
             |          |            |         |
             |          |            |         |
          search.py     |       pipeline.py   |
             |          |         /    \       |
             |          |        /      \      |
             +----------+-------+       intelligence/
             |
        mcp_server.py (NEW)
```

**Both `api.py` and `mcp_server.py` are thin wrappers** that:
1. Load `Settings` from config
2. Create an embedder via `create_embedder()`
3. Get a database connection via `get_connection()`
4. Call `hybrid_search()` (or `dense_search()` / `bm25_search()`)
5. Format results for their respective consumers (JSON for API, text for MCP)

This is the key architectural insight: the existing `search.py` module is already the right abstraction boundary. The new modules are **presentation layers**, not new business logic.

---

## 8. Build Order (Recommended)

Build in this order to get working feedback loops at each step:

### Phase 1: Docker Compose + pgvector (foundation)

**Build:** `compose.yaml` with `db` service only, `Dockerfile` for app image.

**Validates:**
- pgvector container starts and initializes schema
- App container builds and installs bbj-rag package
- App container can connect to db via Docker network
- App container can reach Ollama on host via `host.docker.internal`

**Test:** `docker compose run --rm app bbj-rag ingest --source flare` (full pipeline through Docker)

**Why first:** Everything else depends on the containerized database and networking being correct.

### Phase 2: REST API (`api.py`)

**Build:** FastAPI app with `/health` and `/search` endpoints.

**Validates:**
- Search works through HTTP
- Connection pooling works under concurrent requests
- Embedder can reach Ollama from container

**Test:** `curl http://localhost:8000/search -d '{"query": "BBjGrid"}'`

**Why second:** The REST API is the simplest new code (one file, two endpoints) and provides immediate interactive testing via the Swagger UI at `/docs`.

### Phase 3: MCP Server (`mcp_server.py`)

**Build:** FastMCP server with `search_bbj_knowledge` tool.

**Validates:**
- MCP stdio transport works with Claude Desktop
- Tool receives queries and returns formatted results
- Database connection from host process works

**Test:** Configure in Claude Desktop, ask "What is BBjGrid?"

**Why third:** The MCP server depends on the same search infrastructure as the API but adds the MCP SDK dependency and Claude Desktop integration testing, which is harder to automate.

### Phase 4: `schema.py` Fix + Config Additions

**Build:** Fix the `_SQL_DIR` path in `schema.py`, add `ollama_host` to config.

**Why last (or folded into Phase 1):** These are small targeted fixes that can be addressed when they surface during container testing. They may also be folded into Phase 1 if they block the initial build.

---

## 9. Anti-Patterns to Avoid

### Do Not Containerize Ollama

Running Ollama in Docker on macOS means no GPU acceleration (Metal is not available in Linux containers on macOS). Embedding throughput drops dramatically. Keep Ollama on the host.

### Do Not Create Separate Containers for API and MCP

They share the same 500MB+ of Python dependencies and the same 6 lines of search logic. Separate containers double image pull time, double memory, and create a coordination problem for zero benefit.

### Do Not Use SQLAlchemy

The codebase uses psycopg3 directly with raw SQL. The search queries use pgvector-specific operators (`<=>`, `vector` casts) and PostgreSQL-specific features (`ts_rank_cd`, `GENERATED ALWAYS`). An ORM adds complexity without value here.

### Do Not Make the MCP Server Run Inside Docker

Claude Desktop spawns MCP servers as local child processes via stdio. It writes to the process's stdin and reads from stdout. It cannot do this with a process inside a Docker container. The MCP server must run on the host, connecting to the Dockerized pgvector via the exposed port.

### Do Not Use Async psycopg in the API

The existing codebase uses synchronous `psycopg.Connection`. Switching to `psycopg.AsyncConnection` would require rewriting `search.py`, `db.py`, and all SQL execution paths. FastAPI handles sync functions by running them in a threadpool, which is perfectly adequate for a search endpoint serving a few requests per second.

---

## 10. Configuration Strategy

The existing Pydantic Settings system (`config.py`) already supports:
- TOML file defaults (`config.toml`)
- Environment variable overrides (`BBJ_RAG_` prefix)
- Constructor injection (highest priority)

This maps perfectly to Docker:

| Setting | TOML Default | Docker Override | MCP Server Override |
|---------|-------------|-----------------|---------------------|
| `database_url` | `postgresql://localhost:5432/bbj_rag` | `BBJ_RAG_DATABASE_URL=postgresql://bbj_rag:bbj_rag@db:5432/bbj_rag` | `BBJ_RAG_DATABASE_URL=postgresql://bbj_rag:bbj_rag@localhost:5432/bbj_rag` |
| `flare_source_path` | `""` | `BBJ_RAG_FLARE_SOURCE_PATH=/data/flare` | Not needed (ingestion only) |
| `embedding_model` | `qwen3-embedding:0.6b` | Inherited | Inherited |
| Ollama host | N/A (client reads `OLLAMA_HOST`) | `OLLAMA_HOST=http://host.docker.internal:11434` | `OLLAMA_HOST=http://localhost:11434` (default) |

The `config.toml` file provides development defaults. Docker Compose environment variables override them for containerized execution. The MCP server running on the host uses the defaults or its own env vars.

No changes to the priority system (`init > env > TOML > defaults`) are needed.

---

## 11. Confidence Assessment

| Area | Confidence | Rationale |
|------|-----------|-----------|
| Service topology | HIGH | Standard Docker Compose pattern for app + database. Verified pgvector/pgvector image tags on Docker Hub. |
| Docker networking (Ollama) | HIGH | `host.docker.internal` + `OLLAMA_HOST` env var is a well-documented pattern. Ollama Python client confirmed to read this env var. |
| REST API (FastAPI) | HIGH | FastAPI + psycopg3 + Pydantic is a well-established stack. The project already depends on Pydantic. |
| MCP server (FastMCP) | HIGH | Official MCP Python SDK docs confirm `@mcp.tool()` decorator pattern. stdio transport is the canonical local transport. SDK at v1.26.0, stable. |
| MCP stdio vs Docker | HIGH | MCP spec explicitly documents stdio as local child-process transport. Cannot work across container boundaries. |
| Volume mount strategy | MEDIUM | Bind mounts work but paths are macOS-specific. Would need adjustment for CI/CD or other developers. |
| schema.py path fix | MEDIUM | The `Path(__file__)` approach breaks in installed packages but the exact fix depends on whether `sql/` is included as package data or kept external. |

---

## Sources

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) -- Official SDK, FastMCP included, v1.26.0 (Jan 2026)
- [MCP Build Server Guide](https://modelcontextprotocol.io/docs/develop/build-server) -- `@mcp.tool()` pattern, stdio transport
- [MCP Transport Specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports) -- stdio vs Streamable HTTP
- [pgvector/pgvector Docker Hub](https://hub.docker.com/r/pgvector/pgvector) -- Image tags, `0.8.1-pg17`
- [Ollama Python Client](https://github.com/ollama/ollama-python) -- `OLLAMA_HOST` env var, `Client(host=...)` constructor
- [Ollama FAQ](https://docs.ollama.com/faq) -- Binding to `0.0.0.0`, Docker connectivity
- [FastAPI Documentation](https://fastapi.tiangolo.com/) -- ASGI, Pydantic integration, sync endpoint threadpool
- [Docker host.docker.internal](https://openillumi.com/en/en-docker-ollama-localhost-connect-host-docker-internal/) -- Container-to-host connectivity pattern
