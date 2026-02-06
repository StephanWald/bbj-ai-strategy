# Architecture: Fine-Tuned Model Integration with RAG + MCP System

**Milestone:** v1.7 Documentation Refresh & Fine-Tuning Strategy
**Researched:** 2026-02-06
**Mode:** Ecosystem (architecture dimension)
**Overall confidence:** MEDIUM (model serving path verified; generate_bbj_code implementation is design recommendation; IDE integration options verified against current docs)

> **Context:** The RAG system is operational (v1.6). The fine-tuning repo (`bbjllm`) trains Qwen2.5-Coder-32B-Instruct with QLoRA/PEFT on 9,922 ChatML examples targeting a remote GPU server. The documentation (Chapter 2) describes a `generate_bbj_code` MCP tool and a generate-validate-fix loop that do not yet exist. This research defines the realistic integration architecture and identifies what the documentation should say.

---

## 1. Current System Topology (Actual State)

```
                         macOS Host (Developer)
                    +---------------------------+
                    |  Ollama :11434            |  Qwen3-Embedding-0.6B (embeddings)
                    |  bbjcpl compiler          |  BBj syntax validation
                    +------------+--------------+
                                 |
                   host.docker.internal:11434
                                 |
        Docker Compose Network (bbj-rag-net)
   +----------------------------------------------------------+
   |                                                          |
   |  +------------------+     +---------------------------+  |
   |  | db (pgvector)    |     | app (FastAPI)             |  |
   |  | pg17 + pgvector  |     |                           |  |
   |  | :5432            |<--->| GET  /health              |  |
   |  |                  |     | POST /search              |  |
   |  | 51K+ chunks      |     | GET  /stats               |  |
   |  | HNSW + GIN idx   |     | GET  /chat                |  |
   |  +------------------+     | POST /chat/stream         |  |
   |                           | POST /mcp (Streamable HTTP)|  |
   |                           +---------------------------+  |
   +----------------------------------------------------------+
                                 |
                           :10800 (mapped)
                                 |
               +--------+--------+--------+
               |                          |
   Claude Desktop (MCP stdio)    Web Browser (/chat)
   Claude Desktop (MCP HTTP)     Claude API (chat backend)


                    Remote GPU Server
                    +---------------------------+
                    |  bbjllm repo              |
                    |  Qwen2.5-Coder-32B        |
                    |  QLoRA training (PEFT)     |
                    |  9,922 ChatML examples     |
                    |  NOT connected to RAG      |
                    +---------------------------+
```

### What Exists (Operational)

| Component | Status | Location |
|-----------|--------|----------|
| RAG pipeline (pgvector, 51K+ chunks) | Operational | Docker Compose |
| FastAPI REST API (/search, /stats, /health) | Operational | Docker Compose |
| MCP server (search_bbj_knowledge, validate_bbj_syntax) | Operational | stdio + Streamable HTTP |
| Web chat (/chat, Claude API, SSE streaming) | Operational | Docker Compose |
| Compiler validation (bbjcpl -N) | Operational | Host-side subprocess |
| Training data repo (2 seed examples, JSON Schema) | Operational | training-data/ |

### What Does NOT Exist

| Component | Doc Chapter | Status |
|-----------|-------------|--------|
| `generate_bbj_code` MCP tool | Ch. 2 describes it | NOT IMPLEMENTED |
| Generate-validate-fix loop (automated) | Ch. 2 describes sequence diagram | NOT IMPLEMENTED (chat has manual validate-fix) |
| Fine-tuned model served via Ollama | Ch. 3 describes it | NOT TRAINED YET (training script exists) |
| Connection between bbjllm and RAG system | Ch. 2 implies it | NO CONNECTION |
| Training data conversion pipeline (markdown to ChatML) | Implied by both repos | DOES NOT EXIST |

---

## 2. Model Serving Architecture

### The Path from QLoRA Training to Ollama Serving

The bbjllm repo trains a QLoRA adapter on Qwen2.5-Coder-32B-Instruct using PEFT. The adapter output is safetensors format at `/usr2/yasser_experiment/trained_models/bbj_qwen_coder_adapters_32b_4bit/`. To serve via Ollama, there are two paths:

**Path A: GGUF Conversion (Recommended)**

```
QLoRA Adapter (safetensors)
        |
        v
convert_lora_to_gguf.py (llama.cpp)  -- converts adapter to GGUF format
        |
        v
Ollama Modelfile:
  FROM qwen2.5-coder:32b-instruct-q4_K_M
  ADAPTER ./bbj-adapter.gguf
        |
        v
ollama create bbj-coder -f Modelfile
        |
        v
ollama run bbj-coder
  (or via OpenAI-compatible API at :11434/v1/chat/completions)
```

**Path B: Direct Safetensors Import (Simpler but less tested for Qwen2)**

