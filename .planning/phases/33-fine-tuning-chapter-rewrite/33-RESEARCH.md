# Phase 33: Fine-Tuning Chapter Rewrite - Research

**Researched:** 2026-02-06
**Domain:** Documentation rewrite (Chapter 3 - Fine-Tuning the Model)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Model comparison framing:**
- Guided comparison: present all 3 options (7B-Base, 14B-Base, 32B-Instruct) with tradeoffs, but make the 14B-Base preference clear through the evidence
- Format: comparison table (size, training suitability, etc.) followed by narrative explaining why 14B-Base wins for this use case
- Explain the alignment tax concept for 32B-Instruct — define it, explain why Instruct models resist domain adaptation, cite the research finding. Educate the reader
- Do NOT include cost/hardware implications — keep focus on training quality, not ops concerns

**bbjllm relationship & tone:**
- Frame bbjllm as a "valuable first attempt" — demonstrated feasibility, produced working training infrastructure, recommended approach builds on this foundation while addressing key gaps
- Be direct and specific about the 3 blocker issues: name each one (no validation set, full-sequence loss, Instruct model choice), explain why each is a blocker, state the fix
- Include a side-by-side table: bbjllm current approach vs recommended approach (rows: Model, Training stage, Loss masking, Validation, etc.)
- Training data detail level: Claude's discretion on how deep to go on the 9,922 ChatML examples and training-data/ pipeline connection

**Evaluation methodology:**
- Actionable spec level: enough detail that someone could build the eval suite from this section (test set structure, pass criteria, baseline comparison protocol, reporting format)
- Cover both compile@1 (automated) and qualitative evaluation (human review for code quality, idiomatic BBj patterns, documentation quality)
- Name specific baseline models: base Qwen2.5-Coder-14B (pre fine-tune), Claude API (current production), and bbjllm's 32B output
- Include a sample eval test case showing a prompt and what pass/fail looks like with bbjcpl — make the methodology tangible

### Claude's Discretion

- Chapter structure and section ordering (not discussed -- Claude determines best flow)
- Depth of training data quality/coverage assessment for bbjllm's 9,922 examples
- How to integrate the two-stage training approach (continued pretraining + instruction fine-tuning) into the chapter narrative
- Exact wording and tone transitions between sections

### Deferred Ideas (OUT OF SCOPE)

None -- discussion stayed within phase scope.

</user_constraints>

## Summary

This phase rewrites Chapter 3 (Fine-Tuning the Model) to incorporate findings from the bbjllm repository analysis and current (2026) best practices. The current chapter is 423 lines of Markdown covering training data structure, base model selection (7B-Base), QLoRA overview, toolchain (Unsloth + llama.cpp + Ollama), hosting, and status. The rewrite must update the model recommendation to 14B-Base, add entirely new sections (bbjllm gap analysis, evaluation methodology, training data pipeline, two-stage training), update the model comparison table, and revise status/tone to match Phase 32 conventions.

The research confirms this is a substantial content rewrite, not a minor edit. Of the current chapter's 8 major sections, 6 require significant modification and 3-4 entirely new sections must be added. The existing chapter structure provides a reasonable skeleton but the ordering needs revision to accommodate the new content -- particularly the bbjllm relationship section (which has no current equivalent) and the evaluation methodology section (which is entirely new).

The primary technical source is `.planning/research/fine-tuning/SUMMARY.md`, which contains all the domain findings. This research focuses on the documentation editing task itself: what the current chapter says, what needs to change, how new sections fit, and how to structure the rewrite for maximum clarity.

**Primary recommendation:** Restructure the chapter with bbjllm gap analysis early (to establish the "why" for all changes), model selection updated next (incorporating the comparison framing decisions), two-stage training approach integrated into the existing QLoRA section, and evaluation methodology as a new major section near the end. Work in 2-3 plan waves: core content rewrite first, then new sections, then status/tone/cross-reference cleanup.

## Standard Stack

This phase involves editing a single Markdown file in a Docusaurus 3.9.2 site.

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Docusaurus | 3.9.2 | Site framework | Existing project stack |
| Markdown | N/A | Content format | Chapter 3 is `.md` (not `.mdx`) |
| `npm run build` | N/A | Build verification | Ensures no broken links or syntax |
| `bbjcpl -N` | Local install | BBj code validation | Validate any new BBj code examples |

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| Mermaid diagrams | Training pipeline visualization | Chapter already uses Mermaid for flow diagrams |

