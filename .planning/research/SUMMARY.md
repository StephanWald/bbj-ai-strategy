# Project Research Summary

**Project:** BBj AI Strategy — RAG Deployment Service (v1.4)
**Domain:** RAG pipeline Docker deployment with REST API and MCP server
**Researched:** 2026-02-01
**Confidence:** HIGH

## Executive Summary

v1.4 transforms the battle-tested RAG ingestion pipeline (310 tests, 6 parsers, hybrid search) into a deployable service. The architecture is straightforward: Docker Compose orchestrates a pgvector container and a Python app container, with Ollama remaining on the host macOS machine for Metal GPU acceleration. A thin FastAPI layer exposes the existing `search.py` hybrid search over HTTP, while an MCP server provides the `search_bbj_knowledge` tool for Claude Desktop integration via stdio transport.

The recommended approach leverages the project's existing strengths. The codebase already has clean abstraction boundaries — `search.py` accepts a connection and returns dataclasses, `embedder.py` is protocol-based, `config.py` uses pydantic-settings with env var overrides. The deployment stack adds only 4 new dependencies (FastAPI, uvicorn, psycopg-pool, mcp) and two presentation-layer modules (`api.py` and `mcp_server.py`). Both wrap the same search functions, differing only in response format (JSON for REST, formatted text for MCP).

The key risks are configuration fragility (TOML file expectations vs 12-factor env vars), Ollama network connectivity from Docker (`host.docker.internal` requires explicit setup), and MCP transport selection (stdio for local use, not Streamable HTTP). All are well-documented pitfalls with proven mitigations. The implementation path is incremental: Docker foundation first, REST API second (validates search integration), MCP server third (adds only protocol wiring).

## Key Findings

### Recommended Stack

The stack builds on the project's existing Python 3.12 ecosystem (psycopg3, pgvector, Ollama, Pydantic) with minimal additions for deployment. Docker is the delivery mechanism, not a fundamental architecture change.

**Core technologies:**

- **pgvector/pgvector:0.8.0-pg17** — PostgreSQL 17 with pgvector extension. Version-pinned Docker image. Fresh deployment, no migration concerns. PG17 improvements (incremental JSON, better VACUUM, improved planner) are free upgrades.

- **FastAPI + uvicorn[standard]** — REST API framework with async support and automatic Pydantic integration. The project already depends on Pydantic v2 — FastAPI uses it natively for request/response validation. One endpoint (`/search`) wraps existing `hybrid_search()` function.

- **MCP Python SDK (v1.x, `mcp` package)** — Official SDK with `FastMCP` class and `@mcp.tool()` decorator. Pin `>=1.25,<2` for stability (v2 coming Q1 2026). Supports both stdio (for Claude Desktop) and Streamable HTTP (future remote access).

- **psycopg-pool** — Connection pooling for psycopg3. The existing code uses bare `psycopg.connect()` per operation, which works for the CLI but is inadequate for an API server. `psycopg_pool.ConnectionPool` is the official pool with a `configure` callback for pgvector type registration.

- **python:3.12-slim-bookworm** — Base Docker image matching `requires-python = ">=3.12"`. Slim variant (~150MB vs ~1GB full) with glibc for binary wheels. NOT Alpine (musl breaks psycopg[binary], lxml, and PyMuPDF wheels).

- **Docker Compose** — Service orchestration with auto-initialized schema (`/docker-entrypoint-initdb.d/` mounts `schema.sql`), health checks, and environment-based configuration. Two services: `db` (pgvector) and `app` (Python). Ollama on host accessed via `host.docker.internal:11434`.

**What NOT to add:** SQLAlchemy (the raw SQL is clean and pgvector-specific), Alembic (single-table schema, `IF NOT EXISTS` idempotency), Redis caching (premature — search is already <100ms), async ingestion API (CLI sufficient), nginx (uvicorn direct serving is fine for local/internal use).

### Expected Features

The feature set is tightly scoped: wrap existing search capabilities in two interfaces (REST and MCP), deploy via Docker, orchestrate ingestion for all 6 sources.

**Must have (table stakes):**

- **`POST /search` endpoint** — HTTP layer over `hybrid_search()`. Takes query text (embedded on-the-fly via Ollama), optional `generation` filter (all/character/vpro5/bbj_gui/dwc), optional `limit` (default 5). Returns JSON with structured `SearchResult` fields: content, source_url, title, doc_type, generations, score.

- **`search_bbj_knowledge` MCP tool** — Matches Ch2's exact JSON schema (query string required, generation enum optional, limit integer default 5). Returns formatted text optimized for LLM consumption (not raw JSON). Implemented with `@mcp.tool()` decorator — type annotations auto-generate MCP tool schema.

