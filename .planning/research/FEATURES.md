# Feature Landscape: v1.5 Alpha-Ready RAG System

**Domain:** RAG chat system with compiler validation for alpha engineer review
**Researched:** 2026-02-03
**Overall confidence:** HIGH (Claude API docs verified, codebase analyzed, MCP transport patterns confirmed)
**Supersedes:** Previous FEATURES.md covered v1.4 Docker deployment. That milestone shipped. This document covers features needed to make the RAG system useful for alpha testers: web chat, Claude API integration, compiler validation, remote access, concurrent ingestion, and source-balanced ranking.

---

## Research Context

### What Already Exists (v1.4 Shipped)

| Component | Current State |
|-----------|--------------|
| REST API | POST /search (hybrid RRF), GET /stats, GET /health -- FastAPI with async psycopg3 pool |
| MCP server | `search_bbj_knowledge` tool via stdio, proxies to REST API |
| Search | Dense vector + BM25 hybrid with RRF fusion, generation filtering |
| Corpus | 50,439 chunks: Flare (88.4%), WordPress (5.8%), Web Crawl (3.6%), MDX (1.9%), BBj Source (0.21%), PDF (0.09%) |
| Docker | pgvector + Python app, Ollama on host, schema auto-init |
| Validation | 17-query E2E suite, 13/17 passing (4 failures due to corpus imbalance, not pipeline bugs) |

### What v1.5 Adds

Six feature areas, each addressing a specific gap between "pipeline works" and "engineers will use this":

1. **Web chat interface** -- Engineers need a browser-based way to ask questions and see grounded answers
2. **Claude API integration** -- Turn retrieved chunks into coherent answers with source citations
3. **bbjcpl compiler validation** -- Validate BBj code in responses to build trust
4. **Remote/shared deployment** -- Team members access a single shared instance on the network
5. **Concurrent ingestion** -- Faster rebuilds when corpus changes
6. **Source-balanced ranking + clickable links** -- Surface minority sources; make source URLs navigable

### The Trust Thesis

The central insight driving v1.5 priorities: engineers must TRUST the system before they adopt it. Three features directly address trust:
- **Source citations** prove answers come from real documentation, not hallucination
- **Compiler validation** proves BBj code is syntactically correct
- **Clickable source links** let engineers verify claims against the original docs

Everything else (remote access, ingestion speed, ranking) is infrastructure that makes the trust-building features accessible.

---

## Table Stakes

Features engineers expect from an alpha RAG chat. Missing any of these means the alpha test produces no useful feedback.

### TS-1: Web Chat Interface

| Aspect | Details |
|--------|---------|
| **Feature** | Browser-accessible chat page where engineers type questions and receive RAG-grounded answers |
| **Why Expected** | Engineers cannot evaluate retrieval quality through raw API calls. They need a conversational interface to ask natural questions. MCP via Claude Desktop is available but requires per-user setup; a web chat is zero-setup for alpha testers. |
| **Complexity** | Medium |
| **Depends On** | REST API (exists), Claude API integration (TS-2) |

**What engineers expect from an alpha chat UI:**
- Text input field, send button, response area -- minimal but functional
- Streaming response display (text appears as it generates, not after a long wait)
- Source citations visible with each answer (not hidden in a debug panel)
- BBj code blocks rendered with syntax highlighting or at minimum monospace formatting
- Works in a standard browser -- no install, no build step, no npm

**What engineers do NOT expect from an alpha:**
- Conversation history persistence across sessions
- User accounts or personalization
- Mobile-optimized layout
- Dark mode toggle
- File upload or multi-modal input

**Implementation approach:** Serve a single HTML page from the existing FastAPI app. Use server-sent events (SSE) or WebSocket for streaming. The frontend can be a single HTML file with inline JavaScript -- no React, no build toolchain. htmx or vanilla JS are both viable for this scope. The key is zero deployment overhead: `docker compose up` serves both the API and the chat page.

