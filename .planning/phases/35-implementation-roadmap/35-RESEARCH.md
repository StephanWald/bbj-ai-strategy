# Phase 35: Implementation Roadmap Restructure - Research

**Researched:** 2026-02-06
**Domain:** Documentation rewrite (Chapter 7 - Implementation Roadmap)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Chapter structure (strip to essentials):**
- CUT the entire 4-phase implementation plan (Phases 1-4 with MVPs, deliverables, success criteria)
- CUT the infrastructure costs table and cost-by-scenario table
- CUT the NIST risk assessment framework and risk matrix
- CUT the success metrics tables (technical, user, business metrics)
- CUT the "Establishing Baselines" section
- KEEP: TL;DR (rewrite), progress/comparison table, component summary, forward plan, status block, cross-references
- Result should be significantly shorter than the current 311 lines

**Delivered work presentation (component summary):**
- Organize by component (RAG system, MCP server, web chat, documentation site, language server, fine-tuning research) with current state of each
- NOT organized by milestone history (v1.0, v1.1, etc.) -- focus on what exists now, not the journey
- Use Phase 32 status terminology throughout: operational / operational for internal exploration / active research / planned

**Progress comparison table (keep):**
- Keep the "Paper Status Jan 2025 vs Actual Feb 2026" comparison table
- Update with accurate data: 14B-Base recommendation (not 7B), RAG operational with 51K+ chunks, MCP server operational with 2 tools, web chat operational, etc.
- Shows distance traveled from the original strategy paper

**Forward plan (bulleted list):**
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

### Deferred Ideas (OUT OF SCOPE)

None -- discussion stayed within phase scope.

</user_constraints>

## Summary

This phase restructures Chapter 7 (Implementation Roadmap) from a speculative 4-phase plan into a concise progress-and-plan chapter. The current chapter is 311 lines and presents an elaborate roadmap with phases, MVP checkpoints, infrastructure costs, risk assessment, success metrics, and baselines -- all written as if the project were about to begin Phase 1. In reality, 7 milestones have been delivered (v1.0-v1.6), the RAG system is operational with 51K+ chunks, the MCP server has 2 operational tools, web chat is running, and the language server has 508 commits. The chapter needs to reflect this reality.

The restructure is a significant deletion-and-rewrite: approximately 200+ lines of speculative content are removed (4-phase plan, cost tables, risk matrix, success metrics, baselines) and replaced with approximately 100-120 lines of concrete content (updated comparison table, component summary, forward plan). The result should be roughly 120-160 lines -- significantly shorter than the current 311.

The research below catalogs the current chapter section-by-section, maps accurate data for the comparison table and component summary from the other updated chapters (3, 4, 5, 6), and provides recommendations for the Claude's Discretion items.

**Primary recommendation:** Execute as a single plan wave. The work is primarily deletion + data-accurate rewriting of 4 kept sections. There is no new conceptual content to develop -- everything is pulling accurate status from the already-updated chapters (2, 3, 4, 5, 6). One wave of ~15-20 tasks handles the entire rewrite plus build verification.

## Standard Stack

This phase involves editing a single Markdown file in a Docusaurus 3.9.2 site.

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Docusaurus | 3.9.2 | Site framework | Existing project stack |
| Markdown | N/A | Content format | Chapter 7 is `.md` (not `.mdx`) |
| `npm run build` | N/A | Build verification | Ensures no broken links or syntax |

No new installations needed.

## Architecture Patterns

### File Location

```
docs/
└── 07-implementation-roadmap/
    └── index.md          # Chapter 7 -- the only file to edit
```

Single-file chapter (311 lines currently). No sub-pages or supporting assets.

### Pattern: Chapter Structure Convention

From Phase 32, the established chapter pattern is:
1. YAML front matter (sidebar_position, title, description)
2. `# Title` heading
3. `:::tip[TL;DR]` summary block
4. Intro paragraphs with cross-references to other chapters
5. Major sections with `## Heading`
6. `:::info[Decision: ...]` callouts for key choices (Choice/Rationale/Alternatives/Status)
7. `:::note[Where Things Stand]` status block near the end
8. Closing paragraph with cross-references to other chapters

