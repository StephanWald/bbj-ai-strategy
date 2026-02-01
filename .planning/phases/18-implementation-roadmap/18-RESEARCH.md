# Phase 18: Implementation Roadmap - Research

**Researched:** 2026-02-01
**Domain:** Docusaurus documentation update -- updating Chapter 7 (Implementation Roadmap) to reflect v1.2 accomplishments, weave MCP server deliverables into phases, and add compiler validation as hallucination mitigation
**Confidence:** HIGH

## Summary

Phase 18 updates Chapter 7 (Implementation Roadmap) to synthesize everything accomplished in Phases 15-17. Chapter 7 is the final technical chapter -- it ties together the roadmap phases, status tracking, risk assessment, and success metrics. The updates are structural (table rows, bullet points, status blocks) rather than narrative (no new sections or diagrams).

The chapter currently reflects January 2026 state: a 5-row "Where We Stand" table, four implementation phases without MCP deliverables, a risk assessment that does not mention compiler validation, and a "Current Status" block that predates v1.2 RAG pipeline shipping and MCP architecture definition. All of these need updating to February 2026 state while honestly acknowledging that nothing is truly deployed -- the RAG pipeline is built but not live, the model is incomplete, and MCP exists only as architecture.

This is a documentation update to a single existing chapter (301 lines), not software development. The established conventions from Phases 15-17 (status block format, decision callout format, cross-reference patterns) apply directly. The CONTEXT.md decisions are well-scoped and the chapter structure needs augmentation, not restructuring.

**Primary recommendation:** Update Chapter 7 in two logical passes: (1) status table and phase descriptions (XREF-04), then (2) risk assessment and remaining sections (XREF-03). Keep phase names as-is. Update the existing hallucination risk row to include compiler validation as an additional mitigation rather than adding a new row. Weave MCP deliverables as bullets within existing phases. Update the "Current Status" block and TL;DR to reflect February 2026 state.

## Standard Stack

This phase is a documentation update, not a code project. The "stack" is the set of tools and patterns used to author and present the content.

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Docusaurus | 3.9.2 | Site framework (existing) | Already configured and deployed |
| Markdown tables | Standard | Status tables, risk assessment | Already used throughout Chapter 7 |
| `:::note[Where Things Stand]` admonition | Docusaurus built-in | Current status block | Already used in Chapter 7 and all other chapters |
| `:::tip[TL;DR]` admonition | Docusaurus built-in | Chapter opening summary | Already present in Chapter 7 |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `:::info[Decision: ...]` admonition | Docusaurus built-in | Architecture decision callouts | Already present in Chapter 7 (one existing callout) |
| Mermaid `graph LR` | Mermaid (bundled) | Phase flow diagram | Already present in Chapter 7, no changes needed |
| `:::note[MVP Checkpoint]` admonition | Docusaurus built-in | Phase checkpoint markers | Already present in Chapter 7, no changes needed |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Updating existing hallucination risk row | Adding new "Compiler validation" risk row | Compiler validation is a *mitigation* for the hallucination risk, not a separate risk; updating the existing row keeps the risk matrix focused on actual risks |
| Keeping phase names unchanged | Renaming phases to mention MCP | Phase names describe outputs (Model, IDE, RAG+Chat, Refinement); MCP is a delivery mechanism, not a phase identity; renaming would dilute the conceptual clarity |

**Installation:** No new dependencies. The entire phase uses the existing Docusaurus configuration. No `npm install` needed.

## Architecture Patterns

### Chapter 7: Current Content Structure (with line references)

```
docs/07-implementation-roadmap/index.md (301 lines)

1.  Frontmatter (lines 1-5)
2.  # Implementation Roadmap heading (line 7)
3.  TL;DR block (lines 9-11) .................... NEEDS UPDATE
4.  Opening paragraphs (lines 13-15)
5.  ## Where We Stand (lines 17-28) ............. NEEDS UPDATE
    - Status table: 5 rows, "Actual (Jan 2026)" column
    - Decision callout: "Acknowledging Existing Work" (lines 30-34)
6.  ## Implementation Phases (lines 36-48)
    - "Why This Order" subsection (lines 40-49)
    - Mermaid flow diagram (lines 51-66) ........ NO CHANGES NEEDED
    - ### Phase 1: Model Validation (lines 68-90) .. NEEDS MCP BULLET
    - ### Phase 2: IDE Integration (lines 92-114) .. NEEDS MCP + COMPILER BULLETS
    - ### Phase 3: RAG + Doc Chat (lines 116-138) .. NEEDS MCP BULLET
    - ### Phase 4: Refinement (lines 140-162) ...... MINOR MCP MENTION
7.  ## Infrastructure Costs (lines 164-197) ..... NO CHANGES NEEDED
8.  ## Risk Assessment (lines 199-232) .......... NEEDS UPDATE
    - Risk table: 6 rows (lines 205-212)
    - "Reading the Risk Matrix" (lines 214-222)
    - "Using This Matrix During Execution" (lines 224-232)
9.  ## Success Metrics (lines 234-276) .......... NO CHANGES NEEDED
10. ## Current Status (lines 279-287) ........... NEEDS UPDATE
11. ## Cross-References (lines 289-301) ......... NO CHANGES NEEDED
```

