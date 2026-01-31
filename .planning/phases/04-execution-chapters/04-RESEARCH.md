# Phase 4: Execution Chapters - Research

**Researched:** 2026-01-31
**Domain:** Documentation content authoring (Chapters 4-7) covering IDE integration, documentation chat, RAG database design, and implementation roadmap -- plus cross-chapter quality pass
**Confidence:** MEDIUM (overall -- varies by topic; see breakdown below)

## Summary

This phase writes four execution-depth chapters (4-7) and performs a cross-cutting quality pass across all seven chapters. Unlike prior phases, the "standard stack" here is not libraries to install but rather the **subject matter each chapter must cover accurately**. The research therefore focuses on: (1) the current state of the art for each chapter's technical domain, (2) Docusaurus content patterns proven in Chapters 1-3, and (3) the actual bbj-language-server repository and BBj ecosystem details that anchor the chapters in reality.

**Key findings across all four chapter domains:**

- **Chapter 4 (IDE Integration):** The bbj-language-server (v0.5.0, Langium-based, MIT licensed, 450+ commits) is a real, shipped product on the VS Code Marketplace. The Copilot landscape has shifted dramatically -- the Copilot extension is being deprecated in early 2026 and merged into Copilot Chat, BYOK with Ollama is supported for chat but NOT for inline completions, and LSP 3.18 adds `textDocument/inlineCompletion` as a formal protocol feature. Langium AI (from TypeFox) provides tools for bridging DSLs and LLMs. The two-path architecture (custom LLM client vs Copilot bridge) is well-grounded in current technical reality.

- **Chapter 5 (Documentation Chat):** The doc chat space has matured with kapa.ai, DocsBot AI, and similar commercial products. For BBj's custom model requirement, self-hosted alternatives (Open WebUI, custom RAG chat) are the relevant architecture. The chapter should present architectural requirements without committing to a specific deployment model, per CONTEXT.md decisions.

- **Chapter 6 (RAG Database):** The RAG field has evolved significantly -- semantic chunking with contextual headers, hybrid search (BM25 + dense embeddings), and cross-encoder reranking are standard best practices in 2025/2026. For BBj's corpus size (likely under 50,000 chunks), pgvector on PostgreSQL is the pragmatic default vector store. MadCap Flare stores content as W3C-compliant XHTML topics and can export Clean XHTML for pipeline ingestion. Embedding model fine-tuning for specialized domains is now accessible with as few as 1,000-5,000 samples.

- **Chapter 7 (Implementation Roadmap):** Enterprise AI implementation patterns recommend phased rollout with explicit checkpoints. The NIST AI Risk Management Framework provides a credible risk assessment structure. Cost frameworks should separate hardware/infrastructure from staffing (per CONTEXT.md). The original paper's timeline (6 months) and metrics are reasonable starting points but need updating to reflect current status.

**Primary recommendation:** Write each chapter following Chapter 3's depth pattern (specific tools, configurations, architectural details) but with architecture-first framing (describe requirements and design patterns, then reference current tools as examples). Every chapter gets a Current Status section. The cross-chapter quality pass (04-05) retrofits Chapters 1-3 with Current Status sections and updates Chapter 3's outdated claims.

## Standard Stack

Since this phase is about writing documentation content, "Standard Stack" refers to the Docusaurus authoring tools and the key technical references each chapter must cite.

### Core (Docusaurus Authoring -- Already Configured)

| Tool | Version | Purpose | Status |
|------|---------|---------|--------|
| Docusaurus | 3.9.2 | Site framework | Configured, running |
| `@docusaurus/theme-mermaid` | ^3.9.2 | Architecture diagrams | Installed, theme: neutral/dark |
| Prism BBj grammar | Built-in | Code syntax highlighting | `additionalLanguages: ['bbj']` configured |
| Admonitions (tip, info, note, warning) | Built-in | TL;DR, Decision callouts | Styled in Phase 2 |
| Tabs + TabItem | Built-in | Code comparisons (MDX only) | Proven in Chapter 1 |

### Core (Research References Per Chapter)

| Chapter | Key Reference | Type | Confidence |
|---------|--------------|------|------------|
| Ch 4 | bbj-language-server (BBx-Kitchen, v0.5.0) | GitHub repo | HIGH |
| Ch 4 | Langium framework (v4.1.x, Eclipse Foundation) | Official docs | HIGH |
| Ch 4 | VSCode InlineCompletionItemProvider API | Official API | HIGH |
| Ch 4 | LSP 3.18 textDocument/inlineCompletion | Official spec | HIGH |
| Ch 4 | Langium AI toolbox (TypeFox, langium-ai-tools) | Official blog | MEDIUM |
| Ch 4 | GitHub Copilot BYOK with Ollama | Official docs | HIGH |
| Ch 5 | kapa.ai, DocsBot AI (commercial reference) | Product docs | MEDIUM |
| Ch 5 | Open WebUI (self-hosted chat) | GitHub repo | MEDIUM |
| Ch 6 | RAG chunking/embedding best practices 2025 | Multiple sources | MEDIUM |
| Ch 6 | pgvector (PostgreSQL extension) | Official docs | HIGH |
| Ch 6 | MadCap Flare XHTML content format | Official docs | MEDIUM |
| Ch 7 | NIST AI Risk Management Framework | Official publication | HIGH |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| .md files | .mdx files | Only needed if a chapter uses JSX components (Tabs). Chapters 4-7 likely stay as .md unless cross-generation code comparisons are needed. |
| Standard admonitions | Custom admonition types | Could create custom "Current Status" admonition type via swizzling. However, a `:::note[Current Status]` or `:::info[Current Status]` is simpler and consistent with existing patterns. |

## Architecture Patterns

### Chapter Content Structure (Proven Pattern from Chapters 1-3)

```
---
sidebar_position: N
title: "Chapter Title"
description: "One-line description for SEO and sidebar."
---

# Chapter Title

:::tip[TL;DR]
2-3 sentence executive summary.
:::

[Opening paragraph -- problem statement, why this matters]

## [Technical Content Sections]

[Architecture-first: describe the design/requirements, then reference tools]

:::info[Decision: Key Choice Name]
**Choice:** What was decided
**Rationale:** Why
**Alternatives considered:** Brief list
**Status:** Current state
:::

```mermaid
graph TD
    [Architecture diagram]
