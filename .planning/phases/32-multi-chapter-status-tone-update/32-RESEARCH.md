# Phase 32: Multi-Chapter Status & Tone Update - Research

**Researched:** 2026-02-06
**Domain:** Documentation content editing (Markdown/MDX status blocks and tone)
**Confidence:** HIGH

## Summary

This phase is a content editing task, not a software engineering task. The goal is to update the "Where Things Stand" status blocks and tone language across chapters 1, 2, 5, and 6 to accurately reflect the February 2026 state of the project. The primary challenge is not technical -- it is factual accuracy: understanding what is actually operational versus what the current docs claim.

Through direct investigation of the codebase and planning history, this research establishes the exact current state of every component mentioned in the target chapters. The key finding is a significant gap between what the docs say and reality. Several systems described as "planned" or "not yet built" are now fully operational (web chat, MCP server with 2 tools, full RAG corpus deployment). Meanwhile, the docs use language like "shipped" and "production-grade" that overstates the maturity level -- these are internal exploration tools, not production systems.

The research also catalogues every instance of problematic terminology ("shipped", "production", "deployed") across the four target chapters and identifies the specific text replacements needed. This gives the planner a concrete, line-by-line understanding of the scope.

**Primary recommendation:** Work through each chapter systematically, updating status blocks first, then doing a full-text tone pass to replace prohibited terms. Use the factual inventory below as the single source of truth for what to write.

## Standard Stack

This phase involves editing Markdown (.md) and MDX (.mdx) documentation files in a Docusaurus 3.9.2 site. No libraries, APIs, or code changes are involved.

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Docusaurus | 3.9.2 | Site framework | Existing project stack |
| Markdown/MDX | N/A | Content format | Existing content format |
| `npm run build` | N/A | Build verification | Ensures no broken links or syntax |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `bbjcpl -N` | Local install | BBj code validation | If any BBj code blocks are touched |

No new installations needed.

## Architecture Patterns

### File Locations

The four files to edit:

```
docs/
├── 01-bbj-challenge/index.mdx     # Chapter 1 (MDX - has React imports)
├── 02-strategic-architecture/index.md  # Chapter 2
├── 05-documentation-chat/index.md      # Chapter 5
└── 06-rag-database/index.md            # Chapter 6
```

### Pattern: Status Block Structure

All chapters use the same admonition pattern for status:

```markdown
:::note[Where Things Stand]
- **Item:** Description of current state
:::
```

Key decision from prior milestones: Status block dates were removed permanently (v1.3 decision). The blocks use `:::note[Where Things Stand]` with no month/year date in the block itself. The content inside should describe the February 2026 state.

### Pattern: Decision Callout Structure

Decision callouts follow a four-field format established in v1.3:

```markdown
:::info[Decision: Title]
**Choice:** What was decided
**Rationale:** Why
**Alternatives considered:** What else was evaluated
**Status:** Current state of the decision
:::
```

The **Status** field in decision callouts may also need tone updates (e.g., changing "Architecture defined. Model fine-tuning and RAG pipeline are in progress." to reflect actual state).

### Pattern: Chapter 1 is MDX

Chapter 1 (`index.mdx`) uses React components (Tabs, TabItem). The status block is at the bottom under `## Current Status`. Edit carefully -- MDX is sensitive to whitespace and JSX syntax.

## Factual Inventory: What Is Actually Operational

This is the single source of truth for the planner. All findings are HIGH confidence, verified by reading the actual codebase and planning history.

### RAG System

| Component | Status | Evidence |
|-----------|--------|----------|
| Ingestion pipeline | Operational for internal exploration | 7 parsers, Docker Compose deployment |
| Corpus size | 51,134 chunks (50,439 base + 695 JavaDoc) | v1.4 + v1.6 milestone data |
| Source groups | 7 groups: Flare (44,587), WordPress (2,950), Web Crawl (1,798), MDX (951), JavaDoc (695), BBj Source (106), PDF (47) | MILESTONES.md, validation reports |
| REST API | Operational: POST /search, GET /stats, GET /health | app.py, routes |
| Embedding model | Qwen3-Embedding-0.6B via Ollama (1024 dims) | config.toml, PROJECT.md |
| Database | PostgreSQL 17 + pgvector 0.8.0 via Docker Compose | docker-compose.yml |

