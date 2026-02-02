# Plan 23-01: MCP Server Module + stdio Transport + Claude Desktop Config

**Status:** Complete
**Completed:** 2026-02-02

## What Was Built

Thin MCP server that proxies search requests to the existing REST API and returns LLM-optimized formatted text responses. Claude Desktop can invoke `search_bbj_knowledge` to retrieve relevant BBj documentation from the running system.

## Deliverables

| File | What it provides |
|------|-----------------|
| `rag-ingestion/src/bbj_rag/mcp_server.py` | MCP server module with `FastMCP`, `search_bbj_knowledge` tool, `_format_results` formatter, error handling |
| `rag-ingestion/pyproject.toml` | `mcp[cli]>=1.25,<2` dependency, `bbj-mcp` script entry |
| `~/Library/Application Support/Claude/claude_desktop_config.json` | `bbj-knowledge` server entry (stdio transport, uv runner) |
| `rag-ingestion/docker-compose.yml` | Individual source data volume mounts, `DATA_DIR=/data` env |
| `rag-ingestion/sql/schema.sql` | `rrf_score` bigint fix for `rank()` compatibility |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| `61bced3` | feat | Create MCP server module and wire dependencies |
| `479e13f` | fix | Mount source data dirs individually and add DATA_DIR env |
| `9ccf8d5` | fix | Use bigint for rrf_score to match rank() return type |

## Deviations

1. **Docker volume symlinks don't work** — Symlinks in a bind-mounted directory point to host paths that don't exist inside the container. Fixed by mounting each source repo as a separate volume in `docker-compose.yml`.

2. **rrf_score type mismatch** — PostgreSQL `rank()` returns `bigint` but `rrf_score()` was defined with `int` parameters. Never surfaced before because search hadn't been tested against a populated database. Fixed in both `schema.sql` and the live database.

3. **Claude Desktop config is outside the repo** — `claude_desktop_config.json` is a user-level file, not a project artifact. Task 2 has no repo commit (expected).

## Verification

- MCP server starts and responds to JSON-RPC (automated test passed)
- `search_bbj_knowledge` tool appears in Claude Desktop tool list (human verified)
- Tool returns formatted text results with titles, content, source URLs (human verified)
- Generation parameter schema: `enum: ["all", "character", "vpro5", "bbj-gui", "dwc"]` (automated)
- No `print()` calls in module (automated)
- Logging configured to stderr (automated)
- Ruff lint and mypy pass (automated)

## Requirements Covered

| Requirement | How |
|-------------|-----|
| MCP-01 | `search_bbj_knowledge` tool with matching JSON schema |
| MCP-02 | `mcp.run(transport="stdio")`, spawned by Claude Desktop |
| MCP-03 | `_format_results()` returns formatted text blocks |
| MCP-04 | `Literal["all", "character", "vpro5", "bbj-gui", "dwc"]` generates enum |
