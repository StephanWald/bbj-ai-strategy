# Project Research Summary

**Project:** BBj AI Strategy v1.5 Alpha-Ready RAG System
**Domain:** RAG-enhanced documentation chat with compiler validation
**Researched:** 2026-02-03
**Confidence:** HIGH

## Executive Summary

v1.5 transforms the working v1.4 Docker-based RAG system into an alpha-ready product that engineers will trust and use. The core insight driving feature priorities: engineers must TRUST the system before they adopt it. Three features directly address trust: source citations prove answers come from real documentation (not hallucination), compiler validation proves BBj code is syntactically correct, and clickable source links let engineers verify claims against the original docs. Everything else (remote access, ingestion speed, ranking) is infrastructure that makes these trust-building features accessible.

The recommended approach builds on v1.4's validated foundation without replacement. Add a web chat UI served from the existing FastAPI app using HTMX + Jinja2 (zero build pipeline), integrate Claude API for answer generation with Citations API (search result content blocks), and mount the MCP server via Streamable HTTP for remote access. The critical architectural decision: bbjcpl compiler validation runs host-side (where BBj is installed), not in Docker. The MCP server must be refactored from REST proxy to direct database access when mounted in FastAPI to avoid self-referential deadlock.

The most critical risks are SSE newline corruption destroying code blocks in streaming responses (first-impression killer), Claude API context window stuffing degrading answer quality through "lost in the middle" effect, and MCP mounting issues in FastAPI requiring fallback to standalone process. All three have proven mitigations: base64-encode SSE payloads, hard-cap context at 8-10 chunks with token budget, and test MCP mounting early with standalone fallback ready.

## Key Findings

### Recommended Stack

v1.5 adds ONE new direct dependency: `anthropic>=0.77,<1` for Claude API integration. Everything else reuses existing dependencies or standard library. Jinja2 and sse-starlette are already transitive dependencies of FastAPI/MCP SDK. HTMX loads via CDN (14KB, no build step). Concurrent ingestion uses asyncio stdlib with the existing ollama AsyncClient.

**Core technology additions:**
- **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`) — answer generation at $1/M input, $5/M output (3x cheaper than Sonnet, 4-5x faster, sufficient quality for RAG Q&A)
- **Citations API** (stable, not beta) — search result content blocks with `citations.enabled=True` eliminate prompt-engineering citations
- **HTMX 2.0.8 + Jinja2** — zero-build chat UI served from FastAPI, SSE streaming via `hx-ext="sse"`, no Node.js/React overhead
- **MCP Streamable HTTP** — existing SDK supports mounting at `/mcp` path (known issues with path doubling, fallback to standalone process)
- **asyncio.Semaphore** — concurrent ingestion with semaphore=2 limit prevents Ollama GPU saturation

**Critical version constraint:** anthropic SDK v0.77.0 (Jan 2026) confirmed on PyPI. Citations API is GA (not beta). Claude Haiku 4.5 model ID verified in migration guide.

**What NOT to add:** LangChain (unnecessary abstraction over 10-line SDK call), React/Vue (build pipeline overkill for alpha), Tailwind CSS (requires build step), WebSockets (SSE handles unidirectional streaming better), Celery (asyncio.Semaphore handles concurrency), separate frontend container (CORS overhead).

### Expected Features

**Must ship for alpha (table stakes):**
- Web chat interface — browser-based, zero-setup access for engineers
- Claude API integration — turn chunks into coherent cited answers
- Source citations displayed — primary trust mechanism, inline or footnotes
- Streaming response display — 3-10s wait feels broken without streaming
- Clickable source links — verification loop (flare:// → documentation.basis.cloud)
- Remote server access — shared deployment, no per-engineer Docker setup

**Should ship for alpha (differentiators):**
- bbjcpl compiler validation — unique value, no other tool validates BBj syntax
- Source-balanced ranking — surface minority sources (PDF/BBj Source never appear in top-5 without boost)
- Remote MCP via Streamable HTTP — Claude Desktop integration for team

**Can defer to post-alpha:**
- Concurrent ingestion — nice for rebuilds but not needed for alpha testing
- Chat history persistence — alpha evaluates retrieval quality, not chat UX
- User accounts/auth — trusted network, shared API key with rate limiting
- Answer rating/feedback — collect verbally, not via formal system

**Anti-features (explicitly exclude):**
- Conversation memory — stateless queries only, no multi-turn context
- Agentic RAG — single-step retrieval reveals quality issues
- Custom embedding fine-tuning — alpha will generate training data
- Production infrastructure (HTTPS, monitoring, cloud) — local network only

### Architecture Approach

v1.5 is additive. The v1.4 system (pgvector + FastAPI at :10800, MCP stdio on host, Ollama on host) continues to work unchanged. New features mount onto the existing app container with zero new containers, zero new ports, zero schema changes.

**Major components:**
1. **Chat UI module** (`bbj_rag/chat/`) — FastAPI router for `GET /chat` (HTML page) and `POST /chat/send` (SSE stream), Jinja2 templates, HTMX frontend
2. **Claude API wrapper** (`chat/claude.py`) — assembles RAG context from search results, streams via `client.messages.stream()`, formats citations
3. **MCP Streamable HTTP** — refactor `mcp_server.py` from httpx proxy to direct `async_hybrid_search()` calls, mount via `app.mount("/mcp", mcp.streamable_http_app())`
4. **bbjcpl validation** (`validation.py`) — subprocess wrapper for `bbjcpl -N`, MCP tool on host (where BBj installed), optional validation proxy for chat UI
5. **Source-balanced reranker** — Python post-processing in `search.py`, not SQL modification, round-robin by source with max-per-source limit
6. **URL mapping** (`url_mapping.py`) — configuration-based string transformation, `flare://Content/` → `https://documentation.basis.cloud/BASISHelp/WebHelp/`

