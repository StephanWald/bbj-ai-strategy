# Feature Landscape: RAG Deployment Service (v1.4)

**Domain:** RAG retrieval API + MCP server + Docker deployment for BBj documentation
**Researched:** 2026-02-01
**Overall confidence:** HIGH (existing codebase analyzed, MCP SDK patterns verified, Docker/pgvector patterns well-established)
**Supersedes:** Previous FEATURES.md covered v1.3 MCP architecture content updates. That milestone shipped. This document covers the features needed to deploy the existing RAG ingestion pipeline as a running Docker-based service with REST API and MCP server.

---

## Research Context

### What Already Exists

The RAG ingestion pipeline is **code-complete** (v1.2). The following are built, tested (310 tests), and working:

| Component | Module | What It Does |
|-----------|--------|-------------|
| 6 parsers | `parsers/flare.py`, `parsers/pdf.py`, `parsers/mdx.py`, `parsers/bbj_source.py`, `parsers/wordpress.py`, `parsers/web_crawl.py` | Parse Flare XHTML, PDFs, MDX, BBj source, WordPress (Advantage + KB), web crawl |
| Chunker | `chunker.py` | Heading-aware splitting, 400-token chunks, 50-token overlap, code block preservation |
| Intelligence | `intelligence/` | Multi-signal generation tagging (all/character/vpro5/bbj_gui/dwc), doc type classification (7 types), context headers |
| Embedder | `embedder.py` | Ollama (primary) + OpenAI (fallback), Protocol-based abstraction |
| Search | `search.py` | Dense vector (cosine), BM25 (tsvector), hybrid RRF -- all with optional `generation_filter` |
| DB layer | `db.py` | psycopg3 with pgvector, binary COPY bulk inserts, content-hash dedup |
| Schema | `sql/schema.sql` | HNSW index, GIN indexes on tsvector and generations array, `rrf_score()` function |
| Pipeline | `pipeline.py` | Full orchestration: parse -> intelligence -> chunk -> embed -> bulk insert |
| CLI | `cli.py` | Click-based: `bbj-rag ingest`, `parse`, `report`, `validate` |
| Config | `config.py` | pydantic-settings with TOML + env var override (`BBJ_RAG_` prefix) |
| Quality | `intelligence/report.py` | Post-ingestion quality report with anomaly detection |

### What v1.4 Adds

v1.4 wraps the existing pipeline in a deployable service:

1. **Docker Compose** -- pgvector container + Python app container, `docker compose up` runs everything
2. **REST API** -- HTTP layer on top of `search.py` so external tools can query
3. **MCP server** -- Thin wrapper exposing `search_bbj_knowledge` tool matching Ch2's JSON schema
4. **Ingestion orchestration** -- Run all 6 parsers in sequence from Docker, with real data paths configured
5. **Multi-MDX support** -- Config currently supports one `mdx_source_path`; need list for 3 MDX tutorial sites

### What v1.4 Does NOT Add

Per PROJECT.md "Out of Scope":
- `generate_bbj_code` MCP tool (requires fine-tuned model, not yet ready)
- `validate_bbj_syntax` MCP tool (requires compiler integration)
- Authentication/access control
- Agentic RAG (query routing, multi-step reasoning)
- Cloud/production hosting
- CI/CD pipeline for ingestion
- Embedding fine-tuning

---

## Table Stakes

Features users expect from a working RAG deployment service. Missing any of these means "it does not work."

### REST Retrieval API