### MCP Server

| Component | Status | Evidence |
|-----------|--------|----------|
| `search_bbj_knowledge` | Operational | mcp_server.py -- registered as FastMCP tool |
| `validate_bbj_syntax` | Operational | mcp_server.py -- calls bbjcpl via compiler.py |
| `generate_bbj_code` | Planned (not implemented) | Not in mcp_server.py; requires fine-tuned model |
| Transport: stdio | Operational | For Claude Desktop local use |
| Transport: Streamable HTTP | Operational | At /mcp endpoint, stateless_http=True |

### Web Chat

| Component | Status | Evidence |
|-----------|--------|----------|
| Chat endpoint | Operational at /chat | api/chat.py, chat.html template |
| LLM backend | Claude API (Anthropic SDK) | chat/stream.py uses AsyncAnthropic |
| Streaming | SSE via sse-starlette | chat/stream.py event generator |
| Source citations | Inline with clickable links | chat/stream.py sends sources event |
| BBj code validation | Automatic via bbjcpl in chat responses | chat/validation.py, 3-attempt auto-fix |
| Model used | claude-sonnet-4-5 (configurable) | config.py default |

### Fine-Tuned Model

| Component | Status | Evidence |
|-----------|--------|----------|
| bbjllm repo | Exists with 9,922 ChatML examples | STATE.md, research findings |
| Model trained | Qwen2.5-Coder-32B-Instruct (not 7B-Base) | Research findings |
| Training approach | QLoRA via PEFT (not Unsloth) | Research findings |
| Research recommendation | 14B-Base, two-stage training | Research SUMMARY.md |
| Operational BBj model | None -- no fine-tuned model deployed | No Ollama bbj-coder model exists |

### Compiler Validation

| Component | Status | Evidence |
|-----------|--------|----------|
| bbjcpltool v1 | Operational proof-of-concept | PROJECT.md |
| validate_bbj_syntax MCP tool | Operational | mcp_server.py |
| Chat code validation | Operational | chat/validation.py |

### Training Data Repository

| Component | Status | Evidence |
|-----------|--------|----------|
| training-data/ directory | Operational | 7 topic dirs, JSON Schema validation |
| Seed examples | 2 working examples | hello-window, keyed-file-read |
| Contributor docs | Complete | README, FORMAT, CONTRIBUTING guides |

## Current Status Blocks vs. Required State

### Chapter 1 (01-bbj-challenge/index.mdx) -- Lines 313-321

**Current text (WRONG):**
```
- **Shipped:** The bbj-language-server brings Langium-powered IDE features...
- **In progress:** A fine-tuned model based on Qwen2.5-Coder-7B...10,000 curated examples...
- **In progress:** Copilot BYOK integration is in early exploration...
- **Validated:** Testing with ChatGPT, Claude, and GitHub Copilot confirms...
- **webforJ AI tools operational:** The MCP server approach is working for webforJ...
```

**Required state:**
- bbj-language-server: operational (v0.5.0, VS Code Marketplace) -- use "operational" not "shipped"
- Fine-tuned model: active research, not yet operational -- bbjllm has 9,922 examples on 32B-Instruct, research recommends 14B-Base
- RAG system: operational for internal exploration (51K+ chunks, REST API, MCP server, web chat)
- Web chat: operational for internal exploration with Claude API + RAG
- MCP server: operational with search_bbj_knowledge and validate_bbj_syntax
- Copilot BYOK: still in early exploration
- Compiler validation: operational via MCP tool and chat integration

### Chapter 2 (02-strategic-architecture/index.md) -- Lines 364-385

