# Phase 33: Fine-Tuning Chapter Rewrite - Context

**Gathered:** 2026-02-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Research-backed rewrite of Chapter 3 (Fine-Tuning) incorporating findings from the bbjllm repo analysis. Covers model recommendation (14B-Base), two-stage training approach, bbjllm gap analysis, and evaluation methodology. Does not add new capabilities or change the actual training infrastructure — this is documentation only.

</domain>

<decisions>
## Implementation Decisions

### Model comparison framing
- Guided comparison: present all 3 options (7B-Base, 14B-Base, 32B-Instruct) with tradeoffs, but make the 14B-Base preference clear through the evidence
- Format: comparison table (size, training suitability, etc.) followed by narrative explaining why 14B-Base wins for this use case
- Explain the alignment tax concept for 32B-Instruct — define it, explain why Instruct models resist domain adaptation, cite the research finding. Educate the reader
- Do NOT include cost/hardware implications — keep focus on training quality, not ops concerns

### bbjllm relationship & tone
- Frame bbjllm as a "valuable first attempt" — demonstrated feasibility, produced working training infrastructure, recommended approach builds on this foundation while addressing key gaps
- Be direct and specific about the 3 blocker issues: name each one (no validation set, full-sequence loss, Instruct model choice), explain why each is a blocker, state the fix
- Include a side-by-side table: bbjllm current approach vs recommended approach (rows: Model, Training stage, Loss masking, Validation, etc.)
- Training data detail level: Claude's discretion on how deep to go on the 9,922 ChatML examples and training-data/ pipeline connection

### Evaluation methodology
- Actionable spec level: enough detail that someone could build the eval suite from this section (test set structure, pass criteria, baseline comparison protocol, reporting format)
- Cover both compile@1 (automated) and qualitative evaluation (human review for code quality, idiomatic BBj patterns, documentation quality)
- Name specific baseline models: base Qwen2.5-Coder-14B (pre fine-tune), Claude API (current production), and bbjllm's 32B output
- Include a sample eval test case showing a prompt and what pass/fail looks like with bbjcpl — make the methodology tangible

### Claude's Discretion
- Chapter structure and section ordering (not discussed — Claude determines best flow)
- Depth of training data quality/coverage assessment for bbjllm's 9,922 examples
- How to integrate the two-stage training approach (continued pretraining + instruction fine-tuning) into the chapter narrative
- Exact wording and tone transitions between sections

</decisions>

<specifics>
## Specific Ideas

- Research summary at `.planning/research/fine-tuning/SUMMARY.md` is the primary source for technical findings
- bbjllm has 3 blocker-level issues identified in research: no validation set, full-sequence loss, Instruct model choice
- Two-stage approach: continued pretraining on raw BBj corpus, then instruction fine-tuning — important for zero-representation languages
- Training data pipeline: training-data/ markdown format connects to bbjllm ChatML JSONL

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 33-fine-tuning-chapter-rewrite*
*Context gathered: 2026-02-06*
