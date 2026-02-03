---
phase: 26-chat-interface
plan: 01
subsystem: api
tags: [anthropic, claude, sse, streaming, fastapi, chat, rag]

# Dependency graph
requires:
  - phase: 25-result-quality
    provides: "SearchResult dataclass with display_url, source_type; async_hybrid_search; rerank_for_diversity"
provides:
  - "POST /chat/stream SSE endpoint with sources/delta/done/error events"
  - "build_rag_system_prompt() for RAG-grounded system prompts"
  - "stream_chat_response() async generator for Claude API streaming"
  - "Chat config settings (model, max_tokens, confidence thresholds)"
affects: [26-02-chat-ui, 26-03-chat-polish]

# Tech tracking
tech-stack:
  added: [anthropic, sse-starlette, jinja2]
  patterns: [post-based-sse-streaming, json-encoded-sse-events, rag-grounded-prompts]

key-files:
  created:
    - rag-ingestion/src/bbj_rag/chat/__init__.py
    - rag-ingestion/src/bbj_rag/chat/prompt.py
    - rag-ingestion/src/bbj_rag/chat/stream.py
    - rag-ingestion/src/bbj_rag/api/chat.py
  modified:
    - rag-ingestion/pyproject.toml
    - rag-ingestion/src/bbj_rag/config.py
    - rag-ingestion/src/bbj_rag/app.py

key-decisions:
  - "JSON-encode all SSE data payloads to safely transport newlines in code blocks"
  - "Use cast() for MessageParam typing rather than runtime conversion"
  - "Emit low_confidence flag per-source in sources event for frontend flexibility"

patterns-established:
  - "SSE event dict format: {event: str, data: json.dumps(...)} for sse-starlette"
  - "Sliding window message truncation via chat_max_history setting"
  - "Confidence heuristic: fewer than min_results OR top score below min_score"

# Metrics
duration: 4min
completed: 2026-02-03
---

# Phase 26 Plan 01: Chat Backend Infrastructure Summary

**POST /chat/stream SSE endpoint with Anthropic SDK streaming, RAG-grounded system prompts with numbered source blocks, and JSON-encoded event payloads (sources/delta/done/error)**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-03T12:54:27Z
- **Completed:** 2026-02-03T12:58:24Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Chat module with prompt construction (numbered source blocks, citation instructions, low_confidence caveat) and Claude API async streaming
- FastAPI SSE endpoint at POST /chat/stream that orchestrates Ollama embedding, hybrid search, diversity reranking, and Claude streaming
- All SSE events JSON-encoded to solve the multiline newline problem for code blocks
- Configurable chat settings: model, max_tokens, max_history, confidence thresholds

## Task Commits

Each task was committed atomically:

1. **Task 1: Add dependencies and chat config settings** - `0ad1669` (feat)
2. **Task 2: Create chat module and wire SSE streaming endpoint** - `05b6a09` (feat)

## Files Created/Modified
- `rag-ingestion/src/bbj_rag/chat/__init__.py` - Chat module package with re-exports
- `rag-ingestion/src/bbj_rag/chat/prompt.py` - build_rag_system_prompt() with numbered source blocks and citation instructions
- `rag-ingestion/src/bbj_rag/chat/stream.py` - stream_chat_response() async generator yielding SSE event dicts
- `rag-ingestion/src/bbj_rag/api/chat.py` - GET /chat (placeholder) and POST /chat/stream (SSE streaming)
- `rag-ingestion/src/bbj_rag/app.py` - Added chat router inclusion
- `rag-ingestion/src/bbj_rag/config.py` - Added chat_model, chat_max_tokens, chat_max_history, confidence settings
- `rag-ingestion/pyproject.toml` - Added anthropic, sse-starlette, jinja2 dependencies

## Decisions Made
- JSON-encode all SSE data payloads -- prevents newline truncation in code blocks (the primary pitfall identified in research)
- Use `cast()` for Anthropic MessageParam typing rather than constructing TypedDicts at runtime -- cleaner and avoids unnecessary object creation
- Emit `low_confidence` flag per-source entry in the sources event rather than as a separate event -- gives frontend flexibility to display inline
- Sources event emitted before streaming begins -- allows frontend to render source pills while response streams

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed mypy type error for Anthropic MessageParam**
- **Found during:** Task 2 (commit attempt, caught by pre-commit mypy hook)
- **Issue:** `list[dict[str, str]]` not assignable to `Iterable[MessageParam]` -- the Anthropic SDK expects TypedDict with `role: Literal["user", "assistant"]`
- **Fix:** Added `from anthropic.types import MessageParam` and `cast(list[MessageParam], ...)` for the truncated messages
- **Files modified:** rag-ingestion/src/bbj_rag/chat/stream.py
- **Verification:** mypy passes cleanly
- **Committed in:** 05b6a09 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Type fix required for pre-commit hooks to pass. No scope creep.

## Issues Encountered
- Pre-existing test failure in test_pdf_parser.py (unrelated to this plan) -- confirmed by running test on prior commit. All 338 other tests pass.

## User Setup Required

ANTHROPIC_API_KEY environment variable required for Claude API access.
- Source: console.anthropic.com -> API Keys -> Create Key
- Set as: `export ANTHROPIC_API_KEY=sk-ant-...` or in .env/Docker config
- Verification: The /chat/stream endpoint will return an error event if the key is missing

## Next Phase Readiness
- SSE streaming contract fully defined and ready for frontend consumption (Plan 02)
- GET /chat returns placeholder HTML -- Plan 02 will add Jinja2 template with chat UI
- All event types documented: sources, delta, done, error

---
*Phase: 26-chat-interface*
*Completed: 2026-02-03*
