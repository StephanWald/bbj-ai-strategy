# Phase 11: BBj Intelligence - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Automatically classify every parsed document by BBj generation and document type, and prepend contextual headers to chunks derived from source hierarchy. This is the BBj-specific intelligence layer that makes the pipeline valuable beyond generic document ingestion. Does NOT include chunking, embedding, or storage — those are Phase 12.

</domain>

<decisions>
## Implementation Decisions

### Generation tagging rules
- Five canonical generation labels only: `all`, `character`, `vpro5`, `bbj-gui`, `dwc` — no "bbj" catch-all
- Replace existing `["bbj"]` default from Phase 10 with specific labels or flag as untagged
- When no signal matches any generation: flag as untagged (empty/unknown) rather than defaulting
- Multi-signal conflict resolution: Claude's discretion (rank signals or union — pick what produces best tagging)
- Scan code blocks for generation-specific syntax patterns (REM for character, PROCESS_EVENTS for GUI, BBjAPI() patterns, etc.) as a tagging signal
- Multi-generation content (e.g., migration guides): tag with all applicable generations, don't split chunks

### Document type classification
- Seven starting types: `api-reference`, `concept`, `example`, `migration`, `language-reference`, `best-practice`, `version-note`
- Design for extensibility — adding new types shouldn't require rewriting the classifier
- Use both structural signals (headings like "Syntax", "Parameters", "Returns") and content-based signals (regex, keyword density) with equal weight
- Single vs multiple types per chunk: Claude's discretion
- api-reference vs language-reference distinction: Claude's discretion based on actual Flare content patterns

### Contextual header format
- Store as separate field on chunk (chunk.context_header) alongside chunk.content — not baked into content text
- Embed the concatenation for vector search, but keep fields distinct in the DB
- Header verbosity: Claude's discretion (full breadcrumb vs minimal)
- Header separator format: Claude's discretion (arrow breadcrumb vs markdown headings)
- Web crawl fallback headers: combine URL path segments for breadcrumb + page headings for within-page context

### Deprecated/superseded handling
- Tag deprecated content with its original generation normally
- Add a boolean deprecated/superseded flag for filtering — don't exclude deprecated content from ingestion

### Reporting
- Always print a summary report after tagging a batch: counts by generation, by type, flagged/untagged items
- Under 50% tagged "all" is an acceptable distribution — the tagger should resolve most content to specific generations

### Claude's Discretion
- Multi-signal conflict resolution strategy for generation tagging
- Single vs multiple document types per chunk
- api-reference vs language-reference distinction
- Contextual header verbosity and separator format
- Specific syntax patterns to scan in code blocks

</decisions>

<specifics>
## Specific Ideas

- The 5 canonical generations map to BBj's product evolution: character (green-screen), vpro5 (Visual PRO/5), bbj-gui (BBj GUI/Swing), dwc (Dynamic Web Client), all (cross-generation)
- Condition tags from Flare (Primary.BASISHelp, Primary.Deprecated, Primary.Superseded) are already extracted in Phase 10 and available as metadata
- The `["bbj"]` default currently set in Phase 10's condition tag extractor should be replaced by this phase's tagger output
- Quality validation: the tagger should produce a plausible distribution — if >50% is tagged "all", the signals aren't working well enough

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-bbj-intelligence*
*Context gathered: 2026-01-31*