```

[Code examples with ```bbj or ```typescript]

## Current Status

[Honest assessment: what's built, in progress, and planned]
[Cross-references to other chapters]
```

### Pattern: Architecture-First, Tools-as-Examples

**What:** Describe the requirements and design patterns first, then reference specific tools/libraries as current implementations. Avoid hard-coding tool recommendations that will date quickly.

**Why:** The LLM/AI ecosystem moves fast. By leading with architecture ("the system needs a vector store with hybrid search and metadata filtering") and following with current tools ("as of 2026, pgvector and Qdrant both meet these requirements"), the content remains useful even as tools change.

**Example:**
```markdown
## Retrieval Strategy

The retrieval layer must support three capabilities:
1. **Semantic search** -- finding documents by meaning, not just keywords
2. **Metadata filtering** -- restricting results by generation, document type, or version
3. **Hybrid ranking** -- combining keyword matches with semantic similarity

As of 2026, PostgreSQL with pgvector handles all three requirements for datasets
under 50,000 chunks. For larger deployments, dedicated vector databases like Qdrant
or Weaviate offer better scaling characteristics.
```

### Pattern: Current Status Section

**What:** A dedicated section at the end of each chapter that honestly states what exists, what is in progress, and what is planned.

**Recommended format (using `:::note` admonition):**
```markdown
## Current Status

:::note[Where Things Stand -- January 2026]
- **Shipped:** The bbj-language-server (v0.5.0) is published on the VS Code Marketplace with syntax highlighting, code completion, diagnostics, and formatting.
- **In progress:** Fine-tuned model showing promising results with ~10K training data points. Copilot integration in early exploration.
- **Planned:** LLM-powered ghost text completion, generation detection in the language server, semantic context API for enriched prompts.
:::

The chapters that follow build on this foundation...
```

### Pattern: Vision-Forward Framing

**What:** Lead with the strategic vision, then ground it in what currently exists.

**When to use:** Chapters 4 and 5, where significant capabilities are planned but not yet built.

**Example flow:**
1. Open with the vision ("AI-powered IDE completion that understands all four BBj generations")
2. Present the architecture ("two completion mechanisms: deterministic via Langium, generative via LLM")
3. Ground in reality ("the bbj-language-server already ships the Langium foundation")
4. Show the path forward ("adding LLM integration requires X, Y, Z")
5. Close with Current Status

### Anti-Patterns to Avoid

- **Anti-pattern: Copying original paper verbatim.** The strategy paper is a structural outline, not content to copy. Each chapter must be rewritten with current research.
- **Anti-pattern: Hard tool recommendations without version/date context.** Always qualify tool recommendations with "as of [date]" framing.
- **Anti-pattern: Pretending unbuilt features exist.** Current Status sections must be honest. "Planned" is fine; pretending something is shipped when it is not is harmful.
- **Anti-pattern: Missing cross-references.** Every chapter should link forward and backward to related content in other chapters. The RAG chapter references the chat and IDE chapters. The IDE chapter references the fine-tuning chapter for the model.
- **Anti-pattern: Chapters without Mermaid diagrams.** Every execution chapter should have at least one architecture/flow diagram. These are critical for the leadership audience.

## Don't Hand-Roll

Problems that have existing solutions or established patterns:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Architecture diagrams | Static images, ASCII art | Mermaid code blocks | Already configured, version-controllable, auto-themes |
| Decision documentation | Ad-hoc paragraphs | `:::info[Decision: ...]` admonitions | Consistent pattern from Chapters 1-3, scannable |
| Code examples | Pseudocode | Real BBj/TypeScript with syntax highlighting | `bbj` and `typescript` Prism grammars available |
| Chapter navigation | Manual "see also" sections | Docusaurus `/docs/path` links | Built-in, verified by `onBrokenLinks: 'throw'` |
| Cross-generation comparisons | Side-by-side text | `<Tabs groupId="bbj-generation">` (requires .mdx) | Proven in Chapter 1 |
| Risk assessment format | Custom table format | Standard risk matrix (likelihood x impact) with mitigation | Industry standard, readers expect this format |

**Key insight:** The presentation stack is fully solved from Phases 1-3. All effort in this phase should go into content research and writing, not tooling.

## Common Pitfalls

### Pitfall 1: Outdated Copilot Claims

**What goes wrong:** Describing Copilot as a separate extension or stating that custom models are impossible.
**Why it happens:** The Copilot landscape changed dramatically in late 2025 -- the extension is being deprecated, BYOK was introduced, and the VS Code Language Model API opened up model access.
**How to avoid:** Chapter 4 must accurately describe the current Copilot state: (1) Copilot is merging into a single Chat extension by early 2026, (2) BYOK supports Ollama for chat but NOT for inline completions, (3) the `InlineCompletionItemProvider` extension API is the mechanism for custom ghost text providers.
**Warning signs:** Mentioning "Copilot uses Codex" (outdated), or stating you cannot bring custom models to VS Code at all.

### Pitfall 2: Treating the Original Paper as Ground Truth

**What goes wrong:** Chapter content reflects the January 2025 paper's state rather than current reality.
**Why it happens:** The paper has detailed content that is tempting to copy. But it is 12+ months old in a fast-moving field.
**How to avoid:** Every claim from the paper must be verified against current sources. Key changes: training data has grown from "schema defined, no examples" to "~10K data points with promising results"; base model candidates have shifted from CodeLlama/StarCoder2 to Qwen2.5-Coder; Copilot has fundamentally changed.
**Warning signs:** Mentioning CodeLlama as a candidate, describing training data as "not yet curated", or quoting the paper's original resource estimates without update.

### Pitfall 3: RAG Content That Is Too Generic