- **Docker Compose with `docker compose up` simplicity** — Single command starts pgvector + app containers. Schema auto-applied on first startup. Persistent volume for database. Source data bind-mounted read-only. Environment variable configuration (no TOML file in container).

- **Ingestion orchestration** — Run all 6 parsers (Flare, PDF, MDX, BBj source, WordPress, web crawl) against real data paths. Either a shell script or new CLI command `bbj-rag ingest-all` that sequences the 6 `ingest --source X` calls. Idempotent (content-hash dedup) with progress logging.

- **Health endpoint** — `GET /health` checks database connectivity, Ollama reachability, and chunks table row count. Returns 200 or 503 with component status JSON.

**Should have (differentiators):**

- **Generation filtering across all search modes** — BBj's multi-generation model is unique. The existing `search.py` already supports `generation_filter` on dense, BM25, and hybrid search with GIN-indexed `generations` array. This is a table-stakes requirement for BBj but a differentiator in the RAG ecosystem.

- **`context_header` in results** — Currently stored in DB but omitted from `SearchResult`. Provides section path (e.g., "BBj Objects > BBjWindow > Methods > addButton"). High value for LLM prompt assembly — adds context beyond raw chunk content.

- **Search mode selection** — Expose `mode` parameter (dense/bm25/hybrid) on REST API. Different queries benefit from different modes: API name lookups favor BM25, conceptual questions favor dense. Hybrid (default) uses RRF fusion.

- **Stats endpoint** — `GET /stats` returns chunk counts by source, generation, doc_type. Reuses existing `intelligence/report.py` query functions. Lets operators verify ingestion completeness.

**Defer (v2+):**

- **`generate_bbj_code` MCP tool** — Requires fine-tuned model (not yet ready). Out of scope per PROJECT.md.

- **`validate_bbj_syntax` MCP tool** — Requires BBj compiler integration in Docker (licensing, runtime distribution). Separate milestone.

- **Authentication, rate limiting, HTTPS** — v1.4 is local Docker deployment, single user. No external access requirements.

- **Agentic RAG (query rewriting, multi-step retrieval, answer generation)** — Explicitly out of scope. Retrieval only. The consuming LLM (Claude, Cursor) handles prompt assembly and generation.

### Architecture Approach

The architecture is presentation-layer-only. The existing codebase provides all business logic — Docker wraps it, FastAPI exposes it, MCP formalizes it. Both `api.py` and `mcp_server.py` are thin wrappers (~30-50 lines each) that initialize embedder, get DB connection, call `hybrid_search()`, and format results.

**Major components:**

1. **Docker Compose network** — `db` service (pgvector/pgvector:0.8.0-pg17) and `app` service (custom Python 3.12 image). App container connects to `db:5432` via Docker DNS, to Ollama via `host.docker.internal:11434` (requires `extra_hosts: host-gateway` for Linux portability). Persistent named volume for PostgreSQL data. Bind mounts for source data (Flare XHTML, PDFs, MDX, BBj code).

2. **REST API (api.py)** — FastAPI with `/search`, `/health`, and `/stats` endpoints. Connection pool via `psycopg_pool.ConnectionPool` (the existing `get_connection()` creates single connections, inadequate for API). Singleton embedder initialized at startup. Search logic delegated to existing `search.py` functions. Pydantic response models map `SearchResult` fields to JSON.

3. **MCP server (mcp_server.py)** — FastMCP with `@mcp.tool()` decorated function. stdio transport (spawned by Claude Desktop as subprocess). NOT in Docker (stdio cannot cross container boundaries). Runs on host, connects to pgvector via exposed port (localhost:5432) and Ollama at localhost:11434. Returns formatted text blocks (title, source, doc_type, content) for LLM consumption.

4. **Configuration layer** — Existing `Settings(BaseSettings)` with `BBJ_RAG_` env var prefix works perfectly with Docker Compose `environment:` blocks. No new config system needed. Critical change: make TOML source conditional (file may not exist in container). Docker overrides: `BBJ_RAG_DATABASE_URL=postgresql://bbj:bbj@db:5432/bbj_rag`, `OLLAMA_HOST=http://host.docker.internal:11434`.

5. **Database initialization** — Mount `sql/schema.sql` to `/docker-entrypoint-initdb.d/01-schema.sql` in pgvector container. PostgreSQL auto-executes on first startup. Schema uses `IF NOT EXISTS` throughout (idempotent). Critical: set `shm_size: '256mb'` in docker-compose for HNSW parallel builds (default 64MB too small for `maintenance_work_mem`).

