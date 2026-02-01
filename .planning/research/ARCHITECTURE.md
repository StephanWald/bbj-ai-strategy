# Architecture Research: MCP Integration into Existing Chapters

**Milestone:** v1.3 -- MCP Architecture Integration
**Researched:** 2026-02-01
**Confidence:** HIGH (chapter analysis, content flow) / MEDIUM (MCP spec details, conflict assessment)

> **Supersedes:** Previous ARCHITECTURE.md covered the v1.2 RAG ingestion sub-project. That architecture is built and shipped. This document covers how MCP server architecture content should be distributed across the existing 7 Docusaurus chapters for v1.3.

---

## 1. The Core Integration Question

The existing 7 chapters tell a story: problem (Ch1) -> architecture (Ch2) -> components (Ch3-6) -> execution (Ch7). Currently, Ch2's "Strategic Architecture" describes a **passive, abstract** unified infrastructure -- "one model and RAG pipeline shared by multiple consumers." The consumers (IDE extension, documentation chat) connect directly to Ollama and the RAG database.

MCP transforms this from a passive shared-infrastructure story into an **active orchestration** story. The MCP server becomes the concrete realization of Ch2's promise: a single server that exposes tools for RAG search, code generation, and compiler validation. The generate-validate-fix loop -- where the BBj compiler provides ground-truth feedback on AI-generated code -- is the key innovation that ties Ch3 (model), Ch4 (IDE/compiler), Ch5 (chat/RAG search), and Ch6 (RAG database) together through a concrete protocol.

**The fundamental content architecture decision:** MCP is NOT a new Chapter 8. It is the integration layer that connects the existing chapters. Ch2 is its natural home; Ch4 and Ch5 get substantial new sections; Ch3, Ch6, and Ch7 get lighter updates.

---

## 2. Per-Chapter Content Assessment

### Chapter 1: The BBj Challenge (index.mdx)

**Change level:** NONE (cross-reference only, optional)

**Current content (324 lines):** Problem statement. Four BBj generations, LLM hallucination failures, why Copilot fails, the webforJ contrast, current status.

**Why no changes needed:** Ch1 establishes the *problem*. MCP is part of the *solution*. The problem statement remains unchanged regardless of the solution architecture. Ch1 already links forward to Ch2 ("the unified architecture") and all other chapters.

**Optional enhancement:** The "Current Status" note at the bottom could add one bullet mentioning the bbjcpltool proof-of-concept validating the compiler-in-the-loop concept. This is minor and deferrable.

**Risk of changes:** LOW. Ch1 is stable, well-reviewed content. Adding MCP references here would dilute the clean problem-focused narrative.

**Recommendation:** Leave Ch1 untouched. It works as-is.

---

### Chapter 2: Strategic Architecture (index.md)

**Change level:** MAJOR REWRITE of the architecture section

**Current content (215 lines):** "Case against point solutions," abstract architecture diagram (apps -> model + RAG), description of shared foundation, three initiatives overview, benefits, current status.

**What needs to change:**

The current Ch2 is too abstract. It says "shared infrastructure" but never explains *how* the components connect. The architecture diagram shows direct arrows from each consumer app to Model and RAG, with no intermediary. MCP provides the concrete answer: a server that exposes tools via a standard protocol, any MCP-compatible client can call them, and the generate-validate-fix loop adds a quality dimension the current architecture lacks.

**Specific content additions:**

1. **MCP Server as the Orchestration Layer** (new major section, ~150-200 lines)
   - What MCP is (brief -- the protocol, not a deep spec dive)
   - Why MCP fits: standard protocol, JSON-RPC 2.0, same architectural lineage as LSP (which Langium/bbj-language-server already uses)
   - The BBj MCP server concept: one server, three tools
   - Tool definitions (concrete, with inputSchema):
     - `bbj_rag_search` -- query the RAG database with generation-aware filtering
     - `bbj_generate_code` -- invoke the fine-tuned model for code generation
     - `bbj_compile_check` -- validate BBj code via `bbjcpl -N` compiler
   - How any MCP-compatible client (Claude, VS Code via Copilot, custom IDE extension) can use these tools

