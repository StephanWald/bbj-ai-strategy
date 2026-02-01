# Project Research Summary

**Project:** BBj AI Strategy -- v1.3 MCP Architecture Documentation Update
**Domain:** Technical strategy documentation update for existing 7-chapter Docusaurus site
**Researched:** 2026-02-01
**Confidence:** HIGH

## Executive Summary

The v1.3 milestone updates an existing 7-chapter BBj AI Strategy site to document MCP (Model Context Protocol) server architecture as the concrete integration mechanism connecting RAG search, fine-tuned code generation, and compiler validation. This is NOT a greenfield project -- it is a surgical documentation update that weaves MCP concepts into existing chapters without contradicting the independently-researched v1.0 content or replacing the established two-layer architecture narrative.

The research reveals three critical success factors: (1) MCP must be framed as the concrete realization of Chapter 2's "unified infrastructure" promise, not a replacement architecture; (2) compiler validation via `bbjcpl -N` is the strongest technical differentiator and must be documented with concrete working proof (the bbjcpltool); (3) technology recommendations in new content must align with published chapters, not the outdated original strategy paper. The existing Docusaurus configuration (Mermaid diagrams, BBj syntax highlighting, Tabs component) already supports all needed presentation patterns -- no new npm dependencies required.

The recommended approach: update Chapter 2 first (MCP architecture definitions that other chapters reference), then Chapter 4 (compiler validation module, the most substantial new content), then Chapters 5, 3, 6 in parallel (cross-references and MCP tool integration), and finally Chapter 7 (roadmap phase updates). The highest risk is technology contradictions between the outdated MCP concept paper recommendations (CodeLlama, Qdrant implied) and the published chapters (Qwen2.5-Coder, pgvector documented). All new BBj code must pass `bbjcpl -N` validation before publishing.

## Key Findings

### Recommended Stack

The MCP architecture content requires NO new technology stack -- it documents how existing components (Qwen2.5-Coder via Ollama, pgvector RAG database, bbjcpl compiler) are exposed through MCP tools. The stack analysis focused on documentation presentation technologies and MCP SDK patterns.

**Core documentation technologies (already configured):**
- **Docusaurus 3.9.2** with Mermaid theme -- Already installed and configured. Supports all needed diagram types (graph TB/LR, sequenceDiagram) with consistent styling.
- **Prism syntax highlighting** -- Already configured for TypeScript, JSON, BBj, Bash. New MCP code examples use existing language tokens.
- **Mermaid diagrams** (v3.6+ architecture support) -- Use existing `graph TB`/`graph LR` patterns, NOT `architecture-beta`. Maintain visual consistency with established color palette.
- **Docusaurus Tabs component** (built-in) -- No installation needed. Use for showing MCP tool definitions in TypeScript vs JSON-RPC wire format.

**MCP protocol references (for documentation accuracy):**
- **MCP Specification 2025-11-25** -- Current stable version. Protocol is managed by Linux Foundation AAIF. Cite this version in documentation.
- **MCP TypeScript SDK v1.25.2** -- Current SDK version for code examples. Shows `registerTool()` patterns with Zod schemas. v2 anticipated Q1 2026 but v1.x remains supported.
- **JSON-RPC 2.0** -- MCP's transport protocol. Mention once, link to spec, do not explain in depth.

**Technology alignment requirements (CRITICAL):**
- Use Qwen2.5-Coder-7B (Ch3 documented), NOT CodeLlama (original paper)
- Reference pgvector (Ch6 documented), NOT Qdrant
- Reference Ollama OpenAI-compatible API (Ch3 documented)
- All MCP tool backends map to existing v1.0/v1.2 stack decisions

### Expected Features

The research identified "features" as content elements that readers expect when MCP architecture is introduced into existing strategy documentation.