**Confidence: HIGH** -- FastAPI natively supports WebSocket and SSE. Multiple RAG chat implementations follow this exact pattern (FastAPI backend + minimal HTML frontend). The existing app already serves HTTP.

### TS-2: Claude API Integration for Answer Generation

| Aspect | Details |
|--------|---------|
| **Feature** | Use Claude API (Anthropic Python SDK) to synthesize retrieved chunks into coherent, cited answers |
| **Why Expected** | The existing system returns raw chunks. Engineers want answers, not a list of documentation fragments. The leap from "retrieval" to "answer" is what makes this useful vs just searching the docs site directly. |
| **Complexity** | Medium |
| **Depends On** | REST API /search (exists), Anthropic API key (required) |

**Critical finding: Claude's Search Result Content Blocks**

The Claude API provides a purpose-built feature for RAG citation: **search result content blocks**. This is the recommended approach for this project, verified against official Anthropic documentation (GA, no beta header required).

How it works:
1. Retrieve chunks from the existing /search endpoint
2. Format each chunk as a `SearchResultBlockParam` with `source`, `title`, `content`, and `citations: {"enabled": True}`
3. Send to Claude Messages API along with the user's question
4. Claude automatically generates cited responses -- each claim links back to a specific search result

The response structure includes `search_result_location` citations with `source`, `title`, `cited_text`, and `search_result_index`. This eliminates the need to prompt-engineer citations or build custom citation parsing.

**Streaming support:** The Claude API supports streaming via SSE (`client.messages.stream()`). The Python SDK provides `stream.text_stream` for text and `citations_delta` events for streaming citations. This enables real-time response display in the chat UI.

**Model selection for alpha:** Use `claude-sonnet-4-5` (or `claude-haiku-4-5` for cost-sensitive testing). Sonnet provides good quality/speed balance. Extended thinking is unnecessary for document Q&A at alpha stage.

**System prompt:** Include BBj context: "You are a BBj programming assistant. Answer questions using ONLY the provided documentation sources. BBj is Business BASIC for Java by BASIS International. Always cite your sources."

**Token economics for alpha:** With 5-10 search results (each ~400 tokens = ~4,000 input tokens of context) plus system prompt and question, each query costs roughly 5K-8K input tokens + 500-2K output tokens. At Sonnet 4.5 pricing, this is approximately $0.02-0.04 per query. For an alpha with 5-10 engineers doing 20-50 queries/day, monthly cost would be $10-60. Acceptable for alpha.

**Confidence: HIGH** -- Verified against official Claude API documentation at platform.claude.com/docs/en/build-with-claude/search-results. Search result content blocks are GA. Streaming support confirmed.

### TS-3: Source Citations Displayed in Chat

| Aspect | Details |
|--------|---------|
| **Feature** | Each answer shows which documentation sources were used, with enough context to verify |
| **Why Expected** | Without citations, the chat is just "Claude said so." With citations, engineers can verify claims against the docs they know. This is the primary trust mechanism. |
| **Complexity** | Low (rendering) -- Medium (if building clickable links, see D-2) |
| **Depends On** | Claude API integration (TS-2), source URL mapping (D-2) |

**What citation display should look like:**
- Each answer segment shows its source inline or as footnotes
- Source title and URL are visible
- Engineers can click through to the original documentation (when URLs are mapped, see D-2)
- The citation format matches what engineers see in the Claude API response: `cited_text` from `source` with `title`

**Rendering approach:** Parse the Claude API response content blocks. When a text block has `citations`, render the cited text with a superscript or inline reference. Collect unique sources into a "Sources" section at the bottom of each answer. Each source shows title + URL.

**Confidence: HIGH** -- The Claude API response format is well-documented. Citation rendering is a frontend concern with straightforward implementation.

### TS-4: Streaming Response Display

| Aspect | Details |
|--------|---------|
| **Feature** | Answers stream to the browser as they are generated, not delivered as one block after completion |
| **Why Expected** | Claude API calls with RAG context take 3-10 seconds. Without streaming, the UI appears frozen. Engineers will assume it is broken and close the tab. Streaming provides immediate feedback that the system is working. |
| **Complexity** | Medium |
| **Depends On** | Claude API streaming (TS-2), WebSocket or SSE transport |

