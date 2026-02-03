# Architecture: v1.5 Alpha-Ready Feature Integration

**Milestone:** v1.5 Alpha-Ready RAG System
**Researched:** 2026-02-03
**Confidence:** HIGH (existing codebase analysis verified, SDK docs confirmed via web research)

> **Context:** v1.4 is a working Docker Compose system (pgvector + FastAPI app at :10800, MCP server via stdio on host, Ollama on host). This document defines how v1.5 features integrate with the existing architecture -- not a redesign. Every recommendation references specific existing files and functions.

---

## 1. Existing Component Map (v1.4 Baseline)

```
                        macOS Host
                   +---------------------+
                   |   Ollama :11434     |  (Qwen3-Embedding-0.6B)
                   |   bbjcpl compiler   |  (BBj toolchain)
                   +----------+----------+
                              |
                host.docker.internal:11434
                              |
       Docker Compose Network (bbj-rag-net)
  +------------------------------------------------------+
  |                                                      |
  |  +------------------+    +------------------------+  |
  |  | db (pgvector)    |    | app (FastAPI)          |  |
  |  | pg17 + pgvector  |    |                        |  |
  |  | :5432            |<-->| uvicorn :8000          |  |
  |  |                  |    | POST /search           |  |
  |  | 50,439 chunks    |    | GET  /stats            |  |
  |  | HNSW + GIN idx   |    | GET  /health           |  |
  |  +------------------+    +------------------------+  |
  +------------------------------------------------------+
                              |
                        :10800 (mapped)
                              |
                   +----------+----------+
                   |  MCP Server (host)  |  stdio transport
                   |  bbj-mcp process    |  spawned by Claude Desktop
                   |  -> HTTP to :10800  |
                   +---------------------+
```

### Key Existing Files

| File | Role | Lines |
|------|------|-------|
| `rag-ingestion/docker-compose.yml` | Service orchestration: `db` + `app` | 62 |
| `rag-ingestion/src/bbj_rag/app.py` | FastAPI lifespan: pool, settings, ollama client on `app.state` | 89 |
| `rag-ingestion/src/bbj_rag/api/routes.py` | `/search` and `/stats` endpoints | 124 |
| `rag-ingestion/src/bbj_rag/api/deps.py` | DI: `get_conn`, `get_settings`, `get_ollama_client` | 33 |
| `rag-ingestion/src/bbj_rag/api/schemas.py` | `SearchRequest`, `SearchResponse`, `SearchResultItem` | 51 |
| `rag-ingestion/src/bbj_rag/search.py` | `hybrid_search`, `async_hybrid_search`, `dense_search`, `bm25_search` | 280 |
| `rag-ingestion/src/bbj_rag/mcp_server.py` | FastMCP `search_bbj_knowledge` tool, stdio, proxies to REST API | 111 |
| `rag-ingestion/src/bbj_rag/ingest_all.py` | Sequential ingestion CLI with resume, `--parallel` stub | 454 |
| `rag-ingestion/src/bbj_rag/embedder.py` | `OllamaEmbedder.embed_batch()`, sync, uses `ollama.embed()` | 105 |
| `rag-ingestion/src/bbj_rag/config.py` | Pydantic Settings with `BBJ_RAG_` prefix | 99 |
| `rag-ingestion/src/bbj_rag/pipeline.py` | `run_pipeline()`: parse -> intelligence -> chunk -> embed -> store | 214 |
| `rag-ingestion/sql/schema.sql` | chunks table, HNSW index, GIN indexes, `rrf_score()` function | 59 |

---

## 2. New Features and Where They Live

### 2.1 Chat UI (New Route on Existing FastAPI App)

**Decision: Add routes to the existing FastAPI app, not a separate container.**

Rationale:
- The app container already runs FastAPI with uvicorn at :8000
- Adding HTML routes is a one-line `app.include_router()` in `app.py`
- No CORS issues (same origin for API + UI)
- No new Docker service, no new port mapping
- The Chat UI needs to call `/search` and a new `/chat` endpoint -- same-origin requests are simplest

**Pattern: Jinja2 templates + HTMX + SSE for streaming**

This is the standard pattern for Python-first chat UIs without a JS build toolchain. The project already has zero frontend dependencies. HTMX adds interactivity via HTML attributes. SSE (Server-Sent Events) handles streaming Claude API responses.

**New files:**

| File | Purpose |
|------|---------|
| `src/bbj_rag/chat/__init__.py` | Chat module package |
| `src/bbj_rag/chat/routes.py` | FastAPI router: `GET /chat` (HTML page), `POST /chat/send` (SSE stream) |
| `src/bbj_rag/chat/claude.py` | Anthropic API client wrapper: RAG context assembly + streaming |
| `src/bbj_rag/chat/templates/chat.html` | Jinja2 template: chat interface with HTMX |
| `src/bbj_rag/chat/static/chat.css` | Minimal styling (Tailwind CDN or plain CSS) |

