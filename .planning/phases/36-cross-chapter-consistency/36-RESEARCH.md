# Phase 36: Cross-Chapter Consistency Pass - Research

**Researched:** 2026-02-06
**Domain:** Content consistency audit across 7-chapter documentation site -- model names, MCP tool status, training data counts, cross-references, and BBj code compilation
**Confidence:** HIGH

## Summary

Phase 36 is the final phase of v1.7 (Documentation Refresh & Fine-Tuning Strategy). Its purpose is to ensure that a reader moving between any two chapters encounters no contradictions in model names, tool status, training data counts, or cross-reference descriptions. Phases 32-35 updated chapters individually, and several cross-chapter references are now stale.

Direct examination of all 7 chapter files plus the landing page (`src/pages/index.tsx`) reveals **12 specific inconsistencies** that need correction. The issues fall into four categories: (1) model name/size contradictions (Chapter 2 still references Qwen2.5-Coder-7B in two places; Chapter 1 Decision callout still says "base model evaluation underway"; Chapter 5 references "the 7B model"), (2) status terminology inconsistency (Chapter 1 uses "Under investigation" instead of Phase 32 conventions), (3) four stale cross-references to Chapter 7 that describe content Ch7 no longer contains (already identified by Phase 35), and (4) the landing page description for Chapter 7 which is outdated.

The site currently builds with zero content warnings (`npm run build` clean). The BBj compiler (`bbjcpl`) is NOT available on the development machine, which affects CONS-04 validation. No BBj code blocks were modified during Phases 32-35 (all content changes were to prose sections, not code blocks), so the risk of broken code samples is minimal.

**Primary recommendation:** Execute as a single plan with two tasks: Task 1 audits and fixes all text-based consistency issues (CONS-01, CONS-02, CONS-03 plus stale cross-references and landing page). Task 2 verifies BBj code blocks compile (CONS-04) and runs the final build gate. For CONS-04, since `bbjcpl` is not locally installed, flag this for user decision on validation approach (the code blocks were not modified in v1.7, reducing risk).

## Standard Stack

This phase is a content audit and text correction pass. No libraries or tools are installed.

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| `npm run build` | Docusaurus 3.9.2 | Zero-warnings build gate | `onBrokenLinks: 'throw'` catches broken links automatically |
| `grep`/search tools | N/A | Pattern scanning across 7 chapters | Finding all instances of model names, tool names, counts |
| Text editor | N/A | Direct file editing | All fixes are text replacements in markdown files |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `bbjcpl -N` | BBj installation required | BBj code compilation validation | CONS-04: NOT available on dev machine |
| `github-slugger` | bundled with Docusaurus | Anchor slug verification | Only if new cross-references are created |

## Architecture Patterns

### File Inventory

```
docs/
  01-bbj-challenge/index.mdx       (326 lines, .mdx)
  02-strategic-architecture/index.md (389 lines)
  03-fine-tuning/index.md           (703 lines)
  04-ide-integration/index.md       (674 lines)
  05-documentation-chat/index.md    (309 lines)
  06-rag-database/index.md          (538 lines)
  07-implementation-roadmap/index.md (136 lines)
src/pages/index.tsx                 (230 lines, landing page)
```

### Pattern 1: Authoritative Source for Each Consistency Domain

Each consistency requirement has a single authoritative source:

| Domain | Authoritative Source | What It Says |
|--------|---------------------|--------------|
| Model name/size (CONS-01) | Chapter 3 (fine-tuning) | Qwen2.5-Coder-14B-Base as primary recommendation; bbjllm used 32B-Instruct |
| MCP tool names/status (CONS-02) | Chapter 2 (strategic architecture) | search_bbj_knowledge (operational), validate_bbj_syntax (operational), generate_bbj_code (planned) |
| Training data counts (CONS-03) | Chapter 3 (fine-tuning) | 9,922 ChatML examples in bbjllm; 2 seed examples in training-data/ |
| Status terminology | Phase 32 decisions | operational / operational for internal exploration / active research / planned |
| Chapter 7 content | Chapter 7 (implementation roadmap) | Progress summary + forward plan (no timelines, phases, resources, risks, metrics) |

