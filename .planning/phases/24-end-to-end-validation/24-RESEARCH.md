# Phase 24: End-to-End Validation - Research

**Researched:** 2026-02-02
**Domain:** RAG pipeline validation (REST API + MCP, query-driven, report generation)
**Confidence:** HIGH

## Summary

Phase 24 validates the complete RAG pipeline end-to-end: user query enters through REST API or MCP server, hits the real ingested BBj documentation corpus, and returns relevant results. This is a validation phase, not a feature-building phase. The existing codebase already has all the infrastructure needed -- the work is writing a validation script that exercises the APIs, asserts quality, and produces a Markdown report.

The codebase already contains a `test_search_validation.py` with YAML-driven parametrized tests and a `_query_report_data()` function in the intelligence report module. The validation script for Phase 24 builds on these patterns but produces a standalone `VALIDATION.md` report rather than pytest assertions.

**Primary recommendation:** Write a single Python validation script that: (1) checks prerequisites (Docker, DB, Ollama), (2) calls `/stats` to verify all 6 sources have chunks, (3) runs source-targeted and topic-based queries through `/search`, (4) runs a subset through the MCP server via the `mcp` SDK's `ClientSession.call_tool()`, (5) generates `VALIDATION.md` with per-query results and corpus stats.

## Standard Stack

### Core

The validation script uses only libraries already in the project's dependency tree. No new dependencies are needed.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | >=0.28,<1 | REST API calls to `/search` and `/stats` | Already a project dependency; async HTTP client |
| mcp[cli] | >=1.25,<2 | MCP client SDK for programmatic `search_bbj_knowledge` invocation | Already a project dependency; provides `ClientSession`, `stdio_client`, `StdioServerParameters` |
| anyio | (transitive) | Async runtime for MCP client | Comes with mcp SDK; required for `stdio_client` context manager |
| click | >=8.1,<9 | CLI for the validation script (if registered as console script) | Already a project dependency |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | >=2.12,<3 | Validate API response shapes | Already available; use for type-safe response parsing |
| pathlib | stdlib | File paths for report output | Always |
| json | stdlib | Parse REST API JSON responses | Always |
| datetime | stdlib | Timestamps in report | Always |
| textwrap | stdlib | Content snippet truncation | Report formatting |

### Alternatives Considered

No alternatives needed -- this phase uses the existing project stack exclusively.

**Installation:** No new packages needed. The existing `uv sync` provides everything.

## Architecture Patterns

### Validation Script Structure

```
rag-ingestion/
    scripts/
        validate_e2e.py      # Main validation script (new)
    VALIDATION.md            # Generated report (project root of rag-ingestion/)
```

The validation script lives in `scripts/` (where `reset-db.sh` already exists). The output `VALIDATION.md` goes in the `rag-ingestion/` directory root for visibility.

### Pattern 1: Prerequisites Check Before Queries

**What:** Verify Docker containers running, DB accessible, Ollama responding, and all 6 sources present before running any queries.
**When to use:** Always -- fail fast with clear error messages.

```python
# Source: Existing health.py pattern + /stats endpoint
async def check_prerequisites(client: httpx.AsyncClient, api_base: str) -> dict:
    """Check health endpoint and verify all 6 sources have chunks."""
    # 1. Health check
    resp = await client.get(f"{api_base}/health")
    health = resp.json()
    if health["status"] != "healthy":
        sys.exit(f"Prerequisites failed: {health}")

    # 2. Stats check -- verify 6 sources
    resp = await client.get(f"{api_base}/stats")
    stats = resp.json()

    # The /stats endpoint groups by doc_type, but we need by source_url prefix.
    # Use the report module's SQL grouping pattern from _query_report_data()
    # OR connect directly to DB to run the source-prefix CASE query.
    #
    # IMPORTANT: The /stats endpoint returns by_source grouped by doc_type,
    # NOT by source_url prefix. The report module's _query_report_data()
    # has the correct source-prefix CASE statement. For validation, the
    # simplest approach is to call /stats for total_chunks and by_source
    # (which groups by doc_type), then verify source diversity via query
    # results rather than trying to replicate the SQL prefix grouping.
    return stats
```

