---
phase: 28-compiler-validation
plan: 02
subsystem: validation
tags: [bbjcpl, compiler, chat, sse, anthropic]

# Dependency graph
requires:
  - phase: 28-01
    provides: BBj compiler validation module with detect_bbj_code() and validate_bbj_syntax()
  - phase: 26
    provides: Chat streaming infrastructure with SSE events
provides:
  - BBj code block extraction from chat responses
  - Automatic validation of BBj code before display
  - Auto-fix loop with Claude for invalid code (up to 3 attempts)
  - validation_warning SSE events for unfixable code
affects: [frontend-chat-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: [batch-then-simulate-stream, code-block-extraction]

key-files:
  created:
    - rag-ingestion/src/bbj_rag/chat/validation.py
  modified:
    - rag-ingestion/src/bbj_rag/chat/stream.py
    - rag-ingestion/src/bbj_rag/chat/__init__.py

key-decisions:
  - "Batch response + simulated streaming for validation (validates before user sees code)"
  - "Max 3 total attempts per code block (initial + 2 fix attempts)"
  - "Graceful degradation when bbjcpl unavailable (skip validation, no warning)"
  - "validation_warning event includes code_index, errors, code_preview"

patterns-established:
  - "Code block extraction: regex with start/end positions for replacement"
  - "Simulated streaming: chunk at word boundaries with small delays for UX"

# Metrics
duration: 4min
completed: 2026-02-04
---

# Phase 28 Plan 02: Auto-Validation in Chat Summary

**BBj code validation in chat responses with automatic fix attempts via Claude and validation_warning SSE events**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-04T07:22:16Z
- **Completed:** 2026-02-04T07:26:31Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created validation.py module with CodeBlock dataclass and code block extraction
- Integrated validation loop into chat streaming with up to 3 fix attempts
- Added validation_warning SSE event type for unfixable code blocks
- Implemented simulated streaming after validation for UX consistency
- Graceful handling of bbjcpl unavailable/timeout scenarios

## Task Commits

Each task was committed atomically:

1. **Task 1: Create chat validation module** - `74ae4c0` (feat)
2. **Task 2: Integrate validation loop into chat streaming** - `cafd8c4` (feat)

## Files Created/Modified
- `rag-ingestion/src/bbj_rag/chat/validation.py` - Code block extraction, validation wrapper, fix prompt builder, block replacement
- `rag-ingestion/src/bbj_rag/chat/stream.py` - Batch response with validation loop, simulated streaming, validation_warning events
- `rag-ingestion/src/bbj_rag/chat/__init__.py` - Exports for validation module functions

## Decisions Made
- Switched from real-time streaming to batch + simulated streaming to enable pre-display validation
- Fix prompt is minimal ("return ONLY the corrected code") to avoid markdown wrapping in responses
- Strip markdown fences from Claude's fix responses in case it ignores instructions
- Chunk splitting prefers word boundaries for natural streaming appearance

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-commit ruff formatter modified dict formatting to multi-line style - auto-fixed by re-staging

## User Setup Required

None - no external service configuration required. Engineers with BBj installed will have bbjcpl available for validation. The module gracefully handles machines without bbjcpl (validation skipped, no warning).

## Next Phase Readiness
- Compiler validation integration complete
- Chat responses now validate BBj code before display
- Phase 28 (Compiler Validation) is complete
- Ready for Phase 29 (Performance Optimization)

---
*Phase: 28-compiler-validation*
*Completed: 2026-02-04*
