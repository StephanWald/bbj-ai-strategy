# Domain Pitfalls: MCP Architecture Integration into Existing Documentation

**Domain:** Updating a 7-chapter Docusaurus strategy site to weave MCP server architecture, compiler validation, and ecosystem concepts into existing content
**Researched:** 2026-02-01
**Focus:** v1.3 milestone -- adding MCP architecture across chapters 2-7 without contradicting existing v1.0 content, while referencing an external bbjcpltool proof-of-concept and an original strategy paper with outdated technology recommendations

---

## Critical Pitfalls

Mistakes that cause reader confusion, credibility damage, or require rewriting multiple chapters.

### 1. Technology Recommendation Contradictions Between Old Strategy Paper and Published Chapters

**What goes wrong:** The original strategy paper (`bbj-llm-strategy.md`, January 2025) recommends CodeLlama-7B/13B as the base model and does not mention Qdrant or pgvector by name. The published chapters (v1.0, January 2026) updated these recommendations based on independent research -- Chapter 3 recommends Qwen2.5-Coder-7B, Chapter 6 recommends pgvector over Qdrant. If the MCP concept paper references the original strategy paper's technology choices (CodeLlama, or suggests Qdrant for the MCP server's vector store), the new v1.3 content contradicts the already-published chapters. A reader who reads Chapter 6 (pgvector recommended) and then the new MCP architecture section (mentioning Qdrant) loses confidence in the entire document.

**Why it happens:**
- The MCP concept paper was drafted from the January 2025 strategy paper, which predates the independently-researched chapters
- The original paper listed CodeLlama-7B/13B as a base model candidate; Chapter 3 explicitly superseded this with Qwen2.5-Coder-7B and documented why ("All three have been surpassed by Qwen2.5-Coder on code generation benchmarks")
- Chapter 6 specifically evaluated Qdrant as an alternative and chose pgvector with documented rationale ("sub-millisecond p50 latency differences between pgvector and Qdrant at datasets under 100K vectors")
- If new MCP content is derived from the concept paper without reconciling against the published chapters, it will reintroduce superseded recommendations

**Consequences:**
- The site's credibility rests on consistency -- the "unified infrastructure" message in Chapter 2 promises "one source of truth." Contradictory technology recommendations undermine this exact message
- Readers may choose the wrong technology based on which chapter they read first
- Internal reviewers who remember the original paper will wonder whether the updated recommendations were wrong

**Prevention:**
- Before writing any MCP content, create a technology alignment table that maps every technology mentioned in the concept paper to its current recommendation in the published chapters. Any discrepancy must be resolved in favor of the published chapters (which were independently researched)
- The alignment table for known conflicts:

| Concept Paper Says | Published Chapter Says | Resolution |
|--------------------|----------------------|------------|
| CodeLlama-7B/13B | Qwen2.5-Coder-7B (Ch3) | Use Qwen2.5-Coder-7B. Do not mention CodeLlama in new content. |
| (no vector DB named) | pgvector (Ch6) | MCP RAG tool references pgvector, not Qdrant. |
| "Fine-tuned model" (generic) | Qwen2.5-Coder-7B via Ollama with OpenAI-compatible API (Ch3) | MCP tool definitions reference Ollama endpoints specifically. |

- Any new technology introduced by MCP content (e.g., MCP SDK, transport protocols) should be introduced as additive, never contradicting existing recommendations
- Run a cross-reference check after writing: search all 7 chapters for every technology name mentioned in new content and verify no contradictions exist

**Detection:** After drafting all MCP content, grep all docs/ files for technology names: `Qdrant`, `CodeLlama`, `ChromaDB`, `Weaviate`, `StarCoder`, `DeepSeek`. Any match in new content that contradicts an existing decision callout is a conflict.

**Phase/Chapter:** Must be resolved before writing begins. Affects all chapters receiving MCP updates (Ch2, Ch3, Ch4, Ch5, Ch6, Ch7).

---

### 2. The "Two Architecture" Problem -- MCP Layer Contradicts the Existing Two-Layer Model

**What goes wrong:** Chapter 2 establishes a clear two-layer architecture: "Shared Foundation" (model + RAG) consumed by "Application Layer" (IDE, Chat, Future). This is documented with a specific Mermaid diagram (`graph TB` with `APPS` and `FOUNDATION` subgraphs) and a sequence diagram showing the data flow: App detects context, queries RAG, assembles prompt, calls Model. The MCP server introduces a third conceptual layer -- an orchestration layer between the applications and the foundation -- that manages tool definitions, the generate-validate-fix loop, and compiler validation. If this is presented as replacing or competing with the existing two-layer model, the chapter's core narrative breaks.

**Why it happens:**
- The existing Ch2 architecture is "App calls RAG, App calls Model" -- applications are the orchestrators
- MCP introduces "App calls MCP Server, MCP Server calls RAG/Model/Compiler" -- the MCP server becomes the orchestrator
- These are genuinely different architectures. The existing chapters describe direct integration; MCP describes mediated integration
- Without careful framing, the MCP addition reads as "the original architecture was wrong, here is the real one" -- which undermines the chapters that readers have already internalized

