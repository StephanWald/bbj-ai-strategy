# Roadmap: BBj AI Strategy v1.2 -- RAG Ingestion Pipeline

## Overview

This milestone bridges the gap between Chapter 6's strategic RAG design and actual implementation by delivering a Python-based ingestion pipeline that processes five BBj documentation sources into a generation-aware pgvector database. The work progresses from project scaffolding and schema contracts, through the primary Flare parser, BBj-specific intelligence (the make-or-break generation tagger), embedding pipeline, additional source parsers, and finally documentation and quality validation. Phases 8-14 continue from v1.1's Phase 7.

## Milestones

- v1.0 Documentation Site (Phases 1-5) -- shipped 2026-01-31
- v1.1 Code Corrections & Branding (Phases 6-7) -- shipped 2026-01-31
- **v1.2 RAG Ingestion Pipeline (Phases 8-14) -- in progress**

## Phases

- [x] **Phase 8: Project Scaffold & README** - Python sub-project setup and repo README
- [x] **Phase 9: Schema & Data Models** - pgvector DDL, Pydantic models, config system, deduplication
- [x] **Phase 10: Flare Parser** - MadCap Flare XHTML parser (project files + condition tags + crawl fallback)
- [ ] **Phase 11: BBj Intelligence** - Generation tagger, document type classifier, contextual chunk headers
- [ ] **Phase 12: Embedding Pipeline** - Embedding model, pgvector storage, hybrid search validation (end-to-end for Flare)
- [ ] **Phase 13: Additional Parsers** - PDF, WordPress/Advantage, WordPress/KB, Docusaurus MDX, BBj source code
- [ ] **Phase 14: Documentation & Quality** - Getting Started page, sub-project README, ingestion quality reports

## Phase Details

### Phase 8: Project Scaffold & README
**Goal**: Engineers can clone the repo and find a working Python project structure alongside the docs site, with a clear repo README explaining the whole project
**Depends on**: Phase 7 (v1.1 complete)
**Requirements**: DOC-01, INFRA-01
**Success Criteria** (what must be TRUE):
  1. Repo README at project root describes the project, links to the live site, and summarizes the tech stack
  2. Running `uv sync` in `rag-ingestion/` installs all dependencies without errors
  3. The `rag-ingestion/` directory has a valid `pyproject.toml` with Python 3.12+ requirement and all core dependencies declared
**Plans**: 1 plan

Plans:
- [x] 08-01-PLAN.md -- Scaffold rag-ingestion/ Python project with uv and write repo README

### Phase 9: Schema & Data Models
**Goal**: The database schema and data contracts are defined so all downstream parsers, taggers, and embedders work against stable interfaces
**Depends on**: Phase 8
**Requirements**: INFRA-02, INFRA-03, INFRA-04, INFRA-05
**Success Criteria** (what must be TRUE):
  1. Running the schema DDL against a pgvector-enabled PostgreSQL creates the chunks table with vector column, tsvector generated column, generation array column, and all indexes (HNSW, GIN)
  2. Pydantic `Document` and `Chunk` models validate parsed content with required fields (source_url, content, title, doc_type, generations) and reject malformed data
  3. Configuration loads source paths, database connection string, embedding model name, and chunk sizes from a config file without hardcoded values
  4. Inserting a chunk with the same content hash is idempotent -- no duplicate rows created on re-ingestion
**Plans**: 2 plans

Plans:
- [x] 09-01-PLAN.md -- Pydantic data models (Document/Chunk), config system (pydantic-settings + TOML), content-hash dedup, unit tests
- [x] 09-02-PLAN.md -- pgvector schema DDL, database connection module (psycopg3 + register_vector), schema helper, DB tests

### Phase 10: Flare Parser
**Goal**: The MadCap Flare documentation corpus (the largest and most complex source) is parseable into structured Document objects, validating the entire pipeline architecture
**Depends on**: Phase 9
**Requirements**: PARSE-01, PARSE-02, PARSE-03
**Success Criteria** (what must be TRUE):
  1. Parser reads raw Flare XHTML files from a local Content/ directory and produces Document objects with extracted text, headings, and source paths -- MadCap namespace tags are stripped, not embedded in content
  2. Parser reads TOC files (.fltoc) to derive hierarchical section paths (e.g., "BBj Objects > BBjWindow > Methods") for each topic
  3. Condition tags (Primary.BASISHelp, Primary.Deprecated, Primary.Superseded, etc.) are extracted per topic and available as metadata for downstream generation tagging
  4. Web crawl fallback parser can extract content from documentation.basis.cloud when project files are unavailable
