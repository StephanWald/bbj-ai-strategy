#!/usr/bin/env python3
"""End-to-end validation of the BBj RAG pipeline.

Exercises both the REST API and MCP server against the real ingested corpus,
evaluates result relevance with lightweight heuristics, and generates a
human-readable VALIDATION.md report.

Usage:
    uv run python scripts/validate_e2e.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_BASE = "http://localhost:10800"
RAG_DIR = Path(__file__).resolve().parent.parent  # rag-ingestion/

# Logical source groups with expected source_url prefixes.
SOURCE_GROUPS: dict[str, str] = {
    "Flare": "flare://",
    "PDF": "pdf://",
    "MDX": "mdx-",
    "BBj Source": "file://",
    "WordPress": "https://basis.cloud/",
    "Web Crawl": "https://documentation.basis.cloud/",
}

# ---------------------------------------------------------------------------
# Query definitions
# ---------------------------------------------------------------------------


@dataclass
class SourceQuery:
    """A query targeting a specific logical source."""

    query: str
    target_source: str
    expected_prefix: str


@dataclass
class TopicQuery:
    """A topic-based query with keyword heuristics."""

    query: str
    keywords: list[str]


SOURCE_QUERIES: list[SourceQuery] = [
    SourceQuery("BBjWindow addButton method", "Flare", "flare://"),
    SourceQuery("customer information program BBj GUI example", "PDF", "pdf://"),
    SourceQuery("DWC web component tutorial getting started", "MDX", "mdx-"),
    SourceQuery("BBj sample source code PROCESS_EVENTS", "BBj Source", "file://"),
    SourceQuery(
        "Advantage magazine BBj article",
        "WordPress",
        "https://basis.cloud/",
    ),
    SourceQuery(
        "documentation.basis.cloud BBj reference",
        "Web Crawl",
        "https://documentation.basis.cloud/",
    ),
]

TOPIC_QUERIES: list[TopicQuery] = [
    TopicQuery("How do I create a BBjGrid?", ["grid", "BBjGrid"]),
    TopicQuery("BBj string manipulation functions", ["string", "str"]),
    TopicQuery("DWC web component styling CSS", ["css", "style", "dwc"]),
    TopicQuery("BBj database connection SQL", ["sql", "database", "connection"]),
    TopicQuery(
        "Event handling callbacks in BBj",
        ["event", "callback", "notify"],
    ),
    TopicQuery("BBj file I/O operations", ["file", "open", "read", "write"]),
    TopicQuery(
        "Migration from Visual PRO/5 to BBj",
        ["migration", "pro/5", "vpro5", "visual pro"],
    ),
]

# Subset for MCP validation.
MCP_QUERIES: list[str] = [
    "BBjWindow addButton method",
    "How do I create a BBjGrid?",
    "Event handling callbacks in BBj",
]

# Generation-filtered query (extra).
GENERATION_QUERY = TopicQuery("DWC web component styling CSS", ["css", "style", "dwc"])
GENERATION_FILTER = "dwc"


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------


@dataclass
class RestResult:
    """Result from a REST API query evaluation."""

    query: str
    category: str  # "source-targeted", "topic-based", "generation-filtered"
    passed: bool
    reason: str
    result_count: int
    top_source_url: str = ""
    top_title: str = ""
    top_score: float = 0.0
    snippet: str = ""
    all_source_urls: list[str] = field(default_factory=list)


@dataclass
class McpResult:
    """Result from an MCP tool invocation."""

    query: str
    passed: bool
    response_preview: str
    is_error: bool


# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------


async def check_prerequisites(client: httpx.AsyncClient) -> dict:
    """Verify the API is healthy and the corpus is populated."""
    # Health check
    try:
        resp = await client.get(f"{API_BASE}/health", timeout=10.0)
    except httpx.ConnectError:
        print("FATAL: Cannot connect to REST API at", API_BASE)
        print("Start the system with: cd rag-ingestion && docker compose up -d")
        sys.exit(1)

    health = resp.json()
    if health.get("status") != "healthy":
        print("FATAL: API is not healthy:", health)
        sys.exit(1)
    print("  Health check: OK")

    # Stats
    resp = await client.get(f"{API_BASE}/stats", timeout=10.0)
    stats: dict = resp.json()
    total = stats.get("total_chunks", 0)
    if total == 0:
        print("FATAL: No chunks in database -- run ingestion first")
        sys.exit(1)
    print(f"  Corpus: {total:,} chunks")
    return stats


# ---------------------------------------------------------------------------
# REST API query runner
# ---------------------------------------------------------------------------


async def run_rest_query(
    client: httpx.AsyncClient,
    query: str,
    *,
    limit: int = 5,
    generation: str | None = None,
) -> dict:
    """POST to /search and return parsed JSON response."""
    payload: dict[str, object] = {"query": query, "limit": limit}
    if generation:
        payload["generation"] = generation
    try:
        resp = await client.post(f"{API_BASE}/search", json=payload, timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        return {"error": str(exc), "results": [], "count": 0, "query": query}


# ---------------------------------------------------------------------------
# Result evaluators
# ---------------------------------------------------------------------------


def evaluate_source_query(data: dict, sq: SourceQuery) -> RestResult:
    """Evaluate a source-targeted query result."""
    results = data.get("results", [])
    count = len(results)
    all_urls = [r["source_url"] for r in results]

    if count == 0:
        return RestResult(
            query=sq.query,
            category="source-targeted",
            passed=False,
            reason="no results returned",
            result_count=0,
            all_source_urls=all_urls,
        )

    top = results[0]
    source_url = top.get("source_url", "")
    title = top.get("title", "")
    score = top.get("score", 0.0)
    content = top.get("content", "")
    snippet = textwrap.shorten(content, 150, placeholder="...")

    passed = source_url.startswith(sq.expected_prefix)
    if passed:
        reason = f"top result from {sq.target_source}"
    else:
        reason = (
            f"top result source_url '{source_url}' "
            f"does not start with '{sq.expected_prefix}'"
        )

    return RestResult(
        query=sq.query,
        category="source-targeted",
        passed=passed,
        reason=reason,
        result_count=count,
        top_source_url=source_url,
        top_title=title,
        top_score=score,
        snippet=snippet,
        all_source_urls=all_urls,
    )


def evaluate_topic_query(
    data: dict,
    tq: TopicQuery,
    *,
    category: str = "topic-based",
) -> RestResult:
    """Evaluate a topic-based query result."""
    results = data.get("results", [])
    count = len(results)
    all_urls = [r["source_url"] for r in results]

    if count == 0:
        return RestResult(
            query=tq.query,
            category=category,
            passed=False,
            reason="no results returned",
            result_count=0,
            all_source_urls=all_urls,
        )

    top = results[0]
    source_url = top.get("source_url", "")
    title = top.get("title", "")
    score = top.get("score", 0.0)
    content = top.get("content", "")
    snippet = textwrap.shorten(content, 150, placeholder="...")

    combined = (title + " " + content).lower()
    matched = any(kw.lower() in combined for kw in tq.keywords)
    reason = (
        "keyword match in top result"
        if matched
        else f"no keyword match ({tq.keywords}) in top result"
    )

    return RestResult(
        query=tq.query,
        category=category,
        passed=matched,
        reason=reason,
        result_count=count,
        top_source_url=source_url,
        top_title=title,
        top_score=score,
        snippet=snippet,
        all_source_urls=all_urls,
    )


# ---------------------------------------------------------------------------
# MCP query runner
# ---------------------------------------------------------------------------


async def run_mcp_queries(queries: list[str]) -> list[McpResult]:
    """Invoke search_bbj_knowledge via MCP stdio transport."""
    # Lazy imports -- only needed if MCP section runs.
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    server_params = StdioServerParameters(
        command="uv",
        args=["--directory", str(RAG_DIR), "run", "bbj-mcp"],
        env={
            **os.environ,
            "BBJ_RAG_API_URL": API_BASE,
        },
    )

    results: list[McpResult] = []
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Verify tool is listed.
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            if "search_bbj_knowledge" not in tool_names:
                print(
                    "WARNING: search_bbj_knowledge not in tool list:",
                    tool_names,
                )
                return [
                    McpResult(
                        query=q,
                        passed=False,
                        response_preview="Tool not found",
                        is_error=True,
                    )
                    for q in queries
                ]

            for query in queries:
                try:
                    result = await session.call_tool(
                        "search_bbj_knowledge",
                        arguments={"query": query, "limit": 5},
                    )
                    text = result.content[0].text if result.content else ""
                    passed = not result.isError and "No results found" not in text
                    results.append(
                        McpResult(
                            query=query,
                            passed=passed,
                            response_preview=text[:200],
                            is_error=result.isError,
                        )
                    )
                except Exception as exc:
                    results.append(
                        McpResult(
                            query=query,
                            passed=False,
                            response_preview=f"Error: {exc}",
                            is_error=True,
                        )
                    )

    return results


# ---------------------------------------------------------------------------
# Cross-source collector
# ---------------------------------------------------------------------------


def collect_cross_source(rest_results: list[RestResult]) -> dict[str, bool]:
    """Map results to logical source groups and return found/not-found."""
    all_urls: list[str] = []
    for r in rest_results:
        all_urls.extend(r.all_source_urls)

    found: dict[str, bool] = {}
    for group, prefix in SOURCE_GROUPS.items():
        found[group] = any(url.startswith(prefix) for url in all_urls)
    return found


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------


def generate_report(
    stats: dict,
    rest_results: list[RestResult],
    mcp_results: list[McpResult],
    cross_source: dict[str, bool],
) -> str:
    """Generate the VALIDATION.md content string."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    total_queries = len(rest_results) + len(mcp_results)
    passed = sum(1 for r in rest_results if r.passed) + sum(
        1 for r in mcp_results if r.passed
    )
    status = "PASS" if passed == total_queries else "FAIL"

    lines: list[str] = []

    # -- Header --
    lines.append("# End-to-End Validation Report")
    lines.append("")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Status:** {status} ({passed}/{total_queries} queries passed)")
    lines.append("")

    # -- Corpus Stats --
    lines.append("## Corpus Stats")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    total_chunks = stats.get("total_chunks", 0)
    lines.append(f"| Total chunks | {total_chunks:,} |")

    by_source = stats.get("by_source", {})
    for src, count in sorted(by_source.items(), key=lambda x: -x[1]):
        lines.append(f"| doc_type: {src} | {count:,} |")

    by_gen = stats.get("by_generation", {})
    if by_gen:
        for gen, count in sorted(by_gen.items(), key=lambda x: -x[1]):
            lines.append(f"| generation: {gen} | {count:,} |")

    lines.append("")

    # -- Source-Targeted Queries --
    source_results = [r for r in rest_results if r.category == "source-targeted"]
    lines.append("## Source-Targeted Queries")
    lines.append("")
    for i, r in enumerate(source_results, 1):
        lines.append(f"### Query {i}: {r.query}")
        lines.append("")
        lines.append(f"- **Result:** {'PASS' if r.passed else 'FAIL'}")
        lines.append(f"- **Reason:** {r.reason}")
        lines.append(f"- **Source:** `{r.top_source_url}`")
        lines.append(f"- **Title:** {r.top_title}")
        lines.append(f"- **Score:** {r.top_score:.4f}")
        lines.append(f"- **Snippet:** {r.snippet}")
        lines.append("")

    # -- Topic-Based Queries --
    topic_results = [r for r in rest_results if r.category == "topic-based"]
    lines.append("## Topic-Based Queries")
    lines.append("")
    for i, r in enumerate(topic_results, 1):
        lines.append(f"### Query {i}: {r.query}")
        lines.append("")
        lines.append(f"- **Result:** {'PASS' if r.passed else 'FAIL'}")
        lines.append(f"- **Reason:** {r.reason}")
        lines.append(f"- **Source:** `{r.top_source_url}`")
        lines.append(f"- **Title:** {r.top_title}")
        lines.append(f"- **Score:** {r.top_score:.4f}")
        lines.append(f"- **Snippet:** {r.snippet}")
        lines.append("")

    # -- Generation-Filtered Query --
    gen_results = [r for r in rest_results if r.category == "generation-filtered"]
    if gen_results:
        lines.append("## Generation-Filtered Query")
        lines.append("")
        for r in gen_results:
            lines.append(f"### Query: {r.query} (generation={GENERATION_FILTER})")
            lines.append("")
            lines.append(f"- **Result:** {'PASS' if r.passed else 'FAIL'}")
            lines.append(f"- **Reason:** {r.reason}")
            lines.append(f"- **Source:** `{r.top_source_url}`")
            lines.append(f"- **Title:** {r.top_title}")
            lines.append(f"- **Score:** {r.top_score:.4f}")
            lines.append(f"- **Snippet:** {r.snippet}")
            lines.append("")

    # -- MCP Validation --
    lines.append("## MCP Validation")
    lines.append("")
    for i, r in enumerate(mcp_results, 1):
        lines.append(f"### Query M{i}: {r.query}")
        lines.append("")
        lines.append(f"- **Result:** {'PASS' if r.passed else 'FAIL'}")
        preview = r.response_preview.replace("\n", " ")
        lines.append(f"- **Response preview:** {preview}")
        if r.is_error:
            lines.append("- **Error:** yes")
        lines.append("")

    # -- Cross-Source Summary --
    lines.append("## Cross-Source Summary")
    lines.append("")
    lines.append("| Source Group | Expected Prefix | Found in Results |")
    lines.append("|-------------|-----------------|-----------------|")
    for group, prefix in SOURCE_GROUPS.items():
        found = "Yes" if cross_source.get(group, False) else "No"
        lines.append(f"| {group} | `{prefix}` | {found} |")
    lines.append("")

    # -- Known Issues --
    failed_rest = [r for r in rest_results if not r.passed]
    failed_mcp = [r for r in mcp_results if not r.passed]
    missing_sources = [g for g, found in cross_source.items() if not found]

    lines.append("## Known Issues")
    lines.append("")
    if not failed_rest and not failed_mcp and not missing_sources:
        lines.append("None -- all queries passed and all sources represented.")
    else:
        if failed_rest:
            lines.append("### REST API Failures")
            lines.append("")
            for r in failed_rest:
                lines.append(f"- **{r.query}** ({r.category}): {r.reason}")
            lines.append("")
        if failed_mcp:
            lines.append("### MCP Failures")
            lines.append("")
            for r in failed_mcp:
                lines.append(f"- **{r.query}**: {r.response_preview[:100]}")
            lines.append("")
        if missing_sources:
            lines.append("### Missing Source Groups")
            lines.append("")
            for g in missing_sources:
                pfx = SOURCE_GROUPS[g]
                lines.append(f"- **{g}** (`{pfx}`): no results found across any query")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the full end-to-end validation suite."""
    print("=" * 60)
    print("  BBj RAG End-to-End Validation")
    print("=" * 60)
    print()

    # -- Prerequisites --
    print("[1/5] Checking prerequisites...")
    async with httpx.AsyncClient() as client:
        stats = await check_prerequisites(client)

        # -- Source-targeted REST queries --
        print("[2/5] Running source-targeted queries (6)...")
        rest_results: list[RestResult] = []
        for sq in SOURCE_QUERIES:
            data = await run_rest_query(client, sq.query)
            result = evaluate_source_query(data, sq)
            status_char = "+" if result.passed else "-"
            print(f"  [{status_char}] {sq.target_source}: {sq.query}")
            rest_results.append(result)

        # -- Topic-based REST queries --
        print("[3/5] Running topic-based queries (7 + 1 generation-filtered)...")
        for tq in TOPIC_QUERIES:
            data = await run_rest_query(client, tq.query)
            result = evaluate_topic_query(data, tq, category="topic-based")
            status_char = "+" if result.passed else "-"
            print(f"  [{status_char}] {tq.query}")
            rest_results.append(result)

        # Generation-filtered query
        data = await run_rest_query(
            client, GENERATION_QUERY.query, generation=GENERATION_FILTER
        )
        gen_result = evaluate_topic_query(
            data, GENERATION_QUERY, category="generation-filtered"
        )
        status_char = "+" if gen_result.passed else "-"
        gq = GENERATION_QUERY.query
        print(f"  [{status_char}] {gq} (generation={GENERATION_FILTER})")
        rest_results.append(gen_result)

    # -- MCP queries --
    print("[4/5] Running MCP queries (3)...")
    try:
        mcp_results = await run_mcp_queries(MCP_QUERIES)
        for r in mcp_results:
            status_char = "+" if r.passed else "-"
            print(f"  [{status_char}] {r.query}")
    except Exception as exc:
        print(f"  MCP validation failed: {exc}")
        mcp_results = [
            McpResult(
                query=q,
                passed=False,
                response_preview=f"Session error: {exc}",
                is_error=True,
            )
            for q in MCP_QUERIES
        ]

    # -- Cross-source collection --
    cross_source = collect_cross_source(rest_results)

    # -- Report generation --
    print("[5/5] Generating report...")
    report = generate_report(stats, rest_results, mcp_results, cross_source)
    output_path = RAG_DIR / "VALIDATION.md"
    output_path.write_text(report, encoding="utf-8")
    print(f"  Report written to: {output_path}")

    # -- Summary --
    total = len(rest_results) + len(mcp_results)
    passed_count = sum(1 for r in rest_results if r.passed) + sum(
        1 for r in mcp_results if r.passed
    )
    source_count = sum(1 for v in cross_source.values() if v)
    print()
    rest_passed = sum(1 for r in rest_results if r.passed)
    mcp_passed = sum(1 for r in mcp_results if r.passed)
    print("-" * 60)
    print(f"  REST queries: {rest_passed}/{len(rest_results)} passed")
    print(f"  MCP queries:  {mcp_passed}/{len(mcp_results)} passed")
    print(f"  Total:        {passed_count}/{total} passed")
    print(f"  Sources:      {source_count}/6 represented")
    print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())