**Consequences:**
- The existing sequence diagram (App -> RAG -> Model -> App) no longer matches the actual proposed flow (App -> MCP Server -> RAG + Model + Compiler -> App)
- Readers who understood the two-layer model now face cognitive dissonance
- The "unified infrastructure" message becomes muddled: is the shared foundation the model+RAG, or is it the MCP server?

**Prevention:**
- Frame MCP as the **concrete realization** of the Chapter 2 architecture, not a replacement. The two-layer model (shared foundation + applications) remains correct; MCP is *how* applications connect to the shared foundation
- The PROJECT.md already contains this framing: "MCP is the integration layer connecting Ch3-6, not a separate initiative; fits as the concrete realization of Ch2's unified architecture promise." Use this exact framing in the content
- Update Chapter 2's architecture diagram to show MCP as the **interface boundary** between layers, not as a new layer. The MCP server exposes tools that map to the existing foundation components:
  - `bbj_rag_search` tool -> RAG Database (Ch6)
  - `bbj_code_generate` tool -> Fine-tuned Model (Ch3)
  - `bbj_compile_check` tool -> BBj Compiler (new, referenced in Ch4)
- Keep the existing sequence diagram but add a second one showing the MCP-mediated flow. Label the first "Direct Integration (simple deployments)" and the second "MCP-Mediated Integration (full orchestration)". Both are valid architectures at different deployment scales
- The "Shared Foundation" subgraph should expand to include the MCP server as a component within it, not above it

**Detection:** After writing Ch2 updates, check whether the original sequence diagram is still present and still accurate for simple deployments. If it was deleted or contradicted, the framing is wrong.

**Phase/Chapter:** Chapter 2 update is the highest-priority, highest-risk chapter change. All other chapters reference Ch2's architecture. Get this right first.

---

### 3. Stale "Current Status" Blocks Across All 7 Chapters

**What goes wrong:** Every chapter has a `:::note[Where Things Stand -- January 2026]` block that describes the project status as of v1.0. These blocks include specific claims like "The ingestion pipeline and vector store have not been built" (Ch6), "Nothing. The documentation chat is a planned capability" (Ch5), and "LLM-powered completions have not yet been integrated" (Ch4). When v1.3 adds MCP content to these chapters, the status blocks must be updated to reflect v1.2 accomplishments (the RAG ingestion pipeline is now built -- 310 tests, 5,004 lines of Python) and v1.3 additions (MCP architecture). If the MCP content is added but the status blocks are not updated, readers encounter a chapter that describes an MCP-orchestrated RAG search tool but whose status section says "ingestion pipeline not yet built."

