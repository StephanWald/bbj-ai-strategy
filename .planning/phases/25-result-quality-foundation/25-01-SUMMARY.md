---
phase: 25
plan: 01
subsystem: rag-ingestion
tags: [url-mapping, source-type, display-url, schema, backfill]
dependency_graph:
  requires: []
  provides:
    - url_mapping module (classify_source_type, map_display_url)
    - source_type and display_url columns on chunks table
    - Updated models and DB insert layer
    - Backfill script for existing chunks
  affects:
    - 25-02 (search API needs source_type for diversity ranking)
    - 25-03 (MCP server returns display_url in results)
tech_stack:
  added: []
  patterns:
    - Pure function module for URL classification and mapping
    - Idempotent ALTER TABLE migration in backfill script
    - Batch UPDATE with commit-per-batch for large table backfill
key_files:
  created:
    - rag-ingestion/src/bbj_rag/url_mapping.py
    - rag-ingestion/tests/test_url_mapping.py
    - rag-ingestion/scripts/backfill_urls.py
  modified:
    - rag-ingestion/sql/schema.sql
    - rag-ingestion/src/bbj_rag/models.py
    - rag-ingestion/src/bbj_rag/db.py
decisions: []
metrics:
  duration: 3m 25s
  completed: 2026-02-03
---

# Phase 25 Plan 01: URL Mapping and Data Foundation Summary

Pure-function URL mapping module with 6 source type classifications and display URL generation, plus schema/model/DB updates and a batch backfill script for existing chunks.

## What Was Done

### Task 1: URL Mapping Module and Unit Tests (f92b69b)

Created `rag-ingestion/src/bbj_rag/url_mapping.py` with two pure functions:

- **`classify_source_type(source_url)`** -- maps source URL prefixes to semantic labels using ordered prefix matching: `flare`, `pdf`, `bbj_source`, `mdx`, `wordpress`, `web_crawl`, or `unknown`
- **`map_display_url(source_url)`** -- transforms `flare://Content/...` to `https://documentation.basis.cloud/BASISHelp/WebHelp/...`, passes through `https://` URLs, and wraps unmappable URLs in brackets

Created `rag-ingestion/tests/test_url_mapping.py` with 20 tests using parametrized inputs covering all 6 source types plus edge cases (empty string, unknown scheme).

### Task 2: Schema, Models, DB Layer, and Backfill Script (f6c5018)

**Schema (`schema.sql`):**
- Added `source_type TEXT NOT NULL DEFAULT ''` and `display_url TEXT NOT NULL DEFAULT ''` columns to chunks table
- Added `idx_chunks_source_type` btree index for diversity queries

**Models (`models.py`):**
- Added `source_type: str = ""` and `display_url: str = ""` fields to both `Document` and `Chunk` models
- Updated `Chunk.from_content()` to accept and pass through `source_type` and `display_url` parameters
- All defaults are empty strings for backward compatibility

**DB Layer (`db.py`):**
- Updated `_INSERT_CHUNK_SQL` from 10 to 12 columns/placeholders
- Updated `_chunk_to_params()` to include `chunk.source_type` and `chunk.display_url`
- Updated `bulk_insert_chunks()` COPY column list, `set_types()`, `write_row()`, and INSERT ... SELECT to include both new columns

**Backfill Script (`scripts/backfill_urls.py`):**
- Idempotent `ALTER TABLE ADD COLUMN IF NOT EXISTS` migration
- Creates `idx_chunks_source_type` index
- Fetches distinct `source_url` values where `source_type = '' OR display_url = ''`
- Batch-updates using `classify_source_type()` and `map_display_url()` with commit every 1000 distinct URLs
- Logs progress and final counts

## Verification Results

- 20/20 url_mapping unit tests pass
- 338 existing tests pass (1 skipped), no regressions from model/DB changes
- 10 pre-existing PDF parser test failures (unrelated to this plan -- `_split_sections` receives list instead of string)
- `Chunk.from_content()` correctly accepts and stores `source_type` and `display_url`
- INSERT SQL has 12 columns and 12 `%s` placeholders (verified programmatically)
- Backfill script is syntactically valid

## Deviations from Plan

None -- plan executed exactly as written.

## Next Phase Readiness

Plan 25-02 (search API diversity ranking) can proceed. The `source_type` column and index are in place for source-balanced result ranking. Plan 25-03 (MCP server display URLs) can proceed once `display_url` is available on chunks.

The backfill script should be run against the production database before deploying search API changes that depend on `source_type` and `display_url` being populated.
