"""Anthropic SDK streaming generator yielding SSE event dicts.

Provides an async generator that streams Claude API responses as
dict events compatible with sse-starlette's EventSourceResponse.
Events: sources, validation_warning, delta, done, error.

BBj code blocks are validated via bbjcpl before streaming. Invalid
code triggers automatic fix attempts (up to 3 total). Persistently
invalid code is shown with a validation_warning event.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from bbj_rag.chat.prompt import build_rag_system_prompt
from bbj_rag.chat.validation import (
    build_fix_prompt,
    extract_code_blocks,
    replace_code_block,
    validate_code_blocks,
)
from bbj_rag.config import Settings
from bbj_rag.search import SearchResult

logger = logging.getLogger(__name__)


async def _get_claude_response(
    client: AsyncAnthropic,
    settings: Settings,
    system_prompt: str,
    messages: list[MessageParam],
) -> tuple[str, int, int]:
    """Get a complete Claude response (non-streaming).

    Args:
        client: Anthropic API client
        settings: Application settings
        system_prompt: System prompt for the request
        messages: Conversation messages

    Returns:
        Tuple of (response_text, input_tokens, output_tokens)
    """
    response = await client.messages.create(
        model=settings.chat_model,
        max_tokens=settings.chat_max_tokens,
        system=system_prompt,
        messages=messages,
    )

    # Extract text content
    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text

    return text, response.usage.input_tokens, response.usage.output_tokens


async def _get_fix_from_claude(
    client: AsyncAnthropic,
    settings: Settings,
    code: str,
    errors: str,
) -> str:
    """Ask Claude to fix BBj code with syntax errors.

    Args:
        client: Anthropic API client
        settings: Application settings
        code: The BBj code with errors
        errors: The compiler error output

    Returns:
        Fixed code (just the code, no markdown)
    """
    fix_prompt = build_fix_prompt(code, errors)

    response = await client.messages.create(
        model=settings.chat_model,
        max_tokens=2048,  # Shorter limit for fix responses
        messages=[{"role": "user", "content": fix_prompt}],
    )

    # Extract text content
    fixed = ""
    for block in response.content:
        if hasattr(block, "text"):
            fixed += block.text

    # Strip any markdown fences Claude might add despite instructions
    fixed = fixed.strip()
    if fixed.startswith("```"):
        # Remove opening fence with optional language tag
        fixed = re.sub(r"^```\w*\n?", "", fixed)
    if fixed.endswith("```"):
        fixed = fixed[:-3]

    return fixed.strip()


async def _validate_response_code(
    client: AsyncAnthropic,
    settings: Settings,
    response: str,
    max_attempts: int = 3,
) -> tuple[str, list[dict[str, Any]]]:
    """Validate BBj code blocks and attempt fixes.

    Extracts BBj code blocks, validates each via bbjcpl, and asks
    Claude to fix any with errors. Continues until valid or max
    attempts reached.

    Args:
        client: Anthropic API client
        settings: Application settings
        response: The full response text containing code blocks
        max_attempts: Maximum validation+fix attempts per block

    Returns:
        Tuple of (final_response, warnings_list)
        warnings_list contains dicts for blocks that couldn't be fixed
    """
    warnings: list[dict[str, Any]] = []
    current_response = response

    # Track offset adjustments when blocks are replaced
    # (replacement may change block length)
    blocks = extract_code_blocks(current_response)
    bbj_blocks = [b for b in blocks if b.is_bbj]

    if not bbj_blocks:
        # No BBj code to validate
        return current_response, warnings

    # Validate all BBj blocks
    await validate_code_blocks(bbj_blocks)

    # Process each block, attempting fixes for invalid ones
    for block_index, block in enumerate(bbj_blocks):
        result = block.validation_result

        # Skip if validation was unavailable or timed out (add warning but continue)
        if result is None:
            continue

        if result.unavailable:
            logger.debug("bbjcpl unavailable, skipping validation")
            continue

        if result.timed_out:
            warnings.append(
                {
                    "code_index": block_index + 1,
                    "errors": "Validation timed out",
                    "code_preview": block.code[:50],
                }
            )
            continue

        # If valid, nothing to do
        if result.valid:
            continue

        # Invalid code - attempt fixes
        current_code = block.code
        current_errors = result.errors

        while block.attempts < max_attempts and not result.valid:
            logger.info(
                f"BBj validation failed (attempt {block.attempts}/{max_attempts}), "
                f"requesting fix"
            )

            # Ask Claude to fix the code
            try:
                fixed_code = await _get_fix_from_claude(
                    client, settings, current_code, current_errors
                )
            except Exception as exc:
                logger.warning(f"Fix request failed: {exc}")
                break

            # Re-validate the fixed code
            from bbj_rag.compiler import validate_bbj_syntax

            result = await validate_bbj_syntax(fixed_code)
            block.attempts += 1
            block.validation_result = result

            if result.valid:
                # Fix worked - replace in response
                current_response = replace_code_block(
                    current_response, block, fixed_code
                )
                # Re-extract blocks to update positions after replacement
                blocks = extract_code_blocks(current_response)
                bbj_blocks = [b for b in blocks if b.is_bbj]
                # Update the block reference for subsequent iterations
                if block_index < len(bbj_blocks):
                    block = bbj_blocks[block_index]
                break
            else:
                current_code = fixed_code
                current_errors = result.errors

        # If still invalid after max attempts, add warning
        if not result.valid and not result.unavailable and not result.timed_out:
            warnings.append(
                {
                    "code_index": block_index + 1,
                    "errors": result.errors,
                    "code_preview": current_code[:50],
                }
            )

    return current_response, warnings


def _split_into_chunks(text: str, chunk_size: int = 50) -> Iterator[str]:
    """Split text into chunks for simulated streaming.

    Prefers splitting at word boundaries when possible.

    Args:
        text: Text to split
        chunk_size: Target chunk size in characters

    Yields:
        Text chunks
    """
    if not text:
        return

    pos = 0
    while pos < len(text):
        end = min(pos + chunk_size, len(text))

        # If not at end, try to split at word boundary
        if end < len(text):
            # Look for last space in chunk
            space_pos = text.rfind(" ", pos, end)
            if space_pos > pos:
                end = space_pos + 1  # Include the space

        yield text[pos:end]
        pos = end


async def stream_chat_response(
    messages: list[dict[str, str]],
    search_results: list[SearchResult],
    settings: Settings,
    low_confidence: bool,
) -> AsyncIterator[dict[str, Any]]:
    """Stream a Claude chat response as SSE event dicts.

    BBj code blocks are validated via bbjcpl before streaming.
    Invalid code triggers automatic fix attempts (up to 3 total).

    Yields dicts with ``event`` and ``data`` keys suitable for
    sse-starlette's ``EventSourceResponse``.

    Event sequence:
    1. ``sources`` -- metadata about RAG results used for context
    2. ``validation_warning`` (0 or more) -- errors for unfixable code
    3. ``delta`` (repeated) -- incremental text chunks
    4. ``done`` -- token usage summary
    5. ``error`` (on failure) -- error message

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

    # Build sources metadata
    sources_list = [
        {
            "index": i,
            "title": r.title,
            "url": r.display_url or r.source_url,
            "source_type": r.source_type or "",
            "low_confidence": low_confidence,
        }
        for i, r in enumerate(search_results, 1)
    ]

    try:
        # Phase 1: Get complete response for validation
        initial_response, input_tokens, output_tokens = await _get_claude_response(
            client, settings, system_prompt, truncated
        )

        # Phase 2: Validate and fix BBj code blocks
        validated_response, warnings = await _validate_response_code(
            client, settings, initial_response, max_attempts=3
        )

        # Phase 3: Emit sources
        yield {"event": "sources", "data": json.dumps(sources_list)}

        # Phase 4: Emit validation warnings (if any)
        for warning in warnings:
            yield {
                "event": "validation_warning",
                "data": json.dumps(warning),
            }

        # Phase 5: Stream the validated response as deltas (simulated streaming)
        for chunk in _split_into_chunks(validated_response, chunk_size=50):
            yield {"event": "delta", "data": json.dumps({"text": chunk})}
            await asyncio.sleep(0.01)  # Small delay for streaming feel

        # Phase 6: Done
        yield {
            "event": "done",
            "data": json.dumps(
                {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }
            ),
        }

    except Exception as exc:
        logger.exception("Chat stream error")
        yield {
            "event": "error",
            "data": json.dumps({"message": str(exc)}),
        }