**Critical refactoring:** MCP server currently proxies to REST API via httpx. When mounted in FastAPI, this creates self-referential loop (app calls itself, deadlocks under single-worker uvicorn). Must call `async_hybrid_search()` directly using `app.state.pool`.

**Data flow for chat query:** Browser → POST /chat/send → embed query (Ollama) → async_hybrid_search (pgvector HNSW + BM25) → source_balanced_rerank (10 results from 30) → map URLs → Claude API stream → SSE to browser. Latency: ~700-1700ms to first token.

### Critical Pitfalls

1. **SSE newline corruption destroys markdown** — Multi-line content (code blocks, paragraphs) splits across SSE frames because `data:` fields are newline-delimited. BBj code examples render as garbled single-line fragments. Engineers see broken output on first query and lose confidence. Prevention: base64-encode each SSE payload and decode client-side, or JSON-encode with escaped newlines. Test with BBj code block BEFORE building full UI. (BLOCKER — first-impression killer)

2. **Claude API context window stuffing degrades quality** — Sending 30 results (to ensure diversity) uses 15-20K tokens. Claude's attention dilutes ("lost in the middle" effect) and answers become vague despite highly relevant chunks. Anthropic research confirms mechanically stuffing lengthy text scatters model attention. Prevention: hard cap at 8-10 results with token budget (~4K tokens), place most relevant results FIRST, log input_tokens for every query. (BLOCKER — fails at primary purpose)

3. **MCP self-referential loop deadlocks** — Current `mcp_server.py` calls `POST /search` via httpx. When mounted in FastAPI, this is self-referential. Under single-worker uvicorn, deadlock: inbound MCP request holds worker, outbound HTTP call needs worker. Prevention: refactor to call `async_hybrid_search()` directly with `app.state.pool`. Test remote MCP early. (BLOCKER — remote MCP non-functional)

4. **ANTHROPIC_API_KEY exposed in shared deployment** — No per-user auth, shared key in Docker env var, no rate limiting, no spending alerts. Runaway script exhausts monthly budget in hours. Prevention: set `max_tokens=2048` per call, add 30 req/min global rate limit, set Anthropic spending alerts ($50/day), use Haiku 4.5 (3x cheaper than Sonnet), log input/output tokens. (BLOCKER — operational incident)

5. **bbjcpl exit code always 0** — Unlike most compilers, bbjcpl exits 0 regardless of success/failure. Errors are on stderr only. Standard pattern (`if result.returncode != 0`) never detects errors. All code blocks marked "validated" including syntax errors. Prevention: parse stderr content (not exit code), test with known-bad code, port stderr parsing from bbjcpltool PoC. (DEGRADED — validation feature produces false positives)

## Implications for Roadmap

Based on research, suggested 5-phase structure aligned with feature dependencies and risk mitigation:

### Phase 1: Foundation (Source Mapping + Balanced Ranking)
**Rationale:** Zero-risk additions that improve quality for all consumers (API, MCP, chat). No new dependencies, no containers, no API keys. Build confidence in codebase changes before major integrations.