**Implementation pattern:**
1. Chat endpoint receives user question via WebSocket or POST
2. Backend calls /search to get RAG chunks (fast, <1s)
3. Backend calls Claude API with `client.messages.stream()` passing search result blocks
4. Backend forwards `text_delta` events to the browser in real-time via SSE or WebSocket
5. Frontend appends text as it arrives, rendering markdown/code blocks incrementally
6. `citations_delta` events are accumulated and rendered after each content block completes

**SSE vs WebSocket decision:** SSE is simpler (unidirectional, built into browsers, works with FastAPI's `StreamingResponse`). WebSocket is bidirectional but adds complexity. For a single-turn Q&A chat without conversation state, SSE is sufficient. Use SSE.

**Confidence: HIGH** -- Claude streaming + FastAPI SSE is a well-established pattern. The Python SDK's `stream.text_stream` iterator maps directly to SSE event generation.

---

## Differentiators

Features that make this alpha compelling vs "just ask Claude without RAG." These are what make the system worth evaluating.

### D-1: bbjcpl Compiler Validation of BBj Code

| Aspect | Details |
|--------|---------|
| **Feature** | Automatically validate BBj code blocks in RAG responses using the bbjcpl compiler |
| **Value Proposition** | This is the unique differentiator. No other tool validates BBj code for syntactic correctness. LLMs hallucinate BBj syntax. Compiler validation catches this. Engineers trust code that compiles. |
| **Complexity** | Medium-High |
| **Depends On** | bbjcpl binary accessible from server, BBj code extraction from Claude response |

**How it should work:**
1. Claude generates an answer containing BBj code blocks (fenced with \`\`\`bbj)
2. Backend extracts code blocks from the response
3. Each code block is written to a temp file and validated with `bbjcpl -N <file>` (syntax-only, no execution)
4. Validation results are attached to the code block in the response

**Validated vs unvalidated code presentation:**

| Status | Visual Indicator | Behavior |
|--------|-----------------|----------|
| Validated (passes) | Green checkmark or "Compiler validated" badge | Code shown normally with confidence indicator |
| Validated (fails) | Yellow warning with compiler error message | Code shown with warning: "Compiler found syntax error: [message]" |
| Not validated | Gray "Not validated" label | Code not identified as BBj, or bbjcpl not available |

**When validation fails:** Show the code AND the error. Do not suppress the code. Engineers can learn from the error and may recognize the intent. The error message from bbjcpl is often specific enough to guide correction. The chat could optionally suggest "Try asking Claude to fix this code based on the compiler error."

**Architecture consideration:** bbjcpl runs as a subprocess. On a shared server, BBj must be installed (or just the compiler binary available). Alpha testers at BASIS have BBj installed locally, so for a self-hosted server on the BASIS network, this is available. For non-BBj environments, validation should gracefully degrade to "Not validated."

**Existing prior art:** The bbjcpltool proof-of-concept at `/Users/beff/bbjcpltool/` already implements the PostToolUse hook pattern for Claude Code. The v1.5 compiler integration follows the same principle but runs server-side during answer generation.

**Performance:** `bbjcpl -N` is fast (typically <100ms per file). Even with 3-5 code blocks per response, validation adds <500ms total. This is acceptable during streaming -- validate after the full response is assembled.

**Confidence: MEDIUM** -- The bbjcpl compiler pattern is proven (bbjcpltool v1 works). The integration with streaming responses and temp file management in Docker adds complexity. The main risk is whether bbjcpl is available in the Docker container or needs to run on the host.

### D-2: Clickable Source Links (source_url Mapping)

| Aspect | Details |
|--------|---------|
| **Feature** | Map internal source_url values (flare://, pdf://, mdx-*//, file://) to clickable HTTP URLs |
| **Value Proposition** | Engineers can click to verify any claim in the original documentation. Closes the trust loop: "Claude said X, source is Y, I can read Y myself." |
| **Complexity** | Low-Medium |
| **Depends On** | Source URL patterns (exist in DB), target URL mappings |

**Current source_url patterns and target mappings:**

| Pattern | Example | Maps To | Mapping Approach |
|---------|---------|---------|-----------------|
| `flare://Content/path.htm` | `flare://Content/bbjobjects/Window/bbjwindow.htm` | `https://documentation.basis.cloud/path.htm` | Replace `flare://Content/` with `https://documentation.basis.cloud/` |
| `https://basis.cloud/*` | `https://basis.cloud/advantage/article-slug` | Same URL (already HTTP) | Pass through |
| `https://documentation.basis.cloud/*` | `https://documentation.basis.cloud/topic.htm` | Same URL (already HTTP) | Pass through |
| `mdx-dwc://path` | `mdx-dwc://docs/getting-started.md` | Depends on whether MDX tutorials are deployed | Requires mapping table or "not linkable" |
| `mdx-beginner://path` | `mdx-beginner://docs/intro.md` | Depends on deployment | Same as above |
| `pdf://filename#section` | `pdf://GuideToGuiProgrammingInBBj.pdf#chapter-1` | Not directly linkable (local PDF) | Show "PDF: [title]" without link, or link to documentation.basis.cloud if available |
| `file://path.bbj` | `file://samples/hello.bbj` | Not HTTP-accessible | Show "Source code: [filename]" without link |

**Key insight:** The two largest clickable sources (Flare at 88.4% and WordPress at 5.8%) already have straightforward HTTP mappings. Web Crawl URLs (3.6%) are already HTTP. This covers 97.8% of the corpus. The remaining 2.2% (MDX, BBj Source, PDF) can display as "local source" without clickable links for alpha.

**Implementation:** Add a `resolve_source_url(source_url: str) -> str | None` function that returns an HTTP URL or None. The chat UI renders URLs as clickable links when not None, and as plain text labels when None.

**Confidence: HIGH** -- The flare:// to documentation.basis.cloud mapping is the critical one and is straightforward string substitution. Other HTTP sources pass through. Edge cases (MDX, PDF, file://) gracefully degrade.

### D-3: Source-Balanced Ranking

| Aspect | Details |
|--------|---------|
| **Feature** | Boost minority sources (PDF, BBj Source, MDX) in search results so they appear alongside the dominant Flare corpus |
| **Value Proposition** | The E2E validation proved that PDF (0.09%) and BBj Source (0.21%) never appear in top-5 results despite having relevant content. Engineers need to see results from ALL sources to trust that the system indexes everything. |
| **Complexity** | Medium |
| **Depends On** | Search module (exists), corpus statistics (exists via /stats) |

**The imbalance problem:**
- Flare: 44,587 chunks (88.4%) -- dominates every query
- WordPress: 2,950 chunks (5.8%) -- sometimes appears
- Web Crawl: 1,798 chunks (3.6%) -- sometimes appears
- MDX: 951 chunks (1.9%) -- rarely appears
- BBj Source: 106 chunks (0.21%) -- never appears in top-5
- PDF: 47 chunks (0.09%) -- never appears in top-5

**Approach options:**

1. **Source diversity slot reservation** (recommended for alpha): Reserve 1-2 of the top-N result slots for non-Flare sources. If the top-5 are all Flare, replace positions 4-5 with the highest-scoring non-Flare results. Simple, predictable, easy to explain to testers.

2. **Source-weighted RRF boost**: Multiply RRF scores by a source-weight factor inversely proportional to corpus fraction. PDF chunks get a higher weight than Flare chunks. More principled but harder to tune and explain.

3. **Post-retrieval re-ranking with diversity constraint**: Retrieve top-20, then re-rank with a diversity constraint (maximum 3 results from any single source group). Most sophisticated but over-engineered for alpha.

**Recommendation:** Use option 1 (slot reservation) for alpha. It is transparent ("We always show at least one non-Flare result when available"), easy to implement (post-processing on the result list), and easy to remove if it turns out to be unhelpful.

**How it interacts with Claude API:** Source-balanced results feed into the Claude API as search result blocks. Claude sees a diverse set of sources and can synthesize information from multiple perspectives. This is strictly better than feeding 5 Flare chunks that may all say the same thing.

**Confidence: MEDIUM** -- The slot reservation approach is straightforward to implement. The risk is that forced diversity may surface irrelevant results from minority sources. This needs alpha tester feedback to calibrate.

### D-4: Remote/Shared Server Access

| Aspect | Details |
|--------|---------|
| **Feature** | Deploy the RAG system on a shared server that team members can access via browser (chat) and Claude Desktop (MCP) |
| **Value Proposition** | Without shared access, each engineer must run Docker locally with 50K chunks + Ollama. That is a significant setup barrier. A shared server means zero-setup access for alpha testers. |
| **Complexity** | Medium |
| **Depends On** | Docker deployment (exists), network accessibility |

**What engineers need for browser access:**
- HTTP URL to the chat interface (e.g., `http://rag-server.local:10800/chat`)
- No authentication for alpha (trusted internal network)
- Works from any machine on the local network

**What engineers need for Claude Desktop MCP access:**

Claude Desktop supports remote MCP servers via Streamable HTTP transport. Two approaches:

**Approach A: Native Streamable HTTP** (if Claude Desktop supports it natively)
The MCP server adds Streamable HTTP transport alongside stdio. Claude Desktop connects directly:
```json
{
  "mcpServers": {
    "bbj-knowledge": {
      "type": "http",
      "url": "http://rag-server.local:10800/mcp"
    }
  }
}
```

**Approach B: mcp-remote bridge** (fallback if native HTTP not available for all users)
Use the `mcp-remote` npm package as a bridge:
```json
{
  "mcpServers": {
    "bbj-knowledge": {
      "command": "npx",
      "args": ["mcp-remote", "http://rag-server.local:10800/mcp"]
    }
  }
}
```

**Current MCP server architecture:** The existing `mcp_server.py` proxies to the REST API via httpx. This is already transport-agnostic -- the MCP server just needs to add HTTP transport alongside stdio. The MCP Python SDK supports both: `mcp.run(transport="streamable-http")` as an alternative to `mcp.run(transport="stdio")`. Select via environment variable.

**Server deployment:** The Docker Compose stack already runs on the host. For shared access, bind the app to `0.0.0.0` (already configured: `uvicorn ... --host 0.0.0.0`) and ensure the firewall allows port 10800. No additional infrastructure needed for local network alpha.

**Confidence: HIGH** for browser access (HTTP is straightforward on LAN). **MEDIUM** for MCP remote access (Claude Desktop's Streamable HTTP support is confirmed for Pro/Max/Team/Enterprise plans; the mcp-remote fallback works but adds a Node.js dependency).

### D-5: Concurrent Ingestion Workers

| Aspect | Details |
|--------|---------|
| **Feature** | Parallelize embedding generation across multiple concurrent workers for faster corpus rebuilds |
| **Value Proposition** | Current sequential ingestion of 50,439 chunks takes considerable time. Concurrent embedding can reduce this significantly, enabling faster iteration when sources change. |
| **Complexity** | Medium |
| **Depends On** | Pipeline module (exists), Ollama concurrent request support |

**Current bottleneck:** The pipeline processes batches of 64 chunks sequentially. Each batch calls `embedder.embed_batch(texts)` which sends a single request to Ollama. The embedding call is I/O-bound (waiting for Ollama to respond), meaning the pipeline spends most of its time waiting.

**Ollama concurrency support:** Ollama supports concurrent requests since v0.2 (default `OLLAMA_NUM_PARALLEL=4`). The embedding model (Qwen3-Embedding-0.6B) is small enough that 4 parallel requests use minimal additional memory.

**Implementation pattern:**
```
# Conceptual: replace sequential batch processing with concurrent
semaphore = asyncio.Semaphore(4)  # match OLLAMA_NUM_PARALLEL

async def embed_batch_async(batch):
    async with semaphore:
        return await ollama_client.embed(model=model, input=batch)

# Process multiple batches concurrently
tasks = [embed_batch_async(batch) for batch in batches]
results = await asyncio.gather(*tasks)
```

**Expected speedup:** With 4 concurrent workers and Ollama's built-in parallelism, expect 2-3x speedup on embedding time. The bottleneck shifts from I/O wait to Ollama GPU throughput. On Apple Silicon with Metal, the 0.6B embedding model can handle 4 parallel requests efficiently.

**Also: HTTP connection reuse.** The current `embedder.py` uses `ollama.embed()` which creates a new HTTP connection per call. Using a persistent `httpx.Client` with connection pooling eliminates TCP handshake overhead for each batch. This alone may provide 10-20% speedup independent of concurrency.

**Note:** The `--parallel` flag already exists in `ingest_all.py` but currently prints a warning and falls back to sequential. v1.5 would implement it.

**Confidence: MEDIUM** -- The asyncio.Semaphore pattern is well-established. The main uncertainty is whether the existing synchronous pipeline can be converted to async without a major rewrite, or whether `ThreadPoolExecutor` is more practical for wrapping the synchronous embedder.

---

## Anti-Features

Features to deliberately NOT build for v1.5 alpha. Each would add complexity without matching the milestone goal of "engineers can evaluate whether the RAG system provides useful, accurate BBj documentation retrieval."

### Conversation Memory / Multi-Turn Context

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Chat history persistence** | Alpha is for evaluating retrieval quality, not building a production chat product. Conversation memory adds state management, session handling, and context window management. | Each query is independent. Stateless. If an engineer wants to refine a question, they retype it. PROJECT.md explicitly excludes chat history persistence. |

### User Accounts / Authentication

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Login, API keys, user management** | Internal alpha on trusted network. Auth adds setup friction that discourages alpha participation. | No auth. Anyone on the network can access. If the server hosts an Anthropic API key, that key serves all users. Monitor usage via /stats endpoint. |

### Agentic RAG (Query Routing, Multi-Step)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Query rewriting, follow-up retrieval, tool chains** | Agentic patterns are complex to build and debug. Alpha testers need to evaluate baseline retrieval quality first. Agentic features mask retrieval problems by working around them. | Single-step retrieval: one query, one search, one answer. If retrieval quality is poor, we will know because the answer is poor. That is the point of alpha testing. |

### Custom Embedding Model / Fine-Tuning

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Training a BBj-specific embedding model** | Requires labeled data (which the alpha will help generate), training infrastructure, and evaluation methodology. All prerequisites for fine-tuning, not the fine-tuning itself. | Use the existing Qwen3-Embedding-0.6B. Collect quality feedback from alpha testers to build future training data. |

### Production Deployment Infrastructure

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **HTTPS, reverse proxy, cloud hosting, monitoring, alerting** | Alpha runs on local network for 5-10 engineers. Production infrastructure is premature. | Plain HTTP on LAN. Docker Compose on a shared workstation or server. Manual monitoring via /health and /stats endpoints. |

### Polished UI / Design System

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Custom CSS framework, animations, responsive design, accessibility audit** | Engineers evaluate retrieval quality through the UI, they do not evaluate the UI itself. Time spent on UI polish is time not spent on retrieval quality. | Minimal functional UI. Clean typography, readable code blocks, visible citations. A single HTML file with 200 lines of CSS is sufficient for alpha. |

### Answer Rating / Feedback System

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Thumbs up/down, star ratings, comment fields** | Feedback collection infrastructure adds complexity. Alpha testers can provide feedback verbally or via email/Slack. A formal feedback system is premature. | Ask alpha testers to note good/bad answers in a shared document or Slack channel. Structured feedback collection comes after alpha proves the concept. |

### generate_bbj_code MCP Tool

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **MCP tool that generates BBj code via fine-tuned model** | Fine-tuned BBj model does not exist yet. This tool requires a separate milestone. PROJECT.md explicitly defers this. | Rely on Claude's code generation grounded by RAG context. Compiler validation (D-1) checks the output. The RAG system provides the knowledge; Claude provides the generation. |

---

## Feature Dependencies

### Dependency Graph

```
Docker Compose + Network Access (exists)
  |
  +--> REST API /search (exists)
  |     |
  |     +--> Claude API Integration (TS-2)
  |     |     |
  |     |     +--> Source Citations (TS-3)
  |     |     +--> Streaming Response (TS-4)
  |     |     +--> bbjcpl Validation (D-1) [post-generation]
  |     |     |
  |     |     +--> Web Chat Interface (TS-1) [requires all above]
  |     |
  |     +--> Source-Balanced Ranking (D-3) [modifies search results before Claude]
  |     |
  |     +--> Source URL Mapping (D-2) [transforms URLs in results]
  |
  +--> MCP Server + Streamable HTTP (D-4) [parallel to chat, shares REST API]
  |
  +--> Concurrent Ingestion (D-5) [independent, modifies pipeline only]
```

### Critical Path for Alpha Testing

The shortest path to "an engineer can open a browser and ask a BBj question":

1. **Claude API integration** (TS-2) -- without this, no answer generation
2. **Streaming response** (TS-4) -- without this, UI feels broken on 3-10s waits
3. **Web chat interface** (TS-1) -- the actual UI
4. **Source citations** (TS-3) -- trust mechanism, renders citation data from TS-2

These four features form the minimum viable alpha. Everything else enhances quality but is not required for the first alpha test session.

### Independent Tracks

These features can be built in parallel with the chat UI:

- **D-5: Concurrent ingestion** -- purely pipeline modification, no UI impact
- **D-2: Source URL mapping** -- a utility function, enhances citation display
- **D-3: Source-balanced ranking** -- modifies search, improves result quality
- **D-4: Remote access** -- deployment configuration, enables team access

### Phase Ordering Recommendation

**Phase A (Foundation):** Claude API integration + streaming + chat UI + basic citations
- Gets the core experience working end-to-end
- Alpha testers can start using it immediately

**Phase B (Quality):** Source-balanced ranking + clickable source links + compiler validation
- Improves result quality and trust signals
- Can be added incrementally during alpha

**Phase C (Infrastructure):** Concurrent ingestion + remote MCP access
- Performance and accessibility improvements
- Needed for sustained alpha use but not for initial evaluation

---

## MVP Recommendation

For the v1.5 alpha, prioritize in this order:

### Must Ship for Alpha

1. **Claude API integration with search result content blocks** (TS-2) -- the core innovation
2. **Streaming response display** (TS-4) -- usability requirement
3. **Web chat interface** (TS-1) -- access point for alpha testers
4. **Source citations** (TS-3) -- primary trust mechanism
5. **Clickable source links** (D-2) -- closes the verification loop (at least for flare:// + HTTP sources)
6. **Remote server access** (D-4, browser only) -- team members can reach the chat

### Should Ship for Alpha

7. **Source-balanced ranking** (D-3) -- improves result diversity
8. **bbjcpl compiler validation** (D-1) -- unique differentiator, high trust value
9. **Remote MCP access** (D-4, Streamable HTTP) -- engineers use Claude Desktop too

### Can Defer to Post-Alpha

10. **Concurrent ingestion** (D-5) -- nice for rebuilds but not needed for alpha testing

---

## Interaction with Existing Features

### How Chat UI Consumes Existing /search

The chat flow reuses the entire existing search infrastructure:

```
User types question in browser
  --> POST /chat (new endpoint)
  --> Backend calls existing POST /search internally
  --> Gets SearchResult[] with content, source_url, title, etc.
  --> Formats as Claude SearchResultBlockParam[]
  --> Calls Claude API with search results + question
  --> Streams response back to browser via SSE
```

No changes to the existing /search endpoint are needed. The chat endpoint is a new layer on top.

### How Compiler Validation Integrates

Compiler validation is a post-processing step on Claude's response:

```
Claude streams response
  --> Response complete
  --> Extract code blocks tagged as ```bbj
  --> For each block: write to temp file, run bbjcpl -N
  --> Annotate each block with validation result
  --> Send validation results as a follow-up SSE event
```

Validation runs after streaming completes. It does not block the initial response display.

### How Source-Balanced Ranking Modifies Search

Source balancing is a post-processing layer on hybrid_search results:

```
hybrid_search() returns top-20 results (existing)
  --> Group by source_group (flare, wordpress, mdx, etc.)
  --> If top-N are all from one group, swap in best results from other groups
  --> Return modified top-N to caller
```

This can be implemented as a wrapper function around the existing search, not a modification to the SQL queries.

---

## Sources

### HIGH Confidence (Official Documentation, Verified)

- Claude API Search Results: [platform.claude.com/docs/en/build-with-claude/search-results](https://platform.claude.com/docs/en/build-with-claude/search-results) -- GA, no beta header. Verified 2026-02-03. Search result content blocks with `SearchResultBlockParam`, citation fields including `search_result_location` with `source`, `title`, `cited_text`.
- Claude API Citations: [platform.claude.com/docs/en/build-with-claude/citations](https://platform.claude.com/docs/en/build-with-claude/citations) -- Document-based citations with character/page/block indices. Plain text, PDF, and custom content document types.
- Claude API Streaming: [platform.claude.com/docs/en/build-with-claude/streaming](https://platform.claude.com/docs/en/build-with-claude/streaming) -- SSE with `text_delta` and `citations_delta` event types. Python SDK `client.messages.stream()` with `stream.text_stream` iterator.
- MCP Remote Servers: [support.claude.com/en/articles/11503834-building-custom-connectors-via-remote-mcp-servers](https://support.claude.com/en/articles/11503834-building-custom-connectors-via-remote-mcp-servers) -- Claude Desktop supports Streamable HTTP for remote MCP servers. Pro/Max/Team/Enterprise plans.
- Ollama Concurrency: [github.com/ollama/ollama/issues/8778](https://github.com/ollama/ollama/issues/8778) -- `OLLAMA_NUM_PARALLEL` default 4, batch embedding support since v0.2.
- Existing codebase: `rag-ingestion/src/bbj_rag/` -- all modules analyzed. REST API, MCP server, search, pipeline, source config patterns documented.

### MEDIUM Confidence (Multiple Sources Agree)

- FastAPI WebSocket/SSE patterns: [fastapi.tiangolo.com/advanced/websockets/](https://fastapi.tiangolo.com/advanced/websockets/) + multiple RAG chat tutorials confirm the FastAPI + SSE approach for streaming chat.
- Corpus imbalance mitigation: [ReFaRAG paper](https://homepages.tuni.fi/konstantinos.stefanidis/docs/FEHDA2025.pdf) -- Re-ranking for diversity in RAG, slot reservation as a simple diversity approach.
- Compiler-in-the-loop validation: [LLMLOOP (ICSME 2025)](https://valerio-terragni.github.io/assets/pdf/ravi-icsme-2025.pdf) -- Compilation checking as first feedback loop for LLM-generated code.
- asyncio.Semaphore for concurrent API calls: [superfastpython.com](https://superfastpython.com/asyncio-semaphore/), [Instructor blog](https://python.useinstructor.com/blog/2023/11/13/learn-async/) -- Standard pattern for rate-limited concurrent I/O.

### LOW Confidence (Needs Validation at Implementation)

- Exact bbjcpl behavior in Docker container: Whether the BBj compiler binary can be installed in the Docker image or must run on the host. Depends on BBj licensing and binary distribution.
- Claude Desktop native Streamable HTTP support: Confirmed for Pro/Max/Team/Enterprise but exact configuration format (`type: "http"` in config) needs testing with the current Claude Desktop version. The mcp-remote fallback is confirmed.
- Concurrent embedding speedup magnitude: 2-3x estimate based on Ollama's `OLLAMA_NUM_PARALLEL=4` and the I/O-bound nature of embedding calls. Actual speedup depends on GPU saturation and model load time.
