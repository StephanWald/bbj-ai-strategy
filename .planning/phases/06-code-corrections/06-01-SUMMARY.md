---
phase: 06-code-corrections
plan: 01
subsystem: docs
tags: [bbj, visual-pro5, dwc, code-samples, mnemonic-syntax, sysgui]

# Dependency graph
requires:
  - phase: none
    provides: existing Chapter 1 MDX content
provides:
  - "Chapter 1 with corrected BBj code samples matching authoritative PDF reference"
  - "Accurate Visual PRO/5 mnemonic syntax examples"
  - "Correct DWC addWindow signatures with coordinate parameters"
affects: [06-02, 06-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Visual PRO/5 mnemonic pattern: print (sysgui)'window'(x,y,w,h,title,flags,context)"
    - "Channel-based CTRL: ctrl(sysgui,controlId,index)"
    - "DWC addWindow with full coordinate signature"

key-files:
  created: []
  modified:
    - docs/01-bbj-challenge/index.mdx

key-decisions:
  - "Used lowercase print/open/ctrl in Visual PRO/5 examples to match PDF reference style"
  - "DWC code block given same coordinate params as BBj GUI to show API equivalence"

patterns-established:
  - "Correct Visual PRO/5 mnemonic syntax for all future chapters"
  - "Channel-based CTRL() syntax pattern for all future chapters"

# Metrics
duration: 2min
completed: 2026-01-31
---

# Phase 6 Plan 1: Fix Chapter 1 BBj Code Samples Summary

**Corrected all hallucinated Visual PRO/5 mnemonic syntax, DWC method signatures, and CTRL() channel-based references in Chapter 1 (The BBj Challenge)**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-01-31T13:33:11Z
- **Completed:** 2026-01-31T13:34:35Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Replaced fabricated `WINDOW CREATE` / `BUTTON CREATE` verb syntax with correct `PRINT (sysgui)'WINDOW'(...)` / `'BUTTON'(...)` mnemonic syntax across 3 Visual PRO/5 code blocks
- Fixed DWC `addWindow` / `addStaticText` / `addButton` method signatures to include coordinate parameters
- Corrected all `CTRL()` references from wrong `CTRL(wnd,id)` to channel-based `ctrl(sysgui,controlId,index)` syntax
- Updated comparison table Legacy GUI row and all prose descriptions to match corrected code

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix all Visual PRO/5 code blocks and DWC code block** - `2057213` (fix)

## Files Created/Modified

- `docs/01-bbj-challenge/index.mdx` - Corrected 6 locations: 3 Visual PRO/5 code blocks, 1 DWC code block, 1 comparison table row, 2 prose descriptions

## Decisions Made

- Used lowercase `print`/`open`/`ctrl` in Visual PRO/5 examples to match the style shown in the authoritative PDF reference (GuideToGuiProgrammingInBBj.pdf)
- Gave the DWC code block the same coordinate parameters as the BBj GUI tab to clearly demonstrate API equivalence between the two generations

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- Chapter 1 code samples are now authoritative and match the PDF reference
- Plans 06-02 and 06-03 can proceed to fix remaining chapters
- The corrected Visual PRO/5 mnemonic pattern and CTRL() syntax established here should be followed in all subsequent chapter corrections

---
*Phase: 06-code-corrections*
*Completed: 2026-01-31*
