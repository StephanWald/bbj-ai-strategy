# BBj AI Support Strategy

## Intelligent Code Assistance Across Four Generations of Business BASIC

**Version:** 1.0  
**Date:** January 2025  
**Author:** BASIS International Development Team

---

## Executive Summary

This paper outlines a comprehensive AI support strategy for BBj, addressing the unique challenges of providing intelligent code assistance for a language that spans four distinct generations of development paradigms - from character-based terminal interfaces through Visual PRO/5, Swing-based GUI, to modern browser-based DWC applications.

Unlike mainstream languages where generic large language models (LLMs) can provide reasonable assistance with minimal customization, BBj requires a fundamentally different approach. Base LLMs have essentially no knowledge of BBj syntax, idioms, or APIs. This necessitates fine-tuning a dedicated model and building generation-aware infrastructure that can understand legacy code while guiding developers toward modern patterns.

The strategy encompasses three interconnected initiatives:

1. **Fine-tuned BBj Language Model** - A custom-trained model that understands all BBj generations
2. **VSCode Extension with Langium Integration** - IDE-based code completion with semantic context awareness
3. **Documentation Chat System** - Website-based conversational AI for BBj documentation

All three initiatives share a common RAG (Retrieval-Augmented Generation) database and the same fine-tuned model, ensuring consistency and maximizing the return on investment in AI infrastructure.

---

## The BBj Challenge: Four Generations, One Language

### Why BBj Is Different

When a developer asks a generic AI assistant "How do I create a window?", the response depends entirely on understanding what "window" means in context. In BBj, this single question has four fundamentally different answers - plus a foundation of universal syntax that works across all generations:

| Generation | Era | Runtime | Answer |
|------------|-----|---------|--------|
| Character UI | 1980s-present | Terminal | `PRINT @(10,5), "Hello"` with mnemonics |
| Visual PRO/5 | 1990s-2000s | Windows GUI | `WINDOW CREATE wnd_id, @(0,0), 80, 24, "Title"` |
| BBj GUI | 2000s-present | Java Swing | `window! = sysgui!.addWindow(100,100,800,600,"Title")` |
| DWC | 2010s-present | Browser | Same API as BBj GUI, renders in browser |

All four approaches remain valid BBj code. All four exist in production systems. A developer maintaining a 30-year-old banking application may need to understand character mnemonics, while a developer building a new web application needs modern DWC patterns - and a developer modernizing legacy code needs to understand both.

### Universal vs Generation-Specific Patterns

Beyond the four UI generations, BBj has a substantial core of universal syntax that works identically across all generations:

| Scope | Label | Examples |
|-------|-------|----------|
| Universal | `"all"` | `FOR/NEXT`, `IF/THEN`, `GOSUB`, string functions, file I/O, `SETERR` |
| Modern BBj | `["bbj-gui", "dwc"]` | `class`, `method`, `use`, object syntax with `!` |
| Any GUI | `["vpro5", "bbj-gui", "dwc"]` | Window and control concepts (syntax varies) |
| DWC only | `["dwc"]` | `BBjWebManager`, `executeAsyncScript`, browser APIs |
| Legacy GUI | `["vpro5"]` | `WINDOW CREATE`, `BUTTON CREATE`, `CTRL()` |
| Character only | `["character"]` | `@(x,y)` positioning without GUI context |

This distinction matters for training data - universal patterns should be labeled `"all"` so the model learns they apply everywhere, while generation-specific patterns need appropriate scoping.

### The Generic LLM Problem

Modern LLMs like GPT-4 and Claude are trained primarily on mainstream languages. Their knowledge of BBj is essentially nonexistent:

**What happens when you ask a generic LLM about BBj:**

```
User: "How do I create a button in BBj?"

Generic LLM (hallucinating VB-style code):
    Dim button As New BBjButton
    button.Caption = "Click Me"
    button.OnClick = Sub() MsgBox("Hello") End Sub

Correct BBj:
    button! = window!.addButton(101, 10, 10, 100, 25, "Click Me")
    button!.setCallback(button!.ON_BUTTON_PUSH, "handleClick")
```

The generic LLM doesn't understand:
- Object references ending with `!` (e.g., `window!`, `button!`)
- String variables ending with `$` (e.g., `name$`, `value$`)
- Field references starting with `#` (e.g., `#myField!`)
- The callback/label pattern for event handling
- The `err=*next` error handling idiom
- Any of the actual BBj API methods

### Contrast with webforJ

webforJ, our Java-based web framework, takes a fundamentally different approach to AI support:

| Aspect | webforJ | BBj |
|--------|---------|-----|
| Base language | Java (billions of training examples) | BBj (near-zero training examples) |
| LLM comprehension | Excellent - understands syntax natively | None - will hallucinate |
| What AI needs | Framework-specific context via RAG | Fundamental language understanding |
| Fine-tuning required | No | Yes - absolutely essential |
| Generic tools (Copilot, Algolia Ask AI) | Work reasonably well | Actively harmful - teach wrong patterns |

For webforJ, we provide an MCP (Model Context Protocol) server that gives AI assistants access to framework documentation. The base LLM already understands Java; we just supplement with webforJ-specific knowledge.

For BBj, we must teach the LLM the language itself before framework knowledge becomes useful.

### Why GitHub Copilot Won't Work for BBj