No new installations needed.

## Architecture Patterns

### File Location

```
docs/
└── 03-fine-tuning/
    └── index.md          # Chapter 3 -- the only file to edit
```

This is a single-file chapter (423 lines currently). No sub-pages or supporting assets.

### Pattern: Chapter Structure Convention

From Phase 32, the established chapter pattern is:
1. YAML front matter (sidebar_position, title, description)
2. `# Title` heading
3. `:::tip[TL;DR]` summary block
4. Intro paragraphs with cross-references to other chapters
5. Major sections with `## Heading`
6. `:::info[Decision: ...]` callouts for key choices (Choice/Rationale/Alternatives/Status)
7. `:::note[Where Things Stand]` status block near the end
8. Closing paragraph with cross-references to other chapters

### Pattern: Decision Callout Format

```markdown
:::info[Decision: Title]
**Choice:** What was decided
**Rationale:** Why
**Alternatives considered:** What else was evaluated
**Status:** Current state
:::
```

Phase 32 established that Status fields must use the correct terminology: "operational", "operational for internal exploration", "active research", "planned".

### Pattern: Status Block Convention

```markdown
:::note[Where Things Stand]
- **Operational:** Component description
- **Active research:** Component description
- **Planned:** Component description
:::
```

No dates in status blocks (v1.3 decision). Use bullet points with bold status labels.

### Pattern: Prohibited Terminology

| Prohibited | Replace With |
|------------|-------------|
| "shipped" | "operational" or "available" |
| "production" | "operational for internal exploration" or remove |
| "deployed" (as final state) | "operational for internal exploration" |
| "production-grade" | "functional" or remove |
| "production corpus" | "full documentation corpus" |

## Current Chapter Analysis: Section-by-Section

This is the core research output. It maps every section of the current chapter to its required fate (keep, modify, replace, or delete) and identifies where new sections must be inserted.

### Current Section Inventory

| # | Section | Lines | Fate | Requirement |
|---|---------|-------|------|-------------|
| 1 | YAML front matter | 1-5 | **Modify** | Update description to mention 14B-Base |
| 2 | `# Fine-Tuning the Model` | 7 | Keep | |
| 3 | `:::tip[TL;DR]` | 9-11 | **Replace** | Must mention 14B-Base, two-stage training, bbjllm context |
| 4 | Intro paragraphs | 13-16 | **Modify** | Minor updates -- still accurate conceptually |
| 5 | `## Training Data Structure` | 17-116 | **Major modify** | Update volume/status, add training-data/ pipeline, connect to bbjllm 9,922 examples |
| 6 | `## Base Model Selection` | 118-169 | **Replace** | New 3-model comparison (FT-01, FT-03, FT-09), alignment tax, guided recommendation |
| 7 | `## The QLoRA Fine-Tuning Approach` | 171-239 | **Modify** | Keep QLoRA fundamentals, integrate two-stage training (FT-07), update hyperparameters |
| 8 | `## Toolchain: Unsloth + llama.cpp + Ollama` | 241-299 | **Modify** | Update versions (FT-02), expand Unsloth description |
| 9 | `## Hosting via Ollama` | 328-407 | **Modify** | Update Ollama version, update hardware table for 14B, update status language |
| 10 | `## Current Status` | 409-421 | **Replace** | Rewrite to match Phase 32 status conventions |
| 11 | Closing paragraph | 423 | **Modify** | Update cross-references |

### New Sections Required

| New Section | Requirement | Insert After | Estimated Size |
|-------------|------------|-------------|----------------|
| **bbjllm Gap Analysis** | FT-05 | After intro, before model selection | 80-120 lines (side-by-side table, 3 blockers, tone framing) |
| **Evaluation Methodology** | FT-04 | After training approach, before toolchain | 100-150 lines (compile@1, qualitative, baselines, sample test case) |
| **Training Data Pipeline** | FT-06 | Within or after Training Data section | 40-60 lines (markdown -> ChatML, two-repo relationship) |
| **Training Workflow** | FT-08 | After toolchain, before hosting | 30-50 lines (artifact management, commit practices, iteration) |

### Estimated Total Size

Current chapter: ~423 lines. Estimated rewritten chapter: ~550-650 lines. The increase comes from the 3-4 entirely new sections, offset partially by tightening some existing sections.

## Recommended Chapter Structure

Based on the user's decisions and the content requirements, the recommended section ordering for the rewritten chapter:

```
# Fine-Tuning the Model
  :::tip[TL;DR]
  [Intro paragraphs]

## The bbjllm Foundation                              [NEW - FT-05]
  - What bbjllm built (positive framing)
  - Side-by-side table: current vs recommended
  - Three blocker issues (named, explained, fixes stated)
  - Tone: "valuable first attempt, builds foundation"

## Base Model Selection                               [REWRITTEN - FT-01, FT-03, FT-09]
  :::info[Decision: Qwen2.5-Coder-14B-Base]
  - Updated comparison table (7B-Base, 14B-Base, 32B-Instruct + Qwen3 note)
  - Alignment tax explanation for 32B-Instruct
  - Narrative: why 14B-Base wins for niche-language fine-tuning
  - No cost/hardware implications per user decision

## Training Data                                      [MODIFIED - FT-06]
  - Training data format and schema (keep existing, minor updates)
  - Training data pipeline: training-data/ markdown as canonical source
  - bbjllm's 9,922 ChatML examples as current training input
  - Conversion pipeline description (markdown -> ChatML JSONL)
  :::info[Decision: Quality-First Data Strategy]

## The QLoRA Fine-Tuning Approach                     [MODIFIED - FT-07]
  - QLoRA fundamentals (keep, still accurate)
  - Two-stage training approach integrated here
    - Stage 1: Continued pretraining (raw BBj corpus)
    - Stage 2: Instruction fine-tuning (ChatML examples)
  - Updated hyperparameters (learning rate, completion masking)
  - Catastrophic forgetting (keep, still relevant)

## Evaluation Methodology                             [NEW - FT-04]
  - compile@1 automated metric (bbjcpl-based)
  - Qualitative evaluation (human review criteria)
  - Baseline models: Qwen2.5-Coder-14B (pre-finetune), Claude API, bbjllm 32B
  - Test set structure (held-out split, category coverage)
  - Sample eval test case with pass/fail illustration
  - Reporting format

## Toolchain                                          [MODIFIED - FT-02]
  - Unsloth (updated version, new capabilities)
  - llama.cpp (GGUF conversion)
  - Ollama (updated version)
  - Version update table

## Training Workflow                                  [NEW - FT-08]
  - Artifact management (what to save, Git LFS)
  - What to commit back to repo
  - Iterative improvement process

## Hosting via Ollama                                 [MODIFIED]
  - Updated version (0.15.x)
  - Updated hardware table for 14B model
  - Self-hosting rationale (keep, still valid)
  - API compatibility (keep, still valid)
  - Deployment architecture (keep with minor updates)
  - MCP integration (keep with status updates)

## Current Status                                     [REPLACED]
  :::note[Where Things Stand]
  [Closing paragraph]
```

### Rationale for This Ordering

1. **bbjllm first** -- Establishes the "why" for everything that follows. The reader immediately understands there is existing work, it has known issues, and the chapter presents the improved approach. This also satisfies the user's "valuable first attempt" framing.

2. **Model selection second** -- Now the reader has context for why we are recommending 14B-Base instead of 32B-Instruct. The alignment tax explanation makes sense because we just described bbjllm using Instruct. The comparison table is more meaningful with the gap analysis as context.

3. **Training data third** -- Flows naturally from model selection. We have selected the model; now what do we train it on? This is where the training-data/ pipeline and bbjllm's 9,922 examples get connected.

4. **QLoRA + two-stage fourth** -- The training methodology. We have the model and the data; now how do we train? Two-stage training is integrated here rather than being a separate section because it is the training approach, not a separate concept.

5. **Evaluation fifth** -- After describing the training, describe how to measure success. This position makes logical sense: train, then evaluate. The sample test case gives the reader a concrete picture.

6. **Toolchain and workflow sixth** -- Practical implementation details. By this point the reader understands what and why; these sections cover how.

7. **Hosting last** -- Deployment comes after everything else. This section is largely unchanged.

## Detailed Change Analysis

### Section: TL;DR Block

**Current:** References "Qwen2.5-Coder-7B", "single $1,500 GPU", Ollama for local inference.

**Required changes:**
- Update model to "Qwen2.5-Coder-14B-Base"
- Mention two-stage training approach
- Reference bbjllm as existing implementation that informs the recommendation
- Mention evaluation via bbjcpl
- Remove the "$1,500 GPU" detail (user decided: no cost/hardware implications in model section -- apply consistently)
- Keep the core message about self-hosted inference via Ollama

