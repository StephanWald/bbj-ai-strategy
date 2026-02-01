# Phase 23: MCP Server - Research

**Researched:** 2026-02-02
**Domain:** Model Context Protocol (MCP) Python server with stdio transport
**Confidence:** HIGH

## Summary

Phase 23 implements a thin MCP server that runs on the host machine (not inside Docker), communicates via stdio transport with Claude Desktop, and proxies search requests to the existing REST API running on `localhost:10800`. The MCP server exposes a single tool (`search_bbj_knowledge`) that accepts a query and optional generation filter, calls the REST `/search` endpoint via HTTP, and formats the results as human-readable text blocks optimized for LLM consumption.

The standard approach uses the official `mcp` Python SDK v1.x (specifically `mcp.server.fastmcp.FastMCP`) with `httpx` for async HTTP calls to the REST API. The server is a single Python file with minimal dependencies, run via `uv` from the `claude_desktop_config.json`. The architecture is intentionally simple: the REST API handles all search complexity (embedding, hybrid RRF, generation normalization), and the MCP server is just a formatting layer.

The MCP Python SDK v1.x is the recommended production version (pin to `mcp>=1.25,<2`). SDK v2 is in pre-alpha and expected Q1 2026 but is not yet stable. The v1.x `FastMCP` class provides decorator-based tool definition with automatic JSON schema generation from Python type hints and docstrings.

**Primary recommendation:** Use the official `mcp` SDK v1.x with `FastMCP`, a single-file MCP server that calls the REST API via `httpx`, and configure Claude Desktop to spawn it with `uv run`.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `mcp` | >=1.25,<2 | MCP protocol SDK (FastMCP high-level API) | Official SDK from modelcontextprotocol; v1.x is production-recommended |
| `httpx` | >=0.28,<1 | Async HTTP client to call REST API | Already a project dependency; async-native; used in official MCP examples |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@modelcontextprotocol/inspector` | latest (npx) | Visual testing/debugging of MCP servers | Development and verification; not a Python dependency |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Official `mcp` SDK | Standalone `fastmcp` (jlowin) | Standalone has more features (OpenAPI gen, composition) but is a separate project; official SDK is simpler and sufficient for a single-tool server |
| `httpx` | `requests` | `requests` is sync-only; `httpx` is already a dependency and supports async |
| `mcp` v2 (`MCPServer`) | `mcp` v1 (`FastMCP`) | v2 is pre-alpha, not production-ready; v1.x has 6+ months of continued support |

**Installation:**
```bash
# In the rag-ingestion directory (adds to existing pyproject.toml)
uv add "mcp[cli]>=1.25,<2"
```

Note: `httpx` is already a dependency in `pyproject.toml` (>=0.28,<1).

## Architecture Patterns

### Recommended Project Structure
```
rag-ingestion/
├── src/bbj_rag/
│   ├── mcp_server.py       # MCP server entry point (single file)
│   ├── api/                 # Existing REST API (unchanged)
│   │   ├── routes.py
│   │   └── schemas.py
│   └── ...
├── pyproject.toml           # Add mcp dependency + bbj-mcp script entry
└── ...
```

The MCP server lives inside the existing `bbj_rag` package as a single module. This keeps it in the same codebase and allows sharing the `httpx` dependency version pin, while maintaining clear separation from the REST API code.

### Pattern 1: Thin MCP Proxy over REST API
**What:** The MCP server does NOT access the database directly. It calls the REST API at `http://localhost:10800/search` via HTTP, which handles embedding, hybrid search, and generation normalization. The MCP server's only job is (1) accept tool invocations, (2) call the REST API, and (3) format results as text.
**When to use:** When a REST API already exists and encapsulates all search logic.
**Why:** Clean separation of concerns. The REST API can be tested independently. The MCP server is trivially simple. Docker networking is not a concern because the MCP server runs on the host.

```python
# Source: Official MCP docs + project REST API
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("bbj-knowledge")

API_BASE = "http://localhost:10800"

@mcp.tool()
async def search_bbj_knowledge(
    query: str,
    generation: str | None = None,
    limit: int = 5,
) -> str:
    """Search BBj documentation and code examples with generation-aware filtering.

    Returns ranked results from the RAG pipeline with source citations.

    Args:
        query: Natural language search query about BBj programming
        generation: Filter by BBj generation (all, character, vpro5, bbj_gui, dwc).
                    Omit for cross-generation search.
        limit: Maximum number of results to return (1-50, default 5)
    """
    payload = {"query": query, "limit": limit}
    if generation and generation != "all":
        payload["generation"] = generation

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{API_BASE}/search", json=payload)
        resp.raise_for_status()

    data = resp.json()
    return _format_results(data)
```

