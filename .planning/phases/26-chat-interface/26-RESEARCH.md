# Phase 26: Chat Interface - Research

**Researched:** 2026-02-03
**Domain:** Web chat UI with Claude API streaming, FastAPI SSE, client-side markdown rendering
**Confidence:** HIGH

## Summary

This phase adds a `/chat` web page served from the existing FastAPI app where engineers ask BBj questions and receive Claude-generated, RAG-grounded answers with source citations. The response streams visibly via Server-Sent Events (SSE).

The standard approach is: (1) a FastAPI POST endpoint that calls the Anthropic Python SDK's async streaming API, pipes text deltas through `sse-starlette`'s `EventSourceResponse` as JSON-encoded SSE events, and (2) a single-page HTML chat UI using vanilla JavaScript with `fetch()` + `ReadableStream` for POST-based SSE consumption, `marked.js` for incremental markdown rendering, and Prism.js for BBj-aware code syntax highlighting.

HTMX was evaluated but rejected for this use case due to a fundamental, unresolved SSE newline issue (GitHub issue #2292, still open) that breaks multiline content like code blocks -- the exact scenario flagged in the success criteria. Vanilla JS with `fetch()` provides full control over SSE parsing, POST request bodies (needed for conversation history), and incremental rendering.

**Primary recommendation:** Use vanilla JS + `fetch()` ReadableStream for the frontend, `sse-starlette` EventSourceResponse for the backend, JSON-encode each SSE chunk to solve the newline problem, and `marked.js` + Prism.js for rendering.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `anthropic` | 0.77.0 | Claude API client (async streaming) | Official SDK with `AsyncAnthropic.messages.stream()` helper |
| `sse-starlette` | 3.2.0 | SSE response for FastAPI | W3C-compliant, built-in ping/disconnect, works with FastAPI natively |
| `jinja2` | 3.1.x | HTML template rendering | Already bundled with `fastapi[standard]`; single template for chat page |
| `marked.js` | 17.0.x | Client-side markdown-to-HTML | Fastest, simplest API (`marked.parse()`), GFM support, CDN-loadable |
| Prism.js | 1.30.0 | Code syntax highlighting with BBj | BBj language already defined (PR #3511), matches Docusaurus Prism themes |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI `StaticFiles` | (built-in) | Serve CSS/JS assets | Mount at `/static` for chat page assets |
| FastAPI `Jinja2Templates` | (built-in) | Render chat.html | Single template for the `/chat` route |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `marked.js` | `markdown-it` | Better CommonMark compliance and plugin system, but more verbose API; marked is simpler for this use case |
| Prism.js | highlight.js | highlight.js has auto-detection but larger bundle; Prism has native BBj support matching the Docusaurus site |
| Vanilla JS | HTMX | HTMX simplifies HTML swapping but has unresolved SSE newline bug (#2292) that breaks code blocks; also only supports GET-based EventSource, not POST with message history |
| `sse-starlette` | Raw `StreamingResponse` | Raw streaming works but lacks W3C compliance, ping heartbeats, and disconnect detection |
| `fetch()` ReadableStream | Native `EventSource` | EventSource is simpler but only supports GET (no POST body for conversation history) and no custom headers |

**Installation:**
```bash
# Backend (add to pyproject.toml dependencies)
uv add anthropic sse-starlette

# Frontend (CDN, no install needed)
# marked.js:  https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js
# Prism core: https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-core.min.js
# Prism BBj:  https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-bbj.min.js
# Prism theme: https://cdn.jsdelivr.net/npm/prismjs@1/themes/prism.min.css (light)
#              or prism-okaidia.min.css (dark, closest to Dracula)
```

## Architecture Patterns

### Recommended Project Structure
```
rag-ingestion/
├── src/bbj_rag/
│   ├── app.py               # Add chat router
│   ├── api/
│   │   ├── routes.py         # Existing search routes
│   │   └── chat.py           # NEW: /chat page + /chat/stream SSE endpoint
│   ├── chat/
│   │   ├── __init__.py
│   │   ├── prompt.py         # System prompt construction with RAG context
│   │   └── stream.py         # Anthropic SDK streaming + SSE generator
│   ├── templates/
│   │   └── chat.html         # Jinja2 template (single page)
│   └── static/
│       ├── chat.css           # Chat-specific styles
│       └── chat.js            # Vanilla JS: fetch SSE, render markdown
```

### Pattern 1: POST-based SSE Streaming (Backend)
**What:** Client POSTs conversation history, server streams Claude's response as SSE events
**When to use:** Every chat message exchange
**Example:**
```python
# Source: Anthropic SDK docs + sse-starlette docs
from anthropic import AsyncAnthropic
from sse_starlette import EventSourceResponse
from fastapi import APIRouter, Request
import json

router = APIRouter()
client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY from env

@router.post("/chat/stream")
async def chat_stream(request: Request, body: ChatRequest):
    async def generate():
        # 1. Run RAG search to get context
        results = await do_search(body.messages[-1].content, ...)

        # 2. Build system prompt with RAG context
        system_prompt = build_system_prompt(results)

        # 3. Stream Claude response
        async with client.messages.stream(
            model="claude-sonnet-4-5",
            max_tokens=2048,
            system=system_prompt,
            messages=body.messages,
        ) as stream:
            # 4. Send sources metadata first
            yield {"event": "sources", "data": json.dumps(sources_data)}

            # 5. Stream text deltas as JSON-encoded SSE
            async for text in stream.text_stream:
                yield {"event": "delta", "data": json.dumps({"text": text})}

            # 6. Send usage/completion signal
            final = await stream.get_final_message()
            yield {
                "event": "done",
                "data": json.dumps({
                    "input_tokens": final.usage.input_tokens,
                    "output_tokens": final.usage.output_tokens,
                })
            }

    return EventSourceResponse(generate())
```

### Pattern 2: fetch() + ReadableStream SSE Client
**What:** Client sends POST with JSON body, reads SSE stream from response
**When to use:** Frontend chat message handling
**Example:**
```javascript
// Source: MDN ReadableStream docs + SSE spec
async function sendMessage(messages) {
    const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages }),
        signal: abortController.signal,  // for stop button
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE lines from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop();  // keep incomplete line in buffer

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                // Handle event based on preceding 'event:' line
            }
            // Parse event: lines to know the event type
        }
    }
}
```

### Pattern 3: Incremental Markdown Rendering
**What:** Re-render accumulated text as markdown on each delta
**When to use:** Displaying streamed response with formatting
**Example:**
```javascript
// Source: marked.js docs
import { marked } from 'marked';

let accumulated = '';

function onDelta(text) {
    accumulated += text;
    // Re-parse full accumulated text (marked is fast enough)
    const html = marked.parse(accumulated);
    responseEl.innerHTML = html;
    // Re-highlight any code blocks
    responseEl.querySelectorAll('pre code').forEach(block => {
        Prism.highlightElement(block);
    });
}
```

### Pattern 4: JSON-Encoded SSE Events (Newline Solution)
**What:** JSON-encode each SSE data payload to safely transport newlines
**When to use:** Always -- this is the solution to the multiline SSE problem
**Example:**
```python
# Backend: JSON-encode handles \n safely
yield {"data": json.dumps({"text": "```bbj\nrem Hello\nprint \"world\"\n```"})}
# SSE wire format: data: {"text":"```bbj\\nrem Hello\\nprint \"world\"\\n```"}\n\n
# The \n inside JSON becomes \\n, which SSE treats as literal characters

