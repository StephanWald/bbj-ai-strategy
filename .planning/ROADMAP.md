# Milestone v1.7: Documentation Refresh & Fine-Tuning Strategy

**Status:** In progress
**Phases:** 32-36
**Total Plans:** TBD

## Overview

v1.7 refreshes all 7 documentation chapters to reflect the actual state of the BBj AI strategy project as of February 2026. The biggest change is a research-backed rewrite of Chapter 3 (Fine-Tuning) incorporating findings from the bbjllm repo analysis — switching the recommendation from 7B-Base to 14B-Base, documenting the two-stage training approach, and adding evaluation methodology. Smaller updates correct status/tone across all chapters, update Chapter 4 (IDE Integration) with Continue.dev as the primary path, restructure Chapter 7's implementation roadmap against completed milestones, and ensure cross-chapter consistency for model names, tool status, and data counts.

## Phases

- [ ] **Phase 32: Multi-Chapter Status & Tone Update** - Update status sections and correct tone across chapters 1, 2, 5, 6
- [ ] **Phase 33: Fine-Tuning Chapter Rewrite** - Research-backed rewrite of Chapter 3 with 14B-Base recommendation and evaluation methodology
- [ ] **Phase 34: IDE Integration Update** - Update Chapter 4 with Continue.dev path and FIM requirements
- [ ] **Phase 35: Implementation Roadmap Restructure** - Restructure Chapter 7 separating completed work from forward plan
- [ ] **Phase 36: Cross-Chapter Consistency Pass** - Verify model names, tool status, data counts, and code samples across all chapters

## Phase Details

### Phase 32: Multi-Chapter Status & Tone Update

**Goal**: Readers of any chapter see an honest, current snapshot of what is operational versus what is planned
**Depends on**: Nothing (first phase)
**Requirements**: STAT-01, STAT-02, STAT-03, STAT-04, CHAT-01, CHAT-02
**Success Criteria** (what must be TRUE):
  1. Every chapter's "Where Things Stand" block describes the February 2026 state, not the January 2025 strategy paper state
  2. No chapter uses "production", "shipped", or "deployed" to describe any component -- "operational for internal exploration" is the ceiling
  3. Chapter 5 describes the web chat as operational with Claude API + RAG + SSE streaming + source citations
  4. Chapter 2 describes MCP tools with correct status: search_bbj_knowledge (operational), validate_bbj_syntax (operational), generate_bbj_code (planned)
  5. RAG system (51K+ chunks, REST API, MCP server, web chat) described consistently as operational for internal exploration
**Plans**: 1 plan

Plans:
- [ ] 32-01: Update status blocks and tone across chapters 1, 2, 5, 6

### Phase 33: Fine-Tuning Chapter Rewrite

**Goal**: Chapter 3 presents a research-backed fine-tuning strategy grounded in the actual bbjllm implementation and current (2026) best practices
**Depends on**: Phase 32 (status context established)
**Requirements**: FT-01, FT-02, FT-03, FT-04, FT-05, FT-06, FT-07, FT-08, FT-09
**Success Criteria** (what must be TRUE):
  1. Reader understands why 14B-Base is recommended over 7B-Base and 32B-Instruct, with the tradeoff analysis visible
  2. Reader can follow the two-stage training approach (continued pretraining then instruction fine-tuning) and understand why it matters for zero-representation languages
  3. The relationship between bbjllm repo (9,922 ChatML examples, 32B-Instruct, PEFT/QLoRA) and recommended approach is clearly documented with gap analysis
  4. Evaluation methodology section describes bbjcpl-based compile@1 metric and baseline comparison approach
  5. Training data pipeline connecting training-data/ markdown format to bbjllm ChatML JSONL is described
**Plans**: 2-3 plans (TBD at planning time)

Plans:
- [ ] 33-01: Update model recommendation, toolchain versions, and model comparison table
- [ ] 33-02: Add evaluation methodology, bbjllm relationship, training pipeline, and two-stage approach sections
- [ ] 33-03: Add training workflow recommendations and final chapter polish (if needed)

### Phase 34: IDE Integration Update