| Feature | Why Expected | Complexity | Depends On | Notes |
|---------|-------------|------------|------------|-------|
| **`POST /search` endpoint** | The core purpose of the service. Takes a query string, returns ranked chunks. Every RAG API has this. | Low | `search.py` (exists) | Thin HTTP layer over existing `hybrid_search()`. Must embed the query text before searching. |
| **`generation` filter parameter** | BBj's defining characteristic is 4 generations. The existing `search.py` already supports `generation_filter` on all 3 search functions. Ch2's `search_bbj_knowledge` schema requires it. | Low | `search.py` generation_filter (exists) | Enum: `all`, `character`, `vpro5`, `bbj_gui`, `dwc`. Optional -- omit for cross-generation search. Note: Ch2 schema uses `"bbj-gui"` but DB stores `"bbj_gui"` (underscore). API must accept both or normalize. |
| **`limit` parameter** | Standard pagination/result-count control. Ch2 schema specifies `"default": 5`. | Low | `search.py` limit parameter (exists) | Default 5, max 20 is reasonable. |
| **Structured JSON response** | Callers need machine-parseable results. Must include: content, source_url, title, doc_type, generations, score. | Low | `SearchResult` dataclass (exists) | Map `SearchResult` fields directly to JSON. Add `context_header` to response -- it exists in the DB but `SearchResult` currently omits it. |
| **Source citations in results** | RAG best practice: every result must link back to its source. `source_url` field already exists in `SearchResult`. URLs use scheme prefixes: `flare://`, `pdf://`, `file://`, `mdx://`, `https://`. | Low | `SearchResult.source_url` (exists) | No transformation needed -- pass through as-is. Consumer decides how to render. |
| **Query embedding on the fly** | The search endpoint receives text, not vectors. Must embed the query using the same model as ingestion. | Medium | `embedder.py` (exists) | Requires Ollama reachable from Docker container at query time. The embedder must be initialized once at startup and reused. |
| **`GET /health` endpoint** | Standard operational check. Docker Compose healthcheck, monitoring, and load balancers need this. | Low | DB connection (exists) | Check: (1) DB connection alive, (2) chunks table has rows, (3) Ollama reachable. Return 200 or 503 with component status. |
| **`doc_type` filter parameter** | The existing schema has 7 doc types + 2 from non-Flare parsers (`article`, `tutorial`). Filtering by doc type is expected when the data supports it. | Low | `chunks` table `doc_type` column (exists) | Add WHERE clause. Not in Ch2's MCP schema but natural for REST API. Optional parameter. |

### MCP Server (`search_bbj_knowledge`)

| Feature | Why Expected | Complexity | Depends On | Notes |
|---------|-------------|------------|------------|-------|
| **`search_bbj_knowledge` tool** | Ch2 defines this with exact JSON schema (query, generation, limit). This is the one MCP tool for v1.4. | Medium | REST API or direct `search.py` call | Use MCP Python SDK (`mcp` package, v1.x). The `@mcp.tool()` decorator auto-generates the tool schema from Python type annotations and docstring. |
| **Match Ch2's input schema** | Ch2 specifies: `query` (string, required), `generation` (string enum, optional), `limit` (integer, default 5). The MCP tool MUST match this contract. | Low | Ch2 JSON schema (documented) | Python function signature with type annotations maps directly. `generation: str | None = None`, `limit: int = 5`. |
| **Formatted text response** | MCP tools return content to an LLM. The response should be formatted text (not raw JSON) optimized for LLM consumption: chunk content with source URL, title, doc_type as metadata headers. | Low | `SearchResult` (exists) | Format each result as a text block: `## {title}\nSource: {source_url}\nType: {doc_type} | Generations: {generations}\n\n{content}`. Score is useful for debugging but not for LLM consumption -- omit or include at end. |
| **stdio transport** | Default MCP transport for local development. Claude Desktop, Cursor, VS Code all use stdio for local MCP servers. This is the v1.4 target. | Low | MCP Python SDK | `mcp.run(transport="stdio")` -- literally one line. |
| **Streamable HTTP transport** | Ch2 describes remote deployment via Streamable HTTP. While v1.4 targets local Docker, supporting HTTP transport makes the MCP server usable by remote clients. | Low | MCP Python SDK | `mcp.run(transport="streamable-http")` -- also one line. Transport selected by config/CLI flag. |

### Docker Deployment

