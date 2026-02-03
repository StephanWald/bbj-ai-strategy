# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-03)

**Core value:** Stakeholders can understand the BBj AI strategy through a well-structured documentation site, backed by a running RAG system serving retrieval via REST API and MCP server.
**Current focus:** v1.5 Alpha-Ready RAG System — Phase 26 (Chat Interface)

## Current Position

Milestone: v1.5 Alpha-Ready RAG System
Phase: 25 of 29 (Result Quality Foundation) — COMPLETE
Plan: 3 of 3
Status: Phase 25 complete — ready for Phase 26
Last activity: 2026-02-03 — Completed Phase 25 (Result Quality Foundation)

Progress: [██░░░░░░░░] 20%

## Performance Metrics

**Cumulative:**
- v1.0: 5 phases, 15 plans (docs site shipped)
- v1.1: 2 phases, 5 plans (code corrections + branding)
- v1.2: 7 phases, 15 plans (RAG ingestion pipeline)
- v1.3: 5 phases, 10 plans (MCP architecture integration)
- v1.4: 7 phases, 14 plans (RAG deployment + validation)
- **Total: 26 phases, 59 plans delivered across 5 milestones**

## Accumulated Context

### Decisions

See .planning/PROJECT.md Key Decisions table for full log (33 decisions, all validated).

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

### Research Flags

- Phase 26 (Chat Interface): NEEDS research — SSE encoding for multi-line content, HTMX chat patterns
- Phase 27 (Remote Access): NEEDS research — MCP SDK mounting issues, Streamable HTTP fallback patterns
- Phases 25, 28, 29: Standard patterns, skip research

## Session Continuity

Last session: 2026-02-03
Stopped at: Phase 25 complete (all 3 plans executed, verified 14/14 must-haves)
Resume file: None
Next action: /gsd:discuss-phase 26 (Chat Interface)