A natural question arises: "Can we use GitHub Copilot with our fine-tuned model?" The short answer is **no** - Copilot is a closed system that does not allow custom models.

**Copilot Architecture Constraints:**

| Aspect | Copilot | What BBj Needs |
|--------|---------|----------------|
| Model | OpenAI Codex/GPT (fixed) | Fine-tuned BBj model |
| Customization | None for base completions | Full control over model |
| Training | Microsoft/GitHub controlled | Our BBj-specific training |
| Hosting | GitHub cloud only | Self-hosted option for customer privacy |

**What Copilot offers that doesn't help:**
- *Copilot Extensions* - Allow chat plugins, but base code completion still uses their model
- *Copilot for Business* - Adds policy controls, not model customization
- *Language Model API* - VS Code extensions can request Copilot completions, but still their model

**The fundamental problem:** Copilot's model has no meaningful BBj training data. Even with perfect RAG context, the model will:
- Suggest syntactically invalid code (`Dim` instead of `declare`)
- Hallucinate method names that don't exist
- Confuse BBj with VB, VBA, or other BASIC variants
- Misunderstand object references (`!`), string markers (`$`), and field references (`#`)

### Alternative AI Coding Assistants

Several tools do support custom/self-hosted models:

| Tool | Custom Model Support | BBj Viability |
|------|---------------------|---------------|
| **GitHub Copilot** | No | Not viable |
| **Continue.dev** | Yes - Ollama, any OpenAI-compatible | Good candidate |
| **Tabby** | Yes - fully self-hosted | Good candidate |
| **Cody (Sourcegraph)** | Limited model selection | Partial |
| **CodeGPT** | Yes - custom endpoints | Good candidate |
| **Our VSCode Extension** | Yes - full control | Best option |

**Our recommendation:** Build our own VSCode extension with Langium integration. This provides:
- Complete control over the model (our fine-tuned BBj model via Ollama)
- Semantic context from Langium that no external tool can access
- Generation-aware completions
- No dependency on third-party model availability
- Self-hosting option for customers with data privacy requirements

The investment in a custom extension is justified because no existing tool can provide meaningful BBj assistance - we're not competing with Copilot, we're filling a gap Copilot cannot fill.

---

## Strategic Architecture

### Unified AI Infrastructure

