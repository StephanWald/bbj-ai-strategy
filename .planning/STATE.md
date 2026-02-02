# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-01)

**Core value:** A running Docker-based system that ingests all 6 BBj documentation sources and serves retrieval via REST API and MCP server.
**Current focus:** Phase 23.1 -- WordPress Parser Fix (INSERTED, next)

## Current Position

Milestone: v1.4 RAG Deployment -- IN PROGRESS
Phase: 23.1 (WordPress Parser Fix -- INSERTED)
Plan: 0 of ? in current phase
Status: Phase 23 complete, Phase 23.1 not planned yet
Last activity: 2026-02-02 -- Phase 23.1 inserted after Phase 23

Progress: [████████░░] 80%

## Performance Metrics

**Cumulative:**
- v1.0: 5 phases, 15 plans (docs site shipped)
- v1.1: 2 phases, 5 plans (code corrections + branding)
- v1.2: 7 phases, 15 plans (RAG ingestion pipeline)
- v1.3: 5 phases, 10 plans (MCP architecture integration)
- v1.4: 6 phases, 9 plans (RAG deployment -- in progress, +23.1 inserted)
- **Total: 25 phases, 54 plans (52 complete)**

## Accumulated Context

### Decisions

See .planning/PROJECT.md Key Decisions table for full log.

Recent decisions affecting current work:
- Docker Compose for RAG deployment (self-contained local deployment)
- Host Ollama (not containerized) for macOS Metal GPU acceleration
- REST API + thin MCP server (clean separation)
- Python for MCP server (same language as existing pipeline)
- uv 0.9.28 pinned in Dockerfile (matches local install)
- DB password fail-fast via :? syntax in compose
- External ports above 10000 (10800 app, 10432 db)
- extra="ignore" in Settings model_config to silently skip old TOML database_url key
- Conditional Path("config.toml").exists() check for TOML source inclusion
- Soft warning for default password in production (not hard fail)
- sources.toml ships with blank data_dir; resolved via DATA_DIR env var at runtime
- Each MDX tutorial directory is a separate [[sources]] entry for independent enable/disable
- MdxParser source_prefix defaults to "dwc-course" for backward compat
- Sequential execution default for bbj-ingest-all (parallel deferred)
- Fresh DB connection per source with try/finally for isolation
- Resume state as .ingestion-state.json file in working directory
- Annotated[T, Depends()] pattern for FastAPI DI (ruff B008 compliance)
- tuple_row cursor factory for mypy-safe row indexing in /stats endpoint
- Sync psycopg fallback in health check for early startup race condition
- MCP SDK v1.x (mcp>=1.25,<2) with FastMCP for single-tool server
- Individual volume mounts per source repo (symlinks don't resolve across Docker boundaries)
- rrf_score function uses bigint to match rank() return type

### Pending Todos

- Batch embedding requests (send 32+ chunks per Ollama `/api/embed` call instead of 1-at-a-time)
- Concurrent ingestion workers (parallel embedding calls to keep GPU saturated)
- Persistent HTTP connection reuse for Ollama embedding calls during ingestion
- Map source_url to clickable HTTP links (e.g., flare:// → https://documentation.basis.cloud/...) — high value for chat users who want to read the full doc

### Roadmap Evolution

- Phase 23.1 inserted after Phase 23: WordPress Parser Fix (URGENT)

### Blockers/Concerns

- Ollama must be running on host with `OLLAMA_HOST=0.0.0.0:11434` for Docker connectivity
- shm_size required for pgvector HNSW index builds (256mb minimum)

## Session Continuity

Last session: 2026-02-02
Stopped at: Phase 23.1 inserted (WordPress Parser Fix)
Resume file: None
Next action: `/gsd:plan-phase 23.1` or `/gsd:discuss-phase 23.1`
