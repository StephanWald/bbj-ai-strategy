---
phase: 24-end-to-end-validation
plan: 02
subsystem: ingestion
tags: [pdf, pymupdf4llm, parser-fix, validation, pgvector, gap-closure]

# Dependency graph
requires:
  - phase: 24-end-to-end-validation
    plan: 01
    provides: "Validation script and initial VALIDATION.md report showing PDF as missing source"
provides:
  - "Fixed PDF parser that correctly extracts 23 sections from GuideToGuiProgrammingInBBj.pdf"
  - "47 PDF chunks in database (was 0)"
  - "Updated VALIDATION.md with all 6 sources represented in corpus"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pymupdf4llm single-string conversion (not page_chunks) for heading detection"
    - "Fallback to full-document single section when no headings detected"
    - "_strip_bold() to clean **bold** markers from PDF heading text"

key-files:
  created: []
  modified:
    - "rag-ingestion/src/bbj_rag/parsers/pdf.py"
    - "rag-ingestion/VALIDATION.md"

key-decisions:
  - "Use to_markdown(write_images=False) without page_chunks=True -- page_chunks suppresses heading detection"
  - "Add full-document fallback for PDFs with no detectable headings"
  - "Strip **bold** markers from heading text before slugifying"

patterns-established:
  - "pymupdf4llm page_chunks=True suppresses heading detection; avoid for section-based parsing"

# Metrics
duration: 7min
completed: 2026-02-02
---

# Phase 24 Plan 02: PDF Ingestion Fix Summary

**Fixed pymupdf4llm page_chunks heading suppression bug, producing 23 sections (47 chunks) from BBj GUI programming PDF -- all 6 corpus sources now populated**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-02T22:08:33Z
- **Completed:** 2026-02-02T22:15:46Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Diagnosed root cause: `pymupdf4llm.to_markdown(page_chunks=True)` suppresses heading detection, rendering PDF headings as `**bold**` text instead of `#` markdown headings, causing `_split_sections()` to find 0 matches
- Fixed PdfParser to use single-string markdown conversion (without `page_chunks`), which correctly produces 24 `#` headings and 23 content sections
- Added fallback for PDFs that have no detectable headings (full document as single section)
- Added `_strip_bold()` to clean bold markers from heading text
- Re-ingested PDF: 23 docs, 48 chunks, 47 stored (1 dedup)
- Total corpus increased from 50,392 to 50,439 chunks
- All 6 logical sources now confirmed in database: Flare (44,587), WordPress (2,950), Web Crawl (1,798), MDX (951), BBj Source (106), PDF (47)
- Regenerated VALIDATION.md with updated corpus stats

## Task Commits

Each task was committed atomically:

1. **Task 1: Diagnose PDF ingestion failure and fix root cause** - `62b41b9` (fix)
2. **Task 2: Re-run validation and update report** - `c314582` (docs)

## Files Created/Modified

- `rag-ingestion/src/bbj_rag/parsers/pdf.py` - Removed page_chunks=True and hdr_info logic; use single-string to_markdown(); added _strip_bold() and full-document fallback
- `rag-ingestion/VALIDATION.md` - Regenerated with 50,439 total chunks, updated timestamp, same 13/17 pass rate

## Decisions Made

- **Removed page_chunks=True:** The `page_chunks` parameter causes pymupdf4llm to return per-page dicts without converting headings to markdown `#` syntax. Without it, the library correctly identifies 24 headings from the PDF's font sizes, producing proper `#`/`##`/`###` markers that `_split_sections` can parse.
- **Removed hdr_info (TocHeaders/IdentifyHeaders) logic:** Without `page_chunks`, pymupdf4llm handles heading detection internally. The explicit `TocHeaders`/`IdentifyHeaders` calls were unnecessary scaffolding that added complexity without improving results.
- **Added full-document fallback:** If a future PDF has no detectable headings at all, the parser now yields the entire content as a single Document rather than silently producing 0 Documents. This prevents the "0 docs, 0 chunks, OK" silent failure that occurred.
- **Strip bold from headings:** pymupdf4llm wraps some heading text in `**bold**` markers (e.g., `### **Introduction**`). The new `_strip_bold()` function cleans these before slugifying and titling.

## Deviations from Plan

None -- plan executed exactly as written. The root cause was scenario (b) as predicted.

## Issues Encountered

- **`uv` not in container PATH:** The plan's diagnostic commands used `uv run bbj-ingest-all` but the runtime container only has the `.venv/bin` on PATH (uv is in the builder stage only). Used `bbj-ingest-all` directly instead. Not a code issue, just a command invocation detail.
- **Pre-commit trailing whitespace:** The validation script's generated VALIDATION.md had trailing whitespace. Pre-commit hook auto-fixed on second commit attempt.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The v1.4 milestone verification gap is now fully closed: all 6 logical sources have chunks in the database
- PDF and BBj Source still don't appear in cross-source query results (0.09% and 0.21% of corpus respectively) -- this is expected ranking behavior with Flare's 88% dominance, not a pipeline issue
- Source-balanced ranking remains a documented future improvement opportunity

---
*Phase: 24-end-to-end-validation*
*Completed: 2026-02-02*