### Pattern 2: LLM-Optimized Text Formatting
**What:** Tool returns formatted text blocks (not raw JSON). Each result includes title, content, context header, source URL, and deprecation status in a readable format.
**When to use:** MCP-03 requires formatted text optimized for LLM consumption.

```python
def _format_results(data: dict) -> str:
    """Format REST API search results as LLM-friendly text blocks."""
    results = data.get("results", [])
    if not results:
        return f"No results found for query: {data.get('query', '')}"

    blocks = []
    for i, r in enumerate(results, 1):
        header = f"## Result {i}: {r['title']}"
        if r.get("deprecated"):
            header += " [DEPRECATED]"
        parts = [header]
        if r.get("context_header"):
            parts.append(f"*{r['context_header']}*")
        parts.append(r["content"])
        parts.append(f"Source: {r['source_url']}")
        if r.get("generations"):
            parts.append(f"Generations: {', '.join(r['generations'])}")
        blocks.append("\n".join(parts))

    return f"Found {len(results)} results for: {data['query']}\n\n" + "\n\n---\n\n".join(blocks)
```

### Pattern 3: stdio Entry Point
**What:** The server runs with `mcp.run(transport="stdio")` and is spawned by Claude Desktop as a subprocess.
**When to use:** Always for local Claude Desktop integration.

```python
# Bottom of mcp_server.py
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Anti-Patterns to Avoid
- **Direct database access from MCP server:** The MCP server runs on the host, not in Docker. Connecting directly to the database would bypass the REST API's embedding logic and require duplicating the Ollama client setup. Always proxy through the REST API.
- **Writing to stdout:** NEVER use `print()` in an MCP stdio server. stdout is the JSON-RPC communication channel. Use `logging` configured to write to stderr.
- **Returning raw JSON:** The tool should return formatted text, not `json.dumps(response)`. LLMs consume text much better than raw JSON.
- **Hardcoding the API URL:** Use an environment variable (`BBJ_RAG_API_URL`) with a default of `http://localhost:10800` so the URL is configurable via `claude_desktop_config.json`'s `env` field.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP protocol handling | Custom JSON-RPC over stdio | `mcp` SDK `FastMCP` | Protocol is complex (tool discovery, schema generation, content types); SDK handles it all |
| JSON Schema from Python types | Manual schema dict | FastMCP auto-generation from type hints | Docstrings become descriptions, type hints become schema; no manual mapping needed |
| Tool parameter validation | Manual type checking | FastMCP + Pydantic (built-in) | SDK validates inputs against the generated schema automatically |
| Claude Desktop config format | Manual JSON editing instructions | Documented `claude_desktop_config.json` pattern | Well-established format with `command`, `args`, `env` fields |
| MCP server testing | Manual stdio piping | `npx @modelcontextprotocol/inspector` | Visual UI for testing tools without Claude Desktop |

**Key insight:** The `FastMCP` class eliminates virtually all protocol boilerplate. A tool is just a decorated Python function with type hints. The SDK handles JSON-RPC framing, tool discovery (`tools/list`), schema generation, and content formatting.

## Common Pitfalls

### Pitfall 1: stdout Corruption
**What goes wrong:** Server writes to stdout (via `print()` or misconfigured logging), Claude Desktop receives malformed JSON-RPC and the connection breaks.
**Why it happens:** Python's `print()` defaults to stdout. Some logging configurations also default to stdout.
**How to avoid:** Configure logging explicitly to stderr: `logging.basicConfig(stream=sys.stderr, level=logging.INFO)`. Never use `print()`. Use `logging.getLogger(__name__)` instead.
**Warning signs:** Claude Desktop shows "connection error" or the tool disappears from the tool list.

### Pitfall 2: REST API Not Running
**What goes wrong:** MCP server starts but the Docker Compose stack is not up. Tool invocations fail with connection errors.
**Why it happens:** The MCP server is spawned by Claude Desktop on the host, independently of Docker.
**How to avoid:** The tool should catch `httpx.ConnectError` and return a clear error message: "BBj RAG API is not running. Start it with: cd rag-ingestion && docker compose up -d". Set `isError` appropriately.
**Warning signs:** "Connection refused" errors in Claude Desktop logs.

### Pitfall 3: Absolute Path in Claude Desktop Config
**What goes wrong:** Claude Desktop cannot find `uv` or the project directory because relative paths don't work.
**Why it happens:** Claude Desktop spawns the MCP server process with its own working directory, not your project directory.
**How to avoid:** Always use absolute paths in `claude_desktop_config.json`. Use `which uv` to get the full `uv` path. Use the full path to the project directory with `--directory`.
**Warning signs:** Server doesn't appear in Claude Desktop's tool list after restart.

