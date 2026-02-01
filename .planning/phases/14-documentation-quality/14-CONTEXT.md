# Phase 14: Documentation & Quality - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce written documentation (Getting Started sub-page, rag-ingestion README) and a post-ingestion quality report so engineers can understand, set up, run, and validate the pipeline. No new pipeline code or parser work — this phase is about documenting what's already built and making ingestion quality measurable.

</domain>

<decisions>
## Implementation Decisions

### Getting Started page
- Design-first structure: start with "why" (source-by-source approach, generation tagging, chunking strategy rationale), then transition to "how" (practical steps)
- Lives as a dedicated sub-page under Chapter 6 in the docs site (not inline in Chapter 6)
- Include a pipeline flow diagram (parse → tag → chunk → embed → store) showing how sources feed through stages
- Show short inline code snippets for key concepts (data models, parser examples) alongside GitHub links to full files
- GitHub URLs constructed from git remote origin

### README audience & depth
- Audience: readable by outsiders, optimized for internal BASIS engineers
- Full setup guide for all prerequisites (PostgreSQL/pgvector, Ollama model pull, Python/uv) — step-by-step, assumes minimal prior setup
- Full configuration reference: table of all TOML settings, env vars, types, defaults, and descriptions
- Full CLI command reference: every command with flags, usage examples, and expected output
- Cross-links to docs site (Getting Started page, Chapter 6) for design rationale

### Quality report
- CLI output only — no file generated
- Available both as standalone command (`report`) AND auto-printed after every ingestion run
- Include automated warnings that flag anomalies (empty sources, unbalanced distributions, unknown doc types, suspiciously low counts)

### Code linking strategy
- GitHub URLs derived from git remote
- Bidirectional cross-linking: Getting Started → code files, README → docs site

### Claude's Discretion
- Report granularity (three-way breakdown vs cross-tabs) — pick what's most useful for quality validation
- GitHub URL format (branch-based vs tag-based) — pick based on project release cadence
- File-level vs function-level deep links — pick per reference based on what helps the reader most
- Pipeline diagram format (Mermaid, ASCII, or image)
- README section ordering and structure

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

*Phase: 14-documentation-quality*
*Context gathered: 2026-02-01*