### Pattern 2: Fix-in-Place (No Structural Changes)

All fixes are text replacements within existing prose. No sections are added, removed, or restructured. This keeps the scope tight and avoids cascading changes.

### Anti-Patterns to Avoid

- **Rewriting sections during a consistency pass:** This phase fixes factual inconsistencies only. Do not improve prose, restructure paragraphs, or add new content.
- **Changing the authoritative chapters (Ch3, Ch2, Ch7):** These were updated in their dedicated phases (33, 32, 35). Only update OTHER chapters to match them.
- **Modifying BBj code blocks:** No code blocks should be changed. The audit verifies they still compile, not that they should be rewritten.

## Consistency Audit: Complete Findings

### CONS-01: Model Name/Size Consistency

**Authoritative:** Chapter 3 -- Qwen2.5-Coder-14B-Base as primary recommendation; bbjllm experiment used 32B-Instruct.

| Chapter | Line | Current Text | Issue | Fix |
|---------|------|-------------|-------|-----|
| Ch2 | 98 | "the current recommendation is [Qwen2.5-Coder-7B](...)" | **Wrong model size.** Should be 14B-Base per Phase 33. | Update to "Qwen2.5-Coder-14B-Base" |
| Ch2 | 184 | "fine-tuned model (Qwen2.5-Coder-7B via Ollama)" | **Wrong model size.** Should be 14B. | Update to "Qwen2.5-Coder-14B-Base via Ollama" |
| Ch1 | 274 | "**Status:** Training data structure defined; base model evaluation underway." | **Stale status.** Base model has been selected (14B-Base recommended). | Update to reflect 14B-Base recommendation and bbjllm experiment |
| Ch5 | 173 | "For the 7B model with a 4096-token context" | **Wrong model size.** Should reference 14B model. Context window also changes (14B supports larger context). | Update to "For the 14B model" and adjust context window reference |

**Chapters already consistent:** Ch3 (authoritative), Ch4 (references 14B correctly), Ch7 (references 14B-Base correctly).

### CONS-02: MCP Tool Names and Status

**Authoritative:** Chapter 2 -- search_bbj_knowledge (operational), validate_bbj_syntax (operational), generate_bbj_code (planned).

All chapters that reference MCP tools (Ch2, Ch3, Ch4, Ch5, Ch6, Ch7) use consistent tool names. The three tool names are identical everywhere: `search_bbj_knowledge`, `generate_bbj_code`, `validate_bbj_syntax`.

Status descriptions are also consistent across chapters:
- search_bbj_knowledge: described as operational everywhere
- validate_bbj_syntax: described as operational everywhere
- generate_bbj_code: described as planned everywhere

**No fixes needed for CONS-02.** MCP tool consistency is already correct.

### CONS-03: Training Data Counts

**Authoritative:** Chapter 3 -- 9,922 ChatML examples in bbjllm; 2 seed examples in training-data/.

| Chapter | Line | Current Text | Status |
|---------|------|-------------|--------|
| Ch1 | 319 | "9,922 training examples" | Correct |
| Ch2 | 372 | "9,922 ChatML examples" | Correct |
| Ch2 | 386 | "2 seed examples, 7 topic directories" | Correct |
| Ch3 | 26 | "9,922 curated ChatML examples" | Correct (authoritative) |
| Ch3 | 228 | "2 seed examples in Markdown format" | Correct (authoritative) |
| Ch4 | 29 | "9,922 ChatML examples" | Correct |
| Ch4 | 76 | "9,922 examples" | Correct |
| Ch7 | 28 | "9,922 ChatML examples (bbjllm); 2 seed examples" | Correct |
| Ch7 | 78 | "9,922 ChatML examples" | Correct |

**No fixes needed for CONS-03.** Training data counts are already consistent.

### Stale Cross-References to Chapter 7

**Identified by Phase 35 (known scope for Phase 36):**