```
Ollama Modelfile:
  FROM qwen2.5-coder:32b-instruct
  ADAPTER /path/to/adapter/directory/
        |
        v
ollama create bbj-coder -f Modelfile
```

**Confidence: MEDIUM.** Ollama's import docs list supported architectures for safetensors adapter import as "Llama, Mistral, Gemma." Qwen2 is NOT explicitly listed for safetensors adapter import, though the Qwen2 architecture is fully supported for base model inference. GitHub issue #8132 reports issues with fine-tuned Qwen2.5-Instruct models. The GGUF conversion path via llama.cpp's `convert_lora_to_gguf.py` is more reliable because llama.cpp's Qwen2 architecture support is mature.

**Critical consideration for 32B model:** The 32B parameter model at Q4 quantization requires approximately 18-20 GB VRAM. This is feasible on modern consumer GPUs (RTX 4090: 24GB) or Apple Silicon (M2 Ultra: 192GB unified). For a shared internal server, this is the primary hardware constraint. Inference latency for a 32B Q4 model on a single GPU is approximately 10-30 tokens/second, which is acceptable for code generation but slow for interactive chat.

**Recommendation for documentation:** State that the fine-tuned model will be served via Ollama's OpenAI-compatible API at `http://<server>:11434/v1/chat/completions`. This is the same interface already used for embeddings, requiring no new infrastructure. The GGUF conversion step should be documented as a required post-training step.

### How generate_bbj_code Connects to Ollama

The `generate_bbj_code` MCP tool is the bridge between the MCP protocol and the fine-tuned model. It does NOT call Claude API -- it calls the local Ollama instance serving the fine-tuned BBj model.

**Recommended implementation:**

```python
# In mcp_server.py (addition to existing tools)

import httpx

OLLAMA_MODEL_URL = os.environ.get(
    "BBJ_CODE_MODEL_URL", "http://localhost:11434"
)
BBJ_CODE_MODEL = os.environ.get("BBJ_CODE_MODEL", "bbj-coder")


@mcp.tool()
async def generate_bbj_code(
    prompt: str,
    generation: str = "dwc",
    context: str | None = None,
    max_tokens: int = 512,
) -> str:
    """Generate BBj code using the fine-tuned BBj model.

    Uses the locally hosted fine-tuned Qwen2.5-Coder model via Ollama.
    Optionally enriches the prompt with RAG-retrieved documentation.

    Args:
        prompt: Natural language description of the code to generate.
        generation: Target BBj generation (character, vpro5, bbj-gui, dwc).
        context: Optional surrounding code or additional context.
        max_tokens: Maximum tokens in the generated response.
    """
    # Step 1: Retrieve relevant documentation from RAG
    rag_context = ""
    try:
        rag_results = await _search_rag(prompt, generation, limit=3)
        if rag_results:
            rag_context = _format_rag_context(rag_results)
    except Exception:
        pass  # RAG enrichment is optional; model works without it

    # Step 2: Build prompt for the fine-tuned model
    system_msg = (
        f"You are an expert BBj programmer. Generate {generation}-generation "
        f"BBj code. Use correct syntax for the target generation."
    )
    if rag_context:
        system_msg += f"\n\nRelevant documentation:\n{rag_context}"

    user_msg = prompt
    if context:
        user_msg = f"Context:\n{context}\n\nTask: {user_msg}"

    # Step 3: Call fine-tuned model via Ollama OpenAI-compatible API
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{OLLAMA_MODEL_URL}/v1/chat/completions",
            json={
                "model": BBJ_CODE_MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()

    result = resp.json()
    return result["choices"][0]["message"]["content"]
```

**Key design decisions:**

1. **Uses Ollama's OpenAI-compatible API**, not the native Ollama API. This allows swapping in vLLM or any OpenAI-compatible server without code changes.
2. **RAG enrichment is optional.** The fine-tuned model has BBj knowledge baked in from training. RAG provides supplemental context (API signatures, latest docs) but is not required for every generation request.
3. **Separate from the chat endpoint.** The `/chat` endpoint uses Claude API with RAG context for documentation Q&A. The `generate_bbj_code` tool uses the fine-tuned model for code generation. These are different models for different tasks.

### How generate_bbj_code Differs from Claude API Chat

| Aspect | /chat (Claude API) | generate_bbj_code (Fine-tuned Model) |
|--------|-------------------|--------------------------------------|
| Model | Claude Sonnet 4.5 (cloud) | bbj-coder via Ollama (local) |
| Primary use | Documentation Q&A, explanations | Code generation, completions |
| RAG dependency | Required (grounding for citations) | Optional (enrichment only) |
| Cost | Per-token (Anthropic billing) | Zero per-query (local inference) |
| Latency | 500-1500ms first token (network) | 200-500ms first token (local) |
| BBj knowledge source | RAG retrieval + Claude's training | Fine-tuned weights + optional RAG |
| Quality for code | Good with RAG context, but Claude invents syntax | Trained on actual BBj syntax |
| Quality for explanations | Excellent (strong instruction following) | Weaker (32B vs frontier model) |
| Validation | Manual validate-fix in chat stream | Automated loop possible via MCP |
| Privacy | Code sent to Anthropic API | Fully local |

