# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-03)

**Core value:** Stakeholders can understand the BBj AI strategy through a well-structured documentation site, backed by a running RAG system serving retrieval via REST API and MCP server.
**Current focus:** v1.5 Alpha-Ready RAG System

## Current Position

Milestone: v1.5 Alpha-Ready RAG System -- DEFINING REQUIREMENTS
Phase: Not started (defining requirements)
Plan: --
Status: Defining requirements for v1.5
Last activity: 2026-02-03 -- Milestone v1.5 started

Progress: [░░░░░░░░░░] 0%

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

- Concurrent ingestion workers (parallel embedding calls to keep GPU saturated)
- Persistent HTTP connection reuse for Ollama embedding calls during ingestion
- Map source_url to clickable HTTP links (e.g., flare:// -> https://documentation.basis.cloud/...)
- Source-balanced ranking (boosting minority sources like PDF, BBj Source for more diverse top-k)

### Known Operational Notes

- Ollama must be running on host with `OLLAMA_HOST=0.0.0.0:11434` for Docker connectivity
- shm_size required for pgvector HNSW index builds (256mb minimum)
- PDF and BBj Source source-targeted queries rank below Flare's 88% corpus dominance (corpus imbalance, not pipeline issue)
- Engineers have BBj (and bbjcpl) installed locally — distribution not needed in Docker
- Alpha deployment targets shared server on local network + local per-engineer option

## Session Continuity

Last session: 2026-02-03
Stopped at: Defining v1.5 requirements
Resume file: None
Next action: Complete requirements definition and roadmap creation