**Current text (WRONG):**
```
- **Shipped:** bbj-language-server (v0.5.0)...
- **Shipped:** RAG ingestion pipeline (v1.2)...
- **Shipped:** bbjcpltool v1 proof-of-concept...
- **In progress:** Fine-tuned BBj model -- approximately 10,000 curated training examples on Qwen2.5-Coder-7B...
- **In progress:** MCP server architecture defined (v1.3)...
- **Planned:** MCP server implementation...
- **Planned:** Documentation chat...
```

Plus the status table (lines 376-384) uses terms like "shipped", "in progress", "planned" that are all outdated.

**Required state:**
- MCP server: operational (not "planned") with search_bbj_knowledge and validate_bbj_syntax
- RAG database: operational with 51K+ chunks (not "v1.2 awaiting deployment")
- Web chat: operational for internal exploration (not "planned")
- generate_bbj_code: planned (requires fine-tuned model)
- Fine-tuned BBj model: active research, bbjllm experiment underway
- bbj-language-server: operational (not "shipped")
- Compiler validation: operational (not just "proof-of-concept")

Also update decision callout Status fields in this chapter:
- "Architecture defined. Model fine-tuning and RAG pipeline are in progress." needs updating
- "Architecture defined. Three tool schemas specified." needs updating to reflect 2 tools operational

### Chapter 5 (05-documentation-chat/index.md) -- Lines 278-287

**Current text (VERY WRONG):**
```
- **Shipped:** Nothing. The documentation chat is a planned capability, not a shipped product.
- **Defined:** Two-path architecture...
- **Available upstream:** RAG ingestion pipeline (v1.2) shipped. Fine-tuned model in progress...
- **Planned:** Chat backend service, embedded chat component...
```

And the paragraph after the status block (line 285-287) says chat "cannot be implemented" until dependencies are operational.

**Required state:**
- Web chat: operational for internal exploration at /chat endpoint
- Architecture: Claude API + RAG retrieval + SSE streaming (NOT fine-tuned model)
- Source citations: operational with clickable documentation links
- BBj code validation: operational in chat responses with visual indicators
- MCP access path: operational via search_bbj_knowledge and validate_bbj_syntax
- generate_bbj_code: planned (not yet available)
- The chat uses Claude API, not the fine-tuned model -- this is a significant architectural difference from what was described

This chapter also needs CHAT-02 addressed: the architecture description throughout the chapter assumes a fine-tuned model backend (Ollama). The actual implementation uses Claude API + RAG. Key sections to update:
- TL;DR (line 10): references "fine-tuned model" and "generate_bbj_code"
- "The Shared Foundation" section (lines 43-53): describes generate_bbj_code as a primary capability
- "Path 2: Documentation Chat" (lines 65-69): describes using shared fine-tuned model
- Architectural Requirements (lines 252-264): requirement 1 says "must use fine-tuned model"
- "What Comes Next" section (lines 289-300): references dependencies that are now met

### Chapter 6 (06-rag-database/index.md) -- Lines 507-515

**Current text (WRONG):**
```
- **Shipped:** RAG ingestion pipeline (v1.2) -- 6 source parsers...awaiting deployment against production corpus.
- **Defined:** Source corpus identified...
- **Planned:** Retrieval exposed via MCP search_bbj_knowledge tool...
- **Planned next:** Deploy pipeline against production corpus...
```

**Required state:**
- RAG ingestion pipeline: operational for internal exploration (not "v1.2 awaiting deployment")
- Full corpus: deployed with 51,134 chunks across 7 source groups (including JavaDoc)
- 7 parsers (not 6): MadCap Flare, PDFs, WordPress/Advantage, WordPress/KB, Docusaurus MDX, BBj source code, JavaDoc JSON
- MCP search_bbj_knowledge: operational (not "planned")
- Hybrid retrieval: operational with source-balanced ranking
- Embedding model: Qwen3-Embedding-0.6B via Ollama (1024 dims)
- Database: PostgreSQL 17 + pgvector 0.8.0 via Docker Compose

