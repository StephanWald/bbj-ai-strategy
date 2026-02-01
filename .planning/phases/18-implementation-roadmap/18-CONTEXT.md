# Phase 18: Implementation Roadmap - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Update Chapter 7 (Implementation Roadmap) to reflect v1.2 accomplishments, weave MCP server deliverables into existing implementation phases, and add compiler validation as hallucination mitigation in the risk assessment. The chapter presents a proposed architecture — the engineering team still needs to digest and validate.

</domain>

<decisions>
## Implementation Decisions

### Status table updates
- Add new rows for MCP Server and Compiler Validation (7 rows total, up from 5)
- Update date column from "Actual (Jan 2026)" to "Actual (Feb 2026)" to reflect current state
- Nothing is truly shipped/deployed — be honest about the gap between designed and running
- RAG pipeline: built but not live
- Fine-tuned LLM: in progress, not complete
- Training data: 10k collected, estimated 50-80k total needed
- MCP Server: design only, no implementation exists yet
- Compiler validation (bbjcpl): proof-of-concept validated the concept, not deployed

### MCP weaving into phases
- MCP deliverables appear as bullets within each relevant existing phase — not as a cross-cutting section
- Phase names: Claude's discretion on whether to update or keep as-is
- MCP deliverables fold into existing MVP checkpoints — no separate MCP gates
- Documentation chat: add MCP bullet noting delivery mechanism, don't reframe the section around MCP

### Risk assessment additions
- Compiler validation as hallucination mitigation: Claude decides whether to update an existing risk row or add a new one (whichever fits better)
- Tone: "designed, not deployed" — honest about the gap between proof-of-concept and production
- No MCP-specific risk row — MCP is an implementation choice, not a project risk
- Training data sufficiency: update the existing risk to reflect 10k/50-80k reality

### Current status / accomplishments
- Frame progress as "architecture proposed" — engineering team needs to digest and validate
- Keep the framing implicit — present the proposed state honestly, don't explicitly call out "awaiting engineering review"
- Cross-references section: keep as-is, no MCP-specific annotations
- Success metrics: keep existing, no MCP-specific metrics added

### Claude's Discretion
- Whether phase names get updated to reflect MCP or stay as-is
- Whether compiler validation mitigation updates an existing risk or becomes a new row
- Exact wording of status table entries
- TL;DR block updates

</decisions>

<specifics>
## Specific Ideas

- "Nothing is really shipped" — the honest framing. Pipeline is built but not live, LLM is being completed, data collection is 10k of 50-80k
- Architecture is proposed, not validated by the engineering team
- bbjcpl proof-of-concept proved the concept works, but production deployment is future work

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 18-implementation-roadmap*
*Context gathered: 2026-02-01*
