# Phase 16: Compiler Validation - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Chapter 4 updated to explain how BBj's compiler (bbjcpl) provides ground-truth syntax validation in the IDE completion pipeline. Includes bbjcpltool proof-of-concept documentation, updated architecture diagram, and decision callout. The chapter status block is updated to reflect bbjcpltool v1 shipped and compiler-in-the-loop validated.

</domain>

<decisions>
## Implementation Decisions

### Narrative framing
- Primary audience is technical decision-makers — strategic focus on WHY compiler validation matters, not implementation how-to
- Key message: ground-truth beats heuristics — the compiler is the authoritative source for syntax validity, not pattern matching or guessing
- BBj terminology (bbjcpl, .bbj, BASIS) introduced briefly, then used freely throughout
- No contrast with other language ecosystems — let BBj's compiler validation story stand on its own

### Diagram approach
- Detailed diagram with 5-6 participants (IDE, Extension, MCP Client, MCP Server, LLM, Compiler)
- Must show the error/retry path — the generate-validate-fix cycle is the whole point
- Relationship to Chapter 2's diagram is Claude's discretion (zoom-in vs IDE pipeline focus)
- Diagram format (sequence vs flowchart) is Claude's discretion

### Proof-of-concept depth
- Validation report tone — factual, measured: "we built it, tested it, here's what we learned"
- Include one illustrative example showing hallucinated BBj code alongside the compiler error output — makes validation tangible
- Light metrics if available (e.g., "caught N errors across M completions") but don't invent precision
- No file paths, no hook scripts per success criteria; Claude's discretion on other redaction boundaries

### Section structure
- Section placement within Chapter 4 is Claude's discretion based on existing chapter flow
- Error format presentation (own subsection vs inline) is Claude's discretion
- Decision callout "Compiler Validation via bbjcpl" must mention two alternatives considered:
  - Language server / static analysis — rejected because it catches patterns, not ground-truth syntax
  - LLM self-check — rejected because the LLM that hallucinated can't reliably catch its own errors
  - Note: BBj doesn't have a traditional linter; the language server is the closest alternative (user was unsure of exact capabilities)
- Chapter status block (:::note[Where Things Stand]) updated inline as part of this phase, reflecting bbjcpltool v1 shipped

### Claude's Discretion
- Diagram format choice (sequence vs flowchart)
- Diagram scope (zoom into validation step vs IDE pipeline view)
- Section placement within Chapter 4
- Error format presentation approach (subsection vs inline)
- Implementation detail redaction boundaries beyond stated rules
- Whether light metrics strengthen the narrative given available data

</decisions>

<specifics>
## Specific Ideas

- One concrete example: hallucinated BBj code + compiler error output — shows the reader exactly what "ground-truth validation" means in practice
- Decision callout alternatives should acknowledge the language server as the closest alternative to a linter, since BBj doesn't have a standalone linter per se

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 16-compiler-validation*
*Context gathered: 2026-02-01*
