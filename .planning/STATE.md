# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-05)

**Core value:** Stakeholders can understand the BBj AI strategy through a well-structured documentation site, backed by a running RAG system serving retrieval via REST API and MCP server.
**Current focus:** v1.6 Data Expansion — BBjAPI JavaDoc ingestion and training data infrastructure

## Current Position

Milestone: v1.6 Data Expansion
Phase: 30 of 31 (BBjAPI JavaDoc Ingestion) — Complete
Plan: 2 of 2 complete
Status: Phase complete
Last activity: 2026-02-05 — Completed 30-02-PLAN.md (pipeline integration)

Progress: [██░░░░░░░░] 20%

## Performance Metrics

**Cumulative:**
- v1.0: 5 phases, 15 plans (docs site shipped)
- v1.1: 2 phases, 5 plans (code corrections + branding)
- v1.2: 7 phases, 15 plans (RAG ingestion pipeline)
- v1.3: 5 phases, 10 plans (MCP architecture integration)
- v1.4: 7 phases, 14 plans (RAG deployment + validation)
- v1.5: 5 phases, 13 plans (alpha-ready features)
- v1.6: 1 phase, 2 plans (BBjAPI JavaDoc ingestion complete)
- **Total: 31 phases, 74 plans delivered across 6 milestones**

## Accumulated Context

### Decisions

See .planning/PROJECT.md Key Decisions table for full log.

**v1.6 key decisions:**
- One Document per BBj API class (not per method) for complete API overview queries
- html.parser for lightweight HTML fragment parsing in JavaDoc
- Truncate method descriptions to first sentence or 100 chars for scannable reference cards
- Use BBJ_HOME env var for JavaDoc path instead of data_dir
- Preserve parser-set display_url when map_display_url returns empty

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
- BBJ_HOME environment variable required for JavaDoc ingestion (points to BBj installation)

### Future Improvements (Captured from Alpha Development)

**Content Quality (future milestone):**
- Improve RAG retrieval quality — better chunking strategies, embedding tuning, search parameter optimization
- Reduce hallucinations — stronger grounding instructions, citation verification
- Response quality — better prompting, example-based guidance

**Streaming UX (from Phase 28):**
- Validation batch-then-simulate pattern causes response to arrive in one rush after long wait
- Consider exploring alternatives: progressive validation, partial streaming, or visual validation indicator

**Performance (from Phase 29):**
- Parallel ingestion achieved ~1.24x speedup (4 workers vs sequential) — bottleneck appears to be Ollama embedding throughput, not chunk parallelism
- Further optimization would require profiling Ollama GPU utilization and batch sizes

## Session Continuity

Last session: 2026-02-05T06:03:33Z
Stopped at: Completed 30-02-PLAN.md (pipeline integration)
Resume file: None
Next action: Phase 30 complete, proceed to next milestone phase