| Feature | Why Expected | Complexity | Depends On | Notes |
|---------|-------------|------------|------------|-------|
| **`docker compose up` starts everything** | The definition of "it just works." One command, service is running. | Medium | Dockerfile, docker-compose.yml | Two services: `db` (pgvector/pgvector:pg17) and `app` (Python). Schema auto-applied on startup. |
| **pgvector container with persistent volume** | Data survives container restarts. Without volume, re-ingestion needed after every `docker compose down`. | Low | pgvector Docker image | Named volume for `/var/lib/postgresql/data`. Init script mounts `schema.sql` to `/docker-entrypoint-initdb.d/`. |
| **Schema auto-application** | The `chunks` table and indexes must exist before ingestion or search. `schema.sql` uses `IF NOT EXISTS` throughout -- safe to run repeatedly. | Low | `schema.sql` (exists, idempotent) | Two paths: (1) init script for fresh DB, (2) Python `apply_schema()` call on app startup for migrations. |
| **Ollama on host, not in container** | PROJECT.md decision: "Host Ollama (not containerized)." Avoids duplicating large model images. Ollama already runs on the developer's machine. | Low | `extra_hosts` Docker config | App container uses `host.docker.internal:11434` for Ollama. Requires `extra_hosts: - host.docker.internal:host-gateway` on Linux. macOS/Windows Docker Desktop handles this natively. |
| **Environment variable configuration** | Docker containers configure via env vars. The existing `Settings` class already supports `BBJ_RAG_` env var prefix. | Low | `config.py` BBJ_RAG_ prefix (exists) | `BBJ_RAG_DATABASE_URL`, `BBJ_RAG_EMBEDDING_MODEL`, etc. Docker Compose `environment:` section maps to these. |
| **Ingestion command from Docker** | Must be able to run `docker compose run app bbj-rag ingest --source flare` (and all 6 sources). | Low | CLI `ingest` command (exists) | The CLI already handles all 6 sources. Docker just needs correct volume mounts for source data. |

### Ingestion Orchestration

| Feature | Why Expected | Complexity | Depends On | Notes |
|---------|-------------|------------|------------|-------|
| **`ingest-all` command or script** | Running 6 separate `bbj-rag ingest --source X` commands is tedious. Need a single command that ingests all sources in sequence. | Low | CLI `ingest` command (exists) | Either: (1) new Click command `bbj-rag ingest-all`, or (2) shell script `ingest-all.sh` that calls ingest 6 times. Shell script is simpler and sufficient for v1.4. |
| **Source data volume mounts** | Flare XHTML, PDFs, MDX tutorials, BBj source code -- all live on the host filesystem. Docker containers need read access via bind mounts. | Low | Docker Compose volumes | Mount as read-only: `-v /Users/beff/bbjdocs:/data/flare:ro`, etc. Config points to `/data/flare` inside container. |
| **Idempotent re-ingestion** | Running ingestion twice must not create duplicates. The existing pipeline uses `ON CONFLICT (content_hash) DO NOTHING`. | Low | `db.py` content-hash dedup (exists) | Already works. The `resume` flag in pipeline.py also allows skipping already-embedded chunks. |
| **Progress logging** | Ingestion of 7,000+ Flare topics takes time. Users need to see progress. | Low | `pipeline.py` batch logging (exists) | Already logs: "Batch stored: X/Y chunks (total: Z docs parsed)". Good enough for v1.4. |
| **Quality report after ingestion** | The `report` command and auto-report after ingest already exist. Must work in Docker context. | Low | `intelligence/report.py` (exists) | Already integrated into `ingest` command. Prints source/generation/doc_type distribution + anomaly warnings. |
| **Multi-MDX source support** | Config has `mdx_source_path: str` (singular). There are 3 MDX tutorial sites (DWC, beginner, DB modernization). Need `mdx_source_dirs: list[str]`. | Low | `config.py` + `parsers/mdx.py` | Change config field from `str` to `list[str]`. Update parser to iterate directories. Or run `ingest --source mdx` 3 times with different env var overrides. |

---

## Differentiators

Features that make this RAG service particularly useful for the BBj domain. Not required for basic functionality, but high-value given the project context.

### Generation-Aware Search (Already Built)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Generation filtering across all search modes** | No other RAG service has BBj generation awareness. The existing `search.py` supports `generation_filter` on dense, BM25, and hybrid search -- the data model (GIN-indexed `generations` array) and query logic are already built. This is the core differentiator. | Already built | This is table-stakes for the BBj use case but a differentiator in the RAG ecosystem. Most RAG APIs do not have domain-specific metadata filtering this clean. |
| **Hybrid RRF scoring** | Dense vectors catch semantic similarity, BM25 catches exact keyword matches (critical for BBj API names like `BBjVector.addItem` which are not natural language). RRF fusion is already implemented with a custom `rrf_score()` SQL function. | Already built | Default search mode should be `hybrid`. Expose `mode` parameter on REST API: `dense`, `bm25`, `hybrid` (default). |

