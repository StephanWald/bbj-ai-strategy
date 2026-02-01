# Phase 17: Chat & Cross-References - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Update Chapters 5, 3, and 6 so they connect to the MCP architecture established in Chapter 2. Readers following any chapter path encounter consistent MCP integration framing. Chapter 5 gets restructured around two independent paths (human chat and MCP). Chapters 3 and 6 get new MCP Integration subsections and cross-references. No new capabilities are added.

</domain>

<decisions>
## Implementation Decisions

### Two-tier chat framing (Chapter 5)
- Chat (human-facing) and MCP (AI-to-AI) are two independent, equally important paths — not a stepping stone relationship
- Chat serves humans on the website, documentation page, and inside the IDE
- MCP is the interface for AI clients talking to BBj AI infrastructure
- Structure: shared foundation first (RAG retrieval, fine-tuned model), then diverge into how each path surfaces it
- Chapter 5 gets restructured around this shared-foundation + divergence framing (not just augmented)
- Chat deployment simplified to one path: embedded on the documentation site — no widget/standalone/hybrid discussion

### Sequence diagram (Chapter 5)
- One unified Mermaid sequence diagram showing both entry points (MCP client and chat UI) converging on the shared backend
- Replaces the existing text-based request flow diagram
- Explicit MCP tool names in the diagram (`search_bbj_knowledge`, `generate_bbj_code`, `validate_bbj_syntax`) — connects directly to Ch2's tool definitions
- All three tools included for a complete picture of the MCP ecosystem

### Cross-reference style (Chapters 3 and 6)
- Both Ch3 and Ch6 get dedicated "MCP Integration" subsections (not just inline mentions)
- Subsections reference Ch2 for full tool schema details — no schema duplication across chapters
- Cross-reference format: Claude's discretion on whether inline links or styled blocks work best for the established chapter style

### Ch6 status update
- Status block only — prose descriptions remain as-is (they describe the design, which is still accurate)
- Pipeline status: "built and tested (v1.2), awaiting deployment against production corpus"
- Status block includes a line about MCP `search_bbj_knowledge` tool as the planned interface for retrieval

### Claude's Discretion
- Mermaid diagram format choice (sequence vs other) for the unified Ch5 diagram
- Cross-reference format (inline links vs styled blocks) — pick what fits established chapter style
- Exact placement of MCP Integration subsections within Ch3 and Ch6
- How much of Ch5's existing content is preserved vs rewritten during restructure

</decisions>

<specifics>
## Specific Ideas

- "MCP is the interface for AI talking to our AI infrastructure" — this framing distinguishes it clearly from the chat path
- Chat is important for human interaction — website, documentation page, IDE
- The pipeline is prepared but not yet exercised against real data — status should reflect "built, not yet deployed"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 17-chat-cross-references*
*Context gathered: 2026-02-01*