**Modified files:**

| File | Change |
|------|--------|
| `src/bbj_rag/app.py` | Add `app.include_router(chat_router)`, mount static files, add Jinja2 templates |
| `rag-ingestion/pyproject.toml` | Add `anthropic>=0.77,<1`, `sse-starlette>=2.0,<3`, `jinja2>=3.1,<4` dependencies |
| `src/bbj_rag/config.py` | Add `anthropic_api_key: str`, `anthropic_model: str` settings |
| `rag-ingestion/docker-compose.yml` | Pass `ANTHROPIC_API_KEY` env var to app container |

**Integration point:** `chat/routes.py` calls the existing `async_hybrid_search()` from `search.py` via the existing `get_conn` dependency, then passes results to the Claude API.

### 2.2 Claude API Integration (New Module, Calls Existing Search)

**Decision: New `chat/claude.py` module as the RAG-to-LLM bridge.**

The Claude API integration is the glue between retrieval and generation. It does not belong in `routes.py` (too much logic) or in `search.py` (search should not know about LLMs).

**Architecture:**

```python
# src/bbj_rag/chat/claude.py (conceptual)

from anthropic import AsyncAnthropic
from bbj_rag.search import SearchResult

async def stream_rag_response(
    query: str,
    search_results: list[SearchResult],
    client: AsyncAnthropic,
    model: str = "claude-sonnet-4-5-20250929",
) -> AsyncIterator[str]:
    """Assemble RAG context from search results, stream Claude response."""

    system_prompt = build_system_prompt()  # BBj expert instructions
    context = format_search_context(search_results)  # Results as numbered blocks

    async with client.messages.stream(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[
            {"role": "user", "content": f"{context}\n\nQuestion: {query}"}
        ],
    ) as stream:
        async for text in stream.text_stream:
            yield text
```

**Key design decisions:**

- **Async streaming:** Use `client.messages.stream()` (high-level) which returns a context manager with `.text_stream` async iterator. This maps directly to SSE `EventSourceResponse`.
- **Search results as context, not tool calls:** The chat endpoint calls `async_hybrid_search()` itself and injects results into the prompt. Claude does not call search as a tool -- that would add latency (LLM decides to search, search runs, LLM reads results) for no benefit when we always want to search.
- **System prompt with BBj expertise:** The system prompt instructs Claude to act as a BBj programming expert, cite sources from the provided context, and flag deprecated APIs. This is configuration, not code -- store in a text file or constant.
- **Citation format:** Search results include `source_url`, `title`, and `content`. The system prompt instructs Claude to reference these. The frontend renders citations as links.

**Anthropic SDK version:** v0.77.0 (Jan 2026, latest). The `AsyncAnthropic` client and `.stream()` method are stable API. HIGH confidence.

### 2.3 bbjcpl Compiler Validation (Host-Side, Not in Docker)

**Decision: Validation runs as a server-side subprocess, not client-side.**

The bbjcpl compiler is installed on the engineer's host machine (part of the BBj toolchain). It is NOT inside the Docker container. This creates an architectural boundary.

**Two validation contexts:**

| Context | Where Code Runs | Where bbjcpl Runs | How They Connect |
|---------|-----------------|-------------------|------------------|
| MCP tool responses | MCP server (host process) | Host | Direct subprocess call |
| Chat UI responses | FastAPI (Docker container) | NOT available | Cannot validate from Docker |

**Architecture for MCP validation (straightforward):**

The MCP server already runs on the host. Add a validation helper:

```python
# src/bbj_rag/validation.py (conceptual)

import subprocess
import tempfile

def validate_bbj_code(code: str, bbjcpl_path: str = "bbjcpl") -> ValidationResult:
    """Write code to temp file, run bbjcpl, parse output."""
    with tempfile.NamedTemporaryFile(suffix=".bbj", mode="w", delete=False) as f:
        f.write(code)
        f.flush()
        result = subprocess.run(
            [bbjcpl_path, f.name],
            capture_output=True, text=True, timeout=10,
        )
    return parse_compiler_output(result.stdout, result.stderr, result.returncode)
```

**New file:** `src/bbj_rag/validation.py` -- shared validation logic, used by MCP server.

**Modified file:** `src/bbj_rag/mcp_server.py` -- add `validate_bbj_code` tool that extracts code blocks from context and validates them.

**Architecture for Chat UI validation (requires design choice):**

Three options, ranked by recommendation:

1. **RECOMMENDED: Validation proxy endpoint on host MCP server.** Add a `/validate` HTTP endpoint to the MCP server (when running in HTTP mode) or create a lightweight validation microservice on the host. The chat UI calls this endpoint. This keeps bbjcpl on the host where it belongs.

