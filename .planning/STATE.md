# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-06)

**Core value:** Stakeholders can understand the BBj AI strategy through a well-structured documentation site, backed by a running RAG system serving retrieval via REST API and MCP server.
**Current focus:** Phase 32 - Multi-Chapter Status & Tone Update

## Current Position

Milestone: v1.7 Documentation Refresh & Fine-Tuning Strategy
Phase: 32 (1 of 5 in v1.7)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-02-06 -- Completed 32-01-PLAN.md (Chapters 1 & 2 status update)

Progress: [#.........] 14% (1/7 plans)

## Performance Metrics

**Cumulative:**
- v1.0-v1.6: 33 phases, 75 plans delivered across 7 milestones
- v1.7: 1/7 plans

**By Phase (v1.7):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 32 | 1/2 | 37min | 37min |

## Accumulated Context

### Decisions

See .planning/PROJECT.md Key Decisions table for full log (57 decisions).

**Phase 32 decisions:**
- Retained legitimate "production" uses in Ch1 line 62 (customer environments) and Ch2 lines 205, 229 (compiler behavior, webforJ external project)
- Established status terminology pattern: operational / operational for internal exploration / active research / planned
- Left Ch2 TL;DR unchanged (architectural vision, not status claim)

**Research findings informing v1.7:**
- 14B-Base recommended over 7B-Base (better fine-tuning improvement) and 32B-Instruct (alignment tax)
- Two-stage training: continued pretraining on raw BBj, then instruction fine-tuning
- bbjllm has 3 blocker-level issues: no validation set, full-sequence loss, Instruct model choice
- Continue.dev is practical IDE path; Copilot BYOK limited to chat only
- Evaluation methodology needed: bbjcpl-based compile@1 metric

### Known Operational Notes

- Ollama must be running on host with `OLLAMA_HOST=0.0.0.0:11434` for Docker connectivity
- Engineers have BBj (and bbjcpl) installed locally -- bbjcpl validation runs host-side
- ANTHROPIC_API_KEY needed for chat interface
- BBJ_HOME environment variable required for JavaDoc ingestion
- Research summary at .planning/research/fine-tuning/SUMMARY.md -- essential for Phase 33

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-06
Stopped at: Completed 32-01-PLAN.md (Chapters 1 & 2 status update)
Resume file: None
Next action: Execute 32-02-PLAN.md (Chapters 5 & 6 status update)
