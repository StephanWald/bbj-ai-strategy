"""API route definitions for the BBJ RAG REST API.

The /search endpoint accepts a query, embeds it via Ollama, runs hybrid
RRF search against pgvector, and returns ranked documentation chunks.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from ollama import AsyncClient as OllamaAsyncClient
from psycopg import AsyncConnection

from bbj_rag.api.deps import get_conn, get_ollama_client, get_settings
from bbj_rag.api.schemas import SearchRequest, SearchResponse, SearchResultItem
from bbj_rag.config import Settings
from bbj_rag.search import async_hybrid_search

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

    # Run hybrid RRF search
    results = await async_hybrid_search(
        conn=conn,
        query_embedding=embedding,
        query_text=body.query,
        limit=body.limit,
        generation_filter=gen_filter,
    )

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
            score=r.score,
        )
        for r in results
    ]

    return SearchResponse(
        query=body.query,
        results=items,
        count=len(items),
    )
