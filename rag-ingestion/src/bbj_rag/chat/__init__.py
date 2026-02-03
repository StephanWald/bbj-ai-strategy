"""Chat module: RAG-grounded system prompts and Claude API streaming."""

from bbj_rag.chat.prompt import build_rag_system_prompt
from bbj_rag.chat.stream import stream_chat_response

__all__ = ["build_rag_system_prompt", "stream_chat_response"]