**Dependency graph:**
```
config.py (Settings) --> embedder.py, db.py, parsers/
                     --> api.py (NEW) --> search.py
                     --> mcp_server.py (NEW) --> search.py
```

Both new modules are **presentation layers**. The existing `search.py` is the abstraction boundary. No business logic changes.

### Critical Pitfalls

These are deployment-killers that must be addressed proactively:

1. **TOML config missing in container crashes Settings** — `TomlConfigSettingsSource` raises `FileNotFoundError` when `config.toml` is absent. The Settings class requires TOML file to exist even when all values come from env vars. Fix: modify `settings_customise_sources` to conditionally include TOML source only if file exists. Test Settings construction with no TOML file present. Do NOT copy config.toml into Docker image (bakes dev defaults).

2. **Ollama unreachable from Docker container on macOS** — Inside container, `127.0.0.1:11434` refers to container itself, not host. Fix: (a) Set `OLLAMA_HOST=0.0.0.0:11434` on macOS host (Ollama listens on all interfaces), (b) Set `OLLAMA_ORIGINS="*"` on host (allows cross-origin requests), (c) Pass `OLLAMA_HOST=http://host.docker.internal:11434` env var to container, (d) Include `extra_hosts: ["host.docker.internal:host-gateway"]` in docker-compose.yml (Linux compatibility). Add health check that verifies Ollama connectivity before pipeline starts.

3. **Docker `--shm-size` too small for parallel HNSW index build** — pgvector's parallel HNSW builder uses `/dev/shm` for shared memory. Docker default is 64MB. For 20K-40K chunks at 1024 dimensions, HNSW needs ~100-200MB `maintenance_work_mem`. Fix: Set `shm_size: '256mb'` in docker-compose.yml for the `db` service. Configure PostgreSQL: `maintenance_work_mem = '128MB'`, `max_parallel_maintenance_workers = 4`.

4. **psycopg[binary] wheels fail on Alpine-based images** — `psycopg-binary` ships manylinux wheels (glibc). Alpine uses musl libc. Wheels fail to install or produce runtime errors. Fix: Use `python:3.12-slim` (Debian-based, glibc) as base image, NOT Alpine. Slim image is ~45MB larger but supports manylinux wheels natively. Also resolves issues with lxml and PyMuPDF (both require glibc).

5. **Synchronous database connections under async API cause deadlocks** — Current `db.py` uses sync `psycopg.connect()`. If FastAPI endpoints are `async def`, sync DB calls block the event loop. Under concurrent load: deadlock, connection pool exhaustion, catastrophic latency. Fix: Use `psycopg_pool.AsyncConnectionPool` for API endpoints OR use `def` (non-async) endpoints which FastAPI runs in threadpool automatically. Test under concurrent load (10 requests) early.

## Implications for Roadmap

Based on research, suggested phase structure follows the critical path: foundation (Docker + DB) → retrieval (API) → protocol (MCP).

### Phase 1: Docker Compose + pgvector Foundation

**Rationale:** Everything depends on containerized database and networking. Validate Docker build, schema initialization, Ollama connectivity, and ingestion pipeline before adding API layers.

**Delivers:**
- `docker-compose.yml` with `db` (pgvector) and `app` services
- Dockerfile for Python 3.12 app image (multi-stage build with uv)
- Schema auto-applied on DB container startup
- Ollama reachable from app container via `host.docker.internal`
- Source data bind mounts for all 6 parsers
- Full ingestion run via `docker compose run app bbj-rag ingest --source flare` (and other sources)

**Addresses:**
- TOML config fix (make source conditional on file existence)
- Database URL configuration (`db:5432` in container vs `localhost:5432` on host)
- `shm_size` configuration for HNSW builds
- Base image selection (`python:3.12-slim` not Alpine)

**Avoids:**
- Pitfall #1 (TOML missing)
- Pitfall #2 (Ollama unreachable)
- Pitfall #3 (shm-size)
- Pitfall #4 (Alpine wheels)
- Pitfall #10 (localhost in database URL)

**Validates:** End-to-end ingestion through Docker produces searchable chunks in pgvector.

### Phase 2: REST Retrieval API

**Rationale:** API is simpler than MCP (no SDK, no transport complexity) and provides immediate interactive testing via Swagger UI. Validates the connection pooling and embedder initialization patterns before MCP reuses them.

