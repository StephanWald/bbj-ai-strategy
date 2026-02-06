# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-06)

**Core value:** Stakeholders can understand the BBj AI strategy through a well-structured documentation site, backed by a running RAG system serving retrieval via REST API and MCP server.
**Current focus:** Phase 33 complete -- Fine-Tuning Chapter Rewrite

## Current Position

Milestone: v1.7 Documentation Refresh & Fine-Tuning Strategy
Phase: 33 (2 of 5 in v1.7)
Plan: 2 of 2 in current phase
Status: Phase complete
Last activity: 2026-02-06 -- Completed 33-02-PLAN.md (Supporting Updates + Status)

Progress: [####......] 57% (4/7 plans)

## Performance Metrics

**Cumulative:**
- v1.0-v1.6: 33 phases, 75 plans delivered across 7 milestones
- v1.7: 4/7 plans

**By Phase (v1.7):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 32 | 2/2 | 56min | 28min |
| 33 | 2/2 | 21min | 10.5min |

## Accumulated Context

### Decisions

See .planning/PROJECT.md Key Decisions table for full log (57 decisions).

**Phase 32 decisions:**
- Retained legitimate "production" uses in Ch1 line 62 (customer environments) and Ch2 lines 205, 229 (compiler behavior, webforJ external project)
- Established status terminology pattern: operational / operational for internal exploration / active research / planned
- Left Ch2 TL;DR unchanged (architectural vision, not status claim)
- Ch5 architecture sections updated to distinguish current (Claude API + RAG) from planned (fine-tuned model) -- aspirational sections kept but marked as future
- Ch6 corpus table replaced with full 7-source table including per-source chunk counts (51,134 total)
- Ch5 Mermaid diagram left showing target architecture; Ch6 Mermaid diagram updated to show operational state

**Phase 33 decisions (33-01):**
- Qwen2.5-Coder-14B-Base as primary recommendation (FT-01): greater fine-tuning improvement, Base variant avoids alignment tax
- Base vs Instruct analysis with alignment tax concept (FT-03): Shadow-FT citation, practical consequence framing
- bbjcpl-based compile@1 as primary automated evaluation metric (FT-04): ground-truth syntax validation
- Constructive framing of bbjllm as "valuable first attempt" (FT-05): names 3 blockers directly while acknowledging accomplishments
- Two-repo training data pipeline with planned conversion (FT-06): training-data/ Markdown as contributor format, bbjllm ChatML as training input
- Section ordering: bbjllm Foundation -> Base Model Selection -> Training Data -> QLoRA -> Evaluation

**Phase 33 decisions (33-02):**
- Version comparison table showing bbjllm pinned versions vs current Feb 2026 (FT-02): highlights critical bitsandbytes bug fix
- Training Workflow section with artifact management, commit practices, iterative loop (FT-08)
- Q4_K_M as recommended quantization format (over Q4_0): better quality-to-size ratio at marginal size increase
- MCP tool status distinction: operational (search_bbj_knowledge, validate_bbj_syntax) vs planned (generate_bbj_code)

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
- Chapter 3 fully rewritten (702 lines, 9 major sections, all 9 FT requirements addressed)

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-06
Stopped at: Completed 33-02-PLAN.md (Supporting Updates + Status) -- Phase 33 complete (2/2 plans)
Resume file: None
Next action: Begin Phase 34 (next phase in v1.7 milestone)
