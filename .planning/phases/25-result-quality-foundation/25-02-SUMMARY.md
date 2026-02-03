---
phase: 25
plan: 02
subsystem: rag-ingestion
tags: [search, diversity, reranking, display-url, source-type, api, mcp]
dependency_graph:
  requires:
    - 25-01 (url_mapping module, source_type/display_url columns)
  provides:
    - SearchResult with display_url and source_type fields
    - rerank_for_diversity() function with SOURCE_BOOST config
    - API response with display_url, source_type, source_type_counts
    - MCP formatted output with display_url as primary source link
  affects:
    - 25-03 (validation plan can verify end-to-end diversity behavior)
    - 26 (chat interface consumes enriched search responses)
tech_stack:
  added: []
  patterns:
    - Over-fetch 2x then rerank for diversity pool
    - Domination threshold gating (only rerank when >= 80% single type)
    - Multiplicative score boost for minority source types
key_files:
  created: []
  modified:
    - rag-ingestion/src/bbj_rag/search.py
    - rag-ingestion/src/bbj_rag/api/schemas.py
    - rag-ingestion/src/bbj_rag/api/routes.py
    - rag-ingestion/src/bbj_rag/mcp_server.py
decisions: []
metrics:
  duration: 3m 21s
  completed: 2026-02-03
---

# Phase 25 Plan 02: Search Result Diversity Summary

Display URL and source type fields propagated through SearchResult -> API schemas -> REST response -> MCP output, with source-balanced diversity reranking via multiplicative boost when a single source type dominates >= 80% of results.

## What Was Done

### Task 1: Enrich SearchResult and add diversity reranking (ed3a1e8)

**SearchResult dataclass:**
- Added `display_url: str` and `source_type: str` fields after `deprecated`, before `score`

**_rows_to_results() column mapping:**
- Updated from 9 to 11 columns: `id(0), source_url(1), title(2), content(3), doc_type(4), generations(5), context_header(6), deprecated(7), display_url(8), source_type(9), score(10)`

**All 4 search functions updated:**
- `dense_search`: Added `display_url, source_type` to SELECT before score expression
- `bm25_search`: Added `display_url, source_type` to SELECT before score expression
- `hybrid_search`: Added `display_url, source_type` to sub-query SELECTs, outer SELECT, and GROUP BY
- `async_hybrid_search`: Same changes as hybrid_search

**rerank_for_diversity() function:**
- `SOURCE_BOOST` dict: pdf=1.3, bbj_source=1.3, mdx=1.2, others=1.0
- `DOMINATION_THRESHOLD = 0.8`
- Algorithm: count source types, check if any >= 80%, if dominated apply multiplicative boost and re-sort, return top `limit` results using `dataclasses.replace()` for immutable update
- Both `SOURCE_BOOST` and `rerank_for_diversity` added to `__all__`

### Task 2: Update API schemas, routes, and MCP formatting (220dbf9)

**schemas.py:**
- Added `display_url: str` and `source_type: str` to `SearchResultItem`
- Added `source_type_counts: dict[str, int]` with `Field(default_factory=dict)` to `SearchResponse`

**routes.py:**
- Imported `rerank_for_diversity` from `bbj_rag.search` and `Counter` from collections
- Over-fetch: `limit=body.limit * 2` in async_hybrid_search call
- Apply `rerank_for_diversity(raw_results, limit=body.limit)` after search
- Compute `source_type_counts` via `Counter(r.source_type for r in results)`
- Pass `display_url`, `source_type`, and `source_type_counts` to response constructors

**mcp_server.py:**
- Replaced `Source: {r['source_url']}` with `Source: {r.get('display_url', r['source_url'])}` (display_url as primary, fallback to source_url)
- Added `Source Type: {r['source_type']}` line when source_type is present
- Header includes source breakdown when `source_type_counts` is available: `"Found N results for: query (flare: 3, pdf: 2)"`

## Verification Results

- `from bbj_rag.search import SearchResult, rerank_for_diversity, SOURCE_BOOST` -- imports clean
- `SearchResultItem.model_fields` contains `display_url` and `source_type`
- `SearchResponse.model_fields` contains `source_type_counts`
- `from bbj_rag.api.routes import router` -- imports clean
- `from bbj_rag.mcp_server import _format_results` -- imports clean
- Inline unit tests: empty input, diverse results (no reranking), dominated results (pdf boosted to rank 1)
- 339 existing tests pass (10 pre-existing PDF parser failures, 1 skipped -- all unrelated)

## Deviations from Plan

None -- plan executed exactly as written.

## Next Phase Readiness

Plan 25-03 (validation) can verify the full chain end-to-end. The search pipeline now carries display_url, source_type through every layer. Diversity reranking will activate automatically when Flare dominates result sets (88% of corpus).

Note: The backfill script from plan 25-01 must be run before these changes take effect, as the display_url and source_type columns need to be populated in the database.
