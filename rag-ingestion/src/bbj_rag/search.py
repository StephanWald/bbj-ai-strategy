"""Search query functions for the BBj RAG pipeline.

Provides dense vector, BM25 keyword, hybrid RRF, and generation-filtered
retrieval against the pgvector-enabled chunks table.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from typing import Any

import psycopg


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A single search result from the chunks table."""

    id: int
    source_url: str
    title: str
    content: str
    doc_type: str
    generations: list[str]
    context_header: str
    deprecated: bool
    display_url: str
    source_type: str
    score: float


def _rows_to_results(rows: list[Any]) -> list[SearchResult]:
    """Convert raw database rows to SearchResult objects.

    Expected column order:
    id(0), source_url(1), title(2), content(3), doc_type(4), generations(5),
    context_header(6), deprecated(7), display_url(8), source_type(9), score(10)
    """
    return [
        SearchResult(
            id=int(row[0]),
            source_url=str(row[1]),
            title=str(row[2]),
            content=str(row[3]),
            doc_type=str(row[4]),
            generations=list(row[5]),
            context_header=str(row[6]),
            deprecated=bool(row[7]),
            display_url=str(row[8]),
            source_type=str(row[9]),
            score=float(row[10]),
        )
        for row in rows
    ]


def dense_search(
    conn: psycopg.Connection[object],
    query_embedding: list[float],
    limit: int = 5,
    generation_filter: str | None = None,
) -> list[SearchResult]:
    """Search chunks by dense vector cosine similarity.

    Returns the top-N most similar chunks ordered by cosine similarity.
    Optionally filters by generation using the GIN-indexed generations array.
    """
    if generation_filter is not None:
        sql = (
            "SELECT id, source_url, title, content, doc_type, generations, "
            "context_header, deprecated, display_url, source_type, "
            "1 - (embedding <=> %s::vector) AS score "
            "FROM chunks "
            "WHERE generations @> ARRAY[%s::text] "
            "ORDER BY embedding <=> %s::vector "
            "LIMIT %s"
        )
        params: tuple[object, ...] = (
            query_embedding,
            generation_filter,
            query_embedding,
            limit,
        )
    else:
        sql = (
            "SELECT id, source_url, title, content, doc_type, generations, "
            "context_header, deprecated, display_url, source_type, "
            "1 - (embedding <=> %s::vector) AS score "
            "FROM chunks "
            "ORDER BY embedding <=> %s::vector "
            "LIMIT %s"
        )
        params = (query_embedding, query_embedding, limit)

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return _rows_to_results(rows)


def bm25_search(
    conn: psycopg.Connection[object],
    query_text: str,
    limit: int = 5,
    generation_filter: str | None = None,
) -> list[SearchResult]:
    """Search chunks by BM25-style full-text keyword matching.

    Uses PostgreSQL's plainto_tsquery and ts_rank_cd for relevance scoring
    against the GIN-indexed search_vector tsvector column.
    """
    if generation_filter is not None:
        sql = (
            "SELECT id, source_url, title, content, doc_type, generations, "
            "context_header, deprecated, display_url, source_type, "
            "ts_rank_cd(search_vector, query) AS score "
            "FROM chunks, plainto_tsquery('english', %s) query "
            "WHERE search_vector @@ query "
            "AND generations @> ARRAY[%s::text] "
            "ORDER BY score DESC "
            "LIMIT %s"
        )
        params: tuple[object, ...] = (query_text, generation_filter, limit)
    else:
        sql = (
            "SELECT id, source_url, title, content, doc_type, generations, "
            "context_header, deprecated, display_url, source_type, "
            "ts_rank_cd(search_vector, query) AS score "
            "FROM chunks, plainto_tsquery('english', %s) query "
            "WHERE search_vector @@ query "
            "ORDER BY score DESC "
            "LIMIT %s"
        )
        params = (query_text, limit)

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return _rows_to_results(rows)


def hybrid_search(
    conn: psycopg.Connection[object],
    query_embedding: list[float],
    query_text: str,
    limit: int = 5,
    generation_filter: str | None = None,
) -> list[SearchResult]:
    """Search chunks using Reciprocal Rank Fusion of dense + BM25 results.

    Runs dense vector and BM25 keyword sub-queries (each top-20), computes
    RRF scores using the rrf_score() SQL function, then combines via SUM
    for a unified ranking.
    """
    gen_where_dense = (
        "WHERE generations @> ARRAY[%s::text] " if generation_filter else ""
    )
    gen_where_bm25 = "AND generations @> ARRAY[%s::text] " if generation_filter else ""

    sql = (
        "SELECT id, source_url, title, content, doc_type, generations, "
        "context_header, deprecated, display_url, source_type, "
        "sum(rrf_score) AS score "
        "FROM ( "
        # Dense vector sub-query
        "(SELECT id, source_url, title, content, doc_type, generations, "
        "context_header, deprecated, display_url, source_type, "
        "rrf_score(rank() OVER (ORDER BY embedding <=> %s::vector)) AS rrf_score "
        "FROM chunks " + gen_where_dense + "ORDER BY embedding <=> %s::vector "
        "LIMIT 20) "
        "UNION ALL "
        # BM25 keyword sub-query
        "(SELECT id, source_url, title, content, doc_type, generations, "
        "context_header, deprecated, display_url, source_type, "
        "rrf_score(rank() OVER ("
        "ORDER BY ts_rank_cd(search_vector, query) DESC"
        ")) AS rrf_score "
        "FROM chunks, plainto_tsquery('english', %s) query "
        "WHERE search_vector @@ query "
        + gen_where_bm25
        + "ORDER BY ts_rank_cd(search_vector, query) DESC "
        "LIMIT 20) "
        ") searches "
        "GROUP BY id, source_url, title, content, doc_type, generations, "
        "context_header, deprecated, display_url, source_type "
        "ORDER BY score DESC "
        "LIMIT %s"
    )

    # Build params tuple based on whether generation filter is active.
    params: list[object] = []
    # Dense sub-query params
    params.append(query_embedding)  # for <=> comparison in rank()
    if generation_filter:
        params.append(generation_filter)
    params.append(query_embedding)  # for ORDER BY
    # BM25 sub-query params
    params.append(query_text)
    if generation_filter:
        params.append(generation_filter)
    # Outer limit
    params.append(limit)

    with conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()

    return _rows_to_results(rows)


