# BBj AI Strategy Documentation Site

## What This Is

A public Docusaurus site that communicates BASIS International's AI strategy for BBj — covering LLM fine-tuning, IDE integration, documentation chat, and RAG database design — plus a running Docker-based RAG system that ingests all 6 BBj documentation sources (50,439 chunks) into pgvector and serves hybrid retrieval via REST API and MCP server (`search_bbj_knowledge`). The site serves three audiences (internal developers, leadership, customers/partners) through 7 researched chapters with full-text search, professional content patterns, BASIS brand identity, and automated deployment. The RAG pipeline bridges strategy documentation with executable code — from documentation source ingestion through to Claude Desktop integration. Live at https://stephanwald.github.io/bbj-ai-strategy/.

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

- ✓ Chapter 2 updated with MCP server as the concrete unified architecture — three tool definitions, generate-validate-fix loop, deployment options — v1.3
- ✓ Chapter 4 updated with compiler validation module and bbjcpltool proof-of-concept — ground-truth syntax checking as AI feedback loop — v1.3
- ✓ Chapter 5 updated with MCP-based RAG search tool definition and two-path architecture (MCP access + embedded chat) — v1.3
- ✓ Chapters 3, 6, 7 updated with cross-references to MCP orchestration and revised status — v1.3
- ✓ All new BBj code samples compiler-validated before publishing (17 blocks via bbjcpl -N) — v1.3

- ✓ Docker Compose orchestration (pgvector 0.8.0-pg17 + Python app) with schema auto-init, Ollama connectivity, env-based config — v1.4
- ✓ TOML source configuration for 9 entries across 7 parser types with bbj-ingest-all CLI (resume, clean, source-filter) — v1.4
- ✓ REST API: POST /search (hybrid RRF + generation filtering), GET /stats, GET /health (pool-based readiness) — v1.4
- ✓ MCP server: search_bbj_knowledge tool via stdio transport for Claude Desktop with LLM-optimized text responses — v1.4
- ✓ Full corpus ingested: 50,439 chunks across 6 source groups, validated via 17-query E2E test suite — v1.4
- ✓ End-to-end validation script + VALIDATION.md report proving both REST API and MCP interfaces operational — v1.4

### Active

**Current Milestone: v1.5 Alpha-Ready RAG System**

**Goal:** Make the RAG system usable by engineers for peer review — fast rebuilds, quality results with source citations, compiler-validated BBj code, a web chat interface backed by Claude API, and remote access for shared server deployment.

