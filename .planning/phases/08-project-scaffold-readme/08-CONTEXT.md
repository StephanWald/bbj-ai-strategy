# Phase 8: Project Scaffold & README - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Set up the `rag-ingestion/` Python sub-project with uv, and replace the repo-level README with a project overview. Engineers can clone the repo, run `uv sync`, and understand what the project is. Parsers, models, pipeline logic, and the ingestion CLI are built in later phases.

</domain>

<decisions>
## Implementation Decisions

### README structure & tone
- Audience: general developers (no BBj knowledge assumed — brief context paragraph)
- Tone: developer-friendly, direct, second-person ("you"), like a well-maintained open-source project
- Structure: minimal orientation — one-paragraph overview, link to live site (homepage only), pointer to `rag-ingestion/` README for pipeline details
- No badges
- No license mention
- No Docusaurus dev commands (readers can figure out it's Docusaurus)
- Replace the existing boilerplate README entirely

### Python project layout
- Package name: `bbj_rag` (imports as `from bbj_rag.parsers import ...`)
- Directory: `rag-ingestion/` at repo root (mono-repo style, decided in v1.2 planning)
- Nested package structure: `bbj_rag/parsers/`, `bbj_rag/models/`, `bbj_rag/pipeline/`, etc.
- Sub-packages created as phases build them vs. full skeleton upfront: Claude's discretion

### Dependency & tooling choices
- Dev tooling: pytest + ruff (lint/format) + mypy (type checking) — full professional setup
- Pre-commit hooks: yes, auto-run ruff + mypy on commit
- Task runner: Makefile (`make test`, `make lint`, `make format`)
- Dependency pinning: pin core deps to specific known-good versions in pyproject.toml (pydantic, psycopg, sentence-transformers, etc.)
- Python version: 3.12+ (from roadmap success criteria)
- Package manager: uv (decided in v1.2 planning)

### Claude's Discretion
- Whether to create full skeleton with stub files in each package or just top-level structure (pick what makes sense for phase boundaries)
- Whether to set up a CLI entry point now or defer to Phase 12
- Exact Makefile targets beyond test/lint/format
- pyproject.toml metadata (description, authors, etc.)
- .gitignore additions for Python

</decisions>

<specifics>
## Specific Ideas

- Live site link: https://stephanwald.github.io/bbj-ai-strategy/ (homepage only, no deep links)
- Package imports should feel natural: `from bbj_rag.parsers import ...`
- README should explain what the project IS (BBj AI strategy + ingestion pipeline) without assuming BBj knowledge

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-project-scaffold-readme*
*Context gathered: 2026-01-31*
