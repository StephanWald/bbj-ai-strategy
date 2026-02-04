---
phase: 29-ingestion-performance
plan: 03
subsystem: cli
tags: [parallel, cli, asyncio, ingestion, performance]

# Dependency graph
requires:
  - phase: 29-02
    provides: ParallelIngestor class with asyncio worker pool
provides:
  - CLI integration with --sequential, --workers, --retry-failed flags
  - Parallel ingestion as default mode
  - Failure recovery via retry-failed
affects: [corpus rebuilds, developer workflow]

# Tech tracking
tech-stack:
  added: []
  patterns: [async CLI integration, mode-based branching]

key-files:
  created: []
  modified:
    - rag-ingestion/src/bbj_rag/ingest_all.py
    - rag-ingestion/src/bbj_rag/config.py

key-decisions:
  - "Parallel mode is default, --sequential for fallback"
  - "--workers N capped at max_workers (8) with warning"
  - "OLLAMA_HOST env var takes priority over default for Docker compatibility"
  - "Exit code 1 for partial failures"

patterns-established:
  - "Mode column in summary table for visibility"
  - "Collect-then-embed pattern for parallel ingestion"

# Metrics
duration: 12min
completed: 2026-02-04
---

# Phase 29 Plan 03: CLI Integration Summary

**Parallel ingestion CLI integration with --sequential fallback and --retry-failed recovery**

## Performance

- **Duration:** 12 min (including checkpoint verification)
- **Started:** 2026-02-04T14:48:00Z
- **Completed:** 2026-02-04T17:00:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Parallel ingestion is now the default mode (no flag needed)
- `--sequential` flag falls back to original run_pipeline flow
- `--workers N` controls concurrency (default 4, capped at 8)
- `--retry-failed` processes only items from failure log
- Summary table shows mode column ("sequential" or "parallel (Nw)")
- Exit code 1 for partial failures with hint to use --retry-failed
- Fixed OLLAMA_HOST env var fallback for Docker compatibility

## Task Commits

1. **Task 1: Update CLI flags for parallel mode** - `e5950de` (feat)
2. **Task 2: Implement parallel ingestion flow** - `e5950de` (feat)
3. **Task 3: Human verification checkpoint** - `1dc60fb` (fix) - OLLAMA_HOST fix discovered during verification

## Files Created/Modified

- `rag-ingestion/src/bbj_rag/ingest_all.py` - Removed --parallel, added --sequential/--workers/--retry-failed, integrated ParallelIngestor
- `rag-ingestion/src/bbj_rag/config.py` - Fixed ollama_host validator to properly check OLLAMA_HOST env var fallback

## Decisions Made

- **Parallel as default** - Most users benefit from parallel; sequential is fallback for debugging
- **Worker cap with warning** - Prevents GPU saturation from misconfiguration
- **OLLAMA_HOST priority fix** - Docker sets OLLAMA_HOST=host.docker.internal, must take priority over field default

## Deviations from Plan

- **OLLAMA_HOST fix required** - During Docker verification, discovered async embedder wasn't using OLLAMA_HOST env var. The validator was returning the default value before checking env vars. Fixed to prioritize: BBJ_RAG_OLLAMA_HOST > OLLAMA_HOST > default

## Issues Encountered

- Parallel mode failed in Docker due to OLLAMA_HOST not being picked up
- Root cause: field_validator checked `if v:` which was True for default value
- Fix: Check `if v and v != default` before falling back to env var

## Verification Results

- Sequential mode: 4.5s for 48 chunks (PDF source)
- Parallel mode: 4.5s for 48 chunks (PDF source)
- No speedup observed because 48 chunks fit in 1 batch (batch_size=64)
- Parallel benefit requires multiple batches (larger corpus)
- Both modes complete successfully with correct output

## User Setup Required

None - Docker environment variables already configured correctly.

## Phase 29 Success Criteria Status

1. ✅ `bbj-ingest-all` runs in parallel mode by default
2. ✅ `--sequential` mode falls back to original flow
3. ✅ Multiple workers process without errors
4. ✅ HTTP connections reused via httpx.AsyncClient (from 29-01)
5. ⚠️ Performance improvement requires larger corpus (>64 chunks)

---
*Phase: 29-ingestion-performance*
*Completed: 2026-02-04*
