# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-31)

**Core value:** Engineers can start building the RAG ingestion pipeline with concrete code, schemas, and source-by-source guidance -- bridging Chapter 6's strategic design and actual implementation.
**Current focus:** v1.2 -- Phase 12 in progress (Embedding Pipeline)

## Current Position

Milestone: v1.2 RAG Ingestion Pipeline
Phase: 12 of 14 (Embedding Pipeline)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-02-01 -- Completed 12-01-PLAN.md (Embedding Pipeline Core)

Progress: █████████░░░░░ 9/14 (64%)

## Performance Metrics

**Velocity:**
- Total plans completed: 9 (v1.2)
- Average duration: 5min
- Total execution time: 49min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 08-project-scaffold-readme | 1/1 | 3min | 3min |
| 09-schema-data-models | 2/2 | 8min | 4min |
| 10-flare-parser | 3/3 | 23min | 8min |
| 11-bbj-intelligence | 2/2 | 8min | 4min |
| 12-embedding-pipeline | 1/2 | 7min | 7min |

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
- Simplified _canonicalize to preserve trailing slashes on directory URLs for correct urljoin resolution
- CSS selector lists for chrome stripping rather than hardcoded element removal
- BeautifulSoup with lxml parser for rendered HTML crawl (not lxml.etree which is for XHTML)
- Backslash-to-forward-slash normalization for Windows-authored snippet src attributes on macOS
- 58 unresolvable snippet references are genuine Flare authoring issues -- graceful degradation via warning
- _SnippetMap type alias for dict[str, etree._Element] to reduce function signature verbosity
- Generation StrEnum auto() produces lowercase values: all, character, vpro5, bbj_gui, dwc
- resolve_signals returns ["untagged"] sentinel (not empty list) for below-threshold signals
- Primary.BASISHelp is NOT a generation signal (informational only, 84.6% of files have it)
- Primary.Deprecated/Superseded are lifecycle flags on deprecated boolean field, not generation signals
- Signal weights: path=0.6, condition=0.3-0.5, content=0.4 with 0.3 aggregation threshold
- context_header stored as separate field to avoid content_hash mutation
- Rules without required_headings use min_score=0.15 (not 0.5) to avoid false negatives
- API reference boost +0.2 when Parameters/Return Value present alongside Syntax heading
- url_path_to_hierarchy delegates to web_crawl.url_to_hierarchy (single source of truth)
- vector(1024) matching Qwen3-Embedding-0.6B default output dimensions (changed from 1536)
- Ollama as default embedding provider with OpenAI as configurable fallback
- 400-token target chunk size with 50-token (~12%) overlap for heading-aware chunking
- Context header prepended to chunk content before embedding for richer semantic representation
- Binary COPY via staging table + INSERT ON CONFLICT for idempotent bulk inserts
- _fatal() helper for NoReturn-typed CLI error exits (keeps mypy strict mode clean)

### Pending Todos

None.

### Blockers/Concerns

None open.

## Session Continuity

Last session: 2026-02-01T07:18Z
Stopped at: Completed 12-01-PLAN.md (Embedding Pipeline Core)
Resume file: None
Next action: Execute 12-02-PLAN.md (Search Validation).