**Must have (table stakes):**
- MCP server architecture diagram showing host/client/server topology with the three BBj tools
- Tool definitions with JSON schemas for `search_bbj_knowledge`, `generate_bbj_code`, `validate_bbj_syntax`
- Generate-validate-fix loop diagram (sequence or flowchart) showing compiler-in-the-loop pattern
- Updated "Current Status" blocks across all 7 chapters reflecting v1.2 (RAG pipeline shipped) and v1.3 (MCP architecture)
- Cross-references from Ch3-6 to Ch2's MCP architecture definitions
- Compiler validation section in Ch4 with `bbjcpl -N` integration pattern
- bbjcpltool proof-of-concept documentation proving compiler-in-the-loop works today

**Should have (differentiators):**
- "Why compiler validation changes everything" narrative -- distinguishes BBj strategy from generic RAG+fine-tuning approaches
- Defense-in-depth architecture framing -- RAG (context quality) + Model (generation quality) + Compiler (correctness guarantee) as layered validation
- webforJ MCP precedent reference -- establishes organizational pattern consistency
- Named integration patterns (Generate-Validate-Fix Loop, Documentation Query, Code Review/Migration)
- Deployment flexibility section -- stdio for local, Streamable HTTP for team/remote
- MCP client compatibility table -- any MCP-enabled host (Claude, Cursor, VS Code, etc.) can use BBj tools

**Defer (out of scope for v1.3):**
- MCP server source code or implementation guide -- this is strategy documentation, not a tutorial
- MCP Resources and Prompts (beyond the three tools defined)
- Multi-agent orchestration patterns -- not part of BBj strategy
- Agentic RAG or query routing -- explicitly out of scope per PROJECT.md
- Security/authentication implementation details -- acknowledge as deployment consideration, do not design
- MCP SDK language choice (Python vs TypeScript vs Java) -- implementation decision, not strategy decision
- New standalone Chapter 8 for MCP -- PROJECT.md explicitly rejected this
- JSON Schema rendering plugin -- overkill for 3 tool schemas shown as code blocks

### Architecture Approach

The MCP integration follows a "woven integration" pattern: MCP content is distributed across the existing 7-chapter structure based on each chapter's narrative focus. Chapter 2 establishes the architecture vocabulary; Ch4 and Ch5 demonstrate concrete applications; Ch3, Ch6, and Ch7 get cross-reference updates.

**Major content updates by chapter:**

1. **Chapter 2 (Strategic Architecture)** -- MAJOR REWRITE (~60% updated)
   - Replace abstract "shared foundation" diagram with MCP-centered topology (Host -> Client -> MCP Server -> {RAG DB, Ollama, bbjcpl})
   - Add three-tool overview with JSON schema definitions
   - Add generate-validate-fix loop as signature architectural pattern
   - Frame MCP as the concrete realization of existing two-layer model (not a replacement)
   - Add deployment options (stdio vs Streamable HTTP)
   - Reference webforJ MCP precedent for organizational consistency
   - Update "Current Status" to reflect bbjcpltool proof-of-concept

2. **Chapter 4 (IDE Integration)** -- MAJOR ADDITION (~40% new content)
   - NEW SECTION: "Compiler Validation: Ground-Truth Syntax Checking" (~150-180 lines)
   - Document `bbjcpl -N` as validation oracle, error format, generate-validate-fix loop within IDE completion
   - NEW SUBSECTION: bbjcpltool proof-of-concept (~50-80 lines) -- what it proved, how MCP `validate_bbj_syntax` tool generalizes it
   - Update ghost text architecture diagram with compiler validation step
   - Note: any MCP-enabled host (not just VS Code extension) can use BBj tools
   - Research citations: LLMLOOP, Clover, ProCoder validate compiler-in-the-loop as industry pattern

3. **Chapter 5 (Documentation Chat)** -- MODERATE UPDATE (~20% updated, ~5% new)
   - Reframe chat backend as MCP client calling `search_bbj_knowledge` tool
   - Update sequence diagram to show MCP tool call in flow
   - Two-tier framing: "Quick start: any MCP client" vs "Optimized: custom chat with generation-aware UX"
   - Reference Ch2's Documentation Query integration pattern