**Recommendation for documentation:** The two paths should be described as complementary, not competing. Claude API excels at documentation Q&A and explanations. The fine-tuned model excels at code generation. A developer asking "How do I create a BBj window?" gets a Claude-powered explanation with cited documentation. A developer asking for code generation gets the fine-tuned model output with compiler validation.

---

## 3. Generate-Validate-Fix Loop

### What Chapter 2 Describes (Conceptual)

Chapter 2 shows a sequence diagram where:
1. MCP host calls `search_bbj_knowledge` for context
2. MCP host calls `generate_bbj_code` with enriched prompt
3. MCP host calls `validate_bbj_syntax` with generated code
4. If invalid, MCP host calls `generate_bbj_code` again with errors
5. Loop continues until valid or max iterations

### What Already Exists (Partial Implementation)

The chat streaming module (`stream.py`) already implements a validate-fix loop:

```python
# From stream.py _validate_response_code():
# 1. Extract BBj code blocks from Claude's response
# 2. Validate each via bbjcpl
# 3. If invalid, ask Claude to fix (up to 3 attempts)
# 4. Replace code blocks with fixed versions
# 5. Add warnings for unfixable blocks
```

This is a **server-side, Claude-powered** validate-fix loop. It uses Claude (not the fine-tuned model) to fix code, and it runs automatically as part of the chat streaming pipeline.

### What the MCP Loop Would Look Like (Not Yet Built)

The MCP-based loop is fundamentally different: it is **client-orchestrated** (the MCP host decides when to retry) and uses the **fine-tuned model** (not Claude) for both generation and fixing.

**There are two viable architectures:**

#### Architecture A: Client-Orchestrated Loop (What Ch. 2 Describes)

The MCP host (Claude Desktop, Cursor, IDE extension) orchestrates the loop by calling tools sequentially:

```
MCP Host (Claude Desktop / IDE)
    |
    |-- 1. Call search_bbj_knowledge("BBjGrid creation")
    |       -> Returns: documentation context
    |
    |-- 2. Call generate_bbj_code(prompt, context)
    |       -> Returns: generated BBj code
    |
    |-- 3. Call validate_bbj_syntax(code)
    |       -> Returns: "Invalid: Line 5: Syntax error"
    |
    |-- 4. Call generate_bbj_code(original_prompt + errors)
    |       -> Returns: corrected BBj code
    |
    |-- 5. Call validate_bbj_syntax(corrected_code)
    |       -> Returns: "Valid"
    |
    v
    Present validated code to developer
```

**Advantage:** The MCP host (which is typically a frontier model like Claude) decides when to loop and how to modify the prompt. This leverages Claude's reasoning for error interpretation.

**Disadvantage:** Requires the MCP host to understand the loop pattern. Claude Desktop and Claude Code already do this naturally when they see tool results. But a simple IDE extension would need explicit loop logic.

#### Architecture B: Server-Side Orchestrated Loop (Single Tool)

A single `generate_validated_bbj_code` tool that handles the loop internally:

```python
@mcp.tool()
async def generate_validated_bbj_code(
    prompt: str,
    generation: str = "dwc",
    context: str | None = None,
    max_attempts: int = 3,
) -> str:
    """Generate and validate BBj code, retrying on compiler errors.

    Calls the fine-tuned model, validates via bbjcpl, and retries
    with compiler feedback until valid or max attempts reached.
    """
    code = await _generate_code(prompt, generation, context)

    for attempt in range(max_attempts):
        result = await validate_bbj_syntax(code)
        if "Valid" in result:
            return f"```bbj\n{code}\n```\n\nCompiler validation: PASSED"

        # Feed errors back to fine-tuned model
        fix_prompt = (
            f"The following BBj code has compiler errors:\n\n"
            f"```bbj\n{code}\n```\n\n"
            f"Compiler output:\n{result}\n\n"
            f"Fix the code. Return ONLY the corrected BBj code."
        )
        code = await _generate_code(fix_prompt, generation, context)

    return (
        f"```bbj\n{code}\n```\n\n"
        f"WARNING: Code did not pass validation after {max_attempts} attempts.\n"
        f"Last compiler output:\n{result}"
    )
```

**Advantage:** Simpler for MCP hosts -- one tool call returns validated code. No loop logic needed in the client.

**Disadvantage:** Hides the process from the MCP host. Claude Desktop cannot inspect intermediate results or modify the approach.

### Recommendation

**Use Architecture A (client-orchestrated) as the primary pattern.** Claude Desktop and Claude Code are sophisticated enough to orchestrate the loop themselves -- they already do this with the existing `validate_bbj_syntax` tool. Provide the three tools as building blocks.