**What goes wrong:** Chapter 6 reads like a generic RAG tutorial rather than a BBj-specific design document.
**Why it happens:** RAG best practices are well-documented elsewhere. The temptation is to summarize industry patterns without connecting them to BBj's unique requirements.
**How to avoid:** Every RAG concept must be immediately applied to BBj's context: generation tagging as metadata, MadCap Flare XHTML as the primary ingestion source, BBj API docs as structured content, cross-generation retrieval as a unique challenge.
**Warning signs:** Long sections about generic chunking without mentioning BBj generation metadata. Vector DB comparisons without stating a recommendation for BBj's corpus size.

### Pitfall 4: Implementation Roadmap Disconnected from Current Status

**What goes wrong:** Chapter 7's roadmap starts from zero, ignoring work already done.
**Why it happens:** The original paper's roadmap (Phase 1: Foundation, Months 1-2) was written before any implementation began. Some work has now been completed.
**How to avoid:** The roadmap must acknowledge current status: language server shipped, fine-tuned model in progress (~10K data points), Copilot integration in early exploration. Phase 1 of the roadmap should build on what exists, not restart.
**Warning signs:** "Phase 1: Curate 5,000+ training examples" when ~10K already exist. Timelines that ignore the language server's shipped state.

### Pitfall 5: Missing Cross-References Between Chapters

**What goes wrong:** Chapters feel like isolated documents rather than a cohesive strategy site.
**Why it happens:** Each chapter is written as a separate task, and inter-chapter links are easy to forget.
**How to avoid:** The cross-chapter quality pass (task 04-05) must create a complete link audit. Every chapter should reference at least 2-3 other chapters. Use Docusaurus-style `/docs/chapter-name` links.
**Warning signs:** No forward or backward links in a chapter. Readers asking "where do I learn about X?" when the answer is in another chapter.

### Pitfall 6: Chapter 5 Over-Committing on Deployment Model