**Key insight:** The `/stats` endpoint returns `by_source` grouped by `doc_type` (e.g., "flare", "tutorial", "article", "example", "web_crawl"), NOT by the 7 logical source categories from the report module. The report module's `_query_report_data()` uses a SQL CASE statement on `source_url` prefixes to map to logical sources (flare, advantage, kb, pdf, mdx, bbj-source, web-crawl). For the validation script, two approaches:

1. **Direct DB query** (like the report module) -- requires psycopg connection, duplicates SQL logic
2. **Infer from query results** -- run queries and check that results come from multiple `source_url` prefixes across the full query set

Recommendation: Use approach 2 (infer from results) for cross-source verification, plus call `/stats` to get total_chunks. If zero total chunks, that's a hard failure. The source-targeted queries (one per source) inherently validate each source's presence.

### Pattern 2: REST API Search Query Execution

**What:** POST to `/search` with query text, parse response, evaluate top-1 relevance.
**When to use:** For all 11-16 queries in the validation set.

```python
# Source: Existing api/schemas.py SearchRequest/SearchResponse
async def run_search_query(
    client: httpx.AsyncClient,
    api_base: str,
    query: str,
    limit: int = 5,
    generation: str | None = None,
) -> dict:
    """Execute a search query and return structured results."""
    payload = {"query": query, "limit": limit}
    if generation:
        payload["generation"] = generation
    resp = await client.post(f"{api_base}/search", json=payload, timeout=30.0)
    resp.raise_for_status()
    return resp.json()
```

**Response shape** (from `SearchResponse` schema):
```json
{
    "query": "string",
    "results": [
        {
            "content": "string",
            "title": "string",
            "source_url": "string",
            "doc_type": "string",
            "generations": ["string"],
            "context_header": "string",
            "deprecated": false,
            "score": 0.0
        }
    ],
    "count": 0
}
```

### Pattern 3: MCP Programmatic Tool Invocation

**What:** Spawn `bbj-mcp` via stdio, connect with `ClientSession`, call `search_bbj_knowledge`.
**When to use:** For the 3-4 MCP validation queries.

```python
# Source: mcp SDK client module (verified from installed package)
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def run_mcp_query(query: str, limit: int = 5) -> str:
    """Invoke search_bbj_knowledge via MCP stdio transport."""
    server_params = StdioServerParameters(
        command="uv",
        args=["--directory", str(RAG_DIR), "run", "bbj-mcp"],
        env={
            **os.environ,
            "BBJ_RAG_API_URL": API_BASE,
        },
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "search_bbj_knowledge",
                arguments={"query": query, "limit": limit},
            )
            # result.content is a list of TextContent/ImageContent
            # For text tools, result.content[0].text contains the formatted string
            return result.content[0].text
```

**Critical details about MCP client usage:**
- `stdio_client` is an async context manager that spawns the server process
- `ClientSession` wraps the read/write streams from `stdio_client`
- Must call `session.initialize()` before `call_tool()`
- `call_tool()` returns a `CallToolResult` with `.content` list and `.isError` bool
- Text content is in `result.content[0].text` (the MCP server returns formatted text)
- The env dict passed to `StdioServerParameters` must include the inherited env vars (`stdio_client` uses a filtered default set, but `BBJ_RAG_API_URL` must be explicitly added)
- Server process is automatically terminated when the context manager exits

**IMPORTANT:** Each MCP query spawns/kills a server process. For 3-4 queries, either:
- Spawn once, run all queries, then exit (preferred -- keep session open)
- Spawn per-query (simpler but slower)

Recommendation: Spawn once, run all MCP queries in a single session.

### Pattern 4: Report Generation

**What:** Build a Markdown string and write to `VALIDATION.md`.
**When to use:** After all queries complete.