### Pattern 1: Status Table Expansion (Where We Stand)

**What:** The "Where We Stand" table needs to expand from 5 rows to 7 rows and update the column header from "Actual (Jan 2026)" to "Actual (Feb 2026)".

**Current table (5 rows):**

| Component | Paper Status (Jan 2025) | Actual Status (Jan 2026) |
|-----------|------------------------|------------------------|
| Training data | Schema defined, no curated examples | ~10K data points, promising results |
| Base model | Candidates identified (CodeLlama, StarCoder2) | Qwen2.5-Coder selected, fine-tuning in progress |
| Language server | Architecture planned | v0.5.0 shipped, published on VS Code Marketplace |
| Copilot integration | Not mentioned | Early exploration, cautiously optimistic |
| RAG database | Schema designed | Source corpus identified, pipeline not built |
| Documentation chat | Architecture planned | Vision defined, not yet built |

**Target table (7 rows, updated date, honest status):**

The column header changes to "Actual (Feb 2026)". Existing rows get updated status text. Two new rows are added for MCP Server and Compiler Validation. The "Paper Status (Jan 2025)" column stays as-is for existing rows and gets "Not mentioned" for the two new rows (MCP and compiler validation were not part of the original January 2025 paper).

Recommended row updates:
- **Training data:** "~10K data points collected; estimated 50-80K needed for full coverage"
- **Base model:** keep as-is (still in progress)
- **Language server:** keep as-is (still v0.5.0)
- **Copilot integration:** keep as-is (still early exploration)
- **RAG database:** "Ingestion pipeline built (v1.2); not yet deployed against production corpus"
- **Documentation chat:** "Architecture defined (two-path: MCP access + embedded chat); not yet built"
- **MCP server** (NEW): Paper Status = "Not mentioned" | Actual = "Architecture defined, three tool schemas specified; not yet implemented"
- **Compiler validation** (NEW): Paper Status = "Not mentioned" | Actual = "Proof-of-concept validated (bbjcpltool v1); not yet deployed in production pipeline"

### Pattern 2: MCP Deliverables as Phase Bullets

**What:** Each implementation phase gets one or more bullets for MCP-related deliverables. These are added to the existing "Key deliverables" lists within each phase, not as separate sections.

**Phase 1 (Model Validation):**
- No direct MCP deliverable. Model validation is prerequisite to MCP server. Optionally add a bullet noting the model will be served via MCP `generate_bbj_code` tool (forward reference to how the model gets consumed).

**Phase 2 (IDE Integration):**
- Add bullet: MCP server implementation for `generate_bbj_code` and `validate_bbj_syntax` tools, enabling IDE completions through MCP protocol rather than direct Ollama calls
- Add bullet: Compiler validation integration via `validate_bbj_syntax` -- every LLM suggestion passes through `bbjcpl` before presentation to developer (the generate-validate-fix loop described in Chapter 2)

**Phase 3 (RAG Pipeline + Documentation Chat):**
- Add bullet: MCP `search_bbj_knowledge` tool implementation, exposing the RAG pipeline as a standard tool interface for both chat and any MCP client
- Update existing chat backend bullet to note MCP is the delivery mechanism (not a new bullet, just mention that chat backend acts as MCP client)

**Phase 4 (Refinement + Scaling):**
- Add bullet: MCP server hardening -- monitoring, error handling, and deployment configuration for both stdio (local) and Streamable HTTP (team) modes

### Pattern 3: Risk Assessment Updates

**What:** Two changes to the risk table: (1) update the hallucination risk row to add compiler validation as mitigation, (2) update the training data sufficiency row to reflect 10K/50-80K reality.