### Pitfall 4: Generation Parameter Mismatch
**What goes wrong:** The Chapter 2 schema defines `generation` with enum values `["all", "character", "vpro5", "bbj-gui", "dwc"]` but the REST API normalizes `bbj-gui` to `bbj_gui` (hyphen to underscore).
**Why it happens:** The MCP tool schema uses user-friendly names (with hyphens) while the database uses underscores.
**How to avoid:** The REST API already handles normalization (see `routes.py` line 46: `body.generation.replace("-", "_")`). The MCP server passes the generation value as-is to the REST API, which normalizes it. No MCP-side normalization needed.
**Warning signs:** Queries with `generation="bbj-gui"` return no results if normalization is skipped.

### Pitfall 5: Not Pinning mcp SDK Version
**What goes wrong:** `uv add mcp` installs v2.x (pre-alpha) which has breaking changes (different import path: `MCPServer` vs `FastMCP`).
**Why it happens:** The main branch of the SDK repo is v2; PyPI may have v2 pre-releases.
**How to avoid:** Pin explicitly: `mcp>=1.25,<2`. This ensures v1.x stable is used.
**Warning signs:** Import errors: `cannot import name 'FastMCP' from 'mcp.server.fastmcp'`.

## Code Examples

Verified patterns from official sources:

### Complete MCP Server Module
```python
# Source: MCP official docs (build-server tutorial) + project-specific adaptation
"""BBj Knowledge MCP Server.

Thin MCP server that proxies search requests to the BBj RAG REST API
and returns LLM-optimized formatted text responses.

Runs on the host via stdio transport. Claude Desktop spawns this as
a local process.
"""
from __future__ import annotations

import logging
import os
import sys

import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (stdout is the JSON-RPC channel)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
)
logger = logging.getLogger("bbj_mcp")

# REST API base URL (configurable via env var for flexibility)
API_BASE = os.environ.get("BBJ_RAG_API_URL", "http://localhost:10800")

mcp = FastMCP("bbj-knowledge")


def _format_results(data: dict) -> str:
    """Format REST API search results as LLM-friendly text blocks."""
    results = data.get("results", [])
    query = data.get("query", "")

    if not results:
        return f"No results found for query: {query}"

    blocks: list[str] = []
    for i, r in enumerate(results, 1):
        header = f"## Result {i}: {r['title']}"
        if r.get("deprecated"):
            header += " [DEPRECATED]"

        parts = [header]
        if r.get("context_header"):
            parts.append(f"*{r['context_header']}*")
        parts.append("")
        parts.append(r["content"])
        parts.append("")
        parts.append(f"Source: {r['source_url']}")
        if r.get("generations"):
            parts.append(f"Generations: {', '.join(r['generations'])}")

        blocks.append("\n".join(parts))

    header_text = f"Found {len(results)} results for: {query}\n\n"
    return header_text + "\n\n---\n\n".join(blocks)


@mcp.tool()
async def search_bbj_knowledge(
    query: str,
    generation: str | None = None,
    limit: int = 5,
) -> str:
    """Search BBj documentation and code examples with generation-aware filtering.

    Returns ranked results from the RAG pipeline with source citations.
    Use this to find BBj API references, code patterns, tutorials, and
    documentation across all BBj product generations.

    Args:
        query: Natural language search query about BBj programming.
        generation: Filter by BBj product generation. Options: character,
                    vpro5, bbj-gui, dwc. Omit for cross-generation search.
        limit: Maximum number of results (1-50, default 5).
    """
    payload: dict = {"query": query, "limit": limit}
    if generation and generation != "all":
        payload["generation"] = generation

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{API_BASE}/search", json=payload)
            resp.raise_for_status()
    except httpx.ConnectError:
        return (
            "Error: BBj RAG API is not running.\n"
            "Start it with: cd rag-ingestion && docker compose up -d"
        )
    except httpx.HTTPStatusError as exc:
        return f"Error: REST API returned {exc.response.status_code}"

    return _format_results(resp.json())


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Claude Desktop Configuration (macOS)
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "bbj-knowledge": {
      "command": "/Users/beff/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/beff/_workspace/bbj-ai-strategy/rag-ingestion",
        "run",
        "python",
        "-m",
        "bbj_rag.mcp_server"
      ],
      "env": {
        "BBJ_RAG_API_URL": "http://localhost:10800"
      }
    }
  }
}
```

### pyproject.toml Script Entry (Alternative)
```toml
[project.scripts]
bbj-rag = "bbj_rag.cli:cli"
bbj-ingest-all = "bbj_rag.ingest_all:ingest_all"
bbj-mcp = "bbj_rag.mcp_server:main"  # NEW
```

With this entry, the Claude Desktop config simplifies to:
```json
{
  "mcpServers": {
    "bbj-knowledge": {
      "command": "/Users/beff/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/beff/_workspace/bbj-ai-strategy/rag-ingestion",
        "run",
        "bbj-mcp"
      ],
      "env": {
        "BBJ_RAG_API_URL": "http://localhost:10800"
      }
    }
  }
}
```