Report structure per the CONTEXT.md decisions:
```markdown
# End-to-End Validation Report

**Generated:** YYYY-MM-DD HH:MM
**Status:** PASS / FAIL (N of M queries passed)

## Corpus Stats

| Metric | Value |
|--------|-------|
| Total chunks | N |
| ... by source doc_type ... |

## Source-Targeted Queries

### Query 1: [query text]
- **Result:** PASS / FAIL
- **Source:** [source_url]
- **Title:** [title]
- **Score:** [rrf_score]
- **Snippet:** [first ~100 chars of content]

...

## Topic-Based Queries

### Query 7: [query text]
...

## MCP Validation

### Query M1: [query text]
- **Result:** PASS / FAIL
- **Response preview:** [first ~100 chars]

## Cross-Source Summary

| Source Prefix | Appeared in Results |
|---------------|---------------------|
| flare:// | Yes |
| pdf:// | Yes |
...

## Known Issues

[Any queries with poor results documented here]
```

### Anti-Patterns to Avoid

- **Hardcoding expected content in assertions:** The corpus is real documentation, not test fixtures. Top-1 relevance is judged by whether the result relates to the query topic, not by exact string matching.
- **Running MCP queries through Claude Desktop manually:** The CONTEXT explicitly says programmatic invocation via `ClientSession.call_tool()`.
- **Connecting directly to the database for search:** The validation must go through the REST API and MCP interfaces to prove the full pipeline works end-to-end.
- **Treating the validation script as a test suite:** This is a report generator, not pytest. It produces `VALIDATION.md` with pass/fail per query, not pytest assertions that block CI.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP client connection | Raw JSON-RPC over stdio | `mcp.client.stdio.stdio_client` + `ClientSession` | Protocol handling, message framing, process lifecycle all handled |
| HTTP client | `urllib` / `requests` | `httpx.AsyncClient` | Already in deps; async; timeout handling |
| Content truncation | Manual string slicing | `textwrap.shorten(content, 100, placeholder="...")` | Handles word boundaries properly |
| Report templating | Jinja2 or f-string spaghetti | Simple f-string sections with helper functions | Report is simple enough; no template engine needed |

**Key insight:** The MCP SDK client is already installed (`mcp[cli]>=1.25,<2` in pyproject.toml). The `ClientSession.call_tool()` API is the correct way to programmatically invoke tools -- it handles the full MCP protocol (initialize handshake, JSON-RPC framing, tool discovery).

## Common Pitfalls

### Pitfall 1: /stats endpoint returns doc_type, not logical source

**What goes wrong:** Assuming `/stats` `by_source` field maps to the 7 logical sources (flare, advantage, kb, pdf, mdx, bbj-source, web-crawl). It actually returns `by_source` grouped by `doc_type` column values (e.g., "flare", "tutorial", "article", "example", "web_crawl").
**Why it happens:** The `/stats` endpoint queries `SELECT doc_type, count(*) FROM chunks GROUP BY doc_type` for its `by_source` field.
**How to avoid:** For source-level validation, rely on `source_url` prefixes in query results rather than the `/stats` by_source breakdown. The total_chunks from `/stats` is reliable.
**Warning signs:** Report shows "tutorial" as a source instead of "mdx".

**CORRECTION:** Re-reading the code more carefully:

The `/stats` endpoint has TWO groupings:
- `by_source`: groups by `doc_type` column (`SELECT doc_type, count(*) FROM chunks GROUP BY doc_type`)
- `by_generation`: groups by unnested `generations` array

The `doc_type` values set by parsers are: `"flare"` (FlareParser), `"tutorial"` (MdxParser), `"article"` (AdvantageParser, KnowledgeBaseParser), `"example"` (BbjSourceParser), `"web_crawl"` (WebCrawlParser), and various types from PdfParser (`_classify_doc_type` returns "tutorial", "concept", "api-reference", "language-reference", "best-practice", "version-note").