### Pattern: Status Block Convention

```markdown
:::note[Where Things Stand]
- **Operational:** Component description
- **Active research:** Component description
- **Planned:** Component description
:::
```

No dates in status blocks (v1.3 decision). Use bullet points with bold status labels.

### Pattern: Prohibited Terminology

| Prohibited | Replace With |
|------------|-------------|
| "shipped" | "operational" or "available" |
| "production" | "operational for internal exploration" or remove |
| "deployed" (as final state) | "operational for internal exploration" |
| "production-grade" | "functional" or remove |
| "production corpus" | "full documentation corpus" |

## Current Chapter Analysis: Section-by-Section

This is the core research output. It maps every section of the current chapter to its required fate.

### Section Inventory

| # | Section | Lines | Fate | Notes |
|---|---------|-------|------|-------|
| 1 | YAML front matter | 1-5 | **Modify** | Update description to match new chapter purpose |
| 2 | `# Implementation Roadmap` | 7 | **Keep** | Title stays |
| 3 | `:::tip[TL;DR]` | 9-11 | **Replace** | Must reflect progress-and-plan, not speculative phases |
| 4 | Intro paragraphs | 13-16 | **Replace** | Current framing ("when, how much, what could go wrong") no longer fits; chapter answers "where we are, what's next" |
| 5 | `## Where We Stand` + comparison table | 18-37 | **Modify** | KEEP the table, UPDATE data. Remove the "not a greenfield" preamble (chapter no longer needs to justify building on existing work) |
| 6 | `:::info[Decision: Acknowledging Existing Work]` | 32-37 | **CUT** | Decision callout is about framing the roadmap from current state vs zero -- no longer relevant when the entire chapter IS the current state |
| 7 | `## Implementation Phases` | 39-169 | **CUT entirely** | All 4 phases with MVP checkpoints, deliverables, success criteria |
| 8 | Mermaid diagram | 54-69 | **CUT** | 4-phase diagram has no purpose without the phases |
| 9 | `## Infrastructure Costs` | 172-206 | **CUT entirely** | Cost tables and cost-by-scenario |
| 10 | `:::info[Decision: Hardware Costs Only]` | 201-206 | **CUT** | Accompanies the cost section |
| 11 | `## Risk Assessment` | 208-241 | **CUT entirely** | NIST framework and risk matrix |
| 12 | `## Success Metrics` | 243-286 | **CUT entirely** | Technical, user, business metrics tables; baselines section |
| 13 | `## Current Status` | 288-297 | **Replace** | Rewrite using component-organized format with Phase 32 terminology |
| 14 | `## Cross-References` | 299-311 | **Evaluate** | Claude's discretion -- see recommendation below |

### Line Count Estimate

| Section | Current Lines | New Lines | Change |
|---------|--------------|-----------|--------|
| Front matter + title | 7 | 7 | Same |
| TL;DR + intro | 8 | 8-10 | Rewrite |
| Comparison table ("Where We Stand") | 20 | 20-25 | Update data |
| Component summary | 0 | 35-45 | NEW -- replaces phases + status |
| Forward plan | 0 | 15-25 | NEW -- bulleted next steps |
| Status block | 10 | 10-12 | Rewrite |
| Cross-references / closing | 13 | 8-12 | Trim or keep |
| **TOTAL** | **311** | **~110-140** | **~55-65% reduction** |

## Accurate Data for Comparison Table

The comparison table is the key artifact. Here is the accurate data gathered from the now-updated chapters (2, 3, 4, 5, 6):

### Updated Comparison Table Data

