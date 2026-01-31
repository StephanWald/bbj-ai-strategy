# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-31)

**Core value:** Stakeholders can understand the BBj AI strategy, why it's necessary, and how it will be executed -- through a well-structured, publicly accessible documentation site.
**Current focus:** Phase 3 - Foundation Chapters (Chapters 1-2 written, Chapter 3 next)

## Current Position

Phase: 3 of 5 (Foundation Chapters)
Plan: 3 of 4 in current phase
Status: In progress
Last activity: 2026-01-31 -- Completed 03-03-PLAN.md (Chapter 2: Strategic Architecture)

Progress: [#######░░░░░░░░] 47% (7/15 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: 4 min
- Total execution time: 0.43 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-scaffold-deploy-pipeline | 2/2 | 12 min | 6 min |
| 02-content-architecture-landing-page | 2/2 | 6 min | 3 min |
| 03-foundation-chapters | 3/4 | 6 min | 2 min |

**Recent Trend:**
- Last 5 plans: 02-01 (3 min), 03-01 (1 min), 03-02 (3 min), 03-03 (2 min)
- Trend: consistent 1-3 min for config and content tasks

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
- [03-01]: BBj Prism grammar confirmed to exist in prismjs -- no custom grammar or fallback needed (resolves research concern)
- [03-01]: Used git mv for Chapter 1 rename to preserve file history cleanly
- [03-02]: Two Tab-based cross-generation comparisons in Chapter 1 (greeting + data access) to show both UI divergence and shared core
- [03-02]: webforJ contrast as comparison table, not separate chapter
- [03-02]: Qwen2.5-Coder family referenced in Current Status as leading base model candidate
- [03-03]: Chapter 2 stays as .md (no JSX needed -- only Markdown, admonitions, and Mermaid)
- [03-03]: Architecture framed as two-layer model: shared foundation (model + RAG) consumed by application layer
- [03-03]: Included Qwen2.5-Coder-7B as specific model recommendation with link to official blog post

### Pending Todos

None.

### Blockers/Concerns

- [01-01]: Rspack deprecation warning about experiments.lazyBarrel appears during builds -- cosmetic, no action needed

## Session Continuity

Last session: 2026-01-31 09:41 UTC
Stopped at: Completed 03-03-PLAN.md. Chapter 2 (Strategic Architecture) written and building cleanly. Ready for 03-04 (Chapter 3: Fine-Tuning the Model).
Resume file: None