**Plans**: 3 plans

Plans:
- [x] 10-01-PLAN.md -- Parser foundation: dependencies, DocumentParser protocol, TOC index builder, condition tag extractor
- [x] 10-02-PLAN.md -- Flare XHTML parser: MadCap tag handling, snippet resolution, code blocks, tables, hierarchy paths
- [x] 10-03-PLAN.md -- Web crawl fallback parser: httpx + BeautifulSoup for documentation.basis.cloud

### Phase 11: BBj Intelligence
**Goal**: Every parsed document is automatically classified by BBj generation and document type, and chunks carry contextual headers derived from the source hierarchy -- this is the BBj-specific intelligence that makes the pipeline valuable
**Depends on**: Phase 10
**Requirements**: BBJ-01, BBJ-02, BBJ-03
**Success Criteria** (what must be TRUE):
  1. Generation tagger assigns one or more generation labels (all, character, vpro5, bbj-gui, dwc) to each chunk based on condition tags, file paths, API name patterns, and syntax patterns
  2. Document type classifier categorizes content as api-reference, concept, example, migration, language-reference, best-practice, or version-note based on content structure
  3. Every chunk has a contextual header prepended (e.g., "BBj Objects > BBjWindow > addButton > Parameters") derived from TOC hierarchy and heading structure
  4. Running the tagger on actual Flare content produces a plausible generation distribution (not everything tagged "all")
**Plans**: TBD

Plans:
- [ ] 11-01: Implement generation tagger with multi-signal classification (condition tags, file paths, API patterns, syntax)
- [ ] 11-02: Implement document type classifier and contextual chunk header generation

### Phase 12: Embedding Pipeline
**Goal**: The full pipeline runs end-to-end for the Flare source -- parse, tag, chunk, embed, store -- producing searchable vectors in pgvector with working hybrid retrieval
**Depends on**: Phase 11
**Requirements**: EMBED-01, EMBED-02, EMBED-03
**Success Criteria** (what must be TRUE):
  1. Embedding pipeline processes chunks through the configured model (Qwen3-Embedding-0.6B or equivalent) in batches with progress reporting
  2. Embedded chunks are bulk-inserted into pgvector via psycopg3 COPY protocol with all metadata columns populated
  3. A dense vector similarity query returns relevant Flare documentation chunks for a sample BBj query
  4. A BM25 keyword search query returns relevant chunks for BBj-specific terms (e.g., "BBjWindow addButton")
  5. CLI orchestrates the full pipeline (parse -> tag -> chunk -> embed -> store) for Flare with progress output
**Plans**: TBD

Plans:
- [ ] 12-01: Implement embedding pipeline with batch processing, pgvector bulk storage, and CLI orchestration
- [ ] 12-02: Implement hybrid search validation (dense vector + BM25 keyword queries)

### Phase 13: Additional Parsers
**Goal**: The remaining four source types (PDFs, WordPress articles, WordPress knowledge base, Docusaurus MDX, BBj source code) plug into the proven pipeline, completing source coverage
**Depends on**: Phase 12 (proven pipeline architecture)
**Requirements**: PARSE-04, PARSE-05, PARSE-06, PARSE-07, PARSE-08
**Success Criteria** (what must be TRUE):
  1. PDF parser extracts text from GuideToGuiProgrammingInBBj.pdf with code blocks and tables preserved (not flattened to gibberish)
  2. WordPress parser extracts article content from Advantage magazine pages (basis.cloud/advantage-index/) with boilerplate stripped
  3. WordPress/LearnPress parser extracts Knowledge Base content (basis.cloud/knowledge-base/) with lesson structure preserved
  4. Docusaurus MDX parser extracts content from DWC-Course repository with frontmatter metadata and JSX components stripped
  5. BBj source code parser processes .bbj/.txt sample files and identifies them as code examples with generation metadata