Also update the source corpus table near the top (lines 21-29) which only lists 4 sources. The actual corpus has 7 source types.

## Prohibited and Required Terminology

### Prohibited Terms (STAT-02)

The following terms MUST NOT describe any component of this project:

| Prohibited | Why | Replace With |
|------------|-----|-------------|
| "production" | Nothing is in production | "operational for internal exploration" |
| "shipped" | Implies production release | "operational" or "available" |
| "deployed" (as final state) | Implies production deployment | "operational for internal exploration" |
| "production-grade" | Overstates maturity | Remove or say "functional" |
| "production corpus" | Misleading terminology | "full documentation corpus" |

### Required Terms

| Term | Use For |
|------|---------|
| "operational for internal exploration" | Running systems (RAG, chat, MCP server) |
| "operational" | Standalone tools (bbj-language-server, bbjcpltool) |
| "active research" | Fine-tuned model work |
| "planned" | generate_bbj_code, future capabilities |
| "under investigation" | Things being explored but not committed |

### Specific Replacements Needed

Across chapters 1, 2, 5, 6 the word "shipped" appears 14 times, "production" appears 8 times. Each instance needs individual attention -- some are in status blocks (primary target), some are in decision callout Status fields, some are in body text.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Finding all status blocks | Manual grep | Search for `:::note[Where Things Stand]` | Reliable pattern match |
| Verifying BBj code blocks | Manual checking | `bbjcpl -N` on any modified code blocks | Ground truth validation |
| Checking build integrity | Manual inspection | `npm run build` after edits | Catches broken links and syntax |
| Counting chunk totals | Re-running stats | Use 51,134 from planning docs | Already verified in v1.6 milestone |

**Key insight:** This is a content editing task. The "tools" are text search and the Docusaurus build system. Don't over-engineer the approach.

## Common Pitfalls

### Pitfall 1: Inconsistency Between Status Block and Body Text

**What goes wrong:** The status block is updated but body text still says the old thing. For example, updating the Ch5 status block to say "operational" but leaving paragraph text that says "The documentation chat is a planned capability, not a shipped product."
**Why it happens:** Status blocks are easy to find; scattered body text references are not.
**How to avoid:** After updating each status block, search the entire chapter file for each entity mentioned (e.g., "planned", "not yet built", "awaiting", "depends on") and verify consistency.
**Warning signs:** The word "planned" or "awaiting" appearing for something already operational.

### Pitfall 2: Over-Updating Chapters 3, 4, 7

**What goes wrong:** The implementer updates chapters that are out of scope for Phase 32. Chapters 3 (fine-tuning), 4 (IDE), and 7 (roadmap) are handled by Phases 33-35.
**Why it happens:** Status blocks in chapters 3, 4, and 7 also need updating, and the temptation is to fix them now.
**How to avoid:** Strictly limit edits to chapters 1, 2, 5, and 6. If issues are found in chapters 3/4/7, note them but do not fix them.
**Warning signs:** Opening files in docs/03-*, docs/04-*, or docs/07-* for editing.

### Pitfall 3: MDX Syntax Breakage in Chapter 1

**What goes wrong:** Editing the MDX file breaks JSX syntax (unclosed tags, wrong whitespace near imports).
**Why it happens:** Chapter 1 is `.mdx` with React component imports (Tabs, TabItem). MDX is stricter than plain Markdown.
**How to avoid:** Only edit the status block section at the bottom of the file (lines 313-321). Run `npm run build` after changes. Do not add or modify any JSX elements.
**Warning signs:** Build errors mentioning "JSX" or "unexpected token" in index.mdx.

### Pitfall 4: Changing Architecture Descriptions Instead of Status

