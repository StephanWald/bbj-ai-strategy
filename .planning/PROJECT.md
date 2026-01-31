# BBj AI Strategy Documentation Site

## What This Is

A public Docusaurus site that communicates BASIS International's AI strategy for BBj — covering LLM fine-tuning, IDE integration, documentation chat, and migration tooling. The site serves three audiences (internal developers, leadership, customers/partners) and doubles as implementation context for executing the strategy in phases. Content is organized into topic-based chapters, each researched and written to depth.

## Core Value

Stakeholders (developers, leadership, customers) can understand the BBj AI strategy, why it's necessary, and how it will be executed — through a well-structured, publicly accessible documentation site.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Docusaurus site scaffolded with correct chapter structure
- [ ] Chapter 1: The BBj Challenge — why LLMs fail on BBj, 4 generations explained
- [ ] Chapter 2: Strategic Architecture — unified AI infrastructure vision
- [ ] Chapter 3: Fine-Tuning the Model — training data, base model selection, hosting approach
- [ ] Chapter 4: IDE Integration — VSCode extension + Langium, completion mechanisms
- [ ] Chapter 5: Documentation Chat — website chat system, generation-aware responses
- [ ] Chapter 6: RAG Database Design — multi-generation document structure, retrieval strategy
- [ ] Chapter 7: Implementation Roadmap — phases, resources, timeline, risk assessment
- [ ] Each chapter researched for current best practices (2025/2026 state of the art)
- [ ] Decision rationale documented for key technical choices
- [ ] Current status / what's been tried reflected in content
- [ ] How-to / execution guidance added where the original paper is abstract
- [ ] Site deployed to GitHub Pages
- [ ] Landing page with executive summary and navigation

### Out of Scope

- Authentication or access control — site is fully public
- Interactive features (chat widgets, live demos) — this is documentation, not the AI system itself
- Building the actual AI infrastructure (model, RAG, extension) — this project documents the strategy
- Mobile-optimized design beyond Docusaurus defaults — standard responsive is sufficient
- Internationalization — English only

## Context

- **Source material:** `bbj-llm-strategy.md` — a comprehensive strategy paper (~1100 lines) covering all major topics. Well-structured but reads as a single monolithic document. Missing execution details, current status, and deeper research on specific topics.
- **BBj:** Business BASIC for Java by BASIS International. Spans 4 generations: character UI (1980s), Visual PRO/5 (1990s), BBj GUI/Swing (2000s), DWC/browser (2010s+). Extremely niche — LLMs have near-zero training data on it.
- **The core problem:** Generic LLMs hallucinate BBj code because BBj is too rare in training data. The strategy addresses this through fine-tuning, RAG, and generation-aware tooling.
- **Three initiatives:** Fine-tuned BBj model (via Ollama), VSCode extension with Langium integration, documentation chat system — all sharing unified infrastructure.
- **Audiences:** Internal developers (implementation detail), leadership (strategy/ROI), customers/partners (capability awareness).
- **Content process:** Research-driven — research a topic deeply, then write/rewrite the chapter based on findings. Incremental improvement across sessions.
- **webforJ context:** BASIS also has webforJ (Java-based web framework) where generic LLMs work fine because they know Java. BBj is the unique challenge.

## Constraints

- **Tech stack**: Docusaurus (React-based static site generator) — well-suited for documentation sites
- **Deployment**: GitHub Pages — free, simple, tied to this repo
- **Content source**: Existing strategy paper is the seed; each chapter needs research and potential rewriting
- **Public visibility**: All content must be appropriate for public consumption — no internal secrets or sensitive implementation details

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Docusaurus over alternatives (MkDocs, GitBook, etc.) | Industry standard for docs sites, React-based, good theming, built-in search | — Pending |
| Topic-based chapters over audience-based organization | Strategy has natural topic boundaries; all audiences benefit from the same depth | — Pending |
| GitHub Pages deployment | Free, simple, integrates with the repo naturally | — Pending |
| Public site (no auth) | Strategy communication benefits from accessibility; no sensitive content | — Pending |
| Research-driven content process | Ensures each chapter reflects current state of the art, not just the original paper | — Pending |

---
*Last updated: 2026-01-31 after initialization*