**Delivers:**
- `url_mapping.py` — clickable source links for 97.8% of corpus (Flare + WordPress + Web Crawl)
- `source_balanced_rerank()` in `search.py` — minority sources surface in results
- Configuration-based (sources.toml), no schema changes, no re-ingestion

**Avoids:** Regression in working v1.4 system. These are pure additions, opt-in via parameters.

**Research flags:** Standard patterns, skip `/gsd:research-phase`. Well-documented string manipulation and list reranking.

---

### Phase 2: Chat UI + Claude API Integration
**Rationale:** The marquee v1.5 feature. Depends on Phase 1 (URL mapping for citation links, balanced ranking for quality results). This is the make-or-break alpha feature — engineers evaluate whether RAG provides useful BBj answers.

**Delivers:**
- `chat/routes.py` — `GET /chat` (HTML page), `POST /chat/send` (SSE stream)
- `chat/claude.py` — Claude API wrapper with search result content blocks
- `chat/templates/chat.html` — HTMX + SSE chat interface
- Anthropic API key configuration, rate limiting, spending alerts

**Addresses:**
- TS-1: Web chat interface (zero-setup access)
- TS-2: Claude API integration (Citations API with search results)
- TS-3: Source citations (citation links with mapped URLs)
- TS-4: Streaming response display (SSE via HTMX)
- D-2: Clickable source links (uses Phase 1 URL mapping)

**Avoids:**
- C-1: SSE newline corruption (base64-encode SSE payloads, test code blocks first)
- C-2: Context window stuffing (hard cap 8-10 results, token budget)
- C-4: API key cost exposure (rate limiting, spending alerts, Haiku 4.5)
- I-1: SSE error handling (error events, client-side timeout)

**Research flags:** NEEDS `/gsd:research-phase` for SSE encoding patterns and HTMX chat implementation. Critical UX details (newline handling) not obvious from documentation.

---

### Phase 3: Remote MCP (Streamable HTTP)
**Rationale:** Enables shared server deployment. Low code change (mounting pattern designed in v1.4 STACK.md). Main risks are SDK mounting issues and MCP refactoring. Independent of chat UI — can be built in parallel.

**Delivers:**
- Refactored `mcp_server.py` — direct `async_hybrid_search()` calls, not httpx proxy
- `app.mount("/mcp", mcp.streamable_http_app())` — HTTP transport alongside stdio
- Dual transport support — stdio for local dev, HTTP for shared server
- Claude Desktop configuration for remote MCP

**Addresses:**
- D-4: Remote/shared server access (MCP via Streamable HTTP)

**Avoids:**
- C-3: Self-referential httpx loop (refactor to direct search)
- C-5: MCP SDK mounting issues (test early, standalone fallback ready)
- I-7: AsyncConnectionPool exhaustion (increase max_size=15, release connections before streaming)

