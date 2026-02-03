"""Chat API routes: GET /chat (page), POST /chat/stream (SSE).

The /chat/stream endpoint accepts a messages array, runs RAG search
for the latest user query, builds a grounded system prompt, and
streams Claude's response as JSON-encoded SSE events.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from ollama import AsyncClient as OllamaAsyncClient
from psycopg import AsyncConnection
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from bbj_rag.api.deps import get_conn, get_ollama_client, get_settings
from bbj_rag.chat.stream import stream_chat_response
from bbj_rag.config import Settings
from bbj_rag.search import async_hybrid_search, rerank_for_diversity

router = APIRouter(prefix="/chat", tags=["chat"])

# Annotated dependency types for FastAPI injection
ConnDep = Annotated[AsyncConnection[object], Depends(get_conn)]
OllamaDep = Annotated[OllamaAsyncClient, Depends(get_ollama_client)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


class ChatMessage(BaseModel):
    """A single message in the conversation."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Inbound chat request with conversation history."""

    messages: list[ChatMessage]


@router.get("", response_class=HTMLResponse)
async def chat_page() -> HTMLResponse:
    """Serve the chat HTML page (placeholder until Plan 02)."""
    return HTMLResponse(
        content="<html><body><p>Chat page coming in Plan 02</p></body></html>"
    )


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    conn: ConnDep,
    ollama_client: OllamaDep,
    settings: SettingsDep,
) -> EventSourceResponse:
    """Stream Claude's RAG-grounded response as SSE events.

    Event types:
    - ``sources``: metadata about RAG results used for context
    - ``delta``: incremental text chunks (JSON-encoded)
    - ``done``: token usage summary
    - ``error``: error message on failure
    """
    if not body.messages:
        raise HTTPException(status_code=422, detail="messages array must not be empty")

    # Extract latest user message for RAG search
    user_query = body.messages[-1].content

    # Embed the query using Ollama
    try:
        response = await ollama_client.embed(
            model=settings.embedding_model, input=user_query
        )
        embedding: list[float] = response["embeddings"][0]
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Ollama embedding failed: {exc}"
        ) from exc

    # Run hybrid search with diversity reranking
    raw_results = await async_hybrid_search(
        conn=conn,
        query_embedding=embedding,
        query_text=user_query,
        limit=10,
    )
    results = rerank_for_diversity(raw_results, limit=5)

    # Determine confidence level
    low_confidence = len(results) < settings.chat_confidence_min_results or (
        len(results) > 0 and results[0].score < settings.chat_confidence_min_score
    )

    # Convert messages to dicts for the streaming function
    messages_dicts = [{"role": m.role, "content": m.content} for m in body.messages]

    return EventSourceResponse(
        stream_chat_response(messages_dicts, results, settings, low_confidence)
    )