### Section: Base Model Selection (Major Rewrite)

**Current (lines 118-169):** Single decision callout for 7B-Base. Comparison table with 6 models (Qwen 7B/14B/32B, CodeLlama, StarCoder2, DeepSeek-V3). Narrative focused on 7B rationale. "A Note on Newer Models" subsection about Qwen3-Coder.

**Required changes (FT-01, FT-03, FT-09):**

1. **New decision callout:** Change from "Qwen2.5-Coder-7B-Base as Starting Point" to "Qwen2.5-Coder-14B-Base as Primary Recommendation" with updated rationale citing research findings.

2. **New comparison table format (per user decision):** Three focused rows:
   - 7B-Base: smallest, single GPU, good for experimentation, but less improvement from fine-tuning
   - 14B-Base (recommended): best fine-tuning improvement per Qwen technical report, still trainable on single 24GB GPU, Base variant for two-stage training
   - 32B-Instruct: highest base quality but alignment tax makes fine-tuning counterproductive

   Columns should focus on training suitability, NOT cost/hardware: model size, fine-tuning improvement potential, Base/Instruct suitability, alignment tax risk.

3. **Alignment tax explanation (new subsection):** Define alignment tax. Explain that Instruct models have already been trained to follow instructions; fine-tuning them on domain data overwrites both domain knowledge AND instruction-following simultaneously. Cite Shadow-FT research (ICLR 2025). Explain why this matters specifically for BBj (model may learn syntax but degrade response quality).

4. **Qwen3 update:** Keep the Qwen3-Coder note but update: confirm MoE-only (no dense variants), mention Qwen3 dense models exist but have not been evaluated for BBj fine-tuning yet.

5. **Landscape table update (FT-09):** Add Qwen3 dense models to the comparison, update notes on CodeLlama/StarCoder2 as superseded.

### Section: Training Data Structure (Moderate Modification)

**Current (lines 17-116):** Covers JSON format, generation labels, example types, BBj code sample, volume targets, quality-first decision callout.

**Required changes (FT-06):**

1. **Format discrepancy:** The current chapter describes a JSON format with fields like `id`, `type`, `generation`, `instruction`, `input`, `output`. But the actual training-data/ repo uses Markdown with YAML front matter (see `training-data/FORMAT.md`). And bbjllm uses ChatML JSONL format. The chapter must acknowledge all three formats:
   - training-data/ Markdown with YAML front matter (canonical source for new examples -- 2 seed examples, 7 topic directories)
   - bbjllm ChatML JSONL (current training input -- 9,922 examples)
   - The JSON format currently shown in the chapter (original design, not yet used in practice)

   **Recommendation:** Update the format section to show the training-data/ Markdown format as primary (this is what contributors use), explain the conversion to ChatML JSONL for training, and note the bbjllm dataset as the existing training corpus.

2. **Volume/status update:** Change "10,000 to 50,000 targets" to reflect reality: bbjllm has 9,922 ChatML examples, training-data/ repo has 2 seed examples. Update the decision callout Status field.

3. **Training data pipeline (FT-06 new subsection):** Describe the two-repo relationship:
   - `training-data/` in this repo: Markdown format, human-readable, validated against JSON Schema, canonical for new contributions
   - `bbjllm/` (separate repo): ChatML JSONL, 9,922 examples created independently
   - Planned conversion pipeline: `training-data/` Markdown -> ChatML JSONL for training input
   - Acknowledge the disconnect: bbjllm's 9,922 examples were created independently, not converted from training-data/ format

4. **Data quality note:** Surface the research finding about bbjllm dataset issues (375 duplicates, 60 corrupted newlines, inconsistent formatting) at appropriate depth -- Claude's discretion per user decision, but the issues should be mentioned since they inform the "recommended fixes" narrative.

### Section: QLoRA Fine-Tuning (Moderate Modification)

**Current (lines 171-239):** How LoRA works, QLoRA overview, hardware comparison table, hyperparameters table, sequential fine-tuning (already describes two-stage!), catastrophic forgetting.

**Key finding:** The current chapter ALREADY describes two-stage training (lines 208-229) with a Mermaid diagram. The concepts are sound. What needs to change:

1. **Integrate with bbjllm context:** The two-stage description is currently generic. Update to reference the specific recommendation: Stage 1 on raw BBj source code (which bbjllm skipped), Stage 2 on the 9,922 ChatML examples (which bbjllm did). Make it clear why Stage 1 matters for zero-representation languages.