4. **Chapters 3, 6** -- LIGHT UPDATE (~5% cross-references + status)
   - Ch3: Fine-tuned model accessed via MCP `generate_bbj_code` tool (brief mention)
   - Ch6: RAG retrieval function exposed as `search_bbj_knowledge` tool (brief mention)
   - Both: Update status blocks to reflect v1.2 RAG pipeline completion and v1.3 MCP integration

5. **Chapter 7 (Implementation Roadmap)** -- MODERATE UPDATE (~15% phase updates)
   - Add MCP deliverables to phases: Phase 2 (MCP server + compiler validation), Phase 3 (MCP RAG search tool)
   - Update risk assessment: compiler validation mitigates "LLM hallucinates BBj syntax" risk
   - Update success criteria to include MCP tool call success rate
   - Update "Where We Stand" table with MCP row

6. **Chapter 1** -- NO UPDATE
   - Problem statement remains unchanged. MCP is part of solution, not problem definition.

**Dependency ordering:**
```
Ch2 (defines MCP vocabulary) --> {Ch4, Ch5} (apply MCP patterns) --> {Ch3, Ch6} (cross-references) --> Ch7 (synthesizes)
```

**Content distribution rationale:**
- Ch2 and Ch4 account for ~70% of work (architecture definition + compiler validation)
- Ch5 and Ch7 account for ~20% (MCP reframing + roadmap updates)
- Ch3 and Ch6 are lightweight (~10%, cross-references only)

**Architectural patterns to document:**
- Three-tool MCP server as the orchestration layer (not a new architectural layer -- the interface between existing layers)
- Generate-validate-fix loop: LLM generates -> compiler validates -> if errors, LLM fixes with feedback -> repeat
- MCP transport mapping: stdio for local dev, Streamable HTTP for team deployment
- Defense-in-depth validation chain: RAG provides context, Model generates code, Compiler guarantees correctness

### Critical Pitfalls

1. **Technology Recommendation Contradictions (CRITICAL - affects all chapters)**
   - Original MCP concept paper may reference CodeLlama or Qdrant. Published chapters (v1.0) independently researched and chose Qwen2.5-Coder-7B (Ch3) and pgvector (Ch6) with documented rationale.
   - If new MCP content uses outdated recommendations, readers encounter contradictions that destroy site credibility.
   - **Prevention:** Create technology alignment table BEFORE writing. Grep all new content for technology names and verify consistency with published chapters. Resolution: always use published chapter recommendations, never original paper.

2. **The "Two Architecture" Problem (CRITICAL - Chapter 2)**
   - Existing Ch2 presents two-layer architecture (Apps -> Shared Foundation). MCP introduces orchestration layer (Apps -> MCP Server -> Foundation components).
   - If framed as replacing the original architecture, breaks established narrative and confuses readers.
   - **Prevention:** Frame MCP as "concrete realization" of existing architecture, not replacement. Keep existing sequence diagram, add second one showing MCP-mediated flow. MCP server belongs WITHIN "Shared Foundation" subgraph as the interface boundary, not as a new layer above it.

3. **Stale "Current Status" Blocks (CRITICAL - all 7 chapters)**
   - Every chapter has dated status blocks (January 2026). v1.2 shipped RAG pipeline (5,004 lines, 310 tests). v1.3 adds MCP. Status blocks reference each other across chapters.
   - If MCP content added but status blocks not updated, chapters claim "RAG not yet built" while describing MCP RAG tools.
   - **Prevention:** Update all status blocks in single pass AFTER content changes. Create status block inventory mapping current claims to v1.2/v1.3 reality. Final consistency check: grep for "not yet built" and verify each claim is still accurate.

4. **Unvalidated BBj Code in MCP Examples (CRITICAL - Ch2, Ch4)**
   - v1.1 milestone corrected hallucinated BBj syntax across 6 chapters (fabricated `WINDOW CREATE` syntax replaced with correct mnemonics). Same risk exists for new MCP content.
   - A chapter about compiler validation containing code that fails compiler validation is credibility catastrophe.
   - **Prevention:** Run ALL BBj code blocks through `bbjcpl -N` before publishing. For generate-validate-fix examples, actually run the loop -- write wrong code, confirm compiler rejection, document actual error output, write corrected version. Use GuideToGuiProgrammingInBBj.pdf and bbj-reference.md as authoritative sources.

