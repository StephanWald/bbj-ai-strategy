# Technology Stack: v1.5 Alpha-Ready RAG System

**Project:** BBj AI Strategy -- Alpha-Readiness Features
**Researched:** 2026-02-03
**Scope:** Chat UI, Claude API integration, bbjcpl compiler integration, remote MCP access, concurrent ingestion, source-balanced ranking
**Overall confidence:** HIGH (versions verified via PyPI, GitHub, and official docs as of 2026-02-03)

---

## Context: What This Stack Adds

The v1.4 milestone delivered a working Docker-based RAG system with FastAPI REST API (POST /search, GET /stats, GET /health) at localhost:10800 and an MCP server via stdio transport for Claude Desktop. The v1.5 milestone adds **alpha-readiness features** on top of that foundation:

1. **Web chat interface** -- Browser-based chat UI for engineers to query the RAG system and get Claude-generated answers with source citations
2. **Claude API integration** -- Anthropic SDK for answer generation grounded in RAG search results
3. **bbjcpl compiler integration** -- BBj syntax validation of code in RAG responses or LLM-generated code
4. **Remote MCP access** -- Streamable HTTP transport so the MCP server is network-accessible (not just local stdio)
5. **Concurrent ingestion** -- Parallel embedding calls to speed up the ingestion pipeline
6. **Source-balanced ranking** -- Algorithmic boost for minority sources in RRF results

**Key constraint:** The existing stack (Python 3.12, FastAPI, psycopg3, pgvector, Ollama, MCP SDK v1.x, Docker Compose) is validated and unchanged. This document covers ONLY new additions.

---

## Recommended Stack Additions

### 1. Claude API Integration (Answer Generation)

| Package | Version Constraint | Purpose | Why |
|---------|-------------------|---------|-----|
| `anthropic` | `>=0.77,<1` | Anthropic Python SDK | Official SDK for Claude API. Provides sync/async clients, streaming via `messages.stream()`, and the Citations API for RAG-grounded generation with verifiable source references. |

**Model recommendation:** `claude-haiku-4-5` (model ID: `claude-haiku-4-5-20251001`)

| Factor | Claude Haiku 4.5 | Claude Sonnet 4.5 |
|--------|------------------|-------------------|
| Input tokens | $1/M tokens | $3/M tokens |
| Output tokens | $5/M tokens | $15/M tokens |
| Speed | 4-5x faster than Sonnet | Baseline |
| SWE-bench | 73.3% | Higher |
| Use case fit | Chat responses grounded in RAG context (not complex reasoning) | Overkill for citation-backed Q&A |

**Why Haiku 4.5:** This is a RAG Q&A use case, not a complex reasoning task. The model reads retrieved documentation chunks and generates grounded answers with citations. Haiku 4.5 delivers near-frontier quality at 1/3 the cost of Sonnet and 4-5x the speed, which matters for interactive chat. Upgrade to Sonnet only if answer quality proves insufficient in testing.

**Citations API (stable, not beta):**

The Anthropic Citations API is the key integration point for RAG-grounded generation. Instead of prompt-engineering citations, you send RAG chunks as `document` content blocks with `citations.enabled=True`. Claude returns interleaved text blocks with `cited_text` references back to exact positions in the source documents.

For this project's RAG results, use **plain text documents** -- each search result becomes a document block:

```python
# Each RAG search result becomes a document content block
documents = []
for result in search_results:
    documents.append({
        "type": "document",
        "source": {
            "type": "text",
            "media_type": "text/plain",
            "data": result.content,
        },
        "title": result.title,
        "context": f"Source: {result.source_url} | Type: {result.doc_type}",
        "citations": {"enabled": True},
    })

response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=2048,
    messages=[{"role": "user", "content": documents + [{"type": "text", "text": query}]}],
)
```

**Streaming support:** The SDK provides `client.messages.stream()` for SSE-style token delivery. Combined with the chat UI's SSE endpoint, this enables real-time response streaming to the browser. Citations arrive as `citations_delta` events during streaming.

**Context window:** All active Claude models support 200K context window. With 5-10 RAG results averaging 400 tokens each, the context usage is ~2K-4K tokens per query -- well within limits. Prompt caching (`cache_control: {"type": "ephemeral"}`) can reduce costs if the same system prompt is reused across requests (1-hour cache TTL, minimum 1024 tokens).