2. **Update hyperparameters table:** Current learning rate "2e-4 to 5e-5" is fine for the recommendation (it is the correct range). But add a note about the bbjllm script using 2e-5 (10x lower than QLoRA recommendations) and why this is problematic.

3. **Add completion masking note:** Explain that training should compute loss only on assistant responses, not system/user tokens. This is one of the 3 blocker issues from bbjllm.

4. **Update model references:** Change "7B" to "14B" throughout.

5. **Update the Mermaid diagram:** Change "Qwen2.5-Coder-7B" to "Qwen2.5-Coder-14B-Base".

### Section: Toolchain (Moderate Modification)

**Current (lines 241-299):** Unsloth description, llama.cpp conversion, quantization table, Ollama Modelfile.

**Required changes (FT-02):**

1. **Unsloth update:** Current describes "2x training speed" and "70% less VRAM". Update to mention version 2026.1.4, Dynamic 4-bit Quantization (better accuracy for critical parameters), 500K context support, built-in GGUF export (may eliminate llama.cpp step).

2. **Version table (new):** Add a version comparison table:
   | Library | bbjllm Version | Current Version | Key Changes |
   | transformers | 4.44.0 | 5.1.0 | Major v5 release |
   | peft | 0.12.0 | 0.18.1 | 6 minor versions |
   | bitsandbytes | 0.43.0 | 0.49.1 | Critical QLoRA memory bug fix |
   | trl | (not used) | 0.27.x | SFTTrainer with completion masking |

3. **Quantization table:** Update for 14B model sizes (Q4_K_M ~8.5GB, not ~4GB).

4. **Modelfile:** Update to reference `bbj-coder-14b-q4_k_m.gguf` instead of `bbj-coder-7b-q4_k_m.gguf`.

### Section: Hosting via Ollama (Minor Modification)

**Current (lines 328-407):** Self-hosting rationale, hardware requirements, API compatibility, deployment diagram, MCP integration.

**Required changes:**

1. **Version:** Update "v0.9.x+" to "v0.15.x" throughout.
2. **Hardware table:** Update for 14B model. Current lists 7B Q4_0 at ~4GB; 14B Q4_K_M is ~8.5GB.
3. **API compatibility paragraph:** The claim about "Anthropic-format requests" as of Ollama v0.9.x should be verified or softened.
4. **MCP integration:** Update to reflect that generate_bbj_code is planned, not operational. The current text at line 403 says "consumed through the BBj MCP server's generate_bbj_code tool" without clarifying that this tool does not yet exist. Add status clarity.
5. **Decision callout Status:** Update to current state.
6. **Tone:** Apply Phase 32 terminology conventions.

### Section: Current Status (Full Replace)

**Current (lines 409-421):** Uses "approximately 10,000", "promising results", "operational, not speculative", "validated through active use".

**Required replacement:** Follow Phase 32 conventions exactly:
- **Active research:** bbjllm experiment (9,922 ChatML examples on Qwen2.5-Coder-32B-Instruct via QLoRA/PEFT); research recommends Qwen2.5-Coder-14B-Base with two-stage training approach
- **Operational:** Training data repository (2 seed examples, 7 topic directories, JSON Schema validation, contributor guides)
- **Operational:** Toolchain components (Unsloth, llama.cpp, Ollama) are publicly available and actively maintained
- **Planned:** Evaluation suite using bbjcpl-based compile@1 metric
- **Planned:** Training data conversion pipeline (training-data/ Markdown to ChatML JSONL)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| BBj code example validation | Manual syntax review | `bbjcpl -N` on all code blocks | Ground truth; any new BBj code must compile |
| Build verification | Visual inspection | `npm run build` | Catches broken links, Mermaid syntax, malformed admonitions |
| Finding all status references | Manual reading | Grep for "shipped", "production", "in progress", "planned" | Ensures no stale terminology survives |
| Cross-reference consistency | Manual checking | Grep for "/docs/fine-tuning" across all chapters | Ensures other chapters' links still work |

**Key insight:** Chapter 3 is a single Markdown file. The complexity is in content accuracy, not tooling.

## Common Pitfalls

### Pitfall 1: Inconsistency Between New and Retained Content