2. **Alternative: Mount bbjcpl into Docker container.** Bind-mount the BBj installation directory into the app container. This works but couples the container to the host's BBj installation and adds complexity. BBj is a JVM-based toolchain; the container would need a JRE.

3. **Alternative: Client-side validation API.** Expose bbjcpl as a standalone HTTP service on the host, called directly from the browser. Requires CORS, separate port, separate process management.

**Recommendation:** Option 1. In v1.5, the MCP server is being upgraded to Streamable HTTP anyway (see 2.4). Once it has an HTTP endpoint, add a `validate_bbj_code` tool that the chat backend can call as an MCP client. This unifies the validation path: both MCP and chat use the same tool.

**Practical v1.5 approach:** For the alpha, validation in the chat UI can be deferred or made optional. The MCP server gets validation first (it runs on the host, trivial). Chat UI validation comes after remote MCP is working, since it depends on the HTTP transport being in place.

**bbjcpl capabilities (from research):**
- Accepts ASCII source files, produces tokenized BBj program files
- Reports syntax errors with BBj line number + ASCII file line number
- Reports duplicate labels and duplicate DEF FN names
- Can read from stdin (pipe mode), but type-checking options are ignored in pipe mode
- Supports `-d` (output directory) and `-x` (file extension) flags
- Has type-checking compiler options (introduced later)

**For validation purposes:** Run bbjcpl on temp files (not pipe mode) to get full error reporting including type checking. Parse stderr/stdout for error messages. A non-zero exit code means compilation failed.

### 2.4 Remote MCP (Streamable HTTP Transport)

**Decision: Keep the existing `mcp_server.py` tool definitions. Add HTTP transport as an alternative to stdio. Mount into FastAPI or run standalone.**

The current MCP server (`mcp_server.py`) is a thin REST API proxy -- it calls `POST /search` on the FastAPI app and formats the results. For remote MCP, this same tool definition needs to be accessible over HTTP.

**Two viable approaches:**

**Approach A: Mount MCP into the existing FastAPI app (RECOMMENDED)**

The official MCP SDK (v1.26.0, which this project uses) supports `mcp.streamable_http_app()` which returns a Starlette ASGI app. This can be mounted into the existing FastAPI app:

```python
# In app.py lifespan or as a mount
from bbj_rag.mcp_server import mcp

# Mount the MCP Streamable HTTP endpoint at /mcp
mcp_http = mcp.streamable_http_app()
app.mount("/mcp", mcp_http)
```

This means:
- The FastAPI app at :10800 serves both REST endpoints AND MCP Streamable HTTP at `/mcp`
- No new container, no new port, no new process
- The MCP server's tool (`search_bbj_knowledge`) needs to be refactored from REST-proxy to direct database access (since it is now running inside the same process as the FastAPI app)

**Approach B: Run MCP server standalone with HTTP transport**

```bash
# Instead of stdio:
fastmcp run src/bbj_rag/mcp_server.py --transport http --port 10801
```

This is simpler code-wise but adds another process and port to manage.

**Recommendation: Approach A (mount into FastAPI).**

**Critical refactoring required:** The current `mcp_server.py` uses `httpx` to proxy to the REST API (`POST {API_BASE}/search`). When mounted inside the FastAPI app, this creates a circular dependency (app calls itself via HTTP). The tool function must be refactored to call `async_hybrid_search()` directly, using the same `app.state.pool` and `app.state.ollama_client` that the REST routes use.

**New architecture for mcp_server.py:**

```python
# Refactored mcp_server.py (conceptual)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("bbj-knowledge", stateless_http=True)

# Tool functions will receive dependencies via a different mechanism
# when running inside FastAPI vs standalone stdio

@mcp.tool()
async def search_bbj_knowledge(query: str, ...) -> str:
    # Direct search, not HTTP proxy
    # Dependencies injected at mount time
    ...
```

**Dual transport support:** The same `mcp` object can serve stdio (when spawned by Claude Desktop for local use) OR Streamable HTTP (when mounted in FastAPI for remote use). The tool definitions are transport-agnostic. The transport is selected at runtime:
- `mcp.run(transport="stdio")` -- local Claude Desktop
- `mcp.streamable_http_app()` -- remote HTTP clients

**Modified files:**

| File | Change |
|------|--------|
| `src/bbj_rag/mcp_server.py` | Refactor from httpx proxy to direct search; export `mcp` object for mounting |
| `src/bbj_rag/app.py` | Mount `mcp.streamable_http_app()` at `/mcp` path |

**Known issue:** The official MCP SDK's `streamable_http_app()` has reported issues with mounting in FastAPI (RuntimeError with task groups, GET hanging). Verified via GitHub issues. The standalone `fastmcp` package (v2.3+) has better FastAPI integration with `http_app()` and `combine_lifespans()`. **However**, this project uses `mcp[cli]` (official SDK), not standalone `fastmcp`. Switching packages is possible but adds risk.