So the `/stats` `by_source` map will have keys like `{"flare": N, "tutorial": N, "article": N, "example": N, "web_crawl": N, "concept": N, ...}`. This does NOT distinguish between MDX tutorials and PDF tutorials, or between Advantage articles and KB articles.

For the "all 6 sources must be present" prerequisite check, the validation script needs to either:
1. Connect to DB directly and use the `_query_report_data()` CASE statement
2. Run the source-targeted queries and verify each returns results (inherent validation)

**Recommendation:** Approach 2 is cleaner -- the source-targeted queries (one per source) serve as the presence check. If a source-targeted query returns zero results, that source is missing.

### Pitfall 2: MCP stdio environment variable inheritance

**What goes wrong:** The MCP `stdio_client` uses a filtered default environment (only HOME, PATH, SHELL, etc. on macOS). Custom env vars like `BBJ_RAG_API_URL` are NOT inherited unless explicitly passed.
**Why it happens:** The `StdioServerParameters.env` field, if set, replaces the default environment. If not set, only DEFAULT_INHERITED_ENV_VARS are passed.
**How to avoid:** Explicitly include `BBJ_RAG_API_URL` in the `env` dict, merged with `get_default_environment()` from the MCP SDK.
**Warning signs:** MCP server fails with "Connection refused" because it defaults to `http://localhost:10800` when `BBJ_RAG_API_URL` is missing (which actually IS the correct default, so this is less of an issue than it appears).

### Pitfall 3: MCP server process lifecycle

**What goes wrong:** Spawning a new MCP server process per query is slow (Python startup + uv resolution each time). Or forgetting to properly close the session, leaving zombie processes.
**Why it happens:** The `stdio_client` context manager spawns a subprocess each time.
**How to avoid:** Open ONE `stdio_client` + `ClientSession` for all MCP queries, then exit the context manager once.
**Warning signs:** Validation takes 30+ seconds for MCP queries; orphaned Python processes after script exit.

### Pitfall 4: Confusing "6 sources" with sources.toml entries

**What goes wrong:** The context says "6 sources" but `sources.toml` has 9 entries (3 MDX directories, 2 WordPress sources, etc.).
**Why it happens:** The "6 sources" refers to the 6 parser types / logical source categories, not individual config entries.
**How to avoid:** The 6 logical sources for validation are:
  1. **Flare** -- MadCap Flare XHTML docs (source_url prefix: `flare://`)
  2. **PDF** -- GUI programming guide (prefix: `pdf://`)
  3. **MDX** -- Docusaurus tutorials (prefix: `mdx-dwc://`, `mdx-beginner://`, `mdx-db-modernization://`)
  4. **BBj Source** -- Code samples (prefix: `file://`)
  5. **WordPress** -- Advantage + KB articles (prefix: `https://basis.cloud/...`)
  6. **Web Crawl** -- documentation.basis.cloud (prefix: `https://documentation.basis.cloud/...`)
**Warning signs:** Missing a source category because you counted config entries instead of parser types.

### Pitfall 5: Embedding model warm-up latency

**What goes wrong:** First query takes significantly longer because Ollama loads the embedding model into memory.
**Why it happens:** Ollama lazy-loads models; first embed call triggers model load.
**How to avoid:** The REST API lifespan already does a warm-up embed call. If Docker container just started, the first query may still be slow. Add a brief wait or warm-up call before timing queries.
**Warning signs:** First query timeout; subsequent queries are fast.

### Pitfall 6: Relevance assessment is subjective

**What goes wrong:** Automated pass/fail for "top-1 result is relevant" requires defining what "relevant" means programmatically.
**Why it happens:** The CONTEXT says "a human reading it should be able to answer the original question" -- this is inherently subjective.
**How to avoid:** For automated pass/fail, use lightweight heuristics:
  - Result count > 0 (basic: something came back)
  - Top-1 result content or title contains a keyword from the query topic
  - For source-targeted queries: top-1 result source_url matches expected prefix

  The VALIDATION.md report includes snippets so a human CAN judge, but the automated pass/fail uses the heuristic. Document any queries with questionable results as "known issues."
