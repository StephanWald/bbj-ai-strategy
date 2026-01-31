# Requirements: BBj AI Strategy v1.2

**Defined:** 2026-01-31
**Core Value:** Engineers can start building the RAG ingestion pipeline with concrete code, schemas, and source-by-source guidance — bridging the gap between Chapter 6's strategic design and actual implementation.

## v1.2 Requirements

### Documentation

- [x] **DOC-01**: Repo README rewritten with project description, live site link, and tech stack summary
- [ ] **DOC-02**: RAG Getting Started sub-page under Chapter 6 with source-by-source ingestion approach and design rationale
- [ ] **DOC-03**: Getting Started page links to actual code files in `rag-ingestion/` via GitHub URLs

### Infrastructure

- [x] **INFRA-01**: Python project scaffolded at `rag-ingestion/` with uv, pyproject.toml, and dependency management
- [x] **INFRA-02**: pgvector schema DDL with generation array column, tsvector for BM25, HNSW index for cosine similarity
- [x] **INFRA-03**: Pydantic data models for parsed documents and chunks (common interface across all parsers)
- [x] **INFRA-04**: Configuration system for source paths, database connection, embedding model, chunk sizes
- [x] **INFRA-05**: Content-hash deduplication for idempotent re-ingestion

### Parsers

- [x] **PARSE-01**: MadCap Flare XHTML parser — parses raw project files from Flare Content/ directory, extracts text from MadCap namespace tags, uses TOC files for hierarchy
- [x] **PARSE-02**: MadCap Flare condition tag extractor — reads Primary.flcts and per-topic MadCap:conditions attributes for generation/deprecation signals
- [x] **PARSE-03**: MadCap Flare web crawl parser (fallback for documentation.basis.cloud when project files unavailable)
- [ ] **PARSE-04**: PDF parser for standalone documents (e.g., GuideToGuiProgrammingInBBj.pdf)
- [ ] **PARSE-05**: WordPress/HTML parser for Advantage magazine articles (basis.cloud/advantage-index/)
- [ ] **PARSE-06**: WordPress/LearnPress parser for Knowledge Base (basis.cloud/knowledge-base/)
- [ ] **PARSE-07**: Docusaurus MDX parser for DWC-Course content (github.com/BasisHub/DWC-Course)
- [ ] **PARSE-08**: BBj source code parser for sample files in DWC-Course and standalone examples

### BBj Intelligence

- [x] **BBJ-01**: Generation tagger — classifies chunks using condition tags, file paths (bbjobjects/, dwc/, commands/, mnemonic/), API name patterns, and syntax patterns
- [x] **BBJ-02**: Document type classifier — categorizes as api-reference, concept, example, migration, language-reference, best-practice, or version-note based on content structure
- [x] **BBJ-03**: Contextual chunk headers — uses TOC hierarchy + heading structure to prepend context path to every chunk

### Embedding & Storage

- [ ] **EMBED-01**: Embedding pipeline using researched model (Qwen3-Embedding-0.6B or current best) with batch processing
- [ ] **EMBED-02**: pgvector storage with bulk insert via psycopg3 COPY protocol
- [ ] **EMBED-03**: Hybrid search validation — verify both dense vector and BM25 keyword search return relevant results

### Quality

- [ ] **QUAL-01**: Post-ingestion summary report (chunk counts per source, per generation, per doc type)
- [ ] **QUAL-02**: rag-ingestion/README.md with setup instructions, prerequisites, and usage guide

## Future Requirements

### Retrieval API

- **RETR-01**: REST API endpoint wrapping the hybrid search pipeline
- **RETR-02**: Generation-aware scoring adjustment at query time
- **RETR-03**: Cross-encoder reranking stage

### CI/CD

- **CICD-01**: Automated re-ingestion on documentation updates
- **CICD-02**: Embedding model versioning and migration
- **CICD-03**: Pipeline monitoring and alerting

### Advanced Features

- **ADV-01**: Embedding fine-tuning with BBj query-document pairs
- **ADV-02**: Supersedes/superseded_by linking between generation variants
- **ADV-03**: Incremental ingestion (only process changed files)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Retrieval API server | v1.2 is a batch ingestion tool, not a running service |
| CI/CD pipeline | Starter kit — engineers run manually until ready for automation |
| Embedding fine-tuning | Requires baseline retrieval quality measurement first |
| Production deployment | Code stays in mono-repo; production hosting is a separate project |
| Agentic RAG features | No query routing, agent loops, or multi-step reasoning |
| Web UI for search | Command-line validation script is sufficient for v1.2 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DOC-01 | Phase 8 | Complete |
| INFRA-01 | Phase 8 | Complete |
| INFRA-02 | Phase 9 | Complete |
| INFRA-03 | Phase 9 | Complete |
| INFRA-04 | Phase 9 | Complete |
| INFRA-05 | Phase 9 | Complete |
| PARSE-01 | Phase 10 | Complete |
| PARSE-02 | Phase 10 | Complete |
| PARSE-03 | Phase 10 | Complete |
| BBJ-01 | Phase 11 | Complete |
| BBJ-02 | Phase 11 | Complete |
| BBJ-03 | Phase 11 | Complete |
| EMBED-01 | Phase 12 | Pending |
| EMBED-02 | Phase 12 | Pending |
| EMBED-03 | Phase 12 | Pending |
| PARSE-04 | Phase 13 | Pending |
| PARSE-05 | Phase 13 | Pending |
| PARSE-06 | Phase 13 | Pending |
| PARSE-07 | Phase 13 | Pending |
| PARSE-08 | Phase 13 | Pending |
| DOC-02 | Phase 14 | Pending |
| DOC-03 | Phase 14 | Pending |
| QUAL-01 | Phase 14 | Pending |
| QUAL-02 | Phase 14 | Pending |

**Coverage:**
- v1.2 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

---
*Requirements defined: 2026-01-31*
*Last updated: 2026-01-31 after roadmap creation (all 24 requirements mapped to Phases 8-14)*