| Chapter | Line | Current Text | Issue | Fix |
|---------|------|-------------|-------|-----|
| Ch2 | 388 | "the [implementation roadmap](/docs/implementation-roadmap) with timelines and resource planning" | Ch7 no longer has timelines or resource planning. | Update description to match Ch7's actual content (progress summary + forward plan) |
| Ch4 | 673 | "timelines, milestones, and the path from Continue.dev model delivery to full language-server-powered AI completion" | Ch7 no longer has timelines/milestones. | Update description to match Ch7's actual content |
| Ch5 | 308 | "Timeline, phasing, and resource allocation for all components" | Ch7 no longer has these. | Update description to match Ch7's actual content |
| Ch6 | 537 | "Timeline and phases for building the ingestion pipeline, provisioning the vector store, and validating retrieval quality" | Ch7 no longer has these. | Update description to match Ch7's actual content |

All four describe Chapter 7 using language from its pre-Phase-35 speculative structure. Chapter 7 is now a "progress summary and forward plan" chapter.

### Additional Findings: Status Terminology

| Chapter | Line | Current Text | Issue | Fix |
|---------|------|-------------|-------|-----|
| Ch1 | 320 | "**Under investigation:** Copilot BYOK integration remains in early exploration" | Phase 32 established terminology: "active research" not "under investigation." | Update to use Phase 32 status convention |

### Additional Findings: Landing Page (index.tsx)

| Location | Line | Current Text | Issue | Fix |
|----------|------|-------------|-------|-----|
| Landing page | 44 | `'Phased delivery, resources, risks, and success metrics.'` | Ch7 no longer covers phased delivery, resources, risks, or success metrics. | Update to match Ch7's actual content ("Progress summary and forward plan") |

### Additional Finding: Ch1 Decision Callout Status

| Chapter | Line | Current Text | Issue | Fix |
|---------|------|-------------|-------|-----|
| Ch1 | 274 | "**Status:** Training data structure defined; base model evaluation underway." | Base model evaluation is no longer "underway" -- 14B-Base has been recommended. bbjllm experiment exists. | Update to reflect current state |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Broken link detection | Custom link-checking script | `npm run build` with `onBrokenLinks: 'throw'` | Docusaurus already validates all links at build time |
| Finding all model references | Manual reading of all chapters | `grep -n "7B\|14B\|32B" docs/` | Systematic search catches every occurrence |
| Cross-reference accuracy | Manual URL checking | Docusaurus build + manual contextual review | Build catches broken links; manual review catches stale descriptions |

**Key insight:** The Docusaurus build (`npm run build`) is the final gate. It must pass with zero content warnings after all fixes are applied.

## Common Pitfalls

### Pitfall 1: Changing Content in Authoritative Chapters

**What goes wrong:** Editing Chapter 3, Chapter 2, or Chapter 7 during a consistency pass introduces risk of altering carefully crafted content from Phases 33, 32, and 35.
**Why it happens:** It is tempting to "improve" the authoritative chapter while reading it for comparison.
**How to avoid:** The authoritative chapters (Ch2, Ch3, Ch7) are read-only for this phase. Only non-authoritative chapters receive fixes to match them. Exception: Ch2 lines 98 and 184 reference the wrong model size -- these are factual errors that predate v1.7 and were missed in Phase 32.
**Warning signs:** Any edit to Ch3 or Ch7 content sections.

### Pitfall 2: bbjcpl Not Available

**What goes wrong:** CONS-04 requires verifying BBj code samples compile via `bbjcpl -N`, but the compiler is not installed on the dev machine.
**Why it happens:** bbjcpl is part of the BBj runtime distribution, not available standalone.
**How to avoid:** Flag this explicitly at the start. Options: (a) user provides access to a machine with BBj, (b) accept that code blocks were NOT modified during v1.7 and risk is minimal, (c) user manually reviews as domain expert. The 21 BBj code blocks across chapters were written/validated in earlier phases and have not been touched during v1.7.
**Warning signs:** Silently skipping BBj code validation or claiming it passed without actually running the compiler.

### Pitfall 3: Over-Correcting Cross-Reference Descriptions

