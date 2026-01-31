---
phase: 10-flare-parser
plan: 02
subsystem: parser
tags: [lxml, xhtml, flare, madcap, markdown, code-blocks, tables, snippets]

# Dependency graph
requires:
  - phase: 10-01
    provides: DocumentParser protocol, flare_toc.py, flare_cond.py, models.py
provides:
  - FlareParser class parsing 7,079 XHTML topic files into Document objects
  - MadCap namespace tag handling (12 tag types)
  - Code block preservation as markdown fenced blocks with language hints
  - Table-to-markdown conversion (Methods_Table, Parameter_Table, Flag_Table)
  - Code_Table extraction as code blocks (not markdown tables)
  - Snippet resolution from .flsnp files with backslash path normalization
  - TOC hierarchy paths with directory fallback for orphan topics
  - Condition-to-generation mapping in Document metadata
affects: [10-03, chunking, embedding, rag-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Generator-based parser yielding Documents one at a time"
    - "Pre-loaded snippet dict for O(1) resolution during tree walk"
    - "Recursive element walker with MadCap tag dispatch"
    - "Type alias _SnippetMap to reduce function signature verbosity"

key-files:
  created:
    - "rag-ingestion/src/bbj_rag/parsers/flare.py"
    - "rag-ingestion/tests/test_flare_parser.py"
  modified: []

key-decisions:
  - "Backslash-to-forward-slash normalization for snippet src attributes (Windows-authored paths on macOS)"
  - "58 unresolvable snippet references are genuine Flare authoring issues -- graceful degradation via warning log"
  - "3 files with encoding errors caught by general Exception handler (OSError, not XMLSyntaxError)"
  - "Block containers extracted as frozenset for O(1) lookup"

patterns-established:
  - "_SnippetMap type alias for dict[str, etree._Element] reduces function signature length"
  - "Dispatch pattern: _handle_madcap, _handle_pre, _handle_table, _handle_paragraph"
  - "Inline text collection via recursive _collect_inline_text with MadCap sub-dispatch"
  - "Circular snippet guard via seen_snippets set parameter"

# Metrics
duration: 9min
completed: 2026-01-31
---

# Phase 10 Plan 02: Flare XHTML Parser Summary

**FlareParser yielding 7,079 Documents from raw MadCap Flare XHTML with code blocks, markdown tables, snippet inlining, and condition-to-generation mapping**

## Performance

- **Duration:** 9 min
- **Started:** 2026-01-31T20:43:18Z
- **Completed:** 2026-01-31T20:52:37Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments
- FlareParser parses 7,079 topic files (out of 7,083 -- 3 encoding errors, 1 empty) into validated Document objects
- Zero raw MadCap namespace tags leak into document content (12 tag types handled)
- 3,294 documents contain markdown fenced code blocks with language hints (bbj, java, css, xml, sql)
- 5,407 documents contain properly converted markdown tables
- Snippets resolved with backslash path normalization (205 pre-loaded, 58 genuinely unresolvable)
- Conditions mapped to generations: 5,961+ BBj docs, 108 deprecated, 49 not-implemented
- 131 tests pass across full suite (39 new for FlareParser)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement FlareParser** - `29a6139` (feat)
2. **Task 2: Write comprehensive tests** - `1165cda` (test)

## Files Created/Modified
- `rag-ingestion/src/bbj_rag/parsers/flare.py` - FlareParser class with full XHTML content extraction pipeline (734 lines)
- `rag-ingestion/tests/test_flare_parser.py` - 39 tests: 15 integration (real files) + 24 unit (synthetic XHTML)

## Decisions Made
- **Backslash normalization**: Snippet `src` attributes use Windows backslash paths (`..\..\Resources\Snippets\foo.flsnp`). Added `src.replace("\\", "/")` before path resolution. This fixed snippet resolution for the majority of references.
- **Unresolvable snippets**: 58 snippet references point to non-existent local files (e.g., `bui.flsnp` resolved relative to topic directory instead of Snippets directory). These are genuine Flare authoring issues. Parser logs warnings and continues -- graceful degradation.
- **Encoding errors**: 3 topic files have invalid byte encoding (OSError, not XMLSyntaxError). The general Exception handler catches these, logs warnings, and skips the files.
- **frozenset for tag sets**: Used frozenset for _STRIP_TAGS, _KEEP_TEXT_TAGS, and _BLOCK_CONTAINERS for immutable O(1) membership testing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Windows backslash paths in snippet src attributes**
- **Found during:** Task 1 (initial sanity check)
- **Issue:** Snippet `src` attributes contain Windows-style backslash paths (`..\..\Resources\Snippets\foo.flsnp`) that don't resolve correctly on macOS
- **Fix:** Added `src.replace("\\", "/")` normalization before path resolution
- **Files modified:** rag-ingestion/src/bbj_rag/parsers/flare.py
- **Verification:** Snippet warnings dropped from 150+ to 58 (genuinely unresolvable), document count rose from 7,073 to 7,079
- **Committed in:** 29a6139 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for correct snippet resolution. No scope creep.

## Issues Encountered
- mypy strict mode flagged `row` variable shadowing between `for row in rows` (etree._Element) and `for row in md_rows` (list[str]) loops. Resolved by renaming second loop variable to `md_row`.
- ruff line-length violations (88 char limit) required refactoring long function calls into helper functions (_handle_madcap, _handle_pre, _handle_table, _handle_paragraph) and using _SnippetMap type alias.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- FlareParser is fully operational, producing 7,079 Documents ready for chunking
- Plan 10-03 (web crawl fallback parser) can proceed independently
- Downstream chunking/embedding phases have validated Document objects to consume
- No blockers

---
*Phase: 10-flare-parser*
*Completed: 2026-01-31*
