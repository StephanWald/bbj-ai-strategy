# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-31)

**Core value:** Engineers can start building the RAG ingestion pipeline with concrete code, schemas, and source-by-source guidance -- bridging Chapter 6's strategic design and actual implementation.
**Current focus:** v1.2 -- Phase 10 (Flare Parser)

## Current Position

Milestone: v1.2 RAG Ingestion Pipeline
Phase: 10 of 14 (Flare Parser)
Plan: 1 of 3 in current phase
Status: In progress
Last activity: 2026-01-31 -- Completed 10-01-PLAN.md (Parser Foundations)

Progress: ████░░░░░░░░░░ 4/14 (29%)

## Performance Metrics

**Velocity:**
- Total plans completed: 4 (v1.2)
- Average duration: 5min
- Total execution time: 18min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 08-project-scaffold-readme | 1/1 | 3min | 3min |
| 09-schema-data-models | 2/2 | 8min | 4min |
| 10-flare-parser | 1/3 | 7min | 7min |

*Updated after each plan completion*

## Accumulated Context

### Decisions

See .planning/PROJECT.md Key Decisions table for full log.
Recent decisions affecting current work:

- Python ingestion sub-project as mono-repo directory (keeps scripts co-located with strategy docs)
- Both Flare export and crawl ingestion paths (engineers may or may not have Flare project access)
- Raw Flare XHTML (not Clean XHTML export) -- actual project source at /Users/beff/bbjdocs/ uses MadCap namespace tags
- hatchling build backend (not uv_build) for stable src-layout support
- Pre-commit hooks at repo root scoped to rag-ingestion/ via files filter
- ruff 0.14.x with select rules: E, W, F, I, B, UP, RUF
- str_strip_whitespace=True on Pydantic models to normalize input at boundary
- Chunk.from_content() as canonical factory to ensure hash/content consistency
- Settings field defaults serve as fallbacks when TOML/env absent (useful for tests)
- settings_customise_sources override required for pydantic-settings 2.12 TOML loading
- Two-arg to_tsvector('english', ...) with || operator for IMMUTABLE generated columns
- Standalone SQL DDL file (sql/schema.sql) separated from Python execution (schema.py)
- ON CONFLICT (content_hash) DO NOTHING for idempotent re-ingestion dedup
- register_vector() called on every connection for pgvector type handling
- runtime_checkable on DocumentParser Protocol for isinstance checks
- Frozen dataclass with slots for ConditionTag (immutable, memory-efficient)
- LinkedTitle resolution chain: <title> -> <h1> -> filename stem
- Default to generations=["bbj"] when no conditions or no generation-relevant conditions found

### Pending Todos

None.

### Blockers/Concerns

None open.

## Session Continuity

Last session: 2026-01-31T20:37Z
Stopped at: Completed 10-01-PLAN.md (Parser Foundations)
Resume file: None
Next action: Execute 10-02-PLAN.md (Flare XHTML Parser)
