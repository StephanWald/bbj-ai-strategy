# Phase 21: Data Configuration + Ingestion - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

All 6 BBj documentation sources are configured with real data paths and successfully ingested into pgvector, producing a searchable corpus. Sources: Flare, PDF, MDX (multiple tutorial dirs), BBj source, WordPress, web crawl. The ingestion script runs inside or outside Docker against the running pgvector container from Phase 20.

</domain>

<decisions>
## Implementation Decisions

### Source configuration
- External TOML/YAML config file defining all 6 sources (not hardcoded in Python)
- Each source entry includes: parser type, relative path(s), generation tag, enabled flag
- Paths are relative to a DATA_DIR base directory (set via env var or config key) — portable across machines
- Per-source `enabled: true/false` toggle to include/exclude sources from ingestion runs

### Multi-MDX handling
- Claude's discretion on whether MDX is one entry with multiple paths or separate entries — pick what fits the parser

### Ingestion orchestration
- Standalone CLI script (not a FastAPI management command) — can run inside or outside Docker
- Default to sequential or parallel is Claude's discretion, but expose a flag to choose
- Fail-fast pre-validation: validate all source paths and config before starting any ingestion
- Default to upsert (idempotent), with a `--clean` flag to wipe and re-ingest a source

### Progress & output
- Verbosity level is Claude's discretion (likely per-source summary by default, per-file with `--verbose`)
- Final summary table after all sources complete: source name, files processed, chunks created, duration
- Generation tags shown in output gated by verbosity flag
- Stdout only — no log file

### Resumability & failure
- Resume mechanism is Claude's discretion (database marker or local state file)
- If a source fails, continue ingesting remaining sources — report all failures at end
- Partial data from failed sources is kept in the database (not rolled back)
- No dry-run flag — fail-fast validation at startup is sufficient

### Claude's Discretion
- Multi-MDX structure (one entry vs separate entries)
- Sequential vs parallel default (must expose flag either way)
- Verbosity levels and exact output format
- Resume tracking mechanism (database vs local file)
- Config file format choice between TOML and YAML

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

*Phase: 21-data-configuration-ingestion*
*Context gathered: 2026-02-01*