### BBj-Specific Response Enhancement

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **`context_header` in results** | The `context_header` field provides section path context (e.g., "BBj Objects > BBjWindow > Methods > addButton"). This helps LLMs understand where a chunk sits in the documentation hierarchy. Currently stored in DB but NOT included in `SearchResult` dataclass. | Low | Add `context_header` to `SearchResult`. One extra column in the SELECT. High value for LLM prompt assembly. |
| **`deprecated` flag in results** | Chunks from deprecated APIs carry `deprecated = true`. Surfacing this lets LLMs warn users about deprecated patterns. Currently in DB but NOT in `SearchResult`. | Low | Add `deprecated` to `SearchResult`. Lets MCP tool annotate results: "Note: this API is deprecated." |
| **Search mode selection** | Expose `mode` parameter: `dense` (semantic), `bm25` (keyword), `hybrid` (default). Different query types benefit from different modes. API name lookups benefit from BM25; conceptual questions benefit from dense. | Low | Route to appropriate `search.py` function based on `mode` parameter. |
| **Doc type filtering on API** | Allow filtering by `doc_type` (e.g., only `api-reference` or only `example`). Useful when an LLM wants only code examples, not conceptual docs. | Low | Add WHERE clause. Not in MCP schema but useful for REST API power users and future MCP enhancement. |

### Operational Visibility

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **`GET /stats` endpoint** | Return chunk counts by source, generation, and doc_type. Reuses `_query_report_data()` from `intelligence/report.py`. Lets operators verify ingestion completeness without SSH into container. | Low | `report.py` query functions (exist) | JSON response with same data as CLI `report` command. |
| **Structured health check** | Beyond basic 200/503, return component status: `{"database": "ok", "ollama": "ok", "chunks_count": 12345}`. Useful for debugging connection issues. | Low | Ping DB + Ollama + count query | Ollama check: HTTP GET to `host.docker.internal:11434/api/version`. DB check: `SELECT 1`. Count: `SELECT COUNT(*) FROM chunks`. |

---

## Anti-Features

Features to deliberately NOT build for v1.4. Each would add complexity without matching the milestone goal of "it just works."

### Premature Scaling

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Authentication / API keys** | v1.4 runs locally via Docker Compose. No external users. Auth adds complexity with zero benefit for a local dev service. | Skip entirely. Note in docs that auth is needed for production/shared deployment (future milestone). |
| **Rate limiting** | Local service, single user. Rate limiting solves a problem that does not exist yet. | Skip. |
| **HTTPS / TLS termination** | Local Docker network. HTTPS adds certificate management complexity. | Skip. Use plain HTTP on `localhost`. |
| **Horizontal scaling / load balancing** | Single-user local deployment. The API handles one query at a time fine. | Single process, single container. |
| **Connection pooling** | psycopg3 supports connection pooling but the existing `get_connection()` opens a single connection. For a local service handling sequential queries, pooling is premature. | Use single connection per request or a minimal pool (e.g., psycopg_pool with min=1, max=5) if FastAPI needs async. |

### Agentic / Advanced RAG

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Query rewriting / expansion** | Agentic RAG feature. Explicitly out of scope per PROJECT.md. The hybrid search already handles both semantic and keyword matching. | Pass query directly to search. Let the consuming LLM do query formulation -- it is better at it anyway. |
| **Multi-step retrieval** | Agentic pattern where initial results inform follow-up queries. Out of scope. | Single-step retrieval. One query, one result set. |
| **Answer generation endpoint** | A `/answer` endpoint that retrieves + generates a response. This requires the fine-tuned model (not ready) and conflates retrieval with generation. | Retrieval only. The MCP client (Claude, Cursor) handles prompt assembly and generation. The RAG service just returns relevant chunks. |
| **Conversation memory / session state** | Chat-style RAG with conversation history. This belongs in the documentation chat system (future milestone), not the retrieval API. | Stateless API. Each request is independent. |
| **Re-ranking with cross-encoder** | Advanced retrieval technique. The hybrid RRF already provides good ranking. Cross-encoder adds latency and model dependency. | Use existing RRF ranking. Evaluate quality first; add re-ranking only if retrieval quality is insufficient. |

