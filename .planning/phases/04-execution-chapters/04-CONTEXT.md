# Phase 4: Execution Chapters - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Write Chapters 4-7 (IDE Integration, Documentation Chat, RAG Database Design, Implementation Roadmap) with same research depth as foundation chapters, plus a cross-cutting quality pass across all 7 chapters. Each chapter provides execution-level guidance — specific enough that a developer or technical lead can act on it.

</domain>

<decisions>
## Implementation Decisions

### Chapter depth & prescriptiveness
- All execution chapters match Chapter 3's depth level — specific tools, configurations, and architectural details
- Architecture-first approach: describe requirements and design, then reference current tools as examples (not hard recommendations) — acknowledges fast-moving LLM ecosystem
- Each chapter includes a "Current Status" section — honest about what's built, in progress, and planned
- Vision-forward framing: lead with the strategic architecture, reference existing work as the foundation it builds on

### Chapter 4: IDE Integration framing
- Vision-forward: lead with the AI-powered IDE vision, position the existing language server as the foundation
- Two paths documented equally: (1) custom LLM client in extension/language server (strategic path), (2) Copilot integration (interim bridge)
- Must manage reader expectations around Copilot — readers will assume "just use Copilot" works. Explain why it doesn't for BBj, then present both paths
- The bbj-language-server repo (BBx-Kitchen/bbj-language-server) is real and published on VS Code Marketplace — document from the actual codebase for "what exists," use general Langium/LSP patterns for "what's next"
- Current status: language server shipped, fine-tuned model showing promising results with ~10K data points, Copilot integration in early exploration

### Chapter 5: Documentation Chat framing
- Vision still forming — document the architectural requirements and design principles without committing to a specific deployment model
- Present as generation-aware chat that leverages the shared fine-tuned model + RAG infrastructure
- Current status: vision defined, not yet built

### Chapter 6: RAG Database framing
- Comprehensive corpus scope: MadCap Flare documentation + source code + API references + knowledge base + optionally discussion forums
- Cover industry RAG best practices (chunking, embeddings, vector DBs) then apply to BBj's unique requirements (generation tagging, multi-source ingestion, MadCap Flare as primary doc source)
- Current status: source corpus identified, pipeline not built

### Chapter 7: Implementation Roadmap framing
- Primary audience: technical leads and project managers (not C-level budget approvers)
- Single recommended plan with explicit cut points — mark where you could stop and still have value (MVP checkpoints)
- Hardware/infrastructure costs only — no staffing estimates (varies too much by organization)
- Formal risk assessment section — identified risks, likelihood, impact, mitigation strategies

### Research sourcing strategy
- Original strategy paper is a starting point, not gospel — chapters diverge where current best practices suggest a different approach
- Research the actual bbj-language-server repo for Chapter 4 (real architecture + AI integration vision)
- Chapter 6 research covers both industry RAG state-of-the-art and BBj-specific concerns
- All chapters reference 2025/2026 best practices, not just the paper's original recommendations

### Cross-chapter quality pass (04-05)
- Add "Current Status" sections to ALL 7 chapters (retrofit Chapters 1-3)
- Full refresh of Chapter 3's outdated sections — update from "schema defined, no curated examples" to reflect ~10K data points, promising results, ongoing fine-tuning work
- Full cross-reference audit — every chapter links forward and backward where relevant, consistent navigation between related topics
- Enforce content patterns (TL;DR, decision callouts, Mermaid diagrams) across all 7 chapters — add any missing ones
- Verify all chapters reflect current reality, not just the original paper's state

### Claude's Discretion
- Chapter 5 deployment model (embedded in docs, standalone, or hybrid) — vision is still forming
- Mermaid diagram placement and content per chapter
- Exact structure of Current Status sections (callout box, dedicated section, etc.)
- How to present the Copilot bridge vs. custom client trade-offs visually

</decisions>

<specifics>
## Specific Ideas

- "Readers will come expecting they can use Copilot out of the box — we need to manage that expectation"
- The bbj-language-server is a Langium-based VS Code extension with language server, published on Marketplace: https://github.com/BBx-Kitchen/bbj-language-server
- An engineer is actively fine-tuning the model — ~10K data points, promising results, recognized there's more work needed
- That same engineer has started verifying fine-tuned model integration with Copilot — early but cautiously optimistic
- Documentation curated in MadCap Flare — relevant for RAG ingestion pipeline design
- Custom LLM client (in extension or language server) is the long-term strategic path; Copilot is a bridging step

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-execution-chapters*
*Context gathered: 2026-01-31*
