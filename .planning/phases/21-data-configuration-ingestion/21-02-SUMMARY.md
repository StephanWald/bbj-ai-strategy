---
phase: 21-data-configuration-ingestion
plan: 02
subsystem: ingestion
tags: [click, cli, pgvector, pipeline, orchestration, ingestion]

# Dependency graph
requires:
  - phase: 21-data-configuration-ingestion/01
    provides: "source_config.py (load_sources_config, resolve_data_dir, validate_sources, get_source_url_prefix)"
  - phase: 15-bbj-source-ingestion
    provides: "All 7 parsers (FlareParser, PdfParser, MdxParser, BbjSourceParser, AdvantageParser, KnowledgeBaseParser, WebCrawlParser)"
  - phase: 19-docker-compose-deployment
    provides: "Settings model with DB credentials, embedder factory"
provides:
  - "bbj-ingest-all CLI: single command to ingest all enabled sources"
  - "ingest_all.py orchestration script with fail-fast validation"
  - "Parser factory mapping 7 parser types to 9 source entries"
  - "Resume/clean/source-filter capabilities"
affects: [22-rest-api-search, 23-mcp-server-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-source connection lifecycle with try/finally"
    - "Resume state via JSON file (.ingestion-state.json)"
    - "Fail-fast validation (paths + DB + embedder) before ingestion"
    - "Continue-on-failure with summary table"

key-files:
  created:
    - "rag-ingestion/src/bbj_rag/ingest_all.py"
  modified:
    - "rag-ingestion/pyproject.toml"

key-decisions:
  - "Sequential execution only; parallel flag warns and falls back (correctness over speed)"
  - "Fresh DB connection per source via try/finally to prevent timeout and leak issues"
  - "Shared embedder across sources (stateless, no per-source connection needed)"
  - "Resume state stored as .ingestion-state.json in working directory"

patterns-established:
  - "Parser factory pattern: lazy imports to avoid loading unused parser dependencies"
  - "Source-level isolation: each source gets own connection, failures don't cascade"

# Metrics
duration: 3min
completed: 2026-02-01
---

# Phase 21 Plan 02: Orchestration Script Summary

**Click CLI (bbj-ingest-all) orchestrating all 9 source entries through run_pipeline() with fail-fast validation, per-source DB connections, resume/clean modes, and summary table output**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-01T22:19:35Z
- **Completed:** 2026-02-01T22:22:47Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created ingest_all.py with full Click CLI for single-command ingestion of all 9 source entries
- Parser factory correctly maps 7 parser types to their constructors with lazy imports
- MdxParser receives source.name as source_prefix for unique source_url prefixes (mdx-dwc://, mdx-beginner://, mdx-db-modernization://)
- Fail-fast validation checks all source paths, database connectivity, and embedder before starting any ingestion
- Registered bbj-ingest-all as standalone console script in pyproject.toml

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ingest_all.py orchestration CLI** - `2eec47e` (feat)
2. **Task 2: Register bbj-ingest-all script entry point** - `fee3021` (feat)

## Files Created/Modified

- `rag-ingestion/src/bbj_rag/ingest_all.py` - Standalone orchestration CLI: load config, validate, run pipeline per source, print summary
- `rag-ingestion/pyproject.toml` - Added bbj-ingest-all script entry point

## Decisions Made

- Sequential execution default with parallel as unimplemented warning fallback -- correctness first, parallel can be added later once sequential is proven reliable
- Fresh DB connection per source with try/finally -- prevents timeout on long runs and connection leaks on exceptions
- Shared embedder instance across all sources since it is stateless
- Resume state as simple JSON file in working directory rather than database-backed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `bbj-ingest-all` CLI ready for end-to-end ingestion once infrastructure (PostgreSQL + Ollama) is running
- All 9 source entries configured in sources.toml from Plan 21-01
- Ready for Phase 22 (REST API search) -- ingested data will be queryable via the chunks table

---
*Phase: 21-data-configuration-ingestion*
*Completed: 2026-02-01*