**Environment variable:** `ANTHROPIC_API_KEY` -- the SDK reads this automatically. Store in `.env` file, pass via Docker Compose environment.

**Confidence:** HIGH -- Anthropic SDK v0.77.0 verified on PyPI (2026-01-29). Citations API confirmed stable (not beta) in official docs. Model IDs verified in migration guide.

### 2. Web Chat Interface (Frontend)

**Recommendation: HTMX + Jinja2 templates served from the existing FastAPI app.**

| Component | Version | Purpose | Why |
|-----------|---------|---------|-----|
| `jinja2` | `>=3.1,<4` (already a transitive dep of FastAPI) | HTML templating | FastAPI has native Jinja2 support via `Jinja2Templates`. Already in the dependency tree -- Starlette depends on it. Zero new dependencies. |
| `htmx` | `2.0.8` (via CDN) | Dynamic UI without JavaScript framework | 14KB library, no build pipeline, no Node.js. Perfect for a chat interface that sends POST requests and receives HTML fragments. |
| `sse-starlette` | `>=3.2,<4` | Server-Sent Events for streaming | Production-ready SSE implementation for FastAPI. Enables token-by-token streaming from Claude API to browser via htmx SSE extension. Already a transitive dep of the `mcp` package. |

**Architecture: Serve from FastAPI, not a separate frontend.**

| Approach | Complexity | Fit for Alpha |
|----------|------------|---------------|
| HTMX + Jinja2 from FastAPI | Low -- 2-3 templates, no build step | Perfect |
| React/Vite SPA | Medium -- Node.js, npm, build pipeline, CORS | Overkill |
| Separate Streamlit app | Low for prototype, but separate process | Wrong tool (not embeddable) |

**Why HTMX over React/Vue/Svelte:** This is an alpha for a team of BBj engineers, not a consumer product. The chat UI needs:
- A text input box
- A scrolling message area
- Streaming response display
- Source citation links

HTMX handles all of this with HTML attributes (`hx-post`, `hx-target`, `hx-swap`, `hx-ext="sse"`) and zero JavaScript. The entire frontend is a few Jinja2 templates served from the existing FastAPI app. No build step, no Node.js, no CORS configuration, no separate container.

**Chat streaming pattern:**

1. User types a query, HTMX sends `POST /chat` with the message
2. FastAPI endpoint runs RAG search, then streams Claude API response via SSE
3. HTMX SSE extension (`hx-ext="sse"`, `sse-connect="/chat/stream/{id}"`) receives HTML fragments
4. Each fragment is swapped into the chat area in real-time

**Static files:** Use FastAPI's `StaticFiles` mount for CSS and any minimal JS. Templates in a `templates/` directory within the project.

```python
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
```

**CSS framework:** Use plain CSS or a lightweight utility framework like Pico CSS (~10KB) for basic styling. Do NOT add Tailwind (requires build step) or any CSS framework that needs Node.js.

**Confidence:** HIGH -- FastAPI Jinja2 integration verified in official docs. HTMX 2.0.8 verified on GitHub releases. SSE streaming pattern verified across multiple FastAPI + htmx tutorials and projects. `sse-starlette` 3.2.0 verified on PyPI (2026-01-17).

### 3. bbjcpl Compiler Integration

**The bbjcpl compiler runs on the engineer's host machine, not in Docker.**

This is the critical architectural constraint. bbjcpl lives at a BBj installation path (e.g., `/Users/beff/bbx/bin/bbjcpl`). It is not a Python package. It is a compiled binary that requires a BBj license and installation. It cannot be containerized without the full BBj runtime.

**Three integration paths (in priority order):**

#### Path A: MCP Tool (Recommended for alpha)

Add a `validate_bbj_syntax` tool to the MCP server that extracts BBj code blocks from Claude's response and runs `bbjcpl -N` on them via `asyncio.create_subprocess_exec()`.

| Aspect | Detail |
|--------|--------|
| Where it runs | On the MCP server process (host machine, not Docker) |
| How it's invoked | Claude calls the `validate_bbj_syntax` MCP tool after generating code |
| Subprocess call | `bbjcpl -N <temp_file.bbj>` |
| Error detection | Parse stderr (bbjcpl always exits 0; errors are on stderr) |
| Existing PoC | `/Users/beff/bbjcpltool/` -- PostToolUse hook validates .bbj files via `bbjcpl -N` |