**Mitigation:** Test the official SDK mounting early. If it fails, fall back to running the MCP HTTP server as a separate process on a different port (Approach B). The tool definitions remain the same either way.

**Confidence: MEDIUM.** The mounting pattern is documented but has open issues. Test early.

### 2.5 Concurrent Ingestion (AsyncIO with Semaphore)

**Decision: AsyncIO with `asyncio.Semaphore` to limit Ollama concurrency. Refactor `ingest_all.py` loop, keep `pipeline.py` synchronous per-source.**

The current `ingest_all.py` already has a `--parallel` flag that prints a warning and falls back to sequential. The ingestion loop (lines 364-434) processes sources one at a time.

**What's slow:** Embedding. Each `embed_batch()` call in `pipeline.py` sends a batch of 64 texts to Ollama and waits for the response. The single Ollama instance processes them sequentially. File-based parsers (flare, pdf, mdx, bbj-source) could parse and chunk in parallel while waiting for embeddings.

**Concurrency model:**

```
Source 1: [parse] [chunk] [embed_batch] [store] [embed_batch] [store] ...
Source 2:                  [parse] [chunk] [embed_batch] [store] ...
Source 3:                                  [parse] [chunk] ...

Ollama semaphore (limit=2): Only 2 embed_batch calls active at once
DB writes: Can be concurrent (separate connections per source)
```

**Implementation approach:**

1. **Keep `run_pipeline()` synchronous.** It works correctly and is well-tested. Wrapping it in async would be high-risk for low benefit.

2. **Run each source's pipeline in a thread via `asyncio.to_thread()`:**

```python
# ingest_all.py (conceptual change)

import asyncio

async def ingest_all_async(sources, ...):
    semaphore = asyncio.Semaphore(2)  # Max 2 concurrent Ollama calls

    async def ingest_source(source):
        async with semaphore:
            return await asyncio.to_thread(
                run_single_source, source, settings, ...
            )

    results = await asyncio.gather(
        *[ingest_source(s) for s in sources],
        return_exceptions=True,
    )
```

3. **Limit Ollama concurrency with semaphore.** Qwen3-Embedding-0.6B is small but still GPU-bound. Sending more than 2-3 concurrent batch requests will not speed things up and may OOM on the GPU. A semaphore of 2 allows one batch to be embedding while another is being assembled.

**Modified files:**

| File | Change |
|------|--------|
| `src/bbj_rag/ingest_all.py` | Replace sequential loop with `asyncio.gather()` + semaphore; implement `--parallel` flag |

**What does NOT change:**
- `pipeline.py` -- remains synchronous, called via `asyncio.to_thread()`
- `embedder.py` -- `OllamaEmbedder.embed_batch()` remains synchronous (the `ollama` client is sync)
- `db.py` -- each thread gets its own connection via `get_connection_from_settings()`
- `parsers/` -- all remain synchronous generators

**Interaction with single Ollama instance:** The `ollama` Python client uses `httpx` under the hood with connection pooling. Multiple threads calling `ollama.embed()` simultaneously will result in concurrent HTTP requests to the same Ollama server. The Ollama server queues requests internally. The semaphore prevents overwhelming it.

**Expected speedup:** Moderate. The bottleneck is Ollama embedding, which is inherently sequential on a single GPU. Parallelism helps with I/O overlap (parsing files while embedding) and database writes. Expect 1.5-2x speedup for a full re-ingestion, not a dramatic improvement.

### 2.6 Source-Balanced Ranking (Python Post-Processing in search.py)

**Decision: Post-processing in Python after the existing SQL query, not a SQL modification.**

The current `hybrid_search()` in `search.py` returns results ranked purely by RRF score. If 8 of 10 results come from the Flare parser (the largest source by chunk count), results from tutorials or examples get crowded out.

**Where the reranking happens:**

```
Existing flow:
  async_hybrid_search() -> raw RRF-ranked results (SQL) -> return

New flow:
  async_hybrid_search() -> raw RRF-ranked results (SQL)
      -> source_balanced_rerank() -> return
```

**Implementation:**

```python
# src/bbj_rag/search.py (addition)

def source_balanced_rerank(
    results: list[SearchResult],
    limit: int,
    max_per_source: int = 3,
) -> list[SearchResult]:
    """Rerank results to ensure source diversity.

    Round-robin by source (doc_type), taking top results from each
    source until limit is reached. Falls back to original ranking
    for remaining slots.
    """
    by_source: dict[str, list[SearchResult]] = {}
    for r in results:
        by_source.setdefault(r.doc_type, []).append(r)

    balanced: list[SearchResult] = []
    # Round-robin: take one from each source, repeat
    while len(balanced) < limit:
        added_any = False
        for source_results in by_source.values():
            if source_results and len([b for b in balanced if b.doc_type == source_results[0].doc_type]) < max_per_source:
                balanced.append(source_results.pop(0))
                added_any = True
                if len(balanced) >= limit:
                    break
        if not added_any:
            break

    return balanced
```