# Client: JSON.parse() recovers original newlines
const data = JSON.parse(event.data);
// data.text === "```bbj\nrem Hello\nprint \"world\"\n```"
```

### Anti-Patterns to Avoid
- **Raw text in SSE data field:** Newlines in code blocks will truncate the SSE message. Always JSON-encode.
- **HTMX SSE for streaming code content:** The unresolved newline issue (#2292) makes HTMX SSE unsuitable for content containing code blocks.
- **EventSource for POST requests:** Native EventSource only supports GET. Use `fetch()` with `ReadableStream` for POST-based streaming with conversation history.
- **Rendering markdown on every single token:** While `marked.parse()` is fast, excessively frequent DOM updates cause visual flickering. Debounce or batch renders (e.g., every 50ms or every 3-5 tokens).
- **Building a full SPA framework:** The chat page is a single Jinja2 template with vanilla JS. Do not introduce React, Vue, or build tooling.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE event formatting | Manual `data: ...\n\n` string formatting | `sse-starlette` EventSourceResponse | Handles ping, disconnect detection, W3C compliance, proper headers |
| Markdown to HTML | Regex-based converter | `marked.js` | Edge cases in nested lists, code fences, inline code, etc. are endless |
| Code syntax highlighting | CSS class injection | Prism.js with BBj grammar | Language-specific tokenization is complex; BBj grammar already exists |
| Streaming text accumulation | Manual event concatenation | Anthropic SDK `stream.text_stream` | SDK handles content block assembly, error recovery, typing |
| SSE newline encoding | Custom escaping scheme | JSON.stringify/JSON.parse | Standard, well-tested, handles all special characters |
| Copy-to-clipboard button | Manual selection + execCommand | `navigator.clipboard.writeText()` | Modern API, works in all current browsers |

**Key insight:** The SSE newline problem is the main technical trap in this phase. It looks like you could just send raw text, but any response containing a code block with newlines will break. JSON encoding is the simple, proven solution.

## Common Pitfalls

### Pitfall 1: SSE Newline Truncation
**What goes wrong:** Code blocks in Claude's response contain newlines (`\n`). When sent as raw SSE `data:` fields, the SSE parser treats these as event delimiters, truncating the message at the first newline.
**Why it happens:** The SSE specification uses `\n\n` as event separator and `\n` as line separator. Content newlines are indistinguishable from protocol newlines.
**How to avoid:** JSON-encode every SSE data payload. JSON escapes `\n` as `\\n`, which the SSE parser treats as literal text. The client calls `JSON.parse()` to recover the original content.
**Warning signs:** Code blocks appear truncated or only show the first line; streaming seems to "skip" parts of responses.

### Pitfall 2: EventSource GET-Only Limitation
**What goes wrong:** Using native `EventSource` API for the chat stream. It works for the first message but cannot send conversation history (multi-turn context) because EventSource only supports GET requests.
**Why it happens:** The SSE/EventSource specification was designed for server push (e.g., stock tickers), not request-response patterns. It has no mechanism for request bodies.
**How to avoid:** Use `fetch()` with `ReadableStream` for POST-based SSE. Send the full `messages` array as JSON in the request body.
**Warning signs:** Attempting to encode long conversation history in URL query parameters; URL length limits; inability to send previous messages.

### Pitfall 3: Markdown Rendering Flicker During Streaming
**What goes wrong:** Setting `innerHTML` on every single text delta causes the browser to re-layout and re-render the entire response area, creating visible flicker especially with code blocks.
**Why it happens:** Each `innerHTML` assignment destroys and recreates all DOM nodes. The browser recalculates styles and layout each time.
**How to avoid:** Batch updates using `requestAnimationFrame()` or a simple debounce (e.g., render at most every 50ms). Accumulate deltas in a string buffer and only update the DOM on the next animation frame.
**Warning signs:** Text "flashes" during streaming; scroll position jumps; code blocks appear to blink.

### Pitfall 4: Incomplete Code Block During Streaming
**What goes wrong:** A partially-streamed code fence (e.g., the opening ` ``` ` has been received but not the closing ` ``` `) causes `marked.parse()` to produce broken HTML or treat remaining text as part of the code block.
**Why it happens:** Markdown parsing is stateful -- an unclosed code fence changes interpretation of all subsequent text.
**How to avoid:** Before rendering, check if there's an unclosed code fence in the accumulated text. If so, temporarily append a closing fence for rendering purposes only (don't modify the actual buffer). This gives clean intermediate renders.
**Warning signs:** Text after a code block opening appears as monospace; syntax highlighting applies to prose text.

### Pitfall 5: Not Handling Stream Abort (Stop Button)
**What goes wrong:** User clicks "Stop" but the server keeps streaming, wasting Claude API tokens and server resources.
**Why it happens:** The `AbortController.abort()` on the client closes the fetch connection, but the server's async generator may not detect the disconnect immediately.
**How to avoid:** Use `sse-starlette`'s built-in disconnect detection (`await request.is_disconnected()`), or rely on `sse-starlette`'s automatic cleanup when the client drops. The Anthropic SDK's `stream.close()` method can abort the API call. Wrap the streaming loop in a try/finally that calls `stream.close()`.
**Warning signs:** Claude API usage charges continue after user stops; server logs show continued streaming after client disconnect.

### Pitfall 6: Browser SSE Connection Limit (HTTP/1.1)
**What goes wrong:** With HTTP/1.1, browsers limit to 6 concurrent connections per domain. Long-lived SSE connections can exhaust this pool, blocking other requests.
**Why it happens:** SSE connections remain open for the duration of streaming. If multiple chat tabs are open, they consume connections.
**How to avoid:** This is mitigated by using `fetch()` instead of `EventSource` (fetch connections are released when the stream ends). Also, the chat stream is short-lived (duration of one Claude response), not persistent. HTTP/2 (negotiated default to 100 streams) eliminates this concern entirely.
**Warning signs:** Other API calls (search, static files) hang while a chat response is streaming; only happens with many open tabs.

## Code Examples

### Complete Backend: Chat Stream Endpoint
```python
# Source: Anthropic SDK helpers.md, sse-starlette PyPI docs, FastAPI templates docs
import json
from anthropic import AsyncAnthropic
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