### Future MCP Tools

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **`generate_bbj_code` MCP tool** | Requires fine-tuned model, which is still in training. Cannot implement without the backend. PROJECT.md explicitly defers this. | Implement only `search_bbj_knowledge`. The MCP server architecture supports adding tools later -- just add another `@mcp.tool()` function. |
| **`validate_bbj_syntax` MCP tool** | Requires BBj compiler integration in Docker, which is a separate infrastructure challenge (BBj runtime licensing, compiler binary distribution). | Defer to compiler integration milestone. |
| **MCP Resources or Prompts** | MCP supports Resources (read-only data) and Prompts (templates) beyond Tools. No use case defined for v1.4. | Tools only. Note expansion possibilities in architecture docs. |
| **MCP sampling / multi-agent** | Advanced MCP patterns. No use case for a retrieval-only service. | Skip entirely. |

### Over-Engineering the API

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **OpenAPI / Swagger documentation** | Nice-to-have but the API has 2-3 endpoints. The overhead of setting up Swagger is not justified for a service whose primary consumer is the MCP tool (which does not use REST). | Document endpoints in README. FastAPI generates OpenAPI automatically if used -- get it for free but do not invest time in customizing it. |
| **Pagination with cursors** | The API returns 5-20 results max. Cursor-based pagination solves a problem that does not exist at this result-set size. | `limit` parameter is sufficient. Max 20 results. |
| **Webhook / streaming results** | Results are small (5-20 chunks, each ~400 tokens). Total response under 50KB. No streaming needed. | Synchronous JSON response. |
| **Async ingestion API** | A `POST /ingest` endpoint that triggers background ingestion. Adds job queue complexity. Ingestion is a one-time operation, not a continuous API workload. | CLI command only. `docker compose run app bbj-rag ingest-all`. Ingestion is an operator task, not an API consumer task. |
| **GraphQL** | One query pattern (search). GraphQL adds complexity for no benefit over a simple POST endpoint. | REST (or just POST to a single endpoint). |

---

## Feature Dependencies

### Dependency Chain

```
Docker Compose (db + app containers)
  --> Schema auto-applied (pgvector extension + chunks table)
  --> Ingestion orchestration (all 6 sources via CLI)
  --> Embedder initialization (Ollama reachable from container)
  --> REST API (FastAPI on top of search.py)
  --> MCP server (wraps search via @mcp.tool, consumes same embedder)
```

### Critical Path

1. **Docker Compose with pgvector** must work first (everything depends on the database)
2. **Ollama connectivity from Docker** must work second (embedding depends on it)
3. **Ingestion pipeline in Docker** must run successfully with real data
4. **REST API** wraps existing search module
5. **MCP server** wraps existing search module (independent of REST API -- both can proceed in parallel)

### Existing Code Reuse Map

| v1.4 Feature | Existing Code It Wraps | New Code Needed |
|-------------|----------------------|----------------|
| REST search endpoint | `search.py` (hybrid_search, dense_search, bm25_search) | FastAPI route, request/response models |
| Query embedding | `embedder.py` (OllamaEmbedder) | Startup initialization, singleton embedder |
| MCP search_bbj_knowledge | `search.py` + `embedder.py` | `@mcp.tool()` decorated function, ~30 lines |
| Docker pgvector | `sql/schema.sql` | Dockerfile, docker-compose.yml |
| Ingestion in Docker | `cli.py` (ingest command), `pipeline.py` | Volume mounts, env var config, ingest-all script |
| Health check | `db.py` (get_connection) | Health endpoint, Ollama ping |
| Stats endpoint | `intelligence/report.py` (_query_report_data) | FastAPI route returning JSON |
| Config for Docker | `config.py` (BBJ_RAG_ env vars) | docker-compose.yml environment section |

---