**Warning signs:** All queries "pass" on the heuristic but snippets show irrelevant content.

## Code Examples

### Example 1: Complete REST API Query + Result Evaluation

```python
# Source: Verified from api/schemas.py and search.py
import httpx

async def evaluate_query(
    client: httpx.AsyncClient,
    api_base: str,
    query: str,
    expected_source_prefix: str | None = None,
    keywords: list[str] | None = None,
) -> dict:
    """Run a query and evaluate the top-1 result."""
    payload = {"query": query, "limit": 5}
    resp = await client.post(f"{api_base}/search", json=payload, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()

    results = data["results"]
    passed = len(results) > 0
    reason = "no results" if not passed else "results returned"

    if passed and expected_source_prefix:
        top = results[0]
        if not top["source_url"].startswith(expected_source_prefix):
            passed = False
            reason = f"top result from {top['source_url']}, expected {expected_source_prefix}"

    if passed and keywords:
        top = results[0]
        combined = (top["title"] + " " + top["content"]).lower()
        if not any(kw.lower() in combined for kw in keywords):
            passed = False
            reason = f"no keyword match in top result"

    return {
        "query": query,
        "passed": passed,
        "reason": reason,
        "result_count": len(results),
        "top_result": results[0] if results else None,
        "all_results": results,
    }
```

### Example 2: MCP Session with Multiple Queries

```python
# Source: Verified from mcp SDK installed package
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def run_mcp_validation(queries: list[str], rag_dir: str, api_base: str) -> list[dict]:
    """Run multiple queries through MCP in a single session."""
    server_params = StdioServerParameters(
        command="uv",
        args=["--directory", rag_dir, "run", "bbj-mcp"],
        env={
            "HOME": os.environ.get("HOME", ""),
            "PATH": os.environ.get("PATH", ""),
            "SHELL": os.environ.get("SHELL", ""),
            "USER": os.environ.get("USER", ""),
            "LOGNAME": os.environ.get("LOGNAME", ""),
            "TERM": os.environ.get("TERM", ""),
            "BBJ_RAG_API_URL": api_base,
        },
    )

    results = []
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Verify tool is listed
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            assert "search_bbj_knowledge" in tool_names

            for query in queries:
                result = await session.call_tool(
                    "search_bbj_knowledge",
                    arguments={"query": query, "limit": 5},
                )
                text = result.content[0].text if result.content else ""
                results.append({
                    "query": query,
                    "passed": not result.isError and "No results found" not in text,
                    "response_preview": text[:200],
                    "is_error": result.isError,
                })

    return results
```

### Example 3: Markdown Report Generation

