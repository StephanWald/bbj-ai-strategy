---
phase: 11-bbj-intelligence
plan: 01
subsystem: intelligence
tags: [strenum, signal-scoring, generation-tagging, dataclass, regex, pydantic]

# Dependency graph
requires:
  - phase: 10-flare-parser
    provides: Document/Chunk models, condition tag extraction, parsers
provides:
  - Generation StrEnum with 5 canonical product generation labels
  - Multi-signal generation tagger (path + condition + content)
  - Signal dataclass and resolve_signals() aggregation
  - Summary report module (build_report, print_report)
  - Document/Chunk context_header and deprecated fields
  - Updated SQL DDL with context_header, deprecated columns, search_vector including context_header
affects: [11-02-doc-type-classifier, 11-03-context-headers, 12-chunking, 13-embedding]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "StrEnum with auto() for type-safe string labels"
    - "Frozen dataclass with slots for immutable signal containers"
    - "Signal-based scoring with weighted aggregation and threshold resolution"
    - "Module-level compiled regex patterns for content matching"

key-files:
  created:
    - rag-ingestion/src/bbj_rag/intelligence/__init__.py
    - rag-ingestion/src/bbj_rag/intelligence/generations.py
    - rag-ingestion/src/bbj_rag/intelligence/report.py
    - rag-ingestion/tests/test_generations.py
  modified:
    - rag-ingestion/src/bbj_rag/models.py
    - rag-ingestion/sql/schema.sql

key-decisions:
  - "Generation StrEnum auto() produces lowercase values: all, character, vpro5, bbj_gui, dwc"
  - "resolve_signals returns ['untagged'] sentinel (not empty list) for below-threshold signals"
  - "Primary.BASISHelp is NOT a generation signal (informational only)"
  - "Primary.Deprecated/Superseded are lifecycle flags, not generation signals"
  - "Signal weights: path=0.6, condition=0.3-0.5, content=0.4"
  - "context_header stored as separate field to avoid content_hash mutation"

patterns-established:
  - "intelligence/ package as classification layer consuming parser output"
  - "Signal-based multi-source scoring pattern for document classification"
  - "Threshold-based resolution with untagged sentinel for ambiguous documents"

# Metrics
duration: 4min
completed: 2026-01-31
---

# Phase 11 Plan 01: Generation Tagger Summary

**Multi-signal generation tagger classifying BBj docs into 5 product generations (all, character, vpro5, bbj_gui, dwc) using path prefixes, condition tags, and content regex patterns with weighted signal aggregation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-31T21:41:59Z
- **Completed:** 2026-01-31T21:46:23Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Generation StrEnum with 5 canonical labels replacing the flat "bbj" default from Phase 10
- Signal-based scoring architecture: path (0.6 weight), condition tag (0.3-0.5), content pattern (0.4) with 0.3 threshold
- Ambiguous documents flagged as "untagged" sentinel instead of silently defaulting to "all"
- Document/Chunk models extended with context_header and deprecated fields (backward-compatible defaults)
- 46 tests covering all signal extractors, resolution, integration, model updates, and report module
- Full test suite passes (223 tests, 0 regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create intelligence package, Generation StrEnum, model updates, and DDL changes** - `ce1b3d9` (feat)
2. **Task 2: Write comprehensive tests for generation tagger** - `cc19341` (test)

## Files Created/Modified
- `rag-ingestion/src/bbj_rag/intelligence/__init__.py` - Public API re-exports (Generation, tag_generation, build_report, print_report)
- `rag-ingestion/src/bbj_rag/intelligence/generations.py` - Generation StrEnum, Signal dataclass, 3 signal extractors, resolver, tag_generation()
- `rag-ingestion/src/bbj_rag/intelligence/report.py` - build_report() structured data and print_report() formatted output
- `rag-ingestion/tests/test_generations.py` - 46 tests covering all generation tagger functionality
- `rag-ingestion/src/bbj_rag/models.py` - Added context_header (str, default "") and deprecated (bool, default False) to Document/Chunk
- `rag-ingestion/sql/schema.sql` - Added context_header, deprecated columns; search_vector includes context_header

## Decisions Made
- **Generation StrEnum with auto()**: Produces lowercase string values automatically (e.g., BBJ_GUI -> "bbj_gui"), serializes cleanly to JSON and database
- **["untagged"] sentinel**: Preserves backward compatibility with generations_must_not_be_empty validator while flagging ambiguous content explicitly
- **Primary.BASISHelp excluded as generation signal**: 84.6% of files have it, making it non-discriminating; it means "included in BASISHelp build" not "belongs to a generation"
- **Lifecycle flags separate from generation**: Primary.Deprecated and Primary.Superseded become the `deprecated` boolean field, not generation labels
- **Signal weights from Research**: path=0.6, condition=0.3-0.5, content=0.4 with 0.3 aggregation threshold; designed so single path match is sufficient
- **context_header as separate field**: Keeps content_hash stable when TOC/breadcrumb structure changes

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Two ruff line-length (E501) errors in generations.py from long condition/append lines - fixed by wrapping expressions
- ruff format hook reformatted files on first commit attempts - re-staged and committed cleanly

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- intelligence/ package ready for Plan 11-02 (DocType classifier) to add doc_types.py alongside generations.py
- context_header field ready for Plan 11-03 to populate from TOC breadcrumbs and heading hierarchy
- tag_generation() ready to replace map_conditions_to_generations() in Flare and web crawl parsers
- No blockers or concerns

---
*Phase: 11-bbj-intelligence*
*Completed: 2026-01-31*