**What goes wrong:** The implementer rewrites architectural descriptions (e.g., removing references to generate_bbj_code throughout Chapter 5) instead of just updating status and tone.
**Why it happens:** Chapter 5 describes an architecture that assumed a fine-tuned model backend, but the actual implementation uses Claude API. It feels wrong to leave the architecture description unchanged.
**How to avoid:** For Phase 32, focus on status blocks and tone. The CHAT-02 requirement says "Architecture updated to reflect actual implementation" -- this means updating descriptions of what the chat system IS (Claude API + RAG), not rewriting the aspirational architecture. Update the sections that describe current implementation, leave forward-looking architecture sections that describe the eventual vision.
**Warning signs:** Deleting or rewriting entire sections about generate_bbj_code or fine-tuned model integration.

### Pitfall 5: Forgetting Decision Callout Status Fields

**What goes wrong:** Status blocks are updated but the `**Status:**` line inside `:::info[Decision: ...]` callouts still says outdated things like "Architecture defined. MCP server implementation planned."
**Why it happens:** Decision callouts look immutable -- they document past decisions. But the Status field is meant to reflect current state.
**How to avoid:** Search each chapter for `**Status:**` within `:::info` blocks and verify accuracy.
**Warning signs:** A Status field saying "planned" for something operational.

### Pitfall 6: Wrong Chunk Count

**What goes wrong:** Using 50,439 (pre-JavaDoc) instead of 51,134 (post-JavaDoc) or using a rounded "50K+" when "51K+" is correct.
**Why it happens:** Multiple sources in the planning docs cite different numbers from different milestones.
**How to avoid:** Use 51K+ as the consistent round number. The exact count is 50,439 + 695 = 51,134.
**Warning signs:** Any chapter saying "50,000 chunks" or "50K chunks" -- it should be "51K+ chunks".

## Code Examples

### Finding Status Blocks

```bash
# Find all Where Things Stand blocks
grep -n "Where Things Stand" docs/*/index.md docs/*/index.mdx
```

### Finding Prohibited Terms

```bash
# Find "shipped", "production", "deployed" across target chapters
grep -n -i '"shipped"\|"production"\|"deployed"' \
  docs/01-bbj-challenge/index.mdx \
  docs/02-strategic-architecture/index.md \
  docs/05-documentation-chat/index.md \
  docs/06-rag-database/index.md
```

### Verifying Build After Changes

```bash
cd /Users/beff/_workspace/bbj-ai-strategy
npm run build
```

## State of the Art

| Old State (in current docs) | Actual State (Feb 2026) | Impact on Editing |
|-------|---------|---------|
| RAG v1.2, awaiting production corpus | 51K+ chunks operational, 7 parsers | Major status block rewrite needed |
| MCP server planned | 2 tools operational (search + validate) | Remove "planned" language |
| Documentation chat: nothing shipped | Web chat operational with Claude API | Biggest single status change |
| Fine-tuned model in progress (~10K examples) | bbjllm has 9,922 on 32B-Instruct; research recommends 14B-Base | Complex -- research recommends changes vs actual state |
| 6 source parsers | 7 source parsers (added JavaDoc) | Update corpus description |
| Chat uses fine-tuned model | Chat uses Claude API + RAG | Architectural shift to document |

## Chapter-by-Chapter Edit Scope

### Chapter 1 (The BBj Challenge)

**Sections to edit:**
1. `## Current Status` block (lines 312-321) -- complete rewrite
2. No body text changes needed -- the chapter's technical content about BBj generations is still accurate

**Scope:** Small. One status block rewrite.

### Chapter 2 (Strategic Architecture)

**Sections to edit:**
1. `## Current Status` block (lines 364-374) -- complete rewrite
2. Status table (lines 376-385) -- complete rewrite
3. Decision callout Status fields (search for `**Status:**` in :::info blocks) -- verify and update
4. Body text mentioning "in progress" or "planned" for now-operational components
5. TL;DR might need minor tone adjustment

**Scope:** Medium. Status block + table + scattered body text.

### Chapter 5 (Documentation Chat)

