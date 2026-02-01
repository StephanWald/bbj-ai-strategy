---
phase: 13-additional-parsers
plan: 03
subsystem: parser
tags: [mdx, docusaurus, frontmatter, jsx, pipeline, cli, dwc-course]

# Dependency graph
requires:
  - phase: 13-additional-parsers (plans 01, 02)
    provides: PDF parser, BBj source parser, WordPress parsers (Advantage + KB)
  - phase: 10-flare-parser
    provides: DocumentParser protocol, pipeline orchestration, CLI framework
  - phase: 11-bbj-intelligence
    provides: Intelligence classification (generation tagging, doc_type, context_header)
provides:
  - MdxParser for DWC-Course .md/.mdx files with frontmatter and JSX stripping
  - Pipeline intelligence bypass for pre-populated Documents
  - CLI expanded to all 6 source types (flare, pdf, advantage, kb, mdx, bbj-source)
  - Config settings for all parser source paths
affects: [14-documentation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Intelligence bypass: non-Flare parsers pre-populate doc_type/generations, pipeline skips Flare intelligence"
    - "Uniform generation tagging: all DWC-Course content tagged ['dwc']"
    - "JSX stripping via regex passes: imports, self-closing, wrapper tags, className divs"

key-files:
  created:
    - rag-ingestion/src/bbj_rag/parsers/mdx.py
    - rag-ingestion/tests/test_mdx_parser.py
    - rag-ingestion/tests/test_pipeline.py
  modified:
    - rag-ingestion/src/bbj_rag/pipeline.py
    - rag-ingestion/src/bbj_rag/cli.py
    - rag-ingestion/src/bbj_rag/config.py

key-decisions:
  - "Pipeline intelligence bypass: check doc.doc_type non-empty and != 'web_crawl' to skip _apply_intelligence"
  - "DWC-Course uniform tagging: all content gets generations=['dwc'] and doc_type='tutorial'"
  - "Context header format: 'DWC Course > {chapter} > {title}' with chapter derived from parent dir name"
  - "Title priority: frontmatter title > first # heading > filename stem"

patterns-established:
  - "Intelligence bypass guard: pipeline checks doc_type to decide Flare intelligence vs parser-provided values"
  - "Lazy parser imports in CLI: each source branch imports only when selected"

# Metrics
duration: 4min
completed: 2026-02-01
---

# Phase 13 Plan 03: MDX Parser & Full Integration Summary

**Docusaurus MDX parser for DWC-Course with JSX stripping, plus pipeline intelligence bypass and CLI expansion to all 6 source types**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-01T08:28:12Z
- **Completed:** 2026-02-01T08:32:12Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- MdxParser extracts content from DWC-Course .md/.mdx files with frontmatter metadata parsed and JSX stripped
- Pipeline intelligence bypass correctly skips Flare intelligence for pre-populated Documents from non-Flare parsers
- CLI supports all 6 sources: flare, pdf, advantage, kb, mdx, bbj-source
- Config expanded with settings for pdf_source_path, mdx_source_path, bbj_source_dirs, advantage_index_url, kb_index_url
- 16 new tests (13 MDX parser + 3 pipeline bypass) all passing; full suite 299 passed

## Task Commits

Each task was committed atomically:

1. **Task 1: MDX parser and pipeline integration** - `a083a34` (feat)
2. **Task 2: Unit tests for MDX parser and pipeline intelligence bypass** - `d2b06f8` (test)

**Plan metadata:** [pending] (docs: complete plan)

## Files Created/Modified

- `rag-ingestion/src/bbj_rag/parsers/mdx.py` - MdxParser: Docusaurus MDX parser with frontmatter extraction, JSX stripping, uniform dwc generation tagging
- `rag-ingestion/src/bbj_rag/pipeline.py` - Intelligence bypass guard for pre-populated Documents
- `rag-ingestion/src/bbj_rag/cli.py` - Expanded to 6 source types with lazy imports per branch
- `rag-ingestion/src/bbj_rag/config.py` - Added pdf_source_path, mdx_source_path, bbj_source_dirs, advantage_index_url, kb_index_url
- `rag-ingestion/tests/test_mdx_parser.py` - 13 unit tests for MDX parser
- `rag-ingestion/tests/test_pipeline.py` - 3 tests for pipeline intelligence bypass

## Decisions Made

- Pipeline intelligence bypass: when doc.doc_type is non-empty and not "web_crawl", parser-provided values are used as-is (skip Flare intelligence)
- DWC-Course uniform tagging: all content gets generations=["dwc"] and doc_type="tutorial" regardless of individual file content
- Context header for MDX: "DWC Course > {chapter_label} > {title}" where chapter_label is derived from parent directory name with title-casing
- Title extraction priority: frontmatter title > first `# ` heading > filename stem with dash/underscore-to-space conversion

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 5 new parsers (PDF, BBj Source, Advantage, KB, MDX) are implemented and tested
- Pipeline intelligence bypass works correctly for all parser types
- CLI supports all 6 source types
- Phase 13 is complete; ready for Phase 14 (Documentation)

---
*Phase: 13-additional-parsers*
*Completed: 2026-02-01*