| Component | Paper Status (Jan 2025) | Actual (Feb 2026) |
|-----------|------------------------|-------------------|
| Training data | Schema defined, no curated examples | 9,922 ChatML examples (bbjllm); 2 seed examples in training-data/ repository with JSON Schema validation |
| Base model | Candidates identified (CodeLlama, StarCoder2) | Qwen2.5-Coder-14B-Base recommended; bbjllm experiment validated Qwen2.5-Coder family |
| Language server | Architecture planned | v0.5.0 operational, 508 commits, 13 contributors, VS Code Marketplace |
| IDE integration | Not mentioned | Continue.dev evaluated as primary path; Copilot BYOK researched (chat only) |
| RAG database | Schema designed | Operational for internal exploration -- 7 parsers, 51K+ chunks, PostgreSQL + pgvector, hybrid retrieval |
| Documentation chat | Architecture planned | Operational for internal exploration -- Claude API + RAG, SSE streaming, source citations, auto BBj code validation |
| MCP server | Not mentioned | Operational for internal exploration -- 2 tools (search_bbj_knowledge, validate_bbj_syntax), stdio + Streamable HTTP |
| Compiler validation | Not mentioned | Operational -- bbjcpltool v1 validated, integrated into MCP server and web chat |
| Documentation site | Not mentioned | Operational -- Docusaurus site with 7 chapters covering full strategy |

**Source verification:**
- Training data: Chapter 3 lines 227-228 (9,922 ChatML, 2 seed examples)
- Base model: Chapter 3 lines 61-69 (14B-Base decision callout)
- Language server: Chapter 4 lines 219-228 (v0.5.0, 508 commits, 13 contributors)
- IDE integration: Chapter 4 lines 201-209 (Continue.dev decision)
- RAG database: Chapter 6 lines 519-525 (51K+ chunks, 7 parsers)
- Documentation chat: Chapter 5 lines 285-294 (Claude API + RAG, SSE, citations)
- MCP server: Chapter 2 lines 369-373 (2 tools, stdio + Streamable HTTP)
- Compiler validation: Chapter 2 line 371 (bbjcpltool, MCP tool, chat integration)

## Accurate Data for Component Summary

Organized by component with current status, as the user requested:

### RAG Knowledge System
**Status:** Operational for internal exploration
- 7 source parsers (Flare XHTML, PDF, WordPress Advantage, WordPress KB, Docusaurus MDX, BBj Source, JavaDoc JSON)
- 51,134 chunks across 7 source groups (Flare: 44,587; WordPress: 2,950; Web crawl: 1,798; MDX: 951; JavaDoc: 695; BBj source: 106; PDF: 47)
- PostgreSQL 17 + pgvector 0.8.0, Qwen3-Embedding-0.6B (1024 dimensions)
- Hybrid retrieval (dense vectors + BM25 + reciprocal rank fusion + cross-encoder reranking)
- REST API: POST /search, GET /stats, GET /health
- Source: Chapter 6

### MCP Server
**Status:** Operational for internal exploration
- 2 operational tools: search_bbj_knowledge (semantic search across documentation corpus), validate_bbj_syntax (BBj compiler validation via bbjcpl)
- 1 planned tool: generate_bbj_code (requires operational fine-tuned model)
- Available via stdio and Streamable HTTP transports
- Generate-validate-fix loop validated by bbjcpltool proof-of-concept
- Source: Chapter 2

### Web Chat
**Status:** Operational for internal exploration
- Available at /chat endpoint on documentation site
- Claude API backend with RAG retrieval from 51K+ chunk corpus
- SSE streaming for real-time responses
- Source citations with clickable documentation links
- Automatic BBj code validation via bbjcpl with 3-attempt auto-fix
- Source: Chapter 5

### Documentation Site
**Status:** Operational
- Docusaurus 3.9.2 site with 7 chapters covering full strategy
- Chapters: BBj Challenge, Strategic Architecture, Fine-Tuning, IDE Integration, Documentation Chat, RAG Database, Implementation Roadmap
- Source: Project structure

