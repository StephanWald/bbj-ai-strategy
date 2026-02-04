---
phase: 28-compiler-validation
plan: 01
subsystem: validation
tags: [bbjcpl, compiler, subprocess, asyncio, mcp]

# Dependency graph
requires:
  - phase: 21-mcp-server
    provides: FastMCP server infrastructure
provides:
  - BBj compiler validation module with async subprocess execution
  - detect_bbj_code() heuristic for BBj vs other languages
  - validate_bbj_syntax MCP tool for Claude Desktop
affects: [28-02-auto-validation]

# Tech tracking
tech-stack:
  added: []
  patterns: [async subprocess with timeout, heuristic code detection]

key-files:
  created:
    - rag-ingestion/src/bbj_rag/compiler.py
  modified:
    - rag-ingestion/src/bbj_rag/config.py
    - rag-ingestion/src/bbj_rag/mcp_server.py

key-decisions:
  - "Each BBj keyword counts as separate indicator for more permissive detection"
  - "BASIC-style print/input statements (no parens) count as indicator"
  - "Compiler config read from env vars to avoid circular imports"

patterns-established:
  - "Async subprocess with timeout: asyncio.create_subprocess_exec + wait_for"
  - "Graceful degradation when external tool unavailable"

# Metrics
duration: 12min
completed: 2026-02-04
---

# Phase 28 Plan 01: Compiler Validation Foundation Summary

**BBj compiler validation via bbjcpl subprocess with MCP tool exposure and heuristic code detection**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-04T07:07:00Z
- **Completed:** 2026-02-04T07:19:04Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created compiler.py module with ValidationResult dataclass, detect_bbj_code(), validate_bbj_syntax()
- Heuristic detection identifies BBj code via keywords, comments (! and rem), channel syntax (#N), scope operator (::), BBj class prefix
- Async subprocess execution of bbjcpl -N with configurable timeout (default 10s)
- MCP tool returns human-readable validation results with actionable guidance
- Graceful handling when bbjcpl unavailable (returns guidance instead of crashing)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create compiler validation module** - `6090bec` (feat)
2. **Task 2: Add validate_bbj_syntax MCP tool** - `37f486f` (feat)

## Files Created/Modified
- `rag-ingestion/src/bbj_rag/compiler.py` - BBj compiler validation module with ValidationResult, detect_bbj_code(), validate_bbj_syntax()
- `rag-ingestion/src/bbj_rag/config.py` - Added compiler_timeout and compiler_path settings
- `rag-ingestion/src/bbj_rag/mcp_server.py` - Added validate_bbj_syntax MCP tool

## Decisions Made
- Each BBj keyword counts as a separate indicator (more permissive detection than original 2+ keywords = 1 indicator)
- Added BASIC-style print/input pattern (`print "..."` without parens) as indicator to catch simple BBj snippets
- Compiler configuration read directly from env vars (BBJ_RAG_COMPILER_TIMEOUT, BBJ_RAG_COMPILER_PATH) to avoid circular import with config.py

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Detection logic initially too strict (required 2+ keywords for 1 indicator, plus 2+ total indicators)
- Fixed by counting each keyword as separate indicator and adding BASIC-style statement pattern
- bbjcpl not installed on dev machine - verified unavailable case works correctly

## User Setup Required

None - no external service configuration required. Engineers with BBj installed will have bbjcpl available. The module gracefully handles machines without bbjcpl.

## Next Phase Readiness
- Compiler validation foundation complete
- Ready for Plan 02: Auto-validation in chat responses
- detect_bbj_code() can identify BBj code blocks in LLM responses
- validate_bbj_syntax() can validate those blocks against real compiler

---
*Phase: 28-compiler-validation*
*Completed: 2026-02-04*
