# Project Research Summary

**Project:** BBj AI Strategy Documentation Site - v1.2 RAG Ingestion Pipeline
**Domain:** Multi-source RAG ingestion for technical documentation (niche programming language)
**Researched:** 2026-01-31
**Confidence:** HIGH

## Executive Summary

The BBj AI Strategy project adds a Python-based RAG ingestion pipeline in milestone v1.2 to process five distinct source types into a generation-aware vector database. This is not a generic RAG pipeline—the core differentiator is **generation tagging**, which classifies every chunk of documentation by which BBj generation it applies to (character UI, Visual PRO/5, BBj GUI/Swing, DWC/browser, or cross-generation). Without this, the RAG system would confidently return 1990s Visual PRO/5 syntax when a developer asks for modern DWC patterns—syntactically valid but semantically wrong code.

The recommended approach uses direct library usage (BeautifulSoup, PyMuPDF, sentence-transformers, psycopg3) rather than heavyweight RAG frameworks (LangChain/LlamaIndex), because this is a batch ETL pipeline, not a runtime query system. The stack is optimized for correctness and maintainability: **MadCap Flare Clean XHTML export** (not web crawling) as the primary source, **Qwen3-Embedding-0.6B** for self-hosted embeddings (Apache 2.0, code-aware, 32K context), **chonkie** for document-type-aware chunking, and **pgvector with HNSW indexing** for hybrid retrieval (vector + BM25). The pipeline is built as a standalone Python sub-project (`rag-ingestion/`) within the existing Docusaurus repo, with zero build dependencies between the two.

The critical risk is **generation mistagging**, which produces confidently wrong answers. The BBj GUI programming guide PDF becomes the Rosetta Stone for building classification rules—it contains complete working examples across all four generations with clear labels. Additional risks include MadCap Flare proprietary markup contamination (mitigated by using Clean XHTML export), PDF extraction losing tables and code blocks (mitigated by using pymupdf4llm), and WordPress content being invisible to static HTTP scrapers (mitigated by using Crawl4AI with Playwright or the WordPress REST API).

## Key Findings

### Recommended Stack

**Runtime:** Python 3.12+ with **uv** for package management (10-100x faster than pip, native lockfile support, the 2026 standard). Direct library usage, not framework-based—no LangChain/LlamaIndex because this is a batch pipeline, not a runtime orchestration system.

**Core technologies:**
- **lxml 5.x**: XHTML/XML parsing — 11x faster than BeautifulSoup for well-formed Flare Clean XHTML, native XPath support for namespace-heavy content
- **pymupdf4llm (latest)**: PDF extraction — purpose-built for RAG, outputs Markdown with structure preservation (headers, tables, code blocks), released Jan 2026
- **crawl4ai 0.8.x**: Web crawling — LLM-optimized Markdown extraction with JavaScript rendering via Playwright, strips navigation/boilerplate automatically
- **python-frontmatter 1.1.0 + markdown-it-py 3.x**: MDX parsing — handles Docusaurus MDX with frontmatter extraction and JSX stripping
- **chonkie 1.5.x**: Text chunking — 9 chunking strategies including RecursiveChunker (docs), SemanticChunker (prose), CodeChunker (BBj samples), native pgvector integration
- **Qwen3-Embedding-0.6B (Apache 2.0)**: Embedding model — 600M params, 1024 dims, 32K context, code + text aware, ~4GB VRAM, competitive with 7B models on MTEB
- **sentence-transformers >=2.7.0**: Embedding inference — standard Python framework for local models, batch encoding optimized for GPU/CPU
- **psycopg3 + pgvector 0.4.2**: PostgreSQL driver + vector types — async-capable, binary COPY for fast bulk inserts, native vector type registration
- **pydantic 2.x + typer + rich**: Configuration, CLI, terminal output — type-safe config, multi-command CLI, progress bars for long embedding runs

