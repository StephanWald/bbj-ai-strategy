---
phase: 22-rest-retrieval-api
plan: 01
subsystem: api
tags: [fastapi, psycopg-pool, async, search, ollama, pgvector]
dependency_graph:
  requires: [phase-20, phase-21]
  provides: [POST /search endpoint, async connection pool, SearchResult with context_header/deprecated]
  affects: [phase-22-plan-02, phase-23]
tech_stack:
  added: [psycopg-pool]
  patterns: [Annotated dependency injection, AsyncConnectionPool lifespan, register_vector_async configure callback]
key_files:
  created:
    - rag-ingestion/src/bbj_rag/api/__init__.py
    - rag-ingestion/src/bbj_rag/api/schemas.py
    - rag-ingestion/src/bbj_rag/api/deps.py
    - rag-ingestion/src/bbj_rag/api/routes.py
  modified:
    - rag-ingestion/src/bbj_rag/search.py
    - rag-ingestion/src/bbj_rag/app.py
    - rag-ingestion/pyproject.toml
    - rag-ingestion/uv.lock
decisions:
  - id: annotated-depends
    description: "Use Annotated[T, Depends()] pattern for FastAPI DI to satisfy ruff B008 lint rule"
    rationale: "Modern FastAPI pattern, avoids function calls in argument defaults"
metrics:
  duration: 4m
  completed: 2026-02-01
---

# Phase 22 Plan 01: Search Endpoint and Pool Summary

Async /search endpoint with connection pooling, Ollama query embedding, and hybrid RRF retrieval over ingested BBj documentation corpus.

## What Was Done

### Task 1: Extend search.py with missing fields and async hybrid search (998386a)

Extended the SearchResult dataclass with `context_header` (str) and `deprecated` (bool) fields, placed between `generations` and `score`. Updated `_rows_to_results` to map the new column positions (row[6] for context_header, row[7] for deprecated, row[8] for score). All three search functions (`dense_search`, `bm25_search`, `hybrid_search`) now SELECT `context_header, deprecated` alongside existing columns. The `hybrid_search` GROUP BY clause was updated to include the new columns. Added `async_hybrid_search` using `psycopg.AsyncConnection` with identical SQL logic to the sync version. Added `psycopg[pool]` extra to pyproject.toml, installing psycopg-pool 3.3.0.

### Task 2: Create API subpackage with /search endpoint and extend app.py lifespan (60fe63c)

Created the `api/` subpackage with four files:

- **schemas.py**: `SearchRequest` (query with min_length=1, optional generation filter, limit 1-50), `SearchResultItem` (all chunk fields minus id), `SearchResponse` (query echo, results list, count).
- **deps.py**: `get_conn` yields async connection from pool, `get_settings` and `get_ollama_client` return app.state singletons.
- **routes.py**: `POST /search` normalizes generation filter (hyphen to underscore), embeds query via Ollama, runs `async_hybrid_search`, converts results to response model. Uses `Annotated[T, Depends()]` pattern.

Extended `app.py` lifespan to initialize `AsyncConnectionPool` (min_size=2, max_size=5) with `register_vector_async` configure callback, create `OllamaAsyncClient`, fire warm-up embedding (non-fatal on failure), store all on `app.state`, and close pool on shutdown.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Ruff B008 lint failure on Depends() in argument defaults**

- **Found during:** Task 2 commit
- **Issue:** Pre-commit hook ruff check flagged B008 for `Depends(get_conn)` etc. in function signature defaults
- **Fix:** Switched to `Annotated[T, Depends()]` pattern with module-level type aliases (`ConnDep`, `OllamaDep`, `SettingsDep`)
- **Files modified:** rag-ingestion/src/bbj_rag/api/routes.py
- **Commit:** 60fe63c

**2. [Rule 3 - Blocking] Unstaged uv.lock caused pre-commit conflict**

- **Found during:** Task 1 commit
- **Issue:** `uv sync` updated uv.lock but it was not staged, causing pre-commit "stashed changes conflicted with hook auto-fixes" error
- **Fix:** Staged uv.lock alongside Task 1 files
- **Files modified:** rag-ingestion/uv.lock
- **Commit:** 998386a

## Verification Results

All verification checks passed:

1. `from psycopg_pool import AsyncConnectionPool` -- psycopg-pool installed
2. `SearchResult(context_header='h', deprecated=False, ...)` -- new fields work
3. `from bbj_rag.search import async_hybrid_search` -- async function exists
4. `/search` in `[r.path for r in app.routes]` -- route registered
5. `uv run pytest tests/ -x -q` -- all 310 tests pass (1 skipped)

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| `Annotated[T, Depends()]` for DI | Modern FastAPI pattern; satisfies ruff B008 without disabling lint rule |
| Pool min_size=2, max_size=5 | Matches plan spec; sufficient for single-container deployment |
| register_vector_async as configure callback | Each pooled connection auto-registers pgvector types on checkout |
| Non-fatal embedding warm-up | Server starts even if Ollama is temporarily unavailable |

## Next Phase Readiness

Plan 22-02 (tests + error handling) can proceed. All interfaces are in place:
- `POST /search` endpoint is registered and importable
- `SearchRequest`/`SearchResponse` schemas are defined
- Dependency injection functions are available for test overrides
- `async_hybrid_search` is callable with `AsyncConnection`