**Why it happens:**
- Status blocks are easy to overlook when the focus is on adding new architecture content
- v1.2 shipped the RAG ingestion pipeline, but the published chapters were written during v1.0 and never updated for v1.2 accomplishments
- The status blocks reference each other across chapters (Ch2's status table lists component statuses that match Ch3-6 status blocks), creating a dependency chain where updating one block without updating the others creates inconsistency
- Seven chapters with status blocks means seven updates, each needing to be internally consistent and consistent with the others

**Consequences:**
- A chapter says "we now have MCP-based RAG search" but its status block says "RAG pipeline not yet built" -- readers lose trust
- The status table in Chapter 2 (6 rows of component statuses) is a single point of failure: if any row is wrong, technically-minded readers notice
- Chapter 7's implementation roadmap phase descriptions reference Chapter 6's RAG status -- if Ch6 status is updated but Ch7's phase description is not, the roadmap reads as outdated

**Prevention:**
- Create a "Status Block Inventory" before writing any content. For each chapter, extract:
  1. The current status block text
  2. What has changed since v1.0 (v1.2 shipped RAG pipeline; v1.3 adds MCP)
  3. The new status block text
- Update all status blocks in a single pass after all content changes are complete, not during content writing. This ensures consistency
- The following status claims need updating:

| Chapter | Current Claim | Must Update To |
|---------|--------------|----------------|
| Ch1 | "Training data structure defined" | Add MCP/compiler context |
| Ch2 | "Architecture defined" | "Architecture defined. MCP server design in progress." |
| Ch2 Status Table | "RAG database: Schema designed" | "RAG database: Ingestion pipeline built (v1.2). 6 source parsers, 310 tests." |
| Ch3 | "Ollama infrastructure validated" | Add MCP tool integration context |
| Ch4 | "Ghost text completion planned" | Add compiler validation module, bbjcpltool proof-of-concept |
| Ch5 | "Shipped: Nothing" | Add MCP-based RAG search tool as concrete architectural component |
| Ch6 | "Not built: Ingestion pipeline" | "Shipped: Ingestion pipeline with 6 parsers, 310 tests, generation tagging" |
| Ch7 | Phase descriptions reference "not yet built" | Update phase progress to reflect v1.2 and v1.3 |

- Run a final consistency check: grep all `:::note` blocks for the word "not" and verify each "not yet" claim is still accurate

**Detection:** Search all docs/ files for "not yet built", "not yet", "not built", "no infrastructure", "nothing", "planned" in status blocks. Cross-reference each claim against actual project state.

**Phase/Chapter:** Must be addressed as the LAST step of each chapter update (after all content changes), and then verified in a final cross-chapter consistency pass.

---

### 4. Unvalidated BBj Code in MCP Examples

**What goes wrong:** The MCP concept paper likely contains BBj code examples illustrating the generate-validate-fix loop (e.g., "the LLM generates this BBj code, the compiler rejects it because of X, and the corrected version is Y"). If these BBj code examples are published without running them through `bbjcpl -N` (the BBj compiler's syntax-check-only mode), the chapter about compiler validation would itself contain code that does not pass compiler validation. This is the most embarrassing possible failure mode for a chapter whose central thesis is "use the compiler as ground truth."

**Why it happens:**
- The v1.1 milestone corrected hallucinated BBj code across 6 chapters (replaced fabricated `WINDOW CREATE`/`BUTTON CREATE` syntax with correct mnemonic syntax). This proves that BBj code examples are a known failure mode in this project
- The MCP concept paper may have been drafted by an LLM (or human unfamiliar with BBj), introducing the same kinds of hallucinations the v1.1 corrections addressed
- BBj's mnemonic syntax is counterintuitive -- `print (sysgui)'window'(x,y,w,h,title$,flags$,eventmask$)` -- and easy to get wrong in manual examples
- The original strategy paper already contained an incorrect Visual PRO/5 example: `WINDOW CREATE wnd_id, @(0,0), 80, 24, "Title"` which is fabricated VB-style syntax, not actual BBj

**Consequences:**
- A chapter titled "Compiler Validation" that contains code the compiler rejects is a credibility catastrophe
- Readers testing the examples will immediately discover the error, which undermines the entire strategy's premise
- The error will persist on the public site (stephanwald.github.io/bbj-ai-strategy) until manually discovered and corrected

**Prevention:**
- The v1.3 requirements already state: "All new BBj code samples compiler-validated before publishing." Enforce this literally
- For every BBj code block in new MCP content, run `bbjcpl -N <file>` before publishing. The `-N` flag performs syntax checking without execution
- The bbjcpltool proof-of-concept at `/Users/beff/bbjcpltool/` provides the PostToolUse hook infrastructure for automated validation. Use it during content authoring
- Keep the BBj language reference at `~/.claude/bbj-reference.md` loaded during content generation to ensure correct syntax
- For the generate-validate-fix loop examples specifically: actually run the example through the loop. Write the deliberately-wrong BBj code, confirm the compiler rejects it for the right reason, write the corrected version, confirm it passes. Document the actual compiler output, not a fabricated error message
- Use the GuideToGuiProgrammingInBBj.pdf (project root) as the authoritative reference for any BBj GUI examples in MCP content

**Detection:** After writing each chapter, extract all fenced code blocks with `bbj` language identifier. Run each through `bbjcpl -N`. Any non-zero exit code means the code is wrong.

**Phase/Chapter:** Applies to Ch2 (if BBj examples in architecture), Ch4 (compiler validation module examples), and any other chapter with new BBj code.

---

### 5. Creating a Hard Dependency on bbjcpltool (a Separate Project)

**What goes wrong:** The bbjcpltool proof-of-concept lives at `/Users/beff/bbjcpltool/` -- a separate project with its own lifecycle. When Chapter 4 describes compiler validation, the natural impulse is to reference bbjcpltool's implementation details, link to its source code, or describe its internal architecture. If the documentation creates a hard dependency on bbjcpltool's current implementation (referencing specific file paths, API shapes, or version numbers), any future change to bbjcpltool breaks the documentation. Worse, if bbjcpltool is abandoned or significantly refactored, the chapters become inaccurate.

**Why it happens:**
- bbjcpltool is the only concrete proof-of-concept for compiler validation. It is tempting to document it extensively because it validates the concept
- The PROJECT.md already describes bbjcpltool's internals: "PostToolUse hook runs `bbjcpl -N` on every `.bbj` file Claude writes/edits, plus shared BBj language reference at `~/.claude/bbj-reference.md`"
- Without bbjcpltool, the compiler validation section would be entirely theoretical, which weakens the chapter
- Documentation writers naturally want to show concrete evidence rather than abstract patterns

**Consequences:**
- If bbjcpltool changes its hook mechanism, the documentation describes a non-existent implementation
- If bbjcpltool is not open-source or not published, external readers cannot verify the referenced implementation
- The strategy documentation becomes coupled to a PoC's implementation details rather than the validated concept

**Prevention:**
- Document the **concept and pattern**, not the implementation. The valuable insight is "use the BBj compiler (`bbjcpl -N`) as a ground-truth syntax validator in the AI feedback loop." This is tool-agnostic
- Reference bbjcpltool as **evidence that the pattern works**, not as the pattern itself. Example framing: "A proof-of-concept (bbjcpltool) validates this approach: it hooks into Claude Code's PostToolUse event and runs `bbjcpl -N` on every `.bbj` file the AI writes. This confirms that compiler-in-the-loop validation is practical, not just theoretical."
- Keep bbjcpltool references at the mention level, not the implementation-detail level:
  - YES: "A working proof-of-concept confirms the generate-validate-fix loop is practical."
  - YES: "The PoC uses `bbjcpl -N` (syntax-check-only mode) to validate AI-generated BBj code."
  - NO: "The PostToolUse hook in `/Users/beff/bbjcpltool/hooks/post-tool-use.sh` runs..."
  - NO: "The shared BBj language reference at `~/.claude/bbj-reference.md` contains..."
- Do not link to bbjcpltool's repository unless it is published and stable. If it is not published, reference it as "internal proof-of-concept" without URLs
- Define the compiler validation pattern abstractly in Chapter 4, then note that bbjcpltool validates the concept. The MCP server's `bbj_compile_check` tool definition is the strategic implementation; bbjcpltool is the tactical PoC

**Detection:** After writing Ch4 updates, search for any file paths containing "bbjcpltool", "~/.claude/", or absolute paths. These indicate implementation coupling.

**Phase/Chapter:** Chapter 4 (compiler validation section). Also affects Chapter 2 if the MCP architecture diagram references bbjcpltool directly.

---

## Moderate Pitfalls

Mistakes that cause confusion, reduce content quality, or create technical debt in the documentation.

### 6. Mermaid Diagram Style Inconsistency Across Chapters

**What goes wrong:** The existing 7 chapters contain 11 Mermaid diagrams using consistent patterns: `graph TB`/`graph LR` with subgraphs, `sequenceDiagram` for request flows, styled with fill colors from a consistent palette (`#e8f4e8`, `#e8e8f4`, `#f4e8e8`, `#f0f0f0`), and HTML-formatted node labels using `<b>` and `<br/>`. New MCP diagrams that use different styling (different colors, different node shapes, different layout directions, no subgraph structure) look visually inconsistent and signal to readers that the new content was bolted on rather than integrated.

**Why it happens:**
- The concept paper's diagrams were likely created independently from the published chapters
- Mermaid does not enforce style consistency across files -- each diagram is self-contained
- The existing style patterns are implicit (there is no documented diagram style guide in the project)
- Different authors or AI agents producing content will naturally use different Mermaid conventions

**Prevention:**
- Extract the existing diagram style conventions into a checklist before writing new diagrams:

| Convention | Examples in Published Chapters |
|-----------|-------------------------------|
| Layout direction | `graph TB` for hierarchical, `graph LR` for sequential/pipeline |
| Subgraph labels | ALL CAPS: `APPS`, `FOUNDATION`, `Fine-Tuning`, `Conversion`, `Deployment` |
| Node labels | HTML format: `<b>Bold Title</b><br/>Description<br/><i>Detail</i>` |
| Fill colors | Green: `#e8f4e8,stroke:#2d8a2d`, Blue: `#e8e8f4,stroke:#2d2d8a`, Red: `#f4e8e8,stroke:#8a2d2d`, Yellow: `#f4f4e8,stroke:#8a8a2d`, Gray: `#f0f0f0,stroke:#333` |
| Sequence diagrams | `participant` with `<br/>` for multi-line labels |
| Arrow style | Default solid arrows (no custom styling) |

- New MCP diagrams must use the same color palette and node formatting. If the MCP server is a new component type, assign it a color from the existing palette (e.g., green for infrastructure components, blue for data stores)
- When updating Chapter 2's architecture diagram, modify the existing diagram rather than replacing it wholesale. Add MCP nodes to the existing subgraph structure

**Detection:** Visually compare new diagrams against existing ones when rendered. Check for consistent fill colors, node label formatting, and layout conventions.

**Phase/Chapter:** All chapters receiving new diagrams. Most critical for Chapter 2 (the main architecture diagram) and Chapter 4 (the IDE integration diagram).

---

### 7. MCP Content Overwhelms the Original Chapter Narratives

**What goes wrong:** Each chapter has a clear narrative arc. Chapter 2 argues "unified infrastructure beats point solutions." Chapter 4 argues "two-layer completion (Langium + LLM) gives correctness and creativity." Chapter 5 argues "generic chat fails, shared infrastructure succeeds." When MCP content is added, it can hijack these narratives -- Chapter 4 becomes primarily about MCP tool orchestration instead of IDE completion, or Chapter 2 becomes an MCP explainer instead of a strategic architecture argument. The original value of each chapter is diluted.

**Why it happens:**
- MCP is the exciting new concept. The temptation is to lead with it
- The generate-validate-fix loop is technically interesting and gets over-documented relative to its importance in each chapter's narrative
- Each chapter update adds MCP content, but nothing is removed. The chapters grow longer without the narrative being reorganized
- MCP touches every chapter, so there is no single "home" for MCP content -- it spreads across all of them

**Consequences:**
- Readers opening Chapter 4 for "How does IDE integration work?" find themselves reading about MCP tool definitions before they understand the Langium + LLM architecture
- The chapters lose their accessibility for the non-MCP-expert reader
- The site's 3-audience design (developers, leadership, customers) is compromised because MCP orchestration details are developer-only content shoved into leadership-accessible chapters

**Prevention:**
- Define the MCP content allocation budget per chapter BEFORE writing:

| Chapter | MCP Content Scope | Max Addition |
|---------|------------------|--------------|
| Ch2 (Architecture) | MCP as the integration protocol between layers. Tool definitions. | 1 new section + updated diagram |
| Ch3 (Fine-Tuning) | Cross-reference to MCP code generation tool. Minor update. | 1-2 paragraphs + updated status |
| Ch4 (IDE Integration) | Compiler validation module. Generate-validate-fix loop. bbjcpltool reference. | 1 new major section |
| Ch5 (Doc Chat) | MCP-based RAG search tool definition. | 1 new section showing how chat uses MCP tools |
| Ch6 (RAG Database) | Cross-reference to MCP search tool. v1.2 status update. | 1-2 paragraphs + updated status |
| Ch7 (Roadmap) | Updated phases reflecting MCP. Revised timeline. | Phase descriptions updated, not new phases |

- Each chapter's MCP addition should follow this structure: (1) introduce the MCP concept relevant to THIS chapter in 1-2 paragraphs, (2) show the specific tool definition or pattern, (3) connect back to the chapter's existing narrative
- Lead with the chapter's existing narrative, not with MCP. MCP is a "how," not a "what"
- Do NOT create a standalone "MCP Architecture" section that could be its own chapter. The PROJECT.md already decided against this: "MCP is the integration layer connecting Ch3-6, not a separate initiative"

**Detection:** After all updates, measure the word count of new MCP content versus existing content in each chapter. If MCP content exceeds 30% of the chapter's total, it has likely overwhelmed the narrative.

**Phase/Chapter:** Primarily Chapter 2 and Chapter 4, which receive the most MCP content.

---

### 8. Cross-Reference Chain Breaks When Chapters Are Updated Out of Order

**What goes wrong:** The 7 chapters form a densely cross-referenced web. Chapter 2 links to Ch3-6. Chapter 4 references Ch2's architecture and Ch3's model. Chapter 5 references Ch4's shared infrastructure and Ch6's RAG. When chapters are updated in the wrong order, new cross-references point to content that does not exist yet. If Chapter 5 is updated to reference "the MCP-based RAG search tool defined in Chapter 2" but Chapter 2 has not been updated yet, the link points to missing content. If Chapter 4 references "the compiler validation architecture described in Chapter 2's MCP section" but Ch2 was written differently than expected, the reference is wrong.

**Why it happens:**
- Multiple chapters need MCP content simultaneously, but they cannot all be written at the same time
- Cross-references are written prospectively ("Chapter 2 will describe X") based on assumptions about what other chapters will contain
- The chapters were originally written in sequence (v1.0), so their cross-references are well-tested. New cross-references added during simultaneous updates have no such testing
- Docusaurus builds catch broken links but not semantically incorrect references (a link to Ch2 that exists but does not discuss MCP tools is technically valid but semantically broken)

**Prevention:**
- Update chapters in dependency order:
  1. **Chapter 2 first** -- it defines the architecture that all other chapters reference. Until Ch2's MCP section is written and stable, other chapters cannot safely cross-reference it
  2. **Chapter 4 second** -- it introduces compiler validation, which Ch2 and Ch7 reference
  3. **Chapters 3, 5, 6** -- these receive lighter MCP updates and reference Ch2 and Ch4
  4. **Chapter 7 last** -- the roadmap synthesizes all other chapters and must reflect their final state
- Define the MCP terminology and anchor IDs in Chapter 2 before writing other chapters. If Ch2 will have a section called "MCP Tool Definitions" with anchor `#mcp-tool-definitions`, communicate this to all other chapter updates so they can link correctly
- After all chapters are updated, run `npm run build` (Docusaurus build) which reports broken markdown links. Also manually verify that cross-referenced content actually discusses what the referencing text claims

**Detection:** Docusaurus build reports broken links. For semantic correctness, search for "Chapter 2" or "strategic-architecture" in new content and verify each reference describes content that actually exists in Ch2.

**Phase/Chapter:** This is a process pitfall, not a content pitfall. Must be addressed in the roadmap phase ordering.

---

### 9. MCP Protocol Explanation Scope Creep

**What goes wrong:** MCP (Model Context Protocol) is a real, evolving standard with its own specification, SDKs, transport protocols, security model, and ecosystem. When documenting a BBj MCP server, the temptation is to explain MCP itself: "MCP is a protocol by Anthropic that uses JSON-RPC 2.0 over stdio or HTTP transport..." This turns the BBj strategy documentation into an MCP tutorial, which is not its purpose and will become outdated as MCP evolves.

**Why it happens:**
- Readers may not know what MCP is, so the author feels obligated to explain it
- MCP was donated to the Linux Foundation's Agentic AI Foundation (AAIF) in December 2025 and adopted by OpenAI, Google, and others -- there is a lot to say
- The protocol has multiple transports (stdio, streamable HTTP), security features, and primitives (tools, resources, prompts, sampling) that are technically interesting
- Without careful scoping, explaining "why MCP" becomes "what is MCP" becomes "how MCP works internally"

**Consequences:**
- The chapter balloons with MCP protocol details that belong in MCP's own documentation
- When MCP releases a new version, the protocol explanation is outdated but the BBj tool definitions remain valid
- Readers interested in the BBj strategy must wade through MCP protocol details to find the BBj-specific content

**Prevention:**
- Limit MCP explanation to ONE introductory paragraph per chapter, maximum. Example: "The BBj AI Development Assistant exposes its capabilities through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), an open standard for connecting AI applications to external tools and data sources. MCP defines a client-server architecture where AI hosts (Claude, Copilot, etc.) connect to tool servers that expose structured capabilities."
- Everything beyond this paragraph should be BBj-specific: the tool definitions, the generate-validate-fix loop, the deployment options
- Link to the official MCP documentation for protocol details rather than reproducing them
- Frame MCP as a solved infrastructure problem, not a novel concept that needs explaining. The reader needs to understand "the BBj MCP server exposes three tools" -- they do not need to understand MCP's JSON-RPC layer
- Use the existing content pattern: when Chapter 3 introduced QLoRA, it explained the concept in 2 paragraphs then focused on how it applies to BBj. Do the same for MCP

**Detection:** After writing MCP sections, count paragraphs that explain MCP-the-protocol versus paragraphs that describe BBj-specific MCP tools. If the ratio is more than 1:3 (protocol:BBj), the scope has crept.

**Phase/Chapter:** Chapter 2 (MCP architecture introduction) and Chapter 4 (MCP tool integration). Chapter 5 should reference Ch2's MCP introduction, not re-explain it.

---

### 10. Decision Callout Formatting Breaks or Is Inconsistent

**What goes wrong:** Every published chapter uses a specific pattern for decisions: `:::info[Decision: Title Here]` with fields for Choice, Rationale, Alternatives considered, and Status. New MCP content introduces decisions (e.g., "Decision: MCP as Integration Protocol") but uses inconsistent formatting -- missing the Status field, using different admonition types (`:::note` instead of `:::info`), or using a different field structure. The visual inconsistency signals "different author, different quality standard" and breaks the site's professional appearance.

**Why it happens:**
- The decision callout format is an implicit convention, not enforced by tooling
- The Docusaurus `:::info[...]` admonition syntax is easy to get slightly wrong
- Authors focused on technical content may treat formatting as secondary
- If content is generated by AI, the AI may approximate but not exactly match the existing pattern

**Prevention:**
- Use this exact template for every new decision callout:

```markdown
:::info[Decision: {Title}]
**Choice:** {One sentence stating what was decided.}

**Rationale:** {Why this choice was made, with evidence.}

**Alternatives considered:** {What was rejected and why.}

**Status:** {Current state -- e.g., "Architecture defined. Implementation planned."}
:::
```

- New MCP decisions that need callouts:
  - "Decision: MCP as the Unified Integration Protocol" (Ch2)
  - "Decision: Compiler Validation via bbjcpl" (Ch4)
  - "Decision: MCP Tool Definitions for RAG Search" (Ch5)
- Each new decision callout should be reviewed against an existing one (e.g., the "Decision: Unified Infrastructure Over Point Solutions" in Ch2) for formatting consistency
- TL;DR blocks (:::tip[TL;DR]) also need updating for chapters that receive significant new content

**Detection:** After all updates, search for `:::info[Decision` and verify each instance has all four fields (Choice, Rationale, Alternatives considered, Status).

**Phase/Chapter:** All chapters receiving new decisions.

---

### 11. Outdated Implementation Roadmap Phase Descriptions

**What goes wrong:** Chapter 7's four-phase roadmap (Model Validation, IDE Integration, RAG + Doc Chat, Refinement) was written when the RAG pipeline was "not yet built." The v1.2 milestone shipped a complete RAG ingestion pipeline with 6 parsers, 310 tests, and 5,004 lines of Python. The v1.3 milestone adds MCP architecture. If Chapter 7's phase descriptions are not updated, Phase 3 ("Build the RAG pipeline and chat interface") describes work that is partially complete, and the phase structure itself may no longer make sense (MCP architecture does not fit neatly into any of the four existing phases).

**Why it happens:**
- Chapter 7 is the most complex chapter to update because it synthesizes all other chapters
- The four-phase structure was designed for the v1.0 state; v1.2 and v1.3 may require additional phases or restructured phases
- Phase 3 ("RAG Pipeline + Documentation Chat") bundled two capabilities; the RAG pipeline is now built but the chat interface is not
- MCP is a cross-cutting concern that affects Phases 2, 3, and potentially a new phase

**Consequences:**
- The roadmap loses credibility as a planning tool if its descriptions do not match reality
- The cost estimates and success criteria may be stale
- Readers using Ch7 for project planning will base estimates on outdated descriptions

**Prevention:**
- Update Chapter 7's status blocks to reflect v1.2 accomplishments before adding MCP content
- Consider whether MCP changes the phase structure:
  - Option A: MCP fits within Phase 2 (IDE Integration) and Phase 3 (RAG + Chat). Update phase descriptions.
  - Option B: MCP requires its own phase or sub-phase. Add it between Phase 2 and Phase 3.
  - Option C: MCP is a cross-cutting concern woven into existing phases with no structural change.
- Update the "Where We Stand" comparison table to add a row for MCP / compiler validation
- Update success criteria if MCP changes what "done" looks like for any phase

**Detection:** Read Chapter 7's phase descriptions and check each sentence against current project state. Any "not yet built" or "not yet implemented" claim that is no longer true indicates a stale description.

**Phase/Chapter:** Chapter 7 update. Must be done LAST (after all other chapters) since it synthesizes their content.

---

## Minor Pitfalls

Mistakes that cause friction or suboptimal quality but are fixable without rework.

### 12. MCP Tool Definitions Inconsistent Across Chapters

**What goes wrong:** The MCP server defines tools (e.g., `bbj_rag_search`, `bbj_code_generate`, `bbj_compile_check`). If Chapter 2 shows these tools with one schema (parameter names, types, descriptions) and Chapter 5 shows the same tools with a slightly different schema (different parameter name, additional optional field), readers cannot tell which is authoritative.

**Prevention:**
- Define tool schemas exactly ONCE, in Chapter 2's MCP section. All other chapters reference them by name and link to Ch2 for the full definition
- If a chapter needs to show a tool invocation example, use the exact parameter names from the Ch2 definition
- Store the canonical tool definitions in a planning artifact for reference during writing

**Phase/Chapter:** Chapter 2 (definitions), Chapters 4 and 5 (references).

---

### 13. Forgetting to Update the Landing Page and Navigation

**What goes wrong:** The landing page (`src/pages/index.tsx` or equivalent) has an executive summary and audience routing that references the 7 chapters. If MCP changes what chapters cover (e.g., Chapter 2 now includes "MCP Server Architecture" alongside "Unified Infrastructure"), the landing page descriptions become inaccurate. Similarly, sidebar labels and meta descriptions may need updating.

**Prevention:**
- After all chapter updates, review:
  - Landing page chapter descriptions
  - Sidebar titles and descriptions in frontmatter (`description: "..."` in each chapter's frontmatter)
  - OG meta tags if chapter descriptions changed

**Phase/Chapter:** Final pass after all chapter content is complete.

---

### 14. Introducing MCP Jargon Without Contextualizing for Non-Developer Audiences

**What goes wrong:** The site serves three audiences: internal developers, leadership, and customers/partners. MCP terminology ("tools," "resources," "prompts," "sampling," "transport," "host/client/server") is developer jargon that leadership and customer audiences will not understand. If MCP content uses these terms without contextual framing, the non-technical audiences are excluded from understanding the architecture chapter -- which is arguably the most important chapter for leadership buy-in.

**Prevention:**
- For leadership-facing content, translate MCP concepts: "The AI system exposes structured capabilities (like searching documentation or checking code syntax) that any AI-powered tool can use through a standard protocol" rather than "The MCP server exposes tools via JSON-RPC over stdio transport"
- Use the existing pattern from Chapter 3: when QLoRA was introduced, it was explained in plain language ("achieves comparable results at a fraction of the cost by freezing the base model weights and training only small adapter matrices") before the technical details
- Keep MCP implementation details (transport, JSON-RPC, security) in developer-targeted sections or in a separate deep-dive sub-section

**Phase/Chapter:** Primarily Chapter 2 (architecture) and Chapter 7 (roadmap), which are the most leadership-facing chapters.

---

## Phase-Specific Warnings

| Phase/Chapter | Likely Pitfall | Mitigation |
|--------------|---------------|------------|
| Pre-writing | Technology contradictions (Pitfall 1) | Create alignment table reconciling concept paper with published chapters |
| Pre-writing | Chapter update ordering (Pitfall 8) | Define update order: Ch2 -> Ch4 -> Ch3,5,6 -> Ch7 |
| Ch2 update | Architecture model confusion (Pitfall 2) | Frame MCP as realization of existing architecture, not replacement |
| Ch2 update | MCP scope creep (Pitfall 9) | Limit MCP protocol explanation to 1 paragraph, link to official docs |
| Ch2 update | Diagram style mismatch (Pitfall 6) | Use existing color palette and node formatting conventions |
| Ch4 update | Unvalidated BBj code (Pitfall 4) | Run all BBj examples through `bbjcpl -N` before publishing |
| Ch4 update | bbjcpltool coupling (Pitfall 5) | Reference concept/pattern, not implementation details |
| Ch4 update | Narrative overwhelm (Pitfall 7) | Compiler validation is one section, not the chapter's new primary topic |
| Ch5 update | Tool definition inconsistency (Pitfall 12) | Reference Ch2's tool definitions, do not redefine |
| Ch6 update | Stale status block (Pitfall 3) | Update "not yet built" claims to reflect v1.2 shipped pipeline |
| Ch7 update | Outdated roadmap phases (Pitfall 11) | Update phase descriptions and success criteria for v1.2/v1.3 reality |
| All chapters | Status block inconsistency (Pitfall 3) | Update all status blocks in a single pass after content changes |
| All chapters | Decision callout formatting (Pitfall 10) | Use exact template matching existing callouts |
| Final pass | Cross-reference verification (Pitfall 8) | Run Docusaurus build + manual semantic verification |
| Final pass | Landing page/navigation staleness (Pitfall 13) | Review all chapter descriptions in frontmatter and landing page |

---

## Sources

### MCP Protocol
- [MCP Architecture Overview](https://modelcontextprotocol.io/docs/learn/architecture) -- Official architecture documentation (HIGH confidence)
- [MCP Best Practices](https://modelcontextprotocol.info/docs/best-practices/) -- Server design and deployment best practices (MEDIUM confidence -- community site, not official)
- [MCP GitHub - Specification](https://github.com/modelcontextprotocol/modelcontextprotocol) -- Official specification repository (HIGH confidence)
- [MCP Wikipedia](https://en.wikipedia.org/wiki/Model_Context_Protocol) -- Protocol history: released Nov 2024, donated to AAIF Dec 2025, adopted by OpenAI Mar 2025 (MEDIUM confidence)

### Documentation Consistency
- [Document Version Control Best Practices](https://www.ideagen.com/thought-leadership/blog/document-version-control-best-practices) -- Consistency, transparency, accountability principles (MEDIUM confidence)
- [Mastering Documentation Version Control](https://document360.com/blog/documentation-version-control/) -- Naming conventions and version numbering for multi-document systems (MEDIUM confidence)

### AI Documentation Patterns
- [Writing Documentation for AI (kapa.ai)](https://docs.kapa.ai/improving/writing-best-practices) -- Metadata-rich, chunkable, consistently updated documentation (MEDIUM confidence)
- [Major AI Documentation Trends for 2026](https://document360.com/blog/ai-documentation-trends/) -- Real-time content synchronization, treating docs as adaptive system (MEDIUM confidence)
- [AI Agent Orchestration Patterns (Microsoft)](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) -- Tool design, state management, error recovery documentation (HIGH confidence)

### Mermaid Diagrams
- [Mermaid Architecture Diagrams (v11.1.0+)](https://docs.mermaidchart.com/mermaid-oss/syntax/architecture.html) -- Diagram types and styling options (HIGH confidence)
- [Diagram as Code with Mermaid](https://www.tiagovalverde.com/posts/diagram-as-code-with-mermaid) -- Version control integration, consistent styling (MEDIUM confidence)

### Docusaurus
- [Docusaurus Versioning](https://v1.docusaurus.io/docs/en/versioning) -- Update strategy for existing versioned docs (HIGH confidence)
- [Docusaurus 3.9 Release](https://www.infoq.com/news/2025/10/docusaurus-3-9-ai-search/) -- Latest release capabilities (MEDIUM confidence)

### Project-Specific Sources (Internal)
- Published chapters at `/Users/beff/_workspace/bbj-ai-strategy/docs/` -- Existing content patterns, decision callouts, Mermaid diagrams, status blocks (HIGH confidence -- primary source material)
- PROJECT.md -- "MCP is the integration layer connecting Ch3-6, not a separate initiative; fits as the concrete realization of Ch2's unified architecture promise" (HIGH confidence -- authoritative project decision)
- v1.1 milestone -- Documented that all hallucinated BBj code was corrected across 6 chapters, confirming BBj code validation is a known critical requirement (HIGH confidence)
- Original strategy paper (`bbj-llm-strategy.md`) -- Contains CodeLlama recommendations superseded by published chapters, confirming technology alignment is a known risk (HIGH confidence)

---

*Research completed: 2026-02-01*
*Confidence: HIGH for pitfalls 1-5 (derived from direct analysis of published content, known project history, and explicit technology conflicts); MEDIUM for pitfalls 6-14 (extrapolated from documentation best practices and project patterns)*