```python
@mcp.tool()
async def validate_bbj_syntax(code: str) -> str:
    """Validate BBj source code syntax using the bbjcpl compiler.

    Args:
        code: BBj source code to validate.
    """
    # Write to temp file, run bbjcpl -N, parse stderr
    ...
```

**Why MCP tool over other approaches:**
- The MCP server already runs on the host (stdio transport for Claude Desktop)
- Claude can call the tool proactively after generating BBj code
- The existing bbjcpltool PoC already proves this pattern works
- No changes needed to the Docker container

**Configuration:** The bbjcpl path should be configurable via environment variable (`BBJCPL_PATH`, default `/Users/beff/bbx/bin/bbjcpl`). This matches the existing bbjcpltool pattern.

#### Path B: Chat UI Integration (Future)

When the chat UI generates BBj code via Claude, the server-side `/chat` endpoint could validate code blocks before returning them. This requires the FastAPI container to reach the host's bbjcpl binary, which is architecturally messy (Docker-to-host subprocess). Defer to a later milestone.

#### Path C: Claude Code Hook (Already exists)

The existing bbjcpltool PostToolUse hook at `~/.claude/` already validates .bbj files that Claude Code writes. This covers the "engineer using Claude Code locally" workflow. No new work needed.

**Summary:** For v1.5, add `validate_bbj_syntax` as an MCP tool. The chat UI's code validation is a future enhancement.

**Confidence:** HIGH -- bbjcpl behavior verified from bbjcpltool PROJECT.md (stderr parsing, -N flag, exit code 0). The MCP tool pattern matches existing `search_bbj_knowledge` tool structure. `asyncio.create_subprocess_exec` is stdlib, no new dependency.

### 4. Remote MCP Access (Streamable HTTP)

The existing MCP server uses stdio transport, spawned by Claude Desktop as a local child process. For alpha deployment on a shared server, we need network-accessible MCP.

**The existing v1.4 STACK.md already designed this.** The MCP server mounts on the FastAPI ASGI app:

```python
app.mount("/mcp", mcp_server.streamable_http_app())
```

**What's needed for v1.5:**

| Aspect | Detail |
|--------|--------|
| Transport | Streamable HTTP (replaces stdio for remote access; stdio preserved for local dev) |
| Mount path | `/mcp` on the existing FastAPI app |
| Configuration | `stateless_http=True` on FastMCP (no session state needed for search) |
| No new dependencies | MCP SDK v1.x (`mcp>=1.25,<2`) already supports Streamable HTTP since v1.8.0 |

**Known issue: GitHub #1367 (path doubling)**

When mounting via `app.mount("/mcp", mcp.streamable_http_app())`, the full URL becomes `/mcp/mcp` because the Streamable HTTP app has its own internal `/mcp` path. Two workarounds:

1. **Mount at root with sub-path:** `app.mount("/", mcp_server.streamable_http_app())` -- MCP endpoint at `/mcp`
2. **Override internal path:** Pass `streamable_http_path="/"` to the ASGI app (if supported in current SDK version)
3. **Accept double path:** Document that MCP endpoint is at `http://server:10800/mcp/mcp`

Verify which approach works at implementation time. This is a known SDK issue, not a blocker.

**Lifespan integration:** When mounting MCP alongside FastAPI, the MCP session manager's lifespan must be integrated with FastAPI's lifespan using `contextlib.AsyncExitStack`. The SDK v1.9.0+ documents this pattern:

```python
from contextlib import AsyncExitStack, asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(mcp_server.session_manager.run())
        # ... existing lifespan setup (pool, ollama warmup) ...
        yield
```

**Client configuration for remote MCP:**

Engineers configure their Claude Desktop to connect via Streamable HTTP instead of stdio:

```json
{
  "mcpServers": {
    "bbj-knowledge": {
      "url": "http://shared-server:10800/mcp"
    }
  }
}
```

**Dual transport support:** Keep both stdio (for local dev) and Streamable HTTP (for shared server). The same `FastMCP` instance supports both -- stdio via `mcp.run(transport="stdio")` and HTTP via `mcp.streamable_http_app()`.