**Offer Architecture B as a convenience tool** for simpler clients (IDE extensions, scripts) that want a single-call code generation with validation.

**The existing chat validate-fix loop in stream.py should remain as-is** for the web chat, since there is no MCP client involved -- the server orchestrates validation internally.

### How Similar Systems Handle This

**LLMLOOP (ICSME 2025):** Implements five iterative loops for Java code: compilation errors, static analysis, test failures, mutation analysis, and coverage improvement. The key finding: compiler feedback loops are effective (65-82% of compilation errors fixed in first iteration) but expensive (each loop invocation calls the LLM). Limiting to 3 iterations is the standard trade-off. HIGH confidence -- peer-reviewed research.

**Cursor's approach:** Uses a "lint-fix" pattern where generated code is checked against language-specific linters/compilers, and errors are fed back to the model. This happens transparently inside the agent loop. The model sees the original request + the error output + instructions to fix.

**The BBj system has a unique advantage:** bbjcpl provides binary pass/fail with exact error locations, which is more actionable than heuristic linting. Most LLM code generation systems lack access to the actual production compiler.

---

## 4. RAG + Fine-Tuned Model Interaction

### When to Use Which Path

```
User Query
    |
    +-- Is this a documentation/explanation question?
    |     "What does BBjGrid support?"
    |     "How do callbacks work in BBj?"
    |     -> Route to Claude API + RAG (/chat)
    |     -> Claude excels at explanation, citation, nuance
    |
    +-- Is this a code generation request?
    |     "Write a BBj program that creates a grid with sorting"
    |     "Complete this function"
    |     -> Route to fine-tuned model (generate_bbj_code)
    |     -> Fine-tuned model excels at BBj syntax, patterns
    |
    +-- Is this a code explanation or review request?
    |     "What does this legacy BBj code do?"
    |     -> Route to Claude API + RAG (/chat)
    |     -> Claude's reasoning + RAG context for legacy patterns
    |
    +-- Is this a migration request?
          "Convert this Visual PRO/5 code to DWC"
          -> Route to fine-tuned model with RAG context
          -> Fine-tuned model knows both generations
```

### The Hybrid Pattern: RAFT (Retrieval-Augmented Fine-Tuning)

The ideal architecture is not RAG-or-fine-tuning but RAG-and-fine-tuning. The fine-tuned model has BBj syntax knowledge baked in, but it was trained on a static dataset. RAG provides:

1. **API signatures that may have changed** since training data was curated
2. **Specific documentation passages** that ground the response in official docs
3. **Code examples from the corpus** that the model may not have memorized
4. **Generation-specific context** that helps the model target the right BBj era

**Practical implementation:**

```
generate_bbj_code(prompt="Create a BBjGrid with 3 columns", generation="dwc")
    |
    |-- 1. Search RAG: "BBjGrid creation columns DWC"
    |       Returns: BBjGrid API docs, addColumn() signatures, examples
    |
    |-- 2. Build enriched prompt:
    |       System: "You are a BBj expert. Use the documentation below."
    |       + RAG results (API signatures, examples)
    |       + User prompt
    |
    |-- 3. Call fine-tuned model with enriched prompt
    |       Model generates code using both its training AND the RAG context
    |
    |-- 4. Validate with bbjcpl
    |       If invalid, retry with error feedback
    |
    v
    Return validated BBj code
```

**Why this works better than either approach alone:**
- Fine-tuned model alone: May generate outdated API calls or miss generation-specific nuances
- RAG + Claude alone: Claude invents BBj syntax despite having correct documentation (the core problem from Chapter 1)
- RAG + fine-tuned model: The model knows BBj syntax from training AND has current API docs from RAG

### Query Routing (Future)

For the v1.7 documentation, do NOT describe an automated query router. The current system uses explicit paths:
- Web chat = Claude API + RAG (always)
- MCP generate_bbj_code = fine-tuned model + optional RAG (when implemented)
- MCP search_bbj_knowledge = RAG only (no LLM generation)
- MCP validate_bbj_syntax = bbjcpl only (no LLM involved)

Query routing (automatic detection of "is this a code request or a docs request?") is an agentic RAG feature that is explicitly out of scope per PROJECT.md. Document the manual routing -- developers choose which tool or interface to use.

---

## 5. Training Data Pipeline

### Current State: Two Disconnected Formats

**training-data/ (bbj-ai-strategy repo):**
- Markdown files with YAML front matter
- JSON Schema validation
- 2 seed examples (hello-window, keyed-file-read)
- Topic-based directory structure (gui/, database/, control-flow/, etc.)
- Human-readable, GitHub-renderable
- Designed for contributors to write new examples

