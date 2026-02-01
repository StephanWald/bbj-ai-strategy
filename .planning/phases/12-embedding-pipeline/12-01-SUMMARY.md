---
phase: 12-embedding-pipeline
plan: 01
subsystem: ingestion
tags: [chunker, embedder, ollama, pgvector, click, cli, pipeline, qwen3-embedding]

# Dependency graph
requires:
  - phase: 10-flare-parser
    provides: FlareParser yielding Document objects with markdown content
  - phase: 11-bbj-intelligence
    provides: tag_generation, classify_doc_type, build_context_header, extract_heading_hierarchy
  - phase: 09-schema-data-models
    provides: Chunk model with from_content() factory, schema.sql, db.py insert functions
provides:
  - Heading-aware markdown chunker (chunk_document)
  - Embedding client abstraction (OllamaEmbedder, OpenAIEmbedder, create_embedder)
  - Binary COPY bulk insert (bulk_insert_chunks)
  - Pipeline orchestrator (run_pipeline) wiring parse -> intelligence -> chunk -> embed -> store
  - Click CLI (bbj-rag ingest, bbj-rag parse, bbj-rag validate)
affects: [12-02-search-validation, future-search-api]

# Tech tracking
tech-stack:
  added: [ollama>=0.6, click>=8.1, pyyaml>=6.0, openai>=1.0 (dev)]
  patterns: [protocol-based embedding abstraction, binary COPY via staging table, heading-aware chunking]

key-files:
  created:
    - rag-ingestion/src/bbj_rag/chunker.py
    - rag-ingestion/src/bbj_rag/embedder.py
    - rag-ingestion/src/bbj_rag/pipeline.py
    - rag-ingestion/src/bbj_rag/cli.py
    - rag-ingestion/tests/test_chunker.py
    - rag-ingestion/tests/test_embedder.py
  modified:
    - rag-ingestion/pyproject.toml
    - rag-ingestion/sql/schema.sql
    - rag-ingestion/src/bbj_rag/config.py
    - rag-ingestion/src/bbj_rag/db.py
    - rag-ingestion/tests/test_db.py

key-decisions:
  - "vector(1024) matching Qwen3-Embedding-0.6B default output dimensions"
  - "Ollama as default embedding provider with OpenAI as configurable fallback"
  - "400-token target chunk size with 50-token overlap (~12%)"
  - "Context header prepended to chunk content for richer embeddings"
  - "Binary COPY via staging table + INSERT ON CONFLICT for idempotent bulk inserts"
  - "_fatal() helper for NoReturn-typed CLI error exits (mypy-clean)"

patterns-established:
  - "Protocol-based provider abstraction for swappable embedding backends"
  - "Code block placeholder protection during heading-aware splitting"
  - "Pipeline orchestrator with batch processing and resume mode"
  - "Click CLI with lazy imports for expensive dependencies"

# Metrics
duration: 7min
completed: 2026-02-01
---

# Phase 12 Plan 01: Embedding Pipeline Summary

**Heading-aware chunker, Ollama/OpenAI embedder abstraction, binary COPY bulk insert, and Click CLI orchestrating parse-to-pgvector pipeline**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-01T07:10:33Z
- **Completed:** 2026-02-01T07:18:24Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Heading-aware markdown chunker that splits at ## / ### boundaries, preserves fenced code blocks intact, and sub-splits oversized sections at paragraph/sentence boundaries
- Embedding client abstraction with OllamaEmbedder (primary, qwen3-embedding:0.6b) and OpenAIEmbedder (API fallback) plus create_embedder factory
- Binary COPY bulk insert via psycopg3 staging table pattern with idempotent ON CONFLICT dedup
- Pipeline orchestrator (run_pipeline) wiring parse -> intelligence -> chunk -> embed -> store with batch processing and resume mode
- Click CLI: `bbj-rag ingest --source flare` (full pipeline), `bbj-rag parse` (debug), `bbj-rag validate` (placeholder for Plan 12-02)
- 28 new unit tests (17 chunker, 11 embedder) with mocked backends -- all passing alongside 206 existing tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Foundation updates, chunker, and embedder with unit tests** - `aff7a41` (feat)
2. **Task 2: Pipeline orchestrator and Click CLI** - `431ab01` (feat)

## Files Created/Modified
- `rag-ingestion/src/bbj_rag/chunker.py` - Heading-aware markdown chunker with code block preservation
- `rag-ingestion/src/bbj_rag/embedder.py` - Embedding client abstraction (Ollama + OpenAI + factory)
- `rag-ingestion/src/bbj_rag/pipeline.py` - Pipeline orchestrator with batch processing and resume mode
- `rag-ingestion/src/bbj_rag/cli.py` - Click CLI with ingest, parse, and validate commands
- `rag-ingestion/tests/test_chunker.py` - 17 chunker unit tests
- `rag-ingestion/tests/test_embedder.py` - 11 embedder unit tests with mocked backends
- `rag-ingestion/pyproject.toml` - Added ollama, click, pyyaml deps + bbj-rag entry point
- `rag-ingestion/sql/schema.sql` - Changed vector(1536) to vector(1024) for Qwen3-Embedding-0.6B
- `rag-ingestion/src/bbj_rag/config.py` - New defaults: ollama provider, 1024 dims, 400 chunk size, 64 batch
- `rag-ingestion/src/bbj_rag/db.py` - Added bulk_insert_chunks(), updated INSERT with context_header/deprecated
- `rag-ingestion/tests/test_db.py` - Updated vector dimension assertion from 1536 to 1024

## Decisions Made
- vector(1024) matching Qwen3-Embedding-0.6B default output dimensions (changed from 1536)
- Ollama as default embedding provider with OpenAI as configurable fallback
- 400-token target chunk size with 50-token (~12%) overlap for heading-aware chunking
- Context header prepended to chunk content before embedding for richer semantic representation
- Binary COPY via staging table + INSERT ON CONFLICT pattern for bulk performance with idempotent dedup
- `_fatal()` helper for NoReturn-typed CLI error exits (keeps mypy strict mode clean)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_db.py vector dimension assertion**
- **Found during:** Task 1 (full test suite verification)
- **Issue:** Existing test asserted `vector(1536)` in schema.sql, but we changed to `vector(1024)`
- **Fix:** Updated assertion from `vector(1536)` to `vector(1024)` in `test_schema_sql_contains_required_elements`
- **Files modified:** rag-ingestion/tests/test_db.py
- **Verification:** Full test suite passes (234 tests)
- **Committed in:** aff7a41 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary test update to match the planned schema dimension change. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full embedding pipeline machinery is in place and ready for end-to-end testing
- Plan 12-02 (search validation) can now implement the `bbj-rag validate` command
- To run the pipeline: `ollama pull qwen3-embedding:0.6b` then `bbj-rag ingest --source flare`
- No blockers or concerns

---
*Phase: 12-embedding-pipeline*
*Completed: 2026-02-01*