**Hallucination risk row -- UPDATED mitigation:**
Current: "Langium parser validation of all LLM suggestions before presentation; evaluation benchmarks with known-bad patterns; Copilot bridge as fallback completion source"
Updated: Add compiler validation via `bbjcpl` as ground-truth mitigation. The mitigation column should now include three layers: (1) Langium parser validation (heuristic), (2) `bbjcpl` compiler validation (ground-truth, proven by bbjcpltool v1 proof-of-concept), (3) evaluation benchmarks. Note: per CONTEXT.md, the compiler validation is "designed, not deployed" -- honest about the gap.

**Training data sufficiency risk row -- UPDATED mitigation:**
Current: "Prioritize modern generations (BBj GUI + DWC) first where developer activity is highest; expand to legacy generations iteratively based on user demand"
Updated: Include the 10K/50-80K data point reality. Approximately 10K examples collected; estimated 50-80K needed for full generational coverage. The prioritization strategy remains the same but now has a concrete baseline to measure against.

**No new MCP-specific risk row** per CONTEXT.md decision. MCP is an implementation choice, not a project risk.

### Pattern 4: Current Status Block Update

**What:** The `:::note[Where Things Stand]` block near the end of Chapter 7 needs updating from January 2026 to February 2026. It should reflect the same state documented across all other chapter status blocks.

**Current block (January 2026 state):**
- Phase 1: Partially complete
- Phase 2-4: Planned
- Infrastructure: $2K-5K estimate

**Target block (February 2026 state):**
- Phase 1: Partially complete -- same fundamentals but now with 10K/50-80K training data context
- RAG pipeline built (v1.2) but not deployed against production corpus
- MCP server architecture defined (v1.3) -- three tool schemas, generate-validate-fix loop validated
- Compiler validation concept proven (bbjcpltool v1) but not deployed in production pipeline
- Phase 2-4: Planned (with MCP deliverables now woven into descriptions)
- Infrastructure: same cost estimates (no change)

The block should maintain the implicit "architecture proposed" framing from CONTEXT.md -- present the state honestly without explicitly calling out "awaiting engineering review."

### Pattern 5: TL;DR Block Update

**What:** The TL;DR needs to reflect v1.2 and v1.3 accomplishments alongside the existing content.

**Current TL;DR mentions:**
- bbj-language-server (shipped)
- ~10K data points (in progress)
- $1,500-5,000 cost
- Each phase delivers standalone value

**Target TL;DR should add mentions of:**
- RAG ingestion pipeline shipped (v1.2)
- MCP server architecture defined (standard protocol for all AI tools)
- Compiler validation proven (ground-truth syntax checking)
- Still keep the "each phase delivers standalone value" framing
- Maintain single-paragraph brevity

### Anti-Patterns to Avoid

- **Overpromising:** Do not describe MCP server, compiler validation, or RAG pipeline as "shipped" or "deployed." They are "built" (RAG), "defined" (MCP), or "proven" (compiler). The honest framing is critical.
- **Separate MCP section:** Do not add a cross-cutting "MCP Deliverables" section. Per CONTEXT.md, MCP bullets weave into existing phases.
- **MCP-specific risk rows:** Do not add a risk row for MCP. MCP is an implementation choice, not a project risk.
- **MCP-specific success metrics:** Per CONTEXT.md, success metrics stay as-is. No new MCP metrics.
- **MCP-specific MVP checkpoints:** Per CONTEXT.md, MCP deliverables fold into existing MVP checkpoints. No separate MCP gates.
- **Explicit "awaiting engineering review" language:** Per CONTEXT.md, keep this implicit. Present the proposed state honestly.
- **Cross-reference annotations:** Per CONTEXT.md, cross-references section stays as-is. No MCP annotations.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Status consistency across chapters | Hand-track status text in each chapter | Use the verified status blocks from Ch2/3/4/5/6 as source of truth | Chapter 7's status must be consistent with other chapters; copy the established state |
| Risk table formatting | Custom table layout | Standard Markdown pipe-table format already in use | The existing risk table format is established and works |
| MCP deliverable phrasing | Invent new terminology | Use the established tool names: `search_bbj_knowledge`, `generate_bbj_code`, `validate_bbj_syntax` | Consistency with Chapters 2, 3, 4, 5, 6 -- all use these exact names |

