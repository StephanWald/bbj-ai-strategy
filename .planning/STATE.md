# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-06)

**Core value:** Stakeholders can understand the BBj AI strategy through a well-structured documentation site, backed by a running RAG system serving retrieval via REST API and MCP server.
**Current focus:** Phase 35 complete -- Implementation Roadmap Restructure done

## Current Position

Milestone: v1.7 Documentation Refresh & Fine-Tuning Strategy
Phase: 35 (4 of 5 in v1.7)
Plan: 1 of 1 in current phase
Status: Phase complete
Last activity: 2026-02-06 -- Completed 35-01-PLAN.md (Implementation Roadmap Restructure)

Progress: [#######...] 100% (7/7 plans)

## Performance Metrics

**Cumulative:**
- v1.0-v1.6: 33 phases, 75 plans delivered across 7 milestones
- v1.7: 7/7 plans

**By Phase (v1.7):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 32 | 2/2 | 56min | 28min |
| 33 | 2/2 | 21min | 10.5min |
| 34 | 2/2 | 14min | 7min |
| 35 | 1/1 | 2min | 2min |

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

**Phase 34 decisions (34-01):**
- Continue.dev as primary near-term IDE integration path (over Copilot BYOK)
- config.yaml format for walkthrough (JSON is deprecated)
- FIM training gap as subsection within Continue.dev section (needs space for technical detail)
- Enterprise BYOK updated to public preview (January 2026)
- Langium AI content preserved in place for Plan 02 recontextualization

**Phase 34 decisions (34-02):**
- Section order: Continue.dev -> Why Not Copilot -> Foundation -> Language server sections -> Langium AI -> Status -> What Comes Next
- Ghost text as "closest next milestone" with bbj-vscode + bbj-intellij infrastructure already in place
- Langium AI promoted to standalone section under Eclipse Langium umbrella framing (not "Alternative Architecture")
- LSP 3.18 softened to "potential migration path" (conditional, not definite)
- eclipse-langium/langium-ai as primary repo reference (TypeFox/langium-ai archived Sept 2025)

**Phase 35 decisions (35-01):**
- Status-tier organization for "What We Built" section (ROAD-01): operational -> exploration -> research progression
- Forward plan as bulleted list grouped by area, no phases/timelines/costs (ROAD-02): user constraint
- Both Decision callout boxes removed (ROAD-03): chapter is now the current state summary
- Mermaid diagram removed, cross-references trimmed to closing paragraph (ROAD-04): 4-phase diagram irrelevant without phases
- Chapter 7 reduced from 311 to 135 lines (56% reduction)
- 4 stale cross-references in Chapters 2, 4, 5, 6 identified for Phase 36 scope

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
- Chapter 4 fully rewritten (674 lines): Continue.dev primary, language server repositioned, Langium AI recontextualized, status using Phase 32 conventions
- Chapter 7 restructured (135 lines): progress-and-plan chapter with comparison table, component summary, forward plan

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-06
Stopped at: Completed 35-01-PLAN.md (Implementation Roadmap Restructure) -- Phase 35 complete, v1.7 milestone complete (7/7 plans)
Resume file: None
Next action: Phase 36 (Cross-Chapter Consistency) if planned, or begin next milestone
