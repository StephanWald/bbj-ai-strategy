"""BBj Knowledge MCP Server.

Thin proxy over the REST API for Claude Desktop.

Runs on the host via stdio transport. Claude Desktop spawns this as
a local process. All search complexity is handled by the REST API;
this server is a formatting layer that translates between MCP protocol
and the REST API.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Literal

import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr ONLY (stdout is the JSON-RPC channel)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
)
logger = logging.getLogger("bbj_mcp")

# REST API base URL (configurable via env var in claude_desktop_config.json)
API_BASE = os.environ.get("BBJ_RAG_API_URL", "http://localhost:10800")

mcp = FastMCP(
    "bbj-knowledge",
    stateless_http=True,
    streamable_http_path="/",  # Serve at mount point, not /mcp/mcp
)


def _format_results(data: dict[str, object]) -> str:
    """Format REST API search results as LLM-friendly text blocks."""
    results = data.get("results", [])
    query = data.get("query", "")

    if not results:
        return f"No results found for query: {query}"

    assert isinstance(results, list)
    blocks: list[str] = []
    for i, r in enumerate(results, 1):
        assert isinstance(r, dict)
        header = f"## Result {i}: {r['title']}"
        if r.get("deprecated"):
            header += " [DEPRECATED]"

        parts = [header]
        if r.get("context_header"):
            parts.append(f"*{r['context_header']}*")
        parts.append("")
        parts.append(str(r["content"]))
        parts.append("")
        display = r.get("display_url", r["source_url"])
        parts.append(f"Source: {display}")
        if r.get("source_type"):
            parts.append(f"Source Type: {r['source_type']}")
        if r.get("generations"):
            gens = r["generations"]
            assert isinstance(gens, list)
            parts.append(f"Generations: {', '.join(gens)}")

        blocks.append("\n".join(parts))

    # Build header with optional source breakdown
    counts = data.get("source_type_counts", {})
    assert isinstance(counts, dict)
    if counts:
        summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
        header = f"Found {len(results)} results for: {query} ({summary})"
    else:
        header = f"Found {len(results)} results for: {query}"

    return header + "\n\n" + "\n\n---\n\n".join(blocks)


@mcp.tool()
async def search_bbj_knowledge(
    query: str,
    generation: Literal["all", "character", "vpro5", "bbj-gui", "dwc"] | None = None,
    limit: int = 5,
) -> str:
    """Search BBj documentation and code examples with generation-aware filtering.

    Returns ranked results from the RAG pipeline with source citations.
    Use this to find BBj API references, code patterns, tutorials, and
    documentation across all BBj product generations.

    Args:
        query: Natural language search query about BBj programming.
        generation: Filter by BBj product generation. Omit for cross-generation search.
        limit: Maximum number of results (1-50, default 5).
    """
    payload: dict[str, object] = {"query": query, "limit": limit}
    if generation is not None and generation != "all":
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


def main() -> None:
    """Entry point for the bbj-mcp script."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