```python
# Source: Project convention (follows existing report.py patterns)
from datetime import datetime, timezone
import textwrap

def generate_report(
    stats: dict,
    rest_results: list[dict],
    mcp_results: list[dict],
    source_prefixes_seen: set[str],
) -> str:
    """Generate VALIDATION.md content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total_queries = len(rest_results) + len(mcp_results)
    passed = sum(1 for r in rest_results if r["passed"]) + sum(1 for r in mcp_results if r["passed"])
    status = "PASS" if passed == total_queries else "FAIL"

    lines = [
        f"# End-to-End Validation Report",
        f"",
        f"**Generated:** {now}",
        f"**Status:** {status} ({passed}/{total_queries} queries passed)",
        f"",
        f"## Corpus Stats",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total chunks | {stats['total_chunks']:,} |",
    ]

    # Add by_source breakdown from /stats
    for source, count in stats.get("by_source", {}).items():
        lines.append(f"| {source} | {count:,} |")

    lines.append("")

    # Per-query sections...
    # (source-targeted, topic-based, MCP sections)

    return "\n".join(lines)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual Claude Desktop testing | Programmatic MCP client via `ClientSession` | MCP SDK 1.x (current) | Automated, reproducible MCP validation |
| pytest-only validation | Standalone script + Markdown report | Phase 24 design decision | Human-readable proof alongside automated checks |

**Deprecated/outdated:**
- None relevant -- the MCP SDK 1.x client API is current and stable in the installed version.

## Existing Codebase Assets

Key existing code that the validation script should leverage or be aware of:

| Asset | Location | Relevance |
|-------|----------|-----------|
| `/health` endpoint | `src/bbj_rag/health.py` | Prerequisites check (DB + Ollama) |
| `/search` endpoint | `src/bbj_rag/api/routes.py` | Primary query interface |
| `/stats` endpoint | `src/bbj_rag/api/routes.py` | Corpus stats for report |
| `SearchResponse` schema | `src/bbj_rag/api/schemas.py` | Response shape reference |
| `_query_report_data()` | `src/bbj_rag/intelligence/report.py` | Source-prefix SQL pattern (reference only) |
| `_SOURCE_URL_PREFIXES` | `src/bbj_rag/source_config.py` | Canonical source_url prefix map |
| `validation_cases.yaml` | `tests/validation_cases.yaml` | Existing query patterns (reference for query design) |
| `test_search_validation.py` | `tests/test_search_validation.py` | Existing pytest validation (different purpose) |
| `scripts/reset-db.sh` | `scripts/reset-db.sh` | Scripts directory convention |
| MCP server entry point | `bbj-mcp` console script | Spawned via `uv run bbj-mcp` |

## Source-to-Prefix Mapping (Canonical)

From `_SOURCE_URL_PREFIXES` in `source_config.py`:

| Logical Source | source_url Prefix | Parser | doc_type Value |
|----------------|-------------------|--------|----------------|
| Flare | `flare://` | `FlareParser` | `"flare"` |
| PDF | `pdf://` | `PdfParser` | varies (`"tutorial"`, `"concept"`, etc.) |
| MDX (DWC) | `mdx-dwc://` | `MdxParser` | `"tutorial"` |
| MDX (Beginner) | `mdx-beginner://` | `MdxParser` | `"tutorial"` |
| MDX (DB Mod) | `mdx-db-modernization://` | `MdxParser` | `"tutorial"` |
| BBj Source | `file://` | `BbjSourceParser` | `"example"` |
| Advantage | `https://basis.cloud/advantage...` | `AdvantageParser` | `"article"` |
| Knowledge Base | `https://basis.cloud/knowledge-base...` | `KnowledgeBaseParser` | `"article"` or `"concept"` |
| Web Crawl | `https://documentation.basis.cloud...` | `WebCrawlParser` | `"web_crawl"` |

