"""Anthropic SDK streaming generator yielding SSE event dicts.

Provides an async generator that streams Claude API responses as
dict events compatible with sse-starlette's EventSourceResponse.
Events: sources, delta, done, error.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any, cast

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from bbj_rag.chat.prompt import build_rag_system_prompt
from bbj_rag.config import Settings
from bbj_rag.search import SearchResult

logger = logging.getLogger(__name__)


async def stream_chat_response(
    messages: list[dict[str, str]],
    search_results: list[SearchResult],
    settings: Settings,
    low_confidence: bool,
) -> AsyncIterator[dict[str, Any]]:
    """Stream a Claude chat response as SSE event dicts.

    Yields dicts with ``event`` and ``data`` keys suitable for
    sse-starlette's ``EventSourceResponse``.

    Event sequence:
    1. ``sources`` -- metadata about RAG results used for context
    2. ``delta`` (repeated) -- incremental text chunks from Claude
    3. ``done`` -- token usage summary
    4. ``error`` (on failure) -- error message

    Parameters
    ----------
    messages:
        Conversation history as role/content dicts.
    search_results:
        RAG search results to ground the response.
    settings:
        Application settings (model name, max tokens, etc.).
    low_confidence:
        Whether RAG results indicate low confidence.
    """
    client = AsyncAnthropic()

    # Build system prompt from RAG results
    system_prompt = build_rag_system_prompt(search_results, low_confidence)

    # Truncate messages to sliding window and cast to SDK type
    truncated = cast(list[MessageParam], messages[-settings.chat_max_history :])

    # Emit sources metadata before streaming begins
    sources_list = [
        {
            "index": i,
            "title": r.title,
            "url": r.display_url,
            "source_type": r.source_type,
            "low_confidence": low_confidence,
        }
        for i, r in enumerate(search_results, 1)
    ]
    yield {"event": "sources", "data": json.dumps(sources_list)}

    # Stream Claude response
    try:
        async with client.messages.stream(
            model=settings.chat_model,
            max_tokens=settings.chat_max_tokens,
            system=system_prompt,
            messages=truncated,
        ) as stream:
            async for text in stream.text_stream:
                yield {
                    "event": "delta",
                    "data": json.dumps({"text": text}),
                }

            final = await stream.get_final_message()
            yield {
                "event": "done",
                "data": json.dumps(
                    {
                        "input_tokens": final.usage.input_tokens,
                        "output_tokens": final.usage.output_tokens,
                    }
                ),
            }
    except Exception as exc:
        logger.exception("Chat stream error")
        yield {
            "event": "error",
            "data": json.dumps({"message": str(exc)}),
        }