router = APIRouter(prefix="/chat", tags=["chat"])
templates = Jinja2Templates(directory="templates")
anthropic_client = AsyncAnthropic()  # ANTHROPIC_API_KEY from env


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@router.get("", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Serve the chat HTML page."""
    return templates.TemplateResponse("chat.html", {"request": request})


@router.post("/stream")
async def chat_stream(body: ChatRequest, request: Request):
    """Stream Claude's response as SSE events."""

    async def generate():
        # 1. Extract latest user question for RAG search
        user_query = body.messages[-1].content

        # 2. Search RAG corpus (reuse existing search logic)
        # ... embed query, run hybrid search, get results ...

        # 3. Build system prompt with RAG context
        system_prompt = build_rag_system_prompt(search_results)

        # 4. Send source citations to client before streaming
        sources = [
            {
                "title": r.title,
                "url": r.display_url,
                "source_type": r.source_type,
            }
            for r in search_results
        ]
        yield {"event": "sources", "data": json.dumps(sources)}

        # 5. Stream Claude's response
        try:
            async with anthropic_client.messages.stream(
                model="claude-sonnet-4-5",
                max_tokens=2048,
                system=system_prompt,
                messages=[
                    {"role": m.role, "content": m.content}
                    for m in body.messages
                ],
            ) as stream:
                async for text in stream.text_stream:
                    yield {
                        "event": "delta",
                        "data": json.dumps({"text": text}),
                    }

                final = await stream.get_final_message()
                yield {
                    "event": "done",
                    "data": json.dumps({
                        "input_tokens": final.usage.input_tokens,
                        "output_tokens": final.usage.output_tokens,
                    }),
                }
        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(exc)}),
            }

    return EventSourceResponse(generate())
