# Roadmap: BBj AI Strategy Documentation Site

## Overview

This roadmap delivers a Docusaurus documentation site that communicates BASIS International's BBj AI strategy to three audiences (developers, leadership, customers). Work flows from scaffolding and deployment pipeline, through content architecture patterns, into two phases of chapter authoring (foundation then execution topics), and finishes with search, SEO, and launch polish. Each phase produces a verifiable, deployable increment.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Scaffold & Deploy Pipeline** - Docusaurus project with chapter structure, build pipeline, and GitHub Pages deployment
- [x] **Phase 2: Content Architecture & Landing Page** - Landing page, content patterns (TL;DR, decision callouts, Mermaid), audience routing
- [x] **Phase 3: Foundation Chapters** - Chapters 1-3 (BBj Challenge, Strategic Architecture, Fine-Tuning) with BBj syntax highlighting
- [x] **Phase 4: Execution Chapters** - Chapters 4-7 (IDE, Chat, RAG, Roadmap) with research depth and execution guidance across all chapters
- [x] **Phase 5: Search, SEO & Launch** - Full-text search, navigation polish, Open Graph tags, production verification

## Phase Details

### Phase 1: Scaffold & Deploy Pipeline
**Goal**: A working Docusaurus site with correct chapter structure deploys to GitHub Pages on every push to main
**Depends on**: Nothing (first phase)
**Requirements**: SCAF-01, SCAF-02, SCAF-03, SCAF-04
**Success Criteria** (what must be TRUE):
  1. Running `npm run build` produces a working static site with zero errors
  2. Pushing to main triggers GitHub Actions and the site is live on GitHub Pages within minutes
  3. All 7 chapter folders appear in the sidebar with correct ordering and clickable placeholder pages
  4. The site loads correctly at its GitHub Pages URL (no broken CSS, JS, or images from baseUrl mismatch)
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md -- Scaffold Docusaurus with Rspack, configure for GitHub Pages, create 7-chapter folder structure with placeholders
- [x] 01-02-PLAN.md -- Create GitHub Actions deploy/test workflows, push to main, verify live deployment

### Phase 2: Content Architecture & Landing Page
**Goal**: Visitors land on a professional landing page with audience routing, and content patterns (TL;DR blocks, decision callouts, Mermaid diagrams) are ready for chapter authoring
**Depends on**: Phase 1
**Requirements**: ARCH-01, ARCH-02, ARCH-03, ARCH-04
**Success Criteria** (what must be TRUE):
  1. Landing page shows an executive summary and provides clear navigation paths for developers, leadership, and customers
  2. A TL;DR summary block renders at the top of a sample chapter page (pattern ready for all chapters)
  3. Decision record callouts render with distinct visual styling that highlights strategic choices
  4. At least one Mermaid diagram renders correctly in a chapter page, replacing what would be ASCII art
**Plans**: 2 plans

Plans:
- [x] 02-01-PLAN.md -- Redesign landing page with problem-first hero, executive summary, audience routing cards, and chapter grid
- [x] 02-02-PLAN.md -- Install Mermaid theme, create admonition CSS for TL;DR and decision callouts, demonstrate all patterns in sample chapters

### Phase 3: Foundation Chapters
**Goal**: A reader can understand why BBj needs a custom AI strategy, what the unified architecture looks like, and how the model will be fine-tuned -- through three researched, well-structured chapters with proper BBj syntax highlighting
**Depends on**: Phase 2
**Requirements**: CONT-01, CONT-02, CONT-03, SCAF-05
**Success Criteria** (what must be TRUE):
  1. Chapter 1 explains the 4 BBj generations, why generic LLMs fail on BBj, and contrasts with webforJ -- a reader unfamiliar with BBj understands the problem
  2. Chapter 2 presents the unified AI infrastructure vision (shared model, RAG, three initiatives) with architecture diagrams a leadership reader can follow
  3. Chapter 3 covers training data structure, base model selection (with rationale), LoRA approach, and Ollama hosting -- a developer reader has enough detail to begin implementation
  4. BBj code examples throughout all three chapters render with proper syntax highlighting (not plain text)
  5. Each chapter uses the content patterns from Phase 2 (TL;DR blocks, decision callouts where applicable, Mermaid diagrams for architecture)
