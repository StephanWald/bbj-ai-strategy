# Phase 33 Plan 01: Core Content Rewrite Summary

---
phase: 33
plan: 01
subsystem: documentation
tags: [fine-tuning, chapter-3, bbjllm, model-selection, evaluation, training-data, qlora]

dependency-graph:
  requires: [phase-32]
  provides: [ch3-core-content-rewrite, bbjllm-gap-analysis, evaluation-methodology, 14b-base-recommendation]
  affects: [33-02, phase-36]

tech-stack:
  added: []
  patterns: [bbjllm-constructive-framing, alignment-tax-analysis, compile-at-1-metric, two-stage-training]

file-tracking:
  key-files:
    created: []
    modified: [docs/03-fine-tuning/index.md]

decisions:
  - id: FT-01
    choice: "Qwen2.5-Coder-14B-Base as primary recommendation"
    rationale: "Greater fine-tuning improvement than 7B per Qwen technical report; Base variant avoids alignment tax"
  - id: FT-03
    choice: "Base variant over Instruct for domain fine-tuning"
    rationale: "Alignment tax causes performance degeneration when fine-tuning Instruct models on domain data (Shadow-FT, ICLR 2025)"
  - id: FT-04
    choice: "bbjcpl-based compile@1 as primary automated metric"
    rationale: "BBj compiler provides ground-truth syntax validation; binary, deterministic, non-gameable"
  - id: FT-05
    choice: "Constructive framing of bbjllm as 'valuable first attempt'"
    rationale: "User decision; names 3 blockers directly while acknowledging accomplishments"
  - id: FT-06
    choice: "Two-repo training data pipeline with planned conversion"
    rationale: "training-data/ Markdown as canonical contributor format; bbjllm ChatML JSONL as training input; conversion pipeline planned"

metrics:
  duration: 17min
  completed: 2026-02-06
---

**One-liner:** Rewrote Chapter 3 core content with bbjllm gap analysis, 14B-Base recommendation with alignment tax rationale, two-stage QLoRA training, training data pipeline connecting two repos, and bbjcpl-based evaluation methodology with compile@1 metric and sample test case.

## What Was Done

### Task 1: Replace TL;DR, add bbjllm Foundation section, rewrite Base Model Selection
- Replaced TL;DR to reference 14B-Base, two-stage training, bbjllm context, bbjcpl evaluation, and Ollama
- Updated intro paragraphs to preview the new chapter structure
- Added new "The bbjllm Foundation" section (~40 lines) with:
  - Constructive "valuable first attempt" framing
  - Side-by-side comparison table (9 rows: Model, Model variant, Training stages, Loss computation, Validation, Learning rate, Library stack, Evaluation, Artifact management)
  - Three named blocker issues with explanations and fixes
- Rewrote "Base Model Selection" with:
  - New decision callout for 14B-Base with "Active research" status
  - Preserved `### Why Qwen2.5-Coder` heading (anchor intact)
  - Training suitability comparison table (3 rows: 7B-Base, 14B-Base, 32B-Instruct)
  - New "The Alignment Tax" subsection with Shadow-FT citation
  - Updated landscape comparison: added Qwen3 dense, marked CodeLlama/StarCoder2 as superseded, removed DeepSeek-V3
- Reordered sections to: bbjllm Foundation -> Base Model Selection -> Training Data -> QLoRA
- Relocated and updated Training Data section with Markdown format from training-data/ repo, pipeline description, and volume/status updates