**dataset/dataset.jsonl (bbjllm repo):**
- ChatML JSONL format (9,922 examples)
- System/user/assistant message triples
- Uniform system message: "You are an expert BBj programmer who helps users write and understand BBj code."
- Inconsistent formatting (some examples use ```bbj fences, some use > prefix, some are raw text)
- No generation tagging
- No difficulty metadata

### The Gap

The training-data/ repo was designed as a curated, validated pipeline for high-quality examples. The bbjllm repo's dataset.jsonl was independently created with bulk-generated examples. They share no data and no conversion pipeline.

### Recommended Architecture: training-data/ as Source of Truth

```
training-data/ (human-authored, validated)
    |
    v
convert_to_chatml.py (new script)
    |
    |-- Parse markdown front matter
    |-- Extract code blocks and explanations
    |-- Map example types to ChatML conversations:
    |     completion  -> user: "Write BBj code to..." / assistant: code
    |     comprehension -> user: "Explain this BBj code: ..." / assistant: explanation
    |     migration   -> user: "Convert this ... to ..." / assistant: converted code
    |     explanation -> user: "What does X do?" / assistant: explanation
    |-- Include generation context in system message
    |-- Output: examples.jsonl (ChatML format)
    |
    v
Merge with existing dataset.jsonl (bbjllm repo)
    |
    |-- Deduplicate
    |-- Validate format
    |-- Output: final training dataset
    |
    v
Train via train_qwen_32b.py
```

**Conversion script design:**

```python
# training-data/scripts/convert_to_chatml.py (new)

def convert_completion(example):
    """Convert a 'completion' type example to ChatML."""
    return {
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are an expert BBj programmer. "
                    f"Generate {example['generation']}-generation BBj code."
                ),
            },
            {
                "role": "user",
                "content": example["description"] or example["title"],
            },
            {
                "role": "assistant",
                "content": example["code_blocks"][0],
            },
        ]
    }


def convert_comprehension(example):
    """Convert a 'comprehension' type example to ChatML."""
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are an expert BBj programmer who helps users understand BBj code.",
            },
            {
                "role": "user",
                "content": f"Explain this BBj code:\n\n```bbj\n{example['code_blocks'][0]}\n```",
            },
            {
                "role": "assistant",
                "content": example["explanation"],
            },
        ]
    }
```

**Recommendation for v1.7 documentation:**
- Document training-data/ as the canonical format for new BBj training examples
- Document the conversion pipeline as a planned automation step
- Acknowledge that bbjllm's dataset.jsonl was independently created
- Recommend that high-quality examples from dataset.jsonl be back-ported to training-data/ format for validation and curation
- Do NOT recommend that training-data/ fully replace dataset.jsonl -- the 9,922 existing examples have value even if they lack metadata

### Key Observations About the Existing Dataset

From examining dataset.jsonl:
- Examples are heavily focused on functions (ERR, ADJN, IOR, MAX, DEC, etc.)
- Many are extremely short (one-line answers)
- Some have duplicate user prompts with different responses
- Some assistant responses lack BBj code fences or use inconsistent formatting
- No generation tagging means the model cannot learn generation-appropriate behavior
- System prompt is identical for all 9,922 examples

**These are not blocking issues for an initial fine-tune** but represent technical debt that the training-data/ curation pipeline is designed to address over time.

---

## 6. IDE Integration Options (Ranked by Feasibility)

### Option 1: Continue.dev + Ollama (MOST FEASIBLE)

**Feasibility: HIGH. Available today.**

Continue.dev is an open-source AI coding assistant for VS Code and JetBrains. It supports:
- **Chat:** Configure any Ollama model for chat conversations
- **Tab autocomplete:** Configure a local model for inline completions (FIM)
- **Custom models:** Point to any Ollama endpoint, including custom fine-tuned models
- **MCP tools:** Continue.dev supports MCP server connections (experimental)

**Configuration for BBj:**

```yaml
# ~/.continue/config.yaml
models:
  - title: "BBj Coder"
    provider: ollama
    model: bbj-coder
    apiBase: http://server-ip:11434

tabAutocompleteModel:
  title: "BBj Autocomplete"
  provider: ollama
  model: bbj-coder
  apiBase: http://server-ip:11434