5. **bbjcpltool Implementation Coupling (CRITICAL - Ch4)**
   - bbjcpltool is a separate project at `/Users/beff/bbjcpltool/` with its own lifecycle. Documenting its implementation details (file paths, hook scripts) creates hard dependency that breaks when bbjcpltool changes.
   - **Prevention:** Document the PATTERN (compiler-in-the-loop validation), not the implementation. Reference bbjcpltool as proof-of-concept evidence, not the architecture itself. ONE paragraph mentioning what it proved. NO file paths, NO hook script source code. MCP `validate_bbj_syntax` tool definition is the strategic implementation.

## Implications for Roadmap

Based on research, the v1.3 milestone should follow this phase structure:

### Phase 1: Chapter 2 Update (Strategic Architecture)
**Rationale:** Ch2 defines the MCP vocabulary (tool names, architecture topology, generate-validate-fix loop) that all other chapters reference. Must be written first to establish consistent terminology.

**Delivers:**
- MCP server architecture diagram (replaces existing abstract diagram)
- Three tool definitions with JSON schemas: `search_bbj_knowledge`, `generate_bbj_code`, `validate_bbj_syntax`
- Generate-validate-fix loop sequence diagram
- Decision callout: "MCP as Unified Integration Protocol"
- Updated "Current Status" block
- webforJ MCP precedent reference

**Addresses (from FEATURES.md):**
- MCP server architecture diagram (table stakes)
- Tool definitions with schemas (table stakes)
- Generate-validate-fix loop diagram (table stakes)
- webforJ precedent (differentiator)

**Avoids (from PITFALLS.md):**
- Technology contradictions: Use Qwen2.5-Coder, pgvector, Ollama (not CodeLlama, Qdrant)
- Two-architecture problem: Frame MCP as concrete realization of existing two-layer model
- MCP protocol scope creep: ONE paragraph on MCP, link to spec, focus on BBj tools

**Research depth needed:** LOW -- architecture patterns are clear from research, no additional research needed

**Estimated effort:** ~300-400 new/updated lines, ~60% of chapter rewritten

---

### Phase 2: Chapter 4 Update (IDE Integration + Compiler Validation)
**Rationale:** Compiler validation is the most technically novel content and the strongest differentiator. This is the largest content addition after Ch2. Ch4 depends on Ch2's tool definitions but not on other chapters.

**Delivers:**
- NEW SECTION: "Compiler Validation: Ground-Truth Syntax Checking" with `bbjcpl -N` integration pattern
- bbjcpltool proof-of-concept documentation (what it proved, how it validates the pattern)
- Generate-validate-fix loop within IDE completion pipeline
- Updated ghost text architecture diagram with compiler validation step
- Compiler error format documentation (concrete examples)
- Research citations (LLMLOOP, Clover, ProCoder) positioning BBj strategy within industry pattern
- Decision callout: "Compiler Validation via bbjcpl"
- Updated "Current Status" block

**Implements (from ARCHITECTURE.md):**
- Compiler validation module as quality layer between LLM and ghost text
- Defense-in-depth architecture: Langium (parser) + LLM (generation) + Compiler (ground truth)

**Addresses (from FEATURES.md):**
- Compiler validation section in Ch4 (table stakes)
- bbjcpltool proof-of-concept documentation (table stakes)
- "Why compiler changes everything" narrative (differentiator)
- Defense-in-depth architecture framing (differentiator)

**Avoids (from PITFALLS.md):**
- Unvalidated BBj code: Run ALL examples through `bbjcpl -N` before publishing
- bbjcpltool coupling: Document pattern, not implementation; reference as proof-of-concept only
- Narrative overwhelm: Compiler validation is ONE major section, not the chapter's new primary topic

**Research depth needed:** LOW -- compiler integration pattern is demonstrated by bbjcpltool, research validated industry precedent

**Estimated effort:** ~200-250 new lines, ~40% content addition to existing chapter

---

