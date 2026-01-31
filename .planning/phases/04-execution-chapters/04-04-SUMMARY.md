---
phase: 04-execution-chapters
plan: 04
subsystem: documentation
tags: [implementation-roadmap, risk-assessment, nist-ai-rmf, mvp-checkpoints, infrastructure-costs, success-metrics]

# Dependency graph
requires:
  - phase: 03-foundation-chapters
    provides: Chapters 1-3 (BBj Challenge, Strategic Architecture, Fine-Tuning)
  - phase: 04-execution-chapters plans 01-03
    provides: Chapters 4-6 (IDE Integration, Documentation Chat, RAG Database)
provides:
  - "Chapter 7: Implementation Roadmap with phased plan, MVP checkpoints, costs, risks, and metrics"
  - "Cross-references linking all 7 chapters into a cohesive strategy document"
affects:
  - 04-05 (cross-chapter quality pass -- Chapter 7 now exists for link audit)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "MVP checkpoint pattern: each phase ends with explicit stop-and-have-value description"
    - "Risk matrix pattern: likelihood x impact x mitigation table with NIST AI RMF reference"
    - "Cost scenario table: minimal/typical/cloud-first infrastructure comparison"

key-files:
  created: []
  modified:
    - docs/07-implementation-roadmap/index.md

key-decisions:
  - "Build roadmap from current state (shipped language server, ~10K data points) rather than from zero"
  - "Hardware/infrastructure costs only -- no staffing/personnel estimates"
  - "NIST AI RMF referenced for risk assessment credibility"
  - "MVP checkpoints as explicit safe stopping points (not just milestones)"
  - "Baselines section added to success metrics -- measure before to compare after"

patterns-established:
  - "Risk matrix with checkpoint-based re-evaluation guidance"
  - "Cost scenario comparison (minimal/typical/cloud) for infrastructure planning"

# Metrics
duration: 4min
completed: 2026-01-31
---

# Phase 4 Plan 4: Implementation Roadmap Summary

**Chapter 7 with four-phase roadmap, MVP checkpoints, NIST AI RMF risk assessment, infrastructure cost scenarios, and three-tier success metrics -- all anchored in the shipped language server and in-progress fine-tuning rather than starting from zero**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-31T10:36:34Z
- **Completed:** 2026-01-31T10:41:02Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Replaced 14-line placeholder with 300-line complete chapter covering implementation phases, costs, risks, and metrics
- Four implementation phases with explicit MVP checkpoints describing standalone value at each stop
- Infrastructure cost table with three scenarios (minimal/typical/cloud-first) showing $1,500-5,000 one-time investment
- NIST AI RMF-referenced risk assessment with 6 identified risks, likelihood/impact/mitigation, and checkpoint-based re-evaluation guidance
- Success metrics across technical (7 metrics), user (3 metrics), and business (3 metrics) dimensions with baseline establishment guidance
- Cross-references to all 6 preceding chapters, linking Chapter 7 as the synthesis layer

## Task Commits

Each task was committed atomically:

1. **Task 1: Write Chapter 7 -- Implementation Roadmap** - `911c5d2` (feat)

## Files Created/Modified
- `docs/07-implementation-roadmap/index.md` - Complete Chapter 7: Implementation Roadmap (300 lines, replacing 14-line placeholder)

## Decisions Made
- Built roadmap from current state (shipped language server, ~10K training data points) rather than from zero -- per CONTEXT.md and RESEARCH.md
- Hardware/infrastructure costs only, no staffing estimates -- per CONTEXT.md decision; original paper's $150K-250K estimate excluded
- Referenced NIST AI RMF for risk assessment credibility without over-committing to full framework adoption
- Added "Why This Order" section explaining phase dependency logic (model -> IDE -> RAG -> refinement)
- Added cost scenario comparison table (minimal/typical/cloud-first) beyond the single cost table from RESEARCH.md
- Added "Establishing Baselines" subsection to success metrics -- directional measurement guidance
- Added "Using This Matrix During Execution" subsection to risk assessment -- checkpoint-based risk re-evaluation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed broken anchor link to fine-tuning chapter**
- **Found during:** Task 1 (build verification)
- **Issue:** Link `/docs/fine-tuning#serving-with-ollama` referenced a non-existent anchor; actual heading is "Hosting via Ollama" (`#hosting-via-ollama`)
- **Fix:** Changed anchor to `#hosting-via-ollama`
- **Files modified:** docs/07-implementation-roadmap/index.md
- **Verification:** `npm run build` passes with zero broken anchor warnings
- **Committed in:** 911c5d2 (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Trivial anchor fix. No scope change.

## Issues Encountered
- Initial draft was 252 lines (below 300 minimum). Expanded with substantive content: "Why This Order" phase dependency explanation, cost scenario comparison table, baseline establishment guidance for success metrics, and checkpoint-based risk re-evaluation guidance. All additions are substantive -- no padding.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 7 chapters now have substantive content (no more "Coming Soon" placeholders)
- Ready for 04-05 (cross-chapter quality pass): Chapter 7 provides cross-reference targets and Current Status section that the quality pass can verify
- All Docusaurus links verified via `npm run build` with `onBrokenLinks: 'throw'`

---
*Phase: 04-execution-chapters*
*Completed: 2026-01-31*