**Research flags:** NEEDS `/gsd:research-phase` for MCP SDK mounting issues. GitHub issues (#1367) report path doubling and task group conflicts. Fallback patterns need validation.

---

### Phase 4: bbjcpl Compiler Validation
**Rationale:** The unique differentiator (D-1). Requires Phase 3 (MCP HTTP transport) to proxy validation from Docker to host. Standalone addition — does not block other features. Existing bbjcpltool PoC proves pattern.

**Delivers:**
- `validation.py` — subprocess wrapper for `bbjcpl -N`, stderr parsing
- `validate_bbj_code` MCP tool — invokable by Claude
- Optional: validation proxy endpoint for chat UI (requires host-side validation service)

**Addresses:**
- D-1: bbjcpl compiler validation (trust mechanism, unique value)

**Avoids:**
- I-2: Subprocess hangs (10-second timeout, asyncio.wait_for)
- I-3: Exit code always 0 (parse stderr, test with known-bad code)

**Research flags:** Standard patterns, skip `/gsd:research-phase`. bbjcpltool PoC documents exact behavior. Subprocess timeout + stderr parsing well-established.

---

### Phase 5: Concurrent Ingestion
**Rationale:** Performance optimization, not user-facing. Can be done independently. Biggest code change (async pipeline wrapper) but well-understood pattern. Defer to last to avoid blocking alpha.

**Delivers:**
- `asyncio.gather()` + semaphore in `ingest_all.py` — parallel source processing
- Implement `--parallel` flag (currently stub)
- Resume state file locking (prevent JSON corruption)

**Addresses:**
- D-5: Concurrent ingestion workers (faster corpus rebuilds)

**Avoids:**
- I-5: Resume state race condition (asyncio.Lock for file writes)
- I-6: Ollama GPU saturation (semaphore=2, monitor throughput)

**Research flags:** Standard patterns, skip `/gsd:research-phase`. asyncio.Semaphore + gather() well-documented. Main uncertainty is speedup magnitude (expect 1.5-2x).

---

### Phase Ordering Rationale

- **Phase 1 first:** Zero-risk infrastructure improvements that benefit all phases. No API keys, no containers, no complex integrations.
- **Phase 2 as core:** Chat UI + Claude API is the alpha milestone. Everything else enhances this core feature.
- **Phase 3 parallel to Phase 2:** Remote MCP independent of chat — can be built by separate developer.
- **Phase 4 after Phase 3:** bbjcpl validation needs MCP HTTP (for chat UI proxy) or standalone validation service.
- **Phase 5 last:** Ingestion performance does not block alpha testing. Chat users don't run ingestion.

**Dependency graph:**
```
Phase 1 (URL mapping + balanced ranking)
    ├── Phase 2 (Chat UI + Claude) — DEPENDS on Phase 1 for citations
    ├── Phase 3 (Remote MCP) — INDEPENDENT, parallel to Phase 2
    │       └── Phase 4 (bbjcpl validation) — DEPENDS on Phase 3 for HTTP validation proxy
    └── Phase 5 (Concurrent ingestion) — INDEPENDENT, can be deferred
```

### Research Flags

**Phases needing `/gsd:research-phase` during planning:**
- **Phase 2 (Chat UI + Claude):** SSE encoding patterns for multi-line content, HTMX chat implementation details, citation rendering. The SSE newline corruption pitfall is critical and not obvious from docs.
- **Phase 3 (Remote MCP):** MCP SDK mounting issues (#1367), path doubling workarounds, lifespan integration. GitHub issues report problems with FastAPI mounting.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (URL mapping + ranking):** Configuration-based string transformation and list reranking. No ambiguity.
- **Phase 4 (bbjcpl validation):** subprocess.run with timeout, stderr parsing. Proven by bbjcpltool PoC.
- **Phase 5 (Concurrent ingestion):** asyncio.Semaphore + gather(). Well-documented stdlib pattern.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | anthropic SDK v0.77.0 verified on PyPI (Jan 2026). Citations API confirmed GA. Jinja2/sse-starlette already transitive deps. HTMX 2.0.8 verified on GitHub releases. |
| Features | HIGH | Claude API Citations with search result blocks verified against official docs. HTMX SSE patterns confirmed across multiple tutorials. bbjcpl behavior documented in bbjcpltool PoC. |
| Architecture | HIGH | FastAPI + Jinja2 + HTMX is well-established pattern. MCP mounting issues documented with fallback. asyncio.Semaphore standard for concurrent I/O. |
| Pitfalls | HIGH | SSE newline corruption confirmed in HTMX chatbot article. "Lost in the middle" confirmed by Anthropic research. bbjcpl exit code 0 documented in bbjcpltool PROJECT.md. |

**Overall confidence:** HIGH

v1.5 builds on a working v1.4 foundation with minimal new dependencies and well-documented integration patterns. The critical risks (SSE encoding, context stuffing, MCP deadlock) have proven mitigations from community experience and official SDK docs.

### Gaps to Address

**SSE encoding for multi-line content:** The base64 approach is documented but implementation details (client-side decoding in HTMX, performance impact of 33% payload increase) need validation during Phase 2 planning. Alternative: JSON-encode with escaped newlines. Both approaches tested in community projects but choice depends on HTMX version compatibility.

**MCP SDK mounting stability:** The official SDK's `streamable_http_app()` has reported issues (RuntimeError with task groups, path doubling). The standalone `fastmcp` package (v2.3+) has better FastAPI integration but is a different package. Decision between official SDK + fallback vs standalone package needs evaluation at Phase 3 start.

**Source-balanced ranking calibration:** The `min_score_ratio=0.5` threshold prevents boosting irrelevant minority sources, but this is a guess. Alpha tester feedback will calibrate. Make configurable from start. No need for upfront research — tune based on usage.

**Ollama concurrent embedding speedup:** Expected 1.5-2x speedup with semaphore=2 based on I/O overlap, but actual speedup depends on GPU saturation and model load time. Profile baseline before implementing to set realistic expectations. If speedup is marginal, defer this phase entirely.

## Sources

### Primary (HIGH confidence)

**Stack:**
- [Anthropic Python SDK — PyPI](https://pypi.org/project/anthropic/) — v0.77.0 (2026-01-29), MIT license
- [Anthropic Python SDK — GitHub](https://github.com/anthropics/anthropic-sdk-python) — Streaming, Citations API examples
- [Anthropic Citations API](https://platform.claude.com/docs/en/build-with-claude/citations) — Stable (not beta), search result content blocks
- [Claude Haiku 4.5 Announcement](https://www.anthropic.com/news/claude-haiku-4-5) — Pricing, performance benchmarks
- [MCP Python SDK — PyPI](https://pypi.org/project/mcp/) — v1.26.0 (2026-01-24)
- [MCP SDK GitHub Issues](https://github.com/modelcontextprotocol/python-sdk/issues/1367) — Streamable HTTP mounting issues
- [htmx — GitHub Releases](https://github.com/bigskysoftware/htmx/releases) — v2.0.8, SSE extension
- [FastAPI Templates](https://fastapi.tiangolo.com/advanced/templates/) — Jinja2Templates, StaticFiles
- [sse-starlette — PyPI](https://pypi.org/project/sse-starlette/) — v3.2.0 (2026-01-17)

**Features:**
- [Claude API Search Results](https://platform.claude.com/docs/en/build-with-claude/search-results) — GA, `SearchResultBlockParam` format
- [Claude API Streaming](https://platform.claude.com/docs/en/build-with-claude/streaming) — SSE with `text_delta` events
- [MCP Remote Servers](https://support.claude.com/en/articles/11503834-building-custom-connectors-via-remote-mcp-servers) — Streamable HTTP support
- [Ollama Python SDK](https://github.com/ollama/ollama-python) — AsyncClient, embed() API
- [Ollama Concurrency](https://github.com/ollama/ollama/issues/8778) — OLLAMA_NUM_PARALLEL default 4

**Architecture:**
- [FastMCP HTTP Deployment](https://gofastmcp.com/deployment/http) — Mount pattern, lifespan integration
- [FastAPI + HTMX Chat Pattern](https://karl-sparks.github.io/ks-personal-blog/posts/fastapi-htmx-docker-tutorial/) — SSE streaming
- [bbjcpltool PROJECT.md](/Users/beff/bbjcpltool/.planning/PROJECT.md) — Compiler behavior: stderr parsing, -N flag

**Pitfalls:**
- [HTMX SSE Newline Corruption](https://towardsdatascience.com/javascript-fatigue-you-dont-need-js-to-build-chatgpt-part-2/) — base64 encoding workaround
- [HTMX SSE Error Handling Issue #134](https://github.com/bigskysoftware/htmx-extensions/issues/134) — SSE extension doesn't handle errors
- [Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) — "Lost in the middle" effect
- [Ollama Per-Model Concurrency Issue #5693](https://github.com/ollama/ollama/issues/5693) — Parallelism vs memory pressure
- [psycopg3 Pool Documentation](https://www.psycopg.org/psycopg3/docs/advanced/pool.html) — Exhaustion behavior

### Secondary (MEDIUM confidence)

- [FastAPI + HTMX Modern Approach](https://dev.to/jaydevm/fastapi-and-htmx-a-modern-approach-to-full-stack-bma) — Stack validation
- [ReFaRAG paper](https://homepages.tuni.fi/konstantinos.stefanidis/docs/FEHDA2025.pdf) — Re-ranking for diversity
- [LLMLOOP (ICSME 2025)](https://valerio-terragni.github.io/assets/pdf/ravi-icsme-2025.pdf) — Compilation checking for LLM code
- [Converting STDIO to Remote MCP](https://portkey.ai/docs/guides/converting-stdio-to-streamable-http) — Migration guide
- [How Ollama Handles Parallel Requests](https://www.glukhov.org/post/2025/05/how-ollama-handles-parallel-requests/) — Queuing behavior

### Tertiary (LOW confidence)

- [Ollama Async Client Issue #197](https://github.com/ollama/ollama-python/issues/197) — Concurrent request limits (may be resolved)
- [FastAPI SSE in Docker Discussion #11590](https://github.com/fastapi/fastapi/discussions/11590) — Environment-specific issues

---
*Research completed: 2026-02-03*
*Ready for roadmap: yes*