### Language Server (bbj-language-server)
**Status:** Operational
- v0.5.0, published on VS Code Marketplace
- Langium 4.x framework, TypeScript (87.9%)
- 508 commits, 13 contributors
- Syntax highlighting, code completion, diagnostics, formatting, code execution
- bbj-vscode (VS Code) + bbj-intellij (IntelliJ) extensions
- Source: Chapter 4

### Fine-Tuning Research
**Status:** Active research
- bbjllm experiment: 9,922 ChatML examples fine-tuned on Qwen2.5-Coder-32B-Instruct via QLoRA/PEFT
- Research recommends: Qwen2.5-Coder-14B-Base with two-stage training (continued pretraining + instruction fine-tuning)
- Three identified improvements: validation set, completion masking, Base model variant
- Evaluation methodology designed: bbjcpl-based compile@1 metric
- Toolchain identified: Unsloth 2026.1.4 + llama.cpp + Ollama 0.15.x
- Source: Chapter 3

### Compiler Validation
**Status:** Operational
- bbjcpltool v1 proof-of-concept validated
- Integrated into MCP server (validate_bbj_syntax tool) and web chat (auto-validation)
- bbjcpl -N for syntax-only compilation checking
- Source: Chapters 2, 4

## Accurate Data for Forward Plan

Credible next steps drawn from Chapters 3 and 4:

### Fine-Tuning Next Steps (from Chapter 3)
- Build evaluation suite using bbjcpl-based compile@1 metric with held-out test set
- Address training methodology: add validation set (10% holdout), implement completion masking (mask system/user tokens), switch to Base model variant
- Switch from Qwen2.5-Coder-32B-Instruct to Qwen2.5-Coder-14B-Base
- Implement two-stage training: continued pretraining on raw BBj source code, then instruction fine-tuning on ChatML examples
- Upgrade toolchain: Unsloth 2026.1.4 (replaces raw PEFT), fix bitsandbytes QLoRA memory bug
- Clean bbjllm dataset: deduplicate ~375 entries, fix ~60 formatting issues
- Build training data conversion pipeline: training-data/ Markdown to ChatML JSONL
- Export to GGUF (Q4_K_M quantization) and deploy via Ollama

### IDE Integration Next Steps (from Chapter 4)
- FIM fine-tuning on BBj source code for tab completion support
- Continue.dev integration: connect fine-tuned BBj model for chat (instruction-tuned) and autocomplete (FIM-trained)
- Ghost text completion via InlineCompletionItemProvider with Langium semantic context
- Generation detection in the Langium parser
- Semantic context API for enriched LLM prompts
- Compiler validation in the completion pipeline (generate-validate-fix loop)

### MCP / Infrastructure Next Steps (from Chapters 2, 5)
- Implement generate_bbj_code MCP tool (requires operational fine-tuned model)
- Expand MCP tool ecosystem for deeper IDE integration

## Claude's Discretion Recommendations

### TL;DR Rewrite
**Recommendation:** Brief, progress-focused summary. Something like: "Seven milestones delivered. The RAG knowledge system, MCP server, web chat, documentation site, and language server are operational. Fine-tuning research has identified the path forward: Qwen2.5-Coder-14B-Base with evaluation via the BBj compiler. This chapter summarizes what exists and what comes next."

Key points for the TL;DR:
- Emphasize delivered work, not a plan
- Name the operational components
- Mention the forward direction briefly
- No phases, timelines, or costs

### Component Summary Ordering
**Recommendation:** Order by visibility/impact to a technical reader:

1. **Language server** -- most mature component, 508 commits, operational on Marketplace
2. **RAG knowledge system** -- backbone of retrieval, 51K+ chunks
3. **MCP server** -- integration layer, 2 operational tools
4. **Web chat** -- user-facing capability
5. **Documentation site** -- where the reader is right now
6. **Compiler validation** -- cross-cutting capability
7. **Fine-tuning research** -- active research, forward-looking