**What goes wrong:** New sections (bbjllm gap analysis, evaluation methodology) are written with current facts, but retained sections (training data, hosting) still reference 7B model, old Ollama version, or outdated status.
**Why it happens:** Retained sections look "done" and get skimmed during review.
**How to avoid:** After writing all new content, do a full-file pass specifically for: model name/size references, version numbers, and status language. Grep for "7B", "v0.9", "shipped", "production", "in progress".
**Warning signs:** Mixed references to "7B" and "14B" in the same chapter.

### Pitfall 2: Over-Technical Gap Analysis That Sounds Adversarial

**What goes wrong:** The bbjllm section reads like a bug report rather than a constructive assessment. The three blocker issues are presented as failures rather than improvement opportunities.
**Why it happens:** The research summary is analytical and direct; copying its tone into user-facing documentation can sound harsh.
**How to avoid:** Lead with what bbjllm accomplished (working QLoRA pipeline, 9,922 curated examples, proved feasibility). Then frame issues as "gaps the recommended approach addresses" rather than "problems to fix". Use the user's framing: "valuable first attempt" that "builds foundation".
**Warning signs:** Words like "critical flaw", "fundamentally broken", "must be fixed" in the chapter text.

### Pitfall 3: Evaluation Section Too Abstract

**What goes wrong:** The evaluation methodology section describes metrics and processes but doesn't include the tangible sample test case the user explicitly requested.
**Why it happens:** Writing a concrete eval example requires inventing a BBj prompt, a model response, and showing what bbjcpl would say -- more work than writing abstract methodology.
**How to avoid:** Draft the sample eval test case FIRST, then write the surrounding methodology. The concrete example anchors the section and makes the abstract concepts real.
**Warning signs:** The section talks about "what compile@1 measures" without showing a single example of a test case being evaluated.

### Pitfall 4: Alignment Tax Section Too Academic

**What goes wrong:** The alignment tax explanation reads like a research paper summary rather than a practical decision aid. The reader cannot connect it to their BBj fine-tuning choice.
**Why it happens:** The concept is from academic research (Shadow-FT, ICLR 2025) and it is tempting to reproduce the academic framing.
**How to avoid:** Start with the practical consequence ("Fine-tuning an Instruct model on BBj data risks degrading its ability to follow instructions -- the very capability that makes it useful"). Then explain the mechanism. Then cite the research. Always connect back to "this is why we recommend Base, not Instruct."
**Warning signs:** Paragraphs of explanation before the reader understands why they should care.

### Pitfall 5: Training Data Format Confusion

**What goes wrong:** The chapter shows three different data formats (JSON from current docs, Markdown from training-data/, ChatML JSONL from bbjllm) without clearly explaining which one the reader should use and how they relate.
**Why it happens:** Three formats genuinely exist and the relationship is not straightforward.
**How to avoid:** State clearly upfront: "Contributors create examples in Markdown format (training-data/ repository). A conversion pipeline transforms these into ChatML JSONL for training. The bbjllm repository contains 9,922 examples already in ChatML JSONL format, created independently." Show the flow: Markdown (author) -> ChatML JSONL (train) -> GGUF (deploy).
**Warning signs:** The reader cannot answer "If I want to add a training example, what format do I use and where do I put it?"

### Pitfall 6: Breaking Cross-References from Other Chapters

**What goes wrong:** Restructuring sections changes anchor headings, breaking links from Chapters 2, 4, 5, and 7 that reference `#why-qwen25-coder`, `#the-qlora-fine-tuning-approach`, etc.
**Why it happens:** Other chapters link to specific section anchors in Chapter 3.
**How to avoid:** Before restructuring, inventory all incoming links. After restructuring, verify they still resolve. Docusaurus auto-generates anchors from headings; changing a heading changes the anchor.
**Warning signs:** `npm run build` reports broken links.

### Pitfall 7: Scope Creep Into Implementation Changes

**What goes wrong:** The implementer starts fixing things beyond documentation -- updating the bbjllm training script, modifying the training-data/ schema, or creating the conversion pipeline.
**Why it happens:** The research summary describes concrete code fixes, making it tempting to implement them.
**How to avoid:** This phase is documentation only. The chapter should DESCRIBE the recommended approach but not implement it. Any code changes are out of scope (explicitly listed in REQUIREMENTS.md "Out of Scope").
**Warning signs:** Editing files outside `docs/03-fine-tuning/index.md`.

## Cross-Reference Inventory

Other chapters that reference Chapter 3 content (these links must be verified after the rewrite):

### Incoming Links to Chapter 3