async def async_hybrid_search(
    conn: psycopg.AsyncConnection[object],
    query_embedding: list[float],
    query_text: str,
    limit: int = 5,
    generation_filter: str | None = None,
) -> list[SearchResult]:
    """Async version of hybrid_search for use with AsyncConnectionPool.

    Runs dense vector and BM25 keyword sub-queries (each top-20), computes
    RRF scores using the rrf_score() SQL function, then combines via SUM
    for a unified ranking.
    """
    gen_where_dense = (
        "WHERE generations @> ARRAY[%s::text] " if generation_filter else ""
    )
    gen_where_bm25 = "AND generations @> ARRAY[%s::text] " if generation_filter else ""

    sql = (
        "SELECT id, source_url, title, content, doc_type, generations, "
        "context_header, deprecated, display_url, source_type, "
        "sum(rrf_score) AS score "
        "FROM ( "
        # Dense vector sub-query
        "(SELECT id, source_url, title, content, doc_type, generations, "
        "context_header, deprecated, display_url, source_type, "
        "rrf_score(rank() OVER (ORDER BY embedding <=> %s::vector)) AS rrf_score "
        "FROM chunks " + gen_where_dense + "ORDER BY embedding <=> %s::vector "
        "LIMIT 20) "
        "UNION ALL "
        # BM25 keyword sub-query
        "(SELECT id, source_url, title, content, doc_type, generations, "
        "context_header, deprecated, display_url, source_type, "
        "rrf_score(rank() OVER ("
        "ORDER BY ts_rank_cd(search_vector, query) DESC"
        ")) AS rrf_score "
        "FROM chunks, plainto_tsquery('english', %s) query "
        "WHERE search_vector @@ query "
        + gen_where_bm25
        + "ORDER BY ts_rank_cd(search_vector, query) DESC "
        "LIMIT 20) "
        ") searches "
        "GROUP BY id, source_url, title, content, doc_type, generations, "
        "context_header, deprecated, display_url, source_type "
        "ORDER BY score DESC "
        "LIMIT %s"
    )

    # Build params tuple based on whether generation filter is active.
    params: list[object] = []
    # Dense sub-query params
    params.append(query_embedding)  # for <=> comparison in rank()
    if generation_filter:
        params.append(generation_filter)
    params.append(query_embedding)  # for ORDER BY
    # BM25 sub-query params
    params.append(query_text)
    if generation_filter:
        params.append(generation_filter)
    # Outer limit
    params.append(limit)

    async with conn.cursor() as cur:
        await cur.execute(sql, tuple(params))
        rows = await cur.fetchall()

    return _rows_to_results(rows)


# Diversity boost factors for underrepresented source types.
SOURCE_BOOST: dict[str, float] = {
    "pdf": 1.3,
    "bbj_source": 1.3,
    "mdx": 1.2,
    "wordpress": 1.0,
    "web_crawl": 1.0,
    "flare": 1.0,
    "unknown": 1.0,
}
DOMINATION_THRESHOLD = 0.8


def rerank_for_diversity(
    results: list[SearchResult],
    limit: int,
    domination_threshold: float = DOMINATION_THRESHOLD,
) -> list[SearchResult]:
    """Rerank search results to promote minority source types.

    When a single source type dominates the result set (>= domination_threshold
    fraction), apply multiplicative score boosts to underrepresented types so
    they can surface in the final ranking.

    If the result set is naturally diverse, return as-is (no reranking).
    """
    if len(results) == 0:
        return []

    # Count occurrences of each source_type
    type_counts = Counter(r.source_type for r in results)
    total = len(results)

    # Check if any single source_type dominates
    dominated = any(
        count / total >= domination_threshold for count in type_counts.values()
    )

    if not dominated:
        return results[:limit]

    # Apply multiplicative boost and re-sort
    boosted = sorted(
        (
            replace(r, score=r.score * SOURCE_BOOST.get(r.source_type, 1.0))
            for r in results
        ),
        key=lambda r: r.score,
        reverse=True,
    )

    return boosted[:limit]


__all__ = [
    "SOURCE_BOOST",
    "SearchResult",
    "async_hybrid_search",
    "bm25_search",
    "dense_search",
    "hybrid_search",
    "rerank_for_diversity",
]