**Why NOT LangChain/LlamaIndex:** These are retrieval + generation frameworks designed for query-time workflows, not batch ingestion. They add 100+ transitive dependencies to wrap the same underlying libraries (BeautifulSoup, PyMuPDF, sentence-transformers). For a focused ETL pipeline with 5 known source types and a single vector store, direct library usage is simpler, faster, and more maintainable.

**Why Qwen3-Embedding-0.6B over alternatives:**
- BGE-M3 (568M params, 1024 dims): Strong but 8K context limit may truncate long Flare pages, no explicit code training emphasis
- Nomic Embed Text v2 (300M active): 8K context limit, less code-aware
- EmbeddingGemma-300M: More restrictive Gemma license than Apache 2.0, newer with less production validation
- All-MiniLM-L6-v2: Too small (384 dims, 56.3 MTEB) for production quality

### Expected Features

Research identifies three feature categories: table stakes (must-have), differentiators (BBj-specific intelligence), and anti-features (deliberately excluded).

**Must have (table stakes):**
- **XHTML/HTML parsing for MadCap Flare output** — primary corpus; must extract text from semantic elements while stripping markup
- **Heading hierarchy extraction** — section headings form contextual headers for chunks (FinanceBench showed 83% vs. 19% baseline with contextual chunk headers)
- **PDF text extraction** — standalone PDFs are a defined source type
- **Document-type-aware chunk sizing** — API refs 200-400 tokens, concepts 400-600 tokens, per Chapter 6 design
- **Contextual chunk headers (CCH)** — prepend section hierarchy to each chunk before embedding (highest-ROI generic RAG feature)
- **Code block integrity** — never split code examples across chunks; BBj functions split in half are useless
- **Embedding generation via local model** — self-hostable per enterprise data policy
- **pgvector schema creation** — table with vector column, metadata columns, tsvector for BM25 hybrid search
- **HNSW index creation** — built after bulk insertion for approximate nearest neighbor search
- **Content hashing for idempotent ingestion** — re-runs must not create duplicates; engineers will run pipeline multiple times during development
- **Source URL tracking** — every chunk links back to source for citation

**Should have (differentiators - BBj-specific):**
- **Automatic generation classification** — tag every chunk with `all`, `character`, `vpro5`, `bbj-gui`, or `dwc` based on API names, syntax patterns, file paths (the defining feature)
- **Multi-generation tag support** — single chunk can apply to multiple generations; PostgreSQL array column with GIN indexing
- **Document type classification** — classify as api-reference, concept, example, migration, language-reference, best-practice, or version-note to drive chunk sizing
- **MadCap Flare TOC-aware parsing** — use TOC structure to maintain hierarchical relationships, providing the "Section > Subsection" breadcrumbs for contextual headers
- **BBj code block preservation** — detect BBj syntax patterns (REM, LET, PRINT, sysgui!, BBj* classes) and preserve as atomic units

**Defer (v2+, anti-features for starter kit):**
- **CI/CD automated re-ingestion** — v1.2 is a starter kit, not production infrastructure; manual CLI invocation is sufficient
- **Incremental ingestion** — full re-ingestion with idempotent upserts is fast enough at ~50K chunks
- **Docker/container packaging** — assumes deployment target; starter kit runs on engineer's machine
- **Embedding fine-tuning** — Chapter 6 explicitly defers this until baseline pipeline is operational
- **LLM-assisted chunk summarization** — contextual chunk headers provide most of the same benefit deterministically
- **Retrieval API server** — ingestion writes to pgvector; building FastAPI retrieval is a separate project
- **Automated web crawling with link discovery** — curated URL lists per source type; Flare uses Clean XHTML export (file system, not crawl)

### Architecture Approach

The pipeline is a standalone Python sub-project (`rag-ingestion/`) within the existing Docusaurus repo, sharing git history but zero build dependencies. Two completely independent toolchains: npm/Node.js for the docs site, uv/Python for ingestion. The only connection is documentation—the new `docs/06-rag-database/getting-started.md` page links to scripts/config files via absolute GitHub URLs (Docusaurus cannot resolve links outside `docs/`).