| Source | Link Target | Context |
|--------|------------|---------|
| Chapter 2 (line 98) | `/docs/fine-tuning` | "the current recommendation is Qwen2.5-Coder-7B" -- **WILL BECOME STALE** (Phase 36 CONS-01 handles this) |
| Chapter 2 (line 112) | `/docs/fine-tuning` | "Chapter 3 covers base model selection..." |
| Chapter 2 (line 372) | `/docs/fine-tuning` | Status table link |
| Chapter 4 (line 13) | `/docs/fine-tuning` | "Chapter 3 describes how to build a BBj-aware language model" |
| Chapter 4 heading | `#why-qwen25-coder` | Section anchor reference -- **AT RISK if heading changes** |
| Chapter 7 (line 75) | `/docs/fine-tuning#why-qwen25-coder` | Direct section anchor -- **AT RISK** |
| Chapter 7 (multiple) | Various | Multiple references to fine-tuning status |

**Important:** Phase 36 (Cross-Chapter Consistency) handles updating references in other chapters. Phase 33 should NOT edit other chapter files. But Phase 33 MUST be aware of incoming anchors and try to preserve them or create redirect-compatible headings.

### Anchor Preservation Strategy

Current anchors that other chapters link to:
- `#why-qwen25-coder` -- If this heading survives (even modified), the anchor works
- `#the-qlora-fine-tuning-approach` -- Should survive as the section is modified, not removed
- No other specific anchor links found

**Recommendation:** Keep the `## Why Qwen2.5-Coder` subsection heading (even if the content changes significantly) to preserve the `#why-qwen25-coder` anchor. Or if the heading must change, note the broken anchor for Phase 36.

## Requirement Coverage Map

How each FT requirement maps to chapter sections:

| Req | Description | Target Section | Type |
|-----|-------------|---------------|------|
| FT-01 | 14B-Base recommendation | Base Model Selection | Rewrite |
| FT-02 | Toolchain version updates | Toolchain section + version table | Modify |
| FT-03 | Base vs Instruct analysis | Base Model Selection (alignment tax subsection) | New content |
| FT-04 | Evaluation methodology | Evaluation Methodology | New section |
| FT-05 | bbjllm relationship | The bbjllm Foundation | New section |
| FT-06 | Training data pipeline | Training Data (pipeline subsection) | New content |
| FT-07 | Two-stage training | QLoRA section (integrated) | Modify existing |
| FT-08 | Training workflow | Training Workflow | New section |
| FT-09 | Model comparison table | Base Model Selection | Rewrite |

## Plan Wave Recommendation

Given the scope (6 modified sections + 3-4 new sections), recommend splitting into 2-3 plan waves:

### Option A: Two Waves (Recommended)

**Wave 1: Core content rewrite (larger)**
- Rewrite TL;DR
- New bbjllm Foundation section (FT-05)
- Rewrite Base Model Selection (FT-01, FT-03, FT-09)
- Modify Training Data section + pipeline subsection (FT-06)
- Modify QLoRA section with two-stage integration (FT-07)
- New Evaluation Methodology section (FT-04)

**Wave 2: Supporting updates + status**
- Update Toolchain versions (FT-02)
- New Training Workflow section (FT-08)
- Update Hosting via Ollama (version, hardware table, status)
- Replace Current Status block
- Full-file tone pass (prohibited terminology)
- Build verification + anchor check

**Rationale for two waves:** Wave 1 does all the intellectually demanding content work. Wave 2 does mechanical updates and verification. This keeps plan sizes manageable (~250-350 lines of task specification each).

### Option B: Three Waves

Split Wave 1 into: (a) bbjllm + model selection, (b) training data + QLoRA + evaluation. More granular but more overhead.

**Recommendation:** Option A (two waves). The content in Wave 1 is thematically connected -- bbjllm context informs model selection, which informs training approach, which informs evaluation. Writing them together ensures consistency.

## Content Sources for the Planner

The planner should reference these sources for factual content:

