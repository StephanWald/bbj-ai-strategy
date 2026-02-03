# Phase 25: Result Quality Foundation - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Search results link to real documentation and surface all source types, not just Flare. This phase adds clickable display URLs to every search result and implements source-balanced ranking so minority sources (PDF, BBj Source, MDX) appear alongside dominant Flare results when relevant. No new UI, no chat — this is API/MCP response enrichment and ranking logic.

</domain>

<decisions>
## Implementation Decisions

### URL Mapping Strategy
- Pattern-based rules per source type (regex/pattern transforms internal paths to public URLs)
- Mapping computed at ingestion time and stored in the chunks table alongside source_url
- Flare sources map directly to `https://documentation.basis.cloud/` — reference example: `https://documentation.basis.cloud/BASISHelp/WebHelp/bbjobjects/bbjapi/bbjapi.htm`
- When a source has no mappable public URL, echo the source_url as-is but mark it with brackets (e.g., `[path/to/file.bbj]`) so consumers can distinguish resolved vs unresolved URLs
- Every source type gets a display_url — bracketed fallback for unmappable sources, never null

### Result Display Format
- Both `display_url` and `source_type` fields included in every result
- `source_type` is always present regardless of whether display_url resolved to a real URL
- Source type is an explicit field (e.g., 'flare', 'pdf', 'bbj_source', 'mdx') — no human-readable label, type is enough
- Response metadata includes source type breakdown (count per source type in result set)
- Both REST API and MCP tool (`search_bbj_knowledge`) return display_url and source_type

### Source Type Coverage
- Flare: direct path mapping to `documentation.basis.cloud` (confirmed)
- PDF: researcher should determine if page-level deep-linking is feasible from chunk metadata
- BBj Source: researcher should investigate whether these are hosted anywhere publicly (Git repo, web viewer)
- MDX: researcher should check what URLs the deployed docs site uses and whether they're reachable
- All source types get display_url — bracketed fallback for any that can't resolve to public URLs

### Balanced Ranking Behavior
- Boost minority sources but don't guarantee inclusion — if raw scores are too low, don't force them in
- Researcher should identify test queries where non-Flare content exists but currently doesn't surface
- No specific test queries provided — researcher to identify validation cases from corpus analysis

### Claude's Discretion
- API field structure (top-level vs nested) — pick based on existing API patterns
- Score transparency (raw vs adjusted) — pick the cleaner approach
- Boost factor configurability vs hardcoded — pick based on engineering tradeoffs
- Balancing trigger logic (all queries vs dominated-only) — pick the triggering approach
- PDF deep-linking approach — pick based on available chunk metadata

</decisions>

<specifics>
## Specific Ideas

- Flare URL reference: `https://documentation.basis.cloud/BASISHelp/WebHelp/bbjobjects/bbjapi/bbjapi.htm` — use this to derive the pattern rule
- Bracketed fallback convention for unmappable URLs (e.g., `[path/to/local/file.bbj]`) signals "not clickable" to consumers
- Source breakdown in response metadata helps developers verify balancing is working

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 25-result-quality-foundation*
*Context gathered: 2026-02-03*