**Pipeline data flow:**
```
Source Acquisition → Enrichment Pipeline → Embedding + Storage

1. Source Acquisition (5 source-specific parsers)
   - Flare Clean XHTML: lxml with XPath, strip MC namespace
   - PDFs: pymupdf4llm for Markdown output
   - WordPress (Advantage + KB): Crawl4AI with Playwright OR REST API
   - Docusaurus MDX (DWC-Course): frontmatter + markdown-it-py + JSX stripping
   - BBj code samples: plain text with generation tagging logic
   → Produces: List[Document] (Pydantic models)

2. Enrichment Pipeline
   - Generation Tagger: assigns generation labels based on API names, syntax patterns
   - Doc-Type Classifier: classifies as api-reference, concept, example, etc.
   - Chunker: document-type-aware sizing, contextual headers, 10-15% overlap, code block protection
   → Produces: List[Chunk]

3. Embedding + Storage
   - Embedder: sentence-transformers with Qwen3-Embedding-0.6B, batch processing
   - Storage: psycopg3 bulk insert via COPY protocol, pgvector registration
   → Produces: PostgreSQL/pgvector table with embeddings, metadata, tsvector
```

**Major components:**
1. **Parsers (`parsers/`)** — 5 source-specific parsers implementing common `BaseParser` interface, all output `Document` objects
2. **Pipeline (`pipeline/`)** — tagger.py (generation classification), chunker.py (type-aware splitting), embedder.py (batch embedding)
3. **Storage (`storage/`)** — schema.sql (pgvector table DDL), db.py (connection + operations), migrate.py (schema creation)
4. **CLI (`cli.py`)** — typer-based multi-command CLI orchestrating full pipeline with rich progress bars

**Database schema:** Single denormalized table (not document + chunks) at ~50K scale. Includes: vector(1024) for embeddings, TEXT[] for multi-generation tags, tsvector GENERATED column for BM25, HNSW index with cosine similarity, GIN indexes on generation/source_type/doc_type, unique constraint on content hash for deduplication.

**Build order:** (1) Schema + models, (2) Flare parser (primary source, validates full pipeline), (3) Chunker + tagger (BBj-specific intelligence), (4) Embedder + storage (completes end-to-end for one source), (5) Additional parsers, (6) Documentation page.

### Critical Pitfalls

Research identified 16 pitfalls across 3 severity levels. Top 5 critical pitfalls that require rewrites if missed:

1. **Generation Mistagging Produces Confidently Wrong Answers** — A Visual PRO/5 chunk tagged as DWC means retrieval returns 1990s syntax for modern queries. Trust collapses after a few wrong-generation responses. **Prevention:** Build dedicated generation classifier as pipeline stage; use BBj GUI programming PDF as Rosetta Stone for API signatures; chunk at generation boundaries for multi-generation pages; require generation as retrieval filter (not just boost); build evaluation set with generation-boundary queries. **Phase:** Schema/architecture design, validated before any other features.

2. **MadCap Flare Proprietary Markup Contaminates Chunks** — Flare XHTML contains extensive `MadCap:*` namespace elements/attributes. Generic HTML parsing embeds invisible metadata noise that dilutes semantic signal. Clean XHTML export strips most MadCap tags but web crawl preserves them. **Prevention:** Prefer Clean XHTML export over web crawl; strip all `MadCap:*` and `data-mc-*` attributes, `MC` CSS classes; use headless browser for web crawl to expand dropdowns/togglers; extract from topic content container only, ignore navigation. **Phase:** Flare parser implementation (must be first parser built).

