# Phase 19: Final Consistency Pass - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Quality verification across all chapters updated in v1.3 (Phases 15-18). Cross-references resolve, BBj code validates, JSON schemas are valid, status blocks are consistent, decision callouts follow format, and the Docusaurus site builds with zero warnings. No new content is created — this phase fixes what's already there.

</domain>

<decisions>
## Implementation Decisions

### Validation scope
- Validate ALL BBj code samples site-wide, not just v1.3 additions
- All BBj code must pass `bbjcpl -N` — no pseudo-code exceptions; if it's in the docs, it compiles
- JSON tool schemas (Chapter 2 MCP definitions) also get syntax validation
- Mermaid diagrams get syntax-only validation (no render verification)

### Fix vs. flag approach
- Two-pass workflow: audit first (scan everything, produce findings), then fix systematically
- Audit findings are ephemeral — tracked as tasks in the plan, not a separate report file
- Clear-cut issues: Claude fixes directly
- Ambiguous/judgment-call issues: flag for user decision before applying
- Landing page descriptions are aspirational — only fix outright contradictions with chapter content, not minor drift

### Cross-reference verification
- Both approaches: Docusaurus build broken-link check AND manual grep for anchor targets
- Verify cross-references contextually — the linked section should actually cover what the referring text claims
- Scope: all cross-references site-wide, not just v1.3 additions
- Fix ALL build warnings, including pre-existing ones unrelated to v1.3 — zero means zero

### Status block reconciliation
- Chapter 7 (implementation roadmap) is the source of truth for component status
- Other chapters' status blocks must be consistent with Chapter 7's timeline
- Keep natural voice in each chapter's status phrasing — no forced standardization of terminology
- Remove dates from status blocks — they go stale and add maintenance burden
- Decision callouts verified for both format (four fields present) AND content quality (substantive rationale, genuine alternatives)

### Claude's Discretion
- Order of audit checks (which validation to run first)
- How to structure the plan breakdown (one plan vs. multiple)
- Specific fix wording when updating status blocks or descriptions
- Whether to batch related fixes or commit them individually

</decisions>

<specifics>
## Specific Ideas

- "Zero warnings means zero" — the success criteria in the roadmap is absolute, not aspirational
- "If it's in the docs, it compiles" — the site advocates compiler validation, so its own code must pass
- Chapter 7 as single source of truth prevents conflicting status narratives across chapters

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 19-final-consistency-pass*
*Context gathered: 2026-02-01*