**Why Python, not SQL:** The SQL query already does the heavy lifting (HNSW index scan + BM25 + RRF). Adding source-balancing logic in SQL would mean modifying the already-complex RRF query with window functions and CTEs, making it harder to test and tune. The Python layer receives ~20 results and picks the best ~10 with diversity constraints. This is a trivial operation on a small list.

**Modified files:**

| File | Change |
|------|--------|
| `src/bbj_rag/search.py` | Add `source_balanced_rerank()` function |
| `src/bbj_rag/api/routes.py` | Call `source_balanced_rerank()` after `async_hybrid_search()` |
| `src/bbj_rag/api/schemas.py` | Optionally add `balanced: bool = True` to `SearchRequest` |

**What does NOT change:** The SQL queries in `hybrid_search()` and `async_hybrid_search()` remain untouched. The database schema, indexes, and `rrf_score()` function are unchanged.

**Fetch more, then filter:** To have enough results for balancing, the SQL query should return more results than the final limit. Request `limit * 3` from SQL, then balance down to `limit`. Modify the `limit` parameter passed to the SQL query, not the SQL itself.

### 2.7 Source URL Mapping (Configuration + Runtime Transformation)

**Decision: URL mapping table in `sources.toml`, runtime transformation in a new utility function.**

The current `source_url` values are internal identifiers:
- `flare://Content/bbjobjects/Window/bbjwindow.htm`
- `pdf://GuideToGuiProgrammingInBBj.pdf#section-name`
- `mdx-dwc://docs/getting-started.mdx`
- `file://samples/example.bbj`
- `https://basis.cloud/advantage/article-title` (already real URLs)
- `https://documentation.basis.cloud/...` (already real URLs)

For the chat UI, users need clickable links. Some source_url values are already real URLs; others need mapping.

**Mapping table (in sources.toml or a new config):**

```toml
[url_mapping]
"flare://" = "https://documentation.basis.cloud/BASISHelp/WebHelp/"
"pdf://" = ""  # No web URL for PDF content
"mdx-dwc://" = "https://basishub.github.io/bbj-dwc-tutorial/"
"mdx-beginner://" = "https://basishub.github.io/bbj-beginner-tutorial/"
"mdx-db-modernization://" = "https://basishub.github.io/bbj-db-modernization-tutorial/"
"file://" = ""  # No web URL for local source files
```

**Implementation:**

```python
# src/bbj_rag/url_mapping.py

def to_public_url(source_url: str, mapping: dict[str, str]) -> str | None:
    """Convert internal source_url to a public web URL.

    Returns None if no mapping exists (e.g., PDF or local files).
    """
    for prefix, base_url in mapping.items():
        if source_url.startswith(prefix):
            if not base_url:
                return None
            relative = source_url[len(prefix):]
            return f"{base_url}{relative}"
    # Already a real URL (wordpress, web-crawl)
    if source_url.startswith("http"):
        return source_url
    return None
```

**Where it's applied:**
- Chat UI responses: `chat/claude.py` maps URLs before injecting context into Claude prompt and before rendering citations
- API responses: Optionally add a `public_url` field to `SearchResultItem`
- MCP responses: `mcp_server.py` already shows `source_url` -- could add mapped URL

**New files:**

| File | Purpose |
|------|---------|
| `src/bbj_rag/url_mapping.py` | `to_public_url()` function + mapping loader |

**Modified files:**

| File | Change |
|------|--------|
| `src/bbj_rag/config.py` or `sources.toml` | Add URL mapping configuration |
| `src/bbj_rag/api/schemas.py` | Add optional `public_url: str | None` to `SearchResultItem` |

**NOT a database migration.** The `source_url` column stays as-is. Mapping is a pure runtime transformation. This avoids re-ingestion and keeps the internal identifiers stable for deduplication and cleaning.

---

## 3. Data Flow: Chat Query End-to-End

