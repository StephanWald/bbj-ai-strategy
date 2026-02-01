# BBj AI Strategy Documentation Site

## What This Is

A public Docusaurus site that communicates BASIS International's AI strategy for BBj — covering LLM fine-tuning, IDE integration, documentation chat, and RAG database design — plus a Python RAG ingestion pipeline that processes 6 BBj documentation sources into a generation-aware pgvector database. The site serves three audiences (internal developers, leadership, customers/partners) through 7 researched chapters with full-text search, professional content patterns, BASIS brand identity, and automated deployment. The ingestion pipeline bridges strategy documentation with executable code. Live at https://stephanwald.github.io/bbj-ai-strategy/.

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
- ✓ All BBj code samples corrected to match authoritative PDF reference (mnemonic syntax, DWC signatures, CTRL() channel-based syntax) — v1.1
- ✓ PDF reference attribution (GuideToGuiProgrammingInBBj.pdf) added to Chapter 1 — v1.1
- ✓ Custom favicon and navbar logo using BASIS DWC brand assets — v1.1
- ✓ Blue brand color palette (#2563eb/#60a5fa) with matching admonition backgrounds — v1.1
- ✓ Typography confirmed as Infima defaults (no custom fonts needed) — v1.1
- ✓ Repo README with project description and link to live site — v1.2
- ✓ RAG Getting Started sub-page under Chapter 6 with source-by-source ingestion approach and design rationale — v1.2
- ✓ Python ingestion sub-project (`rag-ingestion/`) with parsers, chunking pipeline, pgvector schema, and embedding pipeline — v1.2
- ✓ Source coverage: MadCap Flare docs, standalone PDFs, Advantage articles, Knowledge Base, DWC-Course (6 parsers) — v1.2
- ✓ Current embedding model recommendation: Qwen3-Embedding-0.6B via Ollama (researched Jan 2026) — v1.2

### Active

(None — next milestone requirements TBD via `/gsd:new-milestone`)

### Out of Scope

- Authentication or access control — site is fully public
- Interactive features (chat widgets, live demos) — this is documentation, not the AI system itself
- Production deployment of the RAG pipeline (CI/CD, hosting) — the ingestion sub-project is a starter kit, not production infrastructure
- Mobile-optimized design beyond Docusaurus defaults — standard responsive is sufficient
- Internationalization — English only
- Retrieval API server — v1.2 is a batch ingestion tool, not a running service
- Embedding fine-tuning — requires baseline retrieval quality measurement first
- Agentic RAG features — no query routing, agent loops, or multi-step reasoning

## Context

- **Source material:** `bbj-llm-strategy.md` — original strategy paper (~1100 lines). Each chapter was researched independently and rewritten, not just ported.
- **BBj:** Business BASIC for Java by BASIS International. Spans 4 generations: character UI (1980s), Visual PRO/5 (1990s), BBj GUI/Swing (2000s), DWC/browser (2010s+). Extremely niche — LLMs have near-zero training data on it.
- **The core problem:** Generic LLMs hallucinate BBj code because BBj is too rare in training data. The strategy addresses this through fine-tuning, RAG, and generation-aware tooling.
- **Three initiatives:** Fine-tuned BBj model (via Ollama), VSCode extension with Langium integration, documentation chat system — all sharing unified infrastructure.
- **Audiences:** Internal developers (implementation detail), leadership (strategy/ROI), customers/partners (capability awareness).
- **webforJ context:** BASIS also has webforJ (Java-based web framework) where generic LLMs work fine because they know Java. BBj is the unique challenge.
- **Current state:** v1.2 shipped 2026-02-01. RAG ingestion pipeline complete with 6 source parsers, generation-aware intelligence, embedding pipeline, and hybrid search. v1.1 shipped 2026-01-31 with code corrections and branding. 2,441 lines of docs content + 5,004 lines Python source + 4,906 lines tests. 310 tests passing. Site live at stephanwald.github.io/bbj-ai-strategy. Tech stack: Docusaurus 3.9.2, Rspack, GitHub Actions, GitHub Pages + Python 3.12, uv, pgvector, psycopg3, Ollama.
- **RAG source corpus:** 6 sources with working parsers: (1) MadCap Flare XHTML (7,079 topics), (2) standalone PDFs (GUI programming guide), (3) Advantage magazine articles, (4) Knowledge Base (WordPress/ECKB), (5) DWC-Course (Docusaurus MDX), (6) BBj source code samples.
- **Flare access:** Engineers have both Flare project access (raw XHTML with MadCap namespace tags) and the live site (crawl fallback). Both paths implemented as parsers.
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
| Lowercase Visual PRO/5 examples matching PDF reference | `print`/`open`/`ctrl` in code blocks matches authoritative source style | ✓ Good |
| General documentation.basis.cloud URL for PDF reference | More resilient than deep-linking specific PDF path | ✓ Good |
| Tailwind blue-600 scale for brand palette | Matches reference project (bbj-dwc-tutorial); tested shade progression | ✓ Good |
| No srcDark navbar logo variant | DWC logo has dark background with white icon; works in both modes | ✓ Good |
| Infima default typography (no custom fonts) | Clean sans-serif matches reference project; no BASIS font spec exists | ✓ Good |

| Python ingestion sub-project as mono-repo directory | Keeps scripts co-located with strategy docs until ready for CI/CD | ✓ Good |
| Both Flare export and crawl ingestion paths | Engineers may or may not have Flare project access; crawl is fallback | ✓ Good |
| hatchling build backend for src-layout | Stable src-layout support vs uv_build which was experimental | ✓ Good |
| Qwen3-Embedding-0.6B via Ollama (1024 dims) | Local inference, no API costs; 0.6B params balances quality and speed | ✓ Good |
| Multi-signal generation tagging (path + condition + content) | Single signal insufficient for BBj's complex documentation corpus | ✓ Good |
| Binary COPY via staging table for bulk inserts | psycopg3 COPY protocol with ON CONFLICT dedup for performance + idempotency | ✓ Good |
| Pipeline intelligence bypass for non-Flare parsers | Non-Flare parsers pre-populate doc_type/generations; avoids Flare-specific logic | ✓ Good |
| 400-token chunks with 50-token overlap | Heading-aware splitting preserves semantic coherence at section boundaries | ✓ Good |

---
*Last updated: 2026-02-01 after v1.2 milestone*