### Task 2: Modify QLoRA section, add Evaluation Methodology
- Updated QLoRA opening to reference 14B parameter model
- Updated VRAM comparison table for 14B (16-20 GB for QLoRA)
- Added completion masking row to hyperparameters table
- Added learning rate note about bbjllm's 2e-5 being 5-10x below QLoRA recommendations
- Added completion masking guidance with TRL SFTTrainer reference
- Renamed "Sequential Fine-Tuning" to "Two-Stage Training Approach"
- Updated Mermaid diagram: 14B-Base, ChatML examples, bbjcpl compile@1
- Added bbjllm context: skipped Stage 1, zero-representation language rationale
- Added new "Evaluation Methodology" section (~120 lines) with:
  - compile@1 automated metric definition and process
  - Qualitative evaluation criteria (code quality, idiomatic patterns, documentation quality)
  - Three named baselines (14B-Base unmodified, Claude API, bbjllm 32B)
  - Test set structure (held-out split, category coverage, size, difficulty distribution)
  - Concrete sample eval test case with PASS and FAIL examples using bbjcpl
  - Standardized reporting format table

## Requirements Coverage

| Requirement | Description | Status |
|-------------|-------------|--------|
| FT-01 | 14B-Base recommendation | Covered -- decision callout, comparison table, narrative |
| FT-03 | Base vs Instruct analysis | Covered -- alignment tax subsection with Shadow-FT citation |
| FT-04 | Evaluation methodology | Covered -- new section with compile@1, baselines, sample test case |
| FT-05 | bbjllm relationship | Covered -- new Foundation section with side-by-side table and 3 blockers |
| FT-06 | Training data pipeline | Covered -- pipeline subsection with two-repo description and Mermaid flow |
| FT-07 | Two-stage training | Covered -- integrated into QLoRA section with bbjllm context |
| FT-09 | Model comparison table | Covered -- training suitability table + landscape comparison |

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Replace TL;DR, add bbjllm Foundation, rewrite Base Model Selection | 5f8500d | docs/03-fine-tuning/index.md |
| 2 | Modify QLoRA section, add Evaluation Methodology | b246eb9 | docs/03-fine-tuning/index.md |

## Decisions Made

1. **Section ordering:** bbjllm Foundation -> Base Model Selection -> Training Data -> QLoRA -> Evaluation. This follows the research recommendation where bbjllm context informs model selection, which informs training approach, which informs evaluation.

2. **Training data format example:** Used the actual `training-data/gui/hello-window.md` file as the canonical format example (4-backtick fenced to handle nested code blocks), replacing the theoretical JSON format that was never used in practice.

3. **bbjllm tone:** Maintained constructive framing throughout. Used "gaps the recommended approach addresses" rather than "critical flaws." Named all three blockers directly with explanations and fixes per user decision.

4. **Evaluation test case:** Used realistic BBj code for both PASS and FAIL examples. FAIL example shows `.addEventListener()` and `alert()` (JavaScript patterns) -- exactly the kind of fabrication generic LLMs produce for BBj.

5. **Alignment tax section:** Led with practical consequence, then mechanism, then research citation, then BBj connection -- following the research pitfall guidance to avoid starting too academic.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

- `npm run build`: PASSED (no errors)
- `### Why Qwen2.5-Coder` anchor: PRESERVED (line 71)
- `## The QLoRA Fine-Tuning Approach` anchor: PRESERVED (line 269)
- Prohibited terminology ("shipped", "production-grade"): NONE found
- Toolchain section onwards: UNTOUCHED (left for 33-02)
- compile@1 metric: appears 11 times across evaluation and related sections
- "alignment tax" concept: appears in bbjllm blocker #3, decision callout, and dedicated subsection
- Chapter line count: 423 -> 653 lines (230 lines added, net)

## Next Phase Readiness

Plan 33-02 should address:
- Toolchain section: update versions (Unsloth 2026.1.4, Ollama 0.15.x), add version comparison table
- Hosting section: update Ollama version, hardware table for 14B, MCP integration status clarity
- Current Status block: replace with Phase 32 conventions
- Mermaid diagrams in Toolchain: still reference "7B" and "JSON examples"
- Modelfile: still references `bbj-coder-7b-q4_k_m.gguf`
- Quantization table: sizes still for 7B model
- Full-file tone pass for any remaining prohibited terminology

## Self-Check: PASSED