```

### Complete Frontend: SSE Consumer with Markdown Rendering
```javascript
// Source: MDN Fetch/ReadableStream, marked.js docs, Prism.js docs

// --- SSE Stream Consumer ---
async function streamChat(messages, responseEl, abortController) {
    const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages }),
        signal: abortController.signal,
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let accumulated = '';
    let currentEvent = 'message';
    let renderPending = false;

    function scheduleRender() {
        if (renderPending) return;
        renderPending = true;
        requestAnimationFrame(() => {
            renderMarkdown(accumulated, responseEl);
            renderPending = false;
        });
    }

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();  // incomplete line stays in buffer

        for (const line of lines) {
            if (line.startsWith('event: ')) {
                currentEvent = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
                const payload = line.slice(6);
                handleEvent(currentEvent, payload);
            }
        }
    }

    // Final render
    renderMarkdown(accumulated, responseEl);

    function handleEvent(event, dataStr) {
        const data = JSON.parse(dataStr);
        switch (event) {
            case 'delta':
                accumulated += data.text;
                scheduleRender();
                break;
            case 'sources':
                displaySources(data);
                break;
            case 'done':
                // Optionally show token usage
                break;
            case 'error':
                showError(data.message);
                break;
        }
    }
}

// --- Markdown Rendering with Syntax Highlighting ---
function renderMarkdown(text, element) {
    // Handle unclosed code fences for clean intermediate rendering
    let renderText = text;
    const fenceCount = (text.match(/```/g) || []).length;
    if (fenceCount % 2 !== 0) {
        renderText += '\n```';
    }

    element.innerHTML = marked.parse(renderText);

    // Apply Prism syntax highlighting to all code blocks
    element.querySelectorAll('pre code').forEach(block => {
        Prism.highlightElement(block);
    });
}
```

### Stop Button Implementation
```javascript
// Source: MDN AbortController docs
let currentAbort = null;

function onSendClick() {
    currentAbort = new AbortController();
    showStopButton();
    disableInput();

    streamChat(messages, responseEl, currentAbort)
        .catch(err => {
            if (err.name === 'AbortError') {
                // User clicked stop -- expected
            } else {
                showError(err.message);
            }
        })
        .finally(() => {
            hideStopButton();
            enableInput();
            currentAbort = null;
        });
}

function onStopClick() {
    if (currentAbort) {
        currentAbort.abort();
    }
}
```

### Copy Button for Code Blocks
```javascript
// Source: MDN navigator.clipboard API
function addCopyButtons(responseEl) {
    responseEl.querySelectorAll('pre').forEach(pre => {
        if (pre.querySelector('.copy-btn')) return;  // already has one
        const btn = document.createElement('button');
        btn.className = 'copy-btn';
        btn.textContent = 'Copy';
        btn.onclick = () => {
            const code = pre.querySelector('code').textContent;
            navigator.clipboard.writeText(code).then(() => {
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = 'Copy', 2000);
            });
        };
        pre.style.position = 'relative';
        pre.appendChild(btn);
    });
}
```

### RAG System Prompt Construction
```python
# Source: Project search.py + Anthropic messages API docs
def build_rag_system_prompt(results: list[SearchResult]) -> str:
    """Build a system prompt that grounds Claude in RAG search results."""
    context_blocks = []
    for i, r in enumerate(results, 1):
        block = f"[Source {i}: {r.title}]\n"
        block += f"URL: {r.display_url}\n"
        block += f"Type: {r.source_type}\n"
        if r.context_header:
            block += f"Context: {r.context_header}\n"
        block += f"\n{r.content}\n"
        context_blocks.append(block)

    context_text = "\n---\n".join(context_blocks)

    return f"""You are a BBj programming assistant embedded in the official documentation site.
Answer questions using ONLY the reference material provided below. When you use information
from a source, cite it inline using [Source N] notation matching the source numbers.

If the reference material doesn't contain enough information to fully answer the question,
say so clearly and indicate what aspects you can address.

Format your response using Markdown. Use ```bbj for BBj code blocks.

Reference Material:
{context_text}"""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WebSockets for chat | SSE via fetch() for LLM streaming | 2024-2025 | SSE is simpler, unidirectional (perfect for LLM responses), no connection upgrade needed |
| HTMX SSE extension | Vanilla JS fetch() + ReadableStream | 2025 | HTMX SSE newline bug (#2292) makes it unsuitable for code-heavy content |
| EventSource API | fetch() + ReadableStream | 2024-2025 | fetch() supports POST bodies and custom headers; EventSource is GET-only |
| Server-rendered chat pages | Client-side markdown rendering | 2024-2025 | Streaming text must be rendered incrementally; server can't render partial markdown |
| highlight.js auto-detect | Prism.js with explicit language | Stable | Prism has BBj language support; matches Docusaurus site theme |

**Deprecated/outdated:**
- `EventSource` API for POST-based chat: Cannot send message history in request body. Use `fetch()` + `ReadableStream` instead.
- HTMX SSE for multiline content: Open bug #2292 means code blocks break. Use vanilla JS.

## Open Questions

1. **Prism theme matching with Docusaurus**
   - What we know: Docusaurus uses `prism-react-renderer` with `github` (light) and `dracula` (dark) themes. Prism.js standalone has `prism.css` (light) and `prism-okaidia.css` (dark, closest to Dracula).
   - What's unclear: Exact CSS variable mapping between `prism-react-renderer` themes and standalone Prism themes. The colors will be close but may not be pixel-identical.
   - Recommendation: Use `prism.css` / `prism-okaidia.css` as base, then adjust CSS custom properties to match the Docusaurus color palette from `custom.css` (`--ifm-color-primary: #2563eb`).

2. **Claude model selection and cost**
   - What we know: `claude-sonnet-4-5` is the recommended model for the streaming examples. The project notes that ANTHROPIC_API_KEY spending alerts should be set.
   - What's unclear: Whether Claude Haiku 3.5 would be sufficient for BBj Q&A (cheaper, faster) or if Sonnet quality is needed.
   - Recommendation: Start with `claude-sonnet-4-5` as the default, make the model configurable via `Settings` (env var `BBJ_RAG_CHAT_MODEL`). Can downgrade to Haiku later based on quality evaluation.

3. **Conversation context window management**
   - What we know: Multi-turn is supported (session-only, clears on refresh). Claude has context limits.
   - What's unclear: How many turns of history to include before hitting token limits. Long conversations could exceed context.
   - Recommendation: Keep last N messages (e.g., 10 turns / 20 messages). Implement a simple sliding window. Monitor `input_tokens` from usage data to warn if approaching limits.

4. **Confidence hint when RAG context is thin**
   - What we know: The decision requires showing "Based on limited sources" when few/low-relevance results back the answer.
   - What's unclear: Exact threshold for "thin" context (number of results? score cutoff?).
   - Recommendation: Heuristic: if fewer than 2 search results returned OR the top result score is below a threshold (e.g., 0.3 RRF score), include a confidence disclaimer in the system prompt and send a `low_confidence` flag in the `sources` SSE event for the frontend to display.

## Sources

### Primary (HIGH confidence)
- Anthropic SDK helpers.md (GitHub) - Streaming API: `text_stream`, `get_final_message()`, async context manager pattern
- Anthropic Messages Streaming API docs (platform.claude.com) - Event types: `message_start`, `content_block_delta` (text_delta), `message_stop`; SSE format
- sse-starlette 3.2.0 (PyPI) - `EventSourceResponse`, dict yield format, ping/disconnect, W3C compliance
- Prism.js BBj language (GitHub commit 1134bdfc) - Full BBj grammar definition with keywords, operators, strings, comments
- MDN EventSource.close() - Client-side stream termination
- MDN Server-Sent Events specification - SSE data field multiline handling (`data:` prefix per line)

### Secondary (MEDIUM confidence)
- FastAPI templates documentation (fastapi.tiangolo.com) - Jinja2Templates, StaticFiles patterns
- marked.js 17.0.x (npm/CDN) - `marked.parse()` API, GFM support
- HTMX SSE newline issue #2292 (GitHub) - Confirmed unresolved, multiline HTML breaks SSE parsing
- Towards Data Science HTMX chatbot article (Nov 2025) - HTMX + SSE chat pattern, session-based architecture
- Multiple FastAPI + SSE + LLM streaming articles (Medium, 2025) - Patterns for StreamingResponse and EventSourceResponse

### Tertiary (LOW confidence)
- Prism vs highlight.js comparison sources - General consensus on Prism being lighter and more modular
- sse.js polyfill (GitHub) - Alternative for POST-based EventSource (not needed since using fetch())

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified via official docs/PyPI/npm; versions confirmed current
- Architecture: HIGH - POST-based SSE with fetch() is well-established pattern for LLM chat; verified across multiple independent sources
- SSE newline solution: HIGH - JSON encoding is the documented standard solution per MDN and multiple framework issue trackers
- Frontend rendering: HIGH - marked.js + Prism.js verified with CDN availability and BBj language support
- HTMX rejection: HIGH - Issue #2292 confirmed open and unresolved; fundamental SSE protocol limitation
- Pitfalls: MEDIUM - Based on common patterns across multiple sources; some edge cases (debounce timing, token limits) need tuning during implementation

**Research date:** 2026-02-03
**Valid until:** 2026-03-05 (stable domain, 30 days)