**Delivers:**
- `src/bbj_rag/api.py` with FastAPI app
- `/search` endpoint (POST with query, generation, limit parameters)
- `/health` endpoint (DB + Ollama connectivity check)
- `/stats` endpoint (chunk counts by source/generation/doc_type)
- Connection pool via `psycopg_pool.ConnectionPool`
- Singleton embedder with Ollama host from config
- Pydantic response models mapping `SearchResult` to JSON
- OpenAPI docs at `/docs` for interactive testing

**Uses:**
- FastAPI (already selected)
- uvicorn[standard] (ASGI server)
- psycopg-pool (connection pooling)
- Existing search.py functions (no changes)

**Implements:**
- Presentation layer over existing search module
- Environment-based configuration (no code-level config)

**Avoids:**
- Pitfall #5 (sync DB under async API) — use `def` endpoints with threadpool OR async pool
- Pitfall #17 (no connection pooling) — psycopg_pool with min=2, max=10

**Validates:** `curl http://localhost:8000/search -d '{"query": "BBjGrid", "limit": 5}'` returns relevant chunks.

### Phase 3: MCP Server

**Rationale:** MCP server reuses search infrastructure from Phase 2 (same embedder, same DB connection logic, same search functions). Adds only MCP SDK dependency and stdio transport wiring. Simplest to implement after API validates the integration patterns.

**Delivers:**
- `src/bbj_rag/mcp_server.py` with FastMCP
- `@mcp.tool()` decorated `search_bbj_knowledge` function
- stdio transport (for Claude Desktop spawning)
- Formatted text response (not JSON) optimized for LLM consumption
- Claude Desktop configuration JSON (`claude_desktop_config.json`)
- Generation value normalization (Ch2 uses `"bbj-gui"` hyphenated, DB uses `"bbj_gui"` underscored)

**Uses:**
- MCP Python SDK (`mcp>=1.25,<2`)
- Same embedder, db, search modules as API
- stdio transport (runs on host, not in Docker)

**Implements:**
- MCP tool matching Ch2 JSON schema exactly
- Protocol-specific formatting (text blocks with metadata headers)

**Avoids:**
- Pitfall #8 (transport mismatch) — stdio for local Claude Desktop, not Streamable HTTP
- Pitfall #9 (SDK version churn) — pin `>=1.25,<2`
- Pitfall #16 (stdout corruption) — redirect logging to stderr

**Validates:** Ask Claude Desktop "What is BBjGrid?" triggers `search_bbj_knowledge` tool, returns relevant documentation.

### Phase Ordering Rationale

- **Docker first** because both API and MCP depend on pgvector and Ollama connectivity. No value in building presentation layers before the foundation works.

- **API before MCP** because it provides faster feedback (Swagger UI for manual testing, no client-side MCP setup needed) and validates the embedder + connection pool patterns that MCP will reuse. MCP adds protocol complexity without new business logic.

- **MCP separate from API** despite code similarity because the deployment models differ (stdio subprocess on host vs HTTP server in Docker). Attempting to combine them into a single endpoint with transport auto-detection adds complexity for marginal benefit.

- **Ingestion folded into Phase 1** (not separate) because Docker validation requires running the full pipeline. Can't declare success on "database works" without proving the parsers, chunker, embedder, and bulk insert all function in the containerized environment.

### Research Flags

**Phases with standard patterns (skip `/gsd:research-phase`):**

- **Phase 1 (Docker):** Well-documented Docker Compose + PostgreSQL + Python patterns. All critical decisions resolved in STACK.md (base image, Ollama connectivity, shm-size, schema initialization). No unknowns.

- **Phase 2 (API):** FastAPI + psycopg3 is a standard stack with extensive documentation. The existing `search.py` is already tested and clean. Presentation-layer only.

- **Phase 3 (MCP):** MCP Python SDK docs are comprehensive. The transport choice (stdio) is resolved. Ch2 schema defines the contract. Only integration work, no research needed.

**No phases need deeper research.** The existing codebase provides battle-tested business logic, and the deployment stack uses proven patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified on PyPI (2026-02-01). Docker images verified on Docker Hub. Ollama connectivity pattern documented in official Ollama FAQ. |
| Features | HIGH | Existing codebase analyzed directly. Ch2 MCP schema is source of truth. Feature set is tightly scoped (wrap, deploy, orchestrate — no new algorithms). |
| Architecture | HIGH | Service topology is standard Docker Compose. Integration points with existing modules are clean (config, embedder, db, search all have correct abstraction boundaries). |
| Pitfalls | HIGH | All critical pitfalls sourced from official docs (pgvector README, Docker docs, MCP SDK docs) or multiple independent reports (psycopg binary on Alpine, Ollama Docker connectivity). |

**Overall confidence:** HIGH