**Target features:**
- Concurrent ingestion workers and persistent HTTP connection reuse (carried-forward performance debt)
- Source-balanced ranking to surface minority sources (PDF, BBj Source) alongside Flare-dominated results
- source_url mapped to clickable HTTP links (flare:// → documentation.basis.cloud/...)
- bbjcpl compiler integration for syntactic validation of BBj code in RAG responses
- Web chat interface with Claude API for answer generation, RAG-grounded responses with source citations
- Remote access: shared server deployment (MCP over network, chat UI accessible by team)

### Out of Scope

- Authentication or access control — internal alpha; engineers on trusted network
- Mobile-optimized design beyond Docusaurus defaults — standard responsive is sufficient
- Internationalization — English only
- Embedding fine-tuning — requires baseline retrieval quality measurement first
- Agentic RAG features — no query routing, agent loops, or multi-step reasoning
- MCP `generate_bbj_code` tool — requires fine-tuned BBj model (separate milestone)
- Cloud/production hosting — v1.5 targets shared server on local network, not cloud
- CI/CD pipeline for ingestion — manual trigger is sufficient for v1.5
- Chat history persistence — alpha phase, no need to save conversations
- User accounts or multi-tenancy — single shared instance for internal team

## Context

- **Source material:** `bbj-llm-strategy.md` — original strategy paper (~1100 lines). Each chapter was researched independently and rewritten, not just ported.
- **BBj:** Business BASIC for Java by BASIS International. Spans 4 generations: character UI (1980s), Visual PRO/5 (1990s), BBj GUI/Swing (2000s), DWC/browser (2010s+). Extremely niche — LLMs have near-zero training data on it.
- **The core problem:** Generic LLMs hallucinate BBj code because BBj is too rare in training data. The strategy addresses this through fine-tuning, RAG, and generation-aware tooling.
- **Three initiatives:** Fine-tuned BBj model (via Ollama), VSCode extension with Langium integration, documentation chat system — all sharing unified infrastructure.
- **Audiences:** Internal developers (implementation detail), leadership (strategy/ROI), customers/partners (capability awareness).
- **webforJ context:** BASIS also has webforJ (Java-based web framework) where generic LLMs work fine because they know Java. BBj is the unique challenge.
- **Current state:** v1.4 shipped 2026-02-02. RAG system running via Docker Compose — 50,439 chunks from all 6 sources, REST API at localhost:10800, MCP server for Claude Desktop. v1.5 targets alpha readiness for engineer peer review. Tech stack: Docusaurus 3.9.2, Rspack, GitHub Actions, GitHub Pages + Python 3.12, uv, pgvector 0.8.0-pg17, psycopg3, FastAPI, Ollama (Qwen3-Embedding-0.6B), MCP SDK v1.x. 3,015 lines docs content + ~8,000 lines Python source + 329+ tests passing. Site live at stephanwald.github.io/bbj-ai-strategy.
- **Alpha testers:** Internal BASIS engineers with BBj installed locally. Most will access via shared server; some may run locally. Engineers have Claude Desktop/Code access and bbjcpl available on their machines.
- **Source data inventory (v1.4):** Flare project at `/Users/beff/bbjdocs/` (7,087 .htm topics), PDF at project root, 3 MDX tutorial sites (DWC, beginner, DB modernization — 98 .md files), BBj source code in SVN checkout + tutorial samples (1,363+ .bbj files), WordPress articles at basis.cloud (HTTP), documentation.basis.cloud for web crawl (HTTP).
- **MCP concept paper:** Draft architecture for BBj AI Development Assistant — MCP server orchestrating RAG search, fine-tuned code model, and compiler validation. Key innovation: generate-validate-fix loop using BBj compiler as ground truth.
- **bbjcpltool:** Working proof-of-concept at `/Users/beff/bbjcpltool/` — v1 shipped. PostToolUse hook runs `bbjcpl -N` on every `.bbj` file Claude writes/edits, plus shared BBj language reference at `~/.claude/bbj-reference.md`. Validates the compiler-in-the-loop concept described in the MCP paper.
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

| MCP architecture woven into existing chapters (not standalone Ch8) | MCP is the integration layer connecting Ch3-6, not a separate initiative; fits as the concrete realization of Ch2's unified architecture promise | ✓ Good |
| MCP topology diagram replaces original two-layer architecture diagram | MCP Server sits between clients and backends; original conceptual flow preserved in "How They Work Together" sequence diagram | ✓ Good |
| JSON Schema format for MCP tool definitions | Language-neutral, matches MCP spec native format; avoids premature TypeScript/Python commitment | ✓ Good |
| Compiler validation as quality gate, not "third layer" | Preserves existing Two-Layer Completion Architecture decision; bbjcpl validates LLM output | ✓ Good |
| Chat and MCP as two independent, equally important paths | Not a stepping stone; both paths consume same BBj MCP Server backend | ✓ Good |
| No MCP tool schemas duplicated across chapters | All downstream chapters cross-reference Ch2 definitions; single source of truth | ✓ Good |
| Status block dates removed permanently | :::note[Where Things Stand] with no month/year; avoids staleness across deployments | ✓ Good |

| Docker Compose for RAG deployment | Self-contained local deployment; pgvector + app in single `docker compose up` | ✓ Good |
| Host Ollama (not containerized) | Avoid duplicating large Ollama container; host already runs it with Metal GPU | ✓ Good |
| REST API + thin MCP server | Clean separation: API serves retrieval, MCP wraps it for LLM clients | ✓ Good |
| Python for MCP server | MCP server consumes same retrieval logic as API; avoids cross-language boundary | ✓ Good |
| uv 0.9.28 pinned in Dockerfile | Matches local install; deterministic builds | ✓ Good |
| External ports above 10000 (10800 app, 10432 db) | Avoids conflicts with common development ports | ✓ Good |
| sources.toml with DATA_DIR env var resolution | Blank data_dir in TOML; resolved via Docker DATA_DIR=/data at runtime | ✓ Good |
| Sequential ingestion (parallel deferred) | Proven reliable; GPU saturation optimization deferred to future milestone | ✓ Good |
| Lightweight keyword heuristics for E2E validation | Human-reviewable snippets; automated pass/fail without complex NLP | ✓ Good |

---
*Last updated: 2026-02-03 after v1.5 milestone started*
