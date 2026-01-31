# Phase 2: Content Architecture & Landing Page - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Landing page with executive summary and audience routing for developers, leadership, and customers. Reusable content patterns (TL;DR blocks, decision callouts, Mermaid diagrams) ready for chapter authoring in Phases 3-4. No chapter content is written in this phase.

</domain>

<decisions>
## Implementation Decisions

### Content pattern styling
- Use Docusaurus built-in admonition system (:::tip, :::note, etc.) with custom CSS — not custom React components
- Keeps patterns simple, maintainable, and consistent with ecosystem

### Tone & voice
- Technical authority voice — confident engineering tone: "here's what we're building and why it's the right approach"
- Problem-first narrative on landing page — lead with "generic LLMs fail on BBj" to establish the gap, then present the strategy as the solution
- Minimal assumed BBj knowledge — explain BBj concepts briefly when introduced, accessible to someone who's never seen BBj
- Transparent implementation status — clearly mark what's implemented, in progress, and planned throughout content

### Claude's Discretion
- TL;DR block visual treatment (prominence, color, placement) — pick what fits the Docusaurus theme
- Decision callout format (structured ADR vs inline highlight) — pick what works best for the mixed audience
- Mermaid diagram types and styling — configure for whatever fits the content
- Landing page layout structure and audience routing mechanism

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

*Phase: 02-content-architecture-landing-page*
*Context gathered: 2026-01-31*