**Key insight:** Chapter 7 is a synthesis chapter. Every fact it states should be traceable to a more detailed chapter. When in doubt about wording, check what the upstream chapter says.

## Common Pitfalls

### Pitfall 1: Status Inconsistency Across Chapters

**What goes wrong:** Chapter 7 states a component's status differently from the chapter that owns that component (e.g., Chapter 7 says "RAG pipeline planned" when Chapter 6 says "RAG pipeline shipped v1.2").
**Why it happens:** Chapter 7 was last updated before the other chapters received their v1.3 updates.
**How to avoid:** Cross-reference every status claim in Chapter 7 against the corresponding chapter's `:::note[Where Things Stand]` block. The following table maps components to their authoritative chapters:

| Component | Authoritative Chapter | Current Status Text |
|-----------|----------------------|---------------------|
| Fine-tuned model | Ch3 (Jan 2026) | ~10K examples, Qwen2.5-Coder-7B fine-tuning in progress |
| Language server | Ch4 (Feb 2026) | v0.5.0 shipped on VS Code Marketplace |
| Compiler validation | Ch4 (Feb 2026) | bbjcpltool v1 proof-of-concept shipped |
| Documentation chat | Ch5 (Feb 2026) | Two-path architecture defined, nothing shipped |
| RAG database | Ch6 (Feb 2026) | Ingestion pipeline shipped v1.2, not deployed to production |
| MCP server | Ch2 (Feb 2026) | Architecture defined v1.3, three tool schemas specified |
| Ollama deployment | Ch3 (Jan 2026) | Validated for model serving |

**Warning signs:** Any use of "planned" or "not built" for the RAG pipeline (it is built), or "shipped" for MCP (it is defined, not implemented).

### Pitfall 2: Overstating Deployment Readiness

**What goes wrong:** Chapter 7 implies components are production-ready when they are built/defined/proven but not deployed.
**Why it happens:** Enthusiasm about progress leads to overly positive framing.
**How to avoid:** Use the precise language from CONTEXT.md:
- RAG pipeline: "built but not live" (not "shipped" in isolation)
- Fine-tuned LLM: "in progress, not complete"
- Training data: "10K collected, estimated 50-80K total needed"
- MCP server: "design only, no implementation exists yet"
- Compiler validation: "proof-of-concept validated the concept, not deployed"
**Warning signs:** "Shipped" without qualification, "deployed" for anything except the language server and VS Code extension.

### Pitfall 3: MCP Deliverables as Separate Section