**What goes wrong:** Rewriting the entire sentence or paragraph around a stale cross-reference, changing the chapter's narrative flow.
**Why it happens:** The temptation to "improve" the surrounding text while fixing the cross-reference.
**How to avoid:** Change ONLY the descriptive text about what Chapter 7 contains. Do not alter the sentence structure, surrounding paragraphs, or narrative flow.
**Warning signs:** Diff showing changes to more than one sentence per stale cross-reference.

### Pitfall 4: Missing the Landing Page

**What goes wrong:** Fixing all chapter-level inconsistencies but forgetting the landing page (`src/pages/index.tsx`), which has a stale Chapter 7 description.
**Why it happens:** The landing page is a TSX file, not a markdown doc -- easy to forget.
**How to avoid:** Include `src/pages/index.tsx` in the fix scope explicitly.
**Warning signs:** Landing page still showing "Phased delivery, resources, risks, and success metrics" after all chapter fixes are applied.

### Pitfall 5: Breaking the Build with Cross-Reference Edits

**What goes wrong:** Changing a cross-reference URL or anchor fragment and introducing a broken link.
**Why it happens:** The cross-reference text needs updating, but the URL/anchor may not.
**How to avoid:** For the 4 stale cross-references, only change the descriptive text, NOT the URL path. The URLs (`/docs/implementation-roadmap`) are still correct; only the surrounding prose describing what Chapter 7 contains is wrong. Run `npm run build` after all fixes.
**Warning signs:** `npm run build` failing with broken link errors.

## Code Examples

### Finding All Model Size References

```bash
grep -n "7B\|14B\|32B" docs/*/index.md docs/*/index.mdx
```

### Finding All MCP Tool References

```bash
grep -n "search_bbj_knowledge\|generate_bbj_code\|validate_bbj_syntax" docs/*/index.md docs/*/index.mdx
```

### Finding All Training Data Count References

```bash
grep -n "9,922\|9922\|seed example" docs/*/index.md docs/*/index.mdx
```

### Finding Stale Ch7 Cross-References

```bash
grep -n "timeline\|phasing\|resource planning\|resource allocation\|success metric" docs/*/index.md docs/*/index.mdx
```

### Running the Build Gate

```bash
npm run build 2>&1 | grep -i -E "warn|error|broken"
# Expected: no output (only Rspack deprecation notice, which is from Docusaurus internals)
```

## BBj Code Block Inventory (CONS-04)

21 BBj code blocks across the documentation. None were modified during v1.7 phases:

| Chapter | Count | Line Numbers | Modified in v1.7? |
|---------|-------|-------------|-------------------|
| Ch1 (index.mdx) | 13 | 55, 68, 82, 95, 116, 126, 136, 146, 163, 175, 186, 198 | No |
| Ch3 (index.md) | 4 | 141, 196, 402, 430 | No (surrounding prose changed, not code blocks) |
| Ch4 (index.md) | 2 | 506, 521 | No |
| Ch5 (index.md) | 2 | 89, 110 | No (these are inside blockquotes as example responses) |

Note: Ch5 code blocks (lines 89, 110) are inside `> ` blockquote markdown, displayed as example chat responses. They are demonstration output, not standalone programs. Whether these need `bbjcpl` validation is debatable -- they are code snippets inside prose, not complete compilable programs.

## Complete Fix List (Ordered by File)

### File 1: `docs/01-bbj-challenge/index.mdx`

1. **Line 274**: Update Decision callout status from "Training data structure defined; base model evaluation underway" to reflect 14B-Base recommendation and bbjllm experiment status.
2. **Line 320**: Change "Under investigation" to use Phase 32 status terminology (e.g., "Active research" or "Planned" depending on best fit for Copilot BYOK + Continue.dev).

### File 2: `docs/02-strategic-architecture/index.md`

3. **Line 98**: Change "Qwen2.5-Coder-7B" to "Qwen2.5-Coder-14B-Base" and update surrounding text as needed (size/self-hosting language may need minor adjustment since 14B is still practical for self-hosting).
4. **Line 184**: Change "Qwen2.5-Coder-7B via Ollama" to reference 14B-Base.
5. **Line 388**: Update cross-reference description from "timelines and resource planning" to accurately describe Ch7's current content.

### File 3: `docs/04-ide-integration/index.md`

