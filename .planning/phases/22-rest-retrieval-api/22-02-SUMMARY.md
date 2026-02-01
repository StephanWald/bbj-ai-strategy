---
phase: 22-rest-retrieval-api
plan: 02
subsystem: api
tags: [fastapi, stats, health, pool, readiness, generation-filter]
dependency_graph:
  requires: [phase-22-plan-01]
  provides: [GET /stats endpoint, pool-based /health with three-tier readiness, generation normalization verified]
  affects: [phase-23]
tech_stack:
  added: []
  patterns: [tuple_row cursor factory for mypy-safe row indexing, three-tier health readiness semantics, pool-based health checks]
key_files:
  created: []
  modified:
    - rag-ingestion/src/bbj_rag/api/schemas.py
    - rag-ingestion/src/bbj_rag/api/routes.py
    - rag-ingestion/src/bbj_rag/health.py
decisions:
  - id: D22-02-01
    summary: "tuple_row cursor factory for mypy-safe row indexing in /stats"
    context: "Default psycopg cursor returns rows typed as object, causing mypy index errors"
    choice: "Use conn.cursor(row_factory=tuple_row) for properly typed tuple rows"
  - id: D22-02-02
    summary: "Sync psycopg fallback in health check for early startup"
    context: "Pool may not exist during startup race; health endpoint could be hit before lifespan completes"
    choice: "Keep sync psycopg.connect fallback guarded by getattr(app.state, 'pool', None)"
metrics:
  duration: 4m
  completed: 2026-02-01
---

# Phase 22 Plan 02: Stats, Health, and Generation Filter Summary

Pool-based /health with three-tier readiness, GET /stats with unnested generation counts, generation normalization verified in /search.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add /stats endpoint and StatsResponse schema | 726fa73 | schemas.py, routes.py |
| 2 | Extend /health with pool-based checks and readiness semantics | c4fd833 | health.py |

## What Was Built

### GET /stats Endpoint
- `StatsResponse` Pydantic model with `total_chunks`, `by_source` (doc_type counts), `by_generation` (unnested generation counts)
- Three SQL queries: total count, GROUP BY doc_type, unnest(generations) GROUP BY
- Uses `ConnDep` Annotated DI pattern (same as /search) for pool-based connection
- Uses `tuple_row` cursor factory so mypy accepts row indexing
- 503 HTTPException on database errors

### /health Pool-Based Checks
- Database check now uses `request.app.state.pool.connection()` instead of standalone `psycopg.connect()`
- Sync fallback via `getattr(app.state, 'pool', None)` for startup race condition
- Three-tier readiness: healthy (200), degraded (503), unhealthy (503)
- Ollama check unchanged (httpx.AsyncClient)

### Generation Normalization (Verified)
- `/search` endpoint at line 46: `body.generation.replace("-", "_")` -- confirmed correct
- `bbj-gui` normalizes to `bbj_gui`, matching database column values

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] mypy index errors on cursor rows**
- **Found during:** Task 1
- **Issue:** Default psycopg async cursor returns rows typed as `object`, causing `Value of type "object" is not indexable` mypy errors
- **Fix:** Used `conn.cursor(row_factory=tuple_row)` from `psycopg.rows` for properly typed tuple rows
- **Files modified:** rag-ingestion/src/bbj_rag/api/routes.py
- **Commit:** 726fa73

**2. [Rule 3 - Blocking] ruff import ordering**
- **Found during:** Task 1 (pre-commit hook)
- **Issue:** ruff auto-sorted the `psycopg.rows` import into the correct position
- **Fix:** Accepted ruff auto-fix, re-staged, committed cleanly
- **Files modified:** rag-ingestion/src/bbj_rag/api/routes.py
- **Commit:** 726fa73

## Verification Results

| Check | Result |
|-------|--------|
| StatsResponse JSON schema | total_chunks (int), by_source (object), by_generation (object) |
| StatsResponse serialization | `{"total_chunks":100,"by_source":{"flare":50},"by_generation":{"dwc":30}}` |
| /search and /stats routes registered | Both present in router.routes |
| health accepts Request parameter | `request` in function signature |
| mypy routes.py | Success |
| mypy health.py | Success |
| pytest (313 tests) | All pass |

## API Surface After Plan 22-02

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /health | GET | Pool-based database + Ollama check with 3-tier readiness |
| /search | POST | Hybrid RRF search with generation filter + normalization |
| /stats | GET | Corpus statistics: total chunks, by doc_type, by generation |

## Next Phase Readiness

Phase 22 (REST Retrieval API) is now complete. All three endpoints are implemented:
- /search with generation filtering and normalization
- /stats with corpus statistics
- /health with pool-based checks and three-tier readiness

Phase 23 (MCP Server) can proceed -- it will consume these REST endpoints.
