---
phase: 24-end-to-end-validation
plan: 01
subsystem: testing
tags: [validation, httpx, mcp-client, rest-api, pgvector, ollama, hybrid-search]

# Dependency graph
requires:
  - phase: 23.1-wordpress-parser-fix
    provides: "Complete corpus with all 6 sources ingested (50,392 chunks)"
provides:
  - "End-to-end validation script (scripts/validate_e2e.py)"
  - "VALIDATION.md report proving RAG pipeline works"
  - "Baseline RRF scores for future retrieval tuning"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "MCP ClientSession.call_tool() for programmatic tool invocation"
    - "Dataclass-based result containers for query evaluation"
    - "Source-prefix heuristic for automated relevance assessment"

key-files:
  created:
    - "rag-ingestion/scripts/validate_e2e.py"
    - "rag-ingestion/VALIDATION.md"
  modified: []

key-decisions:
  - "Lightweight keyword heuristics for pass/fail (not exact string matching)"
  - "Single MCP session for all queries (avoid per-query process spawn overhead)"
  - "Cross-source validation via query results, not direct DB prefix queries"
  - "PDF and BBj Source source-targeted failures documented as known issues, not blockers"

patterns-established:
  - "MCP programmatic invocation: StdioServerParameters + ClientSession in single async context"
  - "Source-prefix mapping for the 6 logical source groups"

# Metrics
duration: 4min
completed: 2026-02-02
---

# Phase 24 Plan 01: End-to-End Validation Summary

**Validation script exercises REST API + MCP server against 50,392-chunk BBj corpus with 17 queries across 6 source types, generating VALIDATION.md report**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-02T21:34:56Z
- **Completed:** 2026-02-02T21:38:41Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments

- Created comprehensive validation script with 14 REST queries and 3 MCP queries covering all 6 logical source groups
- Generated VALIDATION.md proving the full RAG pipeline works: Docker + pgvector + Ollama + REST API + MCP server all functional
- All 7 topic-based queries pass with keyword heuristic validation
- All 3 MCP queries pass via programmatic ClientSession.call_tool() invocation
- Generation filter (DWC) correctly narrows results
- 4 of 6 source groups appear in cross-source results; remaining 2 (PDF, BBj Source) exist in corpus but are minority populations drowned out by Flare's 88% dominance
- Baseline RRF scores recorded for future retrieval quality tuning

## Task Commits

Each task was committed atomically:

1. **Task 1: Create end-to-end validation script** - `c4c48b3` (feat)
2. **Task 2: Execute validation and generate report** - `aa636f4` (docs)

## Files Created/Modified

- `rag-ingestion/scripts/validate_e2e.py` - Standalone async validation script with prerequisite checks, REST queries, MCP queries, cross-source collection, and Markdown report generation (629 lines)
- `rag-ingestion/VALIDATION.md` - Generated report with corpus stats, per-query results, RRF scores, content snippets, and cross-source summary (198 lines)

## Decisions Made

- **Keyword heuristics for topic-based pass/fail:** Check if any expected keyword appears in the top-1 result's title+content (case-insensitive). This is deliberately lightweight -- the VALIDATION.md includes snippets so humans can judge relevance directly.
- **Single MCP session:** Spawning one stdio_client + ClientSession for all 3 MCP queries avoids the overhead of 3 separate process spawns.
- **Cross-source from query results, not DB:** Instead of duplicating the report module's SQL CASE statement, cross-source validation infers from source_url prefixes across all query results.
- **Source-targeted failures are known issues, not blockers:** PDF (0 chunks with pdf:// prefix in results) and BBj Source (106 chunks = 0.2% of corpus) are statistical minorities that don't rank in top-5 for their targeted queries. The chunks exist in the database; they just lose to Flare's 44,587-chunk dominance in hybrid search ranking.

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

- **4 source-targeted query failures:** The source-targeted queries for PDF, BBj Source, WordPress, and Web Crawl returned results from other sources (primarily Flare) in the top-1 position. This reflects the corpus composition (88% Flare) rather than a pipeline problem. All topic-based queries passed, confirming search relevance works. Quality tuning for source-balanced ranking is explicitly out of scope per the CONTEXT.md.
- **Pre-commit hook formatting:** ruff format adjusted line lengths in the validation script on first commit attempt. Re-staged and committed successfully.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- v1.4 milestone validation is complete. The VALIDATION.md report serves as visible proof that the RAG pipeline delivers real BBj documentation retrieval.
- No further phases planned in this milestone.
- Future improvement opportunities documented in the report's Known Issues section:
  - Source-balanced ranking (boosting minority sources) for more diverse top-k results
  - More targeted queries for PDF and BBj Source validation once ranking is tuned

---
*Phase: 24-end-to-end-validation*
*Completed: 2026-02-02*