```
User types question in browser
        |
        v
[1] Browser sends POST /chat/send  (HTMX hx-post)
    Body: { "query": "How do I create a BBjGrid?" }
        |
        v
[2] chat/routes.py::send_message()
    |
    |-- [2a] Embed query via app.state.ollama_client
    |         ollama_client.embed(model="qwen3-embedding:0.6b", input=query)
    |         Returns: list[float] (1024-dim vector)
    |
    |-- [2b] Search via async_hybrid_search()
    |         Uses app.state.pool connection
    |         SQL: dense (HNSW) + BM25 (GIN) -> RRF fusion
    |         Returns: list[SearchResult] (top 30)
    |
    |-- [2c] Source-balanced rerank
    |         source_balanced_rerank(results, limit=10, max_per_source=3)
    |         Returns: list[SearchResult] (top 10, diverse)
    |
    |-- [2d] Map source URLs
    |         to_public_url(r.source_url) for each result
    |         Returns: list of (SearchResult, public_url) pairs
    |
    |-- [2e] Build Claude API request
    |         System prompt: "You are a BBj programming expert..."
    |         Context: formatted search results with titles + content
    |         User message: original query
    |
    v
[3] Stream Claude response via SSE
    |
    |-- AsyncAnthropic.messages.stream(
    |       model="claude-sonnet-4-5-20250929",
    |       system=system_prompt,
    |       messages=[{"role": "user", "content": context + query}],
    |       max_tokens=2048,
    |   )
    |
    |-- For each text chunk from stream.text_stream:
    |       yield SSE event: { "data": chunk }
    |
    v
[4] EventSourceResponse streams to browser
    |
    v
[5] Browser (HTMX SSE extension) appends text to chat container
    |
    |-- Markdown rendered client-side (lightweight: marked.js or similar)
    |-- Citations rendered as links using mapped source URLs
    |-- Code blocks with syntax highlighting
    |
    v
[6] Stream ends -> final SSE event with citations summary
    |
    |-- Sources used: [title1](url1), [title2](url2), ...
    |-- Optional: "Validate code?" button (if response contains BBj code)
```

**Latency budget:**
- Step 2a (embedding): ~50ms (Qwen3 0.6B is fast)
- Step 2b (search): ~100ms (HNSW + BM25 + RRF)
- Step 2c-2d (rerank + URL map): ~1ms (in-memory, 10-30 items)
- Step 2e (API call setup): ~1ms
- Step 3 (first token from Claude): ~500-1500ms (network to Anthropic API)
- Step 3 (streaming): tokens arrive every ~20-50ms
- **Time to first visible token: ~700-1700ms**

---

## 4. Data Flow: bbjcpl Validation

### 4A: MCP Tool Validation (Host Process)

```
Claude generates BBj code in response
        |
        v
[1] Claude calls validate_bbj_code MCP tool
    Input: { "code": "REM BBj example\nPRINT 'Hello'\n" }
        |
        v
[2] mcp_server.py::validate_bbj_code()
    |
    |-- Write code to tempfile.NamedTemporaryFile(suffix=".bbj")
    |-- subprocess.run(["bbjcpl", tempfile_path], capture_output=True)
    |-- Parse stdout/stderr for error messages
    |-- Delete tempfile
    |
    v
[3] Return validation result to Claude
    "Compilation successful" or "Line 5: Syntax error: ..."
        |
        v
[4] Claude incorporates result into response
    "The code compiles successfully." or "I found an error on line 5..."
```

**Requirements:**
- `bbjcpl` must be on the host's PATH (or configured via `BBJ_BBJCPL_PATH` env var)
- BBj must be installed on the host machine
- 10-second timeout to prevent hanging on malformed input

### 4B: Chat UI Validation (Requires Host Proxy)

```
User clicks "Validate" on a code block in chat UI
        |
        v
[1] Browser sends POST /chat/validate
    Body: { "code": "REM example\n..." }
        |
        v
[2] chat/routes.py::validate_code()
    |
    |-- OPTION A (if MCP HTTP is mounted):
    |   Call mcp.search_bbj_knowledge or direct function
    |   But bbjcpl is NOT in the Docker container!
    |
    |-- OPTION B (recommended for v1.5):
    |   Forward to a host-side validation endpoint
    |   httpx.post("http://host.docker.internal:10801/validate", ...)
    |   Where 10801 is a lightweight validation service on the host
    |
    v
[3] Return result to browser
    SSE or JSON: { "valid": false, "errors": [...] }
```

**v1.5 practical recommendation:** For the alpha:
1. Implement bbjcpl validation in the MCP server first (trivial, host-side)
2. For chat UI, add a small FastAPI validation service on the host (separate from Docker)
3. The chat UI calls this service via `host.docker.internal`
4. Alternatively, defer chat UI validation to a fast-follow and focus on MCP validation for alpha

---

## 5. Data Flow: Remote MCP (Streamable HTTP)

```
Remote Claude Desktop / Claude Code (on another machine on LAN)
        |
        v
[1] HTTP POST to http://server-ip:10800/mcp
    MCP protocol messages (JSON-RPC over Streamable HTTP)
        |
        v
[2] FastAPI app routes to mounted MCP Streamable HTTP app
    app.mount("/mcp", mcp.streamable_http_app())
        |
        v
[3] MCP protocol handler invokes search_bbj_knowledge tool
    |
    |-- Refactored tool calls async_hybrid_search() directly
    |   (no HTTP proxy to itself)
    |-- Uses app.state.pool for DB connection
    |-- Uses app.state.ollama_client for embedding
    |
    v
[4] Tool returns formatted text results
        |
        v
[5] MCP protocol sends response back over HTTP
        |
        v
[6] Remote Claude Desktop renders results
```