| Content Need | Source | Location |
|--------------|--------|----------|
| Technical findings (all) | Research summary | `.planning/research/fine-tuning/SUMMARY.md` |
| bbjllm gap analysis details | Research summary | SUMMARY.md "Gap Analysis" section |
| 3 blocker issues | Research summary | SUMMARY.md "Critical Pitfalls" section |
| Model recommendation rationale | Research summary | SUMMARY.md "Recommended Stack" section |
| Version numbers | Research summary | SUMMARY.md "Critical version updates" |
| Evaluation methodology | Research summary | SUMMARY.md "Expected Features" section |
| Training-data/ format | Format spec | `training-data/FORMAT.md` |
| Training-data/ example | Seed example | `training-data/gui/hello-window.md` |
| Phase 32 tone conventions | Phase 32 research | `.planning/phases/32-multi-chapter-status-tone-update/32-RESEARCH.md` |
| Terminology rules | Phase 32 research | 32-RESEARCH.md "Prohibited and Required Terminology" |
| Cross-chapter status | Chapter 2 (updated) | `docs/02-strategic-architecture/index.md` |

## Open Questions

1. **Should the original JSON format examples be kept or removed?**
   - What we know: The current chapter shows JSON training examples (lines 25-47). The actual training-data/ repo uses Markdown with YAML front matter. bbjllm uses ChatML JSONL.
   - What's unclear: Whether the JSON format was ever used or is purely aspirational.
   - Recommendation: Replace with the actual Markdown format from training-data/ repo. Show the real format, not a theoretical one. Include a note about conversion to ChatML JSONL.

2. **How deep to go on bbjllm dataset quality issues?**
   - What we know: 375 duplicates, 60 corrupted newlines, inconsistent formatting (research finding).
   - What's unclear: User said "Claude's discretion" on training data detail depth.
   - Recommendation: Mention the issues at a summary level (one paragraph noting duplicates and formatting inconsistencies as areas for improvement). Do not reproduce the full statistical breakdown from the research summary. The gap analysis table (bbjllm current vs recommended) naturally surfaces these issues without belaboring them.

3. **Should the BBj code sample (lines 73-93) be kept?**
   - What we know: The "Modern BBj Event Handler" code block is a valid BBj example showing what the model learns.
   - What's unclear: Whether it still serves the narrative in the restructured chapter.
   - Recommendation: Keep it. It is a useful illustration of what correct BBj code looks like, and it helps non-BBj readers understand the domain. Verify with `bbjcpl -N` to ensure it still compiles.

4. **Exact heading for the bbjllm section?**
   - Options: "The bbjllm Foundation", "Current Implementation: bbjllm", "Building on bbjllm", "What Exists: The bbjllm Experiment"
   - Recommendation: "The bbjllm Foundation" -- positive framing that positions it as the base we build on, matching the "valuable first attempt" tone.

## Sources

### Primary (HIGH confidence)

- Direct file inspection: `docs/03-fine-tuning/index.md` -- current chapter content (423 lines), all sections inventoried
- Direct file inspection: `.planning/research/fine-tuning/SUMMARY.md` -- technical findings source (293 lines)
- Direct file inspection: `training-data/FORMAT.md` -- actual training data format specification
- Direct file inspection: `training-data/gui/hello-window.md` -- example training data file
- Direct file inspection: `training-data/README.md` -- training data repository overview
- Direct file inspection: `.planning/REQUIREMENTS.md` -- FT-01 through FT-09 requirements
- Direct file inspection: `.planning/phases/32-multi-chapter-status-tone-update/32-RESEARCH.md` -- Phase 32 conventions
- Direct file inspection: `.planning/phases/32-multi-chapter-status-tone-update/32-01-PLAN.md` -- Phase 32 plan structure pattern
- Direct file inspection: `docs/02-strategic-architecture/index.md` -- cross-references to Chapter 3
- Direct file inspection: `docs/04-ide-integration/index.md` -- cross-references to Chapter 3
- Direct file inspection: `.planning/phases/33-fine-tuning-chapter-rewrite/33-CONTEXT.md` -- user decisions

### Secondary (MEDIUM confidence)

- Grep results across docs/ directory -- all cross-reference instances to fine-tuning/Chapter 3 catalogued

### Tertiary (LOW confidence)

- None

## Metadata

**Confidence breakdown:**
- Current chapter analysis: HIGH -- direct file inspection of every section
- Required changes: HIGH -- mapped to explicit requirements (FT-01 through FT-09) and user decisions
- Recommended structure: HIGH -- informed by content analysis and user decisions
- Cross-reference inventory: HIGH -- grep-verified across all chapter files
- Plan wave recommendation: MEDIUM -- editorial judgment on optimal split; either 2 or 3 waves would work

**Research date:** 2026-02-06
**Valid until:** 2026-03-06 (documentation editing task; findings stable unless chapter files change)
