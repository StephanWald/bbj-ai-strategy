# Phase 30: BBjAPI JavaDoc Ingestion - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Parse the structured JSON files from `/Users/beff/bbx/documentation/javadoc/` and ingest into RAG corpus. The JSON's value is the **structural class hierarchy map** — showing what classes exist, what methods they have, and how they relate. The actual documentation content is already in Flare docs; this adds the navigable API structure.

</domain>

<decisions>
## Implementation Decisions

### Chunking Strategy
- **One chunk per class** — each chunk is a "class reference card"
- Chunk contains:
  - Class name and brief description (if available)
  - Parent class / inheritance chain (Claude's discretion on depth)
  - Full list of methods with **complete signatures** (return type, name, parameter types)
  - Link to documentation.basis.cloud for the class
- Methods include their individual doc links for citation
- Overloaded methods: Claude's discretion on grouping vs listing separately

### Metadata Preservation
- **source_type:** `bbj_api`
- **generations:** `bbj_gui,dwc` (BBjAPI is BBj-specific, not character/vpro5)
- **display_url:** Extract from `[Docs](https://...)` links in the JSON
- Package name indexing: Claude's discretion based on existing schema

### Documentation Handling
- Convert HTML in documentation strings to **Markdown** (preserve structure like bold, links)
- **Include classes/methods with empty documentation** — the signature and existence info is still valuable
- Extract `[Docs](https://documentation.basis.cloud/...)` links as display_url for each item

### Source Configuration
- Use `BBJ_HOME` env var pattern (like `BBJ_RAG_COMPILER_PATH` for bbjcpl)
- JavaDoc path derived from BBj installation: `$BBJ_HOME/documentation/javadoc/`
- Single source entry in sources.toml pointing to the directory
- Parser handles all 7 JSON files (proxies, proxies.event, proxies.sysgui, etc.)

### Claude's Discretion
- Inheritance chain depth (direct parent vs full chain)
- Overload grouping strategy
- Package name as separate metadata field vs embedded in content
- Exact Markdown formatting for the class reference card

</decisions>

<specifics>
## Specific Ideas

- The chunk should function as a "class reference card" — when someone asks "what methods does BBjWindow have?", the chunk provides a complete method listing at a glance
- This is complementary to Flare docs, not a replacement — Flare has the detailed explanations, this has the structural overview

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 30-bbjapi-javadoc-ingestion*
*Context gathered: 2026-02-05*
