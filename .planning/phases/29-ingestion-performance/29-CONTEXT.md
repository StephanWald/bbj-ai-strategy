# Phase 29: Ingestion Performance - Context

**Gathered:** 2026-02-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Optimize corpus rebuild speed through concurrent processing. Add parallel workers for ingestion and persistent HTTP connections to Ollama. Sequential mode remains available as fallback.

</domain>

<decisions>
## Implementation Decisions

### Worker Behavior
- Fixed default of 4 workers (not auto-detected)
- Work distribution and GPU contention handling at Claude's discretion
- Workers use persistent HTTP connections to Ollama (reuse across batches)

### Progress Output
- Default verbosity at Claude's discretion
- `-v/--verbose` flag for detailed per-worker, per-batch output
- Completion report format at Claude's discretion

### Failure Handling
- Workers retry failed batches 3 times before giving up
- Other workers continue if one fails
- Successfully ingested chunks remain in DB (no rollback on partial failure)
- Failed items logged to file for re-run
- `--retry-failed` flag to re-process only items from failure log
- Exit code non-zero if any batches failed (partial failure = exit 1)
- Failure threshold and service outage handling at Claude's discretion

### Configuration
- Parallel mode is the default (use `--sequential` to disable)
- `--workers N` flag to override default worker count
- Environment variables supported (BBJ_INGEST_WORKERS, etc.)
- Worker count capped automatically if set higher than sensible maximum

### Claude's Discretion
- Work distribution strategy (by source type vs chunk batches)
- GPU contention handling approach
- Default output verbosity level
- Completion report format (summary, comparison, or both)
- Failure threshold (if any)
- Service outage behavior (wait and retry vs fail immediately)
- CI/scripting output considerations
- Maximum worker cap logic

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 29-ingestion-performance*
*Context gathered: 2026-02-04*