Rather than building separate AI systems for different use cases, we propose a unified infrastructure where the same fine-tuned model and knowledge base serve multiple interfaces:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BBj AI Infrastructure                                │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    Fine-Tuned BBj Language Model                        │ │
│  │                                                                         │ │
│  │  Understands:                                                           │ │
│  │  • All four generations of BBj syntax                                   │ │
│  │  • Object references (!, $, #)                                          │ │
│  │  • Event handling patterns                                              │ │
│  │  • Error handling idioms                                                │ │
│  │  • API method signatures                                                │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│  ┌───────────────────────────────────┼─────────────────────────────────────┐ │
│  │                    Shared RAG Database                                  │ │
│  │                                                                         │ │
│  │  • API documentation (all generations)                                  │ │
│  │  • Code examples                                                        │ │
│  │  • Best practices                                                       │ │
│  │  • Migration guides                                                     │ │
│  │  • Version-specific information                                         │ │
│  │                                                                         │ │
│  │  Metadata: generation, version, deprecation status, superseded_by      │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │ │
│            ┌─────────────────────────┼─────────────────────────┐            │
│            │                         │                         │            │
│            ▼                         ▼                         ▼            │
│  ┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  │
│  │  VSCode Extension │  │  Documentation Chat  │  │  Future: CLI Tools   │  │
│  │                   │  │                      │  │                      │  │
│  │  • Ghost text     │  │  • Website widget    │  │  • Terminal helper   │  │
│  │  • Popup completion│ │  • Q&A interface     │  │  • Script assistant  │  │
│  │  • Langium context│  │  • Conversation      │  │                      │  │
│  └──────────────────┘  └──────────────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Benefits of Unified Infrastructure

1. **Single training investment** - Fine-tuning effort benefits all interfaces
2. **Consistent answers** - Same model ensures consistent guidance across IDE and documentation
3. **Shared knowledge updates** - Documentation improvements benefit all interfaces
4. **Reduced maintenance** - One system to maintain rather than three
5. **Cross-pollination** - User questions from chat inform training data improvements

---

## Component 1: Fine-Tuned BBj Language Model

### Training Objectives

The model must develop two distinct capabilities:

**Comprehension (All Generations)**

The model must understand code from any BBj generation to:
- Read and explain legacy code
- Support migration projects
- Debug mixed-generation applications
- Answer "what does this code do?" regardless of era

**Generation (Context-Appropriate)**

When producing code, the model must:
- Match the generation of surrounding code
- Default to modern DWC patterns for new projects
- Warn when suggesting deprecated approaches
- Offer migration paths when appropriate

### Training Data Structure

Training data should be labeled with generation scope to indicate applicability:

**Universal pattern (applies to all generations):**

```json
{
    "type": "completion",
    "generation": "all",
    "instruction": "Complete the FOR loop",
    "input": "total = 0\nFOR i = 1 TO 10\n    total = total + i\n",
    "output": "NEXT i\nPRINT \"Sum: \", total"
}
```

**Generation-specific pattern:**

```json
{
    "type": "comprehension",
    "generation": "vpro5",
    "instruction": "Explain this BBj code",
    "input": "WINDOW CREATE wnd_id, @(0,0), 80, 24, \"Main\"",
    "output": "This is Visual PRO/5 style GUI code. It creates a window with ID stored in wnd_id, positioned at row 0, column 0, with dimensions 80x24 characters, titled 'Main'. The WINDOW CREATE verb was used in Visual PRO/5 before the object-oriented BBjAPI was introduced. For new development, consider using sysgui!.addWindow() instead."
}
```

**Modern-only pattern (multiple generations):**

```json
{
    "type": "completion",
    "generation": ["bbj-gui", "dwc"],
    "instruction": "Complete the code to add a button to the window",
    "context": "window! = sysgui!.addWindow(100, 100, 400, 300, \"Test\")\n",
    "output": "button! = window!.addButton(101, 10, 10, 100, 25, \"Click Me\")\nbutton!.setCallback(button!.ON_BUTTON_PUSH, \"handleClick\")"
}
```

**Generation Label Schema:**

```typescript
// Generation can be:
// - "all" for universal patterns (FOR/NEXT, string functions, file I/O)
// - Single string for generation-specific ("vpro5", "dwc")
// - Array for subset of generations (["bbj-gui", "dwc"])

type GenerationLabel = "all" | Generation | Generation[];
type Generation = "character" | "vpro5" | "bbj-gui" | "dwc";
```

### Generation Detection Signals

The model should recognize generation from code patterns:

| Signal | Indicates |
|--------|-----------|
| `PRINT @(x,y),` without GUI code | Character UI |
| `WINDOW CREATE`, `WINDOW SET`, `CTRL()` | Visual PRO/5 |
| `BBjAPI().getSysGui()`, `BBjTopLevelWindow` | BBj GUI or DWC |
| `BBjAPI().getWebManager()`, `executeAsyncScript` | DWC specifically |
| `use ::path::ClassName` | Modern BBj (any GUI) |
| `class public`, `method public` | Modern BBj OOP |

### Model Selection and Hosting

**Base Model Candidates:**
- CodeLlama 7B/13B - Well-understood, good code performance
- DeepSeek Coder 6.7B/33B - Strong on niche languages
- StarCoder2 - Open weights, code-focused

**Hosting:**
- Ollama for local deployment
- Enables customer self-hosting for data privacy
- No per-query API costs after initial setup

**Fine-Tuning Approach:**
- LoRA/QLoRA for efficient training
- Target: 10,000-50,000 training examples
- Include examples from all four generations
- Weight toward modern patterns while maintaining comprehension of legacy

---

## Component 2: VSCode Extension with Langium Integration

### Overview

The BBj VSCode extension combines traditional language server capabilities (via Langium) with AI-powered code completion. This creates a hybrid system where:

- **Langium** provides deterministic, correct completions for symbols, types, and keywords
- **Fine-tuned LLM** provides generative completions for multi-line code, pattern completion, and context-aware suggestions

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VSCode Extension                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      Extension Client (TypeScript)                      │ │
│  │                                                                         │ │
│  │  ┌─────────────────────┐         ┌───────────────────────────────────┐ │ │
│  │  │  Language Client    │         │  Inline Completion Provider       │ │ │
│  │  │  (LSP Protocol)     │         │  (Ghost Text)                     │ │ │
│  │  │                     │         │                                   │ │ │
│  │  │  Popup completions  │         │  • Generation detection           │ │ │
│  │  │  Hover info         │         │  • Semantic context extraction    │ │ │
│  │  │  Go to definition   │         │  • Prompt assembly                │ │ │
│  │  │  Diagnostics        │         │  • LLM invocation                 │ │ │
│  │  └─────────┬───────────┘         └──────────────┬────────────────────┘ │ │
│  └────────────┼────────────────────────────────────┼────────────────────────┘ │
│               │                                    │                         │
│               │ LSP                                │ Custom Request          │
│               │                                    │ + HTTP                  │
│               ▼                                    ▼                         │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────────┐ │
│  │  BBj Language Server        │    │  Ollama Server                      │ │
│  │  (Langium)                  │    │                                     │ │
│  │                             │    │  ┌───────────────────────────────┐  │ │
│  │  • Parser / AST             │    │  │  bbj-finetuned model          │  │ │
│  │  • Scope resolution         │◄───┤  │                               │  │ │
│  │  • Type inference           │    │  │  Understands all generations  │  │ │
│  │  • Generation detection     │    │  │  Generates appropriate code   │  │ │
│  │  • Semantic context API     │    │  └───────────────────────────────┘  │ │
│  └─────────────────────────────┘    └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Two Completion Mechanisms

**Popup Completion (Langium - Deterministic)**

Triggered by typing `.` or pressing Ctrl+Space. Provides exhaustive, correct list of available symbols.

| Characteristic | Value |
|----------------|-------|
| Source | Langium scope resolution |
| Latency | <10ms |
| Correctness | 100% - only valid symbols |
| Use case | Symbol selection, method names |

**Ghost Text (LLM - Generative)**

Appears as dimmed text after a pause in typing. Provides multi-line, context-aware suggestions.

| Characteristic | Value |
|----------------|-------|
| Source | Fine-tuned model via Ollama |
| Latency | 200-1000ms |
| Correctness | High but not guaranteed |
| Use case | Statement completion, patterns, boilerplate |

### Generation-Aware Completion

The Langium parser detects the code generation and includes this in the prompt:

```typescript
interface GenerationContext {
    detected: 'character' | 'vpro5' | 'bbj-gui' | 'dwc' | 'mixed' | 'unknown';
    confidence: number;
    signals: string[];
}

function detectGeneration(ast: BbjProgram): GenerationContext {
    const signals: string[] = [];
    
    // DWC-specific signals
    if (hasCall(ast, 'BBjAPI().getWebManager')) {
        signals.push('dwc:getWebManager');
    }
    
    // BBj GUI signals (also valid in DWC)
    if (hasCall(ast, 'BBjAPI().getSysGui')) {
        signals.push('bbj:getSysGui');
    }
    
    // Visual PRO/5 signals
    if (hasStatement(ast, 'WINDOW CREATE')) {
        signals.push('vpro5:window-verb');
    }
    
    // Character UI signals
    if (hasMnemonic(ast, '@(') && !hasAnyGuiCode(ast)) {
        signals.push('character:mnemonics-only');
    }
    
    return inferGeneration(signals);
}
```

### Semantic Context for Prompts

Langium provides rich context that dramatically improves LLM suggestions:

```typescript
interface SemanticContext {
    // Structural context
    containingClass: string | null;
    containingMethod: string | null;
    
    // Generation context
    generation: GenerationContext;
    
    // Scope information
    visibleSymbols: Array<{
        name: string;
        type: string;
        kind: 'field' | 'local' | 'parameter' | 'method';
    }>;
    
    // Expression context (if completing after dot)
    receiver: {
        expression: string;
        resolvedType: string;
        availableMembers: MemberInfo[];
    } | null;
    
    // Recent code for flow understanding
    precedingStatements: string[];
}
```

### Example: Enriched Prompt

For cursor at `#custGrid!.█` after fetching a recordset:

```
You are a BBj code completion assistant.

<generation>
Detected: BBj DWC (Browser-based)
Confidence: High
Signals: BBjAPI().getSysGui(), BBjTopLevelWindow, setCallback()
</generation>

<rules>
- Generate code matching the BBj DWC generation
- Use object-oriented patterns (window!, button!, etc.)
- Do NOT suggest Visual PRO/5 verbs (WINDOW CREATE)
- Do NOT suggest character mnemonics (@(x,y)) for GUI code
</rules>

<receiver>
Expression `#custGrid!` has type `CustomerGrid` with members:
- method: setData(BBjRecordSet rs!) returns void
- method: refresh() returns void
- method: clearSelection() returns void
- method: getSelectedRow() returns BBjNumber
</receiver>

<scope>
orderId: BBjNumber (parameter)
rs!: BBjRecordSet (local)
#window!: BBjTopLevelWindow (field)
#custGrid!: CustomerGrid (field)
</scope>

<code>
    method public void loadOrder(BBjNumber orderId)
        #currentOrderId = orderId
        declare BBjRecordSet rs!
        rs! = #getOrderRecordSet(orderId)
        #custGrid!.█
    methodend
</code>

Generate only the completion. No explanation.
```

Expected output: `setData(rs!)`

---

## Component 3: Documentation Chat System

### Purpose

A conversational AI interface embedded in the BBj documentation website, allowing developers to ask natural language questions and receive accurate, generation-appropriate answers.

### Why Not Use Generic Services?

Services like Algolia Ask AI or kapa.ai work well for mainstream technologies but fail for BBj:

| Service | How It Works | Why It Fails for BBj |
|---------|--------------|----------------------|
| Algolia Ask AI | Generic LLM + crawled docs | LLM doesn't understand BBj syntax in docs |
| kapa.ai | Generic LLM + RAG | Same problem - base model is BBj-illiterate |
| GitHub Copilot | Generic code model | Suggests wrong syntax, hallucinated methods |

These services work for webforJ because the underlying LLM understands Java. For BBj, we need our fine-tuned model.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Documentation Website Chat                               │
│                                                                              │
│  documentation.basis.cloud                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │                     Chat Widget                                   │ │ │
│  │  │                                                                   │ │ │
│  │  │  User: "How do I create a window in BBj?"                        │ │ │
│  │  │                                                                   │ │ │
│  │  │  Assistant: In modern BBj (DWC/GUI), you create windows          │ │ │
│  │  │  using the BBjAPI:                                               │ │ │
│  │  │                                                                   │ │ │
│  │  │  ```bbj                                                          │ │ │
│  │  │  sysgui! = BBjAPI().getSysGui()                                  │ │ │
│  │  │  window! = sysgui!.addWindow(100,100,800,600,"My App")           │ │ │
│  │  │  ```                                                             │ │ │
│  │  │                                                                   │ │ │
│  │  │  [Source: BBjSysGui.addWindow documentation]                     │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│                          WebSocket / REST                                    │
│                                      │                                       │
└──────────────────────────────────────┼───────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Chat Backend Service                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         Request Handler                                  ││
│  │                                                                          ││
│  │  1. Receive user question                                                ││
│  │  2. Analyze for generation hints                                         ││
│  │  3. Query RAG for relevant documentation                                 ││
│  │  4. Assemble prompt with context                                         ││
│  │  5. Call fine-tuned model                                                ││
│  │  6. Stream response with citations                                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                          │                         │                         │
│                          ▼                         ▼                         │
│  ┌───────────────────────────────┐  ┌─────────────────────────────────────┐ │
│  │  RAG Database                 │  │  Ollama                             │ │
│  │  (Shared with IDE)            │  │  (Shared with IDE)                  │ │
│  │                               │  │                                     │ │
│  │  • Generation-tagged docs     │  │  • bbj-finetuned model              │ │
│  │  • Version metadata           │  │  • Same model as IDE completion     │ │
│  │  • Code examples              │  │                                     │ │
│  └───────────────────────────────┘  └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Generation-Aware Responses

Chat responses should adapt to the user's context:

**Question without context:**
> "How do I create a window?"

**Response:**
> In modern BBj (DWC), you create windows using the BBjAPI:
> 
> ```bbj
> sysgui! = BBjAPI().getSysGui()
> window! = sysgui!.addWindow(100, 100, 800, 600, "My Application")
> ```
> 
> The parameters are: x position, y position, width, height, and title.
> 
> *Note: If you're maintaining legacy Visual PRO/5 code, the older `WINDOW CREATE` verb is also supported. Let me know if you need help with that syntax instead.*

**Question with legacy context:**
> "I'm working on a Visual PRO/5 application. How do I create a window?"

**Response:**
> In Visual PRO/5, you create windows using the WINDOW CREATE verb:
> 
> ```bbj
> WINDOW CREATE wnd_id, @(0,0), 80, 24, "My Application"
> ```
> 
> The parameters are: window ID variable, position, columns, rows, and title.
> 
> *Consider: For new development or gradual modernization, the BBjAPI approach offers more flexibility and better browser support. I can show you how to migrate this pattern if you're interested.*

---

## Component 4: RAG Database Design

### Multi-Generation Documentation Structure

Each documentation chunk includes generation metadata enabling filtered retrieval. The `generation` field uses the same schema as training data:

**Universal documentation (applies to all generations):**

```json
{
    "id": "bbj-for-next-001",
    "type": "language-reference",
    "topic": "FOR/NEXT loop",
    "generation": "all",
    "content": "The FOR/NEXT loop executes a block of statements a specified number of times. Syntax: FOR var = start TO end [STEP increment]...NEXT var",
    "keywords": ["loop", "iteration", "for", "next", "control flow"]
}
```

**Modern API documentation:**

```json
{
    "id": "bbj-addwindow-001",
    "type": "api-reference",
    "class": "BBjSysGui",
    "method": "addWindow",
    "generation": ["bbj-gui", "dwc"],
    "since_version": "12.00",
    "content": "Creates a new top-level window. Syntax: addWindow(int x, int y, int w, int h, String title)...",
    "signatures": [
        "BBjTopLevelWindow addWindow(int x, int y, int w, int h, String title)",
        "BBjTopLevelWindow addWindow(int id, int x, int y, int w, int h, String title)"
    ],
    "related": ["BBjTopLevelWindow", "BBjChildWindow", "addChildWindow"],
    "supersedes": "vpro5-window-create",
    "keywords": ["window", "gui", "create", "toplevel"]
}
```

**Legacy documentation (still valid, but superseded):**

```json
{
    "id": "vpro5-window-create-001",
    "type": "api-reference",
    "verb": "WINDOW CREATE",
    "generation": ["vpro5"],
    "deprecated_in": "12.00",
    "still_valid": true,
    "content": "Creates a GUI window using Visual PRO/5 syntax. WINDOW CREATE wnd_id, @(row,col), rows, cols, title$...",
    "superseded_by": "bbj-addwindow-001",
    "migration_note": "For new development, use BBjSysGui.addWindow() for better DWC compatibility.",
    "keywords": ["window", "gui", "create", "vpro5", "legacy"]
}
```

### Retrieval Strategy

```typescript
async function retrieveDocumentation(
    query: string, 
    generationHint?: string
): Promise<DocChunk[]> {
    // Vector search for semantic relevance
    const candidates = await vectorStore.search(query, { topK: 20 });
    
    // Score and filter by generation appropriateness
    const scored = candidates.map(doc => ({
        ...doc,
        generationScore: computeGenerationScore(doc.generation, generationHint)
    }));
    
    // Sort: modern first, but include legacy for context
    scored.sort((a, b) => {
        // Prefer exact generation match
        if (a.generationScore !== b.generationScore) {
            return b.generationScore - a.generationScore;
        }
        // Then by semantic relevance
        return b.relevanceScore - a.relevanceScore;
    });
    
    // Return top results with generation diversity
    return selectDiverseResults(scored, { maxResults: 5 });
}

function computeGenerationScore(
    docGeneration: "all" | string | string[], 
    targetGeneration?: string
): number {
    // Universal docs are always highly relevant
    if (docGeneration === "all") return 95;
    
    if (!targetGeneration) {
        // No hint: prefer modern, then universal
        if (Array.isArray(docGeneration)) {
            if (docGeneration.includes('dwc')) return 90;
            if (docGeneration.includes('bbj-gui')) return 85;
        }
        if (docGeneration === 'dwc') return 90;
        if (docGeneration === 'bbj-gui') return 85;
        if (docGeneration === 'vpro5') return 50;
        if (docGeneration === 'character') return 30;
        return 70;
    }
    
    // With target: check for match
    if (Array.isArray(docGeneration)) {
        if (docGeneration.includes(targetGeneration)) return 100;
    } else if (docGeneration === targetGeneration) {
        return 100;
    }
    
    // Close matches for GUI generations
    const guiGenerations = ['vpro5', 'bbj-gui', 'dwc'];
    if (guiGenerations.includes(targetGeneration)) {
        if (Array.isArray(docGeneration) && 
            docGeneration.some(g => guiGenerations.includes(g))) {
            return 70;
        }
    }
    
    return 20; // Different generation
}
```

### Document Types

| Type | Generation | Description | Example |
|------|------------|-------------|---------|
| `language-reference` | Usually `"all"` | Core language syntax | FOR/NEXT loops, file I/O |
| `api-reference` | Varies | Method/class documentation | BBjSysGui.addWindow() |
| `concept` | Varies | Conceptual explanation | "Understanding BBj Events" |
| `example` | Varies | Working code sample | "Creating a Grid Application" |
| `migration` | N/A (has from/to) | How to modernize legacy code | "Migrating from WINDOW CREATE" |
| `best-practice` | Often `"all"` | Recommended patterns | "Error Handling in BBj" |
| `version-note` | Varies | Version-specific behavior | "New in BBj 23.04: await parameter" |

---

## Implementation Roadmap

### Phase 1: Foundation (Months 1-2)

**Objectives:** Establish infrastructure and validate approach

**Deliverables:**
- [ ] Curate initial training dataset (5,000+ examples across all generations)
- [ ] Set up Ollama infrastructure
- [ ] Fine-tune initial model on base CodeLlama/DeepSeek
- [ ] Build basic RAG database with core API documentation
- [ ] Create evaluation benchmark for generation detection

**Success Criteria:**
- Model correctly identifies generation in 90%+ of test cases
- Model produces syntactically valid BBj code 95%+ of time
- Basic completion works for common patterns

### Phase 2: VSCode Extension (Months 2-4)

**Objectives:** Deliver IDE-based code assistance

**Deliverables:**
- [ ] Implement generation detection in Langium parser
- [ ] Create semantic context extraction API
- [ ] Build inline completion provider with Ollama integration
- [ ] Implement conflict avoidance with popup completion
- [ ] Add configuration UI and status indicators
- [ ] Beta testing with internal developers

**Success Criteria:**
- Ghost text latency <500ms (P50)
- Completion acceptance rate >20%
- Generation-appropriate suggestions in 95%+ of cases

### Phase 3: Documentation Chat (Months 4-5)

**Objectives:** Deploy website-based chat assistance

**Deliverables:**
- [ ] Build chat backend service
- [ ] Create embeddable chat widget
- [ ] Integrate with documentation website
- [ ] Implement streaming responses
- [ ] Add citation and source linking

**Success Criteria:**
- Accurate answers for common questions
- Source citations for all factual claims
- Appropriate generation handling

### Phase 4: Refinement (Months 5-6)

**Objectives:** Improve quality based on real-world usage

**Deliverables:**
- [ ] Expand training data based on user interactions
- [ ] Improve RAG coverage for edge cases
- [ ] Add migration assistant features
- [ ] Performance optimization
- [ ] Documentation and training materials

**Success Criteria:**
- Reduced hallucination rate
- Improved customer satisfaction scores
- Comprehensive documentation coverage

---

## Resource Requirements

### Infrastructure

| Component | Specification | Purpose |
|-----------|--------------|---------|
| Training server | GPU with 24GB+ VRAM | Model fine-tuning |
| Ollama server | 16GB+ RAM, GPU recommended | Model inference |
| Vector database | PostgreSQL + pgvector or dedicated vector DB | RAG storage |
| Chat backend | Standard web server | API for chat widget |

### Personnel

| Role | Effort | Responsibilities |
|------|--------|------------------|
| ML Engineer | 50% for 6 months | Fine-tuning, evaluation, optimization |
| Backend Developer | 50% for 6 months | RAG database, chat service, APIs |
| VSCode Extension Developer | 50% for 4 months | Langium integration, completion provider |
| Technical Writer | 25% for 3 months | Training data curation, documentation |
| QA | 25% for 4 months | Testing, benchmark development |

### Estimated Costs

| Item | One-Time | Monthly |
|------|----------|---------|
| GPU cloud for training | $2,000-5,000 | - |
| Ollama hosting (production) | - | $200-500 |
| Vector database hosting | - | $50-200 |
| Development time (6 months) | $150,000-250,000 | - |
| **Total Year 1** | **~$200,000-300,000** | **~$300-700** |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Fine-tuned model hallucinates BBj syntax | Medium | High | Extensive evaluation benchmark, Langium validation of suggestions |
| Training data insufficient for all generations | Medium | Medium | Prioritize common patterns, expand iteratively based on user feedback |
| Latency too high for good UX | Medium | Medium | Streaming responses, caching, model quantization |
| Customer code privacy concerns | Medium | Medium | Self-hosted Ollama option, clear data handling policies |
| Model size too large for customer hardware | Low | Medium | Offer multiple model sizes, cloud option for small customers |
| Generation detection fails for mixed codebases | Medium | Medium | Default to modern suggestions with legacy awareness |

---

## Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Completion latency (P50) | <500ms | Telemetry |
| Completion latency (P95) | <1500ms | Telemetry |
| Syntactically valid completions | >95% | Automated testing |
| Generation detection accuracy | >90% | Benchmark suite |
| Hallucination rate | <5% | Manual evaluation |

### User Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Completion acceptance rate | >20% | Telemetry (Tab presses / suggestions shown) |
| Chat satisfaction | >4/5 | User surveys |
| Feature adoption | >50% of active users | Telemetry |
| Support ticket reduction | 15% | Support system metrics |

### Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Customer retention improvement | +5% | CRM data |
| New developer onboarding time | -20% | Customer surveys |
| Migration project acceleration | -30% effort | Project tracking |

---

## Conclusion

BBj's unique position as a language spanning four generations of development paradigms creates both challenges and opportunities for AI-assisted development. While generic AI tools fail to provide meaningful assistance, a purpose-built solution combining fine-tuned language models, generation-aware context detection, and unified infrastructure can deliver significant value to the BBj developer community.

The proposed strategy leverages the same fine-tuned model and knowledge base across IDE and documentation interfaces, maximizing return on investment while ensuring consistency. By understanding all BBj generations while guiding developers toward modern patterns, the system supports both maintenance of legacy applications and development of new browser-based solutions.

This investment in AI infrastructure represents a competitive moat - no third-party tool can provide comparable BBj assistance, making our integrated solution an essential part of the BBj development experience.

---

## Appendix A: BBj Generation Quick Reference

### Universal Syntax (All Generations)

```bbj
REM Universal patterns work in ALL BBj generations

REM Variables and types
name$ = "John"           : REM String ($ suffix)
count = 42               : REM Numeric
price = 19.99            : REM Numeric (decimal)

REM Control structures
FOR i = 1 TO 10
    IF i MOD 2 = 0 THEN
        PRINT "Even: ", i
    ELSE
        PRINT "Odd: ", i
    ENDIF
NEXT i

REM File I/O
OPEN (1)"customers.dat"
READ (1, KEY=custId$) name$, balance
CLOSE (1)

REM Error handling
SETERR ERR_HANDLER
x = 1/0  : REM Will trigger error
GOTO CONTINUE
ERR_HANDLER:
    PRINT "Error: ", ERR
CONTINUE:

REM Subroutines
GOSUB CALC_TOTAL
PRINT "Total: ", total
END

CALC_TOTAL:
    total = subtotal * (1 + taxRate)
RETURN
```

### Character UI (Terminal)

```bbj
REM Character-mode application
PRINT 'CS',           : REM Clear screen
PRINT @(10,5),"Name: ",
INPUT name$
PRINT @(10,7),"Hello, ",name$
```

### Visual PRO/5 (Windows GUI)

```bbj
REM Visual PRO/5 GUI application
WINDOW CREATE wnd_id, @(0,0), 80, 24, "Main Window"
WINDOW SET wnd_id, 0, 100, 100  : REM Position
BUTTON CREATE btn_id, wnd_id, "Click Me", @(10,10), 15, 3
```

### BBj GUI (Swing) / DWC (Browser)

```bbj
REM Modern BBj application (GUI or DWC)
use java.util.HashMap

class public OrderEntry

    field private BBjTopLevelWindow window!
    field private BBjButton saveButton!
    
    method public void create()
        sysgui! = BBjAPI().getSysGui()
        #window! = sysgui!.addWindow(100, 100, 800, 600, "Order Entry")
        #saveButton! = #window!.addButton(101, 10, 10, 100, 25, "Save")
        #saveButton!.setCallback(#saveButton!.ON_BUTTON_PUSH, #this!, "onSave")
    methodend
    
    method public void onSave(BBjButtonPushEvent event!)
        rem Handle save
    methodend

classend
```

### DWC-Specific Features

```bbj
REM DWC-specific functionality
bui! = BBjAPI().getWebManager()
bui!.setCallback(bui!.ON_BROWSER_CLOSE, "handleClose")

REM Execute JavaScript asynchronously
bui!.setCallback(bui!.ON_EXECUTE_SCRIPT, "handleResult")
index = bui!.executeAsyncScript("fetch('/api/data').then(r => r.json())", 1)
```

---

## Appendix B: Sample Training Data Format

### Universal Pattern Example (generation: "all")

```json
{
    "id": "universal-for-loop-001",
    "type": "completion",
    "generation": "all",
    "difficulty": "basic",
    "instruction": "Complete the loop to calculate factorial",
    "input": "fact = 1\nFOR i = 1 TO n\n    fact = fact * i\n",
    "output": "NEXT i\nPRINT \"Factorial: \", fact"
}
```

```json
{
    "id": "universal-file-io-001",
    "type": "comprehension",
    "generation": "all",
    "difficulty": "intermediate",
    "instruction": "Explain this file operation",
    "input": "OPEN (1)\"customer.dat\"\nREAD (1,KEY=custId$)name$,address$,balance\nCLOSE (1)",
    "output": "This code reads a customer record from a keyed file:\n\n1. `OPEN (1)` opens the file 'customer.dat' on channel 1\n2. `READ (1,KEY=custId$)` reads the record matching the key value in custId$, storing fields in name$, address$, and balance\n3. `CLOSE (1)` closes the file channel\n\nThis keyed file access pattern works across all BBj generations."
}
```

### Generation-Specific Example (Visual PRO/5)

```json
{
    "id": "comp-vpro5-001",
    "type": "comprehension",
    "generation": "vpro5",
    "difficulty": "intermediate",
    "instruction": "Explain what this BBj code does",
    "input": "WINDOW CREATE wnd,@(5,5),40,10,\"Input\"\nBUTTON CREATE btn1,wnd,\"OK\",@(15,7),10,1\nBUTTON CREATE btn2,wnd,\"Cancel\",@(15,8),10,1",
    "output": "This Visual PRO/5 code creates a dialog window with two buttons:\n\n1. `WINDOW CREATE` creates a window stored in variable `wnd`, positioned at row 5, column 5, with dimensions 40 columns by 10 rows, titled \"Input\"\n2. Two buttons are created inside the window:\n   - \"OK\" button at position (15,7)\n   - \"Cancel\" button at position (15,8)\n\nThis is legacy Visual PRO/5 syntax. In modern BBj, you would use `sysgui!.addWindow()` and `window!.addButton()` for better DWC compatibility."
}
```

### Modern BBj Example (bbj-gui and dwc)

```json
{
    "id": "comp-modern-001", 
    "type": "completion",
    "generation": ["bbj-gui", "dwc"],
    "difficulty": "basic",
    "instruction": "Complete the event handler setup",
    "prefix": "class public MyApp\n\n    field private BBjTopLevelWindow window!\n    field private BBjButton button!\n    \n    method public void init()\n        sysgui! = BBjAPI().getSysGui()\n        #window! = sysgui!.addWindow(100,100,400,300,\"Test\")\n        #button! = #window!.addButton(101,10,10,100,25,\"Click\")\n        ",
    "completion": "#button!.setCallback(#button!.ON_BUTTON_PUSH, #this!, \"onClick\")\n    methodend\n    \n    method public void onClick(BBjButtonPushEvent event!)\n        rem Handle button click\n    methodend"
}
```

### DWC-Specific Example

```json
{
    "id": "dwc-async-001",
    "type": "completion",
    "generation": ["dwc"],
    "difficulty": "advanced",
    "instruction": "Complete the async JavaScript execution with callback",
    "prefix": "bui! = BBjAPI().getWebManager()\nbui!.setCallback(bui!.ON_EXECUTE_SCRIPT, \"handleResult\")\n",
    "completion": "index = bui!.executeAsyncScript(\"fetch('/api/data').then(r => r.json())\", 1)\n\nhandleResult:\n    event! = sysgui!.getLastEvent()\n    result! = event!.getResult()\n    rem Process the JavaScript result\nreturn"
}
```

### Migration Example

```json
{
    "id": "mig-001",
    "type": "migration",
    "from_generation": "vpro5",
    "to_generation": ["bbj-gui", "dwc"],
    "instruction": "Convert this Visual PRO/5 code to modern BBj",
    "input": "WINDOW CREATE wnd,@(0,0),80,24,\"Main\"\nBUTTON CREATE btn,wnd,\"Submit\",@(10,20),12,1",
    "output": "sysgui! = BBjAPI().getSysGui()\nwindow! = sysgui!.addWindow(0, 0, 640, 480, \"Main\")\nbutton! = window!.addButton(101, 80, 400, 96, 25, \"Submit\")\n\nREM Note: Coordinates converted from character cells to pixels\nREM assuming approximately 8 pixels per character column\nREM and 20 pixels per character row"
}
```

### Training Data Schema

```typescript
interface TrainingExample {
    id: string;
    type: 'comprehension' | 'completion' | 'migration' | 'explanation';
    
    // Generation scope:
    // - "all" for universal patterns (loops, file I/O, string functions)
    // - Single generation: "character" | "vpro5" | "bbj-gui" | "dwc"
    // - Array for subset: ["bbj-gui", "dwc"]
    generation: "all" | Generation | Generation[];
    
    instruction: string;
    input?: string;           // For comprehension/migration
    prefix?: string;          // For completion
    output: string;           // Expected completion or explanation
    completion?: string;      // Alternative to output for completion type
    
    // Optional metadata
    difficulty?: 'basic' | 'intermediate' | 'advanced';
    topics?: string[];
    from_generation?: Generation;  // For migration examples
    to_generation?: Generation | Generation[];
    requires_version?: string;     // e.g., "23.04"
}

type Generation = "character" | "vpro5" | "bbj-gui" | "dwc";
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **"all" (generation)** | Label for patterns that work across all BBj generations (loops, file I/O, string functions) |
| **BBj** | BASIS Business BASIC for Java - the current generation of the Business BASIC language |
| **DWC** | Dynamic Web Client - BBj's browser-based rendering engine |
| **Visual PRO/5** | The Windows-based GUI generation of Business BASIC (1990s-2000s) |
| **Character UI** | Terminal-based text interface using mnemonics and positioning |
| **Langium** | TypeScript-based language engineering framework for building language servers |
| **RAG** | Retrieval-Augmented Generation - combining search with LLM generation |
| **MCP** | Model Context Protocol - standard for connecting AI assistants to external tools |
| **Fine-tuning** | Training a base model on domain-specific data to improve performance |
| **Ghost text** | Dimmed inline code suggestions in an editor (Copilot-style) |
| **Generation** | One of the four paradigms of BBj development (character, VP/5, GUI, DWC) |
| **Ollama** | Open-source tool for running LLMs locally |
| **LoRA/QLoRA** | Parameter-efficient fine-tuning techniques for LLMs |