```

**Limitations:**
- Tab autocomplete works best with models trained for Fill-in-the-Middle (FIM). The current bbjllm training is instruction-tuned (ChatML), NOT FIM-trained. This means chat works well but inline ghost-text completion may be poor.
- Continue.dev does not have BBj syntax highlighting. Code blocks will be treated as plain text.
- MCP integration in Continue.dev is experimental as of early 2026.

**Recommendation:** This is the fastest path to "developer uses fine-tuned BBj model in their IDE." The chat interface will work immediately. Tab autocomplete requires FIM training data, which is a training methodology change for a future iteration.

### Option 2: GitHub Copilot BYOK + Ollama (FEASIBLE FOR CHAT ONLY)

**Feasibility: MEDIUM. Chat works; inline completions do NOT.**

GitHub Copilot BYOK (Bring Your Own Key) now supports Ollama as a provider:
- **Chat:** Works. Configure `github.copilot.chat.byok.ollamaEndpoint` in VS Code settings.
- **Inline completions:** NOT SUPPORTED for local models. BYOK only works for chat, not for ghost-text tab completion.
- **Agent mode:** Works with BYOK models for tool-calling scenarios.

**Configuration for BBj:**

```json
// VS Code settings.json
{
  "github.copilot.chat.models": [
    {
      "provider": "ollama",
      "model": "bbj-coder",
      "name": "BBj Coder"
    }
  ]
}
```

**Critical limitation:** The most valuable IDE integration (inline code completion as you type) does not work with local models in Copilot BYOK. You only get the chat panel. This significantly reduces the value proposition compared to Continue.dev.

**Known issues:** Multiple GitHub community discussions report compatibility regressions with Ollama in Copilot BYOK as of early 2026. The integration is in public preview and unstable.

### Option 3: Cursor + Ollama via OpenAI Override (FEASIBLE WITH WORKAROUNDS)

**Feasibility: MEDIUM. Requires ngrok or network tunnel.**

Cursor supports OpenAI API overrides, and Ollama provides an OpenAI-compatible API. However, Cursor's backend runs in a sandboxed environment that cannot access `localhost:11434` directly.

**Workaround:** Use ngrok to tunnel Ollama to a public URL:
```bash
OLLAMA_ORIGINS="*" ollama serve
ngrok http 11434
# Use the ngrok URL in Cursor settings
```

**Or** for a shared server on LAN:
```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
# Use server-ip:11434 in Cursor settings
```

Cursor supports using custom models for chat. Inline completions with custom models are possible but less reliable than the built-in models.

### Option 4: bbj-language-server (Existing, Not AI-Powered)

**Feasibility: Already exists (v0.5.0 on Marketplace).**

The existing bbj-language-server provides:
- Syntax highlighting
- Symbol completion
- Diagnostics
- Formatting
- Code execution

This does NOT use AI. The Chapter 4 vision of "two-layer completion" (Langium deterministic + LLM generative) is aspirational. Integrating the fine-tuned model into the language server requires:
1. A VS Code extension that acts as MCP client
2. Or a direct Ollama API integration in the extension
3. FIM-trained model for inline completions

**This is the most complex option** and should be described as a future phase, not a near-term goal.

### IDE Integration Summary

| Option | Chat | Inline Completion | MCP Tools | Setup Effort | Stability |
|--------|------|-------------------|-----------|-------------|-----------|
| Continue.dev + Ollama | YES | YES (needs FIM model) | Experimental | Low | HIGH |
| Copilot BYOK + Ollama | YES | NO | Agent mode | Low | MEDIUM |
| Cursor + Ollama | YES | Partial | No | Medium (ngrok) | MEDIUM |
| bbj-language-server | NO (future) | NO (future) | NO (future) | High | N/A |

**Documentation recommendation:** Present Continue.dev as the primary IDE integration path for the fine-tuned model. It is the only option that supports both chat and inline completions with local models. Copilot BYOK is a secondary option for teams already using Copilot. The bbj-language-server + AI integration is a future phase.

---

## 7. Deployment Topology

### Recommended Setup for Internal Exploration

```
Shared Server (GPU-equipped, on LAN)
+--------------------------------------------------+
|                                                  |
|  Ollama :11434                                   |
|    - qwen3-embedding:0.6b  (RAG embeddings)     |
|    - bbj-coder             (fine-tuned model)    |
|                                                  |
|  Docker Compose                                  |
|    - db: pgvector (51K+ chunks)    :10432        |
|    - app: FastAPI                  :10800        |
|      - /search (RAG API)                         |
|      - /chat (Claude API + RAG)                  |
|      - /mcp (Streamable HTTP)                    |
|                                                  |
|  bbjcpl compiler (host-side)                     |
|                                                  |
+--------------------------------------------------+
         |              |              |
    LAN :10800     LAN :11434    LAN :10432
         |              |              |
   +-----+-----+  +----+----+  +-----+-----+
   |           |  |         |  |           |
