# Phase 22: REST Retrieval API - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

FastAPI server inside the Docker app container exposes hybrid search over the ingested BBj documentation corpus, plus health and stats endpoints. The existing `/health` endpoint (Phase 20) is extended, not replaced. The MCP server (Phase 23) will consume these endpoints.

</domain>

<decisions>
## Implementation Decisions

### Search response shape
- Return top 10 results by default, caller can override with `limit` param (max 50)
- Each result includes: `content`, `title`, `source_url`, `doc_type`, `generations`, `score`
- Results ordered by RRF hybrid score descending
- No pagination — single result set per query (MCP and curl consumers don't need cursor-based pagination)
- Scores are raw RRF scores (no normalization to 0-1), matching the existing `SearchResult` dataclass

### Search parameters
- Required: `query` (string)
- Optional: `generation` (string) — filters to chunks matching this generation tag; `bbj-gui` normalized to `bbj_gui` automatically
- Optional: `limit` (int, default 10, max 50) — number of results to return
- No exposed knobs for keyword vs semantic weighting — hybrid RRF is the only search mode (the existing `hybrid_search()` function is the single entry point)
- No minimum score threshold exposed — return top-N regardless (filtering low-quality results is the MCP server's concern if needed)

### Error responses
- Consistent JSON error format: `{"detail": "message"}` (FastAPI default)
- Ollama unreachable during query embedding: HTTP 503 with detail explaining Ollama connectivity failure
- Database unreachable: HTTP 503 with detail explaining database connectivity failure
- Empty/missing query: HTTP 422 (FastAPI validation default)
- No results found: HTTP 200 with empty `results` array (not an error)

### Health endpoint extension
- Extend existing `/health` to continue returning database and Ollama status
- Add readiness distinction: healthy (all components up) vs degraded (partial) vs unhealthy (critical down)
- HTTP 200 for healthy, HTTP 503 for degraded/unhealthy

### Stats endpoint
- `/stats` returns chunk counts grouped by `source` (doc_type) and by `generation`
- Include total chunk count
- No ingestion timestamps or index health metrics — keep it simple for Phase 22

### Claude's Discretion
- Connection pooling strategy (asyncpg pool vs per-request connections)
- Whether to make search async or sync (existing search.py is sync — may need async wrapper)
- Pydantic response model structure and naming
- OpenAPI documentation details
- Startup embedding warm-up (whether to pre-load the embedding model)

</decisions>

<specifics>
## Specific Ideas

- The existing `SearchResult` dataclass in `search.py` already has the fields needed — the API response model should mirror it closely
- `hybrid_search()` already accepts `generation_filter` — the API just needs to wire the query param through
- The existing `app.py` lifespan already validates Ollama connectivity — reuse that pattern for health checks
- Generation normalization (`bbj-gui` → `bbj_gui`) should happen at the API layer before passing to search

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 22-rest-retrieval-api*
*Context gathered: 2026-02-01*