### Testing with MCP Inspector
```bash
# From the rag-ingestion directory (requires Docker stack running)
npx @modelcontextprotocol/inspector uv run python -m bbj_rag.mcp_server
# Opens visual UI at http://localhost:6274 for testing tool invocations
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `mcp.server.fastmcp.FastMCP` (v1) | `mcp.server.mcpserver.MCPServer` (v2) | v2 pre-alpha, Q1 2026 | v2 not yet stable; use v1 `FastMCP` and pin `<2` |
| SSE transport | Streamable HTTP transport | MCP spec 2025-06-18 | For remote servers; not relevant for stdio/local use |
| Unstructured text-only tool results | Structured content (`structuredContent` field) | MCP spec 2025-06-18 | Optional; text content in `content` field is sufficient for our use case |

**Deprecated/outdated:**
- SSE transport is being superseded by Streamable HTTP for remote deployments, but stdio remains the standard for local Claude Desktop integration.
- The standalone `fastmcp` package (jlowin) diverges from the official SDK's `FastMCP`. Use the official SDK's version (`from mcp.server.fastmcp import FastMCP`).

## Open Questions

1. **Should the MCP server be a separate uv project or stay in the existing `rag-ingestion` package?**
   - What we know: The MCP server runs on the HOST, not in Docker. It needs `mcp` and `httpx` as dependencies. The existing `rag-ingestion` package already has `httpx`.
   - What's unclear: Adding `mcp` to `rag-ingestion/pyproject.toml` means the Docker image will also install it (unnecessary but harmless).
   - Recommendation: Keep it in the existing package for simplicity. The `mcp` dependency is small and the Docker image size increase is negligible. A separate project would require duplicating the `httpx` dependency and maintaining two `pyproject.toml` files.

2. **Should the `generation` parameter use an enum type or free-form string?**
   - What we know: Chapter 2 schema defines `"enum": ["all", "character", "vpro5", "bbj-gui", "dwc"]`. The REST API accepts any string and normalizes it.
   - What's unclear: Whether to validate at the MCP level or let the REST API handle it.
   - Recommendation: Use `Literal["all", "character", "vpro5", "bbj-gui", "dwc"] | None` as the type hint. FastMCP will generate the enum in the JSON schema automatically. This matches Chapter 2's specification exactly.

3. **Environment variable expansion in `claude_desktop_config.json`**
   - What we know: Claude Desktop supports an `env` field for passing environment variables. There have been reported bugs with env variable expansion on some platforms.
   - What's unclear: Whether the `env` field works reliably on the user's macOS setup.
   - Recommendation: Use the `env` field for `BBJ_RAG_API_URL` but also provide a sensible default in the code (`http://localhost:10800`). Document both approaches.

## Sources

### Primary (HIGH confidence)
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk) - v1.x branch, FastMCP API, version status
- [MCP Official Docs: Build a Server](https://modelcontextprotocol.io/docs/develop/build-server) - Complete Python FastMCP tutorial, Claude Desktop config, stdio transport, logging best practices
- [MCP Official Docs: Tools Specification](https://modelcontextprotocol.io/docs/concepts/tools) - Protocol revision 2025-06-18, tool schema, content types, error handling
- [PyPI: mcp 1.26.0](https://pypi.org/project/mcp/1.26.0/) - Current v1.x version, Python >=3.10, optional extras
- Project codebase: `rag-ingestion/src/bbj_rag/api/routes.py`, `schemas.py`, `config.py` - REST API implementation details
- Project codebase: `docs/02-strategic-architecture/index.md` - Chapter 2 JSON schema for `search_bbj_knowledge`

### Secondary (MEDIUM confidence)
- [MCP Inspector GitHub](https://github.com/modelcontextprotocol/inspector) - Testing tool for MCP servers
- [Stainless: From REST API to MCP Server](https://www.stainless.com/mcp/from-rest-api-to-mcp-server) - REST-to-MCP proxy patterns
- [MCP Official Docs: Connect Local Servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers) - Claude Desktop config format, env variables

### Tertiary (LOW confidence)
- Various Medium articles and blog posts about MCP server development patterns (used for cross-verification only, not as primary sources)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official SDK docs, PyPI version verified, official tutorial consulted
- Architecture: HIGH - Pattern directly matches official tutorial + project REST API already built
- Pitfalls: HIGH - stdout corruption and logging documented in official docs; REST API connection is straightforward engineering
- Code examples: HIGH - Based on official MCP build-server tutorial adapted to project specifics

**Research date:** 2026-02-02
**Valid until:** 2026-03-02 (MCP SDK v2 may release in Q1 2026, but v1.x will remain supported; pin ensures stability)
