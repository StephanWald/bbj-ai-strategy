---
phase: 21-data-configuration-ingestion
plan: 01
subsystem: infra
tags: [toml, pydantic, config, mdx-parser, source-config, report]

# Dependency graph
requires:
  - phase: 12-rag-ingestion
    provides: "All 6 parsers (flare, pdf, mdx, bbj-source, wordpress, web-crawl), pipeline.py, report.py"
provides:
  - "sources.toml config file defining all 9 source entries"
  - "source_config.py Pydantic loader/validator with DATA_DIR env resolution"
  - "MdxParser source_prefix parameter for multi-directory support"
  - "Fixed report.py SQL CASE patterns matching real source_url prefixes"
  - "get_source_url_prefix() helper for clean/delete operations"
affects: [21-02-PLAN, orchestration-script, ingestion-cli]

# Tech tracking
tech-stack:
  added: [tomllib]
  patterns: [TOML-array-of-tables-config, env-var-path-override, per-instance-parser-prefix]

key-files:
  created:
    - "rag-ingestion/sources.toml"
    - "rag-ingestion/src/bbj_rag/source_config.py"
  modified:
    - "rag-ingestion/src/bbj_rag/parsers/mdx.py"
    - "rag-ingestion/src/bbj_rag/intelligence/report.py"
    - "rag-ingestion/.gitignore"
    - "rag-ingestion/tests/test_mdx_parser.py"
    - "rag-ingestion/tests/test_report.py"

key-decisions:
  - "sources.toml data_dir intentionally blank for portability; resolved via DATA_DIR env var at runtime"
  - "Each MDX tutorial directory is a separate [[sources]] entry (not one entry with multiple paths) for independent enable/disable and resume tracking"
  - "MdxParser source_prefix defaults to 'dwc-course' for backward compat with existing CLI"
  - "Context header label derived dynamically from source_prefix via .title() (Dwc Course, Mdx Beginner, etc.)"

patterns-established:
  - "TOML [[sources]] array-of-tables for multi-source config with per-entry parser type, paths, generation_tag, enabled flag"
  - "DATA_DIR env var override for Docker vs host path portability"
  - "source_prefix parameter on parsers for unique source_url namespaces across multiple instances"

# Metrics
duration: 6min
completed: 2026-02-01
---

# Phase 21 Plan 01: Source Configuration Summary

**TOML-based source config with 9 entries across 7 parser types, MdxParser multi-directory prefix support, and fixed report SQL pattern matching**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-01T22:10:27Z
- **Completed:** 2026-02-01T22:16:07Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Created sources.toml defining all 9 BBj documentation source entries with portable data_dir, parser types, generation tags, and enabled flags
- Created source_config.py with Pydantic validation, tomllib loader, DATA_DIR env resolution, path validation, and source_url prefix helper
- Added source_prefix parameter to MdxParser enabling unique source_url namespaces per tutorial directory (mdx-dwc://, mdx-beginner://, mdx-db-modernization://)
- Fixed report.py SQL CASE expression to match real source_url prefixes (was using non-existent mdx://) and added web-crawl source detection

## Task Commits

Each task was committed atomically:

1. **Task 1: Create sources.toml and source_config.py** - `2fa4035` (feat)
2. **Task 2: Update MdxParser for multi-directory source_prefix support** - `30f82c3` (feat)
3. **Task 3: Fix report.py source_url SQL patterns for MDX and add web_crawl** - `e4fa5ab` (fix)

## Files Created/Modified
- `rag-ingestion/sources.toml` - TOML config with 9 source entries, portable data_dir, comments explaining override mechanism
- `rag-ingestion/src/bbj_rag/source_config.py` - SourceEntry/SourcesConfig Pydantic models, load_sources_config, resolve_data_dir, validate_sources, get_source_url_prefix
- `rag-ingestion/src/bbj_rag/parsers/mdx.py` - Added source_prefix parameter (default "dwc-course"), _prefix_label property, dynamic source_url/context_header/metadata
- `rag-ingestion/src/bbj_rag/intelligence/report.py` - Fixed SQL CASE patterns: dwc-course://, mdx-%%://, documentation.basis.cloud; added web-crawl to expected_sources
- `rag-ingestion/.gitignore` - Added .ingestion-state.json for resume tracking
- `rag-ingestion/tests/test_mdx_parser.py` - Updated context_header assertion for dynamic label, added test_mdx_parser_custom_prefix
- `rag-ingestion/tests/test_report.py` - Updated expected source count from 5 to 6, added web-crawl to clean_data test

## Decisions Made
- sources.toml ships with blank data_dir for portability -- runtime resolution via DATA_DIR env var prevents machine-specific paths in version control
- Each MDX tutorial directory gets its own [[sources]] entry rather than a single entry with multiple paths, enabling independent enable/disable and per-source resume tracking
- MdxParser defaults to "dwc-course" source_prefix for backward compatibility with existing `bbj-rag ingest --source mdx` CLI command
- Context header labels derived via .title() from prefix (e.g., "Dwc Course" instead of hardcoded "DWC Course") -- acceptable tradeoff for generalization

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated context_header test assertion for dynamic label**
- **Found during:** Task 2 (MdxParser source_prefix)
- **Issue:** Test asserted hardcoded "DWC Course" in context_header, but the dynamic label from "dwc-course".title() produces "Dwc Course"
- **Fix:** Updated test assertion from "DWC Course" to "Dwc Course" to match new dynamic behavior
- **Files modified:** rag-ingestion/tests/test_mdx_parser.py
- **Verification:** All 14 MDX tests pass
- **Committed in:** 30f82c3 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary update for context_header generalization. No scope creep.

## Issues Encountered
- Flare source (bbjdocs directory) not present on host filesystem -- validation correctly reports this as an error. Not a blocker since the path will be valid when the Flare export is available.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- sources.toml and source_config.py are ready for the orchestration script (Plan 21-02) to consume
- Plan 21-02 will create the ingest_all.py CLI that reads sources.toml, instantiates parsers, and runs the pipeline across all enabled sources
- All parsers produce unique source_url prefixes, enabling per-source --clean deletion

---
*Phase: 21-data-configuration-ingestion*
*Completed: 2026-02-01*
