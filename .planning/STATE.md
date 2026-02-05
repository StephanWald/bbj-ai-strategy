# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-05)

**Core value:** Stakeholders can understand the BBj AI strategy through a well-structured documentation site, backed by a running RAG system serving retrieval via REST API and MCP server.
**Current focus:** v1.5 shipped — ready for v1.6 planning

## Current Position

Milestone: v1.5 Alpha-Ready RAG System — **SHIPPED**
Phase: 29 of 29 — Complete
Plan: All complete
Status: Milestone shipped
Last activity: 2026-02-05 — v1.5 milestone complete

Progress: [██████████] 100%

## Performance Metrics

**Cumulative:**
- v1.0: 5 phases, 15 plans (docs site shipped)
- v1.1: 2 phases, 5 plans (code corrections + branding)
- v1.2: 7 phases, 15 plans (RAG ingestion pipeline)
- v1.3: 5 phases, 10 plans (MCP architecture integration)
- v1.4: 7 phases, 14 plans (RAG deployment + validation)
- v1.5: 5 phases, 13 plans (alpha-ready features)
- **Total: 31 phases, 72 plans delivered across 6 milestones**

## Accumulated Context

### Decisions

See .planning/PROJECT.md Key Decisions table for full log.

**v1.5 key decisions:**
- JSON-encode all SSE data payloads to safely transport newlines in code blocks
- FastMCP stateless_http=True with streamable_http_path="/" for remote MCP access
- Each BBj keyword counts as separate indicator for permissive BBj detection
- Batch response + simulated streaming for validation (validates before user sees code)
- Parallel ingestion as default, --sequential for fallback

### Known Operational Notes

- Ollama must be running on host with `OLLAMA_HOST=0.0.0.0:11434` for Docker connectivity
- shm_size required for pgvector HNSW index builds (256mb minimum)
- Engineers have BBj (and bbjcpl) installed locally — bbjcpl validation runs host-side, not in Docker
- Alpha deployment targets shared server on local network + local per-engineer option
- ANTHROPIC_API_KEY needed for chat interface — set spending alerts
- Remote access: Claude Desktop connects via `npx mcp-remote http://<server>:10800/mcp --allow-http`

### Future Improvements (Captured from Alpha Development)

**Content Quality (future milestone):**
- Improve RAG retrieval quality — better chunking strategies, embedding tuning, search parameter optimization
- Reduce hallucinations — stronger grounding instructions, citation verification
- Response quality — better prompting, example-based guidance

**Streaming UX (from Phase 28):**
- Validation batch-then-simulate pattern causes response to arrive in one rush after long wait
- Consider exploring alternatives: progressive validation, partial streaming, or visual validation indicator

**New Data Source:**
- BBjAPI JavaDoc is available and should be ingested — provides structured API documentation that would significantly improve RAG quality for API-related queries

**Performance (from Phase 29):**
- Parallel ingestion achieved ~1.24x speedup (4 workers vs sequential) — bottleneck appears to be Ollama embedding throughput, not chunk parallelism
- Further optimization would require profiling Ollama GPU utilization and batch sizes

## Session Continuity

Last session: 2026-02-05
Stopped at: v1.5 milestone complete
Resume file: None
Next action: `/gsd:new-milestone` to define v1.6 scope