3. **PDF Extraction Silently Loses Tables, Code Blocks, and Formatting** — Basic PDF libraries (PyPDF2, pdfplumber) mangle code examples, flatten tables into nonsense, interleave multi-column layouts. BBj GUI programming guide contains multi-generation code samples and comparison tables that degrade catastrophically. **Prevention:** Use layout-aware parser (pymupdf4llm rated 10/10 for RAG); detect monospace font regions for code blocks; strip repeating headers/footers; use table-aware extractor preserving row/column structure; validate 5 sample pages manually before full pipeline run. **Phase:** PDF parser implementation (prototype first to validate tool selection).

4. **Chunking Destroys Code Example Integrity** — Standard text splitters cut BBj code mid-function/class. Retrieved code is syntactically broken; LLM hallucinates completions. **Prevention:** Structure-aware splitter treats code blocks as atomic units; if code block exceeds chunk size, include as standalone chunk with preceding description; detect BBj code via `REM`, `LET`, `PRINT`, `sysgui!`, `BBj*` patterns; two-pass chunking (extract protected code regions, chunk narrative, reassemble); set minimum chunk size to 400-800 tokens. **Phase:** Chunking pipeline implementation, tested with actual BBj samples before production.

5. **WordPress/LearnPress Content Is Invisible to HTTP Scrapers** — WordPress sites render content via JavaScript/AJAX; `requests.get()` returns page shell but not lesson/article content. Pipeline appears to succeed but chunks contain only navigation boilerplate. **Prevention:** Use headless browser (Crawl4AI with Playwright); wait for content-specific selectors before extraction; strip WordPress chrome (nav, sidebars, footers); check WordPress REST API (`/wp-json/wp/v2/posts`) as cleaner path than scraping; validate extraction length against visible browser content. **Phase:** WordPress parser implementation (test approach early—REST API changes entire strategy).

## Implications for Roadmap

Based on research, v1.2 should be structured as 5-6 sequential phases building the pipeline incrementally, with Flare parsing as the critical path and generation tagging as the make-or-break feature.

### Suggested Phase Structure

**Phase 1: Schema + Core Infrastructure**
- **Rationale:** Establishes contracts before any code is written. pgvector schema, Pydantic models, and database connection must exist before parsers can output data.
- **Delivers:** `pyproject.toml`, `models.py` (Document/Chunk/EmbeddedChunk), `schema.sql`, `db.py`, `migrate.py`, `setup_db.sh` script
- **Addresses:** pgvector schema creation, content hashing for idempotent ingestion, source URL tracking
- **Avoids:** Embedding model lock-in (dimension configurable from day one), pgvector index misconfiguration (document index creation as separate post-load step)
- **Research flag:** STANDARD PATTERNS — established PostgreSQL/pgvector setup, no deep research needed