**What goes wrong:** Chapter 5 describes a specific deployment architecture when the vision is still forming.
**Why it happens:** The temptation to be prescriptive (matching Chapter 3's depth) conflicts with the CONTEXT.md decision that the vision is still forming.
**How to avoid:** Frame Chapter 5 around architectural requirements and design principles. Present deployment models as options (embedded widget, standalone service, hybrid) with trade-offs. Let the Current Status section state clearly that the deployment model is not yet decided.
**Warning signs:** Specific deployment URLs, infrastructure diagrams for a production service, or hard tool recommendations for the chat backend.

## Code Examples

These are content patterns and code snippets that chapters should USE (not code to implement).

### Chapter 4: VSCode InlineCompletionItemProvider Pattern

The key API for custom ghost text in VSCode:

```typescript
// Source: VSCode Extension API
// https://code.visualstudio.com/api/language-extensions/programmatic-language-features

import * as vscode from 'vscode';

const provider: vscode.InlineCompletionItemProvider = {
    async provideInlineCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        context: vscode.InlineCompletionContext,
        token: vscode.CancellationToken
    ): Promise<vscode.InlineCompletionList> {
        // 1. Extract semantic context from Langium language server
        // 2. Detect BBj generation from AST
        // 3. Assemble prompt with generation context + scope info
        // 4. Call Ollama API for completion
        // 5. Return inline completion items

        return {
            items: [{
                insertText: completionText,
                range: new vscode.Range(position, position),
            }],
        };
    },
};

vscode.languages.registerInlineCompletionItemProvider(
    { language: 'bbj' },
    provider
);
```

### Chapter 4: LSP 3.18 Inline Completion (Language Server Side)

```typescript
// Source: LSP 3.18 specification
// https://microsoft.github.io/language-server-protocol/specifications/lsp/3.18/specification/

// Server capability registration
{
    capabilities: {
        inlineCompletionProvider: {
            // Enable textDocument/inlineCompletion
        }
    }
}

// Handler for textDocument/inlineCompletion
connection.onRequest('textDocument/inlineCompletion', async (params) => {
    const { textDocument, position, context } = params;
    // context.triggerKind: Invoked (1) or Automatic (2)
    // Generate completion using Langium AST + Ollama
    return {
        items: [{
            insertText: generatedCode,
            range: { start: position, end: position }
        }]
    };
});
```

### Chapter 4: Copilot BYOK with Ollama (Chat Only)

```json
// Source: VS Code docs
// https://code.visualstudio.com/docs/copilot/customization/language-models
// NOTE: BYOK supports Ollama for CHAT only, NOT for inline completions

// VS Code settings for Copilot + Ollama:
// 1. Open Command Palette > "Chat: Manage Language Models"
// 2. Select "Add Models" > Choose "Ollama"
// 3. Enter endpoint: http://localhost:11434
// 4. Select model (e.g., bbj-coder)
//
// Limitation: This gives Copilot Chat access to the model,
// but inline code completions still use GitHub's cloud models.
// For custom inline completions, use InlineCompletionItemProvider.
```

### Chapter 6: MadCap Flare to RAG Ingestion Pipeline (Conceptual)

```typescript
// Conceptual: MadCap Flare XHTML ingestion pipeline
// Source: MadCap Flare docs + RAG best practices

interface FlareDocument {
    filePath: string;          // e.g., Content/Topics/BBjAPI/addWindow.htm
    title: string;             // Extracted from <head><title>
    body: string;              // Extracted from <body>, HTML stripped
    headings: string[];        // Section hierarchy for contextual headers
    generation: string[];      // Inferred from content + path
    docType: 'api-reference' | 'concept' | 'example' | 'migration';
}

// Pipeline steps:
// 1. Export Clean XHTML from Flare (removes MadCap-specific tags)
// 2. Parse XHTML files, extract text + metadata
// 3. Apply generation tagging based on content signals
// 4. Chunk with contextual headers (preserve section context)
// 5. Embed chunks using selected embedding model
// 6. Store in vector database with generation metadata
```

### Chapter 6: Generation-Aware Retrieval Pattern

```typescript
// Source: Original strategy paper (enhanced with 2025 best practices)

async function retrieveDocumentation(
    query: string,
    generationHint?: string
): Promise<DocChunk[]> {
    // Hybrid search: combine semantic + keyword matching
    const semanticResults = await vectorStore.search(
        embed(query),
        { topK: 20, filter: buildGenerationFilter(generationHint) }
    );
    const keywordResults = await fullTextSearch(query, { topK: 20 });

    // Reciprocal Rank Fusion to merge results
    const fused = reciprocalRankFusion(semanticResults, keywordResults, {
        semanticWeight: 0.7,
        keywordWeight: 0.3
    });

    // Cross-encoder reranking for precision
    const reranked = await rerank(fused, query, { topK: 5 });

    return reranked;
}
```

### Mermaid Diagram Templates for Each Chapter

#### Chapter 4: IDE Extension Architecture

```
graph TD
    subgraph "VSCode Extension"
        LC["Language Client<br/>(LSP Protocol)"]
        ICP["Inline Completion<br/>Provider<br/>(Ghost Text)"]
    end

    subgraph "Language Server (Langium)"
        PARSER["BBj Parser / AST"]
        SCOPE["Scope Resolution"]
        GENDET["Generation Detection"]
        SEMCTX["Semantic Context API"]
    end

    subgraph "AI Backend"
        OLLAMA["Ollama Server<br/>(bbj-coder model)"]
    end

    LC <--> PARSER
    LC <--> SCOPE
    ICP --> GENDET
    ICP --> SEMCTX
    ICP --> OLLAMA
    GENDET --> PARSER
    SEMCTX --> SCOPE
```

#### Chapter 5: Documentation Chat Architecture

```
sequenceDiagram
    participant U as User
    participant CW as Chat Widget
    participant BE as Chat Backend
    participant RAG as RAG Database
    participant LLM as Ollama (bbj-coder)

    U->>CW: "How do I create a window in BBj?"
    CW->>BE: Query + session context
    BE->>BE: Detect generation hints
    BE->>RAG: Semantic search + generation filter
    RAG-->>BE: Relevant doc chunks + metadata
    BE->>BE: Assemble enriched prompt
    BE->>LLM: Prompt + retrieved context
    LLM-->>BE: Stream response
    BE-->>CW: Response + citations
    CW-->>U: Generation-aware answer
```

#### Chapter 6: RAG Pipeline Architecture

```
graph LR
    subgraph "Source Corpus"
        FLARE["MadCap Flare<br/>XHTML Topics"]
        CODE["BBj Source Code"]
        API["API References"]
        KB["Knowledge Base"]
    end

    subgraph "Ingestion Pipeline"
        PARSE["Parse + Extract"]
        TAG["Generation Tagging"]
        CHUNK["Semantic Chunking<br/>(contextual headers)"]
        EMBED["Embedding"]
    end

    subgraph "Vector Store"
        PG["PostgreSQL + pgvector<br/>(or dedicated vector DB)"]
    end

    FLARE --> PARSE
    CODE --> PARSE
    API --> PARSE
    KB --> PARSE
    PARSE --> TAG
    TAG --> CHUNK
    CHUNK --> EMBED
    EMBED --> PG
```

#### Chapter 7: Implementation Phases

```
graph LR
    P1["Phase 1<br/>Foundation<br/><i>Model + RAG core</i>"]
    P2["Phase 2<br/>IDE Integration<br/><i>VSCode extension</i>"]
    P3["Phase 3<br/>Documentation Chat<br/><i>Web interface</i>"]
    P4["Phase 4<br/>Refinement<br/><i>Quality + expansion</i>"]

    P1 -->|"MVP checkpoint"| P2
    P2 -->|"MVP checkpoint"| P3
    P3 -->|"MVP checkpoint"| P4

    style P1 fill:#e8f4e8,stroke:#2d8a2d
    style P2 fill:#e8e8f4,stroke:#2d2d8a
    style P3 fill:#f4e8e8,stroke:#8a2d2d
    style P4 fill:#f4f4e8,stroke:#8a8a2d
```

## State of the Art

### Chapter 4: IDE Integration Landscape (January 2026)

| Old Approach (Paper, Jan 2025) | Current State (Jan 2026) | Impact on Chapter |
|-------------------------------|-------------------------|-------------------|
| Copilot as a closed, fixed-model system | Copilot BYOK supports Ollama for chat; extension being deprecated and merged into Chat | Chapter must explain BYOK limitations (chat only, not inline completions) and the ongoing Copilot consolidation |
| Custom InlineCompletionProvider as only path | LSP 3.18 adds `textDocument/inlineCompletion` as protocol-level feature | Chapter can present two approaches: VSCode extension API and/or LSP protocol-level support |
| Langium for deterministic completion only | Langium AI toolbox (2025) provides evaluation, splitting, and constraint tools for LLM integration | Chapter should mention Langium AI as a bridge between Langium parsers and LLM completion |
| bbj-language-server as planned | bbj-language-server v0.5.0 shipped, 450+ commits, 13 contributors | Chapter must reflect the shipped reality, not a future plan |
| No mention of Continue.dev or alternatives | Continue.dev provides open-source Copilot alternative with Ollama tab autocomplete | Chapter should mention as an architecture reference for local-model IDE completion |

**Key factual updates for Chapter 4:**
- The bbj-language-server is a real, published product (v0.5.0, January 2026, MIT licensed)
- It is built on Langium (currently v4.1.x) with TypeScript, includes Java interop
- Features include: syntax highlighting, code completion, diagnostics, formatting, BBj Properties config viewing, direct code execution
- The extension is published on the VS Code Marketplace
- Langium v4.1.0 (October 2025) is current; the framework has graduated to a mature Eclipse Foundation project
- Langium AI (langium-ai-tools v0.0.2, targeting Langium 3.4.x) provides evaluation, splitting, and constraint generation for LLM integration with DSLs

### Chapter 5: Documentation Chat Landscape (January 2026)

| Old Approach (Paper, Jan 2025) | Current State (Jan 2026) | Impact on Chapter |
|-------------------------------|-------------------------|-------------------|
| Generic services (Algolia Ask AI, kapa.ai) fail for BBj | Still true; additionally, kapa.ai has matured significantly (Docker, OpenAI, Nokia use it) but remains cloud-hosted and uses generic LLMs | Strengthens the case for custom model; reference kapa.ai as what works for mainstream tech but not for BBj |
| Custom chat backend required | Open WebUI (self-hosted, open-source) provides a mature RAG chat interface with citations | Chapter can reference Open WebUI as an architectural pattern rather than building from scratch |
| WebSocket/REST for chat widget | Streaming responses via SSE (Server-Sent Events) is now the standard pattern for LLM chat | Update architecture to show SSE streaming |
| Fixed response format | Conversational memory across sessions is now standard | Chapter should mention session context and conversation history |

### Chapter 6: RAG Database Landscape (January 2026)

| Old Approach (Paper, Jan 2025) | Current State (Jan 2026) | Impact on Chapter |
|-------------------------------|-------------------------|-------------------|
| Basic vector search (embed + nearest neighbor) | Hybrid search (BM25 + dense embeddings) with reranking is the standard | Chapter must present hybrid search as the recommended approach |
| "PostgreSQL + pgvector or dedicated vector DB" | pgvector has matured (HNSW support, 471 QPS at 99% recall on 50M vectors); for BBj's corpus size, pgvector is the pragmatic choice | Recommend pgvector as the default, with Qdrant/Weaviate as alternatives for scaling |
| Simple chunking by document boundaries | Semantic chunking with contextual headers, domain-aware chunk sizing | Chapter must cover modern chunking strategies applied to BBj docs |
| Generic embedding models | Fine-tuned embedding models for specialized domains achieve 7%+ improvement with as few as 6.3K samples | Chapter should discuss embedding fine-tuning for BBj-specific terminology |
| No mention of MadCap Flare specifics | Flare stores content as W3C XHTML topics; Clean XHTML export strips MadCap-specific tags | Chapter must describe the specific Flare-to-RAG ingestion pipeline |

### Chapter 7: Implementation Roadmap Updates

| Old Approach (Paper, Jan 2025) | Current State (Jan 2026) | Impact on Chapter |
|-------------------------------|-------------------------|-------------------|
| Starting from zero (no training data, no model, no extension) | Language server shipped; ~10K training data points; fine-tuning showing promising results; Copilot integration in early exploration | Roadmap must acknowledge existing work and build from current state |
| 6-month timeline for entire project | Some phases already partially complete | Timeline should reflect remaining work, not total project duration |
| Generic success metrics | Industry-standard RAG metrics (Precision@K target 0.85+, Answer Rate target 0.90+) and AI governance frameworks (NIST AI RMF) available | Chapter can cite specific, credible metric targets and risk frameworks |
| Personnel estimates included | CONTEXT.md decision: hardware/infrastructure costs only, no staffing | Remove staffing estimates; focus on infrastructure costs |

**Deprecated/outdated from the original paper:**
- CodeLlama and StarCoder2 as base model candidates (replaced by Qwen2.5-Coder)
- "Training data: schema defined, no curated examples" (now ~10K data points with promising results)
- Copilot as a completely closed system (now has BYOK, but still limited for inline completions)
- Personnel cost estimates of $150K-250K (CONTEXT.md excludes staffing estimates)

## Chapter-Specific Research Findings

### Chapter 4: IDE Integration -- Detailed Findings

#### bbj-language-server Repository (HIGH confidence)

- **Repository:** https://github.com/BBx-Kitchen/bbj-language-server
- **Version:** v0.5.0 (released January 22, 2026)
- **Technology:** TypeScript (87.9%), Langium, Java interop
- **Structure:** Two main components -- `bbj-vscode` (VS Code extension + language server) and `java-interop` (Java classpath information via JSON-RPC)
- **Features:** Syntax highlighting, code completion, diagnostics, formatting, BBj Properties/config.bbx viewing, direct code execution, Enterprise Manager integration
- **Build:** Node.js + JDK required; esbuild for bundling; Vitest for testing
- **License:** MIT
- **Contributors:** 13
- **Marketplace status:** Published on VS Code Marketplace

#### Langium Framework (HIGH confidence)

- **Current version:** 4.1.3 (npm), v4.1.0 release (October 2025)
- **Major version timeline:** v3.0 (Feb 2024), v3.3 (Nov 2024, graduated to mature Eclipse project), v3.4 (Feb 2025), v4.0 (July 2025), v4.1 (Oct 2025)
- **Key features for IDE chapter:** Parser/AST generation from grammar, scope resolution, type inference, LSP integration, dependency injection for service customization
- **Custom completion:** Extend `DefaultCompletionProvider`, override `completionFor(context, next, acceptor)`. Full access to LSP API for registering additional handlers.
- **Langium AI (2025):** TypeFox released `langium-ai-tools` -- evaluation pipeline, DSL-aware splitting for RAG, constraint generation for LLM output validation. Targets Langium 3.4.x compatibility.

#### VSCode Inline Completion API (HIGH confidence)

- **API:** `vscode.languages.registerInlineCompletionItemProvider(selector, provider)`
- **Provider interface:** `provideInlineCompletionItems(document, position, context, token)` returns `InlineCompletionList`
- **Lifecycle hooks:** `handleDidShowCompletionItem`, `handleDidPartiallyAcceptCompletionItem`
- **Ghost text rendering:** Items specify `insertText` (string or SnippetString) and optional `range`
- **Trigger context:** `InlineCompletionContext` includes `triggerKind` (Invoked or Automatic) and optional `selectedCompletionInfo`

#### LSP 3.18 textDocument/inlineCompletion (HIGH confidence)

- **Spec status:** LSP 3.18 is under development; `textDocument/inlineCompletion` added as `@since 3.18.0`
- **Request:** `InlineCompletionParams` extends `TextDocumentPositionParams`
- **Context:** Includes `triggerKind` (Invoked=1, Automatic=2) and optional `selectedCompletionInfo`
- **Editor adoption:** Neovim (merged), Helix (PR), Zed (issue open)
- **Significance for Chapter 4:** This means LLM-powered inline completion can potentially be served from the language server itself (not just the extension client), which is architecturally cleaner for the Langium integration

#### Copilot BYOK + Ollama (HIGH confidence)

- **Introduced:** VS Code v1.99.0 (March 2025)
- **Ollama as built-in provider:** Yes, officially supported
- **Chat integration:** Works -- select Ollama model in Copilot Chat model picker
- **Inline completion integration:** DOES NOT WORK via BYOK. BYOK does not support inline completions.
- **Business/Enterprise availability:** Not yet available for Copilot Business or Enterprise plans
- **Agent Mode:** Ollama models only work in Ask Mode, not Agent Mode
- **Copilot extension deprecation:** The separate Copilot extension is being deprecated by early 2026; functionality merged into Copilot Chat extension. Code open-sourced on GitHub.

#### Continue.dev Architecture Reference (MEDIUM confidence)

- **Tab autocomplete with Ollama:** Uses `InlineCompletionItemProvider` API internally
- **Recommended autocomplete model:** Qwen 2.5 Coder 1.5B (small, fast, FIM-trained)
- **Architecture:** Uses LSP for definitions + similarity search over recent files to build context
- **Key insight:** Autocomplete models don't need to be large -- most SOTA autocomplete models are under 10B parameters. FIM (fill-in-the-middle) training format is critical.

### Chapter 5: Documentation Chat -- Detailed Findings

#### Why Generic Services Fail (MEDIUM confidence)

The original paper's claim holds true in 2026. Generic doc chat services (kapa.ai, Algolia Ask AI) use general-purpose LLMs that:
1. Have no BBj training data
2. Cannot understand BBj syntax in documentation snippets
3. Will hallucinate VB/VBA-style code when asked BBj questions
4. Cannot distinguish between BBj generations in responses

kapa.ai has grown significantly (200+ customers including Docker, OpenAI, Nokia) but remains a hosted service using generic LLMs. It is excellent proof of the concept for mainstream technologies but confirms the gap for BBj.

#### Self-Hosted Chat Architecture Options (MEDIUM confidence)

| Option | Description | Trade-offs |
|--------|-------------|------------|
| **Embedded widget in docs** | Chat component in the Docusaurus site itself | Simplest UX; requires Docusaurus plugin or iframe; limited by static site constraints |
| **Standalone service** | Separate web app (e.g., Open WebUI) behind docs link | Most flexible; separate deployment; users leave docs context |
| **Hybrid** | Lightweight chat widget in docs that connects to standalone backend | Best UX; moderate complexity; backend can be shared with IDE |

Per CONTEXT.md, this is Claude's Discretion. Recommendation: Document all three as options with trade-offs. The backend architecture (RAG + Ollama + streaming) is the same regardless of frontend deployment.

#### Streaming Response Pattern (MEDIUM confidence)

Server-Sent Events (SSE) is the standard for LLM chat streaming in 2025/2026. The pattern:
1. Client sends query via POST
2. Server processes through RAG pipeline
3. Server opens SSE stream
4. LLM response tokens stream to client in real-time
5. Citations/sources appended at end of stream

This mirrors Ollama's own streaming API behavior and is compatible with the OpenAI-compatible endpoint.

### Chapter 6: RAG Database -- Detailed Findings

#### MadCap Flare Content Format (MEDIUM confidence)

- **Source format:** Individual XHTML topics (W3C-compliant XML with HTML elements)
- **File structure:** Each topic is a separate `.htm` file with `<html>`, `<head>`, `<body>` elements and `xmlns:MadCap` namespace
- **Content organization:** Topics stored in Content Explorer; organized hierarchically via TOC (Table of Contents) files; Targets define output format
- **Clean XHTML export:** Strips all MadCap-specific tags (`mc:*`, `data-mc-*`), removes conditions/keywords, outputs basic HTML files. This is the recommended export for pipeline ingestion.
- **Key for RAG pipeline:** Use Clean XHTML output as the primary ingestion source. Parse HTML, extract text + headings, apply generation tagging based on content analysis.
- **No programmatic API:** Flare does not expose a REST API for content extraction. Export must be done through Flare's build targets or direct file parsing.

#### Chunking Strategy for BBj Documentation (MEDIUM confidence)

Recommended approach based on 2025 best practices:

1. **Document-type-aware chunking:** Different chunk sizes for different content types:
   - API references: 200-400 tokens per chunk (focused, specific)
   - Conceptual docs: 400-600 tokens per chunk (need more context)
   - Code examples: Keep complete examples intact (variable size)
   - Migration guides: 400-600 tokens with strong contextual headers

2. **Contextual headers:** Prepend the section hierarchy to every chunk. Example: "BBjSysGui > addWindow > Parameters" prepended to the parameter description chunk.

3. **Generation metadata as chunk-level field:** Every chunk carries `generation: ["bbj-gui", "dwc"]` metadata for filtered retrieval.

4. **Overlap:** 10-15% overlap between adjacent chunks to preserve context at boundaries.

#### Vector Database Recommendation (HIGH confidence)

**Recommendation for BBj: PostgreSQL + pgvector as the default.**

Rationale:
- BBj's total corpus (MadCap Flare docs + source code + API refs + knowledge base) will likely produce under 50,000 chunks
- At this scale, pgvector and dedicated vector DBs (Qdrant, Weaviate) perform identically (within 1ms at p50)
- pgvector avoids running a separate database service
- SQL integration allows joining vector results with relational metadata (generation, version, doc type)
- If the corpus grows significantly, migrating to Qdrant or Weaviate is straightforward

Present in chapter as: "pgvector is the pragmatic default for BBj's corpus size; dedicated vector databases become relevant at scale."

#### Embedding Model Strategy (MEDIUM confidence)

- Generic embedding models (OpenAI `text-embedding-3-large`, open-source BGE, E5) will work reasonably well for BBj documentation since most content is in natural English
- BBj code snippets within documentation may benefit from a code-aware embedding model
- Fine-tuning embeddings for BBj-specific terminology is feasible with 1,000-5,000 samples and can yield 7%+ improvement
- **Recommendation for chapter:** Start with a strong general embedding model (BGE-M3 or similar open-source). Evaluate fine-tuning after the initial pipeline is running and baseline metrics are established.

#### Hybrid Search Architecture (MEDIUM confidence)

The chapter should present this as the recommended retrieval strategy:

1. **Dense vector search:** Semantic similarity via embeddings + pgvector
2. **Sparse keyword search:** BM25 (PostgreSQL full-text search) for exact terms, BBj keywords, API names
3. **Fusion:** Reciprocal Rank Fusion (RRF) combining dense and sparse results, weighted 0.7 semantic / 0.3 keyword
4. **Reranking:** Cross-encoder reranker on top-20 fused results to select top-5 for prompt
5. **Generation filtering:** Apply generation metadata filter before or during retrieval

The BBj-specific value of hybrid search: BBj API names (like `BBjSysGui.addWindow()`) are exact terms that benefit from keyword matching, while conceptual questions benefit from semantic search.

### Chapter 7: Implementation Roadmap -- Detailed Findings

#### Updated Current Status (HIGH confidence -- from CONTEXT.md)

| Component | Paper Status (Jan 2025) | Actual Status (Jan 2026) |
|-----------|------------------------|------------------------|
| Training data | "Schema defined, no curated examples" | ~10K data points, promising results |
| Base model | "Candidates identified" | Qwen2.5-Coder selected, fine-tuning in progress |
| Language server | "Architecture planned" | v0.5.0 shipped, on VS Code Marketplace |
| Copilot integration | Not mentioned | In early exploration, "cautiously optimistic" |
| RAG database | "Schema designed" | Source corpus identified, pipeline not built |
| Documentation chat | "Architecture planned" | Vision defined, not yet built |

#### Roadmap Structure (MEDIUM confidence)

Per CONTEXT.md decisions:
- **Primary audience:** Technical leads and project managers
- **Single recommended plan** with explicit cut points (MVP checkpoints)
- **Hardware/infrastructure costs only** -- no staffing estimates
- **Formal risk assessment** section

Recommended phase structure (building on actual current state):

**Phase 1: Model Validation (Current -- Partially Complete)**
- Continue fine-tuning with expanded dataset
- Establish evaluation benchmarks (BBj-specific + general code)
- Validate model quality for IDE completion use case
- MVP checkpoint: Model generates syntactically valid BBj code 95%+ of the time

**Phase 2: IDE Integration**
- Integrate LLM completion into bbj-language-server
- Implement generation detection in Langium parser
- Build semantic context extraction API
- MVP checkpoint: Ghost text completions available in VS Code extension

**Phase 3: RAG Pipeline + Documentation Chat**
- Build MadCap Flare ingestion pipeline
- Set up pgvector with generation-tagged chunks
- Build chat backend with hybrid retrieval
- MVP checkpoint: Chat answers generation-appropriate questions with citations

**Phase 4: Refinement + Scaling**
- Expand training data based on user feedback
- Optimize retrieval quality and latency
- Production deployment hardening
- MVP checkpoint: All components production-ready

#### Risk Assessment Framework (MEDIUM confidence)

Use a standard likelihood x impact matrix format. Key risks to document:

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Fine-tuned model hallucinates BBj syntax | Medium | High | Langium validation of suggestions; evaluation benchmarks; Copilot bridge as fallback |
| Training data insufficient for all 4 generations | Medium | Medium | Prioritize modern (BBj GUI + DWC) first; expand to legacy iteratively |
| Copilot changes break bridge integration | Medium | Low | Custom LLM client as strategic path; Copilot bridge is intentionally interim |
| MadCap Flare content difficult to parse | Low | Medium | Clean XHTML export provides standardized format; pilot with subset first |
| Model too large for customer hardware | Low | Medium | Qwen2.5-Coder-7B at Q4_K_M fits in ~4GB; offer multiple quantization options |
| LLM ecosystem shifts (new models, APIs) | High | Low | Architecture-first design; model-agnostic pipeline; retrain on same data |

The NIST AI Risk Management Framework (AI RMF 1.0, with Generative AI Profile NIST-AI-600-1) provides a credible structure to reference for the risk methodology.

#### Infrastructure Cost Framework (MEDIUM confidence)

Hardware/infrastructure costs only (per CONTEXT.md):

| Component | Specification | One-Time Cost | Monthly Cost |
|-----------|--------------|---------------|--------------|
| Training GPU | RTX 4090 24GB (or cloud equivalent) | ~$1,500 (purchase) or $2-5K (cloud training runs) | $0 (owned) |
| Ollama inference server | 16GB+ RAM, GPU recommended | Varies (existing hardware) | $0 (self-hosted) |
| PostgreSQL + pgvector | Standard PostgreSQL instance | $0 (existing infra) | $50-200 (if cloud-hosted) |
| Chat backend hosting | Standard web server | $0 (existing infra) | $50-200 (if cloud-hosted) |
| Embedding computation | One-time corpus embedding | $10-50 | $5-20/month (incremental updates) |

## Open Questions

1. **Langium AI compatibility with bbj-language-server**
   - What we know: Langium AI (langium-ai-tools v0.0.2) targets Langium 3.4.x. The bbj-language-server is built on Langium but the specific version is unknown.
   - What's unclear: Whether the bbj-language-server could adopt Langium AI tools directly, or whether the version gap (3.4.x vs 4.1.x) requires updates. Also unclear whether TypeFox is tracking Langium AI to 4.x.
   - Recommendation: Mention Langium AI in Chapter 4 as a relevant initiative, but don't assume it is directly usable. Present it as "an emerging bridge between Langium-based language servers and LLM integration."

2. **Exact MadCap Flare export workflow for RAG**
   - What we know: Flare exports Clean XHTML that strips proprietary tags. The content is W3C-compliant XHTML.
   - What's unclear: The exact file organization, naming conventions, and metadata available in the BBj-specific Flare project. Whether the Flare project has structured API docs vs. narrative docs vs. both.
   - Recommendation: Chapter 6 should describe the general Flare-to-RAG pipeline architecture. The specific parsing logic will be determined during implementation. Reference Clean XHTML as the expected input format.

3. **Copilot inline completion with custom models -- future support**
   - What we know: BYOK does NOT support inline completions as of January 2026. Only chat is supported.
   - What's unclear: Whether Microsoft plans to extend BYOK to inline completions. The open-sourcing of the inline suggestions code suggests this may be possible in the future.
   - Recommendation: Chapter 4 should state the current limitation clearly and present the custom `InlineCompletionItemProvider` as the path for custom inline completions. Note that the Copilot bridge currently applies to chat interactions only.

4. **Chapter 3 update scope for the quality pass**
   - What we know: Chapter 3's Current Status section says "Training data: Schema defined. No curated examples exist yet." This is factually outdated -- ~10K data points exist with promising results.
   - What's unclear: What other sections of Chapter 3 need updating beyond the Current Status section. The model recommendation (Qwen2.5-Coder) is already correct.
   - Recommendation: The quality pass (task 04-05) should update Chapter 3's Current Status section and any other paragraphs that describe training data status as "not yet curated." Also verify that the Qwen3-Coder mention is current.

5. **Chapter 5 deployment model recommendation**
   - What we know: This is explicitly Claude's Discretion per CONTEXT.md. The vision is still forming.
   - What's unclear: What specific deployment model to recommend (embedded widget, standalone, hybrid).
   - Recommendation: Present all three options with trade-offs. Recommend the hybrid approach (lightweight widget in docs connecting to a shared backend) as the most architecturally sound, but frame it as a design recommendation, not a commitment.

## Sources

### Primary (HIGH confidence)

- **bbj-language-server GitHub** (https://github.com/BBx-Kitchen/bbj-language-server) -- Repository structure, version, features, technology stack. Fetched 2026-01-31.
- **VSCode InlineCompletionItemProvider API** (https://code.visualstudio.com/api/language-extensions/programmatic-language-features) -- Extension API for ghost text completion.
- **VSCode Inline Completion Sample** (https://github.com/microsoft/vscode-extension-samples/blob/main/inline-completions/src/extension.ts) -- Reference implementation of the provider pattern.
- **LSP 3.18 Specification** (https://microsoft.github.io/language-server-protocol/specifications/lsp/3.18/specification/) -- `textDocument/inlineCompletion` spec.
- **VSCode AI Language Models docs** (https://code.visualstudio.com/docs/copilot/customization/language-models) -- BYOK configuration, Ollama integration, limitations.
- **VSCode Open Source AI Editor Blog** (https://code.visualstudio.com/blogs/2025/11/04/openSourceAIEditorSecondMilestone) -- Copilot extension deprecation, inline suggestions open-sourcing.
- **NIST AI Risk Management Framework** (https://www.nist.gov/itl/ai-risk-management-framework) -- Risk assessment methodology.

### Secondary (MEDIUM confidence)

- **Langium AI blog** (https://www.typefox.io/blog/langium-ai-the-fusion-of-dsls-and-llms/) -- TypeFox announcement of Langium AI toolbox. Describes evaluation, splitting, constraint tools.
- **Langium releases** (https://github.com/eclipse-langium/langium/releases) -- Version history through v4.1.0.
- **MadCap Flare content format** (https://www.madcapsoftware.com/blog/topics-tocs-targets-three-essential-file-types-new-madcap-flare-users-know/) -- XHTML topics, TOC structure, Clean XHTML export.
- **MadCap Flare Clean XHTML** (https://www.madcapsoftware.com/blog/new-feature-highlight-clean-xhtml-output-madcap-flare-2017/) -- Clean XHTML output characteristics.
- **RAG best practices 2025** (https://www.morphik.ai/blog/retrieval-augmented-generation-strategies, https://www.edenai.co/post/the-2025-guide-to-retrieval-augmented-generation-rag) -- Chunking strategies, hybrid search, reranking.
- **Vector database comparison** (https://www.firecrawl.dev/blog/best-vector-databases-2025) -- pgvector vs Qdrant vs Milvus vs Weaviate for various scales.
- **pgvector vs Qdrant small dataset** (https://medium.com/@TheWake/qdrant-vs-pgvector-theyre-the-same-speed-5ac6b7361d9d) -- January 2026 benchmark showing identical performance at small scale.
- **Continue.dev autocomplete docs** (https://docs.continue.dev/customize/deep-dives/autocomplete) -- Architecture reference for local-model IDE completion.
- **kapa.ai** (https://www.kapa.ai/) -- Commercial doc chat product, validates the concept but uses generic LLMs.
- **Open WebUI** (https://github.com/open-webui/open-webui) -- Self-hosted AI chat with RAG, citations.
- **Embedding fine-tuning for specialized domains** (https://weaviate.io/blog/fine-tune-embedding-model, https://redis.io/blog/get-better-rag-by-fine-tuning-embedding-models/) -- Domain-specific embedding improvement patterns.

### Tertiary (LOW confidence)

- **AI implementation roadmap frameworks** (https://www.spaceo.ai/blog/ai-implementation-roadmap/) -- General phased AI implementation patterns. Multiple blog sources agreeing on structure.
- **kapa.ai alternatives** (https://slashdot.org/software/p/kapa.ai/alternatives) -- Market landscape for doc chat tools.
- **Enterprise AI governance** (https://www.liminal.ai/blog/enterprise-ai-governance-guide) -- Governance patterns, may inform Chapter 7 risk section.
- **AWS RAG documentation best practices** (https://docs.aws.amazon.com/prescriptive-guidance/latest/writing-best-practices-rag/best-practices.html) -- Writing documentation optimized for RAG ingestion.

## Metadata

**Confidence breakdown:**
- Docusaurus content patterns: HIGH -- Proven in Chapters 1-3, all tooling configured and working
- Chapter 4 subject matter (IDE/Langium/Copilot): HIGH for current API facts, MEDIUM for architectural recommendations
- Chapter 5 subject matter (Doc Chat): MEDIUM -- Architecture patterns well-understood, but specific BBj deployment model TBD
- Chapter 6 subject matter (RAG): MEDIUM -- Industry practices well-documented; BBj-specific application requires some extrapolation
- Chapter 7 subject matter (Roadmap): MEDIUM -- Current status from CONTEXT.md is reliable; cost/timeline estimates are approximations
- Cross-chapter quality pass: HIGH -- Clear checklist of updates needed, patterns established

**Research date:** 2026-01-31
**Valid until:** ~2026-03-01 (Content patterns: stable; AI/ML landscape: recheck in 30 days; Copilot changes: monitor VS Code release notes)