**Key change from v1.4:** The MCP server switches from "external proxy to REST API" to "internal direct access to search functions." This eliminates the HTTP round-trip and makes the MCP server a first-class citizen of the FastAPI app.

**Backward compatibility for local stdio:** Keep `main()` entry point in `mcp_server.py` that runs `mcp.run(transport="stdio")`. When run standalone (`bbj-mcp` CLI), it uses stdio. When mounted in FastAPI, it uses Streamable HTTP. Same tool definitions, different transport.

---

## 6. Build Order (Dependency-Driven)

Build features in this order based on dependencies:

### Phase 1: Source URL Mapping + Source-Balanced Ranking

**Why first:** These are pure additions with zero risk to existing functionality. No new dependencies, no new containers, no API keys needed. They improve search quality for all consumers (API, MCP, chat).

- Add `url_mapping.py` -- standalone utility, no dependencies
- Add `source_balanced_rerank()` to `search.py` -- pure function
- Wire into `/search` endpoint -- one-line addition to `routes.py`
- **Test:** Existing `/search` endpoint returns balanced, URL-mapped results

### Phase 2: Chat UI + Claude API Integration

**Why second:** This is the marquee v1.5 feature. Depends on URL mapping (for citations) and balanced ranking (for quality results).

- Add `anthropic`, `sse-starlette`, `jinja2` dependencies
- Add `ANTHROPIC_API_KEY` to config and docker-compose
- Build `chat/claude.py` -- Claude API wrapper with RAG context
- Build `chat/routes.py` -- SSE streaming endpoint
- Build `chat/templates/chat.html` -- HTMX chat interface
- Wire into `app.py` -- router + static files mount
- **Test:** Open browser to `http://localhost:10800/chat`, ask a question, see streaming response

### Phase 3: Remote MCP (Streamable HTTP)

**Why third:** Depends on the FastAPI app being stable (Phase 2 validates this). Requires MCP server refactoring.

- Refactor `mcp_server.py` from httpx proxy to direct search
- Mount `mcp.streamable_http_app()` in `app.py`
- Test dual transport (stdio still works for local)
- **Test:** Configure remote Claude Desktop to connect via HTTP

### Phase 4: bbjcpl Validation

**Why fourth:** The MCP refactoring (Phase 3) establishes the pattern for adding tools. Validation is a new tool on the refactored MCP server.

- Add `validation.py` with bbjcpl subprocess wrapper
- Add `validate_bbj_code` tool to MCP server
- Add validation proxy endpoint for chat UI
- **Test:** Claude uses the tool; chat UI validates code blocks

### Phase 5: Concurrent Ingestion

**Why last:** Ingestion is a batch operation, not a user-facing feature. It's an optimization that doesn't block alpha readiness. The `--parallel` flag already exists as a stub.

- Implement `asyncio.gather()` + semaphore in `ingest_all.py`
- **Test:** `bbj-ingest-all --parallel` runs faster than sequential

---

## 7. What Does NOT Change

These components require zero modification in v1.5:

| Component | Why Unchanged |
|-----------|---------------|
| `sql/schema.sql` | No new columns, no new tables, no schema migration needed |
| `db.py` | Connection management, bulk insert, content-hash dedup -- all unchanged |
| `models.py` | `Document`, `Chunk` data models remain transport-agnostic |
| `chunker.py` | Pure function, no I/O dependencies |
| `pipeline.py` | `run_pipeline()` is not modified; concurrent ingestion wraps it |
| `intelligence/` | Classification logic unchanged |
| `parsers/` | All 7 parsers (flare, pdf, mdx, bbj-source, wordpress-advantage, wordpress-kb, web-crawl) unchanged |
| `embedder.py` | `OllamaEmbedder` and `OpenAIEmbedder` unchanged |
| `health.py` | Health check endpoint unchanged |
| `source_config.py` | Source loading and validation unchanged (URL mapping is additive) |
| `startup.py` | Startup validation unchanged |
| Docker `db` service | pgvector container configuration unchanged |

**The v1.4 system continues to work exactly as-is.** New features are additive routes, new modules, and refactored MCP transport. If any new feature breaks, the existing `/search`, `/stats`, `/health` endpoints and the MCP stdio server are unaffected.

---

## 8. New Dependencies

| Package | Version | Purpose | Where Used |
|---------|---------|---------|------------|
| `anthropic` | >=0.77,<1 | Claude API client for chat | `chat/claude.py` |
| `sse-starlette` | >=2.0,<3 | `EventSourceResponse` for SSE streaming | `chat/routes.py` |
| `jinja2` | >=3.1,<4 | HTML template rendering | `chat/routes.py`, `chat/templates/` |

