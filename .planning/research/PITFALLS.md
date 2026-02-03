# Domain Pitfalls: v1.5 Alpha-Ready Feature Integration

**Domain:** Adding chat UI, Claude API, compiler validation, remote MCP, concurrent ingestion, and source-balanced ranking to a working Docker-based RAG system
**Researched:** 2026-02-03
**Focus:** Common mistakes when adding these specific features to the existing v1.4 system. Not generic advice -- every pitfall references existing files, functions, and architectural decisions.
**Supersedes:** Previous PITFALLS.md covered v1.4 Docker deployment pitfalls (config.toml, Ollama connectivity, shm-size, etc.). Those issues are resolved in the shipped v1.4 system. This document covers NEW pitfalls specific to v1.5 feature additions.

---

## Critical Pitfalls (Blockers)

Mistakes that break the system, corrupt data, or require architectural rework. These block alpha testing.

### C-1: SSE Newline Corruption Destroys Markdown in Streamed Chat Responses

**What goes wrong:** The chat UI uses HTMX's SSE extension to stream Claude API responses to the browser. SSE data frames are newline-delimited -- each `data:` line is a separate event payload. When Claude's response contains multi-line content (Markdown paragraphs, code blocks, BBj examples), the newlines within the content split a single logical message across multiple SSE frames. The HTMX SSE extension treats each frame as a complete HTML fragment, producing garbled output where every line of a code block appears as a separate swap operation.

**Why it happens:**
- The SSE protocol spec requires `data:` fields to be single-line. Multi-line data requires sending each line as a separate `data:` field within the same event (the browser concatenates them with `\n`).
- Most SSE tutorials show simple single-line messages. Streaming Claude API responses produces multi-line content including code blocks, lists, and paragraphs.
- The HTMX SSE extension subscribes to named events and swaps the event data into the DOM. If the data contains raw newlines, the browser's EventSource parser may fragment it.
- The Towards Data Science article on HTMX chatbots explicitly warns: "The Event Source that HTMX SSE wraps uses a format of data messages that are new line delimited. This means for streaming markdown, the markdown gets corrupted and cannot be formatted."

**Consequences:**
- BBj code examples (the primary value of this system) render as garbled single-line fragments
- Engineers see broken output on their first interaction and lose confidence
- Markdown formatting (headers, lists, code fences) is destroyed
- The chat appears fundamentally broken, not just cosmetically imperfect

**Warning signs:**
- Single-line responses stream correctly, but any response with code blocks or lists renders incorrectly
- Code blocks appear as separate disconnected lines instead of a formatted block
- Newlines within `data:` payloads visible in browser DevTools Network tab

**Prevention:**
- Base64-encode each SSE data payload, decode on the client. This is the approach documented in the HTMX chatbot article. The tradeoff is ~33% larger payloads, which is negligible for text.
- Alternatively, use JSON encoding: `data: {"html": "<escaped html>"}` where newlines are escaped as `\n` in JSON. Parse on the client with a small JS handler.
- Do NOT use raw `hx-swap` with SSE for multi-line content. Instead, use a custom `htmx:sseMessage` event handler that processes the decoded content.
- Test with a response that includes a multi-line BBj code block BEFORE building the full chat UI. This is the first thing to validate.

**Severity:** BLOCKER -- First-impression killer. If the first query returns garbled code, alpha testers will not trust the system.

**Phase:** Chat UI implementation (validate SSE + multi-line content encoding FIRST, before building templates)

**Confidence:** HIGH -- Confirmed by multiple HTMX SSE implementations and explicitly documented as a known issue.

---

### C-2: Claude API Context Window Stuffing Degrades Answer Quality

**What goes wrong:** The chat endpoint retrieves RAG results and sends them to Claude as context. If too many results are included (or results are too long), several problems emerge: Claude's attention dilutes across irrelevant chunks ("lost in the middle" effect), costs increase non-linearly, and the system prompt instructions get crowded out by context volume. With 10 results at ~400 tokens each, you use ~4K context tokens -- manageable. But if the source-balanced reranker requests 30 results from SQL (to ensure diversity), or if chunk sizes vary widely, context can balloon to 15-20K tokens.

**Why it happens:**
- The architecture calls for `async_hybrid_search()` to over-fetch (e.g., `limit * 3` = 30 results) for the source-balanced reranker to select from. If the reranker passes all 30 to Claude instead of filtering to 10, context is 3x larger than intended.
- The current chunks table has no `token_count` column. Chunk sizes nominally target 400 tokens but vary from 50 to 800+ tokens depending on heading-aware splitting boundaries.
- Anthropic's research confirms that "mechanically stuffing lengthy text into an LLM's context window scatters the model's attention, significantly degrading answer quality through the 'Lost in the Middle' or 'information flooding' effect."
- The temptation is to include MORE context "just in case" -- but research shows diminishing and even negative returns beyond 5-8 focused chunks.

**Consequences:**
- Answers become vague, generic, or fail to cite the most relevant source
- Claude may hallucinate connections between unrelated chunks
- Per-query costs increase (token pricing is linear, but attention computation is quadratic)
- Response latency increases (more input tokens = slower time-to-first-token)

**Warning signs:**
- Answers cite the first and last sources but ignore middle sources
- Generic answers despite highly relevant chunks being in the context
- Increasing response latency as more results are included
- Per-query costs exceeding $0.05 (expected: $0.02-0.04 at Haiku pricing)

**Prevention:**
- Hard cap: Send at most 8-10 search results to Claude, regardless of how many the reranker considers.
- Implement the source-balanced reranker as a FILTER (selects 8-10 from 30), not a pass-through.
- Add a token budget: sum approximate token counts of selected results, stop adding results when budget (~4K tokens) is reached.
- Place the most relevant results FIRST in the context (Claude attends better to early context).
- Monitor actual context sizes during alpha. Log `input_tokens` from the Claude API response metadata for every query.
- Consider using Anthropic's Citations API with `citations.enabled=True` on search result content blocks, which enables Claude to cite specific passages without needing the entire chunk to be in its active attention.

**Severity:** BLOCKER -- Degraded answer quality means the system fails at its primary purpose. Engineers get vague answers and conclude the RAG approach does not work.

**Phase:** Claude API integration (enforce context budget from the start)