**Alternative:** Order by status (operational first, then operational for internal exploration, then active research). This mirrors Phase 32 status conventions and creates a natural progression from "what's done" to "what's in progress."

**Recommendation:** Use the status-ordered approach. It creates a natural narrative arc: here's what's running, here's what's being explored, here's what's next.

### Cross-References Section
**Recommendation:** Trim significantly but keep a brief closing paragraph. The current cross-references section (lines 299-311) is 13 lines listing all 6 preceding chapters. Other chapters already cross-reference each other extensively (verified: Ch4 line 673, Ch5 line 308, Ch6 line 537 all link to /docs/implementation-roadmap). A brief 2-3 line closing noting the chapter's role in the overall strategy is sufficient.

### Decision Callout Boxes
**Recommendation:** Remove both.

1. **"Acknowledging Existing Work"** (lines 32-37): This justified building the roadmap from current state rather than zero. When the entire chapter IS the current state summary, this meta-justification is unnecessary. The comparison table itself demonstrates the point.

2. **"Hardware Costs Only"** (lines 201-206): This justified omitting staffing costs. The cost section is being cut entirely, so the decision callout for it is also irrelevant.

### Mermaid Diagram
**Recommendation:** Remove. The 4-phase graph (lines 54-69) visualizes a plan that no longer exists. No replacement diagram is needed -- the component summary and forward plan are prose sections that don't benefit from a diagram.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Build verification | Visual inspection | `npm run build` | Catches broken links, malformed admonitions |
| Stale terminology | Manual reading | Grep for "shipped", "production", "MVP", "Phase 1-4" | Ensures speculative language is fully removed |
| Cross-reference consistency | Manual checking | Grep for "/docs/implementation-roadmap" in other chapters | Verify other chapters' links still work |
| Data accuracy | Memory | Read the actual status blocks in Chapters 2-6 | Pull exact numbers and terminology from source chapters |

**Key insight:** This is a deletion-heavy rewrite. The main risk is leaving remnants of the old structure (references to "Phase 1", "MVP checkpoint", cost estimates) rather than failing to add new content.

## Common Pitfalls

### Pitfall 1: Remnant References to the 4-Phase Plan
**What goes wrong:** After cutting 200+ lines, surviving text still references "Phase 1", "MVP checkpoint", or "this roadmap" in the speculative sense.
**Why it happens:** The intro paragraphs and cross-references may contain assumptions about the phase structure.
**How to avoid:** After all cuts, grep the file for: "Phase 1", "Phase 2", "Phase 3", "Phase 4", "MVP", "checkpoint", "roadmap" (verify each occurrence makes sense in context).
**Warning signs:** References to "completing Phase 1 before starting Phase 2" or "stopping at any checkpoint."

### Pitfall 2: Comparison Table with Stale Data
**What goes wrong:** The table is kept but some cells still reference old data (e.g., "Qwen2.5-Coder-7B selected" instead of "14B-Base recommended", "ingestion pipeline built (v1.2)" instead of "51K+ chunks operational").
**Why it happens:** The current table was accurate when written but predates the Phase 32-34 updates.
**How to avoid:** Rebuild every cell from the verified data in this research document. Do not edit the current table -- replace it entirely.
**Warning signs:** Mixed terminology (some cells using Phase 32 conventions, some using old language).

### Pitfall 3: Forward Plan Becomes Another Speculative Roadmap
**What goes wrong:** The "next steps" section grows into phases with timelines, milestones, and dependencies -- recreating the problem being solved.
**Why it happens:** It is natural to want to organize and sequence next steps.
**How to avoid:** Enforce the user's decision: simple bulleted list, no phases, no timelines, no cost estimates. Each bullet should be 1-2 sentences maximum. If a bullet needs a sub-list, it is too detailed.
**Warning signs:** Numbered steps, dependency ordering, timeline estimates, or more than ~15 bullets.

