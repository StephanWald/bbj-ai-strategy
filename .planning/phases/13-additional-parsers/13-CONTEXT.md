# Phase 13: Additional Parsers - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Plug the remaining five source types into the proven Flare pipeline (parse -> tag -> chunk -> embed -> store): PDF (GuideToGuiProgrammingInBBj.pdf), WordPress/Advantage articles, WordPress/Knowledge Base lessons, Docusaurus MDX (DWC-Course), and BBj source code files (.bbj/.txt). Pipeline architecture is settled from Phase 12 -- this phase adapts it per source format.

</domain>

<decisions>
## Implementation Decisions

### PDF extraction (GuideToGuiProgrammingInBBj.pdf)
- Run generation tagger per section (not uniform bbj_gui tag) -- book covers general BBj concepts alongside GUI-specific content
- Chapter/section structure, code block detection, and image handling at Claude's discretion (pymupdf4llm capabilities drive approach)

### WordPress content access
- Web crawl (httpx + BeautifulSoup, like Flare crawl fallback) for both Advantage and Knowledge Base -- not WordPress REST API
- Ingest ALL Advantage articles, not filtered by topic -- generation tagger classifies downstream
- Knowledge Base lessons extracted flat (standalone documents) -- no course > lesson hierarchy in context headers
- Strip all media (images, videos, downloads) -- text content only

### Docusaurus MDX (DWC-Course)
- Parse local MDX files from DWC-Course repository clone -- no web crawl fallback
- Tag ALL DWC-Course content as `dwc` generation (uniform, no per-file tagger)
- JSX component handling and frontmatter field usage at Claude's discretion

### BBj source code
- Source files come from mixed locations (BBj installation samples + other repos)
- Extract leading comments/header blocks for description context (not just filename)
- Generation tagging by analyzing code: inspect API usage patterns to classify
- Key domain insight: DWC is a superset of GUI -- `bbj_gui` content is ~95% relevant to DWC users, but `dwc`-specific content (CSS, responsive layouts, web-specific APIs) does NOT apply to traditional GUI. Tagger should identify DWC-specific patterns and tag those as `dwc`; general GUI code gets `bbj_gui`

### Claude's Discretion
- PDF: document granularity (chapter vs section), code block detection approach, image/caption handling
- MDX: which JSX components to strip vs keep inner text, which frontmatter fields to map
- Source code: chunking strategy (whole file vs split by logical blocks) based on typical file sizes
- All parsers: error handling, retry logic, progress reporting

</decisions>

<specifics>
## Specific Ideas

- "DWC is just GUI for the web -- about 95% of GUI knowledge is relevant for DWC, but specific DWC knowledge doesn't find a place in GUI"
- DWC adds CSS, responsive layouts on top of core GUI concepts -- the tagger needs to distinguish web-specific additions from core GUI patterns

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 13-additional-parsers*
*Context gathered: 2026-02-01*