2. **The Generate-Validate-Fix Loop** (new major section, ~100-150 lines)
   - The key innovation: compiler as ground truth
   - Flow: LLM generates BBj code -> compiler validates -> if errors, LLM fixes with compiler feedback -> repeat until valid
   - Why this matters for BBj specifically (LLMs have zero training data, hallucination is the default)
   - Mermaid sequence diagram showing the loop
   - Reference to bbjcpltool proof-of-concept validating this concept

3. **Updated Architecture Diagram** (replace existing)
   - Current: `Apps -> Model + RAG` (flat, passive)
   - New: `MCP Clients -> MCP Server -> {RAG DB, Fine-Tuned Model, BBj Compiler}` (orchestrated, active)
   - Show the three tools as the interface between clients and capabilities

4. **Deployment Options** (new section, ~50-80 lines)
   - Local stdio transport (Claude Code, Claude Desktop)
   - Remote Streamable HTTP transport (web-based chat, multi-user)
   - Both use the same server code, different transports

**What to preserve:**
- "The Case Against Point Solutions" section -- still relevant, still motivates shared infrastructure
- Benefits section -- update to reflect MCP-specific benefits (standard protocol, any-client compatibility)
- The conceptual framing of "shared foundation" -- MCP is the *concrete realization* of this concept

**What to remove or substantially rewrite:**
- The current abstract architecture diagram (replace with MCP-centered version)
- The "How They Work Together" sequence diagram (replace with generate-validate-fix loop)
- The "Three Initiatives" section needs updating -- IDE and Chat are now MCP *clients*, not independent consumers

**Conflict risk:** MEDIUM. The current Ch2 is the most abstract chapter. Rewriting it to be concrete (MCP tools, protocol details) changes its character from "strategic overview" to "strategic overview with implementation specifics." This is intentional -- the chapter currently has a gap between its promise ("unified infrastructure") and its delivery (hand-waving about how apps connect). MCP fills that gap. But the rewrite must maintain the strategic-audience accessibility. Technical details (inputSchema, JSON-RPC) should be in code blocks or expandable sections, not in the main narrative flow.

**Content dependencies:** Ch2 must be written/updated FIRST because Ch4, Ch5, and Ch7 reference it. The MCP tool definitions established here become the vocabulary used in downstream chapters.

---

### Chapter 3: Fine-Tuning the Model (index.md)

**Change level:** LIGHT UPDATE (cross-references + one new subsection)

**Current content (416 lines):** Training data structure, base model selection (Qwen2.5-Coder-7B), QLoRA approach, Unsloth + llama.cpp + Ollama toolchain, Ollama hosting, deployment architecture, current status.

**What needs to change:**

Ch3's content is primarily about model training -- a domain that MCP does not directly affect. The model is still trained the same way, served via Ollama the same way. What changes is *how clients access it*.

**Specific content additions:**

1. **Model as MCP Tool Backend** (new subsection under "Hosting via Ollama," ~30-50 lines)
   - The fine-tuned model is now accessed through the MCP server's `bbj_generate_code` tool, not directly by consumer apps
   - The MCP server calls Ollama's OpenAI-compatible API internally
   - This means consumer apps no longer need to know about Ollama endpoints -- they call MCP tools
   - Cross-reference to Ch2's tool definitions

2. **Updated Deployment Diagram** (modify existing)
   - Add MCP server as intermediary between consumer apps and Ollama
   - Keep the Ollama -> customer premises diagram but add MCP server in the flow

3. **Updated cross-references in "Current Status"**
   - Mention the MCP architecture in Ch2 as the access layer
   - Note that the bbjcpltool proof-of-concept validates compiler-in-the-loop

**What to preserve:** Everything else. The training data section, base model selection, QLoRA methodology, quantization details -- all unchanged.

**Conflict risk:** LOW. The changes are additive. The existing content about Ollama's OpenAI-compatible API actually *supports* the MCP story -- the MCP server uses that same API internally.

**Content dependencies:** Can reference Ch2's MCP tool definitions. Should be updated after Ch2.

---

### Chapter 4: IDE Integration (index.md)

**Change level:** MAJOR ADDITION (new section, ~200-250 lines)

**Current content (431 lines):** bbj-language-server foundation, two-layer completion (Langium popup + LLM ghost text), generation-aware completion, semantic context for prompts, LSP 3.18, Copilot BYOK bridge, Continue.dev / Langium AI alternatives, current status.

**What needs to change:**

Ch4 currently describes the IDE as calling Ollama directly for ghost text completions. With MCP, there are two significant additions:

1. **Compiler Validation Module** -- the `bbj_compile_check` tool validates LLM-generated code before it reaches the developer. This is a new quality layer between the LLM and the ghost text display.

2. **bbjcpltool Proof-of-Concept** -- a working implementation that validates the compiler-in-the-loop concept. This grounds the theoretical architecture in demonstrated reality.

**Specific content additions:**

1. **Compiler Validation: Ground-Truth Syntax Checking** (new major section, ~150-180 lines)
   - The problem: LLM ghost text suggestions may contain hallucinated syntax that passes no validation
   - The solution: route generated code through `bbjcpl -N` (BBj's syntax-only compiler) before presenting
   - The `bbj_compile_check` MCP tool: accepts BBj code, returns compiler output (clean or error messages)
   - How this integrates with the existing ghost text pipeline:
     - Current: `LLM generates -> render ghost text`
     - New: `LLM generates -> compiler validates -> if valid, render ghost text; if invalid, LLM fixes with error context -> re-validate -> render`
   - Mermaid diagram showing the validation loop within the IDE completion pipeline
   - Latency implications: compiler check adds ~50-100ms, but prevents broken suggestions
   - This is the Langium parser validation concept (already mentioned in existing Ch4) taken further with the actual BBj compiler as the authority

2. **bbjcpltool: Proof-of-Concept Validation** (new subsection, ~50-80 lines)
   - What bbjcpltool is: PostToolUse hook in Claude Code that runs `bbjcpl -N` on every `.bbj` file
   - What it proved: the compiler-in-the-loop concept works in practice
   - Key learnings from the proof-of-concept
   - How it maps to the MCP server's `bbj_compile_check` tool
   - The shared `bbj-reference.md` language reference as a precursor to the RAG search tool
   - Cross-reference to Ch2's MCP architecture

3. **Updated Ghost Text Architecture Diagram** (modify existing)
   - Add compiler validation step between LLM response and ghost text rendering
   - Show the MCP server in the flow

**What to preserve:**
- Everything about the bbj-language-server foundation
- The two-layer completion model (Langium popup + LLM ghost text) -- unchanged
- Generation-aware completion -- unchanged
- Semantic context for prompts -- unchanged
- LSP 3.18 discussion -- unchanged
- Copilot BYOK bridge -- update with MCP context (Copilot Chat can be an MCP client)
- Continue.dev / Langium AI references -- unchanged

**What to update in existing content:**
- The "Copilot Bridge" section should note that Copilot Chat is now an MCP host, meaning the BBj MCP server tools are directly accessible in Copilot Chat -- a significant upgrade over the BYOK-chat-only story
- The ghost text architecture section needs a note about the compiler validation step
- Current status section needs updating

**Conflict risk:** MEDIUM. The biggest risk is that the compiler validation section adds significant length to an already-long chapter (431 lines). The new content (~200-250 lines) would push it past 650 lines. Consider whether compiler validation should be a subsection of the existing "Ghost Text Architecture" section or a standalone peer section. Recommendation: make it a peer section after "Generation-Aware Completion" and before "LSP 3.18." This maintains the logical flow: how completions work -> how they become generation-aware -> how they get validated -> protocol evolution.

**Content dependencies:** References Ch2's `bbj_compile_check` tool definition. Should be written after Ch2.

---

### Chapter 5: Documentation Chat (index.md)

**Change level:** MODERATE ADDITION (new section, ~100-150 lines)

**Current content (254 lines):** Why generic chat fails, architectural requirements, generation-aware response design, chat architecture sequence diagram, deployment options, streaming/citations, conversation context, token budget, current status.

**What needs to change:**

Ch5 currently describes the chat system as calling the RAG database and Ollama directly. With MCP, the chat backend can use the MCP server's `bbj_rag_search` tool for retrieval, which standardizes the interface and means any MCP-compatible chat client (not just a custom-built one) can offer BBj documentation assistance.

**Specific content additions:**

1. **MCP-Based RAG Search Tool** (new section, ~80-100 lines)
   - The `bbj_rag_search` tool as the standard interface for documentation queries
   - Tool definition: accepts query text and optional generation hint, returns ranked documentation chunks with citations
   - How this changes the chat architecture: instead of a custom RAG retrieval API, the chat backend (or any MCP client) calls `bbj_rag_search`
   - Updated sequence diagram showing MCP tool call in the flow
   - The benefit: any MCP-compatible client (Claude Desktop, VS Code Copilot Chat, custom web chat) gets BBj documentation assistance without building custom retrieval code

2. **Updated Architecture Implications** (modify existing section, ~30-50 lines)
   - The "Chat Architecture" sequence diagram should show the MCP tool call step
   - Deployment options now include "any MCP client" as a zero-custom-code option alongside the embedded widget and standalone service
   - This strengthens Ch5's "shared infrastructure" argument -- the same `bbj_rag_search` tool serves IDE context enrichment AND chat documentation queries

**What to preserve:**
- "Why Generic Chat Services Fail" -- unchanged
- "Architectural Requirements" -- all 6 requirements still valid; add a 7th about MCP tool compatibility
- "Generation-Aware Response Design" -- unchanged (the MCP tool passes through generation hints)
- "Streaming and Citations" -- unchanged
- "Conversation Context" / "Token Budget" -- unchanged

**What to update in existing content:**
- The chat architecture sequence diagram should include an MCP tool call step
- "Deployment Options" table should add "MCP client (zero-code)" as an option
- Current status section

**Conflict risk:** LOW-MEDIUM. The new content is additive and complementary. The risk is that Ch5 currently positions the chat as a custom-built system, and the MCP story makes some of that custom-build unnecessary (any MCP client can query BBj documentation). This is a *good* change -- it simplifies the story -- but it means some existing content about the custom chat backend becomes "one option among several" rather than "the only path." The rewrite should frame the custom chat backend as the optimized experience, with MCP-client access as the "quick start" that works out of the box.

**Content dependencies:** References Ch2's `bbj_rag_search` tool definition and Ch6's RAG database. Should be written after Ch2.

---

### Chapter 6: RAG Database Design (index.md)

**Change level:** LIGHT UPDATE (cross-references + one subsection)

**Current content (517 lines):** Source corpus, MadCap Flare ingestion, multi-generation document structure, chunking strategy, embedding strategy, pgvector, hybrid retrieval, generation-aware retrieval, current status.

**What needs to change:**

Ch6's content is about the RAG database internals -- ingestion, chunking, embedding, storage, retrieval. MCP does not change any of this. What changes is that the retrieval API described at the end of Ch6 (`retrieveDocumentation()` function) is now exposed as the MCP server's `bbj_rag_search` tool.

**Specific content additions:**

1. **RAG as MCP Tool Backend** (new subsection in "Hybrid Retrieval Strategy," ~30-50 lines)
   - The `retrieveDocumentation()` function described in Ch6 is the implementation behind the `bbj_rag_search` MCP tool
   - The MCP server wraps this function with JSON-RPC protocol handling
   - This means the retrieval logic described in Ch6 is directly accessible to any MCP client
   - Cross-reference to Ch2's tool definition and Ch5's usage in documentation chat

2. **Updated "What Comes Next" section**
   - Mention MCP as the protocol layer that exposes the RAG pipeline to consumers
   - Cross-reference to Ch2

**What to preserve:** Everything. The ingestion pipeline, chunking strategy, embedding approach, pgvector selection, hybrid retrieval implementation, generation-aware scoring -- all unchanged.

**Conflict risk:** VERY LOW. The changes are purely additive cross-references. Ch6's technical content is not affected by MCP.

**Content dependencies:** References Ch2's tool definitions. Can be updated in any order relative to Ch4/Ch5 but after Ch2.

---

### Chapter 7: Implementation Roadmap (index.md)

**Change level:** MODERATE UPDATE (revise phases, add MCP-specific deliverables)

**Current content (301 lines):** Four phases (model validation, IDE integration, RAG + doc chat, refinement), infrastructure costs, risk assessment, success metrics, current status.

**What needs to change:**

The four-phase structure remains valid, but MCP server development needs to be placed within the phases. The generate-validate-fix loop and MCP tool infrastructure are new deliverables that must be sequenced correctly.

**Specific content additions:**

1. **MCP Server Development in Phase Sequencing** (~50-80 lines of updates across phases)
   - Phase 1 (Model Validation): Add `bbj_compile_check` tool implementation as a deliverable -- the compiler validation can be built and tested independently of the full MCP server
   - Phase 2 (IDE Integration): Add MCP server with `bbj_generate_code` and `bbj_compile_check` tools; add the generate-validate-fix loop as a deliverable; reference bbjcpltool as the validated proof-of-concept
   - Phase 3 (RAG + Doc Chat): Add `bbj_rag_search` tool; the chat system can now be "any MCP client" for quick deployment, with custom chat as the optimized path
   - Phase 4 (Refinement): MCP server hardening, transport optimization (stdio vs Streamable HTTP), multi-client support

2. **Updated Risk Assessment** (~30-40 lines)
   - New risk: MCP ecosystem evolving rapidly (protocol versions, SDK changes)
   - Mitigation: MCP is backed by Anthropic + Linux Foundation (AAIF), standard is stabilizing
   - New risk: Compiler validation latency impact on IDE completion speed
   - Mitigation: `bbjcpl -N` is syntax-only (fast), can be async/parallel

3. **Updated "Where We Stand" Table**
   - Add MCP server row: "Architecture defined in Ch2, bbjcpltool validates compiler-in-the-loop concept"

4. **Updated Cost Assessment**
   - MCP server itself adds no infrastructure cost (it is a process, not a service requiring new hardware)
   - The BBj compiler (`bbjcpl`) is part of the existing BBj installation

**What to preserve:**
- Four-phase structure -- still valid
- MVP checkpoint concept -- still valid
- Infrastructure cost analysis -- mostly unchanged
- Success metrics -- add one MCP-specific metric (e.g., "MCP tool call success rate > 99%")

**Conflict risk:** LOW-MEDIUM. The phases need surgical additions, not rewrites. The risk is making the phases too long. Each phase should get 2-3 new bullet points for MCP deliverables, not paragraphs.

**Content dependencies:** Should be updated LAST because it references all other chapters.

---

## 3. Content Dependencies and Build Order

### Dependency Graph

```
Ch2 (Strategic Architecture) -- MUST be first
  |
  +---> Ch4 (IDE Integration) -- references Ch2's tool definitions
  |       |
  |       +---> References bbjcpltool, bbj_compile_check
  |
  +---> Ch5 (Documentation Chat) -- references Ch2's tool definitions, Ch6's retrieval
  |       |
  |       +---> References bbj_rag_search
  |
  +---> Ch3 (Fine-Tuning) -- references Ch2's MCP layer
  |
  +---> Ch6 (RAG Database) -- references Ch2's tool definitions
  |
  +---> Ch7 (Implementation Roadmap) -- references ALL chapters
```

### Recommended Build Order

| Order | Chapter | Change Level | Estimated New Lines | Rationale |
|-------|---------|-------------|--------------------:|-----------|
| 1 | Ch2: Strategic Architecture | MAJOR REWRITE | 300-400 | Establishes MCP vocabulary, tool definitions, and the generate-validate-fix loop. All other chapters reference this. |
| 2 | Ch4: IDE Integration | MAJOR ADDITION | 200-250 | Largest content addition after Ch2. Compiler validation module is the most technically novel content. |
| 3 | Ch5: Documentation Chat | MODERATE ADDITION | 100-150 | MCP-based RAG search tool and updated architecture. Depends on Ch2's tool definitions. |
| 4 | Ch3: Fine-Tuning | LIGHT UPDATE | 30-50 | Cross-references to MCP layer. Low risk, low effort. |
| 5 | Ch6: RAG Database | LIGHT UPDATE | 30-50 | Cross-references to MCP tool wrapping. Low risk, low effort. |
| 6 | Ch7: Implementation Roadmap | MODERATE UPDATE | 80-120 | Phase updates, risk additions. Must be last because it references all chapters. |
| -- | Ch1: BBj Challenge | NONE | 0 | No changes needed. |

**Total estimated new content:** 740-1,020 lines across 6 chapters.

### Parallelization Opportunities

- Ch3 and Ch6 can be updated in parallel (both are light cross-reference updates, no dependency on each other)
- Ch4 and Ch5 can be updated in parallel AFTER Ch2 is complete (both depend on Ch2 but not on each other)
- Ch7 must be last

This gives a 4-step critical path:
1. Ch2 (blocking)
2. Ch4 + Ch5 (parallel)
3. Ch3 + Ch6 (parallel, or combined with step 2 if they are trivial)
4. Ch7 (blocking, final)

---

## 4. MCP Architecture Patterns for the Content

### The Three-Tool MCP Server

This is the core architectural concept that Ch2 must establish and other chapters must reference consistently.

```
BBj AI Development Assistant (MCP Server)
|
+-- bbj_rag_search
|   Description: Search BBj documentation with generation-aware filtering
|   Input: { query: string, generation?: string, limit?: number }
|   Output: Ranked documentation chunks with citations and generation metadata
|   Backend: pgvector hybrid retrieval (Ch6)
|
+-- bbj_generate_code
|   Description: Generate BBj code using the fine-tuned model
|   Input: { prompt: string, generation?: string, context?: string }
|   Output: Generated BBj code with generation metadata
|   Backend: Ollama API to fine-tuned Qwen2.5-Coder (Ch3)
|
+-- bbj_compile_check
|   Description: Validate BBj code syntax using the BBj compiler
|   Input: { code: string, filename?: string }
|   Output: { valid: boolean, errors?: CompilerError[], diagnostics?: string }
|   Backend: bbjcpl -N subprocess (Ch4)
```

### The Generate-Validate-Fix Loop

This is the key innovation that Ch2 introduces and Ch4 demonstrates in the IDE context.

```
1. LLM receives task (write BBj code / complete code)
2. LLM generates BBj code via bbj_generate_code tool
3. Code is passed to bbj_compile_check tool
4. IF compiler returns errors:
   a. Error messages are fed back to LLM
   b. LLM generates corrected code
   c. Go to step 3 (max N iterations)
5. IF compiler returns clean:
   a. Code is presented to user (ghost text, chat response, etc.)
```

### MCP Transport Mapping

| Deployment Scenario | Transport | Client Example |
|--------------------|-----------|-|
| Developer workstation | stdio | Claude Code, Claude Desktop |
| VS Code extension | stdio | bbj-language-server calling MCP server |
| Web-based chat | Streamable HTTP | Browser chat widget, custom web app |
| Team server | Streamable HTTP | Multiple developers sharing one MCP server |

### Relationship to Existing Patterns

The MCP architecture maps cleanly to the existing content:

| Existing Concept (Current Ch2) | MCP Realization |
|-------------------------------|-----------------|
| "Shared Foundation" | MCP Server (single process exposing all tools) |
| "Fine-Tuned Model via Ollama" | Backend for `bbj_generate_code` tool |
| "RAG Database" | Backend for `bbj_rag_search` tool |
| "Consumer App detects generation context" | MCP client passes `generation` parameter to tools |
| "Assembles enriched prompt" | MCP server combines RAG results + model prompt internally |
| "Future Capabilities" | Any new MCP tool added to the server |

---

## 5. Conflict Analysis and Mitigation

### High-Risk Conflicts

**Ch2: Abstract vs. Concrete Balance**

The current Ch2 speaks to leadership and strategic audiences. Adding MCP tool definitions with JSON-RPC and inputSchema risks making it too technical.

*Mitigation:* Keep the main narrative at the strategic level ("MCP server exposes three tools: documentation search, code generation, and compiler validation"). Put the technical details (inputSchema, JSON-RPC examples, transport options) in collapsible details blocks, code tabs, or a subsection clearly marked as "Technical Detail." The Docusaurus site already uses `:::info` admonitions and code blocks effectively -- follow the same pattern.

**Ch4: Length After Additions**

Ch4 is already 431 lines and the longest non-Ch6 chapter. Adding 200-250 lines of compiler validation content pushes it past 650 lines.

*Mitigation:* Consider whether compiler validation warrants a sub-page (like Ch6's getting-started.md). The Ch4 directory already supports sub-pages. If the content exceeds ~600 lines after editing, split the compiler validation into a sub-page. Alternatively, some existing content may be condensable -- the "Alternative Architectures" section (Continue.dev, Langium AI) could be trimmed since it is not the core narrative.

### Medium-Risk Conflicts

**Ch5: Custom Chat Backend vs. "Any MCP Client"**

The current Ch5 devotes significant space to a custom chat backend (SSE streaming, token budget management, session memory). MCP makes this one option among several -- any MCP client can query BBj documentation. The chapter must not invalidate the existing custom-backend content but must honestly present the MCP-client option as a simpler alternative.

*Mitigation:* Frame it as two tiers: (1) "Quick start: any MCP client" for immediate access to BBj documentation assistance, and (2) "Optimized experience: custom chat backend" for generation-aware UX, session memory, and embedded-in-docs deployment. The existing content becomes the "optimized experience" tier. The new MCP content becomes the "quick start" tier.

**Ch7: Phase Bloat**

Each phase currently has 4-6 key deliverables. Adding MCP deliverables to each phase risks making the roadmap feel overwhelming.

*Mitigation:* Add MCP deliverables as sub-bullets under existing deliverables where possible, rather than as new top-level deliverables. For example, under Phase 2's "Inline completion provider," add a sub-bullet: "includes compiler validation via `bbj_compile_check` MCP tool."

### Low-Risk Conflicts

**Ch3 and Ch6:** These chapters are about internals (model training, RAG pipeline) that MCP does not change. The cross-references are purely additive. No conflict expected.

**Ch1:** No changes proposed. No conflict possible.

---

## 6. Content Patterns to Follow

The existing chapters establish consistent patterns that new MCP content must follow:

### TL;DR Block

Every chapter opens with a `:::tip[TL;DR]` block. Ch2's TL;DR needs updating to mention MCP. Proposed:

> Instead of building separate AI systems, the BBj strategy centers on an MCP server
> that orchestrates three capabilities -- documentation search, code generation, and
> compiler validation -- through a standard protocol. Any MCP-compatible client (Claude,
> VS Code, custom tools) can access BBj AI intelligence. The key innovation: a
> generate-validate-fix loop where the BBj compiler provides ground-truth feedback on
> AI-generated code, eliminating hallucinated syntax before it reaches the developer.

### Decision Callouts

Use `:::info[Decision: ...]` for key architectural decisions. New decisions needed:

- **Decision: MCP as the Integration Protocol** (Ch2)
- **Decision: Compiler Validation in the Completion Pipeline** (Ch4)
- **Decision: MCP Tool for RAG Access** (Ch5)

### Mermaid Diagrams

Every chapter uses Mermaid. New diagrams needed:

- Ch2: MCP server architecture (replacing current flat diagram)
- Ch2: Generate-validate-fix sequence diagram
- Ch4: Updated ghost text pipeline with compiler validation step
- Ch5: Updated chat architecture with MCP tool call

### Code Blocks

Use `typescript` and `json` code blocks with titles. New code blocks needed:

- Ch2: MCP tool definitions (JSON or TypeScript)
- Ch4: Compiler validation flow (TypeScript)
- Ch4: bbjcpltool reference (shell/config)

### Current Status Notes

Every chapter ends with a `:::note[Where Things Stand]` block. These all need updating to reflect the MCP architecture.

### Cross-References

Follow the existing pattern of inline links: `[Chapter N](/docs/chapter-slug)`. New cross-references should link to the specific section where a concept is defined (e.g., `[MCP tool definitions](/docs/strategic-architecture#mcp-tool-definitions)`).

---

## 7. The bbjcpltool Proof-of-Concept Story

The bbjcpltool is a working implementation that validates the compiler-in-the-loop concept. It should be referenced in Ch2 (as evidence the concept works) and detailed in Ch4 (as the proof-of-concept for the `bbj_compile_check` tool). Here is what is known about it from PROJECT.md:

- **Location:** `/Users/beff/bbjcpltool/`
- **What it does:** PostToolUse hook in Claude Code that runs `bbjcpl -N` on every `.bbj` file Claude writes/edits
- **Companion:** Shared BBj language reference at `~/.claude/bbj-reference.md`
- **Status:** v1 shipped, working
- **What it validates:** The compiler-in-the-loop concept -- when Claude generates BBj code, the compiler immediately checks it and feeds errors back

This is the strongest evidence that the generate-validate-fix loop works in practice. The MCP server's `bbj_compile_check` tool is the productized version of what bbjcpltool demonstrates.

**Content treatment:**
- Ch2: Mention as proof-of-concept that validates the architecture ("the bbjcpltool demonstrates this loop in practice with Claude Code")
- Ch4: Dedicate a subsection to the proof-of-concept, describing what it does, what it proved, and how the MCP tool generalizes it

---

## 8. Narrative Arc Assessment

After MCP integration, the 7-chapter story should read:

1. **Ch1 (The Problem):** BBj is invisible to LLMs. They hallucinate. We need custom tooling.
2. **Ch2 (The Architecture):** An MCP server orchestrates three capabilities -- RAG search, code generation, and compiler validation. The generate-validate-fix loop ensures correctness. Any MCP client can use it.
3. **Ch3 (The Model):** We fine-tune Qwen2.5-Coder on BBj training data and serve it via Ollama. The MCP server calls it through the `bbj_generate_code` tool.
4. **Ch4 (The IDE):** The bbj-language-server provides deterministic completions. The MCP server adds AI completions with compiler validation. Ghost text suggestions are syntax-validated before rendering.
5. **Ch5 (The Chat):** Any MCP client can search BBj documentation via `bbj_rag_search`. A custom chat provides the optimized, generation-aware experience with streaming and citations.
6. **Ch6 (The RAG Database):** The ingestion pipeline, chunking, embedding, and retrieval logic that powers `bbj_rag_search`.
7. **Ch7 (The Plan):** Four phases, now with MCP server deliverables woven into each phase.

This maintains the existing narrative flow while adding the MCP integration layer. No chapter changes its fundamental purpose. Ch2 goes from "abstract architecture" to "concrete architecture." Ch4 and Ch5 gain new capabilities. Ch3, Ch6, and Ch7 get updated references.

---

## 9. Risks and Open Questions

### Open Questions

1. **MCP SDK choice for the BBj MCP server implementation:** TypeScript SDK (aligns with bbj-language-server) vs. Python SDK (aligns with rag-ingestion). The documentation site does not need to resolve this -- it describes the architecture, not the implementation language. But if the team has a preference, it could be mentioned.

2. **Compiler availability:** The `bbjcpl -N` compiler is part of the BBj installation. Not all developers will have it installed. The MCP server needs a graceful degradation path when the compiler is unavailable (skip validation, warn the user). This should be mentioned in Ch2 or Ch4.

3. **MCP spec version:** The current spec is `2025-11-25` (also referred to as `2025-06-18` in some places -- need to verify which is the latest stable version). The protocol is evolving. Content should reference the specification version and note that updates may apply.

4. **Tool naming conventions:** The tool names (`bbj_rag_search`, `bbj_generate_code`, `bbj_compile_check`) are working names from the concept paper. They should be finalized before being committed to the documentation. The convention of `bbj_` prefix is reasonable for namespace clarity in multi-server environments.

### Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Ch2 rewrite changes the chapter's character from strategic to technical | MEDIUM | Keep narrative strategic; put technical details in code blocks and info callouts |
| Ch4 becomes too long after additions | MEDIUM | Consider sub-page for compiler validation; trim alternative architectures section |
| MCP protocol evolves, making content stale | LOW | Reference spec version; note that the architecture pattern (tool-based orchestration) is stable even if protocol details change |
| bbjcpltool details may not be shareable publicly | LOW | Verify what can be described; focus on the concept validated rather than implementation details |
| Cross-reference consistency across 6 updated chapters | MEDIUM | Use a consistent vocabulary established in Ch2; review all cross-references after all chapters are updated |

---

## Sources

### Primary (HIGH confidence)
- [MCP Specification (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25) -- Official protocol specification
- [MCP Architecture Overview](https://modelcontextprotocol.io/docs/learn/architecture) -- Official architecture documentation
- [MCP GitHub Organization](https://github.com/modelcontextprotocol) -- Official repos, SDKs, reference implementations
- Existing chapter content (all 7 chapters read and analyzed in full)
- PROJECT.md context (MCP concept paper description, bbjcpltool details)

### Secondary (MEDIUM confidence)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk) -- Tool definition patterns and API
- [MCP Wikipedia](https://en.wikipedia.org/wiki/Model_Context_Protocol) -- Governance (donated to Linux Foundation AAIF)
- [Code Feedback MCP pattern](https://blog.niradler.com/how-code-feedback-mcp-enhances-ai-generated-code-quality) -- Generate-validate-fix loop architecture pattern

### Tertiary (LOW confidence)
- WebSearch results on MCP ecosystem trends (2025-2026) -- general landscape context
- MCP Apps announcement (January 2026) -- indicates protocol is actively evolving with UI capabilities

---

*Research date: 2026-02-01*
*Valid until: 2026-04-01 (MCP ecosystem is evolving; protocol version and SDK versions should be re-verified before implementation)*