The research covers deployment of existing code, not new feature development. The codebase is mature (310 tests, 4,906 lines) with clean module boundaries. The deployment stack (Docker, FastAPI, MCP SDK) uses well-established patterns. Critical pitfalls have proven mitigations.

### Gaps to Address

- **Volume mount performance on macOS** — Bind mounts incur ~3x overhead for 7,087 Flare files. Accept the performance hit for v1.4 (15 minutes for full ingestion is tolerable). If ingestion time becomes a problem, migrate source data to Docker volumes or use OrbStack. Not a blocker.

- **Multi-MDX source support** — Current config has `mdx_source_path: str` (singular). Three MDX tutorial sites (DWC, beginner, DB modernization) require either (a) config change to `mdx_source_dirs: list[str]` or (b) run `ingest --source mdx` three times with different env var overrides. Low complexity, handle in Phase 1 during config testing.

- **MCP SDK v2 timeline** — v2 anticipated Q1 2026 with potential breaking changes. Pin to `mcp>=1.25,<2` for stability. Monitor SDK changelog. Plan v2 migration as separate task (not mid-feature). Not a v1.4 concern.

- **PyMuPDF ARM64 wheel availability** — Intermittent across versions. Mitigate by targeting `linux/amd64` explicitly in docker-compose (`platform: linux/amd64`). Adds small runtime overhead on Apple Silicon via Rosetta but guarantees wheel availability. Verify at build time.

## Sources

### Primary (HIGH confidence)

- **Existing codebase** — All modules in `rag-ingestion/src/bbj_rag/` analyzed directly (search.py, db.py, embedder.py, config.py, pipeline.py, intelligence/, parsers/). 310 tests, 4,906 lines of tested code.

- **Ch2 Strategic Architecture** — `/Users/beff/_workspace/bbj-ai-strategy/docs/02-strategic-architecture/index.md` lines 166-180. Defines `search_bbj_knowledge` MCP tool JSON schema (source of truth).

- **PROJECT.md** — `/Users/beff/_workspace/bbj-ai-strategy/.planning/PROJECT.md`. v1.4 target features and explicit out-of-scope items.

- **pgvector GitHub README** — [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector). HNSW index creation, parallel builds, shm-size requirements, maintenance_work_mem guidance.

- **Docker Hub** — pgvector/pgvector:0.8.0-pg17 tag verified, python:3.12-slim-bookworm verified.

- **PyPI** — FastAPI 0.128.0, uvicorn 0.40.0, psycopg-pool 3.3.0, mcp 1.26.0 verified (2026-02-01).

- **MCP Python SDK** — [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk). FastMCP API, stdio transport, `@mcp.tool()` decorator pattern.

- **Ollama FAQ** — [docs.ollama.com/faq](https://docs.ollama.com/faq). Docker connectivity (`OLLAMA_HOST=0.0.0.0`), `host.docker.internal` pattern.

- **uv Docker Guide** — [docs.astral.sh/uv/guides/integration/docker/](https://docs.astral.sh/uv/guides/integration/docker/). Multi-stage build, `--frozen` flag, cache mount patterns.

### Secondary (MEDIUM confidence)

- **FastAPI + psycopg3 connection pooling** — [spwoodcock.dev FastAPI psycopg3 article](https://spwoodcock.dev/blog/2024-10-fastapi-pydantic-psycopg/). Lifespan pattern for pool lifecycle.

- **MCP transport comparison** — [mcpcat.io transport guide](https://mcpcat.io/guides/comparing-stdio-sse-streamablehttp/). stdio vs Streamable HTTP use cases.

- **Docker macOS performance (2025)** — Paolo Mainardi benchmarks. VirtioFS ~3x overhead for many small files. OrbStack improvements noted.

- **Ollama embedding timeouts** — Multiple GitHub issues: LightRAG #2300, Roo-Code #5733, RAGFlow #4934. Batch size reduction (8-16) and retry logic recommended.

- **pgvector HNSW shm-size issues** — GitHub issues #800 (Neon), #409 (pgvector). shm_size must be >= maintenance_work_mem for parallel builds.

### Tertiary (LOW confidence, needs validation)

- **MCP SDK v2 timeline Q1 2026** — Mentioned in SDK README and blog post (December 2025). Actual release date unconfirmed. Mitigation: pin to v1.x regardless.

- **Pydantic-settings nested override regression** — GitHub issue #714. Affects v2.12+ when nested TOML sections override via env vars. Current project uses flat settings (not affected). Monitor for future changes.

---
*Research completed: 2026-02-01*
*Ready for roadmap: yes*
