# Phase 26: Chat Interface - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Web chat interface at `/chat` where engineers ask BBj questions and get Claude-generated answers grounded in RAG results, with streaming responses and source citations. No authentication required. Multi-turn conversation within a session.

Excludes: user accounts, saved history, admin features, alternative LLM backends.

</domain>

<decisions>
## Implementation Decisions

### Chat page layout & feel
- Documentation companion vibe — should feel like part of the existing docs site experience, not a standalone tool or generic chatbot
- Bottom-fixed input bar — input pinned to bottom of viewport, conversation scrolls above (standard chat pattern)
- Claude's Discretion: empty state design (suggested questions, intro text, or combination)
- Claude's Discretion: whether to integrate into docs site navigation or keep as standalone `/chat` route

### Answer presentation
- BBj code blocks with syntax highlighting and copy button — match docs site code block style
- Subtle pulsing dot indicator while streaming — disappears when response completes
- Claude's Discretion: answer length calibration based on question complexity
- Show a confidence hint when RAG context is thin — e.g., "Based on limited sources" note when few or low-relevance results back the answer

### Source citations
- Inline links woven into the answer text — sources referenced naturally where claims are made, like Wikipedia-style references
- Cite top 2-3 supporting sources per claim when multiple results are relevant
- Show source type labels (Flare Docs, PDF Manual, BBj Source, MDX) alongside link text — engineers should know where information comes from
- Source links open in new tab — keeps chat conversation intact

### Conversation behavior
- Multi-turn conversation supported — follow-up questions carry prior context
- Session-only history — clears on page refresh, no persistence
- Clear/New conversation button — visible way to reset without refreshing
- Stop button while streaming — user can halt a response mid-stream
- Input disabled during streaming — one question at a time, re-enabled after stream completes or is stopped

### Claude's Discretion
- Empty state design and content
- Docs site navigation integration approach
- Answer length calibration
- Error state handling and messaging
- Exact visual styling and spacing within documentation companion aesthetic

</decisions>

<specifics>
## Specific Ideas

- Documentation companion feel — the chat should feel like it belongs with the docs, not like a separate product bolted on
- Code blocks should match the styling engineers already see on the documentation site
- Source type visibility matters — engineers want to know if an answer comes from official Flare docs vs PDF manual vs source code

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 26-chat-interface*
*Context gathered: 2026-02-03*
