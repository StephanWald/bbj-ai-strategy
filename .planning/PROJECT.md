# BBj AI Strategy Documentation Site

## What This Is

A public Docusaurus site that communicates BASIS International's AI strategy for BBj — covering LLM fine-tuning, IDE integration, documentation chat, and RAG database design. The site serves three audiences (internal developers, leadership, customers/partners) through 7 researched chapters with full-text search, professional content patterns, and automated deployment. Live at https://stephanwald.github.io/bbj-ai-strategy/.

## Core Value

Stakeholders (developers, leadership, customers) can understand the BBj AI strategy, why it's necessary, and how it will be executed — through a well-structured, publicly accessible documentation site.

## Requirements

### Validated

- ✓ Docusaurus site scaffolded with Rspack, 7-chapter structure, GitHub Pages deployment — v1.0
- ✓ Landing page with problem-first hero, executive summary, audience routing — v1.0
- ✓ Content patterns: TL;DR blocks, decision callouts, Mermaid diagrams, BBj syntax highlighting — v1.0
- ✓ Chapter 1: The BBj Challenge (4 generations, LLM failure analysis, webforJ contrast) — v1.0
- ✓ Chapter 2: Strategic Architecture (unified infrastructure, shared model + RAG) — v1.0
- ✓ Chapter 3: Fine-Tuning (Qwen2.5-Coder, QLoRA/Unsloth, Ollama hosting) — v1.0
- ✓ Chapter 4: IDE Integration (Langium + LLM two-layer completion) — v1.0
- ✓ Chapter 5: Documentation Chat (generation-aware responses, deployment options) — v1.0
- ✓ Chapter 6: RAG Database Design (pgvector, hybrid retrieval, MadCap Flare ingestion) — v1.0
- ✓ Chapter 7: Implementation Roadmap (phases, costs, NIST risk assessment, metrics) — v1.0
- ✓ Full-text search, OG meta tags, robots.txt, verified navigation — v1.0
- ✓ All chapters researched for 2025/2026 best practices with execution guidance — v1.0
- ✓ Current status and decision rationale in every chapter — v1.0

### Active

- **CODE-01**: Fix hallucinated Visual PRO/5 code samples in Chapter 1 (replace fabricated `WINDOW CREATE`/`BUTTON CREATE` verb syntax with correct `PRINT (sysgui)'WINDOW'(...)` mnemonic syntax) — v1.1
- **CODE-02**: Fix hallucinated DWC/BBj GUI code samples in Chapter 1 (correct `addWindow`/`addButton` signatures to include coordinate parameters) — v1.1
- **CODE-03**: Fix hallucinated CTRL syntax in Chapter 1 (replace `CTRL(wnd, n)` with correct `CTRL(sysgui, controlId, index)`) — v1.1
- **CODE-04**: Fix comparison table describing Visual PRO/5 as using `WINDOW CREATE`, `BUTTON CREATE` — v1.1
- **CODE-05**: Audit and correct BBj code samples in all remaining chapters (3, 5, and any others) against PDF reference — v1.1
- **CODE-06**: Add reference/attribution to `GuideToGuiProgrammingInBBj.pdf` as authoritative source — v1.1
- **BRAND-01**: Custom favicon and logo using BASIS brand assets — v1.1
- **BRAND-02**: Custom color theme aligned with BASIS brand colors — v1.1
- **BRAND-03**: Typography updates if BASIS brand fonts are specified — v1.1

### Out of Scope

- Authentication or access control — site is fully public
- Interactive features (chat widgets, live demos) — this is documentation, not the AI system itself
- Building the actual AI infrastructure (model, RAG, extension) — this project documents the strategy
- Mobile-optimized design beyond Docusaurus defaults — standard responsive is sufficient
- Internationalization — English only
- Custom favicon/branding — ~~no BASIS logo available~~ moved to Active (BRAND-01/02/03) for v1.1

## Context

- **Source material:** `bbj-llm-strategy.md` — original strategy paper (~1100 lines). Each chapter was researched independently and rewritten, not just ported.
- **BBj:** Business BASIC for Java by BASIS International. Spans 4 generations: character UI (1980s), Visual PRO/5 (1990s), BBj GUI/Swing (2000s), DWC/browser (2010s+). Extremely niche — LLMs have near-zero training data on it.
- **The core problem:** Generic LLMs hallucinate BBj code because BBj is too rare in training data. The strategy addresses this through fine-tuning, RAG, and generation-aware tooling.
- **Three initiatives:** Fine-tuned BBj model (via Ollama), VSCode extension with Langium integration, documentation chat system — all sharing unified infrastructure.
- **Audiences:** Internal developers (implementation detail), leadership (strategy/ROI), customers/partners (capability awareness).
- **webforJ context:** BASIS also has webforJ (Java-based web framework) where generic LLMs work fine because they know Java. BBj is the unique challenge.
- **Current state:** v1.0 shipped 2026-01-31. v1.1 in progress — fixing hallucinated code samples and adding custom branding. 2,441 lines of content across 7 chapters. Site live at stephanwald.github.io/bbj-ai-strategy. Tech stack: Docusaurus 3.9.2, Rspack, GitHub Actions, GitHub Pages.
- **BBj code reference:** `GuideToGuiProgrammingInBBj.pdf` (project root) — authoritative reference for all BBj GUI patterns across 4 generations. Contains complete working sample programs (cust-cui.txt, cust-gui.txt, cust-bbj.txt, cust-obj.txt).

## Constraints

- **Tech stack**: Docusaurus 3.9.2 with Rspack (`@docusaurus/faster`)
- **Deployment**: GitHub Pages under StephanWald account
- **Content source**: Strategy paper as seed, each chapter independently researched
- **Public visibility**: All content appropriate for public consumption

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Docusaurus over alternatives (MkDocs, GitBook, etc.) | Industry standard for docs sites, React-based, good theming, built-in search | ✓ Good |
| Topic-based chapters over audience-based organization | Strategy has natural topic boundaries; all audiences benefit from the same depth | ✓ Good |
| GitHub Pages deployment | Free, simple, integrates with the repo naturally | ✓ Good |
| Public site (no auth) | Strategy communication benefits from accessibility; no sensitive content | ✓ Good |
| Research-driven content process | Ensures each chapter reflects current state of the art, not just the original paper | ✓ Good |
| Qwen2.5-Coder-7B-Base as recommended model | Surpasses CodeLlama and StarCoder2 on all benchmarks for code generation | ✓ Good |
| QLoRA via Unsloth for training | $1,500 GPU cost vs $50K+ for full fine-tuning | ✓ Good |
| Two-layer IDE completion (Langium + LLM) | Deterministic completions for known patterns, generative for novel code | ✓ Good |
| pgvector over dedicated vector DB | BBj corpus under 50K chunks; identical performance at this scale | ✓ Good |
| Text-only social previews | No custom image needed; removed Docusaurus dinosaur placeholder | ✓ Good |
| @easyops-cn/docusaurus-search-local | Zero-dependency offline search; no Algolia service needed for 7-chapter site | ✓ Good |

---
*Last updated: 2026-01-31 after v1.1 milestone start*
