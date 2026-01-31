---
phase: 10-flare-parser
plan: 01
subsystem: parsers
tags: [lxml, madcap-flare, toc, conditions, xml-parsing, protocol]

# Dependency graph
requires:
  - phase: 09-schema-data-models
    provides: Document and Chunk Pydantic models (bbj_rag.models)
provides:
  - DocumentParser Protocol with parse() -> Iterator[Document] contract
  - build_toc_index() mapping 1,595 topics to arrow-separated breadcrumbs from 4 .fltoc files
  - directory_fallback_path() for orphan topic hierarchy derivation
  - Condition tag extraction (parse_condition_tag_set, extract_topic_conditions, extract_inline_conditions)
  - map_conditions_to_generations() mapping 6 generation-relevant tags to labels
  - MADCAP_NS constant shared across all parsers
affects: [10-02-flare-xhtml-parser, 10-03-web-crawl-parser, 11-chunking]

# Tech tracking
tech-stack:
  added: [lxml>=5.3, httpx>=0.28, beautifulsoup4>=4.13, lxml-stubs>=0.5]
  patterns: [DocumentParser Protocol, lxml.etree XML parsing, flat TOC index lookup, condition-to-generation mapping]

key-files:
  created:
    - rag-ingestion/src/bbj_rag/parsers/__init__.py
    - rag-ingestion/src/bbj_rag/parsers/flare_toc.py
    - rag-ingestion/src/bbj_rag/parsers/flare_cond.py
    - rag-ingestion/tests/test_flare_toc.py
    - rag-ingestion/tests/test_flare_cond.py
  modified:
    - rag-ingestion/pyproject.toml
    - rag-ingestion/uv.lock

key-decisions:
  - "runtime_checkable on DocumentParser Protocol for isinstance checks"
  - "Frozen dataclass (not TypedDict) for ConditionTag -- immutable with slots for efficiency"
  - "LinkedTitle resolution falls back through <title> -> <h1> -> filename stem"
  - "extract_inline_conditions returns tag[index] identifiers for element-level condition tracking"

patterns-established:
  - "Protocol-based parser contract: all parsers implement parse() -> Iterator[Document]"
  - "lxml.etree.parse() with XMLParser(remove_comments=True) for all Flare XML files"
  - "Flat dict[str, str] TOC index -- build once, O(1) lookup per topic"
  - "Priority-ordered TOC parsing: basishelp > emhelp > bdthelp > pro5toc, first-found wins"
  - "Default to generations=['bbj'] when no conditions or no generation-relevant conditions"

# Metrics
duration: 7min
completed: 2026-01-31
---

# Phase 10 Plan 01: Parser Foundations Summary

**DocumentParser protocol, TOC index builder (1,595 entries from 4 .fltoc files), and condition tag extractor (12 tags, 6 generation-relevant) using lxml.etree**

## Performance

- **Duration:** 7 min
- **Started:** 2026-01-31T20:29:56Z
- **Completed:** 2026-01-31T20:37:11Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Defined DocumentParser Protocol as the contract for all parsers (Flare, web crawl)
- Built TOC index from all 4 .fltoc files producing 1,595 entries with correct priority ordering and LinkedTitle resolution
- Implemented condition tag extraction with 6 generation-relevant mappings (bbj, bdt, em, deprecated, superseded, not_implemented)
- 44 tests covering both synthetic unit tests and real Flare project integration tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Add dependencies and create parsers package** - `f3d4b0f` (feat)
2. **Task 2: Write tests for TOC index and condition extraction** - `5ac4cbe` (test)

## Files Created/Modified
- `rag-ingestion/pyproject.toml` - Added lxml, httpx, bs4 dependencies; lxml-stubs dev dep
- `rag-ingestion/uv.lock` - Lock file updated with new dependencies
- `rag-ingestion/src/bbj_rag/parsers/__init__.py` - DocumentParser Protocol, MADCAP_NS constant
- `rag-ingestion/src/bbj_rag/parsers/flare_toc.py` - TOC index builder from .fltoc files with LinkedTitle resolution and directory fallback
- `rag-ingestion/src/bbj_rag/parsers/flare_cond.py` - Condition tag set parser, per-topic condition extractor, generation mapper
- `rag-ingestion/tests/test_flare_toc.py` - 20 tests (12 synthetic unit, 8 real Flare integration)
- `rag-ingestion/tests/test_flare_cond.py` - 24 tests (18 synthetic unit, 6 real Flare integration)

## Decisions Made
- Used `runtime_checkable` on DocumentParser Protocol to enable isinstance checks in tests
- Chose frozen dataclass with slots for ConditionTag (immutable, memory-efficient) over TypedDict
- LinkedTitle resolution chain: `<title>` tag -> `<h1>` text -> filename stem with underscores replaced
- extract_inline_conditions uses `tag[index]` identifiers (e.g., `p[0]`, `h2[1]`) for element-level tracking

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- mypy strict flagged `itertext()` return type as `Iterator[str | bytes] | Any` -- fixed by wrapping with `str()` cast in join comprehension
- ruff format reformatted test files during pre-commit -- re-staged and committed cleanly

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Parser foundations (protocol, TOC index, conditions) ready for Plan 02 (Flare XHTML parser)
- Web crawl parser (Plan 03) can use the DocumentParser protocol and httpx/bs4 dependencies
- No blockers or concerns

---
*Phase: 10-flare-parser*
*Completed: 2026-01-31*
