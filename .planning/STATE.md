# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-31)

**Core value:** Engineers can start building the RAG ingestion pipeline with concrete code, schemas, and source-by-source guidance -- bridging Chapter 6's strategic design and actual implementation.
**Current focus:** v1.2 -- Phase 13 complete (Additional Parsers)

## Current Position

Milestone: v1.2 RAG Ingestion Pipeline
Phase: 13 of 14 (Additional Parsers)
Plan: 3 of 3 in current phase
Status: Phase complete
Last activity: 2026-02-01 -- Completed 13-03-PLAN.md (MDX Parser & Full Integration)

Progress: █████████████░ 13/14 (93%)

## Performance Metrics

**Velocity:**
- Total plans completed: 13 (v1.2)
- Average duration: 5min
- Total execution time: 69min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 08-project-scaffold-readme | 1/1 | 3min | 3min |
| 09-schema-data-models | 2/2 | 8min | 4min |
| 10-flare-parser | 3/3 | 23min | 8min |
| 11-bbj-intelligence | 2/2 | 8min | 4min |
| 12-embedding-pipeline | 2/2 | 12min | 6min |
| 13-additional-parsers | 3/3 | 15min | 5min |

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
- RRF with k=50 constant matching standard academic formula
- search_validation pytest marker separates DB-requiring integration tests from unit tests
- Default pytest addopts excludes search_validation so CI runs without database
- validate CLI delegates to pytest subprocess for full reporting
- Reuse _html_to_markdown from web_crawl module for WordPress parsers (no reimplementation)
- Separate WordPress chrome selectors from Flare chrome selectors (different boilerplate patterns)
- Strip all media tags (img, video, audio, iframe, figure, svg) for text-only WordPress content
- Advantage doc_type="article", KB doc_type="concept"
- Sitemap XML fallback when index page HTML parsing finds zero links
- Per-section generation tagging for PDF parser (content-based regex, not uniform)
- DWC patterns checked before GUI patterns in source code classification
- BBj keyword validation to skip non-BBj .txt files in source directories
- PDF page 0 (TOC) skipped; doc_type: concept/example/tutorial based on content
- Source URL format: pdf://filename#slug for PDF, file://relative-path for BBj source
- Pipeline intelligence bypass: doc_type non-empty and != "web_crawl" skips _apply_intelligence
- DWC-Course uniform tagging: all content gets generations=["dwc"] and doc_type="tutorial"
- MDX context header: "DWC Course > {chapter} > {title}" with chapter from parent dir name
- MDX title priority: frontmatter > first # heading > filename stem

### Pending Todos

None.

### Blockers/Concerns

None open.

## Session Continuity

Last session: 2026-02-01T08:32Z
Stopped at: Completed 13-03-PLAN.md (MDX Parser & Full Integration)
Resume file: None
Next action: Phase 14 (Documentation) -- final phase of v1.2 milestone.