Dev 1       Dev 2        Dev 3          Dev 4
Claude      Continue     Cursor      Web Browser
Desktop     .dev IDE     IDE         /chat
(MCP HTTP)  (Ollama)    (Ollama)    (Claude API)
```

**Key decisions:**

1. **One server, multiple consumers.** All developers connect to the same Ollama instance and the same RAG database. No per-developer GPU needed.

2. **Ollama serves both models.** The embedding model (Qwen3-Embedding-0.6B, ~1.2GB) and the fine-tuned code model (bbj-coder 32B Q4, ~18GB) run on the same Ollama instance. Ollama handles model loading/unloading. With 24+ GB VRAM, both can be resident simultaneously.

3. **bbjcpl must be on the server.** The validate_bbj_syntax MCP tool calls bbjcpl as a subprocess. BBj must be installed on the shared server. This is the only host-side dependency.

4. **Claude API is server-side only.** The ANTHROPIC_API_KEY is configured on the server. Individual developers do not need their own API keys for the web chat. They DO need their own keys if using Claude Desktop directly.

5. **Ollama is network-accessible.** Set `OLLAMA_HOST=0.0.0.0:11434` so that Continue.dev and Cursor on developer machines can reach the fine-tuned model.

### Hardware Requirements

| Component | Min VRAM | Min RAM | Notes |
|-----------|----------|---------|-------|
| Qwen3-Embedding-0.6B | ~0.5 GB | ~2 GB | Small, fast, always loaded |
| bbj-coder 32B Q4 | ~18 GB | ~4 GB | Large, slower inference |
| pgvector (51K chunks) | N/A | ~2 GB | Database, no GPU needed |
| FastAPI + uvicorn | N/A | ~0.5 GB | Application server |
| **Total** | **~19 GB VRAM** | **~8.5 GB RAM** | |

**GPU recommendation:** A single NVIDIA RTX 4090 (24 GB) or A6000 (48 GB). For Apple Silicon, an M2 Pro/Max/Ultra with 32+ GB unified memory. The remote GPU server used for training (bbjllm) could be repurposed for inference if it has CUDA-compatible GPUs.

**If 32B is too large:** Fall back to Qwen2.5-Coder-7B-Instruct with the same QLoRA approach. 7B Q4 requires ~4 GB VRAM and infers at 50-100 tokens/second -- much faster and viable on consumer hardware. The documentation should recommend starting with 7B for internal exploration and scaling to 32B only if quality demands it.

---

## 8. Gap Analysis: Documentation vs Reality

### Chapter 2 Claims vs Actual Status

| Documentation Claim | Actual Status | Recommended Doc Update |
|---------------------|---------------|----------------------|
| Three MCP tools: search, generate, validate | Two implemented (search, validate). Generate does not exist. | State that generate_bbj_code is planned, with implementation design defined. Describe the two working tools as "operational" and the third as "pending fine-tuned model." |
| Generate-validate-fix loop (sequence diagram) | Chat has a server-side validate-fix loop using Claude. MCP-based loop with fine-tuned model does not exist. | Distinguish between existing (chat validate-fix) and planned (MCP generate-validate-fix). The chat loop is working; the MCP loop depends on generate_bbj_code. |
| "Fine-tuned BBj model ~10K examples, Qwen2.5-Coder-7B" | Actually training on 32B-Instruct (not 7B-Base), using PEFT/QLoRA (not Unsloth). 9,922 ChatML examples. | Update model name, training approach, and example count. Major correction needed in Chapter 3. |
| "Qwen2.5-Coder-7B via Ollama" in architecture diagram | Model will be 32B, served via Ollama after GGUF conversion. | Update architecture diagram to show 32B. Note hardware requirements. |
| Clients connect through MCP server to all three tools | search and validate work via MCP. Chat uses Claude API directly (not MCP). | Clarify that web chat is NOT an MCP client -- it is a direct Claude API consumer with RAG context. |
| "Training data structure" shows JSON format | Two separate formats exist: markdown (training-data/) and ChatML JSONL (bbjllm/). Neither matches the JSON shown in docs. | Document both formats honestly. Explain conversion pipeline. |

### Tone Corrections Needed

The documentation uses aspirational language ("The BBj MCP Server defines three tools") for components that do not exist. For v1.7, every component should be labeled:

- **Operational:** search_bbj_knowledge, validate_bbj_syntax, web chat, RAG pipeline
- **In progress:** Fine-tuned model training (bbjllm repo)
- **Planned (design defined):** generate_bbj_code, MCP generate-validate-fix loop
- **Future:** Automated query routing, IDE integration, customer self-hosting

---

## 9. Confidence Assessment

| Area | Confidence | Rationale |
|------|-----------|-----------|
| Model serving via Ollama | MEDIUM | Qwen2 GGUF base model works. Adapter import for Qwen2 specifically has reported issues (GitHub #8132). GGUF conversion via llama.cpp is more reliable. Needs testing. |
| generate_bbj_code implementation | HIGH (design) / N/A (reality) | The implementation pattern (Ollama OpenAI-compatible API + optional RAG enrichment) is well-established. But the tool does not exist yet and depends on a trained model. |
| Generate-validate-fix loop | HIGH (design) | The pattern is proven by LLMLOOP research and by the existing chat validate-fix code. The MCP version is a straightforward extension. |
| RAG + fine-tuned model interaction | MEDIUM | The RAFT (retrieval-augmented fine-tuning) pattern is well-documented. But whether the 32B fine-tuned model actually benefits from RAG context depends on training quality -- untested. |
| Training data conversion pipeline | HIGH (design) | Markdown-to-ChatML conversion is a straightforward script. But the two repos are disconnected and the 9,922 existing examples lack metadata. |
| Continue.dev + Ollama integration | HIGH | Well-documented, multiple tutorials, actively maintained. Configuration is simple. FIM limitation is real but documented. |
| Copilot BYOK + Ollama | MEDIUM | Officially supported but reported as unstable. Chat-only limitation is verified. |
| Cursor + Ollama | MEDIUM | Works but requires network workarounds (ngrok or LAN-accessible Ollama). Not a native integration. |
| Deployment topology | HIGH | Standard pattern: one GPU server, Ollama, Docker Compose. No novel architecture. |
| 32B model feasibility on shared server | MEDIUM | Requires 24+ GB VRAM. Inference speed may be too slow for interactive use (10-30 tok/s). 7B fallback should be documented. |

---

## 10. Open Questions for Phase-Specific Research

1. **Does the QLoRA adapter from PEFT actually convert correctly to GGUF for Qwen2.5-Coder-32B?** This needs testing with the actual training output. If it fails, the fallback is merging the adapter into the base model weights before GGUF conversion.

2. **What is the actual inference latency of the 32B Q4 model via Ollama on the target hardware?** If >1 second per token, the generate_bbj_code tool will be too slow for interactive use and a 7B model should be trained instead.

3. **Does the fine-tuned model actually generate better BBj code than Claude + RAG?** This is the fundamental question. Without evaluation benchmarks, the entire fine-tuning investment is unvalidated.

4. **Should the training data include FIM (Fill-in-the-Middle) examples?** Required for Continue.dev inline completion. The current ChatML format only supports instruction/response pairs.

5. **How should the system handle Ollama model switching?** When both embedding model and code model are loaded, Ollama may need to swap models. With 24 GB VRAM, both can be resident. With less VRAM, there will be model loading latency.

---

## Sources

- [Ollama Import Documentation](https://docs.ollama.com/import) -- Modelfile ADAPTER instruction, supported architectures, GGUF conversion
- [Ollama Qwen2.5-Coder-32B](https://ollama.com/library/qwen2.5-coder:32b) -- Available quantization variants
- [Ollama GitHub Issue #8132](https://github.com/ollama/ollama/issues/8132) -- Fine-tuned Qwen2.5-Instruct import issues
- [llama.cpp convert_lora_to_gguf.py](https://github.com/ggml-org/llama.cpp/discussions/2948) -- PEFT adapter to GGUF conversion
- [GGUF-my-LoRA (HuggingFace)](https://huggingface.co/blog/ngxson/gguf-my-lora) -- LoRA to GGUF conversion tool
- [Continue.dev Ollama Guide](https://docs.continue.dev/guides/ollama-guide) -- Custom model configuration
- [Continue.dev Autocomplete Setup](https://docs.continue.dev/customize/deep-dives/autocomplete) -- Tab completion with local models, FIM requirements
- [GitHub Copilot BYOK Enhancements (Jan 2026)](https://github.blog/changelog/2026-01-15-github-copilot-bring-your-own-key-byok-enhancements/) -- Latest BYOK features
- [VS Code AI Language Models](https://code.visualstudio.com/docs/copilot/customization/language-models) -- BYOK configuration, Ollama provider
- [Copilot BYOK Ollama Discussion #186374](https://github.com/orgs/community/discussions/186374) -- Known compatibility issues
- [Support custom models for Copilot Code Completion #7690](https://github.com/microsoft/vscode-copilot-release/issues/7690) -- Inline completions not supported for BYOK
- [Cursor Ollama Integration Guide](https://thebizaihub.com/how-to-use-local-models-with-cursor-ai/) -- ngrok workaround, OpenAI override
- [LLMLOOP: Improving LLM-Generated Code (ICSME 2025)](https://valerio-terragni.github.io/assets/pdf/ravi-icsme-2025.pdf) -- Iterative compiler feedback loop research
- [Iterative Refinement with Compiler Feedback (arXiv)](https://arxiv.org/html/2403.16792v2) -- Generate-validate-fix pattern in research
- [AWS Guide: RAG, Fine-Tuning, and Hybrid Approaches](https://aws.amazon.com/blogs/machine-learning/tailoring-foundation-models-for-your-business-needs-a-comprehensive-guide-to-rag-fine-tuning-and-hybrid-approaches/) -- When to use RAG vs fine-tuning vs hybrid
- [vLLM vs Ollama Performance (Red Hat)](https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking) -- Inference server comparison
- [Ollama vs vLLM (Northflank)](https://northflank.com/blog/vllm-vs-ollama-and-how-to-run-them) -- Deployment comparison

---

*Research conducted 2026-02-06. External sources verified via WebSearch. Codebase analysis based on direct file reads of bbj-ai-strategy and bbjllm repositories. Confidence levels assigned per source hierarchy (Context7/official docs = HIGH, WebSearch verified = MEDIUM, WebSearch unverified = LOW).*
