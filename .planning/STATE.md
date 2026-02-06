# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-05)

**Core value:** Stakeholders can understand the BBj AI strategy through a well-structured documentation site, backed by a running RAG system serving retrieval via REST API and MCP server.
**Current focus:** v1.7 Documentation Refresh & Fine-Tuning Strategy

## Current Position

Milestone: v1.7 Documentation Refresh & Fine-Tuning Strategy
Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-02-06 — Milestone v1.7 started

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Cumulative:**
- v1.0: 5 phases, 15 plans (docs site shipped)
- v1.1: 2 phases, 5 plans (code corrections + branding)
- v1.2: 7 phases, 15 plans (RAG ingestion pipeline)
- v1.3: 5 phases, 10 plans (MCP architecture integration)
- v1.4: 7 phases, 14 plans (RAG deployment + validation)
- v1.5: 5 phases, 13 plans (alpha-ready features)
- v1.6: 2 phases, 3 plans (data expansion)
- **Total: 32 phases, 75 plans delivered across 7 milestones**

## Accumulated Context

### Decisions

See .planning/PROJECT.md Key Decisions table for full log (57 decisions).

**Recent key decisions (v1.6):**
- One Document per BBj API class (not per method) for complete API overview queries
- BBJ_HOME env var for JavaDoc path instead of data_dir
- Markdown-first training data format (human-editable, GitHub-renderable)
- JSON Schema validation for front matter with jsonschema library
- Topic-based flat directory organization (gui/, database/, etc.)

### Known Operational Notes

- Ollama must be running on host with `OLLAMA_HOST=0.0.0.0:11434` for Docker connectivity
- shm_size required for pgvector HNSW index builds (256mb minimum)
- Engineers have BBj (and bbjcpl) installed locally — bbjcpl validation runs host-side, not in Docker
- Alpha deployment targets shared server on local network + local per-engineer option
- ANTHROPIC_API_KEY needed for chat interface — set spending alerts
- Remote access: Claude Desktop connects via `npx mcp-remote http://<server>:10800/mcp --allow-http`
- BBJ_HOME environment variable required for JavaDoc ingestion (points to BBj installation)
- Training data validation: `python training-data/scripts/validate.py`

### Future Improvements (Captured)

**Content Quality (future milestone):**
- Improve RAG retrieval quality — better chunking strategies, embedding tuning, search parameter optimization
- Reduce hallucinations — stronger grounding instructions, citation verification
- Response quality — better prompting, example-based guidance

**Training Data (from Phase 31):**
- JSONL conversion tooling for fine-tuning (future TRAIN-F03)
- CI integration for validation script
- Content expansion across topic directories

## Session Continuity

Last session: 2026-02-06
Stopped at: v1.7 milestone started, defining requirements
Resume file: None
Next action: Research → Requirements → Roadmap
