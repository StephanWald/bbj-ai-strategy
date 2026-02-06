# Phase 34: IDE Integration Update - Context

**Gathered:** 2026-02-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Update Chapter 4 to present a realistic IDE integration strategy: Continue.dev as the near-term integration path running in parallel with bbj-language-server ghost text as a close next milestone. Copilot BYOK limitations explained, FIM training gap documented. No new capabilities — this is a documentation chapter rewrite.

</domain>

<decisions>
## Implementation Decisions

### Chapter restructure
- Lead with the problem: "What does IDE integration for a zero-representation language like BBj need?"
- Section flow: Problem → Continue.dev → Copilot BYOK limitations → FIM gap → Language server / ghost text → Compiler validation → Status
- TL;DR stays as architectural overview (high-level two-layer approach), updated for accuracy but not reframed as actionable summary
- bbjcpl compiler validation keeps its own standalone section (it's a differentiator)

### Continue.dev depth
- Full config walkthrough — show config.json with Ollama connection, model setup, autocomplete settings so someone could follow along
- Config shows generic Ollama model (e.g. Qwen2.5-Coder) with a note about where to swap in the fine-tuned BBj model when ready
- Chat mode and tab-completion mode split into clear separate subsections: chat works now with instruction-tuned model, tab completion needs FIM-trained model
- Include comparison table: Continue.dev vs Copilot BYOK vs custom language server — covering chat, tab completion, BBj awareness, compiler validation, effort to integrate

### What stays vs what goes
- Ghost text architecture section: KEEP and expand — bbj-language-server has VS Code and IntelliJ extensions in the repo (BBx-Kitchen/bbj-language-server), ghost text implementation is a close next milestone, not distant future
- Generation-aware completion (character, vpro5, bbj-gui, dwc): keep as-is, still relevant
- LSP 3.18 section: Claude's discretion on framing (likely path but not confirmed)
- Langium AI section: KEEP — language server is deeply Langium-based, can't dismiss Langium AI without research and proper decision-making. Contextualize as natural extension of existing Langium architecture, not a throwaway alternative
- "Alternative Architectures" framing goes away — Continue.dev becomes primary section, Langium AI stays contextualized with the language server

### Tone and framing
- Continue.dev and language server framed as parallel strategies: Continue.dev for model delivery, language server for BBj-specific intelligence — they complement, not compete
- Progress-focused tone: "here's what we've built, here's the pragmatic next step, here's where it's all heading" — emphasize momentum
- Copilot BYOK: contrast directly with Continue.dev — show why BYOK falls short (chat only, no inline) and why Continue.dev fills that gap
- Status section uses established Phase 32 terminology: operational / operational for internal exploration / active research / planned

### Claude's Discretion
- LSP 3.18 section framing and hedging level
- Exact structure of the comparison table columns/rows
- How to integrate the FIM training gap explanation (subsection vs callout)
- Typography and spacing within the config walkthrough

</decisions>

<specifics>
## Specific Ideas

- bbj-language-server extensions exist in the repo at https://github.com/BBx-Kitchen/bbj-language-server — this is real infrastructure, not aspirational
- Ghost text implementation is framed as "one of the closest next milestones" — the chapter should convey this proximity
- Language server is deeply Langium-based — Langium AI is not an "alternative" but a natural evolution of the existing architecture
- Comparison table should make it visually clear that Continue.dev has the best near-term coverage while language server has the best long-term potential

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 34-ide-integration*
*Context gathered: 2026-02-06*
