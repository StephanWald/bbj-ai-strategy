# Requirements: BBj AI Strategy v1.7 Documentation Refresh

**Defined:** 2026-02-06
**Core Value:** Stakeholders can understand the BBj AI strategy through a well-structured documentation site, backed by a running RAG system serving retrieval via REST API and MCP server.

## v1.7 Requirements

Requirements for the documentation refresh milestone. Each maps to roadmap phases.

### Status Updates (All Chapters)

- [x] **STAT-01**: All 7 chapters' "Where Things Stand" sections reflect actual project state as of February 2026
- [x] **STAT-02**: Tone corrected throughout: nothing described as "production" or "shipped" — use "operational for internal exploration" for running systems
- [x] **STAT-03**: RAG system (51K+ chunks, REST API, MCP server, web chat) reported as operational for internal exploration
- [x] **STAT-04**: MCP server reported with two operational tools (search_bbj_knowledge, validate_bbj_syntax) and one planned (generate_bbj_code)

### Chapter 3: Fine-Tuning Rewrite

- [ ] **FT-01**: Model recommendation updated from Qwen2.5-Coder-7B-Base to 14B-Base as primary recommendation, with rationale from research
- [ ] **FT-02**: Toolchain updated to current versions (Unsloth 2026.x, transformers 5.x, peft 0.18.x, Ollama 0.15.x)
- [ ] **FT-03**: Base vs Instruct model analysis added — when to use each, tradeoffs, recommendation for BBj
- [ ] **FT-04**: Evaluation methodology section added with bbjcpl-based compile@1 metric, evaluation suite design, base model baseline approach
- [ ] **FT-05**: Relationship to bbjllm repo documented — what exists (32B-Instruct, 9,922 examples, PEFT/QLoRA), how it differs from docs, recommended path forward
- [ ] **FT-06**: Training data pipeline section added — markdown format (training-data/) as canonical source, ChatML JSONL (bbjllm/) as training input, conversion pipeline described
- [ ] **FT-07**: Two-stage training approach described — Stage 1 continued pretraining on raw BBj, Stage 2 instruction fine-tuning
- [ ] **FT-08**: Training workflow recommendations added — artifact management, what to commit back, iterative improvement process
- [ ] **FT-09**: Model comparison table updated with Qwen3 models, current landscape assessment

### Chapter 4: IDE Integration Update

- [ ] **IDE-01**: Continue.dev presented as primary IDE integration path for fine-tuned model (chat + inline completion)
- [ ] **IDE-02**: Copilot BYOK status updated — chat only, no inline completions for local models, unstable integration
- [ ] **IDE-03**: bbj-language-server + AI positioned as future phase, not near-term
- [ ] **IDE-04**: FIM training noted as requirement for tab completion (current ChatML format is instruction-only)

### Chapter 5: Documentation Chat Update

- [x] **CHAT-01**: Web chat reported as operational for internal exploration — /chat endpoint with Claude API, SSE streaming, citations
- [x] **CHAT-02**: Architecture updated to reflect actual implementation (Claude API + RAG, not fine-tuned model)

### Chapter 7: Implementation Roadmap Restructure

- [ ] **ROAD-01**: Completed work clearly separated from remaining work in restructured phase layout
- [ ] **ROAD-02**: Forward-looking plan added with credible next steps based on research findings
- [ ] **ROAD-03**: Progress comparison table updated ("Paper Status Jan 2025" vs "Actual Feb 2026")
- [ ] **ROAD-04**: Cost and timeline estimates updated based on actual experience (7 milestones shipped)

### Cross-Chapter Consistency

- [ ] **CONS-01**: Model name/size consistent across all chapters (14B-Base recommendation, acknowledge 32B bbjllm experiment)
- [ ] **CONS-02**: MCP tool names and status consistent across chapters 2, 4, 5, 7
- [ ] **CONS-03**: Training data counts consistent (9,922 ChatML examples in bbjllm, 2 seed examples in training-data/)
- [ ] **CONS-04**: All BBj code samples remain compiler-validated (bbjcpl -N)

## Future Requirements

Deferred to later milestones.

- **TRAIN-01**: Actually fix bbjllm training script issues (completion masking, learning rate, validation split)
- **TRAIN-02**: Build evaluation suite and run baseline
- **TRAIN-03**: Execute recommended two-stage training approach
- **EVAL-01**: Measure fine-tuned model vs Claude+RAG on BBj tasks
- **CONT-01**: Expand training data corpus across topic directories
- **IDE-05**: Implement Continue.dev integration with fine-tuned model
- **MCP-01**: Implement generate_bbj_code MCP tool

## Out of Scope

| Feature | Reason |
|---------|--------|
| Fixing bbjllm training script | v1.7 documents recommendations; actual fixes are a separate effort |
| Running new training iterations | Documentation milestone, not model training milestone |
| Building evaluation suite | Recommended in docs, built in future milestone |
| Implementing generate_bbj_code | Requires trained model; documented as planned |
| Redesigning site layout/navigation | Content update only, no structural changes |
| New chapters or sub-pages | Update existing 7 chapters, no new pages |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STAT-01 | Phase 32 | Complete |
| STAT-02 | Phase 32 | Complete |
| STAT-03 | Phase 32 | Complete |
| STAT-04 | Phase 32 | Complete |
| CHAT-01 | Phase 32 | Complete |
| CHAT-02 | Phase 32 | Complete |
| FT-01 | Phase 33 | Pending |
| FT-02 | Phase 33 | Pending |
| FT-03 | Phase 33 | Pending |
| FT-04 | Phase 33 | Pending |
| FT-05 | Phase 33 | Pending |
| FT-06 | Phase 33 | Pending |
| FT-07 | Phase 33 | Pending |
| FT-08 | Phase 33 | Pending |
| FT-09 | Phase 33 | Pending |
| IDE-01 | Phase 34 | Pending |
| IDE-02 | Phase 34 | Pending |
| IDE-03 | Phase 34 | Pending |
| IDE-04 | Phase 34 | Pending |
| ROAD-01 | Phase 35 | Pending |
| ROAD-02 | Phase 35 | Pending |
| ROAD-03 | Phase 35 | Pending |
| ROAD-04 | Phase 35 | Pending |
| CONS-01 | Phase 36 | Pending |
| CONS-02 | Phase 36 | Pending |
| CONS-03 | Phase 36 | Pending |
| CONS-04 | Phase 36 | Pending |

**Coverage:**
- v1.7 requirements: 27 total
- Mapped to phases: 27/27
- Unmapped: 0

---
*Requirements defined: 2026-02-06*
*Last updated: 2026-02-06 after roadmap creation*