For the "6 source" validation, group MDX variants together and WordPress variants together:
1. Flare (flare://)
2. PDF (pdf://)
3. MDX (mdx-*://)
4. BBj Source (file://)
5. WordPress (https://basis.cloud/...)
6. Web Crawl (https://documentation.basis.cloud/...)

## Query Design Recommendations (Claude's Discretion)

### Source-Targeted Queries (6 queries, one per source)

Each query should be designed to hit a specific source. Validation: top-1 result source_url matches the expected prefix.

| # | Target Source | Recommended Query | Expected Prefix | Rationale |
|---|--------------|-------------------|-----------------|-----------|
| 1 | Flare | "BBjWindow addButton method" | `flare://` | Core API method, heavily documented in Flare |
| 2 | PDF | "customer information program BBj GUI example" | `pdf://` | GUI programming guide content |
| 3 | MDX | "DWC web component tutorial getting started" | `mdx-dwc://` or `mdx-beginner://` | Tutorial content unique to MDX sources |
| 4 | BBj Source | "BBj sample source code PROCESS_EVENTS" | `file://` | Code examples unique to bbj-source parser |
| 5 | WordPress | "Advantage magazine BBj article" | `https://basis.cloud/` | Advantage/KB articles |
| 6 | Web Crawl | "documentation.basis.cloud BBj reference" | `https://documentation.basis.cloud/` | Web crawl content |

### Topic-Based Queries (5-10 queries)

Representative BBj topics that exercise the hybrid search across sources:

| # | Query | Topic Area |
|---|-------|------------|
| 1 | "How do I create a BBjGrid?" | UI components |
| 2 | "BBj string manipulation functions" | Language reference |
| 3 | "DWC web component styling CSS" | Modern web UI |
| 4 | "BBj database connection SQL" | Data access |
| 5 | "Event handling callbacks in BBj" | Event model |
| 6 | "BBj file I/O operations" | File handling |
| 7 | "Migration from Visual PRO/5 to BBj" | Migration guidance |

### MCP Validation Subset (3-4 queries)

Select a diverse subset from the combined query set:
- 1 source-targeted (e.g., Flare query)
- 2 topic-based (e.g., BBjGrid + event handling)
- Optional: 1 with generation filter

### Generation Filter Testing

**Recommendation: Include one generation-filtered query.** Low effort, demonstrates the feature works, and the REST API already supports it. Add one query with `generation: "dwc"` to the topic-based set.

## Open Questions

### 1. Content snippet length for relevance display

- What we know: CONTEXT says "~100 chars" for snippets
- What's unclear: Whether 100 chars is enough for a human to judge relevance
- Recommendation: Use ~150 chars with `textwrap.shorten()`, truncating at word boundaries. This is more readable while still compact.

### 2. Pass/fail heuristic for topic-based queries

- What we know: Source-targeted queries can check source_url prefix. Topic-based queries need a different signal.
- What's unclear: What automated heuristic is "good enough" for topic-based queries
- Recommendation: For topic-based queries, "pass" = at least 1 result returned AND top-1 result score is above 0 (non-zero RRF score). Any query returning results has passed through embedding + BM25, so the RRF fusion already provides a relevance signal. Document low-score results as potential issues in the report.

### 3. Script execution: standalone vs console script

- What we know: The script could be a standalone `python scripts/validate_e2e.py` or registered as a console script in pyproject.toml
- What's unclear: Whether to register it
- Recommendation: Standalone script in `scripts/` (like `reset-db.sh`). This is a one-time validation, not a daily tool. Keep it simple. Can be run with `uv run python scripts/validate_e2e.py`.

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `src/bbj_rag/api/routes.py` -- REST API endpoints and response schemas
- Codebase inspection: `src/bbj_rag/api/schemas.py` -- SearchRequest, SearchResponse, StatsResponse Pydantic models
- Codebase inspection: `src/bbj_rag/mcp_server.py` -- MCP server implementation (FastMCP, search_bbj_knowledge tool)
- Codebase inspection: `src/bbj_rag/search.py` -- Search functions (dense, bm25, hybrid, async_hybrid)
- Codebase inspection: `src/bbj_rag/source_config.py` -- _SOURCE_URL_PREFIXES canonical mapping
- Codebase inspection: `src/bbj_rag/intelligence/report.py` -- _query_report_data() SQL patterns
- Installed package inspection: `mcp/client/stdio/__init__.py` -- StdioServerParameters, stdio_client API
- Installed package inspection: `mcp/client/session.py` -- ClientSession.call_tool() API

### Secondary (MEDIUM confidence)
- Codebase inspection: `tests/test_search_validation.py` -- Existing validation pattern (pytest-based)
- Codebase inspection: `tests/validation_cases.yaml` -- Existing query patterns

### Tertiary (LOW confidence)
- Query design recommendations are based on understanding of the BBj documentation corpus structure from parser inspection, not from running actual queries against the live corpus. Actual query effectiveness will only be proven at runtime.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- No new dependencies; all APIs verified from installed code
- Architecture: HIGH -- Patterns derived from existing codebase conventions and verified SDK APIs
- Pitfalls: HIGH -- Identified from direct code inspection (stats endpoint grouping, MCP env vars, source mapping)

**Research date:** 2026-02-02
**Valid until:** 2026-03-04 (stable -- no fast-moving dependencies)
