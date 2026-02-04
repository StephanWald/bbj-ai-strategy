# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-03)

**Core value:** Stakeholders can understand the BBj AI strategy through a well-structured documentation site, backed by a running RAG system serving retrieval via REST API and MCP server.
**Current focus:** v1.5 Alpha-Ready RAG System — Phase 29 (Ingestion Performance) In Progress

## Current Position

Milestone: v1.5 Alpha-Ready RAG System
Phase: 29 of 29 (Ingestion Performance) — In Progress
Plan: 2 of 3 complete
Status: In progress — Parallel chunk processor complete
Last activity: 2026-02-04 — Completed 29-02-PLAN.md

Progress: [█████████░] 93%

## Performance Metrics

**Cumulative:**
- v1.0: 5 phases, 15 plans (docs site shipped)
- v1.1: 2 phases, 5 plans (code corrections + branding)
- v1.2: 7 phases, 15 plans (RAG ingestion pipeline)
- v1.3: 5 phases, 10 plans (MCP architecture integration)
- v1.4: 7 phases, 14 plans (RAG deployment + validation)
- v1.5 (in progress): 4 phases, 10 plans (alpha-ready features)
- **Total: 29 phases, 68 plans delivered across 5 milestones**

## Accumulated Context

### Decisions

See .planning/PROJECT.md Key Decisions table for full log (33 decisions, all validated).

**Phase 26 decisions:**
- JSON-encode all SSE data payloads to safely transport newlines in code blocks
- Sources event emitted before streaming with low_confidence flag per-source
- Sliding window message truncation via chat_max_history setting (default 20 messages)
- Sticky positioning for chat input bar (works in flex layout without overlap)
- marked.js imported as ES module from CDN (no build tooling)
- Prism autoloader for on-demand BBj grammar loading

**Phase 27 decisions:**
- FastMCP stateless_http=True with streamable_http_path="/" to avoid double-prefix
- mcp.session_manager.run() context wraps FastAPI yield for proper MCP lifecycle
- Explicit 0.0.0.0 binding in docker-compose.yml for LAN accessibility

**Phase 28 decisions:**
- Each BBj keyword counts as separate indicator for permissive detection
- BASIC-style print/input statements (no parens) count as indicator
- Compiler config read from env vars to avoid circular imports
- Batch response + simulated streaming for validation (validates before user sees code)
- Max 3 total attempts per code block (initial + 2 fix attempts)
- Graceful degradation when bbjcpl unavailable (skip validation, no warning)

**Phase 29 decisions:**
- httpx.Limits(max_connections=10, max_keepalive_connections=5) for connection pooling
- 5-minute timeout for large embedding batches
- OLLAMA_HOST env var fallback for backward compatibility with existing deployments
- asyncio.Queue for batch distribution - workers pull until exhausted
- Each worker owns its AsyncOllamaEmbedder for connection pool isolation
- JSON lines format for failure log - append-only, easy streaming reads
- Exponential backoff 2^attempt seconds (1s, 2s, 4s) between retry attempts

### Pending Todos (Carried Forward into v1.5)

All carried-forward items now mapped to roadmap phases:
- Concurrent ingestion workers → Phase 29 (PERF-01, PERF-02, PERF-03)
- Persistent HTTP connection reuse → Phase 29 (PERF-02)
- Map source_url to clickable HTTP links → Phase 25 (QUAL-02, QUAL-03)
- Source-balanced ranking → Phase 25 (QUAL-01)

### Known Operational Notes

- Ollama must be running on host with `OLLAMA_HOST=0.0.0.0:11434` for Docker connectivity
- shm_size required for pgvector HNSW index builds (256mb minimum)
- PDF and BBj Source source-targeted queries rank below Flare's 88% corpus dominance (addressed by Phase 25 balanced ranking)
- Engineers have BBj (and bbjcpl) installed locally — bbjcpl validation runs host-side, not in Docker
- Alpha deployment targets shared server on local network + local per-engineer option
- ANTHROPIC_API_KEY needed for Phase 26 (Claude API) — set spending alerts
- Remote access: Claude Desktop connects via `npx mcp-remote http://<server>:10800/mcp --allow-http`

### Research Flags

- Phase 26 (Chat Interface): Research COMPLETE — JSON-encoded SSE events, vanilla JS fetch() for POST-based SSE
- Phase 27 (Remote Access): Research COMPLETE — FastMCP stateless_http mode, lifespan session manager integration
- Phase 28 (Compiler Validation): COMPLETE — Code block extraction, validation loop, simulated streaming
- Phase 29: Standard patterns, skip research

### Future Improvements (Captured from Phase 26 Testing)

**Content Quality (future milestone):**
- Improve RAG retrieval quality — better chunking strategies, embedding tuning, search parameter optimization
- Reduce hallucinations — stronger grounding instructions, citation verification
- Response quality — better prompting, example-based guidance

**Streaming UX (from Phase 28):**
- Validation batch-then-simulate pattern causes response to arrive in one rush after long wait
- Consider exploring alternatives: progressive validation, partial streaming, or visual validation indicator

**New Data Source:**
- BBjAPI JavaDoc is available and should be ingested — provides structured API documentation that would significantly improve RAG quality for API-related queries

## Session Continuity

Last session: 2026-02-04
Stopped at: Completed 29-02-PLAN.md (Parallel Chunk Processor)
Resume file: None
Next action: Execute 29-03-PLAN.md (CLI Integration)