**Confidence:** HIGH -- Streamable HTTP verified as recommended transport in MCP spec and SDK docs. `stateless_http=True` pattern verified. Path doubling issue (#1367) documented and workarounds known. MCP SDK v1.26.0 on PyPI.

### 5. Concurrent Ingestion (Parallel Embeddings)

The current pipeline in `pipeline.py` calls `embedder.embed_batch()` synchronously in a single-threaded loop. For 50,439 chunks, this is the bottleneck.

**Approach: `asyncio.Semaphore` + Ollama `AsyncClient` for parallel embedding batches.**

| Component | Already Available | Purpose |
|-----------|-------------------|---------|
| `ollama.AsyncClient` | Yes (`ollama>=0.6,<1`) | Async embedding calls |
| `asyncio.Semaphore` | Yes (stdlib) | Limit concurrent Ollama requests |
| `asyncio.gather()` | Yes (stdlib) | Run batches concurrently |
| `psycopg.AsyncConnection` | Yes (already used in API) | Async DB writes |

**No new dependencies required.**

**Pattern:**

```python
import asyncio
from ollama import AsyncClient

async def embed_batches_concurrent(
    chunks: list[list[str]],
    model: str,
    max_concurrent: int = 4,
) -> list[list[list[float]]]:
    sem = asyncio.Semaphore(max_concurrent)
    client = AsyncClient()

    async def embed_one_batch(batch: list[str]) -> list[list[float]]:
        async with sem:
            response = await client.embed(model=model, input=batch)
            return response.embeddings

    tasks = [embed_one_batch(batch) for batch in chunks]
    return await asyncio.gather(*tasks)
```

**Concurrency limit:** Default to 4 concurrent Ollama embedding requests. Ollama's default `OLLAMA_NUM_PARALLEL` is 4 (can be tuned up). Setting the semaphore higher than the server's capacity just queues requests, so the semaphore primarily prevents overwhelming httpx connection limits.

**Known issue: Ollama async client may limit to 2 concurrent requests** (GitHub issue #197 in ollama-python). If this surfaces, the workaround is using `httpx.AsyncClient` directly against the `/api/embed` endpoint instead of the `ollama` library's `AsyncClient`. This is a fallback, not the default approach.

**Integration with existing pipeline:** The `_embed_and_store()` function in `pipeline.py` currently calls `embedder.embed_batch(texts)` synchronously. Replace with an async wrapper that splits the batch into sub-batches and embeds concurrently. The pipeline orchestrator (`run_pipeline`) would need an async variant.

**Confidence:** HIGH -- `asyncio.Semaphore` + `asyncio.gather()` is the standard Python pattern for concurrent I/O. Ollama AsyncClient documented in ollama-python README. No new dependencies.

### 6. Source-Balanced Ranking

**No new dependencies.** This is a pure algorithmic change to the existing SQL hybrid search query.

The current RRF (Reciprocal Rank Fusion) in `search.py` sums `rrf_score(rank)` across dense and BM25 sub-queries. Source balancing adds a post-RRF reranking step that boosts results from under-represented `doc_type` values.

**Approach: Source diversity multiplier in Python.**

After RRF produces ranked results, apply a diversity-aware reranking:

```python
def source_balanced_rerank(
    results: list[SearchResult],
    target_count: int,
    diversity_weight: float = 0.3,
) -> list[SearchResult]:
    """Rerank results to boost minority sources.

    Applies a penalty to results from doc_types that already appear
    frequently in the ranked list, promoting diversity.
    """
    # Count source appearances so far
    # Apply diminishing returns multiplier per source
    # Re-sort by adjusted score
    ...
```

**Why Python post-processing, not SQL:** The diversity logic requires iterative selection (the score adjustment depends on what's already been selected). This is awkward to express in SQL but trivial in Python. Since we already fetch 20 results per sub-query and return 5-10 to the user, the post-processing operates on a small list.

**Confidence:** HIGH -- Pure algorithmic change. No library needed. The existing `hybrid_search()` returns `SearchResult` objects with `doc_type` and `score` fields, which is all the reranker needs.

---

## Source URL Mapping

The current `source_url` values in the chunks table use internal prefixes:

| Internal Prefix | Example | Real HTTP URL |
|-----------------|---------|---------------|
| `flare://Content/...` | `flare://Content/bbjobjects/BBjGrid/BBjGrid.htm` | `https://documentation.basis.cloud/BASISHelp/WebHelp/bbjobjects/BBjGrid/BBjGrid.htm` |
| `pdf://page/N` | `pdf://page/42` | No direct URL (PDF is local file) |
| `mdx://bbj-dwc-tutorial/...` | `mdx://bbj-dwc-tutorial/docs/intro` | `https://basishub.github.io/bbj-dwc-tutorial/docs/intro` |
| `mdx://bbj-beginner-tutorial/...` | `mdx://bbj-beginner-tutorial/docs/intro` | `https://basishub.github.io/bbj-beginner-tutorial/docs/intro` |
| `bbj-source://...` | `bbj-source://samples/BBjGrid.bbj` | No direct URL (local .bbj file) |
| `https://...` | WordPress/web crawl URLs | Already real URLs |

**Approach: Lookup table in configuration.**

Add a `url_mapping` configuration (in `config.toml` or Settings) that maps internal prefixes to HTTP base URLs:

```toml
[url_mapping]
"flare://Content/" = "https://documentation.basis.cloud/BASISHelp/WebHelp/"
"mdx://bbj-dwc-tutorial/" = "https://basishub.github.io/bbj-dwc-tutorial/"
"mdx://bbj-beginner-tutorial/" = "https://basishub.github.io/bbj-beginner-tutorial/"
"mdx://bbj-db-modernization-tutorial/" = "https://basishub.github.io/bbj-db-modernization-tutorial/"
```

A utility function resolves internal URLs to HTTP URLs at response time:

```python
def resolve_source_url(internal_url: str, mapping: dict[str, str]) -> str | None:
    """Map internal source_url to public HTTP URL.

    Returns None for sources without web URLs (pdf://, bbj-source://).
    """
    for prefix, base_url in mapping.items():
        if internal_url.startswith(prefix):
            return base_url + internal_url[len(prefix):]
    if internal_url.startswith(("http://", "https://")):
        return internal_url
    return None  # No mapping available
```

**No new dependencies.** Pure configuration + string manipulation.

**Confidence:** HIGH -- The `source_url` format is already established in the codebase. This is a presentation-layer mapping applied in the chat UI and API response enrichment.

---

## Complete New Dependencies

Only these packages need to be added to `pyproject.toml` for v1.5:

```toml
[project]
dependencies = [
    # ... existing v1.4 dependencies unchanged ...
    "anthropic>=0.77,<1",
]
```

**That is 1 new direct dependency.** Everything else is either already in the dependency tree or uses stdlib:

| Capability | Library | Status |
|-----------|---------|--------|
| Claude API | `anthropic>=0.77,<1` | **NEW** -- the only new pip dependency |
| Jinja2 templates | `jinja2` | Already transitive dep of FastAPI (via Starlette) |
| SSE streaming | `sse-starlette` | Already transitive dep of `mcp` SDK |
| HTMX | CDN `<script>` tag | No Python package needed |
| Concurrent embedding | `asyncio`, `ollama.AsyncClient` | stdlib + existing dep |
| bbjcpl subprocess | `asyncio.create_subprocess_exec` | stdlib |
| Streamable HTTP MCP | `mcp>=1.25,<2` | Already in project |
| Source-balanced ranking | Pure Python | No dep |
| URL mapping | Pure Python + config | No dep |

### Installation Command

```bash
cd /Users/beff/_workspace/bbj-ai-strategy/rag-ingestion
uv add "anthropic>=0.77,<1"
```

**Confidence:** HIGH -- Minimal dependency addition. The anthropic SDK's only required dependency is httpx, which is already in the project.

---

## What NOT to Add (And Why)

| Temptation | Why Not |
|------------|---------|
| **LangChain / LlamaIndex** | The RAG pipeline is already built with raw psycopg3 + pgvector. Adding a framework for Claude API calls wraps a 10-line SDK call in 500 lines of abstraction. Use the anthropic SDK directly. |
| **React / Vue / Svelte frontend** | Alpha chat UI for a team of ~5 engineers. HTMX + Jinja2 takes hours to build; a React app takes days and adds Node.js, npm, a build pipeline, and CORS configuration. Not justified for alpha. |
| **Tailwind CSS** | Requires a build step (PostCSS/CLI). For an alpha chat UI, plain CSS or Pico CSS (~10KB, zero build) is sufficient. |
| **WebSockets for chat streaming** | SSE (Server-Sent Events) is unidirectional server-to-client, which is exactly what streaming LLM responses needs. WebSockets add bidirectional complexity for no benefit here. HTMX has native SSE support. |
| **Celery / task queue for ingestion** | Concurrent ingestion uses asyncio within a single process. Celery adds Redis/RabbitMQ, worker processes, and deployment complexity. asyncio.Semaphore + gather() handles the concurrency needed. |
| **Separate frontend container** | The chat UI is ~3 HTML templates and a CSS file. Serving from the existing FastAPI app avoids CORS, eliminates a container, and keeps deployment simple. |
| **`fastmcp` standalone package** | The official `mcp` SDK's built-in FastMCP handles everything needed. Standalone fastmcp adds server composition and proxying features that are unnecessary. |
| **`fastapi-mcp` package** | This auto-converts FastAPI endpoints to MCP tools. We want curated MCP tools with specific behavior, not an auto-mirror. |
| **`aiohttp` for Ollama calls** | The `ollama` library's `AsyncClient` already uses `httpx.AsyncClient` internally. Adding aiohttp creates a second HTTP client library for no reason. |
| **Claude Sonnet 4.5 as default model** | 3x the cost of Haiku 4.5 for a RAG Q&A use case that is citation-grounded, not creativity-demanding. Start with Haiku, upgrade per-query if needed. |
| **pgvector HNSW reindexing** | Source-balanced ranking is a post-retrieval reranking step. It does not change the vector index or require schema changes. |
| **Authentication / auth middleware** | Alpha deployment is on a trusted local network for a small team. Add auth in a later milestone when exposing to wider audience. |

---

## Version Matrix (All Verified 2026-02-03)

### New Dependencies

| Package | Constraint | Current Latest | Verified Source |
|---------|-----------|---------------|-----------------|
| `anthropic` | `>=0.77,<1` | 0.77.0 | [PyPI](https://pypi.org/project/anthropic/) (2026-01-29) |

### CDN Resources (No Package Install)

| Library | Version | CDN | Verified Source |
|---------|---------|-----|-----------------|
| `htmx` | 2.0.8 | `cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.min.js` | [GitHub Releases](https://github.com/bigskysoftware/htmx/releases) |

### Already-Available Dependencies (Unchanged)

| Package | Current Constraint | Role in v1.5 | Changes? |
|---------|--------------------|------|----------|
| `mcp[cli]` | `>=1.25,<2` | Streamable HTTP transport, MCP tool for bbjcpl | None. Streamable HTTP supported since v1.8.0. |
| `fastapi` | `>=0.115,<1` | Chat UI templates, SSE endpoints | None. Jinja2Templates and StaticFiles already available. |
| `ollama` | `>=0.6,<1` | AsyncClient for concurrent embeddings | None. AsyncClient available in current version (0.6.1). |
| `httpx` | `>=0.28,<1` | MCP server HTTP client, anthropic transitive dep | None. |
| `pydantic` | `>=2.12,<3` | Chat request/response models | None. |
| `psycopg[binary,pool]` | `>=3.3,<4` | Async connection pool | None. |
| `sse-starlette` | (transitive via mcp) | SSE streaming for chat UI | None. Already installed as mcp dependency. |
| `jinja2` | (transitive via fastapi/starlette) | HTML templates for chat UI | None. Already installed as starlette dependency. |

---

## Alternatives Considered

### Answer Generation SDK

| Option | Considered | Decision | Rationale |
|--------|-----------|----------|-----------|
| `anthropic` (direct SDK) | Yes | **Selected** | Minimal abstraction. Citations API is SDK-native. Streaming works with FastAPI SSE. One dependency. |
| LangChain + ChatAnthropic | Yes | Rejected | Adds langchain-core, langchain-anthropic, and dozens of transitive deps. Wraps a simple `messages.create()` call in chain abstraction. The project has no other LangChain components. |
| LiteLLM | Yes | Rejected | Multi-provider proxy. Useful when switching between OpenAI/Anthropic/etc. This project uses Claude exclusively. The abstraction adds a layer with no benefit. |
| Ollama + local model | Yes | Rejected | Local models cannot match Claude Haiku 4.5's citation quality and instruction following for RAG Q&A. The Ollama stack is already used for embeddings; answer generation needs a stronger model. |

### Chat UI Framework

| Option | Considered | Decision | Rationale |
|--------|-----------|----------|-----------|
| HTMX + Jinja2 | Yes | **Selected** | Zero build pipeline. 14KB JS library. Native SSE support. Served from existing FastAPI. Perfect for alpha. |
| React + Vite | Yes | Rejected | Requires Node.js, npm, build step, CORS config, separate container or static build. Overkill for alpha. |
| Streamlit | Yes | Rejected | Separate process, cannot embed in FastAPI, limited customization, ugly for production use. |
| Gradio | Yes | Rejected | Designed for ML demos. Can mount in FastAPI but styling is not customizable enough. |
| Chainlit | Yes | Rejected | Full-featured chat framework but opinionated and heavy. Adds its own dependency tree. |

### bbjcpl Integration

| Option | Considered | Decision | Rationale |
|--------|-----------|----------|-----------|
| MCP tool on host | Yes | **Selected** | Matches existing architecture (MCP server on host). Claude invokes it naturally. Proven by bbjcpltool PoC. |
| Docker volume mount of binary | Yes | Rejected | bbjcpl requires full BBj runtime. Mounting just the binary does not work (Java dependencies, license files). |
| HTTP wrapper service | Yes | Rejected | Adds a separate service to manage. The MCP tool approach uses the existing MCP server process. |
| Claude Code hook only | Partially | **Already exists** | The bbjcpltool PostToolUse hook covers Claude Code workflows. But the chat UI needs server-side validation too (later milestone). |

### Concurrent Ingestion

| Option | Considered | Decision | Rationale |
|--------|-----------|----------|-----------|
| asyncio.Semaphore + gather | Yes | **Selected** | Standard Python pattern. No new deps. Ollama AsyncClient already available. |
| ThreadPoolExecutor | Yes | Rejected | The sync Ollama client is I/O-bound (HTTP call), not CPU-bound. asyncio is more efficient for I/O concurrency and the codebase already uses async patterns (FastAPI, psycopg async). |
| Celery workers | Yes | Rejected | Massive overhead (Redis/RabbitMQ, separate worker processes) for a batch job that runs occasionally. asyncio handles the parallelism. |
| multiprocessing | Yes | Rejected | Embedding is not CPU-bound in the Python process -- it is an HTTP call to Ollama. Multiple processes add overhead without benefit. |

---

## Integration Points with Existing Code

### Chat UI -> Existing API

The chat endpoint reuses the existing search infrastructure:

```
Browser (htmx) -> POST /chat -> embed query (Ollama) -> hybrid_search (pgvector)
                                -> Claude API (anthropic SDK, with RAG results as documents)
                                -> SSE stream response back to browser
```

The `/chat` endpoint internally calls the same `async_hybrid_search()` and Ollama embedding that `/search` uses. Claude API is the new step between search and response.

### MCP bbjcpl Tool -> Existing MCP Server

The `validate_bbj_syntax` tool is added to the same `FastMCP` instance that hosts `search_bbj_knowledge`. One server, two tools. The bbjcpl subprocess runs on the host (where the MCP stdio server runs).

### Concurrent Ingestion -> Existing Pipeline

The `run_pipeline()` function in `pipeline.py` gets an async variant (`async_run_pipeline()`) that uses the concurrent embedding helper. The sync version remains for backward compatibility.

### Source URL Mapping -> Existing SearchResult

The `resolve_source_url()` function is called in the chat UI's response formatter and optionally in the API's `SearchResultItem` serialization. It reads from the URL mapping configuration.

---

## Implications for Roadmap

### Phase Ordering (Suggested)

1. **Claude API + Chat UI** -- These are coupled. The chat UI needs Claude for answer generation; Claude needs the chat UI for user interaction. Build together as the core new feature.

2. **Remote MCP (Streamable HTTP)** -- Enables shared server deployment. Low code change (mount pattern already designed in v1.4 STACK.md). Main risk is the path doubling issue (#1367).

3. **bbjcpl MCP Tool** -- Standalone addition to the MCP server. Does not depend on other v1.5 features. Quick win from existing bbjcpltool PoC.

4. **Concurrent Ingestion** -- Performance optimization. Can be done independently. Biggest code change (async pipeline variant) but well-understood pattern.

5. **Source-Balanced Ranking** -- Pure algorithm change. Can be done any time. Small, testable independently.

6. **Source URL Mapping** -- Configuration + utility function. Can be done any time. Quick win for chat UI citation links.

### Dependency Graph

```
Source URL Mapping (independent)
Source-Balanced Ranking (independent)
Concurrent Ingestion (independent)
bbjcpl MCP Tool (independent)
Remote MCP (independent)
Claude API + Chat UI (coupled -- build together)
  Claude API needs: anthropic SDK, search results
  Chat UI needs: Claude API, Jinja2 templates, htmx, SSE streaming
```

No feature blocks another. All can be developed in parallel. The suggested ordering is by user-facing impact, not technical dependency.

---

## Sources

- [Anthropic Python SDK -- PyPI](https://pypi.org/project/anthropic/) -- v0.77.0 (2026-01-29), MIT license, Python 3.9+
- [Anthropic Python SDK -- GitHub](https://github.com/anthropics/anthropic-sdk-python) -- Streaming, Citations API examples
- [Anthropic Citations API -- Official Docs](https://platform.claude.com/docs/en/docs/build-with-claude/citations) -- Stable (not beta), plain text document format, citation response structure
- [Claude Haiku 4.5 Announcement](https://www.anthropic.com/news/claude-haiku-4-5) -- Pricing, performance benchmarks
- [Migrating to Claude 4.5](https://docs.anthropic.com/en/docs/about-claude/models/migrating-to-claude-4) -- Model IDs, deprecation dates
- [MCP Python SDK -- PyPI](https://pypi.org/project/mcp/) -- v1.26.0 (2026-01-24), Streamable HTTP support since v1.8.0
- [MCP SDK Issue #1367](https://github.com/modelcontextprotocol/python-sdk/issues/1367) -- Streamable HTTP mounting on FastAPI path doubling
- [MCP SDK Issue #713](https://github.com/modelcontextprotocol/python-sdk/issues/713) -- Multi-server lifespan with AsyncExitStack
- [FastMCP HTTP Deployment](https://gofastmcp.com/deployment/http) -- Mount pattern, lifespan integration, CORS pitfalls
- [htmx -- GitHub Releases](https://github.com/bigskysoftware/htmx/releases) -- v2.0.8, SSE extension
- [htmx SSE Extension](https://htmx.org/extensions/sse/) -- Connection, event handling, reconnection
- [FastAPI Templates -- Official Docs](https://fastapi.tiangolo.com/advanced/templates/) -- Jinja2Templates, StaticFiles
- [sse-starlette -- PyPI](https://pypi.org/project/sse-starlette/) -- v3.2.0 (2026-01-17), EventSourceResponse
- [Jinja2 -- PyPI](https://pypi.org/project/Jinja2/) -- v3.1.6 (2025-03-05)
- [Ollama Python -- GitHub](https://github.com/ollama/ollama-python) -- AsyncClient, embed() API, OLLAMA_NUM_PARALLEL
- [Ollama Python -- PyPI](https://pypi.org/project/ollama/) -- v0.6.1 (2025-11-13)
- [Ollama Async Client Issue #197](https://github.com/ollama/ollama-python/issues/197) -- Concurrent request limit
- [Building AI Chat Bot with FastAPI + HTMX](https://karl-sparks.github.io/ks-personal-blog/posts/fastapi-htmx-docker-tutorial/) -- Chat UI pattern
- [FastAPI + HTMX Modern Approach](https://dev.to/jaydevm/fastapi-and-htmx-a-modern-approach-to-full-stack-bma) -- Stack validation
- [Python asyncio.Semaphore](https://docs.python.org/3/library/asyncio-sync.html) -- Official docs, context manager pattern
- [bbjcpltool PROJECT.md](/Users/beff/bbjcpltool/.planning/PROJECT.md) -- Compiler behavior: stderr parsing, -N flag, exit code always 0, path `/Users/beff/bbx/bin/bbjcpl`

---

*Research conducted 2026-02-03. All version numbers verified against PyPI, GitHub releases, and official documentation as of research date. Existing codebase analyzed for integration points. bbjcpl behavior verified from bbjcpltool proof-of-concept.*
