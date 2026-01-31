---
phase: 08-project-scaffold-readme
plan: 01
subsystem: infra
tags: [python, uv, hatchling, pytest, ruff, mypy, pre-commit, makefile]

# Dependency graph
requires:
  - phase: 07-custom-branding
    provides: completed v1.1 site (branding, code corrections)
provides:
  - Working Python sub-project (rag-ingestion/) with uv, pytest, ruff, mypy
  - Repo-level README describing project and linking to live site
  - Pre-commit hooks scoped to rag-ingestion/
  - Makefile task runner for dev workflow
affects:
  - 09-schema-data-models (builds on rag-ingestion/ scaffold)
  - 10-flare-parser (adds parser code into bbj_rag package)
  - 11-bbj-intelligence (adds BBj-specific modules)
  - 12-embedding-pipeline (adds embedding and storage)
  - 13-additional-parsers (adds more parsers)
  - 14-documentation-quality (writes rag-ingestion/README.md)

# Tech tracking
tech-stack:
  added: [uv 0.9.x, hatchling, pytest 9.x, ruff 0.14.x, mypy 1.19.x, pre-commit 4.x]
  patterns: [src-layout package, uv dependency management, Makefile task runner]

key-files:
  created:
    - rag-ingestion/pyproject.toml
    - rag-ingestion/Makefile
    - rag-ingestion/src/bbj_rag/__init__.py
    - rag-ingestion/src/bbj_rag/py.typed
    - rag-ingestion/tests/__init__.py
    - rag-ingestion/tests/test_placeholder.py
    - rag-ingestion/.python-version
    - rag-ingestion/uv.lock
    - .pre-commit-config.yaml
  modified:
    - .gitignore
    - README.md

key-decisions:
  - "hatchling build backend (not uv_build) for stable src-layout support"
  - "Pre-commit hooks at repo root scoped to rag-ingestion/ via files filter"
  - "ruff 0.14.x with select rules: E, W, F, I, B, UP, RUF"

patterns-established:
  - "src-layout: rag-ingestion/src/bbj_rag/ with hatch wheel config"
  - "uv run prefix: all Python commands go through uv run for venv isolation"
  - "Makefile targets: sync, test, lint, format, typecheck, check (composite)"
  - "Pre-commit scoping: files: ^rag-ingestion/ on all hooks"

# Metrics
duration: 3min
completed: 2026-01-31
---

# Phase 8 Plan 1: Project Scaffold & README Summary

**Python 3.12+ sub-project (bbj-rag) with uv, hatchling src-layout, pytest/ruff/mypy toolchain, pre-commit hooks, and repo README replacing Docusaurus boilerplate**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-31T18:05:33Z
- **Completed:** 2026-01-31T18:08:25Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Scaffolded rag-ingestion/ as a src-layout Python package with hatchling build backend
- Configured pytest, ruff, and mypy with strict settings and all checks passing
- Created Makefile with self-documenting help target and composite `check` target
- Installed pre-commit hooks scoped to rag-ingestion/ (trailing whitespace, end-of-file, ruff, mypy)
- Replaced Docusaurus boilerplate README with project overview linking to live site

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold rag-ingestion/ Python project with uv and dev tooling** - `3ebda23` (feat)
2. **Task 2: Replace repo README with project overview** - `c830312` (docs)

**Plan metadata:** committed separately (docs: complete plan)

## Files Created/Modified

- `rag-ingestion/pyproject.toml` - Python project metadata, dependencies, tool config (ruff, mypy, pytest, hatch)
- `rag-ingestion/Makefile` - Developer task runner (sync, test, lint, format, typecheck, check, clean)
- `rag-ingestion/src/bbj_rag/__init__.py` - Package root with __version__ = "0.1.0"
- `rag-ingestion/src/bbj_rag/py.typed` - PEP 561 type marker
- `rag-ingestion/tests/__init__.py` - Test package marker
- `rag-ingestion/tests/test_placeholder.py` - Version import test
- `rag-ingestion/.python-version` - Python 3.12 pin for uv
- `rag-ingestion/uv.lock` - Pinned dependency lockfile (21 packages)
- `.pre-commit-config.yaml` - Pre-commit hooks scoped to rag-ingestion/
- `.gitignore` - Added Python cache/build patterns
- `README.md` - Project overview replacing Docusaurus boilerplate

## Decisions Made

- Used hatchling (not uv_build) as build backend for stable src-layout support
- Pre-commit config placed at repo root with `files: ^rag-ingestion/` scoping on all hooks
- Selected ruff rules: E, W, F, I, B, UP, RUF (errors, warnings, pyflakes, isort, bugbear, pyupgrade, ruff-specific)
- mypy strict mode with relaxed untyped defs for tests/ only

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed uv package manager**
- **Found during:** Task 1 (project scaffold)
- **Issue:** uv was not installed on the system; all Python tooling depends on it
- **Fix:** Installed uv 0.9.28 via official installer (curl https://astral.sh/uv/install.sh)
- **Files modified:** None (system-level install to ~/.local/bin)
- **Verification:** `uv --version` returns 0.9.28
- **Committed in:** N/A (system tool, not project file)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary prerequisite install. No scope creep.

## Issues Encountered

None -- all tools installed cleanly, all checks passed on first run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- rag-ingestion/ is ready for Phase 9 (Schema & Data Models) to add pgvector DDL, Pydantic models, and config system
- The bbj_rag package is importable and extensible -- new modules can be added under src/bbj_rag/
- Dev tooling (pytest, ruff, mypy) is configured and passing -- Phase 9 code will be checked automatically
- Pre-commit hooks will catch issues on every commit touching rag-ingestion/

---
*Phase: 08-project-scaffold-readme*
*Completed: 2026-01-31*