**Note:** `jinja2` may already be installed as a transitive dependency of FastAPI, but should be declared explicitly. The `anthropic` package is already in the dev dependencies (`openai` is there), suggesting API client patterns are established in this project.

---

## 9. Container Architecture (v1.5)

```
                         macOS Host
                    +------------------+
                    |  Ollama :11434   |
                    |  bbjcpl          |
                    |                  |
                    |  MCP stdio       |  (still works for local Claude Desktop)
                    |  Validation svc  |  (optional, for chat UI bbjcpl proxy)
                    +--------+---------+
                             |
               host.docker.internal:11434
                             |
        Docker Compose Network (bbj-rag-net)
   +-------------------------------------------------------------+
   |                                                             |
   |  +------------------+      +--------------------------+    |
   |  | db (pgvector)    |      | app (FastAPI)            |    |
   |  | pg17 + pgvector  |      |                          |    |
   |  | :5432            |<---->| GET  /health             |    |
   |  |                  |      | POST /search             |    |
   |  | 50,439 chunks    |      | GET  /stats              |    |
   |  +------------------+      | GET  /chat        (NEW)  |    |
   |                             | POST /chat/send   (NEW)  |    |
   |                             | POST /mcp         (NEW)  |    |
   |                             +--------------------------+    |
   +-------------------------------------------------------------+
                              |
                        :10800 (mapped)
```

**Changes from v1.4:**
- Three new routes on the same app container: `/chat`, `/chat/send`, `/mcp`
- No new containers
- No new port mappings
- `ANTHROPIC_API_KEY` env var added to app container

---

## 10. Risk Assessment

| Integration | Risk | Mitigation |
|-------------|------|------------|
| MCP SDK mounting in FastAPI | MEDIUM -- known issues in GitHub | Test early; fall back to standalone HTTP process |
| Claude API streaming via SSE | LOW -- well-documented pattern | Standard `sse-starlette` + `anthropic` SDK |
| bbjcpl in Docker | N/A -- don't put it in Docker | Validation stays host-side |
| Concurrent ingestion + Ollama | LOW -- semaphore limits concurrency | Start with semaphore=2, tune based on GPU |
| HTMX chat UI complexity | LOW -- no JS build step | Server-rendered HTML fragments, progressive enhancement |
| Source-balanced reranking | LOW -- pure Python post-processing | Does not touch SQL or database |
| URL mapping correctness | LOW -- static configuration | Verify mapping for each source type manually |

---

## 11. Confidence Assessment

| Area | Confidence | Rationale |
|------|-----------|-----------|
| Chat UI architecture | HIGH | FastAPI + Jinja2 + HTMX + SSE is a well-established pattern; multiple 2025 tutorials confirm it. No JS build step needed. |
| Claude API integration | HIGH | Anthropic Python SDK v0.77.0 confirmed. `AsyncAnthropic.messages.stream()` with `.text_stream` is stable, documented API. |
| bbjcpl validation | MEDIUM | bbjcpl command-line behavior confirmed from official docs, but exact exit codes and error message format need testing with actual compiler. Pipe mode drops type-checking. |
| Remote MCP (mounted) | MEDIUM | Official SDK supports `streamable_http_app()` but GitHub issues report mounting problems. Standalone HTTP is a reliable fallback. |
| Concurrent ingestion | HIGH | Standard `asyncio.Semaphore` + `asyncio.to_thread()` pattern. Well-documented, no edge cases for this use case. |
| Source-balanced ranking | HIGH | Pure Python list manipulation. Trivial to implement and test. |
| Source URL mapping | HIGH | Configuration-based string transformation. No database changes. |

---

## Sources

- [FastMCP Running Server (transports)](https://gofastmcp.com/deployment/running-server) -- stdio, HTTP, SSE transport options
- [FastMCP + FastAPI Integration](https://gofastmcp.com/integrations/fastapi) -- `http_app()` mounting, `combine_lifespans()`
- [MCP SDK GitHub Issues](https://github.com/modelcontextprotocol/python-sdk/issues/1367) -- `streamable_http_app()` mounting issues
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) -- v0.77.0, streaming API
- [Anthropic Streaming Docs](https://docs.anthropic.com/en/api/messages-streaming) -- SSE event types, `.stream()` helper
- [sse-starlette](https://github.com/sysid/sse-starlette) -- EventSourceResponse for FastAPI
- [bbjcpl Documentation](https://documentation.basis.com/BASISHelp/WebHelp/util/bbjcpl_bbj_compiler.htm) -- Compiler CLI, error reporting
- [FastAPI + HTMX Chat UI Pattern](https://towardsdatascience.com/javascript-fatigue-you-dont-need-js-to-build-chatgpt/) -- Full pattern with SSE streaming
- [Asyncio Semaphore for Rate Limiting](https://rednafi.com/python/limit-concurrency-with-semaphore/) -- Standard concurrency pattern
