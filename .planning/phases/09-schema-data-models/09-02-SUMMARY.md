---
phase: 09-schema-data-models
plan: 02
subsystem: database
tags: [pgvector, psycopg, postgresql, ddl, schema, hnsw, gin, dedup]
requires:
  - phase: 09-schema-data-models plan 01
    provides: Pydantic Chunk model, Settings config
provides:
  - pgvector schema DDL with chunks table and indexes
  - Database connection module with register_vector
  - Idempotent chunk insert with ON CONFLICT dedup
  - Schema application helper
affects: [10-flare-parser, 11-bbj-intelligence, 12-embedding-pipeline]
tech-stack:
  added: []
  patterns: [pgvector DDL, ON CONFLICT dedup, register_vector, Json adapter]
key-files:
  created: [sql/schema.sql, db.py, schema.py, test_db.py]
  modified: []
key-decisions:
  - "Two-arg to_tsvector('english', ...) with || operator for IMMUTABLE generated column"
  - "coalesce() wrapping for NULL safety in string concatenation"
  - "Module-level _INSERT_CHUNK_SQL constant shared by single and batch insert"
  - "_chunk_to_params helper for consistent parameter tuple construction"
patterns-established:
  - "Standalone SQL DDL file executed by Python helper (separation of concerns)"
  - "register_vector() on every connection for pgvector type handling"
  - "ON CONFLICT (content_hash) DO NOTHING for idempotent re-ingestion"
  - "Json() adapter for JSONB serialization in psycopg"
  - "Source inspection tests to verify SQL correctness without live DB"
duration: 4min
completed: 2026-01-31
---

# Phase 09 Plan 02: Database Schema and pgvector Setup Summary

pgvector DDL with chunks table (BIGSERIAL, vector(1536), tsvector GENERATED ALWAYS AS, TEXT[] generations, UNIQUE content_hash), HNSW cosine index, 2 GIN indexes; db.py connection module with register_vector and ON CONFLICT dedup inserts; schema.py DDL applicator; 8 unit tests passing without live DB.

## What Was Done

### Task 1: Create pgvector schema DDL file
- Created `rag-ingestion/sql/schema.sql` with complete DDL
- CREATE EXTENSION IF NOT EXISTS vector
- chunks table: BIGSERIAL id, TEXT source_url/title/doc_type/content, VARCHAR(64) content_hash UNIQUE, TEXT[] generations, vector(1536) embedding (nullable), tsvector search_vector GENERATED ALWAYS AS, JSONB metadata, TIMESTAMPTZ created_at/updated_at
- HNSW index on embedding (cosine, m=16, ef_construction=64)
- GIN index on search_vector for full-text search
- GIN index on generations for array containment queries
- Header comment documents all immutability pitfalls avoided
- Commit: `8799218`

### Task 2: Create database connection module and schema helper
- Created `rag-ingestion/src/bbj_rag/db.py` with get_connection(), insert_chunk(), insert_chunks_batch()
- get_connection() opens psycopg connection and calls register_vector() for pgvector type handling
- insert_chunk() uses ON CONFLICT (content_hash) DO NOTHING with RETURNING id for dedup detection
- insert_chunks_batch() uses executemany for batch efficiency, returns rowcount of inserted rows
- Json() adapter wraps metadata dict for JSONB column serialization
- Created `rag-ingestion/src/bbj_rag/schema.py` with apply_schema() that reads and executes sql/schema.sql
- All imports verified, ruff clean, mypy strict clean (5 source files)
- Commit: `a7e143b`

### Task 3: Add unit tests for database module
- Created `rag-ingestion/tests/test_db.py` with 8 tests (no live PostgreSQL required)
- Module export tests for db.py (3 functions) and schema.py (1 function)
- Schema SQL file existence and size verification
- Required DDL elements: extension, table, columns, indexes, generated column
- Pitfall avoidance: no concat()/concat_ws() in SQL body, uses || and coalesce()
- Insert dedup verification via source inspection for ON CONFLICT clause
- RETURNING id and register_vector presence verified
- Full suite: 22 tests passing (11 models + 3 config + 8 db)
- Commit: `1787fa6`

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Two-arg to_tsvector with \|\| operator | Single-arg form and concat() are STABLE, not IMMUTABLE -- PostgreSQL rejects them in GENERATED columns |
| coalesce() for NULL safety | NULL \|\| 'text' returns NULL, breaking the generated tsvector |
| Module-level SQL constant | Single INSERT statement shared by insert_chunk and insert_chunks_batch avoids drift |
| _chunk_to_params helper | DRY parameter construction ensures consistent field ordering |
| Source inspection tests | Verify SQL correctness and function behavior without requiring a live database |
| Standalone DDL file | sql/schema.sql can be used independently (psql, migration tools) or via apply_schema() |

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

| Check | Result |
|-------|--------|
| schema.sql DDL completeness | All elements present (extension, table, 3 indexes) |
| db.py imports | get_connection, insert_chunk, insert_chunks_batch all importable |
| schema.py imports | apply_schema importable |
| pytest -v | 22 passed (0.40s) |
| ruff check src/ tests/ | All checks passed |
| mypy src/bbj_rag/ | Success: no issues found in 5 source files |
| Immutability pitfalls | Two-arg to_tsvector, \|\| operator, coalesce -- verified |
| register_vector in get_connection | Present -- verified via source inspection |
| ON CONFLICT dedup in insert | Present -- verified via source inspection |
| Json() adapter for metadata | Present in _chunk_to_params |

## Next Phase Readiness

Phase 09 (Schema & Data Models) is now complete. Both plans delivered:
- 09-01: Pydantic models (Document, Chunk) and Settings configuration
- 09-02: pgvector DDL, database connection module, schema applicator

Phase 10 (Flare Parser) can proceed -- it will import Chunk from bbj_rag.models and use insert_chunk/insert_chunks_batch from bbj_rag.db to store parsed documentation fragments.
