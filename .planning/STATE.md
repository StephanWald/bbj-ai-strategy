# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-01)

**Core value:** A running Docker-based system that ingests all 6 BBj documentation sources and serves retrieval via REST API and MCP server.
**Current focus:** Phase 21 -- Data Configuration + Ingestion (complete)

## Current Position

Milestone: v1.4 RAG Deployment -- IN PROGRESS
Phase: 21 of 24 (Data Configuration + Ingestion)
Plan: 2 of 2 in current phase
Status: Phase complete
Last activity: 2026-02-01 -- Completed 21-02-PLAN.md

Progress: [████░░░░░░] 30%

## Performance Metrics

**Cumulative:**
- v1.0: 5 phases, 15 plans (docs site shipped)
- v1.1: 2 phases, 5 plans (code corrections + branding)
- v1.2: 7 phases, 15 plans (RAG ingestion pipeline)
- v1.3: 5 phases, 10 plans (MCP architecture integration)
- v1.4: 5 phases, 8 plans (RAG deployment -- in progress)
- **Total: 24 phases, 53 plans (50 complete)**

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

### Pending Todos

None.

### Blockers/Concerns

- Ollama must be running on host with `OLLAMA_HOST=0.0.0.0:11434` for Docker connectivity
- shm_size required for pgvector HNSW index builds (256mb minimum)
- Flare source (bbjdocs) directory not present on host -- will error during validation until Flare export is available

## Session Continuity

Last session: 2026-02-01
Stopped at: Completed 21-02-PLAN.md (Phase 21 complete)
Resume file: None
Next action: Execute Phase 22 (REST API + Search)
