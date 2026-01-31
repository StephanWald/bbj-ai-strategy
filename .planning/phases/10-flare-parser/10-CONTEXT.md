# Phase 10: Flare Parser - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Parse MadCap Flare XHTML documentation into structured Document objects. Two paths: (1) local project file parser reading raw XHTML from Content/ with TOC hierarchy from .fltoc files and condition tag extraction, and (2) web crawl fallback parsing documentation.basis.cloud when project files are unavailable. Output is Document/Chunk objects matching the Phase 9 Pydantic models.

</domain>

<decisions>
## Implementation Decisions

### XHTML Parsing Rules
- MadCap namespace tags: Claude's discretion per tag type — strip wrappers and keep inner content where useful, drop purely structural noise tags
- Code blocks: Preserve as distinct code blocks — detect `<pre>`, `<code>`, and Flare code snippet patterns, mark as code with language hint if identifiable
- Tables: Convert HTML tables to markdown table format (important for API reference parameter/return value tables)
- Cross-references (MadCap:xref, href to other .htm topics): Claude's discretion — determine what's practical based on actual file structure

### TOC Hierarchy Mapping
- TOC file strategy: Claude's discretion — examine actual .fltoc files in the project and determine whether to combine or use primary
- Orphan topics (in Content/ but not in any TOC): Include them — derive section path from file directory structure (e.g., Content/BBj_Objects/Window/ → "BBj Objects > Window")
- Path separator: Arrow format ("BBj Objects > BBjWindow > Methods")
- Depth limit: No limit — use full hierarchy depth however deep it goes

### Condition Tag Extraction
- Which tags to extract: Claude's discretion — examine .flprj and condition tag sets to determine which are generation-relevant vs cosmetic
- Granularity: Both topic-level AND inline conditions — inline conditions on paragraphs/spans matter for chunk-level generation tagging in Phase 11
- Topics with no conditions: Claude's discretion on safe default for downstream tagging
- Condition expressions (Boolean combinations): Claude's discretion — determine based on whether expressions actually appear in the project

### Crawl Fallback Behavior
- Crawl method: HTTP requests + BeautifulSoup (not Crawl4AI) — lightweight, site likely doesn't need JS rendering
- Hierarchy reconstruction: Best effort from URL structure — derive paths from URL patterns (e.g., /bbj/objects/window/ → "BBj > Objects > Window")
- Crawl scope: Full site crawl of documentation.basis.cloud — crawl all pages
- Missing condition metadata on crawled content: Claude's discretion — determine what's practical for maintaining useful metadata without project-file conditions

### Claude's Discretion
- Per-tag-type handling of MadCap namespace elements (which to strip vs drop)
- Cross-reference link resolution strategy
- TOC file combination strategy
- Which condition tags are generation-relevant vs cosmetic
- Default handling for unconditioned topics
- Condition expression capture (raw vs flat list)
- Crawled content condition metadata approach

</decisions>

<specifics>
## Specific Ideas

- The raw Flare XHTML source is at /Users/beff/bbjdocs/ — uses MadCap namespace tags (not Clean XHTML export)
- Code block preservation matters because the docs are heavily code-example-driven (BBj syntax, Java interop)
- Markdown tables keep the structure of API parameter docs intact for RAG retrieval
- Full crawl of documentation.basis.cloud gives complete coverage when someone doesn't have the Flare project
- Arrow separator for hierarchy paths matches what was envisioned in the roadmap success criteria

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-flare-parser*
*Context gathered: 2026-01-31*