6. **Line 673**: Update cross-reference description from "timelines, milestones, and the path from Continue.dev..." to accurately describe Ch7's current content.

### File 4: `docs/05-documentation-chat/index.md`

7. **Line 173**: Change "the 7B model with a 4096-token context" to reference the 14B model with appropriate context window size.
8. **Line 308**: Update cross-reference description from "Timeline, phasing, and resource allocation" to accurately describe Ch7's current content.

### File 5: `docs/06-rag-database/index.md`

9. **Line 537**: Update cross-reference description from "Timeline and phases for building..." to accurately describe Ch7's current content.

### File 6: `src/pages/index.tsx`

10. **Line 44**: Update Chapter 7 description from "Phased delivery, resources, risks, and success metrics" to match Ch7's current content.

**Total: 10 text fixes across 6 files + CONS-04 code block verification.**

## Open Questions

1. **bbjcpl availability for CONS-04**
   - What we know: `bbjcpl` is not installed on the dev machine. All 21 BBj code blocks were NOT modified during v1.7 (Phases 32-35 only changed prose, not code blocks).
   - What's unclear: Whether the user wants to validate code blocks that were not modified, or accept that unmodified code blocks from earlier phases are still valid.
   - Recommendation: Document that code blocks were not modified. If user has BBj installed elsewhere, validate there. Otherwise, accept the low-risk position that unmodified code is still valid. The code blocks were validated in Phase 19 (or earlier phases when they were created).

2. **Ch2 line 98 surrounding text**
   - What we know: The paragraph at line 98 mentions "7B" and also discusses "practical size for self-hosting." The 14B model is still practical for self-hosting (fits in 16GB RAM as Q4_K_M).
   - What's unclear: How much of the surrounding paragraph should be adjusted. The sentence structure may need minor rewording.
   - Recommendation: Minimal edit -- change the model name and size, keep the self-hosting claim (still valid for 14B).

3. **Ch1 line 320 status terminology**
   - What we know: "Under investigation" is not in the Phase 32 established set (operational / operational for internal exploration / active research / planned).
   - What's unclear: Best replacement. Copilot BYOK is described as "active research" in Ch4. Continue.dev is also "active research."
   - Recommendation: Use "Active research" to match Ch4's treatment of the same topic.

## Sources

### Primary (HIGH confidence)

- Direct examination of all 7 chapter files: `docs/01-bbj-challenge/index.mdx`, `docs/02-strategic-architecture/index.md`, `docs/03-fine-tuning/index.md`, `docs/04-ide-integration/index.md`, `docs/05-documentation-chat/index.md`, `docs/06-rag-database/index.md`, `docs/07-implementation-roadmap/index.md`
- Direct examination of landing page: `src/pages/index.tsx`
- Phase 35 summary: confirmed 4 stale cross-references (Ch2 line 388, Ch4 line 673, Ch5 line 308, Ch6 line 537)
- Phase 32 decisions: established status terminology conventions
- Phase 33 decisions: established 14B-Base as primary recommendation
- `npm run build` output: confirmed zero content warnings
- `bbjcpl` availability: confirmed NOT installed on dev machine

### Secondary (MEDIUM confidence)

- Phase 19 research: confirmed BBj code block count methodology and bbjcpl validation approach
- STATE.md: confirmed all decisions from Phases 32-35

### Tertiary (LOW confidence)

- None. All findings verified by direct file examination.

## Metadata

**Confidence breakdown:**
- Model name consistency (CONS-01): HIGH -- all occurrences found by systematic grep, specific line numbers identified
- MCP tool consistency (CONS-02): HIGH -- all occurrences found by systematic grep, already consistent
- Training data counts (CONS-03): HIGH -- all occurrences found by systematic grep, already consistent
- Code block compilation (CONS-04): MEDIUM -- code blocks inventoried but cannot verify compilation without bbjcpl
- Stale cross-references: HIGH -- identified by Phase 35 summary, verified by direct examination of Chapter 7
- Landing page: HIGH -- examined directly

**Research date:** 2026-02-06
**Valid until:** 2026-03-06 (stable -- no external dependencies, all findings from direct file examination)