**Sections to edit:**
1. `## Current Status` block (lines 278-283) -- complete rewrite
2. Post-status paragraph (lines 285-287) -- rewrite to reflect operational state
3. TL;DR (line 10) -- update to reflect Claude API + RAG, not fine-tuned model
4. "The Shared Foundation" section (lines 43-53) -- update to reflect actual implementation
5. "Path 2: Documentation Chat" intro (lines 65-69) -- update
6. Architectural Requirements section (lines 252-264) -- update requirement 1 re: model
7. "What Comes Next" section (lines 289-300) -- update dependencies that are now met
8. Decision callout Status fields

**Scope:** Large. This chapter has the biggest gap between current text and reality. The status block, multiple body text sections, and the architectural description all need updating to reflect Claude API + RAG instead of fine-tuned model.

### Chapter 6 (RAG Database Design)

**Sections to edit:**
1. `## Current Status` block (lines 507-513) -- complete rewrite
2. Post-status paragraph (lines 515) -- update
3. Source Corpus table (lines 21-29) -- add JavaDoc source, update to 7 sources
4. Source Corpus intro paragraph -- update volume info
5. Decision callout Status fields
6. Body text mentioning "planned" or "awaiting" for now-operational things

**Scope:** Medium. Status block + source corpus section + scattered body text.

## Open Questions

1. **Exact chunk count precision**
   - What we know: 50,439 (pre-JavaDoc) + 695 (JavaDoc) = 51,134
   - What's unclear: Has there been any re-ingestion since v1.6 that changed the count?
   - Recommendation: Use "51K+" as the round number in all chapters. This is safe and consistent.

2. **How much Chapter 5 architecture rewriting is in scope?**
   - What we know: CHAT-02 says "Architecture updated to reflect actual implementation (Claude API + RAG, not fine-tuned model)"
   - What's unclear: Does this mean rewriting the aspirational architecture sections, or just updating status/current-state sections?
   - Recommendation: Update descriptions of what IS to match reality (Claude API + RAG). Keep forward-looking architecture that describes the eventual vision (fine-tuned model) but mark it clearly as future/planned. The key principle: a reader should understand what is operational TODAY vs. what is planned.

3. **Should references to "v1.2" in status blocks be removed?**
   - What we know: The RAG pipeline has gone through v1.2, v1.4, v1.5, v1.6 internally
   - What's unclear: Whether to cite a version number at all
   - Recommendation: Don't cite version numbers in status blocks. Just describe what exists. Version numbers are internal planning artifacts.

## Sources

### Primary (HIGH confidence)

- Direct codebase inspection: `rag-ingestion/src/bbj_rag/mcp_server.py` -- confirmed 2 MCP tools operational
- Direct codebase inspection: `rag-ingestion/src/bbj_rag/api/chat.py` -- confirmed chat endpoint operational
- Direct codebase inspection: `rag-ingestion/src/bbj_rag/chat/stream.py` -- confirmed Claude API (AsyncAnthropic) backend
- Direct codebase inspection: `rag-ingestion/src/bbj_rag/compiler.py` -- confirmed validate_bbj_syntax operational
- `.planning/MILESTONES.md` -- v1.4 (50,439 chunks), v1.5 (chat, remote MCP, compiler validation), v1.6 (695 JavaDoc chunks)
- `.planning/PROJECT.md` -- full project history and validated requirements
- `.planning/STATE.md` -- current project position
- `.planning/REQUIREMENTS.md` -- v1.7 requirements (STAT-01 through CHAT-02)

### Secondary (MEDIUM confidence)

- None needed -- all findings from primary sources

### Tertiary (LOW confidence)

- None

## Metadata

**Confidence breakdown:**
- Factual inventory: HIGH -- all verified by direct codebase inspection
- Edit scope identification: HIGH -- all status blocks and body text catalogued
- Tone guidelines: HIGH -- requirements are explicit and unambiguous
- Architecture change scope for Ch5: MEDIUM -- CHAT-02 requirement is clear but editorial judgment needed

**Research date:** 2026-02-06
**Valid until:** 2026-03-06 (content editing task; findings stable unless codebase changes)
