# Phase 3: Foundation Chapters - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Write three researched chapters covering the foundation of the BBj AI strategy: why BBj needs custom AI (Ch 1), the unified architecture vision (Ch 2), and the fine-tuning approach (Ch 3). Add BBj syntax highlighting for code examples. Creating execution chapters (4-7) is Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Writing voice & depth
- Tone: authoritative practitioner -- confident, direct, like a senior engineer explaining strategy to peers
- Body text is developer-first and technical; TL;DR blocks and decision callouts carry non-technical audiences (leadership, customers)
- State decisions confidently, note alternatives briefly ("We selected X because Y. Z was considered but...")
- Perspective: mixed -- first person plural ("we", "our approach") for strategy decisions, third person ("BASIS International") for company background/context

### Chapter flow & structure
- Chapter length: Claude's discretion per chapter -- calibrate depth to content complexity
- Chapters are standalone with light cross-references -- each works independently, readers can jump to any chapter
- Section pattern: TL;DR -> Problem -> Approach -> Details -> Current Status
- Each chapter ends with a "Current Status" section showing where implementation stands as of writing

### Source material & freshness
- Original strategy paper (bbj-llm-strategy.md) is a starting outline -- rewrite chapters from scratch with new framing and depth
- Actively research alternatives and state of the art for each major topic (model selection, fine-tuning approaches, hosting options)
- Specific tool/model choices from the paper (Qwen2.5-Coder, Ollama, LoRA, Langium) are NOT locked -- research may surface better options, let findings determine recommendations
- Inline citations with links -- link to papers, benchmarks, and docs where claims are made. Not an academic paper, but verifiable.

### BBj code examples
- Minimal code volume -- short 3-5 line conceptual fragments illustrating a point, not runnable programs
- Show all four BBj generations (procedural, OOP, GUI/DWC, webforJ) to illustrate the contrast
- Side-by-side comparisons for the same task across generations -- makes the "why LLMs struggle" argument visceral
- Prism.js already supports BBj as a language -- no custom grammar needed, just configure Docusaurus to use it

### Claude's Discretion
- Chapter length calibration per topic
- Exact section headings within the TL;DR -> Problem -> Approach -> Details -> Status pattern
- How much background context each standalone chapter needs
- Which specific code tasks to use for cross-generation comparisons

</decisions>

<specifics>
## Specific Ideas

- Side-by-side code comparison showing the same operation in procedural BBj, OOP BBj, DWC, and webforJ -- this is the centerpiece illustration for Chapter 1's argument
- Prism.js already has BBj language support (user confirmed) -- plan 03-01 should just configure Docusaurus to register it, not build a grammar from scratch
- "Current Status" section at end of each chapter grounds the strategy in reality -- shows what's been done vs what's planned

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 03-foundation-chapters*
*Context gathered: 2026-01-31*
