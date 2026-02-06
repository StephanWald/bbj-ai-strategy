# Phase 35: Implementation Roadmap Restructure - Context

**Gathered:** 2026-02-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure Chapter 7 from an elaborate 4-phase speculative implementation plan into a streamlined chapter: progress notes about where things stand, and a simple list of what's planned next. No new capabilities -- this is a documentation chapter rewrite that reflects reality after 7 delivered milestones (v1.0-v1.6).

</domain>

<decisions>
## Implementation Decisions

### Chapter structure (strip to essentials)
- CUT the entire 4-phase implementation plan (Phases 1-4 with MVPs, deliverables, success criteria)
- CUT the infrastructure costs table and cost-by-scenario table
- CUT the NIST risk assessment framework and risk matrix
- CUT the success metrics tables (technical, user, business metrics)
- CUT the "Establishing Baselines" section
- KEEP: TL;DR (rewrite), progress/comparison table, component summary, forward plan, status block, cross-references
- Result should be significantly shorter than the current 311 lines

### Delivered work presentation (component summary)
- Organize by component (RAG system, MCP server, web chat, documentation site, language server, fine-tuning research) with current state of each
- NOT organized by milestone history (v1.0, v1.1, etc.) -- focus on what exists now, not the journey
- Use Phase 32 status terminology throughout: operational / operational for internal exploration / active research / planned

### Progress comparison table (keep)
- Keep the "Paper Status Jan 2025 vs Actual Feb 2026" comparison table
- Update with accurate data: 14B-Base recommendation (not 7B), RAG operational with 51K+ chunks, MCP server operational with 2 tools, web chat operational, etc.
- Shows distance traveled from the original strategy paper

### Forward plan (bulleted list)
- Simple bulleted list of next steps
- No phases, no timelines, no cost estimates
- Include credible next steps from research: evaluation suite, training fixes (validation set, completion masking, Base model), FIM fine-tuning, ghost text implementation, Continue.dev integration
- Keep it grounded -- these are the actual next things to do, not aspirational multi-year plans

### Claude's Discretion
- TL;DR rewrite -- should reflect the stripped-down chapter (progress + plan, not elaborate roadmap)
- How to order the component summary entries
- Whether to keep any part of the cross-references section (other chapters already cross-reference each other)
- Decision callout boxes -- keep, update, or remove (the "Acknowledging Existing Work" and "Hardware Costs Only" callouts may no longer fit a stripped-down chapter)
- Mermaid diagram -- likely remove since the 4-phase plan is being cut

</decisions>

<specifics>
## Specific Ideas

- The current chapter presents as if the project is starting Phase 1 of a speculative 4-phase plan. In reality, 7 milestones have been delivered, RAG is operational, MCP server is operational, web chat is running, and the language server has 508 commits. The chapter needs to reflect this reality.
- The comparison table is the key artifact -- it shows concrete progress from paper to reality.
- The forward plan should connect to what the other updated chapters (3, 4) already describe (evaluation methodology, Continue.dev path, FIM gap).

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 35-implementation-roadmap*
*Context gathered: 2026-02-06*