**What goes wrong:** MCP deliverables are presented as a standalone cross-cutting section or a new Phase 5.
**Why it happens:** MCP touches all phases, so grouping it together seems logical.
**How to avoid:** Per CONTEXT.md, weave MCP bullets into existing phase descriptions. MCP is a delivery mechanism, not a phase-level deliverable.
**Warning signs:** Any heading containing "MCP" at the phase level (##), or a section titled "MCP Integration" or similar.

### Pitfall 4: Training Data Risk Not Updated

**What goes wrong:** The training data sufficiency risk still says "Prioritize modern generations first" without mentioning the concrete 10K/50-80K baseline.
**Why it happens:** Risk table rows are easy to overlook since the table is deep in the chapter.
**How to avoid:** Update the mitigation column for the training data risk to include the concrete numbers. The risk itself (Medium likelihood, Medium impact) remains accurate; the mitigation has more concrete data now.
**Warning signs:** Risk table mentions only "prioritize modern generations" without the 10K/50-80K context.

## Code Examples

No code examples needed for this phase. This is a documentation update to Markdown content. The patterns are all textual (table rows, bullet points, status blocks).

### Reference: Status Block Format (from established convention)

```markdown
:::note[Where Things Stand -- February 2026]
- **Phase 1 (Model Validation):** [status text]
- **Phase 2 (IDE Integration):** [status text]
- **Phase 3 (RAG + Doc Chat):** [status text]
- **Phase 4 (Refinement):** [status text]
- **Total infrastructure investment:** [cost text]
:::
```

### Reference: Risk Table Row Format (from established convention)

```markdown
| [Risk description] | [Likelihood] | [Impact] | [Mitigation description] |
```

### Reference: Phase Deliverable Bullet Format (from established convention)

```markdown
- **[Deliverable name]** -- [Description of what it is and what it produces].
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 5-row status table (Jan 2026) | 7-row status table (Feb 2026) | Phase 15 (Chapter 2 expanded table) | Chapter 7 needs to match Chapter 2's expanded tracking |
| Langium-only hallucination mitigation | Langium + bbjcpl compiler validation | Phase 16 (compiler validation added to Ch4) | Risk assessment gains ground-truth mitigation |
| RAG pipeline "not built" | RAG pipeline shipped v1.2 | v1.2 milestone (Phases 8-14) | Status blocks need to reflect built-not-deployed state |
| Documentation chat as single system | Two-path: MCP access + embedded chat | Phase 17 (Chapter 5 restructured) | Phase 3 description needs MCP delivery mechanism noted |

**Deprecated/outdated:**
- "Pipeline not built" for RAG: replaced by "Ingestion pipeline built (v1.2), not yet deployed"
- "Source corpus identified" for RAG: replaced by more detailed status showing 6 parsers, generation tagging, hybrid search
- "Vision defined" for documentation chat: replaced by "Two-path architecture defined"

## Discretionary Recommendations

These are the areas marked as "Claude's Discretion" in CONTEXT.md, with specific recommendations:

### 1. Phase Names: Keep As-Is

**Recommendation:** Do not rename any implementation phases.

**Reasoning:** The current phase names describe outputs:
- Phase 1: Model Validation -- produces a validated model
- Phase 2: IDE Integration -- produces working IDE completions
- Phase 3: RAG Pipeline + Documentation Chat -- produces search and chat
- Phase 4: Refinement + Scaling -- produces production hardening

MCP is a delivery mechanism within each phase, not the phase's identity. Adding "MCP" to phase names would dilute the conceptual clarity. The MCP deliverables are communicated through bullets within each phase description, which is the approach specified by CONTEXT.md.

### 2. Compiler Validation: Update Existing Hallucination Risk Row

**Recommendation:** Update the existing "Fine-tuned model hallucinates BBj syntax" risk row to add compiler validation as an additional mitigation layer.

**Reasoning:**
- Compiler validation is a *mitigation for* the hallucination risk, not a separate risk
- The existing row already lists Langium parser validation as mitigation
- Adding compiler validation gives the row three defense layers: (1) Langium heuristic validation, (2) bbjcpl ground-truth validation, (3) evaluation benchmarks
- A separate row would imply compiler validation is itself a risk, which misrepresents it
- The updated mitigation should note "designed, not deployed" per CONTEXT.md tone

**Recommended mitigation text:** "Three-layer defense: Langium parser validation (heuristic, in language server); `bbjcpl` compiler validation (ground-truth syntax checking, proven by bbjcpltool v1 proof-of-concept -- see [Chapter 4](/docs/ide-integration)); evaluation benchmarks with known-bad patterns. Copilot bridge as fallback completion source. Note: compiler validation is proven at concept level; production pipeline integration is Phase 2 work."

### 3. Status Table Entry Wording

**Recommended wording for each row:**

| Component | Paper Status (Jan 2025) | Actual (Feb 2026) |
|-----------|------------------------|-------------------|
| Training data | Schema defined, no curated examples | ~10K data points collected; estimated 50-80K needed for full generational coverage |
| Base model | Candidates identified (CodeLlama, StarCoder2) | Qwen2.5-Coder-7B selected, fine-tuning in progress |
| Language server | Architecture planned | v0.5.0 shipped, published on VS Code Marketplace |
| Copilot integration | Not mentioned | Early exploration, cautiously optimistic |
| RAG database | Schema designed | Ingestion pipeline built (v1.2) with 6 source parsers; not yet deployed against production corpus |
| Documentation chat | Architecture planned | Two-path architecture defined (MCP access + embedded chat); not yet built |
| MCP server | Not mentioned | Architecture defined, three tool schemas specified; not yet implemented |
| Compiler validation | Not mentioned | Proof-of-concept validated (bbjcpltool v1); production deployment planned |

Note: "Documentation chat" row updates from "Vision defined, not yet built" to "Two-path architecture defined (MCP access + embedded chat); not yet built" to reflect the Chapter 5 restructure.

### 4. TL;DR Block Updates

**Recommendation:** Update the TL;DR to mention RAG pipeline, MCP architecture, and compiler validation alongside existing content. Keep it to a single paragraph.

**Recommended TL;DR:**

"A four-phase roadmap with explicit MVP checkpoints, building on the already-shipped [bbj-language-server](https://github.com/BBx-Kitchen/bbj-language-server), a v1.2 RAG ingestion pipeline (built, awaiting production deployment), in-progress model fine-tuning (~10K of an estimated 50-80K data points), and a defined [MCP server architecture](/docs/strategic-architecture#the-mcp-server-concrete-integration-layer) that provides a standard protocol for all BBj AI tools. Compiler validation via `bbjcpl` has been proven at concept level (see [Chapter 4](/docs/ide-integration)), adding ground-truth syntax checking to the hallucination mitigation strategy. Total infrastructure investment is modest -- roughly $1,500-5,000 one-time plus minimal monthly hosting -- because the strategy uses self-hosted open-source tooling throughout. Each phase delivers standalone value; you can stop at any checkpoint and still have a working system."

## Open Questions

Things that could not be fully resolved:

1. **Mermaid diagram update**
   - What we know: The phase flow diagram (graph LR) shows four phases without MCP annotations. Per CONTEXT.md, MCP deliverables fold into existing phases, not separate gates.
   - What's unclear: Whether the Mermaid diagram needs any annotation (e.g., adding "MCP" as a subtitle in any phase box) or stays completely as-is.
   - Recommendation: Leave the diagram as-is. It shows phase-level flow, and MCP is described in the phase text. Adding annotations to the diagram boxes would clutter them.

2. **"Using This Matrix During Execution" section**
   - What we know: This section provides checkpoint-specific guidance for revisiting risks. Currently it mentions Checkpoints 1-3 with specific risks to re-evaluate.
   - What's unclear: Whether to update checkpoint guidance to mention compiler validation re-evaluation.
   - Recommendation: Add a brief note to the Checkpoint 2 guidance about re-evaluating compiler validation integration status, since that is when IDE integration (including compiler validation) is implemented.

3. **Opening paragraph update**
   - What we know: The opening paragraph (line 13) references "the previous chapters" and lists all six. This still works as-is since the chapters haven't changed titles.
   - What's unclear: Whether to add any mention of MCP architecture to the opening paragraph framing.
   - Recommendation: Leave as-is. The opening paragraph sets up "when, how much, and what could go wrong" -- it doesn't need MCP specifics.

## Sources

### Primary (HIGH confidence)

- `docs/07-implementation-roadmap/index.md` -- Current Chapter 7 content (301 lines), read in full
- `docs/02-strategic-architecture/index.md` (lines 340-387) -- Chapter 2 current status and 7-row component table
- `docs/03-fine-tuning/index.md` (lines 395-424) -- Chapter 3 MCP Integration and status block
- `docs/04-ide-integration/index.md` (lines 490-519) -- Chapter 4 status block with bbjcpltool
- `docs/05-documentation-chat/index.md` (lines 270-301) -- Chapter 5 status block with two-path architecture
- `docs/06-rag-database/index.md` (lines 495-524) -- Chapter 6 MCP Integration and v1.2 shipped status
- `.planning/phases/18-implementation-roadmap/18-CONTEXT.md` -- User decisions constraining this phase
- `.planning/REQUIREMENTS.md` -- XREF-03 and XREF-04 requirement definitions
- `.planning/ROADMAP.md` -- Phase 18 success criteria and dependency information

### Secondary (HIGH confidence -- project artifacts)

- `.planning/phases/15-strategic-architecture/15-VERIFICATION.md` -- Verified Phase 15 outcomes
- `.planning/phases/16-compiler-validation/16-VERIFICATION.md` -- Verified Phase 16 outcomes
- `.planning/phases/17-chat-cross-references/17-VERIFICATION.md` -- Verified Phase 17 outcomes
- `.planning/phases/15-strategic-architecture/15-02-SUMMARY.md` -- Status table expansion to 7 rows
- `.planning/STATE.md` -- Current project state (Phase 17 complete, ready for Phase 18)
- `.planning/milestones/v1.2-ROADMAP.md` -- v1.2 milestone summary (RAG pipeline shipped)

### Tertiary (N/A)

No external sources needed. This is entirely an internal documentation update using information already verified within the project.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Docusaurus markdown, same tools as Phases 15-17
- Architecture: HIGH -- Chapter structure is well-documented, changes are additive (table rows, bullets)
- Pitfalls: HIGH -- Status consistency verified against all six upstream chapters; concrete cross-reference table provided
- Discretionary recommendations: HIGH -- All four areas analyzed with specific rationale and recommended text

**Research date:** 2026-02-01
**Valid until:** 2026-03-01 (stable -- documentation update, no external dependencies)