### Phase 3: Chapters 5, 3, 6 Updates (Cross-References + MCP Tool Integration)
**Rationale:** These chapters receive lighter updates (cross-references to Ch2's MCP architecture, MCP tool integration framing). Can be done in parallel after Ch2 and Ch4 are complete. No dependencies on each other.

**Delivers:**

**Chapter 5 (Documentation Chat) -- MODERATE:**
- MCP-based RAG search tool section
- Updated chat architecture sequence diagram with MCP tool call
- Two-tier framing: "Quick start (any MCP client)" vs "Optimized (custom chat)"
- Reference to Ch2's Documentation Query integration pattern
- Updated "Current Status" block
- Estimated: ~100-150 lines

**Chapter 3 (Fine-Tuning) -- LIGHT:**
- Brief mention: fine-tuned model accessed via MCP `generate_bbj_code` tool
- Cross-reference to Ch2's MCP architecture
- Updated deployment diagram (add MCP server in flow)
- Updated "Current Status" block
- Estimated: ~30-50 lines

**Chapter 6 (RAG Database) -- LIGHT:**
- Brief mention: retrieval function exposed as `search_bbj_knowledge` MCP tool
- Cross-reference to Ch2's tool definition
- Update status block: v1.2 RAG pipeline shipped (6 parsers, 310 tests, 5,004 lines)
- Estimated: ~30-50 lines

**Addresses (from FEATURES.md):**
- Cross-references from Ch3-6 to Ch2 MCP architecture (table stakes)
- MCP client compatibility (any MCP-enabled host can use BBj tools) -- mentioned in Ch5
- Updated status blocks reflecting v1.2 and v1.3 (table stakes)

**Avoids (from PITFALLS.md):**
- Stale status blocks: Update ALL three chapters' status in single pass
- Tool definition inconsistency: Reference Ch2's schemas, do not redefine
- Cross-reference chain breaks: Ch2 and Ch4 must be complete before these updates

**Research depth needed:** NONE -- these are cross-reference updates only

**Estimated combined effort:** ~160-250 lines across 3 chapters

---

### Phase 4: Chapter 7 Update (Implementation Roadmap)
**Rationale:** Ch7 synthesizes all other chapters and must be updated LAST to reflect their final state. Updates phase descriptions with MCP deliverables and adjusts risk assessment based on compiler validation mitigation.

**Delivers:**
- Updated phase descriptions: Add MCP server (Phase 2), MCP RAG search tool (Phase 3)
- Updated risk assessment: Compiler validation mitigates "LLM hallucinates BBj syntax" risk
- Updated "Where We Stand" table: Add MCP / compiler validation row
- Updated success criteria: Add MCP tool call success rate metric
- Updated "Current Status" block
- Cost implications: MCP server adds no infrastructure cost (process, not service; compiler is part of BBj installation)

**Addresses (from FEATURES.md):**
- Updated roadmap phase descriptions (table stakes)
- Cross-references to all updated chapters

**Avoids (from PITFALLS.md):**
- Outdated roadmap phases: Update to reflect v1.2 (RAG shipped) and v1.3 (MCP architecture)
- Phase bloat: Add MCP as sub-bullets under existing deliverables, not new top-level deliverables
- Stale status: Final cross-chapter consistency check

**Research depth needed:** NONE -- synthesizes existing chapter updates

**Estimated effort:** ~80-120 lines of phase description and risk updates

---

### Phase 5: Final Consistency Pass
**Rationale:** After all content updates, verify cross-references, status blocks, and styling consistency.

**Delivers:**
- Run Docusaurus build to catch broken links
- Verify all cross-references point to correct content (semantic correctness, not just link validity)
- Grep for technology names (CodeLlama, Qdrant, ChromaDB) to catch contradictions
- Grep for "not yet built" / "not yet" in status blocks to verify accuracy
- Extract all BBj code blocks and validate with `bbjcpl -N`
- Verify all decision callouts use consistent `:::info[Decision: ...]` format with 4 fields
- Verify Mermaid diagrams use consistent color palette and node formatting
- Update landing page chapter descriptions if Ch2 narrative changed
- Update sidebar/frontmatter descriptions

**Avoids (from PITFALLS.md):**
- Technology contradictions
- Stale status blocks
- Unvalidated BBj code
- Decision callout formatting inconsistency
- Diagram style mismatch
- Cross-reference semantic errors

**Research depth needed:** NONE -- quality assurance pass

**Estimated effort:** ~2-3 hours QA testing

---

### Phase Ordering Rationale

- **Ch2 first (blocking):** Defines vocabulary all other chapters use. Cannot write Ch4/Ch5 references to "MCP tool definitions" until Ch2 defines them.
- **Ch4 second (high-value, independent):** Largest content addition, highest differentiator value, depends only on Ch2, not on Ch5/Ch3/Ch6.
- **Ch5, Ch3, Ch6 parallel (lightweight, independent):** All cross-reference Ch2 but not each other. Can be done simultaneously.
- **Ch7 last (blocking):** Synthesizes all chapters, must reflect their final state.
- **Final pass (blocking):** Catches consistency issues across all updates.

**Critical path:** Ch2 -> Ch4 -> {Ch5, Ch3, Ch6} -> Ch7 -> Final Pass

**Parallelization opportunities:** Ch4 can start as soon as Ch2 is drafted (before Ch2 is finalized). Ch5, Ch3, Ch6 can run in parallel.

### Research Flags

**Phases with standard patterns (skip additional research):**
- **Phase 1 (Ch2):** MCP architecture patterns well-documented in official spec and SDK docs. Tool definition format is standardized JSON Schema.
- **Phase 2 (Ch4):** Compiler validation pattern validated by bbjcpltool proof-of-concept and research literature (LLMLOOP, Clover). `bbjcpl -N` integration is straightforward.
- **Phase 3 (Ch5, Ch3, Ch6):** Cross-reference updates, no new technical patterns.
- **Phase 4 (Ch7):** Roadmap synthesis, no new technical content.

**No phases require `/gsd:research-phase` during planning.** All technical patterns are either (a) already documented in existing chapters, (b) validated by bbjcpltool proof-of-concept, or (c) covered by high-confidence research (STACK.md, FEATURES.md, ARCHITECTURE.md).

**Validation checkpoints during execution:**
- After Ch2 draft: Verify no technology contradictions with published chapters (grep for CodeLlama, Qdrant)
- After Ch4 draft: Validate all BBj code examples with `bbjcpl -N`
- After all updates: Cross-reference semantic correctness check

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Docusaurus configuration verified from project source. MCP SDK versions verified via npm/GitHub. No new npm dependencies needed. |
| Features | HIGH | Content requirements derived from chapter analysis and MCP specification. bbjcpltool provides concrete proof-of-concept validation. |
| Architecture | HIGH | Chapter structure and dependencies analyzed from published content. MCP integration pattern validated against official MCP docs and webforJ precedent. |
| Pitfalls | HIGH | Technology contradictions, status block staleness, BBj code validation are all verified project history risks (v1.0, v1.1 milestones documented these). |

**Overall confidence:** HIGH

This is a documentation update to an existing, well-structured site with clear patterns. The MCP integration architecture is validated by bbjcpltool proof-of-concept. The main risks are process-oriented (technology alignment, status updates, cross-reference consistency) rather than technical unknowns. All risks have concrete prevention strategies.

### Gaps to Address

1. **MCP SDK version stability (LOW severity)**
   - MCP TypeScript SDK v2 anticipated Q1 2026. If released during v1.3 development, code examples using v1.x remain valid for 6+ months.
   - **Mitigation:** Keep v1.x examples, add note: "These examples use MCP SDK v1.x. See migration guide for v2."

2. **bbjcpltool publication status (MEDIUM severity)**
   - Documentation references bbjcpltool as proof-of-concept. If bbjcpltool is not published/shareable, external readers cannot verify.
   - **Mitigation:** Reference as "internal proof-of-concept" and focus on the validated pattern (compiler-in-the-loop), not the specific tool implementation. The MCP `validate_bbj_syntax` tool definition is public and tool-agnostic.

3. **Compiler availability edge case (LOW severity)**
   - `bbjcpl` compiler is part of BBj installation. Not all MCP client users will have it installed.
   - **Mitigation:** Mention graceful degradation in Ch2 or Ch4: "The compiler validation tool requires `bbjcpl` in the system PATH. If unavailable, the MCP server can skip validation with a warning, relying on RAG context and model quality alone."

4. **MCP tool naming finalization (LOW severity)**
   - Tool names (`search_bbj_knowledge`, `generate_bbj_code`, `validate_bbj_syntax`) are working names from concept paper.
   - **Mitigation:** Verify naming convention with project stakeholders before publishing. The `bbj_` prefix provides namespace clarity in multi-server environments (matches webforJ pattern).

5. **Chapter length after Ch4 additions (MEDIUM severity)**
   - Ch4 currently 431 lines. Adding ~200-250 lines pushes it past 650 lines, potentially making it too long.
   - **Mitigation:** Consider splitting compiler validation into a sub-page if final length exceeds ~600 lines. Alternatively, trim "Alternative Architectures" section (Continue.dev, Langium AI) which is not core narrative.

## Sources

### Primary (HIGH confidence)
- **MCP Specification 2025-11-25:** [modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification/2025-11-25) -- Protocol version, tool schema format, host/client/server architecture
- **MCP TypeScript SDK v1.25.2:** [npm](https://www.npmjs.com/package/@modelcontextprotocol/sdk), [GitHub](https://github.com/modelcontextprotocol/typescript-sdk) -- `registerTool()` patterns, Zod schema support, current version
- **Published chapters (all 7):** `/Users/beff/_workspace/bbj-ai-strategy/docs/` -- Existing content patterns, technology decisions (Qwen2.5-Coder, pgvector), diagram styles, decision callout formats
- **Project Docusaurus config:** `docusaurus.config.ts` -- Mermaid, BBj syntax, Tabs, search plugins already configured
- **bbjcpltool PROJECT.md:** `/Users/beff/bbjcpltool/.planning/PROJECT.md` -- Proof-of-concept validation, compiler flags, error parsing
- **webforJ MCP server:** [mcp.webforj.com](https://mcp.webforj.com/), [docs](https://docs.webforj.com/docs/introduction/mcp) -- Organizational precedent

### Secondary (MEDIUM confidence)
- **MCP Architecture Overview:** [modelcontextprotocol.io/docs/learn/architecture](https://modelcontextprotocol.io/docs/learn/architecture) -- Host/client/server model, transport layers
- **MCP Best Practices:** [modelcontextprotocol.info](https://modelcontextprotocol.info/docs/best-practices/) -- Single responsibility, focused services, tool naming
- **Compiler-in-the-loop research:**
  - LLMLOOP (ICSME 2025): 76% -> 90% pass@10 improvement via compiler feedback
  - Stanford Clover: Closed-loop verifiable code generation
  - ProCoder: 80%+ improvement with compiler-guided refinement
  - Martin Fowler/Thoughtworks: LLM agents need environment feedback to fix mistakes
- **Docusaurus Diagrams:** [docusaurus.io/docs/markdown-features/diagrams](https://docusaurus.io/docs/markdown-features/diagrams) -- Mermaid integration, theme configuration
- **MCP Governance:** Wikipedia, official blog -- Donated to Linux Foundation AAIF Dec 2025, adopted by OpenAI/Google/Microsoft

### Tertiary (LOW confidence, needs validation)
- Gartner prediction: 75% of API gateway vendors will have MCP features by 2026 (cited in CData blog, not verified against original Gartner report)
- MCP Registry standardization progress (community discussions, no official timeline)

---

*Research completed: 2026-02-01*
*Ready for roadmap: yes*
*Total estimated effort: 740-1,020 new/updated lines across 6 chapters + QA pass*
*Critical path: Ch2 -> Ch4 -> {Ch5,Ch3,Ch6} -> Ch7 -> Final Pass*
*No additional research needed for any phase*
