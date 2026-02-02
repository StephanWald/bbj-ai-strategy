# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-01)

**Core value:** A running Docker-based system that ingests all 6 BBj documentation sources and serves retrieval via REST API and MCP server.
**Current focus:** v1.4 milestone COMPLETE

## Current Position

Milestone: v1.4 RAG Deployment -- COMPLETE
Phase: 24 (End-to-End Validation) -- COMPLETE
Plan: 1 of 1 in current phase (complete)
Status: v1.4 milestone fully validated. VALIDATION.md proves end-to-end pipeline works.
Last activity: 2026-02-02 -- Completed 24-01-PLAN.md (end-to-end validation)

Progress: [██████████] 100%

## Performance Metrics

**Cumulative:**
- v1.0: 5 phases, 15 plans (docs site shipped)
- v1.1: 2 phases, 5 plans (code corrections + branding)
- v1.2: 7 phases, 15 plans (RAG ingestion pipeline)
- v1.3: 5 phases, 10 plans (MCP architecture integration)
- v1.4: 7 phases, 11 plans (RAG deployment + validation, including 23.1 gap closure)
- **Total: 26 phases, 59 plans (59 complete)**

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
- Document Docker as primary deployment path with local as secondary in README
- Keep _fetch_page() for backward compat; _fetch_response() for header-based routing
- Content-Type substring check for PDF detection handles MIME params
- Lightweight keyword heuristics for automated validation pass/fail assessment
- Single MCP ClientSession for all validation queries (avoid per-query process spawn)
- Cross-source validation via query results, not direct DB prefix queries

### Pending Todos

- ~~Batch embedding requests~~ VERIFIED: already implemented (batch_size=64, embed_batch() -> ollama.embed(input=texts))
- Concurrent ingestion workers (parallel embedding calls to keep GPU saturated)
- Persistent HTTP connection reuse for Ollama embedding calls during ingestion
- Map source_url to clickable HTTP links (e.g., flare:// -> https://documentation.basis.cloud/...) -- high value for chat users who want to read the full doc
- Source-balanced ranking (boosting minority sources like PDF, BBj Source for more diverse top-k)

### Roadmap Evolution

- Phase 23.1 inserted after Phase 23: WordPress Parser Fix (URGENT)

### Blockers/Concerns

- Ollama must be running on host with `OLLAMA_HOST=0.0.0.0:11434` for Docker connectivity
- shm_size required for pgvector HNSW index builds (256mb minimum)
- PDF and BBj Source source-targeted queries rank below Flare's 88% corpus dominance (known issue, not blocker)

## Session Continuity

Last session: 2026-02-02
Stopped at: Completed 24-01-PLAN.md (end-to-end validation) -- v1.4 MILESTONE COMPLETE
Resume file: None
Next action: None -- v1.4 milestone is fully complete. All 26 phases and 59 plans delivered.
