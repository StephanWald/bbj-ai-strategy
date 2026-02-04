"""Chat module: RAG-grounded system prompts and Claude API streaming."""

from bbj_rag.chat.prompt import build_rag_system_prompt
from bbj_rag.chat.stream import stream_chat_response
from bbj_rag.chat.validation import (
    CodeBlock,
    build_fix_prompt,
    extract_code_blocks,
    replace_code_block,
    validate_code_blocks,
)

__all__ = [
    "CodeBlock",
    "build_fix_prompt",
    "build_rag_system_prompt",
    "extract_code_blocks",
    "replace_code_block",
    "stream_chat_response",
    "validate_code_blocks",
]