**Goal**: Chapter 4 presents a realistic near-term IDE integration path with Continue.dev rather than aspirational custom tooling
**Depends on**: Phase 33 (fine-tuning context needed for FIM discussion)
**Requirements**: IDE-01, IDE-02, IDE-03, IDE-04
**Success Criteria** (what must be TRUE):
  1. Continue.dev is presented as the primary IDE integration path with concrete configuration for connecting to a local Ollama model
  2. Copilot BYOK limitations are clearly stated: chat only, no inline completions for local models
  3. bbj-language-server + AI integration is positioned as a future phase with rationale for why it is deferred
  4. Reader understands that tab completion requires FIM-trained model and current ChatML training data only supports instruction/chat use cases
**Plans**: 1 plan

Plans:
- [ ] 34-01: Update Chapter 4 with Continue.dev path, Copilot BYOK status, and FIM requirements

### Phase 35: Implementation Roadmap Restructure

**Goal**: Chapter 7 separates completed work (7 milestones) from credible forward plan, replacing the original speculative timeline
**Depends on**: Phase 33, Phase 34 (forward plan references fine-tuning and IDE decisions)
**Requirements**: ROAD-01, ROAD-02, ROAD-03, ROAD-04
**Success Criteria** (what must be TRUE):
  1. Completed work (v1.0-v1.6) is clearly separated from remaining work in a restructured layout
  2. Forward-looking plan presents credible next steps informed by research findings (evaluation suite, training fixes, model deployment)
  3. "Paper Status Jan 2025" vs "Actual Feb 2026" comparison table shows concrete progress across all dimensions
  4. Cost and timeline estimates reflect actual experience (7 milestones shipped, real infrastructure costs) rather than original projections
**Plans**: 1 plan

Plans:
- [ ] 35-01: Restructure Chapter 7 with completed/remaining separation and updated estimates

### Phase 36: Cross-Chapter Consistency Pass

**Goal**: All 7 chapters use consistent terminology, model names, tool status, and data counts -- a reader moving between chapters encounters no contradictions
**Depends on**: Phase 32, 33, 34, 35 (all content changes complete)
**Requirements**: CONS-01, CONS-02, CONS-03, CONS-04
**Success Criteria** (what must be TRUE):
  1. Model name/size is consistent across all chapters: 14B-Base as primary recommendation, 32B-Instruct acknowledged as bbjllm experiment
  2. MCP tool names and operational status are identical in chapters 2, 4, 5, and 7
  3. Training data counts match across chapters: 9,922 ChatML examples in bbjllm, 2 seed examples in training-data/
  4. All BBj code samples compile cleanly via `bbjcpl -N` (existing samples not broken by surrounding text edits)
  5. Site builds with zero warnings (`npm run build` clean)
**Plans**: 1 plan

Plans:
- [ ] 36-01: Cross-chapter consistency audit and corrections

## Progress

**Execution Order:** 32 -> 33 -> 34 -> 35 -> 36

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 32. Multi-Chapter Status & Tone Update | v1.7 | 0/1 | Not started | - |
| 33. Fine-Tuning Chapter Rewrite | v1.7 | 0/3 | Not started | - |
| 34. IDE Integration Update | v1.7 | 0/1 | Not started | - |
| 35. Implementation Roadmap Restructure | v1.7 | 0/1 | Not started | - |
| 36. Cross-Chapter Consistency Pass | v1.7 | 0/1 | Not started | - |

## Coverage

| Requirement | Phase | Status |
|-------------|-------|--------|
| STAT-01 | 32 | Pending |
| STAT-02 | 32 | Pending |
| STAT-03 | 32 | Pending |
| STAT-04 | 32 | Pending |
| CHAT-01 | 32 | Pending |
| CHAT-02 | 32 | Pending |
| FT-01 | 33 | Pending |
| FT-02 | 33 | Pending |
| FT-03 | 33 | Pending |
| FT-04 | 33 | Pending |
| FT-05 | 33 | Pending |
| FT-06 | 33 | Pending |
| FT-07 | 33 | Pending |
| FT-08 | 33 | Pending |
| FT-09 | 33 | Pending |
| IDE-01 | 34 | Pending |
| IDE-02 | 34 | Pending |
| IDE-03 | 34 | Pending |
| IDE-04 | 34 | Pending |
| ROAD-01 | 35 | Pending |
| ROAD-02 | 35 | Pending |
| ROAD-03 | 35 | Pending |
| ROAD-04 | 35 | Pending |
| CONS-01 | 36 | Pending |
| CONS-02 | 36 | Pending |
| CONS-03 | 36 | Pending |
| CONS-04 | 36 | Pending |

**Mapped: 27/27 -- all v1.7 requirements covered.**

---
*Created: 2026-02-06*
