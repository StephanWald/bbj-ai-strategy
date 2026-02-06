# Phase 34: IDE Integration Update - Research

**Researched:** 2026-02-06
**Domain:** Documentation rewrite (Chapter 4 - IDE Integration)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Chapter restructure:**
- Lead with the problem: "What does IDE integration for a zero-representation language like BBj need?"
- Section flow: Problem -> Continue.dev -> Copilot BYOK limitations -> FIM gap -> Language server / ghost text -> Compiler validation -> Status
- TL;DR stays as architectural overview (high-level two-layer approach), updated for accuracy but not reframed as actionable summary
- bbjcpl compiler validation keeps its own standalone section (it's a differentiator)

**Continue.dev depth:**
- Full config walkthrough -- show config.json with Ollama connection, model setup, autocomplete settings so someone could follow along
- Config shows generic Ollama model (e.g. Qwen2.5-Coder) with a note about where to swap in the fine-tuned BBj model when ready
- Chat mode and tab-completion mode split into clear separate subsections: chat works now with instruction-tuned model, tab completion needs FIM-trained model
- Include comparison table: Continue.dev vs Copilot BYOK vs custom language server -- covering chat, tab completion, BBj awareness, compiler validation, effort to integrate

**What stays vs what goes:**
- Ghost text architecture section: KEEP and expand -- bbj-language-server has VS Code and IntelliJ extensions in the repo (BBx-Kitchen/bbj-language-server), ghost text implementation is a close next milestone, not distant future
- Generation-aware completion (character, vpro5, bbj-gui, dwc): keep as-is, still relevant
- LSP 3.18 section: Claude's discretion on framing (likely path but not confirmed)
- Langium AI section: KEEP -- language server is deeply Langium-based, can't dismiss Langium AI without research and proper decision-making. Contextualize as natural extension of existing Langium architecture, not a throwaway alternative
- "Alternative Architectures" framing goes away -- Continue.dev becomes primary section, Langium AI stays contextualized with the language server

**Tone and framing:**
- Continue.dev and language server framed as parallel strategies: Continue.dev for model delivery, language server for BBj-specific intelligence -- they complement, not compete
- Progress-focused tone: "here's what we've built, here's the pragmatic next step, here's where it's all heading" -- emphasize momentum
- Copilot BYOK: contrast directly with Continue.dev -- show why BYOK falls short (chat only, no inline) and why Continue.dev fills that gap
- Status section uses established Phase 32 terminology: operational / operational for internal exploration / active research / planned

### Claude's Discretion

- LSP 3.18 section framing and hedging level
- Exact structure of the comparison table columns/rows
- How to integrate the FIM training gap explanation (subsection vs callout)
- Typography and spacing within the config walkthrough

### Deferred Ideas (OUT OF SCOPE)

None -- discussion stayed within phase scope

</user_constraints>

## Summary

This phase rewrites Chapter 4 (IDE Integration) to restructure around Continue.dev as the primary near-term integration path, clearly document Copilot BYOK limitations, explain the FIM training gap for tab completion, and reframe the bbj-language-server + ghost text as a close next milestone rather than distant aspiration. The current chapter is 520 lines and treats Continue.dev as an "alternative architecture" -- the rewrite promotes it to a primary section with a full config walkthrough.

The research confirms all five key technology domains with high confidence. Continue.dev (v1.5.34) fully supports Ollama for both chat and autocomplete roles via config.yaml with well-documented configuration. Copilot BYOK explicitly does not support inline completions for local/BYOK models -- this is confirmed across multiple official sources. The FIM training gap is real and well-documented: ChatML instruction-tuned models structurally cannot perform FIM, which is required for tab completion. The bbj-language-server (v0.5.0, 508 commits, 13 contributors) has both VS Code and IntelliJ extensions in the repo. Langium AI tools (v0.0.2) target Langium 3.4.x and have not been updated for Langium 4.x compatibility; the project has moved to eclipse-langium/langium-ai.

**Primary recommendation:** Structure the rewrite in two waves: (1) core content restructure with new Continue.dev section, Copilot BYOK contrast, and FIM gap explanation; (2) language server sections update, status block rewrite, and full-file consistency pass.

## Standard Stack

This phase involves editing a single Markdown file in a Docusaurus 3.9.2 site.

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Docusaurus | 3.9.2 | Site framework | Existing project stack |
| Markdown | N/A | Content format | Chapter 4 is `.md` (not `.mdx`) |
| `npm run build` | N/A | Build verification | Ensures no broken links or syntax |

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| Mermaid diagrams | Architecture visualization | Chapter already uses Mermaid for flow diagrams |

No new installations needed.

## Architecture Patterns

### File Location

```
docs/
└── 04-ide-integration/
    └── index.md          # Chapter 4 -- the only file to edit
```

This is a single-file chapter (520 lines currently). No sub-pages or supporting assets.

### Pattern: Chapter Structure Convention (from Phase 32)

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

No dates in status blocks. Use bullet points with bold status labels.

### Pattern: Prohibited Terminology

| Prohibited | Replace With |
|------------|-------------|
| "shipped" | "operational" or "available" |
| "production" | "operational for internal exploration" or remove |
| "deployed" (as final state) | "operational for internal exploration" |
| "production-grade" | "functional" or remove |
| "in progress" | "active research" or "operational for internal exploration" |

## Continue.dev Research Findings

### Current State (HIGH confidence)

| Attribute | Value | Source |
|-----------|-------|--------|
| Current version | v1.5.34 (January 2026) | GitHub releases page |
| IDE support | VS Code + JetBrains (IntelliJ, PyCharm, WebStorm) | Official docs |
| License | Apache 2.0 | GitHub |
| Config format | YAML (`config.yaml`) -- JSON is deprecated | Official docs |
| Config location | `~/.continue/config.yaml` | Official docs |
| Ollama support | Built-in provider, auto-detected capabilities | Official docs |
| Model roles | chat, autocomplete, edit, apply, embed, rerank, summarize | config.yaml reference |

### Configuration Format (HIGH confidence)

Continue.dev uses `config.yaml` (JSON `config.json` is deprecated but still works). The key insight for the chapter: a single config file can define separate models for chat and autocomplete roles.

**Complete working config for the chapter's walkthrough:**

```yaml
name: BBj AI Assistant
version: 0.0.1
schema: v1
models:
  # Chat model -- instruction-tuned, works today
  - name: Qwen2.5 Coder 14B
    provider: ollama
    model: qwen2.5-coder:14b
    roles:
      - chat
      - edit
      - apply

  # Autocomplete model -- FIM-capable, works today with generic model
  - name: Qwen2.5 Coder 1.5B Autocomplete
    provider: ollama
    model: qwen2.5-coder:1.5b
    roles:
      - autocomplete
    autocompleteOptions:
      maxPromptTokens: 1024
      debounceDelay: 250
      modelTimeout: 150
      maxSuffixPercentage: 0.2
      prefixPercentage: 0.3
      multilineCompletions: always

context:
  - provider: code
  - provider: docs
  - provider: diff
  - provider: terminal
  - provider: problems
  - provider: folder
  - provider: codebase
```

**Important config notes:**
- `autocompleteOptions` parameters: `maxPromptTokens` (1024), `debounceDelay` (250ms), `modelTimeout` (150ms), `maxSuffixPercentage` (0.2), `prefixPercentage` (0.3), `onlyMyCode` (true/false), `multilineCompletions` ("always"/"never"/"auto")
- Autocomplete models are intentionally small (1.5B-7B) -- large models are too slow for inline completion
- Official recommended autocomplete models: Codestral (closed), Qwen2.5-Coder 1.5B/7B (open/local)
- The config shows where to swap in `bbj-coder:14b` for chat and `bbj-coder-fim:1.5b` for autocomplete when fine-tuned models are ready

### Chat vs Tab Completion: The FIM Gap (HIGH confidence)

This is the critical distinction the chapter must make clear:

| | Chat Mode | Tab Completion (Autocomplete) |
|---|---|---|
| **How it works** | User asks question, model responds | Inline ghost text appears as you type |
| **Model format** | ChatML / instruction-tuned | FIM (Fill-in-the-Middle) |
| **Model size** | 7B-14B+ (larger is better) | 1.5B-7B (speed matters more) |
| **Works with current BBj training data** | YES -- ChatML format matches | NO -- ChatML cannot do FIM |
| **Special tokens** | `<|im_start|>`, `<|im_end|>` | `<|fim_prefix|>`, `<|fim_suffix|>`, `<|fim_middle|>` |
| **Continue.dev role** | `chat`, `edit`, `apply` | `autocomplete` |

**The gap:** Current bbjllm training data (9,922 examples) is in ChatML instruction format. This works for chat but structurally cannot produce FIM completions. Tab completion requires a separate FIM fine-tuning step on BBj code, producing training examples in the format:

```
<|fim_prefix|>{code before cursor}<|fim_suffix|>{code after cursor}<|fim_middle|>{code to generate}<|endoftext|>
```

This is called the PSM (Prefix-Suffix-Middle) strategy. The Base model (Qwen2.5-Coder-14B-Base) already has FIM capability from pretraining -- fine-tuning on BBj code in FIM format would teach it BBj-specific patterns while preserving FIM capability.

### Continue.dev Architecture Notes

Continue.dev's autocomplete implementation:
- Uses VS Code's `InlineCompletionItemProvider` API internally (same as described in the ghost text section)
- Sends FIM-formatted prompts to Ollama via `/api/generate` endpoint
- Includes context from: current file prefix/suffix, open files, recently edited files, LSP definitions
- Template is customizable via `autocompleteOptions.template` (Mustache syntax)
- Debounce prevents triggering on every keystroke (default 250ms)

## Copilot BYOK Research Findings

### Current State (HIGH confidence)

| Attribute | Value | Source |
|-----------|-------|--------|
| Inline completions with BYOK | NOT SUPPORTED | Official VS Code docs, VS Code blog |
| Chat with BYOK | Supported (Ask Mode only for local models) | Official docs |
| Agent Mode with BYOK | Requires tool_use capability | Official docs |
| Ollama as provider | Supported as built-in provider | Official docs |
| Enterprise/Business BYOK | Public preview as of Jan 2026 | GitHub changelog |
| Individual BYOK | Available | Official docs |

### Key Limitation Statement (HIGH confidence)

From VS Code official docs: "BYOK does not currently work with completions." And: "Only applies to the chat experience and doesn't affect inline suggestions or other AI-powered features."

This is the core contrast with Continue.dev: Copilot BYOK gives you chat with a local model but NOT inline completions. Continue.dev gives you BOTH chat AND inline completions with a local model.

### BYOK January 2026 Enhancements

The January 15, 2026 changelog added:
- Responses API support (structured outputs)
- Context window configuration
- Streaming responses
- Expanded providers: AWS Bedrock, Google AI Studio, OpenAI-compatible (joining Anthropic, Microsoft Foundry, OpenAI, xAI)

Notably absent: inline completions for BYOK models. Still not supported.

### Enterprise Availability Update

As of January 2026, Enterprise BYOK is in public preview. The current chapter states "BYOK is not yet available for Copilot Business or Enterprise plans" -- this needs updating. Enterprise/Business BYOK is now in public preview with admin configuration through organization/enterprise settings.

### Copilot Service Dependencies

Even with BYOK, the Copilot service is still required for: embeddings, repository indexing, query refinement, intent detection, and side queries. This means BYOK is not a fully local solution -- it still requires internet connectivity and an active Copilot subscription.

## FIM Training Gap Research Findings

### Why ChatML Cannot Do FIM (HIGH confidence)

Source: Qwen2.5-Coder technical report (arxiv.org/html/2409.12186v1), academic research on FIM vs chat format incompatibility.

The structural conflict:
1. **Base models** learn FIM during pretraining alongside next-token prediction. They understand `<|fim_prefix|>...<|fim_suffix|>...<|fim_middle|>` natively.
2. **Instruction-tuned models** have post-training alignment that wraps everything in chat templates (`<|im_start|>system...`, `<|im_start|>user...`). This structurally conflicts with FIM special tokens.
3. **ChatML training data** (like bbjllm's 9,922 examples) teaches the model to respond in chat format. Fine-tuning a Base model on ChatML-only data would overwrite the FIM capability learned during pretraining.

The practical consequence: to support BOTH chat and tab completion, you need either:
- Two separate models (instruction-tuned for chat, FIM-trained for autocomplete) -- Continue.dev supports this natively with separate `roles`
- A model trained with mixed FIM + instruction data (like Qwen2.5-Coder's own training, which uses "a majority of standard SFT data and a small part of FIM instruction samples")

### FIM Training Data Format (HIGH confidence)

The Qwen2.5-Coder FIM format uses four special tokens:
- `<|fim_prefix|>` (token ID 151659) -- code before the gap
- `<|fim_suffix|>` (token ID 151661) -- code after the gap
- `<|fim_middle|>` (token ID 151660) -- code to predict (the target)
- `<|fim_pad|>` (token ID 151662) -- padding during FIM

PSM (Prefix-Suffix-Middle) strategy format:
```
<|fim_prefix|>{prefix_code}<|fim_suffix|>{suffix_code}<|fim_middle|>{middle_code}<|endoftext|>
```

### FIM Fine-Tuning for BBj (MEDIUM confidence)

Based on the llama.vscode GitHub issue #40 and community practice:
- FIM training data is created by sampling random positions in source files and splitting into prefix/suffix/middle
- Typical approach: random file selection, random cursor position, extract middle (up to 256 chars for single-line, longer for multi-line), prefix (up to 2048 chars), suffix (up to 1024 chars)
- Training on Qwen2.5-Coder-7B-Base with 60,000 FIM samples from ~2,000 code files reportedly produced satisfactory results
- LoRA fine-tuning works for FIM (same as instruction fine-tuning)
- tree-sitter can be used to identify syntactically meaningful split points

### Connection to Phase 33 Decisions

Phase 33 established:
- Qwen2.5-Coder-14B-Base as primary recommendation
- Two-stage training: continued pretraining + instruction fine-tuning
- Current training data is ChatML-only (9,922 examples)

The FIM gap means: after the two-stage instruction fine-tuning described in Chapter 3, the model will support chat but NOT tab completion. A separate FIM fine-tuning step (on BBj source code in FIM format) would be needed for tab completion. This is the gap the chapter must document.

## bbj-language-server Research Findings

### Current State (HIGH confidence)

| Attribute | Value | Source |
|-----------|-------|--------|
| Version | v0.5.0 (January 22, 2026) | GitHub releases |
| Commits | 508 on main branch | GitHub |
| Contributors | 13 | GitHub |
| Open PRs | 12 | GitHub |
| Open Issues | 61 | GitHub |
| Framework | Langium (v4.x) | GitHub |
| Languages | TypeScript 67.3%, Java 26.7%, Langium 4.2%, JS 1.6% | GitHub |
| License | MIT | GitHub |

### Repository Structure (HIGH confidence)

The repo contains these top-level directories:
- `bbj-vscode` -- VS Code extension with language server (primary)
- `bbj-intellij` -- IntelliJ IDE support (confirmed in repo)
- `java-interop` -- Java executable providing classpath info via JSON-RPC
- `documentation` -- User and developer guides
- `examples` -- Sample code files
- `QA` -- Testing resources

**Key finding:** The `bbj-intellij` directory confirms IntelliJ extension support exists in the repo. This validates the user's statement that "bbj-language-server has VS Code and IntelliJ extensions in the repo."

### VS Code Marketplace Listing

Publisher: BEU (extension ID: `BEU.bbj-vscode`). The extension provides:
- Syntax highlighting (full BBj grammar including all four generational syntaxes)
- Code completion (Langium-powered symbol completion with scope awareness)
- Diagnostics (real-time error detection)
- Code formatting
- BBj Properties viewing
- Code execution (run BBj programs from VS Code)
- Enterprise Manager integration

### AI Integration Status

No evidence of ghost text, inline completion, or AI integration features in the current codebase. The AI completion features (InlineCompletionItemProvider, semantic context API, generation detection) described in the current chapter are planned, not implemented. The chapter should make this clear while framing ghost text as a close next milestone.

### Update from Current Chapter

The current chapter says "v0.5.0 (January 2026)" and "450+ commits" -- update to "508 commits" based on current data. The 13 contributors figure is still accurate.

## Langium AI Tools Research Findings

### Current State (MEDIUM confidence)

| Attribute | Value | Source |
|-----------|-------|--------|
| Original repo | TypeFox/langium-ai (ARCHIVED Sept 2025) | GitHub |
| New repo | eclipse-langium/langium-ai | GitHub |
| NPM package | `langium-ai-tools` | TypeFox blog |
| Last published version | v0.0.2 | TypeFox blog, web search |
| Target Langium version | 3.4.x | TypeFox blog |
| Current Langium version | 4.2.0 | npm |
| Langium 4.x compatibility | NOT CONFIRMED -- version gap exists | Research finding |
| Published npm packages | None from eclipse-langium/langium-ai | GitHub |
| Commits (new repo) | 15 | GitHub |
| Stars (new repo) | 20 | GitHub |

### What langium-ai-tools Provides (HIGH confidence)

From the TypeFox blog (June 2025):

1. **Evaluation pipelines** -- Composable `Evaluator` objects that score LLM output. "LLM output goes in (such as a generated DSL program), and evaluation results come out as a score." Multiple evaluators can be chained.

2. **DSL-aware splitting** -- Breaks DSL documents at syntactic boundaries. Leverages AST types and concrete syntax tree offsets. Can detect comment blocks and associate them with related code units. Useful for RAG, indexing, and citations.

3. **Constraint generation** -- Derives BNF-style grammars from Langium grammars to restrict LLM token output. "Automates the generation of constraints on output tokens from LLMs, which directly correspond to the valid syntax of the DSL."

### The Langium 4.x Compatibility Gap (MEDIUM confidence)

- langium-ai-tools v0.0.2 targets Langium 3.4.x
- bbj-language-server is built on Langium 4.x
- Langium is now at 4.2.0
- The eclipse-langium/langium-ai repo has 15 commits and no published npm packages
- No evidence found that langium-ai-tools has been updated for Langium 4.x

**What changed in Langium 4.0:** Strict mode for grammars, infix operator support, improved AST generation (`$type` constants), namespace support. The blog post refers to the CHANGELOG for breaking changes but does not enumerate them. The structural changes to AST generation could affect langium-ai-tools' evaluators and splitters.

### Recommendation for the Chapter

The current chapter's framing is largely correct: "langium-ai-tools (v0.0.2) targets Langium 3.4.x, while the bbj-language-server is built on Langium 4.x. Whether the tools will be updated for Langium 4.x compatibility is not yet clear."

The update should:
- Note the repo has moved to eclipse-langium/langium-ai (from TypeFox/langium-ai, archived Sept 2025)
- Keep the "initiative to watch" framing but contextualize it more positively: since both Langium and langium-ai are now under the Eclipse Langium umbrella, version alignment is likely (same organization maintains both)
- Emphasize that the language server's deep Langium foundation makes it a natural fit for Langium AI tools once compatibility is resolved
- Frame as "natural extension of existing architecture" per user decision, not "alternative architecture"

## Comparison Table Research

For the user-requested comparison table (Continue.dev vs Copilot BYOK vs Custom Language Server), here are the verified facts:

| Feature | Continue.dev | Copilot BYOK | Custom Language Server |
|---------|-------------|-------------|----------------------|
| **Chat with local model** | Yes (Ollama) | Yes (Ask Mode only) | Planned (via MCP) |
| **Tab completion with local model** | Yes (FIM-capable models) | No (BYOK does not support completions) | Planned (InlineCompletionItemProvider) |
| **BBj language awareness** | None (generic) | None (generic) | Full (Langium parser, AST, scope) |
| **Generation detection** | No | No | Planned (character/vpro5/bbj-gui/dwc) |
| **Compiler validation** | No | No | Planned (bbjcpl in-the-loop) |
| **Multi-editor support** | VS Code + JetBrains | VS Code only | VS Code + IntelliJ (extensions in repo) |
| **Effort to integrate** | Low (config file only) | Low (built-in) | High (custom extension development) |
| **Model flexibility** | Any Ollama model | Any supported provider | Ollama (custom integration) |
| **Subscription required** | No (open source) | Yes (Copilot plan + internet) | No |
| **Status** | Available today | Available today (chat only) | Active research / planned |

## Recommended Chapter Structure

Based on the user's decisions and research findings:

```
# IDE Integration
  :::tip[TL;DR]
  [Updated: two-layer architecture + Continue.dev as near-term delivery path]

  [Intro: "What does IDE integration for a zero-representation language need?"]

## The Near-Term Path: Continue.dev                    [NEW PRIMARY SECTION]
  ### Chat Mode: Works Today
  - Instruction-tuned model via Ollama
  - Config walkthrough with Qwen2.5-Coder-14B
  - Note about swapping in fine-tuned BBj model
  ### Tab Completion: Needs FIM-Trained Model
  - FIM format explanation (subsection or callout -- Claude's discretion)
  - Config walkthrough with Qwen2.5-Coder-1.5B
  - Note about where BBj FIM model would go
  ### The FIM Training Gap
  - ChatML vs FIM format incompatibility
  - What it means for current training data
  - Path forward: FIM fine-tuning step on BBj source code

## Why Not Copilot?                                    [REFRAMED FROM "The Copilot Bridge"]
  - What BYOK offers (chat, provider support)
  - What BYOK does NOT offer (inline completions)
  - Enterprise BYOK now in public preview (update from current)
  - Comparison table: Continue.dev vs Copilot BYOK vs Language Server

## The Foundation: bbj-language-server                 [KEPT, MINOR UPDATES]
  - v0.5.0, 508 commits, 13 contributors
  - Langium framework, VS Code + IntelliJ extensions
  - Why Langium matters (semantic context)

## Two Completion Mechanisms                           [KEPT AS-IS]
  - Popup vs ghost text comparison table

## Ghost Text Architecture                             [KEPT, EXPANDED]
  - InlineCompletionItemProvider pattern
  - Semantic context API (bbj/semanticContext)
  - Mermaid diagram
  - Framed as "close next milestone"

## Generation-Aware Completion                         [KEPT AS-IS]
  - character/vpro5/bbj-gui/dwc detection
  - Semantic context interface

## Compiler Validation                                 [KEPT AS-IS, STANDALONE]
  - generate-validate-fix loop
  - bbjcpltool PoC
  - bbjcpl -N syntax validation
  - MCP tool integration

## LSP 3.18: Server-Side Inline Completion            [KEPT, Claude's discretion on framing]
  - textDocument/inlineCompletion
  - Multi-editor potential

## Langium AI: Extending the Language Server          [REFRAMED from "Alternative Architectures"]
  - Contextualized as natural extension of Langium architecture
  - Evaluation pipelines, DSL-aware splitting, constraint generation
  - Version gap note (v0.0.2 targets Langium 3.4.x, server on 4.x)
  - Now under eclipse-langium umbrella (positive signal for convergence)

## Current Status                                      [REPLACED with Phase 32 conventions]
  :::note[Where Things Stand]
  - Operational: bbj-language-server v0.5.0 (VS Code Marketplace)
  - Operational: bbjcpltool v1 (compiler-in-the-loop validated)
  - Active research: Continue.dev evaluation as IDE integration path
  - Active research: Copilot BYOK integration (chat only)
  - Planned: Ghost text completion via InlineCompletionItemProvider
  - Planned: FIM fine-tuning for tab completion
  - Planned: Generation detection, semantic context API
  :::

## What Comes Next                                     [KEPT, UPDATED]
```

### Key Structural Changes from Current Chapter

1. **Continue.dev promoted** from 6-line subsection under "Alternative Architectures" to primary section with full config walkthrough
2. **Copilot section reframed** from "The Copilot Bridge" to "Why Not Copilot?" with direct Continue.dev contrast
3. **FIM gap** integrated into Continue.dev section (or as standalone subsection -- Claude's discretion)
4. **"Alternative Architectures" heading eliminated** -- Continue.dev and Langium AI get their own sections
5. **Langium AI recontextualized** as natural extension of the language server's Langium architecture
6. **Language server sections** (foundation, two mechanisms, ghost text, generation-aware, compiler validation) preserved but repositioned after the "pragmatic now" sections

## Current Chapter Analysis: Section-by-Section

### Current Section Inventory

| # | Section | Lines | Fate | Requirement |
|---|---------|-------|------|-------------|
| 1 | YAML front matter | 1-5 | **Modify** | Update description |
| 2 | `# IDE Integration` | 7 | Keep | |
| 3 | `:::tip[TL;DR]` | 9-11 | **Modify** | Add Continue.dev as near-term path, keep two-layer concept |
| 4 | Intro paragraphs | 13-17 | **Replace** | New problem-focused intro per user decision |
| 5 | `## The Foundation: bbj-language-server` | 19-57 | **Move + minor modify** | Moves after Continue.dev/Copilot sections; update commit count |
| 6 | `## Two Completion Mechanisms` | 59-81 | **Move** | Moves with language server sections |
| 7 | Ghost Text Architecture (subsection) | 83-169 | **Move + expand** | Frame as close next milestone |
| 8 | `## Generation-Aware Completion` | 171-296 | **Keep** | Still relevant, keep as-is |
| 9 | `## Compiler Validation` | 298-383 | **Keep** | Standalone section, differentiator |
| 10 | `## LSP 3.18` | 385-436 | **Keep** | Claude's discretion on framing |
| 11 | `## The Copilot Bridge` | 438-474 | **Replace** | Becomes "Why Not Copilot?" with contrast to Continue.dev |
| 12 | `## Alternative Architectures` | 476-497 | **Eliminate heading** | Continue.dev becomes primary section; Langium AI gets own section |
| 13 | `## Current Status` | 499-508 | **Replace** | Phase 32 terminology |
| 14 | `## What Comes Next` | 510-520 | **Modify** | Update cross-references |

### New Sections Required

| New Section | Requirement | Size Estimate |
|-------------|------------|---------------|
| Problem-focused intro | User decision | 15-25 lines |
| Continue.dev primary section | IDE-01 | 100-150 lines (config walkthrough, chat/tab split, FIM gap) |
| Comparison table | User decision | 20-30 lines |
| Langium AI recontextualized section | User decision | 30-40 lines |

### Estimated Total Size

Current: ~520 lines. Estimated rewritten: ~550-650 lines. The Continue.dev section adds significant content, but eliminating the "Alternative Architectures" framing and tightening the Copilot section offsets some of it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Continue.dev config examples | Guess at format | Copy from official docs (verified YAML format above) | Config format is specific; wrong examples destroy credibility |
| FIM token format | Describe from memory | Use exact tokens from Qwen2.5-Coder technical report | Token IDs and format are precise |
| Copilot BYOK limitations | Paraphrase | Quote/cite official VS Code docs | Negative claims need authoritative backing |
| Build verification | Visual inspection | `npm run build` | Catches broken links, Mermaid syntax |
| Terminology consistency | Manual reading | Grep for "shipped", "production", "in progress" | Phase 32 conventions must be followed |

**Key insight:** The Continue.dev config walkthrough must use verified YAML format (not deprecated JSON) with actual field names and default values. Getting the config wrong would undermine the chapter's credibility as a practical guide.

## Common Pitfalls

### Pitfall 1: Using Deprecated JSON Config Format

**What goes wrong:** The Continue.dev config walkthrough shows `config.json` format (with `tabAutocompleteModel` key) instead of the current `config.yaml` format.
**Why it happens:** Many blog posts and tutorials still show the JSON format. Claude's training data likely includes more JSON examples.
**How to avoid:** Use the verified YAML format from this research. The key is `models:` array with `roles:` list, not `tabAutocompleteModel`.
**Warning signs:** Config examples starting with `{` instead of `name:`.

### Pitfall 2: Overstating Copilot BYOK Enterprise Availability

**What goes wrong:** The current chapter says "BYOK is not yet available for Copilot Business or Enterprise plans -- only individual subscriptions." This is now outdated -- Enterprise BYOK entered public preview in November 2025.
**Why it happens:** The chapter was written before the November 2025 changelog.
**How to avoid:** Update to: Enterprise/Business BYOK is in public preview as of January 2026. But the core limitation (no inline completions) remains unchanged regardless of plan tier.
**Warning signs:** Any text that says Enterprise BYOK is "not available."

### Pitfall 3: Conflating Chat and Tab Completion

**What goes wrong:** The chapter implies that having a fine-tuned BBj model means full IDE integration (both chat and tab completion), without explaining that these require fundamentally different training formats.
**Why it happens:** It is natural to think "fine-tuned model = better everywhere." The FIM gap is a technical nuance.
**How to avoid:** The Continue.dev section must explicitly split chat and tab completion into separate subsections with different model requirements. The FIM gap should be explained before showing the autocomplete config.
**Warning signs:** Config walkthrough that shows the same model for both chat and autocomplete roles.

### Pitfall 4: Dismissing Langium AI as Irrelevant

**What goes wrong:** Because langium-ai-tools targets Langium 3.4.x and the language server is on 4.x, the section is written dismissively.
**Why it happens:** The version gap is real and easy to frame as a blocker.
**How to avoid:** Per user decision: "can't dismiss Langium AI without research and proper decision-making." The key reframe: both Langium and langium-ai are now under the Eclipse Langium umbrella (same organization), making version alignment likely. The tools' capabilities (evaluation pipelines, constraint generation) are directly relevant to the language server's goals.
**Warning signs:** Language like "incompatible", "obsolete", "abandoned."

### Pitfall 5: Breaking Cross-References

**What goes wrong:** Restructuring changes section headings, breaking links from other chapters.
**Why it happens:** Docusaurus auto-generates anchors from headings.
**How to avoid:** Inventory incoming links before restructuring. Preserve critical anchors or note them for Phase 36.
**Warning signs:** `npm run build` reports broken links.

### Pitfall 6: Inconsistent Status Terminology

**What goes wrong:** New sections use "operational" but retained sections still say "shipped" or "in progress."
**Why it happens:** Retained sections look "done" and get skimmed.
**How to avoid:** After all content changes, do a full-file grep for prohibited terms.
**Warning signs:** Mixed terminology in the same chapter.

## Cross-Reference Inventory

### Incoming Links to Chapter 4

| Source | Link Target | Context |
|--------|------------|---------|
| Chapter 1 (line 316) | `/docs/ide-integration` | "See IDE Integration for the AI-powered extension roadmap" |
| Chapter 1 (line 320) | Continue.dev mention | "Continue.dev is being evaluated as primary IDE integration path" |
| Chapter 2 (line 306) | "VSCode Extension (Chapter 4)" heading | Architecture component reference |
| Chapter 2 (line 388) | `/docs/ide-integration` | Chapter list |
| Chapter 5 (line 301) | `/docs/ide-integration` | "IDE clients (Chapter 4) can leverage the same retrieval..." |
| Chapter 6 (line 439) | `/docs/ide-integration` | "IDE extension uses the retrieval API..." |
| Chapter 6 (line 533) | `/docs/ide-integration` | Cross-reference list |
| Chapter 7 (line 98) | `/docs/ide-integration` | Phase 2 objective |
| Chapter 7 (line 104) | `/docs/ide-integration` | Generation detection reference |
| Chapter 7 (line 108) | `/docs/ide-integration#compiler-validation-ground-truth-syntax-checking` | Direct anchor link |
| Chapter 7 (line 306) | `/docs/ide-integration` | Cross-reference list |

### Critical Anchors to Preserve

- `#compiler-validation-ground-truth-syntax-checking` -- Chapter 7 links directly to this anchor. If the heading changes, this link breaks.
- `/docs/ide-integration` -- General chapter link, always works as long as file exists.

**Recommendation:** Keep the "Compiler Validation" section heading close to its current form to preserve the anchor. If it must change, note the broken anchor for Phase 36.

## Code Examples

### Continue.dev Config with Ollama (Verified)

```yaml
# Source: https://docs.continue.dev/customize/deep-dives/autocomplete
# and https://docs.continue.dev/reference
name: BBj Development
version: 0.0.1
schema: v1
models:
  # Chat: use the larger instruction-tuned model
  - name: Qwen2.5 Coder 14B
    provider: ollama
    model: qwen2.5-coder:14b
    roles:
      - chat
      - edit
      - apply

  # Autocomplete: use the smaller FIM-capable model
  - name: Qwen2.5 Coder 1.5B
    provider: ollama
    model: qwen2.5-coder:1.5b
    roles:
      - autocomplete
    autocompleteOptions:
      debounceDelay: 250
      multilineCompletions: always
```

### FIM Token Format (Verified)

```
# Source: Qwen2.5-Coder Technical Report (arxiv.org/html/2409.12186v1)
# PSM (Prefix-Suffix-Middle) strategy

<|fim_prefix|>method public void loadOrder(BBjNumber orderId)
    #currentOrderId = orderId
    declare BBjRecordSet rs!
    rs! = #getOrderRecordSet(orderId)
    #custGrid!.<|fim_suffix|>
    methodend<|fim_middle|>setData(rs!)<|endoftext|>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Continue.dev JSON config | Continue.dev YAML config | 2025 | Must use `config.yaml` format |
| Copilot BYOK individual only | Enterprise/Business BYOK in public preview | Nov 2025 | Chapter needs update |
| TypeFox/langium-ai repo | eclipse-langium/langium-ai | Sept 2025 | Repo archived, moved to Eclipse org |
| Continue.dev as "architectural reference" | Continue.dev as primary IDE integration path | User decision | Major chapter restructure |

## Plan Wave Recommendation

### Option A: Two Waves (Recommended)

**Wave 1: Core content restructure**
- New problem-focused intro
- New Continue.dev primary section (config walkthrough, chat/tab split, FIM gap)
- Rewrite Copilot section as "Why Not Copilot?" with comparison table
- Rewrite TL;DR
- Eliminate "Alternative Architectures" heading

**Wave 2: Language server sections + status + cleanup**
- Reposition language server sections (move after Continue.dev/Copilot)
- Expand ghost text section (close next milestone framing)
- Recontextualize Langium AI section
- Update bbj-language-server stats (508 commits)
- Replace status block with Phase 32 conventions
- Full-file tone pass (prohibited terminology grep)
- Build verification + anchor check

**Rationale:** Wave 1 does all the new writing and structural changes. Wave 2 does repositioning, updates, and consistency cleanup. This keeps each wave focused and manageable.

## Open Questions

1. **Should the config walkthrough use config.yaml or config.json?**
   - What we know: YAML is the current format; JSON is deprecated but still works.
   - Resolution: Use YAML. The user decision says "show config.json" but this likely refers to the concept (showing a config file), not the literal format. Using the deprecated JSON format would be immediately outdated.
   - Recommendation: Use YAML with a note that JSON format also works but is deprecated.

2. **Where exactly to position the FIM training gap explanation?**
   - What we know: User said "Claude's discretion" on whether subsection or callout.
   - Recommendation: Make it a subsection within the Continue.dev section ("The FIM Training Gap"). It needs enough space for the token format explanation, the ChatML/FIM contrast, and the connection to Chapter 3's training data decisions. A callout would be too cramped.

3. **How to frame LSP 3.18 given uncertainty?**
   - What we know: LSP 3.18 is a real spec with real editor adoption (Neovim has support). But it is not confirmed as the bbj-language-server's migration path.
   - Recommendation: Keep the section but soften to "potential migration path." Frame as: "If the bbj-language-server implements textDocument/inlineCompletion, it gains multi-editor AI completion support without per-editor extension code." This is factually true without overpromising.

4. **How much Langium 4.x breaking change detail to include?**
   - What we know: Langium 4.0 has breaking changes (strict mode, AST generation, infix operators). The specifics are in the CHANGELOG but not readily available.
   - Recommendation: Don't enumerate breaking changes. Say: "langium-ai-tools v0.0.2 targets Langium 3.4.x. The bbj-language-server is built on Langium 4.x. Both projects are now under the Eclipse Langium umbrella, suggesting version alignment is a matter of when, not if."

## Sources

### Primary (HIGH confidence)

- Continue.dev official docs -- autocomplete config, model roles, Ollama setup: https://docs.continue.dev/customize/deep-dives/autocomplete
- Continue.dev config.yaml reference: https://docs.continue.dev/reference
- Continue.dev Ollama provider docs: https://docs.continue.dev/customize/model-providers/top-level/ollama
- VS Code official docs -- BYOK language models: https://code.visualstudio.com/docs/copilot/customization/language-models
- VS Code blog -- BYOK announcement: https://code.visualstudio.com/blogs/2025/10/22/bring-your-own-key
- GitHub changelog -- BYOK enhancements Jan 2026: https://github.blog/changelog/2026-01-15-github-copilot-bring-your-own-key-byok-enhancements/
- Qwen2.5-Coder technical report -- FIM training details: https://arxiv.org/html/2409.12186v1
- bbj-language-server GitHub repo: https://github.com/BBx-Kitchen/bbj-language-server

### Secondary (MEDIUM confidence)

- TypeFox blog -- Langium AI tools: https://www.typefox.io/blog/langium-ai-the-fusion-of-dsls-and-llms/
- eclipse-langium/langium-ai GitHub: https://github.com/eclipse-langium/langium-ai
- TypeFox blog -- Langium 4.0 release: https://www.typefox.io/blog/langium-release-4.0/
- llama.vscode issue #40 -- FIM fine-tuning discussion: https://github.com/ggml-org/llama.vscode/issues/40
- Continue.dev GitHub releases -- version info: https://github.com/continuedev/continue/releases

### Tertiary (LOW confidence)

- Community blog posts on FIM vs ChatML format incompatibility (consistent across multiple sources but not from official Qwen documentation)

## Metadata

**Confidence breakdown:**
- Continue.dev config/capabilities: HIGH -- verified against official docs
- Copilot BYOK limitations: HIGH -- verified across multiple official VS Code sources
- FIM training gap: HIGH -- confirmed by Qwen technical report and multiple academic sources
- bbj-language-server state: HIGH -- verified against GitHub repo
- Langium AI tools state: MEDIUM -- version gap confirmed but future compatibility is speculation
- Chapter restructure recommendations: HIGH -- based on verified facts and user decisions

**Research date:** 2026-02-06
**Valid until:** 2026-03-06 (documentation editing task; findings stable unless tools release major updates)