**Phase 2: Flare Parser (Primary Source)**
- **Rationale:** MadCap Flare docs are the largest, most complex source and the highest-value corpus. Getting this right validates the entire pipeline architecture. Implements both Clean XHTML export path (preferred) and web crawl fallback.
- **Delivers:** `parsers/base.py`, `parsers/flare.py`, test fixtures, validation against 10 sample topics
- **Addresses:** XHTML parsing, heading hierarchy extraction, MadCap namespace stripping
- **Avoids:** Proprietary markup contamination (Pitfall #2), Flare dropdown content structure loss, TOC-excluded topics leaking into corpus
- **Research flag:** NEEDS RESEARCH — Complex two-path implementation (Clean XHTML vs. crawl), MadCap-specific cleanup, dynamic site crawling patterns

**Phase 3: Generation Tagger + Document Classifier**
- **Rationale:** This is the BBj-specific intelligence layer that makes the pipeline valuable. Without it, this is a generic RAG pipeline. Generation tagging determines pipeline success. Document type drives chunk sizing.
- **Delivers:** `pipeline/tagger.py` (generation classification signals from BBj GUI programming PDF), `pipeline/chunker.py` (type-aware sizing), evaluation query set (30 queries with generation-boundary tests)
- **Addresses:** Automatic generation classification, multi-generation tag support, document type classification, chunk size variation by type
- **Avoids:** Generation mistagging (Pitfall #1 — the most critical failure mode)
- **Research flag:** NEEDS RESEARCH — Domain-specific BBj generation detection, API signature extraction from PDF, classification rule heuristics

**Phase 4: Chunking Pipeline**
- **Rationale:** Implements contextual chunk headers (highest-ROI generic RAG feature per FinanceBench), code block protection, and document-type-aware sizing. Depends on document type classifier from Phase 3.
- **Delivers:** Enhanced `pipeline/chunker.py` with CCH, code block integrity, token-aware splitting, overlap management
- **Addresses:** Contextual chunk headers, chunk overlap, token-aware splitting, code block integrity
- **Avoids:** Chunking destroys code examples (Pitfall #4), cross-references become dead links
- **Research flag:** STANDARD PATTERNS — Established RAG chunking techniques, well-documented chonkie library usage

**Phase 5: Embedder + Storage (End-to-End for Flare)**
- **Rationale:** Completes full pipeline for one source type (Flare). Enables end-to-end testing and retrieval validation before adding breadth with other sources.
- **Delivers:** `pipeline/embedder.py` (sentence-transformers + Qwen3-Embedding-0.6B), `cli.py` orchestration, `config/sources.toml`, HNSW index creation, query example script
- **Addresses:** Embedding generation via local model, batch embedding with progress, chunk insertion with metadata, full-text search vector column, HNSW index
- **Avoids:** Embedding model lock-in (model name in config), index misconfiguration (HNSW with cosine similarity, built after data load)
- **Research flag:** STANDARD PATTERNS — sentence-transformers batch encoding, psycopg3 COPY protocol, pgvector HNSW indexing

**Phase 6: Additional Parsers (Breadth)**
- **Rationale:** Add remaining 4 sources in value/complexity order. Each parser plugs into existing pipeline (same Document model, same enrichment stages).
- **Delivers:**
  - `parsers/pdf.py` (pymupdf4llm for GuideToGuiProgrammingInBBj.pdf)
  - `parsers/wordpress.py` (Crawl4AI or REST API for Advantage + Knowledge Base)
  - `parsers/docusaurus.py` (frontmatter + markdown-it-py for DWC-Course)
  - `parsers/bbj_code.py` (plain text with BBj syntax detection)
- **Addresses:** PDF extraction, WordPress scraping, MDX parsing, BBj code preservation
- **Avoids:** PDF extraction loses tables/code (Pitfall #3), WordPress content invisible to scrapers (Pitfall #5), MDX parsing strips JSX components (Pitfall #9)
- **Research flag:** NEEDS RESEARCH for WordPress (REST API availability, LearnPress structure); STANDARD for PDF/MDX/code

**Phase 7: Documentation + Quality (Optional Extension)**
- **Rationale:** Document completed pipeline and validate quality with evaluation queries.
- **Delivers:** `docs/06-rag-database/getting-started.md`, post-ingestion summary report, generation tag distribution analysis, orphan detection
- **Addresses:** Pipeline documentation, quality reporting, evaluation framework
- **Avoids:** No evaluation framework (Pitfall #10)
- **Research flag:** STANDARD — Documentation writing, SQL reporting queries

### Phase Ordering Rationale

- **Schema first:** All downstream code depends on data models and database schema. Defining these as contracts prevents mid-flight schema changes.
- **Flare before other sources:** Flare is the primary corpus (largest volume, highest complexity). Getting Flare right validates the entire architecture. Other parsers are simpler in comparison.
- **Tagging/classification before chunking:** Document type determines chunk size; generation tags are metadata on chunks. Both must exist before chunking runs.
- **One source end-to-end before breadth:** Completing Flare → parse → tag → chunk → embed → store enables retrieval testing and quality validation before adding the other 4 sources. This prevents building 5 parsers before discovering the chunking or embedding strategy is wrong.
- **Documentation last:** Documenting what was built, not what might be built. The getting-started page reflects the actual implementation.

### Research Flags

**Needs deeper research during phase planning:**
- **Phase 2 (Flare parser):** MadCap Clean XHTML vs. web crawl trade-offs, dynamic site structure, TOC parsing for hierarchy
- **Phase 3 (Generation tagger):** BBj generation classification heuristics, API signature extraction from programming guide PDF
- **Phase 6 (WordPress parser):** WordPress REST API availability, LearnPress LMS content structure, dynamic content loading

**Standard patterns (skip research-phase):**
- **Phase 1 (Schema):** PostgreSQL schema design, pgvector setup, Pydantic models
- **Phase 4 (Chunking):** Contextual chunk headers, text splitting with overlap, code block detection
- **Phase 5 (Embedder):** sentence-transformers batch encoding, pgvector HNSW indexing
- **Phase 6 (PDF/MDX/code parsers):** pymupdf4llm usage, frontmatter extraction, file I/O

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | All libraries verified on PyPI/GitHub with 2026-01-31 versions. Qwen3-Embedding-0.6B benchmarks confirmed on HuggingFace. psycopg3 + pgvector integration documented in official examples. |
| Features | **HIGH** | Chapter 6 design (generation taxonomy, document types, chunk sizes) provides explicit feature requirements. Table stakes vs. differentiators validated against RAG best practices from multiple sources. Anti-features clearly bounded by "starter kit" scope. |
| Architecture | **HIGH** | Directory structure, data flow, and component boundaries verified against uv project standards and Docusaurus monorepo patterns. Database schema matches pgvector documentation. Single-table design appropriate for <50K chunks. |
| Pitfalls | **MEDIUM-HIGH** | MadCap Flare and pgvector pitfalls verified with official docs (HIGH confidence). PDF extraction and WordPress scraping pitfalls verified with multiple 2025-2026 sources (MEDIUM confidence). Generation tagging pitfalls are domain-specific extrapolation from version management research (MEDIUM confidence but critical impact). |

**Overall confidence:** HIGH

The research is grounded in verified technical documentation (MadCap Flare Clean XHTML specs, pgvector GitHub, sentence-transformers PyPI, pymupdf4llm benchmarks), current web sources (all dated 2025-2026), and the existing Chapter 6 design document which provides explicit requirements. The weakest area is generation tagging heuristics, which are BBj-specific and cannot be verified against external sources—but the BBj GUI programming guide PDF provides the ground truth for building classification rules.

### Gaps to Address

**During Phase 2 (Flare parser):**
- **Gap:** MadCap Flare TOC file format (`.fltoc`) is described conceptually but not verified against actual export. May need to inspect actual TOC XML structure.
- **Handling:** Prototype with actual Flare export from engineering team. If TOC parsing is too complex, fall back to heading-based hierarchy inference.

**During Phase 3 (Generation tagger):**
- **Gap:** BBj generation classification signals are inferred from documentation patterns and the GUI programming guide, but not validated against complete API inventories per generation.
- **Handling:** Build initial classifier with known API patterns (e.g., `sysgui!` = vpro5/bbj-gui, `BBjWindow` = bbj-gui/dwc, `PRINT @(x,y)` = character). Tag ambiguous cases as `all` (conservative default). Refine with manual review of generated tag distribution during Phase 7.

**During Phase 6 (WordPress parser):**
- **Gap:** WordPress REST API availability for `basis.cloud/knowledge-base/` and `basis.cloud/advantage-index/` is assumed but not confirmed.
- **Handling:** Test REST API endpoints (`/wp-json/wp/v2/posts`, `/wp-json/lp/v1/`) as first step of Phase 6. If API is disabled or returns excerpts only, fall back to Crawl4AI with Playwright.

**During Phase 5 (Embedder):**
- **Gap:** Optimal chunk size and overlap for BBj documentation (API refs vs. prose vs. code) needs empirical validation.
- **Handling:** Start with Chapter 6 recommendations (API: 200-400 tokens, concept: 400-600 tokens, 10-15% overlap). After initial ingestion, run evaluation queries and tune based on retrieval quality metrics.

## Sources

### Primary (HIGH confidence)
- Chapter 6: RAG Database Design (`/docs/06-rag-database/index.md`) — schema, chunking strategy, generation taxonomy, retrieval architecture
- [MadCap Flare Clean XHTML Blog Post](https://www.madcapsoftware.com/blog/new-feature-highlight-clean-xhtml-output-madcap-flare-2017/) — Clean XHTML stripping behavior
- [MadCap Flare Clean XHTML Official Docs](https://help.madcapsoftware.com/flare2021r2/Content/Flare/Step4-Developing-Targets/Output-Types/Clean-XHTML/Clean-XHTML-Output.htm) — What gets stripped vs. preserved
- [Qwen3-Embedding Blog Post](https://qwenlm.github.io/blog/qwen3-embedding/) — Official benchmarks, architecture details
- [Qwen3-Embedding-0.6B HuggingFace](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) — Model card, usage examples, version requirements
- [pgvector-python GitHub](https://github.com/pgvector/pgvector-python) — Version 0.4.2, driver support, usage examples (Jan 22, 2026)
- [chonkie GitHub](https://github.com/chonkie-inc/chonkie) — Chunking strategies, pgvector integration, version 1.5.2 (Jan 5, 2026)
- [pymupdf4llm PyPI](https://pypi.org/project/pymupdf4llm/) — Latest release Jan 10, 2026, RAG-focused PDF extraction
- [sentence-transformers PyPI](https://pypi.org/project/sentence-transformers/) — Model loading, batch encoding
- [uv Project Docs](https://docs.astral.sh/uv/guides/projects/) — pyproject.toml setup, dependency management

### Secondary (MEDIUM confidence)
- [BentoML Open Source Embedding Models Guide 2026](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models) — Embedding model landscape
- [Snowflake FinanceBench](https://www.snowflake.com/en/engineering-blog/impact-retrieval-chunking-finance-rag/) — Contextual chunk headers (83% vs. 19% baseline)
- [Firecrawl Best Chunking Strategies RAG 2025](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025) — 400-token chunks, 10-20% overlap, variable sizing 9% improvement
- [crawl4ai Documentation](https://docs.crawl4ai.com/) — Deep crawling, Markdown generation, content filtering
- [FlareToSphinx GitHub](https://github.com/boltzmann-brain/FlareToSphinx) — Prior art for Python-based Flare parsing
- [Unstract PDF Library Benchmarks 2026](https://unstract.com/blog/evaluating-python-pdf-to-text-libraries/) — PyMuPDF vs. pdfplumber benchmarks
- [LlamaParse RAG Benchmarks 2025](https://infinityai.medium.com/3-proven-techniques-to-accurately-parse-your-pdfs-2c01c5badb84) — LlamaParse 10/10 for RAG
- [ICCV 2025: OCR Hinders RAG](https://openaccess.thecvf.com/content/ICCV2025/papers/Zhang_OCR_Hinders_RAG_Evaluating_the_Cascading_Impact_of_OCR_on_ICCV_2025_paper.pdf) — OCR noise degrades retrieval
- [AWS Blog: pgvector HNSW vs IVFFlat](https://aws.amazon.com/blogs/database/optimize-generative-ai-applications-with-pgvector-indexing-a-deep-dive-into-ivfflat-and-hnsw-techniques/) — Index comparison
- [Nile: Debunking pgvector Myths](https://www.thenile.dev/blog/pgvector_myth_debunking) — Index not always needed, distance operator matching

### Tertiary (LOW confidence, needs validation)
- WordPress REST API availability for `basis.cloud/knowledge-base/` — assumed based on WordPress standard, not verified
- Advantage article count (~6 visible on index page, may have more behind pagination)
- BBj generation classification signals — inferred from documentation patterns, not validated against complete API inventory

---
*Research completed: 2026-01-31*
*Ready for roadmap: yes*
