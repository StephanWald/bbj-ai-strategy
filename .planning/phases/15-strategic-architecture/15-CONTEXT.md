# Phase 15: Strategic Architecture - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Update Chapter 2 so readers understand how the MCP server concretely realizes the unified architecture — three tools, their schemas, and the generate-validate-fix loop. This is a documentation update to an existing chapter, not new software.

</domain>

<decisions>
## Implementation Decisions

### Content depth & tone
- Authoritative, professional peer voice — not academic, not sales-y
- Enough background on MCP to orient readers, then jump to the essentials for BBj language support
- Everything frames back to why this architecture serves BBj developers
- Developer-primary audience — leadership and customers get enough context from the narrative, but this is a technical chapter

### Schema presentation
- Summarized schemas in Chapter 2 (key fields, descriptions, compact format)
- Full specification will live in a future MCP server sub-project (same pattern as RAG ingestion pipeline)
- Schemas should be concrete enough that a developer understands the three tools' purpose and interface shape

### Diagram approach
- Match whatever diagram approach Chapter 2 already uses (research existing pattern)
- Two diagrams needed: MCP topology (Host/Client/Server/backends) and generate-validate-fix sequence

### Chapter integration
- Claude's discretion on whether to add a new section or expand existing sections
- Goal: reads as one cohesive narrative, not a bolted-on addendum

### TL;DR block
- Match existing TL;DR pattern used elsewhere in the chapter/site (research what pattern is established)
- Must convey: MCP server, three tools, generate-validate-fix loop — skimmable in 30 seconds

### Decision callout framing
- "MCP as the Unified Integration Protocol" — balanced comparison
- Give alternatives (REST API, custom plugin, etc.) fair treatment, then explain why MCP fits best for BBj
- Frame as evolution, not replacement — MCP builds on the existing unified architecture concept

### Claude's Discretion
- How to integrate MCP content into existing Chapter 2 structure (new section vs expanding existing)
- TL;DR framing approach (match existing patterns once researched)
- Exact layout and flow of schema summaries
- Annotation level on diagrams

</decisions>

<specifics>
## Specific Ideas

- Similar sub-project pattern as RAG ingestion for future MCP server implementation — summarized schemas now, full spec later
- Consistency with existing site patterns is paramount — research established conventions for TL;DR blocks, diagrams, decision callouts before writing new content
- The ultimate goal framing: everything connects back to BBj language support

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 15-strategic-architecture*
*Context gathered: 2026-02-01*