### Pitfall 4: Component Summary Duplicates Status Blocks from Other Chapters
**What goes wrong:** The component summary becomes a copy of the status blocks from Chapters 2-6, creating maintenance burden.
**Why it happens:** The same information lives in both places.
**How to avoid:** Keep the component summary concise (1-2 sentences per component with a cross-reference link). Let the individual chapter status blocks carry the detail. The summary's job is to give a high-level "what exists" picture, not to duplicate the per-chapter detail.
**Warning signs:** Component entries exceeding 3-4 lines each.

### Pitfall 5: Overlong Chapter Despite Cuts
**What goes wrong:** The new sections (component summary, forward plan) expand to fill the space freed by cuts, resulting in a chapter that is barely shorter than the original.
**Why it happens:** More detail feels more valuable.
**How to avoid:** Target 120-140 lines total. The cuts save ~200 lines; the additions should total ~50-80 lines. If the draft exceeds 160 lines, it is too long.
**Warning signs:** Draft is over 160 lines.

### Pitfall 6: YAML Front Matter Description Inconsistency
**What goes wrong:** The YAML `description` field still mentions "Phased implementation plan with MVP checkpoints, infrastructure costs, risk assessment, and success metrics" after all those sections are cut.
**Why it happens:** Front matter is easy to overlook.
**How to avoid:** Update the description as the first task. Something like: "Progress summary and forward plan for the BBj AI strategy -- what has been delivered and what comes next."
**Warning signs:** `npm run build` might not catch this, but a meta description mentioning "risk assessment" when the chapter has no risk section is misleading.

### Pitfall 7: Ch2 "timelines and resource planning" Reference
**What goes wrong:** Chapter 2 (line 388) currently says "the implementation roadmap with timelines and resource planning (Chapter 7)." After this rewrite, Ch7 has no timelines or resource planning.
**Why it happens:** Cross-reference was accurate for the old chapter structure.
**How to avoid:** This is Phase 36 scope (Cross-Chapter Consistency). Do NOT edit Chapter 2 in this phase. But note it as a known stale reference for Phase 36.
**Warning signs:** Editing files outside `docs/07-implementation-roadmap/index.md`.

## Chapter Structure: Recommended Final Layout

```
---
sidebar_position: 7
title: "Implementation Roadmap"
description: "[Updated description]"
---

# Implementation Roadmap

:::tip[TL;DR]
[Rewritten -- progress + plan, ~3-4 sentences]
:::

[Brief intro paragraph -- 2-3 sentences repositioning the chapter]

## Where We Stand

[Comparison table: Paper Status Jan 2025 vs Actual Feb 2026]
[Updated with verified data from Chapters 2-6]

## What We Built

[Component summary organized by status tier]
[1-2 sentences per component + cross-reference link]
[Status terminology: operational / operational for internal exploration / active research]

## What Comes Next

[Simple bulleted list of credible next steps]
[Grouped loosely by area: fine-tuning, IDE integration, infrastructure]
[No phases, timelines, or cost estimates]

## Current Status

:::note[Where Things Stand]
[Standard Phase 32 status block]
:::

[Optional: Brief 2-3 line closing connecting to other chapters]
```

**Estimated total: 120-140 lines.** This is a ~55-60% reduction from the current 311 lines.

### Section Heading: "What We Built" vs "Component Summary"
**Recommendation:** "What We Built" is more natural in the context of a progress chapter. "Component Summary" is more technical. Either works, but "What We Built" pairs well with "What Comes Next" for a clear narrative structure.

## Plan Wave Recommendation

**Single wave.** Unlike Phase 33 (which had complex new content to develop -- evaluation methodology, alignment tax analysis, bbjllm gap analysis), this phase is primarily:

1. Delete ~200 lines of speculative content
2. Rewrite ~25 lines (TL;DR, intro, front matter)
3. Update the comparison table with verified data (~25 lines)
4. Write a concise component summary (~35-45 lines)
5. Write a forward plan bulleted list (~15-25 lines)
6. Rewrite the status block (~10-12 lines)
7. Trim cross-references (~8-12 lines)
8. Full-file verification pass

