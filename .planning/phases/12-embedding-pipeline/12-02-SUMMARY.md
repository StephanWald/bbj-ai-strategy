---
phase: 12-embedding-pipeline
plan: 02
subsystem: search
tags: [pgvector, bm25, tsvector, rrf, hybrid-search, pytest, yaml, validation]

# Dependency graph
requires:
  - phase: 12-01-embedding-pipeline
    provides: schema.sql with chunks table, HNSW/GIN indexes, embedder.py, db.py, cli.py
  - phase: 09-schema-data-models
    provides: Chunk model, search_vector tsvector, generations GIN index
provides:
  - Dense vector search function (dense_search)
  - BM25 keyword search function (bm25_search)
  - Hybrid RRF search function (hybrid_search)
  - RRF SQL scoring function (rrf_score)
  - YAML-driven search validation test suite (15 cases, 4 categories)
  - CLI validate command wrapping pytest
affects: [future-search-api, phase-13-sources]

# Tech tracking
tech-stack:
  added: []
  patterns: [reciprocal-rank-fusion SQL, YAML-driven parametrized test cases, pytest marker separation]

key-files:
  created:
    - rag-ingestion/src/bbj_rag/search.py
    - rag-ingestion/tests/validation_cases.yaml
    - rag-ingestion/tests/test_search_validation.py
  modified:
    - rag-ingestion/sql/schema.sql
    - rag-ingestion/src/bbj_rag/cli.py
    - rag-ingestion/pyproject.toml

key-decisions:
  - "RRF with k=50 constant matching standard academic formula"
  - "search_validation pytest marker separates DB-requiring integration tests from unit tests"
  - "Default pytest addopts excludes search_validation so CI runs without database"
  - "validate CLI delegates to pytest subprocess for full reporting"

patterns-established:
  - "YAML data file for test cases -- engineers add cases without code changes"
  - "Pytest marker separation for integration vs unit tests"
  - "CLI command wrapping pytest for developer convenience"

# Metrics
duration: 5min
completed: 2026-02-01
---

# Phase 12 Plan 02: Search Validation Summary

**Hybrid search functions (dense, BM25, RRF) with rrf_score SQL function and 15-case YAML-driven pytest validation suite**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-01T07:22:33Z
- **Completed:** 2026-02-01T07:27:39Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Four search functions (dense_search, bm25_search, hybrid_search, plus generation-filtered variants) with parameterized SQL and SearchResult dataclass
- RRF SQL function (rrf_score) for hybrid Reciprocal Rank Fusion scoring using UNION ALL + window functions
- 15 YAML validation cases across 4 categories: dense (5), BM25 (4), generation-filtered (3), hybrid (3)
- Parametrized pytest suite loading cases from YAML with assertion helpers for URL, title, content, doc_type, and generations matching
- search_validation marker cleanly separates integration tests from the 234 unit tests
- `bbj-rag validate` CLI command wrapping pytest for developer convenience

## Task Commits

Each task was committed atomically:

1. **Task 1: Search functions and RRF SQL function** - `98be339` (feat)
2. **Task 2: YAML validation cases and parametrized test suite** - `5730859` (feat)

## Files Created/Modified
- `rag-ingestion/src/bbj_rag/search.py` - Dense, BM25, hybrid search functions with SearchResult dataclass
- `rag-ingestion/sql/schema.sql` - Added rrf_score() SQL function for hybrid RRF scoring
- `rag-ingestion/tests/validation_cases.yaml` - 15 search validation cases across 4 categories
- `rag-ingestion/tests/test_search_validation.py` - Parametrized pytest suite loading from YAML
- `rag-ingestion/src/bbj_rag/cli.py` - Replaced validate placeholder with pytest-delegating command
- `rag-ingestion/pyproject.toml` - Added search_validation marker and exclusion in default addopts

## Decisions Made
- RRF k=50 constant matching the standard academic formula (prevents division by zero, balances high/low rank influence)
- search_validation pytest marker separates DB-requiring integration tests from fast unit tests
- Default `uv run pytest` excludes search_validation via addopts `-m not search_validation`
- validate CLI command delegates to pytest subprocess (full reporting, marker filtering, -s for verbose)
- Using `typing.Any` for database row types to avoid complex psycopg generic overloads in strict mypy

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None -- no external service configuration required.

## Next Phase Readiness
- Phase 12 (Embedding Pipeline) is now fully complete
- Full validation cycle available: start PostgreSQL, apply schema, run `bbj-rag ingest --source flare`, then `bbj-rag validate`
- Engineers can extend validation by editing `tests/validation_cases.yaml` without code changes
- Ready for Phase 13+ source additions
- No blockers or concerns

---
*Phase: 12-embedding-pipeline*
*Completed: 2026-02-01*