## MCP Tool Contract Alignment

### Ch2 `search_bbj_knowledge` Schema (Source of Truth)

From `/Users/beff/_workspace/bbj-ai-strategy/docs/02-strategic-architecture/index.md`:

```json
{
  "name": "search_bbj_knowledge",
  "description": "Search BBj documentation and code examples with generation-aware filtering. Returns ranked results from the RAG pipeline with source citations.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "Natural language search query" },
      "generation": { "type": "string", "enum": ["all", "character", "vpro5", "bbj-gui", "dwc"], "description": "Filter results by BBj generation. Omit for cross-generation search." },
      "limit": { "type": "integer", "default": 5, "description": "Maximum number of results to return" }
    },
    "required": ["query"]
  }
}
```

### Implementation Mapping

| Ch2 Schema | Python Function Signature | Notes |
|-----------|--------------------------|-------|
| `query` (string, required) | `query: str` | Direct mapping |
| `generation` (string enum, optional) | `generation: str \| None = None` | **IMPORTANT:** Ch2 uses `"bbj-gui"` (hyphen) but DB stores `"bbj_gui"` (underscore). Normalize on input: `generation.replace("-", "_")`. |
| `limit` (integer, default 5) | `limit: int = 5` | Direct mapping |

### Generation Value Normalization

The `Generation` StrEnum produces these values: `all`, `character`, `vpro5`, `bbj_gui`, `dwc`.

Ch2's schema uses `"bbj-gui"` (hyphenated). The implementation must accept both:
- `"bbj-gui"` (from MCP clients following Ch2 schema)
- `"bbj_gui"` (from internal/direct API use)

Simple normalization: `value.replace("-", "_")` before passing to `search.py`.

### MCP SDK Pattern (Verified)

Using the official `mcp` Python SDK (v1.x, package: `mcp`):

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("bbj-rag")

@mcp.tool()
async def search_bbj_knowledge(
    query: str,
    generation: str | None = None,
    limit: int = 5,
) -> str:
    """Search BBj documentation and code examples with generation-aware filtering.
    Returns ranked results from the RAG pipeline with source citations."""
    # Normalize generation value
    # Embed query via Ollama
    # Call hybrid_search()
    # Format results as text for LLM consumption
    ...