No new conceptual content. All data comes from the already-updated chapters. A single plan handles this comfortably.

## Cross-Reference Impact

### Incoming Links to Chapter 7

| Source | Link | Context | Impact |
|--------|------|---------|--------|
| Chapter 2 (line 388) | `/docs/implementation-roadmap` | "timelines and resource planning" | **STALE** after rewrite -- Phase 36 scope |
| Chapter 4 (line 673) | `/docs/implementation-roadmap` | "timelines, milestones, and the path from Continue.dev" | **STALE** after rewrite -- Phase 36 scope |
| Chapter 5 (line 308) | `/docs/implementation-roadmap` | "Timeline, phasing, and resource allocation" | **STALE** after rewrite -- Phase 36 scope |
| Chapter 6 (line 537) | `/docs/implementation-roadmap` | "Timeline and phases for building" | **STALE** after rewrite -- Phase 36 scope |

All four incoming references describe Chapter 7 using language from the old speculative structure ("timelines", "phases", "resource planning/allocation"). These references are in OTHER chapters and should NOT be edited in Phase 35. They are Phase 36 (Cross-Chapter Consistency) scope.

### Outgoing Links from Chapter 7

Current outgoing links in the cross-references section (lines 300-309) link to all 6 preceding chapters. These links will still work -- only the surrounding descriptive text needs updating if the cross-references section is kept.

### Anchor Impact

The current chapter has these section anchors:
- `#where-we-stand` -- KEPT (section survives with modifications)
- `#implementation-phases` -- CUT (section removed)
- `#infrastructure-costs` -- CUT (section removed)
- `#risk-assessment` -- CUT (section removed)
- `#success-metrics` -- CUT (section removed)
- `#current-status` -- KEPT (section survives)
- `#cross-references` -- KEPT or trimmed

**No other chapter links to a specific anchor within Chapter 7** (verified via grep). All incoming links point to `/docs/implementation-roadmap` (the page root). So removing sections does not break any incoming anchor links.

## Sources

### Primary (HIGH confidence)

- Direct file inspection: `docs/07-implementation-roadmap/index.md` -- current chapter content (311 lines), all sections inventoried
- Direct file inspection: `docs/02-strategic-architecture/index.md` -- component status data (389 lines)
- Direct file inspection: `docs/03-fine-tuning/index.md` -- fine-tuning status and forward plan data (703 lines)
- Direct file inspection: `docs/04-ide-integration/index.md` -- IDE integration status and forward plan data (674 lines)
- Direct file inspection: `docs/05-documentation-chat/index.md` -- documentation chat status data (309 lines)
- Direct file inspection: `docs/06-rag-database/index.md` -- RAG system status data (538 lines)
- Direct file inspection: `.planning/phases/35-implementation-roadmap/35-CONTEXT.md` -- user decisions
- Direct file inspection: `.planning/STATE.md` -- project state and accumulated decisions
- Direct file inspection: `.planning/phases/33-fine-tuning-chapter-rewrite/33-RESEARCH.md` -- Phase 32/33 conventions pattern

### Secondary (MEDIUM confidence)

- Grep results across docs/ directory -- all cross-reference instances to/from Chapter 7 catalogued

### Tertiary (LOW confidence)

- None

## Metadata

**Confidence breakdown:**
- Current chapter analysis: HIGH -- direct file inspection of every section
- Accurate data for comparison table: HIGH -- verified against current chapter status blocks
- Accurate data for component summary: HIGH -- verified against current chapter status blocks
- Forward plan items: HIGH -- drawn from specific sections in Chapters 3 and 4
- Claude's Discretion recommendations: MEDIUM -- editorial judgment, but informed by chapter patterns
- Line count estimates: MEDIUM -- based on similar chapter structures but actual length depends on execution

**Research date:** 2026-02-06
**Valid until:** 2026-03-06 (documentation editing task; findings stable unless chapter files change)