**Plans**: 4 plans

Plans:
- [x] 03-01-PLAN.md -- Configure BBj syntax highlighting (additionalLanguages config) and rename Chapter 1 to .mdx for Tabs support
- [x] 03-02-PLAN.md -- Research and write Chapter 1: The BBj Challenge (4 generations, cross-generation code comparisons, generic LLM failure, webforJ contrast)
- [x] 03-03-PLAN.md -- Research and write Chapter 2: Strategic Architecture (unified infrastructure vision, shared model + RAG, three initiatives overview)
- [x] 03-04-PLAN.md -- Research and write Chapter 3: Fine-Tuning the Model (training data, Qwen2.5-Coder selection, QLoRA/Unsloth pipeline, Ollama hosting)

### Phase 4: Execution Chapters
**Goal**: All 7 chapters are complete with current best practices, execution guidance, and decision rationale -- the full strategy is documented to depth
**Depends on**: Phase 3
**Requirements**: CONT-04, CONT-05, CONT-06, CONT-07, CONT-08, CONT-09, CONT-10
**Success Criteria** (what must be TRUE):
  1. Chapter 4 covers VSCode extension architecture, Langium integration, and completion mechanisms -- a developer reader understands how to build the IDE integration
  2. Chapter 5 explains the documentation chat system, why generic chat services fail for BBj, and generation-aware response design
  3. Chapter 6 details the RAG database schema, multi-generation document structure, and retrieval strategy with enough specificity to guide implementation
  4. Chapter 7 presents implementation phases, resource requirements, risk assessment, and success metrics -- a leadership reader can evaluate feasibility
  5. Every chapter across the site reflects 2025/2026 best practices (not just the original paper), includes execution guidance where the paper was abstract, and documents current status and decision rationale
**Plans**: 5 plans

Plans:
- [x] 04-01-PLAN.md -- Write Chapter 4: IDE Integration (VSCode extension architecture, Langium, ghost text completion, Copilot bridge)
- [x] 04-02-PLAN.md -- Write Chapter 5: Documentation Chat (why generic services fail, generation-aware responses, deployment options)
- [x] 04-03-PLAN.md -- Write Chapter 6: RAG Database Design (MadCap Flare ingestion, generation metadata, pgvector, hybrid retrieval)
- [x] 04-04-PLAN.md -- Write Chapter 7: Implementation Roadmap (phased plan, infrastructure costs, risk assessment, success metrics)
- [x] 04-05-PLAN.md -- Cross-chapter quality pass (Current Status retrofit to Ch 1-3, Chapter 3 updates, cross-reference audit)

### Phase 5: Search, SEO & Launch
**Goal**: The site is discoverable, navigable, and ready for public sharing with full-text search, proper link previews, and verified production deployment
**Depends on**: Phase 4
**Requirements**: NAV-01, NAV-02, NAV-03, NAV-04
**Success Criteria** (what must be TRUE):
  1. A visitor can search for any term (e.g., "LoRA", "DWC", "training data") and find relevant results across all chapters
  2. Every chapter page has previous/next pagination linking to adjacent chapters
  3. Every chapter page shows a table of contents generated from its headings
  4. Sharing the site URL on Slack, Twitter, or LinkedIn shows a proper preview card with title, description, and image
**Plans**: 2 plans

Plans:
- [x] 05-01-PLAN.md -- Install @easyops-cn/docusaurus-search-local, configure OG meta tags, create robots.txt, remove default social card
- [x] 05-02-PLAN.md -- Fix sidebar_position values, verify pagination/ToC/sitemap/OG tags, deploy to GitHub Pages and verify live site

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|---------------|--------|-----------|
| 1. Scaffold & Deploy Pipeline | 2/2 | Complete | 2026-01-31 |
| 2. Content Architecture & Landing Page | 2/2 | Complete | 2026-01-31 |
| 3. Foundation Chapters | 4/4 | Complete | 2026-01-31 |
| 4. Execution Chapters | 5/5 | Complete | 2026-01-31 |
| 5. Search, SEO & Launch | 2/2 | Complete | 2026-01-31 |
