---
sidebar_position: 7
title: "Implementation Roadmap"
description: "Progress summary and forward plan for the BBj AI strategy -- what has been delivered and what comes next."
---

# Implementation Roadmap

:::tip[TL;DR]
Seven milestones delivered. The language server, RAG knowledge system, MCP server, web chat,
documentation site, and compiler validation tooling are all operational. Fine-tuning research
has identified the path forward: Qwen2.5-Coder-14B-Base with evaluation via the BBj compiler
(compile@1). This chapter summarizes what exists and what comes next.
:::

The preceding chapters describe the technical blueprints for each component of the BBj AI
strategy. This chapter answers where things stand and what comes next -- a progress summary
organized by component status, followed by a grounded forward plan.

## Where We Stand

The original strategy paper (January 2025) proposed an architecture. Thirteen months later,
most of that architecture is operational. The table below compares the paper's starting point
with the current state.

| Component | Paper Status (Jan 2025) | Actual (Feb 2026) |
|-----------|------------------------|-------------------|
| Training data | Schema defined, no curated examples | 9,922 ChatML examples (bbjllm); 2 seed examples in training-data/ with JSON Schema validation |
| Base model | Candidates identified (CodeLlama, StarCoder2) | Qwen2.5-Coder-14B-Base recommended; bbjllm experiment validated Qwen2.5-Coder family |
| Language server | Architecture planned | v0.5.0 operational, 508 commits, 13 contributors, VS Code Marketplace |
| IDE integration | Not mentioned | Continue.dev evaluated as primary path; Copilot BYOK researched (chat only) |
| RAG database | Schema designed | Operational -- 7 parsers, 51K+ chunks, PostgreSQL + pgvector, hybrid retrieval |
| Documentation chat | Architecture planned | Operational -- Claude API + RAG, SSE streaming, source citations, auto BBj validation |
| MCP server | Not mentioned | Operational -- 2 tools (search_bbj_knowledge, validate_bbj_syntax), stdio + Streamable HTTP |
| Compiler validation | Not mentioned | Operational -- bbjcpltool v1 integrated into MCP server and web chat |
| Documentation site | Not mentioned | Operational -- Docusaurus site with 7 chapters covering full strategy |

## What We Built

The components below are organized by status tier -- operational systems first, then systems
running for internal exploration, then active research areas.

### Operational

**Language server** -- v0.5.0 with 508 commits and 13 contributors, available on the
VS Code Marketplace. Provides syntax highlighting, code completion, diagnostics, formatting,
and code execution across bbj-vscode and bbj-intellij extensions.
See [Chapter 4](/docs/ide-integration).

**Documentation site** -- Docusaurus 3.9.2 site with 7 chapters covering the full BBj AI
strategy, from problem statement through implementation roadmap.
See [Chapter 1](/docs/bbj-challenge).

**Compiler validation** -- bbjcpltool v1 validated and integrated into the MCP server
(validate_bbj_syntax tool) and web chat (automatic code validation with 3-attempt auto-fix).
Uses bbjcpl for ground-truth syntax checking.
See [Chapter 2](/docs/strategic-architecture).

### Operational for Internal Exploration

**RAG knowledge system** -- 7 source parsers ingesting 51K+ chunks into PostgreSQL + pgvector
with hybrid retrieval (dense vectors + BM25 + reciprocal rank fusion + cross-encoder reranking).
Accessible via REST API with search, stats, and health endpoints.
See [Chapter 6](/docs/rag-database).

**MCP server** -- 2 operational tools: search_bbj_knowledge (semantic search across the
documentation corpus) and validate_bbj_syntax (BBj compiler validation via bbjcpl). Available
via stdio and Streamable HTTP transports.
See [Chapter 2](/docs/strategic-architecture).

**Web chat** -- Available at /chat on the documentation site. Claude API backend with RAG
retrieval from the 51K+ chunk corpus, SSE streaming, source citations with clickable
documentation links, and automatic BBj code validation.
See [Chapter 5](/docs/documentation-chat).

### Active Research

**Fine-tuning** -- The bbjllm experiment fine-tuned Qwen2.5-Coder-32B-Instruct on 9,922
ChatML examples via QLoRA. Research recommends switching to Qwen2.5-Coder-14B-Base with
two-stage training (continued pretraining + instruction fine-tuning) and bbjcpl-based
compile@1 evaluation.
See [Chapter 3](/docs/fine-tuning).

## What Comes Next

The forward plan is organized by area. These are concrete next steps, not a phased rollout.

**Fine-tuning and evaluation:**

- Build a compile@1 benchmark using bbjcpl to measure whether generated BBj code compiles,
  with a held-out test set drawn from the training data.
- Add a validation set (10% holdout), implement completion masking to stop training on prompt
  tokens, and switch from the 32B-Instruct model to 14B-Base.
- Deduplicate approximately 375 entries and fix approximately 60 formatting issues in the
  bbjllm dataset.
- Implement two-stage training: continued pretraining on raw BBj source code followed by
  instruction fine-tuning on ChatML examples, using Unsloth 2026.1.4.
- Quantize the fine-tuned model to GGUF Q4_K_M format and serve via Ollama for local
  developer use.

**IDE integration:**

- Train a fill-in-the-middle (FIM) variant of the BBj model to support tab completion.
- Connect the fine-tuned model to Continue.dev for chat (instruction-tuned) and autocomplete
  (FIM-trained).
- Implement ghost text completions via InlineCompletionItemProvider in the language server
  extensions, using Langium semantic context to enrich LLM prompts.
- Extend the Langium parser with generation detection to identify which BBj generation the
  current code belongs to.
- Build a semantic context API within the language server that assembles scope, type, and
  generation information for LLM prompts.

**Infrastructure:**

- Add a generate_bbj_code tool to the MCP server once a fine-tuned model is operational,
  completing the generate-validate-fix loop.

:::note[Where Things Stand]
- **Operational:** Language server (v0.5.0, VS Code Marketplace), documentation site
  (7 chapters), compiler validation (bbjcpltool v1, integrated into MCP + chat)
- **Operational for internal exploration:** RAG knowledge system (51K+ chunks, hybrid
  retrieval), MCP server (2 tools, stdio + Streamable HTTP), web chat (Claude API + RAG,
  SSE streaming, source citations)
- **Active research:** Fine-tuning (14B-Base recommended, compile@1 evaluation designed,
  two-stage training approach)
- **Planned:** FIM training for tab completion, ghost text completions via
  InlineCompletionItemProvider, generate_bbj_code MCP tool
:::

The preceding chapters contain the technical detail behind each component:
[the BBj challenge](/docs/bbj-challenge), [strategic architecture](/docs/strategic-architecture),
[fine-tuning](/docs/fine-tuning), [IDE integration](/docs/ide-integration),
[documentation chat](/docs/documentation-chat), and [RAG database design](/docs/rag-database).
Together, these seven chapters form the complete BBj AI strategy -- from problem statement
through operational system and forward plan.