```

The `@mcp.tool()` decorator auto-generates the MCP tool schema from the function signature and docstring. Type annotations become JSON Schema types. Default values become schema defaults. The docstring becomes the tool description.

**Confidence: HIGH** -- verified against MCP Python SDK documentation and PyPI (v1.26.0 current).

---

## Per-Component Recommendations

### REST API: Use FastAPI

**Recommendation:** FastAPI, because it provides automatic OpenAPI docs for free, async support for concurrent embedding requests, Pydantic model validation (the project already uses Pydantic), and is the standard choice for Python RAG APIs.

**NOT Flask, NOT Django:** Flask lacks async. Django is too heavy. FastAPI is the consensus choice for this workload.

**Endpoints:**

| Method | Path | Purpose | Response |
|--------|------|---------|----------|
| POST | `/search` | Primary search endpoint | `{ results: [...], query: str, mode: str, count: int }` |
| GET | `/health` | Health check | `{ status: "ok"/"degraded", database: "ok"/"error", ollama: "ok"/"error", chunks_count: int }` |
| GET | `/stats` | Ingestion statistics | `{ by_source: {...}, by_generation: {...}, by_doc_type: {...}, total: int }` |

Three endpoints. Simple, focused, sufficient.

### MCP Server: Use Official SDK (`mcp` package)

**Recommendation:** Use the `mcp` package (official Python SDK, v1.x) with `FastMCP` from `mcp.server.fastmcp`. This is the standard, widely adopted approach (70% of MCP servers use some variant of FastMCP).

**NOT standalone `fastmcp` package:** The standalone version has diverged into v3 beta. The official SDK bundles FastMCP and is more stable for production.

**Transport:** Support both `stdio` (default, for Claude Desktop / local use) and `streamable-http` (for Docker / remote access). Select via environment variable or CLI flag.

### Docker: Use `pgvector/pgvector:pg17` Image

**Recommendation:** Official pgvector Docker image. Pre-built, maintained, no custom Dockerfile for the database.

**App container:** Python 3.12 slim image, install project via `pip install .`, expose port 8000 for REST API.

**Ollama:** Not containerized. Use `host.docker.internal:11434` with `extra_hosts` for Linux compatibility.

---

## MVP Feature Set (Ordered)

For v1.4, implement in this order:

1. **Docker Compose** -- pgvector container, app container, schema init, Ollama connectivity
2. **Configuration for real data** -- volume mounts for all 6 sources, env vars for paths
3. **Multi-MDX support** -- expand config to accept list of MDX directories
4. **Ingest-all script** -- single command to run all 6 parsers in sequence
5. **REST API** -- `/search`, `/health`, `/stats` endpoints via FastAPI
6. **MCP server** -- `search_bbj_knowledge` tool via `@mcp.tool()` with stdio + HTTP transport
7. **End-to-end validation** -- query the running system, verify relevant BBj docs come back

### Deferred to Future Milestones

| Feature | Why Defer | When |
|---------|----------|------|
| `generate_bbj_code` MCP tool | Fine-tuned model not ready | After model fine-tuning milestone |
| `validate_bbj_syntax` MCP tool | Compiler integration not ready | After compiler integration milestone |
| Authentication | No external users in v1.4 | Production deployment milestone |
| Re-ranking | Evaluate retrieval quality first | If quality metrics show need |
| Conversation memory | Belongs in chat system | Documentation chat milestone |
| Async ingestion API | CLI sufficient for operator use | If continuous ingestion needed |

---

## Sources

### HIGH Confidence (Codebase Analysis + Official Documentation)

- Existing codebase: All modules in `rag-ingestion/src/bbj_rag/` read and analyzed
- Ch2 MCP tool schemas: `/Users/beff/_workspace/bbj-ai-strategy/docs/02-strategic-architecture/index.md` lines 166-180
- PROJECT.md scope: `/Users/beff/_workspace/bbj-ai-strategy/.planning/PROJECT.md` -- v1.4 target features and out-of-scope
- MCP Python SDK: [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) -- v1.26.0 on PyPI, FastMCP bundled
- MCP PyPI: [pypi.org/project/mcp/](https://pypi.org/project/mcp/) -- v1.26.0 (2026-01-24)
- pgvector Docker: [hub.docker.com/r/pgvector/pgvector](https://hub.docker.com/r/pgvector/pgvector) -- pg17 tag available

### MEDIUM Confidence (WebSearch Verified with Multiple Sources)

- FastAPI as standard for RAG APIs: [DataCamp tutorial](https://www.datacamp.com/tutorial/building-a-rag-system-with-langchain-and-fastapi), [Real Python MCP guide](https://realpython.com/python-mcp/), [DevelopersVoice framework comparison](https://developersvoice.com/blog/python/fastapi_django_flask_architecture_guide/)
- Docker host.docker.internal pattern: [Docker Community Forums](https://forums.docker.com/t/how-to-link-my-ollama-with-my-app-in-docker/144682), [DEV Community Ollama Docker guide](https://dev.to/ajeetraina/the-ollama-docker-compose-setup-with-webui-and-remote-access-via-cloudflare-1ion)
- MCP transport recommendations: [MCP SDK docs](https://modelcontextprotocol.github.io/python-sdk/) -- Streamable HTTP recommended for production
- RAG citation best practices: [Tensorlake citation-aware RAG](https://www.tensorlake.ai/blog/rag-citations), [Cohere RAG citations](https://docs.cohere.com/docs/rag-citations)
- RAG health monitoring: [apxml.com RAG health dashboards](https://apxml.com/courses/optimizing-rag-for-production/chapter-6-advanced-rag-evaluation-monitoring/rag-system-health-dashboards)

### LOW Confidence (Single Source, Needs Validation at Implementation Time)

- MCP SDK v2 timeline (Q1 2026): mentioned in SDK README, actual release date unconfirmed -- pin to v1.x for stability
- FastMCP standalone v3 beta status: [fastmcp PyPI](https://pypi.org/project/fastmcp/) -- v3.0.0b1 pre-release, avoid for production