**Confidence:** HIGH -- "Lost in the middle" is well-documented (Liu et al. 2023, confirmed by Anthropic's contextual retrieval paper). The token budget approach is standard RAG practice.

---

### C-3: MCP Refactoring Creates Self-Referential Loop When Mounted in FastAPI

**What goes wrong:** The current `mcp_server.py` (line 91) calls the REST API via `httpx.AsyncClient().post(f"{API_BASE}/search", json=payload)`. When this MCP server is mounted inside the FastAPI app via `app.mount("/mcp", mcp.streamable_http_app())`, the MCP tool function calls the app's own `/search` endpoint via HTTP -- a self-referential loop. Under uvicorn's single-worker default, this deadlocks: the inbound MCP request holds the only worker thread, which then makes an outbound HTTP request that needs a worker thread to handle.

**Why it happens:**
- The v1.4 architecture intentionally made the MCP server a thin REST proxy. This was correct for stdio transport (MCP runs as a separate process on the host).
- The v1.5 architecture mounts the MCP server inside the FastAPI app for Streamable HTTP. The httpx proxy pattern no longer works because the server is calling itself.
- Even with multiple uvicorn workers, this is fragile: it wastes a worker on internal HTTP overhead and creates a circular dependency.
- The ARCHITECTURE.md (Section 2.4) correctly identifies this: "The tool function must be refactored to call `async_hybrid_search()` directly."

**Consequences:**
- MCP requests hang indefinitely (deadlock under single worker)
- With multiple workers, MCP requests are 2x slower than necessary (HTTP round-trip to self)
- If the internal HTTP call times out (httpx default 30s), the MCP tool returns an error
- Difficult to debug: the request appears to enter the MCP handler but never returns

**Warning signs:**
- MCP tool invocations hang when the server is running as mounted Streamable HTTP
- MCP tools work fine when running as standalone stdio process
- uvicorn logs show the MCP handler receiving the request but no corresponding /search access log entry (because the worker is blocked)

**Prevention:**
- Refactor `mcp_server.py` to call `async_hybrid_search()` directly, not via HTTP. This requires:
  1. The MCP tool function to access the same `app.state.pool` and `app.state.ollama_client` as the REST routes
  2. A dependency injection mechanism that works for both stdio (standalone) and HTTP (mounted) modes
  3. For stdio mode, the MCP server can continue using httpx (separate process, no deadlock)
- Pattern: Create a `SearchService` class that encapsulates embedding + search. Both REST routes and MCP tools use it. In FastAPI, inject via `app.state`. In stdio, inject a version that uses httpx.
- Test: Verify that a remote Claude Desktop can call `search_bbj_knowledge` via Streamable HTTP and get results within 2 seconds (embedding + search, no HTTP round-trip overhead).

**Severity:** BLOCKER -- Remote MCP is non-functional if this is not addressed. Engineers on the shared server cannot use Claude Desktop with the RAG system.

**Phase:** Remote MCP implementation (must be addressed as part of the MCP refactoring, not as an afterthought)

**Confidence:** HIGH -- The deadlock under single-worker uvicorn is deterministic. The httpx self-referential call pattern is a known anti-pattern in ASGI applications.

---

### C-4: ANTHROPIC_API_KEY Exposed in Shared Deployment

**What goes wrong:** The chat UI runs on a shared server. The `ANTHROPIC_API_KEY` is passed as an environment variable to the Docker container. Every chat query uses this key. There is no per-user authentication (alpha on trusted network). If ANY engineer or script makes excessive requests (accidental infinite loop, load testing, copy-paste automation), the API key accumulates charges against the organization's Anthropic account. There is no rate limiting, no per-user quotas, and no spending alerts within the application.

**Why it happens:**
- The alpha explicitly excludes authentication (PROJECT.md: "No auth needed")
- The Anthropic API key is a shared secret for the entire deployment
- There is no application-level rate limiting in the FastAPI app
- The Anthropic SDK's built-in retry logic (2 retries with backoff) means a 429 from Anthropic is silently retried, masking rate limit signals
- Engineers testing the system may run automated scripts against the chat endpoint

**Consequences:**
- Unexpected API bill (uncapped, Anthropic charges per-token)
- If the key hits the organization's rate limit, ALL users are affected simultaneously
- A runaway script could exhaust the monthly budget in hours
- If the key is leaked (shared server, environment variable), unauthorized usage

**Warning signs:**
- Rising costs in Anthropic dashboard without corresponding alpha usage
- 429 errors in server logs indicating rate limiting
- API key visible in `docker inspect` output or Docker Compose environment

**Prevention:**
- Set `max_tokens=2048` on every Claude API call (caps per-response cost)
- Add application-level rate limiting: max 30 requests per minute globally, implemented via a simple in-memory counter in FastAPI middleware
- Log every Claude API call with `input_tokens` and `output_tokens` to estimate running costs
- Set up Anthropic workspace spending alerts ($50/day, $200/month) via the Anthropic console BEFORE deploying
- Store the API key in a `.env` file that is NOT committed to git (already the case with `.env.example`)
- Consider using Claude Haiku 4.5 ($1/M input, $5/M output) instead of Sonnet ($3/$15) for alpha -- 3x cost reduction with acceptable quality for RAG Q&A

**Severity:** BLOCKER -- Not a technical failure, but an operational one. Uncapped API costs on a shared key with no rate limiting is a production incident waiting to happen.

**Phase:** Claude API integration (set rate limits and spending alerts BEFORE deploying to shared server)

**Confidence:** HIGH -- This is a well-known operational pitfall for any shared LLM API deployment. The Anthropic SDK does not enforce any client-side spending limits.

---

### C-5: MCP SDK Mounting Issues Break Streamable HTTP in FastAPI

**What goes wrong:** The official MCP Python SDK's `streamable_http_app()` method has reported issues when mounted as a sub-application in FastAPI. Known problems include: RuntimeError with task groups during concurrent requests, GET requests hanging indefinitely for SSE notifications, and path doubling where the endpoint becomes `/mcp/mcp` instead of `/mcp`.

**Why it happens:**
- The MCP SDK's Streamable HTTP implementation uses `anyio` task groups internally, which can conflict with FastAPI's own ASGI lifecycle management
- Path doubling occurs because `streamable_http_app()` returns an ASGI app with an internal `/mcp` path. Mounting it at `/mcp` in FastAPI produces `/mcp/mcp` (GitHub issue #1367)
- Session management via `Mcp-Session-Id` header may conflict with FastAPI middleware
- The ARCHITECTURE.md notes this risk at MEDIUM confidence: "The official MCP SDK has reported issues with mounting in FastAPI"

**Consequences:**
- Remote MCP via Streamable HTTP is non-functional
- Engineers cannot configure Claude Desktop to connect to the shared server
- Fallback to standalone MCP process requires a separate port and process management

**Warning signs:**
- HTTP POST to `/mcp` returns 404 (path doubling -- try `/mcp/mcp`)
- GET request to the MCP endpoint hangs (SSE notification stream issue)
- RuntimeError in server logs referencing task groups or cancelled scopes
- Session initialization succeeds but subsequent tool calls fail

**Prevention:**
- Test MCP mounting EARLY in the development process (before building the chat UI)
- Try mounting at root first: `app.mount("/", mcp.streamable_http_app())` -- MCP endpoint at `/mcp`, avoids path doubling. Verify this does not conflict with FastAPI's own routes.
- If root mounting conflicts, try `mcp.streamable_http_app(streamable_http_path="/")` and mount at `/mcp`
- If SDK mounting fails entirely, fall back to running the MCP server as a standalone process: `mcp.run(transport="streamable-http", host="0.0.0.0", port=10801)`. This means a second port (10801) but works reliably.
- Consider using the standalone `fastmcp` package (v2.3+) which has `http_app()` and `combine_lifespans()` specifically designed for FastAPI integration. However, this is a different package from the official `mcp` SDK and may introduce its own issues.
- Pin `mcp>=1.25,<2` and check the changelog for mounting fixes before upgrading

**Severity:** BLOCKER for remote MCP access. The chat UI works independently, so the system is not entirely broken, but the MCP use case (Claude Desktop integration for the team) is blocked.

**Phase:** Remote MCP implementation (test mounting approach as the FIRST task in this phase, before refactoring tool functions)

**Confidence:** MEDIUM -- The mounting issues are reported in GitHub issues but may be fixed in newer SDK versions. The standalone fallback is reliable.

---

## Integration Pitfalls (Degraded)

Mistakes that leave the system functional but with degraded quality, performance, or user experience. Engineers can use it but results are suboptimal.

### I-1: HTMX SSE Extension Error Handling Silently Retries on Failure

**What goes wrong:** The HTMX SSE extension (`hx-ext="sse"`) does not gracefully handle HTTP error responses. If the Claude API returns a 500, 429 (rate limit), or 529 (overloaded), the SSE endpoint returns a non-200 status. The standard HTMX request lifecycle respects error status codes, but the SSE extension tries to reconnect indefinitely. The user sees the chat "working" (spinner spinning) but never receives a response or error message.

**Why it happens:**
- The browser EventSource API automatically reconnects on connection loss -- this is by design for long-running SSE streams
- HTMX's SSE extension inherits this reconnection behavior
- A documented HTMX GitHub issue (#134) states: "HTMX SSE extension doesn't know how to handle errors"
- The Claude API can return mid-stream errors (the stream starts with HTTP 200, but an error event arrives later). These bypass HTTP status code error handling entirely.

**Consequences:**
- User waits indefinitely for a response that will never arrive
- No error message displayed in the UI
- Browser DevTools shows repeated connection attempts in the Network tab
- The experience feels buggy and unreliable

**Warning signs:**
- Chat appears to be "thinking" forever after Claude API errors
- Browser console shows EventSource reconnection attempts
- Server logs show Claude API errors but the UI shows nothing

**Prevention:**
- Use `sse-close="complete"` to send a termination event that closes the EventSource when the response is done. Without this, the connection stays open.
- Implement error events: send `event: error\ndata: {"message": "API error"}\n\n` from the server when the Claude API fails. Handle this event on the client to display an error message.
- Set a client-side timeout: if no SSE event arrives within 30 seconds, display "Response timed out. Please try again."
- For mid-stream Claude API errors, catch `anthropic.APIError` in the streaming generator and yield an error SSE event before closing the stream.
- Test: Temporarily set an invalid API key and verify the UI displays an error message (not infinite spinner).

**Severity:** DEGRADED -- System works for successful requests but fails silently on errors. Alpha testers will encounter this during rate limiting or API outages.

**Phase:** Chat UI implementation (implement error handling in the SSE streaming endpoint)

**Confidence:** HIGH -- Confirmed via HTMX GitHub issues and SSE extension documentation.

---

### I-2: bbjcpl Subprocess Hangs on Malformed Input Without Timeout

**What goes wrong:** The `validate_bbj_syntax` MCP tool runs `bbjcpl` as a subprocess. If bbjcpl encounters certain malformed inputs (incomplete programs, binary data, extremely long lines), it may hang waiting for input on stdin or enter an infinite processing loop. Without a subprocess timeout, the MCP tool call never returns, blocking the Claude conversation.

**Why it happens:**
- The bbjcpltool PoC uses `subprocess.run()` with `capture_output=True` but the timeout configuration needs to be explicit
- bbjcpl is designed for well-formed BBj source files. Claude-generated code may include partial programs, pseudocode mixed with BBj, or code fragments without proper program structure
- If bbjcpl reads from stdin (pipe mode fallback), it blocks waiting for EOF
- The ARCHITECTURE.md specifies a 10-second timeout, but this must be enforced at the subprocess level AND at the MCP tool level

**Consequences:**
- A single malformed code block hangs the entire MCP server (if using stdio, the Claude Desktop session is frozen)
- For Streamable HTTP with `stateless_http=True`, the specific request hangs but the server can handle other requests
- Engineers perceive the tool as unreliable and stop using it

**Warning signs:**
- MCP tool call for `validate_bbj_syntax` never returns
- bbjcpl process visible in `ps aux` consuming 0% CPU (waiting for input)
- Server memory gradually increases if hung processes accumulate

**Prevention:**
- Always pass `timeout=10` to `subprocess.run()`:
  ```python
  result = subprocess.run(
      [bbjcpl_path, "-N", temp_file],
      capture_output=True, text=True, timeout=10,
  )
  ```
- Catch `subprocess.TimeoutExpired` and return a clear error: "Compiler timed out (code may be malformed)"
- Write code to a temp FILE, not stdin (bbjcpl -N <file> does not read from stdin)
- Validate input before passing to bbjcpl: reject empty strings, strings longer than 100KB, and strings containing null bytes
- Use `asyncio.create_subprocess_exec()` for the async variant (MCP tools are async) with `asyncio.wait_for()` as a belt-and-suspenders timeout:
  ```python
  proc = await asyncio.create_subprocess_exec(...)
  try:
      stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
  except asyncio.TimeoutError:
      proc.kill()
      return "Compiler timed out"
  ```

**Severity:** DEGRADED -- Hangs one tool invocation. With `stateless_http=True`, other requests are unaffected. With stdio, the entire Claude Desktop session is blocked.

**Phase:** bbjcpl MCP tool implementation (enforce timeout from the first line of code)

**Confidence:** HIGH -- subprocess timeout behavior is well-documented in Python stdlib. The bbjcpltool PoC already handles this pattern.

---

### I-3: bbjcpl Exit Code Is Always 0 -- Error Detection Requires Stderr Parsing

**What goes wrong:** Unlike most compilers, bbjcpl always exits with code 0 regardless of whether compilation succeeded or failed. The existing bbjcpltool PoC documents this: errors are reported on stderr, but the exit code is not meaningful. If the validation code checks `result.returncode != 0` as the error indicator (the standard pattern for subprocess validation), it will never detect compilation errors. Every code block will be marked as "validated" even if it contains syntax errors.

**Why it happens:**
- bbjcpl's exit code behavior is a legacy design choice from the BBj toolchain
- Most Python subprocess documentation shows `if result.returncode != 0: error()` as the standard pattern
- Developers naturally follow this pattern without verifying against the specific tool
- The bbjcpltool PoC at `/Users/beff/bbjcpltool/` correctly parses stderr, but this knowledge must be carried forward

**Consequences:**
- All BBj code blocks are marked "Compiler validated" including those with syntax errors
- Engineers see incorrect code with a green checkmark, destroying trust in the validation feature
- The unique differentiator (D-1 from FEATURES.md) is useless because it reports false positives

**Warning signs:**
- Every code block shows "validated" regardless of content
- Deliberately invalid BBj code (e.g., `PRINT SYNTAX ERROR HERE`) shows as passing
- `result.returncode` is always 0 in subprocess calls

**Prevention:**
- Parse stderr content, not exit code. If stderr is non-empty, treat as error:
  ```python
  result = subprocess.run([bbjcpl_path, "-N", temp_file], capture_output=True, text=True, timeout=10)
  if result.stderr.strip():
      return ValidationResult(valid=False, errors=parse_bbjcpl_errors(result.stderr))
  return ValidationResult(valid=True, errors=[])
  ```
- Write a test that validates known-bad BBj code and asserts the validation returns errors
- Port the stderr parsing logic from the bbjcpltool PoC directly
- Document this behavior in a code comment: "bbjcpl always exits 0; errors are on stderr only"

**Severity:** DEGRADED -- The system works but the validation feature is silently broken, producing false "valid" results that erode trust.

**Phase:** bbjcpl MCP tool implementation (write test with known-bad code FIRST)

**Confidence:** HIGH -- Confirmed from bbjcpltool PoC documentation and the ARCHITECTURE.md research notes.

---

### I-4: Source-Balanced Ranking Over-Boosts Irrelevant Minority Sources

**What goes wrong:** The source-balanced reranker forces minority sources (PDF: 47 chunks, BBj Source: 106 chunks) into the top results even when they are not relevant to the query. For a query about "BBjGrid column formatting," the system replaces a highly relevant Flare API reference (rank #4, score 0.85) with a marginally relevant PDF chunk about GUI programming basics (rank #18, score 0.35). The answer quality drops because Claude is given irrelevant context.

**Why it happens:**
- The slot reservation approach (recommended in FEATURES.md D-3) guarantees at least 1-2 non-Flare results regardless of relevance
- With only 47 PDF chunks and 106 BBj Source chunks, most queries will not have relevant minority-source results
- The reranker forces diversity without a minimum relevance threshold
- There is no ground truth to calibrate the diversity/relevance tradeoff

**Consequences:**
- Answers include irrelevant information from minority sources
- Claude generates a response that mixes relevant Flare content with off-topic PDF content
- Engineers notice the quality degradation and ask "why is it showing me this?"
- The well-intentioned diversity feature actively harms answer quality

**Warning signs:**
- Non-Flare results in the top-5 have significantly lower RRF scores than the Flare results they replaced
- Answers contain non-sequiturs or off-topic paragraphs traceable to the boosted minority source
- Alpha testers report "the answer includes irrelevant sections"

**Prevention:**
- Add a minimum score threshold: only boost minority sources if their RRF score exceeds a minimum (e.g., 50% of the top result's score). If no minority source meets this threshold, return all-Flare results.
  ```python
  def source_balanced_rerank(results, limit, max_per_source=3, min_score_ratio=0.5):
      top_score = results[0].score if results else 0
      threshold = top_score * min_score_ratio
      # Only consider minority sources above threshold
      ...
  ```
- Make source balancing configurable: `balanced: bool = True` parameter on the /search and /chat endpoints. Alpha testers can toggle it off to compare.
- Log the original rank and score of boosted results so you can measure the quality impact.
- Start with `min_score_ratio=0.5` and tune based on alpha feedback. The parameter is easy to adjust without code changes if stored in configuration.

**Severity:** DEGRADED -- Results are returned but quality is noticeably worse for some queries. This makes the system look less capable than it actually is.

**Phase:** Source-balanced ranking implementation (add minimum score threshold from the start)

**Confidence:** HIGH -- This is the classic precision-diversity tradeoff in information retrieval. Over-boosting is the most common calibration mistake in diversity-aware ranking.

---

### I-5: Concurrent Ingestion Race Condition in Resume State File

**What goes wrong:** The current `ingest_all.py` writes resume state to `_STATE_FILE` after each source completes (line 410-411). When sources run concurrently via `asyncio.gather()`, multiple coroutines may try to update the state file simultaneously. Without file locking, concurrent writes can corrupt the JSON state file, causing resume to fail or skip sources.

**Why it happens:**
- The sequential ingestion loop (v1.4) updates the state file after each source -- safe because only one source runs at a time
- Converting to `asyncio.gather()` means multiple sources complete at unpredictable times
- `_save_resume_state()` reads the entire file, modifies the dict, and writes it back -- a classic read-modify-write race
- JSON file corruption (truncated writes, interleaved bytes) is silent -- the next resume attempt fails with a JSON parse error

**Consequences:**
- Resume state file corrupted: `json.JSONDecodeError` on next `--resume` invocation
- Sources marked as completed when they actually failed (or vice versa)
- A corrupted state file requires manual deletion and full re-ingestion
- The resume feature -- critical for long-running ingestion on 50K chunks -- becomes unreliable

**Warning signs:**
- `JSONDecodeError` when invoking `bbj-ingest-all --resume`
- State file contains partial JSON (truncated)
- Sources appear in both `completed_sources` and `failed_sources` simultaneously

**Prevention:**
- Use a threading lock (or `asyncio.Lock`) to serialize state file writes:
  ```python
  state_lock = asyncio.Lock()

  async def update_state(state, source_name, status):
      async with state_lock:
          state["completed_sources"].append(source_name)
          _save_resume_state(_STATE_FILE, state)
  ```
- Alternatively, use `fcntl.flock()` for file-level locking (POSIX systems only)
- Write to a temp file and atomically rename (prevents partial writes):
  ```python
  with tempfile.NamedTemporaryFile(mode='w', dir=state_dir, delete=False) as f:
      json.dump(state, f)
      os.replace(f.name, _STATE_FILE)  # atomic on POSIX
  ```
- Consider using a database table for ingestion state instead of a JSON file (the pgvector database is already available)

**Severity:** DEGRADED -- Ingestion completes but resume state may be wrong. Manual cleanup required. Not visible during alpha testing (testers use the chat UI, not the ingestion CLI), but blocks the developer who maintains the corpus.

**Phase:** Concurrent ingestion implementation (address state management before parallelizing the loop)

**Confidence:** HIGH -- Read-modify-write race conditions are a fundamental concurrency bug. The sequential code is correct; concurrent execution requires explicit synchronization.

---

### I-6: Ollama Concurrent Embedding Requests Saturate GPU Without Speedup

**What goes wrong:** Setting the asyncio semaphore too high (e.g., 8-10 concurrent requests) does not produce proportional speedup. Ollama's `OLLAMA_NUM_PARALLEL` defaults to 4 (or 1, depending on available memory). Requests beyond the server's capacity are queued internally. Worse, on a Mac with a single GPU (Metal), Qwen3-Embedding-0.6B is already GPU-bound at 2-3 concurrent requests. Additional requests consume VRAM for context without meaningful throughput gain, potentially triggering model unloading.

**Why it happens:**
- Ollama does not have per-model concurrency limits (`OLLAMA_NUM_PARALLEL` is global). Setting it high for embeddings also affects any LLM models loaded simultaneously.
- A GitHub issue (#5693) documents: "high parallelism forces the LLM model that will be mostly loaded into CPU, because it is also expecting to serve 20 parallel requests."
- On Apple Silicon, the 0.6B embedding model uses ~1.2GB VRAM. Each additional parallel request allocates context buffers. With high parallelism, other models may be evicted from GPU memory.
- If Ollama must evict the embedding model to make room (due to memory pressure from another model), each embedding batch triggers a model load (several seconds).

**Consequences:**
- No speedup despite more concurrent requests
- If an LLM model is also loaded (e.g., for the chat UI), the LLM gets evicted from GPU, causing cold-start latency for chat queries
- Ollama returns 503 if its internal queue (`OLLAMA_MAX_QUEUE=512`) overflows
- Ingestion appears to run but is actually slower than sequential due to model thrashing

**Warning signs:**
- Embedding throughput does not increase with higher semaphore values
- GPU utilization remains below 50% despite many concurrent requests (CPU-bound scheduling bottleneck)
- Ollama logs show model load/unload cycles during ingestion
- Chat queries become slow during ingestion (model eviction)

**Prevention:**
- Default semaphore to 2 (conservative). The architecture has already recommended this.
- Set `OLLAMA_MAX_LOADED_MODELS=2` on the Ollama host to ensure both the embedding model and any LLM remain loaded
- If running ingestion on a shared server where the chat UI is also active, schedule ingestion during off-hours or use a separate Ollama instance for embeddings
- Profile before tuning: time a baseline sequential run, then a semaphore=2 run, then semaphore=4. If 2 and 4 show similar performance, stick with 2.
- Consider HTTP connection reuse (persistent `httpx.Client`) as a complementary optimization -- this eliminates TCP handshake overhead per batch and may provide 10-20% speedup independent of concurrency.

**Severity:** DEGRADED -- Ingestion works but is slower than expected. No data loss. The real risk is chat UI degradation during concurrent ingestion.

**Phase:** Concurrent ingestion implementation (start conservative, measure before increasing concurrency)

**Confidence:** HIGH -- Ollama's internal queuing and model management behavior is documented. The GPU-bound nature of embeddings limits the benefit of additional concurrency.

---

### I-7: AsyncConnectionPool Exhaustion Under Concurrent Chat + MCP + Ingestion

**What goes wrong:** The FastAPI app creates an `AsyncConnectionPool` with `min_size=2, max_size=5` (line 57-61 of `app.py`). When the chat UI, remote MCP, and concurrent ingestion all share the same pool, 5 connections can be exhausted: 2 chat requests + 2 MCP requests + 1 ingestion query = 5. The 6th concurrent request blocks until a connection is returned, causing a `PoolTimeout` after the configured timeout expires.

**Why it happens:**
- The pool size (max=5) was appropriate for v1.4 (REST API only, low concurrency)
- v1.5 adds three new consumers of the pool: chat UI (query embedding + search per request), remote MCP (search per tool call), and potentially concurrent ingestion
- Alpha testers will use the chat UI and Claude Desktop (MCP) simultaneously
- Each chat request holds a connection for the duration of RAG search + Claude API streaming (potentially 3-10 seconds)
- If concurrent ingestion is running via the API (not the CLI), it also consumes pool connections
- The psycopg3 documentation warns: "Using several connections has an impact on the server's performance"

**Consequences:**
- Chat requests return 503 with "PoolTimeout" error
- MCP tool calls timeout with no response
- Intermittent failures that depend on concurrent load -- difficult to reproduce in development
- Alpha testers experience "sometimes it works, sometimes it times out"

**Warning signs:**
- `psycopg_pool.PoolTimeout` exceptions in server logs
- Pool stats (`pool.get_stats()`) show `pool_available=0` and `requests_queued > 0`
- Response times spike under moderate concurrent usage (3+ simultaneous users)

**Prevention:**
- Increase pool size: `min_size=5, max_size=15` is appropriate for alpha (5-10 concurrent users)
- Release connections quickly: do NOT hold a connection during Claude API streaming. Acquire a connection for search, fetch results, release the connection, THEN stream Claude's response. The connection is only needed for the ~100ms search query, not the 3-10s streaming.
  ```python
  # Bad: holds connection during entire streaming response
  async with pool.connection() as conn:
      results = await async_hybrid_search(conn, ...)
      async for token in stream_claude(results):
          yield token  # conn held for entire stream duration

  # Good: releases connection before streaming
  async with pool.connection() as conn:
      results = await async_hybrid_search(conn, ...)
  # Connection returned to pool
  async for token in stream_claude(results):
      yield token
  ```
- Concurrent ingestion should use its own connection (from `get_connection_from_settings()`, not the pool). The existing `ingest_all.py` already creates per-source connections outside the pool. Ensure this pattern is preserved when adding concurrency.
- Monitor pool health: add pool stats to the `/health` endpoint (e.g., `pool.get_stats()`)

**Severity:** DEGRADED -- Individual requests fail intermittently but the system remains available. Retrying usually works. This manifests as flakiness during the alpha, which erodes confidence.

**Phase:** Chat UI + Remote MCP (increase pool size and fix connection lifecycle before multi-user alpha testing)

**Confidence:** HIGH -- Connection pool exhaustion is the most documented psycopg3 + FastAPI issue. Pool stats confirm it.

---

## UX Pitfalls (Annoyance)

Issues that do not break functionality but create a poor first impression for alpha testers.

### U-1: Chat UI Serves at Root Path, Breaking Existing API Documentation

**What goes wrong:** If the chat UI is mounted at `/` (the root path), it replaces FastAPI's default Swagger UI at `/docs`. Engineers who bookmarked `http://server:10800/docs` for API exploration get the chat UI instead. Similarly, mounting static files at `/static` may conflict with future API routes.

**Prevention:**
- Mount the chat UI at a specific path: `GET /chat` for the HTML page, `POST /chat/send` for the SSE stream
- Keep FastAPI's default `/docs` and `/redoc` intact for API exploration
- Use a clear URL scheme: `/chat/*` for the UI, `/search`, `/stats`, `/health` for the API, `/mcp` for MCP
- Add a root redirect: `GET /` redirects to `/chat` (a one-liner `RedirectResponse`)

**Severity:** ANNOYANCE -- Engineers lose access to the Swagger docs page but the system functions normally.

**Phase:** Chat UI implementation (decide URL scheme before building routes)

---

### U-2: Flare Source URLs Not Clickable Because Mapping Is Wrong

**What goes wrong:** The `flare://Content/path.htm` to `https://documentation.basis.cloud/...` mapping looks correct but the actual URL structure on the documentation site does not match. The Flare project structure uses internal paths that may differ from the published web hierarchy. A click on a "Source" link in the chat UI leads to a 404 page on documentation.basis.cloud.

**Why it happens:**
- The Flare project internal structure (`Content/bbjobjects/Window/bbjwindow.htm`) may differ from the published structure (`BASISHelp/WebHelp/bbjobjects/Window/bbjwindow.htm`)
- The URL mapping in STACK.md shows `flare://Content/` -> `https://documentation.basis.cloud/BASISHelp/WebHelp/` but this mapping needs verification against the live site
- The existing web_crawl parser already uses the real documentation.basis.cloud URLs. Comparing web_crawl source_urls with flare source_urls for the same pages would reveal the correct mapping.

**Prevention:**
- Sample 10 Flare source_urls from the database, manually construct the mapped URL, and verify each one opens in a browser
- Cross-reference with the web_crawl source_urls in the database -- these are already real URLs. Find pages that exist in both Flare and web_crawl to validate the mapping.
- If the mapping is wrong, check whether the path needs a prefix adjustment (e.g., `BASISHelp/WebHelp/` vs `BASISHelp/`)
- Make the mapping configurable (already planned in STACK.md) so it can be corrected without code changes

**Severity:** ANNOYANCE -- Links look clickable but lead to 404s. Engineers lose trust in the citation links.

**Phase:** Source URL mapping (verify against live site before deploying)

---

### U-3: Code Blocks in Chat Not Identified as BBj (No Syntax Highlighting)

**What goes wrong:** Claude returns code blocks fenced with triple backticks but may not always use the `bbj` language tag. It might use `basic`, `vb`, `text`, or no language tag at all. The chat UI renders these as plain monospace text without syntax highlighting. BBj code looks like a gray blob instead of a colorful, readable code block. For a tool specifically designed for BBj developers, this is a poor first impression.

**Prevention:**
- In the system prompt, instruct Claude to always use `bbj` as the code fence language: "When including BBj code examples, always use \`\`\`bbj as the code fence."
- In the client-side markdown renderer, treat `basic`, `vb`, `visual-basic`, and untagged code blocks as BBj (BBj is a BASIC variant -- generic BASIC highlighting is reasonable)
- Use a lightweight syntax highlighting library that supports custom language definitions (e.g., highlight.js with a custom BBj definition, or Prism.js)
- For alpha, plain monospace with a colored background is acceptable. Syntax highlighting is an enhancement, not a blocker.

**Severity:** ANNOYANCE -- Code is readable but not highlighted. BBj engineers are accustomed to syntax highlighting in their IDE.

**Phase:** Chat UI implementation (system prompt instruction is trivial; syntax highlighting is a nice-to-have)

---

### U-4: First Chat Query Is Slow Due to Ollama Embedding Model Cold Start

**What goes wrong:** The FastAPI app warms up the Ollama embedding model at startup (`app.py` line 69). However, Ollama may unload idle models after a configurable keep-alive period (default: 5 minutes). If no search queries are made for 5+ minutes, the first chat query triggers a model reload, adding 2-5 seconds to the response time. The user sees a long delay before anything happens.

**Prevention:**
- Set `OLLAMA_KEEP_ALIVE=-1` on the Ollama host to never unload models (appropriate for a dedicated RAG server)
- Alternatively, add a periodic health check (every 2 minutes) that sends a dummy embedding to keep the model loaded: already partially implemented by the startup warm-up, but needs to be periodic
- Display a "Searching documentation..." loading indicator in the chat UI while the embedding + search happens. This manages expectations even if the model needs to reload.
- The cold-start delay is only 2-5 seconds for the 0.6B model, not catastrophic. But it feels broken if there is no loading indicator.

**Severity:** ANNOYANCE -- First query is slow but subsequent queries are fast. Only affects the first user after an idle period.

**Phase:** Chat UI + Ollama configuration (set OLLAMA_KEEP_ALIVE and add loading indicator)

---

### U-5: Multiple Chat Users See Each Other's Streaming Responses

**What goes wrong:** If the SSE streaming endpoint uses a single shared event queue or channel, multiple concurrent users may receive events from each other's queries. User A asks about BBjGrid and sees tokens from User B's query about BBjProcess. This creates a confusing, unusable experience.

**Why it happens:**
- A naive implementation uses a single SSE endpoint that broadcasts events to all connected clients
- Without per-session isolation, events from different Claude API streams mix
- The alpha explicitly excludes user accounts, so there is no built-in user identity to route events

**Prevention:**
- Generate a unique session ID (UUID) for each chat query
- The SSE endpoint includes the session ID in the URL: `GET /chat/stream/{session_id}`
- Each session ID maps to its own streaming generator -- no shared state between sessions
- The chat UI receives the session ID from the POST response and connects to the session-specific SSE endpoint
- Use a dict (or asyncio.Queue per session) to isolate events:
  ```python
  active_streams: dict[str, asyncio.Queue] = {}
  ```
- Clean up completed session queues to prevent memory leaks

**Severity:** ANNOYANCE to DEGRADED -- Confusing output but no data corruption. Easy to diagnose (responses do not match the question).

**Phase:** Chat UI implementation (per-session SSE routing is a core architectural decision, not an afterthought)

---

## Regression Risk Assessment

### What Could Break in the Working v1.4 System

The v1.4 system is validated with a 17-query E2E test suite. These features are at risk during v1.5 development:

| Existing Feature | Risk Source | Likelihood | Mitigation |
|-----------------|-------------|------------|------------|
| `POST /search` endpoint | Adding source-balanced reranking changes result order | MEDIUM | Make reranking opt-in (`balanced=true` parameter), default OFF for API |
| `GET /stats` endpoint | No changes planned | NONE | -- |
| `GET /health` endpoint | Adding MCP health check could mask existing checks | LOW | Add MCP as a third check, do not modify DB/Ollama checks |
| MCP stdio server | Refactoring from httpx proxy to direct search | HIGH | Keep the httpx proxy as fallback. Test stdio mode explicitly. |
| Database schema | No schema changes in v1.5 | NONE | Source URL mapping is runtime, not DB |
| Ingestion pipeline | Concurrent ingestion modifies `ingest_all.py` only | LOW | Keep `run_pipeline()` unchanged; concurrent wrapper calls it |
| 329+ passing tests | New dependencies may break imports | LOW | Run test suite after adding anthropic dependency |

### First-Impression Risk for Alpha Testers

The alpha test is a make-or-break moment. These are ordered by first-impression impact:

| Scenario | Impact | Prevention |
|----------|--------|------------|
| First chat query returns garbled text (C-1) | Engineers close the tab and never return | Validate SSE + multi-line encoding before building UI |
| First chat query returns vague/wrong answer (C-2) | Engineers conclude RAG does not work for BBj | Limit context to 8-10 focused results, test with known BBj queries |
| Chat query hangs with no response (I-1) | Engineers assume the system is broken | Implement SSE error events and client-side timeout |
| Compiler validation shows green check on bad code (I-3) | Engineers lose trust in the differentiating feature | Parse stderr, test with known-bad code |
| Source links lead to 404 pages (U-2) | Engineers stop clicking sources, reducing trust loop | Verify URL mapping against live site |
| Chat shows a 10-second blank screen before response starts (U-4) | Engineers assume it crashed | Add loading indicator, set OLLAMA_KEEP_ALIVE=-1 |
| Multiple users see mixed responses (U-5) | Engineers cannot use the system concurrently | Per-session SSE routing from day one |

---

## Prevention Checklist

Before deploying v1.5 to alpha testers, verify each item:

### Chat UI + Claude API
- [ ] SSE streaming preserves multi-line content (code blocks, markdown) -- test with a BBj code response
- [ ] Claude API context limited to 8-10 search results (no unbounded context stuffing)
- [ ] SSE error events display user-visible error messages on Claude API failure
- [ ] Per-session SSE routing prevents cross-talk between concurrent users
- [ ] Application-level rate limiting active (30 req/min)
- [ ] `ANTHROPIC_API_KEY` not logged, not exposed in API responses
- [ ] Spending alerts set in Anthropic console
- [ ] Chat UI accessible at `/chat`, does not replace `/docs`

### MCP Refactoring
- [ ] MCP tool calls `async_hybrid_search()` directly (not via httpx self-referential loop)
- [ ] Stdio transport still works for local Claude Desktop (backward compatible)
- [ ] Streamable HTTP mounting tested and working (or standalone fallback deployed)
- [ ] `Mcp-Session-Id` handling does not conflict with FastAPI middleware

### bbjcpl Validation
- [ ] `subprocess.run()` called with `timeout=10`
- [ ] Errors detected by parsing stderr (not exit code)
- [ ] Known-bad BBj code returns validation errors (unit test)
- [ ] Known-good BBj code returns validation success (unit test)

### Source-Balanced Ranking
- [ ] Minimum score threshold prevents irrelevant minority sources from being boosted
- [ ] Reranking is configurable (can be disabled per request)
- [ ] Existing `/search` endpoint behavior unchanged by default (opt-in balancing)

### Concurrent Ingestion
- [ ] Resume state file writes are serialized (lock or atomic rename)
- [ ] Semaphore defaults to 2 (not unbounded)
- [ ] Chat UI performance unaffected during concurrent ingestion
- [ ] Sequential mode (`--no-parallel`) still works as fallback

### Connection Management
- [ ] AsyncConnectionPool `max_size` increased to 15 for multi-user alpha
- [ ] Chat endpoint releases connection before streaming Claude response
- [ ] Pool stats visible in health endpoint

### Source URL Mapping
- [ ] Top 10 flare:// URLs verified against live documentation.basis.cloud
- [ ] HTTP passthrough works for wordpress/web_crawl URLs
- [ ] Non-mappable URLs (pdf://, file://) show descriptive text, not broken links

---

## Phase-Specific Warning Matrix

| Phase | Pitfall | Severity | Test First |
|-------|---------|----------|------------|
| Chat UI + Claude API | C-1: SSE newline corruption | BLOCKER | Stream a code block via SSE, verify rendering |
| Chat UI + Claude API | C-2: Context window stuffing | BLOCKER | Log input_tokens, verify < 6K per query |
| Chat UI + Claude API | C-4: API key cost exposure | BLOCKER | Set spending alerts, add rate limiting |
| Chat UI + Claude API | I-1: SSE error handling | DEGRADED | Set invalid API key, verify error displayed |
| Chat UI + Claude API | U-5: Cross-session contamination | DEGRADED | Open two browser tabs, send concurrent queries |
| Remote MCP | C-3: Self-referential httpx loop | BLOCKER | Invoke MCP tool via HTTP, verify no deadlock |
| Remote MCP | C-5: SDK mounting issues | BLOCKER | Mount and test POST to /mcp BEFORE refactoring tools |
| Remote MCP | I-7: Pool exhaustion | DEGRADED | Run 5 concurrent requests, check for PoolTimeout |
| bbjcpl Validation | I-2: Subprocess hangs | DEGRADED | Validate code that triggers hang, verify timeout |
| bbjcpl Validation | I-3: Exit code always 0 | DEGRADED | Validate known-bad code, verify errors returned |
| Source-Balanced Ranking | I-4: Over-boosting irrelevant sources | DEGRADED | Compare balanced vs unbalanced for 5 test queries |
| Concurrent Ingestion | I-5: Resume state race condition | DEGRADED | Run 3 sources concurrently, verify state file integrity |
| Concurrent Ingestion | I-6: GPU saturation without speedup | DEGRADED | Benchmark semaphore=2 vs semaphore=4 |
| Source URL Mapping | U-2: Flare URLs 404 | ANNOYANCE | Click 10 mapped URLs in browser |

---

## Sources

### SSE Streaming + HTMX
- [HTMX SSE Extension Documentation](https://htmx.org/extensions/sse/) -- event names, sse-close, swap behavior
- [HTMX SSE Extension Error Handling Issue #134](https://github.com/bigskysoftware/htmx-extensions/issues/134) -- SSE extension does not handle errors
- [HTMX SSE Extension Scope Issue #3467](https://github.com/bigskysoftware/htmx/issues/3467) -- misleading documentation on hx-ext placement
- [FastAPI SSE in Docker Discussion #11590](https://github.com/fastapi/fastapi/discussions/11590) -- SSE problems in Docker environment
- [HTMX + SSE Chatbot with Markdown Corruption](https://towardsdatascience.com/javascript-fatigue-you-dont-need-js-to-build-chatgpt-part-2/) -- base64 encoding workaround for newlines

### Claude API
- [Anthropic Streaming Messages API](https://docs.anthropic.com/en/api/messages-streaming) -- mid-stream errors, SSE format
- [Anthropic Error Handling](https://docs.anthropic.com/en/api/errors) -- 429, 529, 413 error codes, retry behavior
- [Anthropic Citations API](https://docs.anthropic.com/en/docs/build-with-claude/citations) -- search result blocks, citation format
- [Anthropic Handling Stop Reasons](https://docs.anthropic.com/en/api/handling-stop-reasons) -- max_tokens, model_context_window_exceeded
- [Anthropic Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) -- chunk relevance, lost-in-the-middle problem
- [Simon Willison: Anthropic Citations API](https://simonwillison.net/2025/Jan/24/anthropics-new-citations-api/) -- practical integration observations

### MCP Transport
- [MCP Transport Future (Official Blog)](http://blog.modelcontextprotocol.io/posts/2025-12-19-mcp-transport-future/) -- session management changes, Q1 2026 spec update
- [MCP Transports Specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports) -- Streamable HTTP protocol details
- [MCP Python SDK GitHub #1367](https://github.com/modelcontextprotocol/python-sdk/issues/1367) -- path doubling when mounting in FastAPI
- [Converting STDIO to Remote MCP Servers (Portkey)](https://portkey.ai/docs/guides/converting-stdio-to-streamable-http) -- migration guide

### Ollama Concurrency
- [Ollama Parallel Processing FAQ](https://docs.ollama.com/faq) -- OLLAMA_NUM_PARALLEL, OLLAMA_MAX_LOADED_MODELS
- [Ollama Per-Model Concurrency Issue #5693](https://github.com/ollama/ollama/issues/5693) -- embedding vs LLM parallelism conflict
- [Ollama vs TEI Performance Issue #12088](https://github.com/ollama/ollama/issues/12088) -- embedding throughput comparison
- [How Ollama Handles Parallel Requests](https://www.glukhov.org/post/2025/05/how-ollama-handles-parallel-requests/) -- queuing, batching behavior

### psycopg3 Connection Pool
- [psycopg3 Connection Pools Documentation](https://www.psycopg.org/psycopg3/docs/advanced/pool.html) -- exhaustion behavior, blocking semantics
- [psycopg3 Pool Leakage Issue #646](https://github.com/psycopg/psycopg/issues/646) -- pool exhaustion symptoms and diagnostics
- [psycopg3 Possible Connection Leak Issue #1176](https://github.com/psycopg/psycopg/issues/1176) -- high TPS connection management
- [psycopg3 PoolTimeout with Background Tasks #985](https://github.com/psycopg/psycopg/discussions/985) -- FastAPI background tasks and pool interaction

### Subprocess Management
- [Python subprocess.run timeout documentation](https://docs.python.org/3/library/subprocess.html) -- timeout parameter, TimeoutExpired exception
- [Subprocess timeout in Python 3.14](https://discuss.python.org/t/subprocess-timeout-in-python-3-14/97391) -- recent timeout behavior changes
- [Docker + Python subprocess issues](https://forums.docker.com/t/how-to-make-python-subprocess-run-work-in-docker-container/81578) -- path resolution across Docker boundary

---

*Research conducted 2026-02-03. All pitfalls verified against the existing codebase (v1.4 at commit f590cdd), official SDK documentation, and community-reported issues. Existing v1.4 PITFALLS.md covered Docker deployment pitfalls; this document covers integration pitfalls specific to v1.5 feature additions.*