**Plans**: TBD

Plans:
- [ ] 13-01: Implement PDF parser (pymupdf4llm) and BBj source code parser
- [ ] 13-02: Implement WordPress parsers (Advantage + Knowledge Base) via REST API or Crawl4AI
- [ ] 13-03: Implement Docusaurus MDX parser for DWC-Course

### Phase 14: Documentation & Quality
**Goal**: The pipeline is documented for engineers to set up and run, the Getting Started page connects strategy docs to actual code, and ingestion quality is measurable
**Depends on**: Phase 13 (all parsers complete; documentation reflects actual implementation)
**Requirements**: DOC-02, DOC-03, QUAL-01, QUAL-02
**Success Criteria** (what must be TRUE):
  1. RAG Getting Started sub-page under Chapter 6 explains the source-by-source ingestion approach with design rationale and links to actual code files via GitHub URLs
  2. rag-ingestion/README.md has setup prerequisites, installation steps, configuration, and usage instructions that a new engineer can follow
  3. Post-ingestion summary report shows chunk counts broken down by source, by generation, and by document type
  4. Running the full pipeline and then the quality report produces meaningful numbers (not all zeros or all "unknown")
**Plans**: TBD

Plans:
- [ ] 14-01: Write RAG Getting Started sub-page and update Chapter 6 navigation
- [ ] 14-02: Write rag-ingestion/README.md and implement post-ingestion summary report

## Coverage

| Requirement | Phase | Description |
|-------------|-------|-------------|
| DOC-01 | Phase 8 | Repo README |
| INFRA-01 | Phase 8 | Python project scaffold |
| INFRA-02 | Phase 9 | pgvector schema DDL |
| INFRA-03 | Phase 9 | Pydantic data models |
| INFRA-04 | Phase 9 | Configuration system |
| INFRA-05 | Phase 9 | Content-hash deduplication |
| PARSE-01 | Phase 10 | Flare XHTML parser |
| PARSE-02 | Phase 10 | Flare condition tag extractor |
| PARSE-03 | Phase 10 | Flare web crawl fallback |
| BBJ-01 | Phase 11 | Generation tagger |
| BBJ-02 | Phase 11 | Document type classifier |
| BBJ-03 | Phase 11 | Contextual chunk headers |
| EMBED-01 | Phase 12 | Embedding pipeline |
| EMBED-02 | Phase 12 | pgvector bulk storage |
| EMBED-03 | Phase 12 | Hybrid search validation |
| PARSE-04 | Phase 13 | PDF parser |
| PARSE-05 | Phase 13 | WordPress/Advantage parser |
| PARSE-06 | Phase 13 | WordPress/KB parser |
| PARSE-07 | Phase 13 | Docusaurus MDX parser |
| PARSE-08 | Phase 13 | BBj source code parser |
| DOC-02 | Phase 14 | RAG Getting Started page |
| DOC-03 | Phase 14 | Getting Started links to code |
| QUAL-01 | Phase 14 | Post-ingestion summary report |
| QUAL-02 | Phase 14 | rag-ingestion/README.md |

**24/24 requirements mapped. No orphans.**

## Progress

**Execution Order:** Phases 8 -> 9 -> 10 -> 11 -> 12 -> 13 -> 14

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 8. Project Scaffold & README | v1.2 | 1/1 | Complete | 2026-01-31 |
| 9. Schema & Data Models | v1.2 | 2/2 | Complete | 2026-01-31 |
| 10. Flare Parser | v1.2 | 3/3 | Complete | 2026-01-31 |
| 11. BBj Intelligence | v1.2 | 0/2 | Not started | - |
| 12. Embedding Pipeline | v1.2 | 0/2 | Not started | - |
| 13. Additional Parsers | v1.2 | 0/3 | Not started | - |
| 14. Documentation & Quality | v1.2 | 0/2 | Not started | - |

---

_Continues from v1.1 (Phases 6-7). See .planning/milestones/v1.1-ROADMAP.md for prior work._
_Prior milestones: v1.0 (Phases 1-5). See .planning/milestones/v1.0-ROADMAP.md._
