"""API route definitions for the BBJ RAG REST API.

The /search endpoint accepts a query, embeds it via Ollama, runs hybrid
RRF search against pgvector, and returns ranked documentation chunks.
The /stats endpoint returns corpus statistics (total chunks, breakdowns
by doc_type and by generation tag).
"""

from __future__ import annotations

from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from ollama import AsyncClient as OllamaAsyncClient
from psycopg import AsyncConnection
from psycopg.rows import tuple_row

from bbj_rag.api.deps import get_conn, get_ollama_client, get_settings
from bbj_rag.api.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    StatsResponse,
)
from bbj_rag.config import Settings
from bbj_rag.search import async_hybrid_search, rerank_for_diversity

router = APIRouter()

# Annotated dependency types for FastAPI injection
ConnDep = Annotated[AsyncConnection[object], Depends(get_conn)]
OllamaDep = Annotated[OllamaAsyncClient, Depends(get_ollama_client)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.post("/search", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    conn: ConnDep,
    ollama_client: OllamaDep,
    settings: SettingsDep,
) -> SearchResponse:
    """Execute a hybrid search over the BBj documentation corpus."""
    # Normalize generation filter: bbj-gui -> bbj_gui
    gen_filter: str | None = None
    if body.generation is not None:
        gen_filter = body.generation.replace("-", "_")

    # Embed the query
    try:
        response = await ollama_client.embed(
            model=settings.embedding_model, input=body.query
        )
        embedding: list[float] = response["embeddings"][0]
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Ollama embedding failed: {exc}"
        ) from exc

    # Over-fetch for diversity reranking pool
    raw_results = await async_hybrid_search(
        conn=conn,
        query_embedding=embedding,
        query_text=body.query,
        limit=body.limit * 2,
        generation_filter=gen_filter,
    )

    # Apply diversity reranking
    results = rerank_for_diversity(raw_results, limit=body.limit)

    # Compute source type breakdown
    source_type_counts = dict(Counter(r.source_type for r in results))

    # Build response
    items = [
        SearchResultItem(
            content=r.content,
            title=r.title,
            source_url=r.source_url,
            doc_type=r.doc_type,
            generations=r.generations,
            context_header=r.context_header,
            deprecated=r.deprecated,
            display_url=r.display_url,
            source_type=r.source_type,
            score=r.score,
        )
        for r in results
    ]

    return SearchResponse(
        query=body.query,
        results=items,
        count=len(items),
        source_type_counts=source_type_counts,
    )


@router.get("/stats", response_model=StatsResponse)
async def stats(conn: ConnDep) -> StatsResponse:
    """Return corpus statistics: total chunks, by source, by generation."""
    try:
        async with conn.cursor(row_factory=tuple_row) as cur:
            # Total chunk count
            await cur.execute("SELECT count(*) FROM chunks")
            row = await cur.fetchone()
            total = row[0] if row else 0

            # Chunks grouped by doc_type
            await cur.execute(
                "SELECT doc_type, count(*) FROM chunks "
                "GROUP BY doc_type ORDER BY count(*) DESC"
            )
            by_source: dict[str, int] = {r[0]: r[1] for r in await cur.fetchall()}

            # Chunks grouped by unnested generation tag
            await cur.execute(
                "SELECT g, count(*) FROM chunks, unnest(generations) AS g "
                "GROUP BY g ORDER BY count(*) DESC"
            )
            by_generation: dict[str, int] = {r[0]: r[1] for r in await cur.fetchall()}
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Database query failed: {exc}"
        ) from exc

    return StatsResponse(
        total_chunks=total,
        by_source=by_source,
        by_generation=by_generation,
    )
