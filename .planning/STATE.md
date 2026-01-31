# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-31)

**Core value:** Stakeholders can understand the BBj AI strategy, why it's necessary, and how it will be executed -- through a well-structured, publicly accessible documentation site.
**Current focus:** Phase 2 complete. Ready for Phase 3 - Foundation Chapters

## Current Position

Phase: 2 of 5 (Content Architecture & Landing Page) -- COMPLETE
Plan: 2 of 2 in current phase (all complete)
Status: Phase complete
Last activity: 2026-01-31 -- Completed 02-01-PLAN.md (Landing page with problem-first hero, audience routing)

Progress: [####░░░░░░░░░░░] 27% (4/15 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 5 min
- Total execution time: 0.3 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-scaffold-deploy-pipeline | 2/2 | 12 min | 6 min |
| 02-content-architecture-landing-page | 2/2 | 6 min | 3 min |

**Recent Trend:**
- Last 5 plans: 01-01 (7 min), 01-02 (5 min), 02-02 (3 min), 02-01 (3 min)
- Trend: accelerating, UI/content tasks consistently fast

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Split content into Foundation (Ch 1-3) and Execution (Ch 4-7) phases for manageable delivery
- [Roadmap]: BBj Prism syntax highlighting placed in Phase 3 (with first content chapters) rather than Phase 1 (scaffold)
- [01-01]: Docusaurus numberPrefix stripping is default -- doc IDs and URLs exclude numeric folder prefix (e.g., bbj-challenge/index not 01-bbj-challenge/index)
- [01-01]: Migrated onBrokenMarkdownLinks to markdown.hooks for v4 compatibility
- [01-02]: Deployed under StephanWald GitHub account (not beff) -- gh CLI authenticated as StephanWald, site live at stephanwald.github.io/bbj-ai-strategy
- [01-02]: Used upload-pages-artifact@v3 (not v4) to preserve .nojekyll and _-prefixed directories
- [01-02]: Added .claude/ to .gitignore to exclude local agent settings
- [02-02]: Admonition type allocation: :::tip reserved for TL;DR, :::info for decision records, :::note/warning/danger for general use
- [02-02]: Mermaid theme pairing: neutral (light) / dark (dark) for clean professional rendering
- [02-02]: CSS uses Infima variable overrides rather than custom class names, staying within Docusaurus conventions
- [02-01]: Landing page hero leads with problem-first headline ("Generic LLMs Fail on BBj"), not product name
- [02-01]: Audience routing uses inline cards with chapter links, not separate per-audience landing pages
- [02-01]: All landing page styling via CSS modules and Infima variables -- no additional npm packages

### Pending Todos

None.

### Blockers/Concerns

- [Research]: BBj Prism grammar may not exist -- fallback to `basic` highlighting if custom grammar exceeds effort budget
- [01-01]: Rspack deprecation warning about experiments.lazyBarrel appears during builds -- cosmetic, no action needed

## Session Continuity

Last session: 2026-01-31 08:37 UTC
Stopped at: Completed 02-01-PLAN.md. Phase 2 fully complete. Ready for Phase 3.
Resume file: None
