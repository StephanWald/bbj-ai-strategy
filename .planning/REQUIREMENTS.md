# Requirements: BBj AI Strategy — v1.4 RAG Deployment

**Defined:** 2026-02-01
**Core Value:** A running Docker-based system that ingests all 6 BBj documentation sources and serves retrieval via REST API and MCP server.

## v1.4 Requirements

### Docker Infrastructure

- [x] **DOCK-01**: Docker Compose orchestrates pgvector and Python app containers with `docker compose up`
- [x] **DOCK-02**: pgvector container uses `pgvector/pgvector:0.8.0-pg17` with schema auto-initialized on first run
- [x] **DOCK-03**: App container uses `python:3.12-slim-bookworm` base with uv for dependency installation
- [x] **DOCK-04**: App container reaches host Ollama via `host.docker.internal:11434`
- [x] **DOCK-05**: Local source data directories (Flare, PDF, MDX, BBj source) are volume-mounted into app container
- [x] **DOCK-06**: pgvector container has `shm_size` configured for HNSW index builds on real corpus

### Data Configuration & Ingestion

- [x] **DATA-01**: All 6 source paths wired to real data locations (Flare at `/Users/beff/bbjdocs/`, PDF at project root, MDX tutorials, BBj source dirs, WordPress URLs, web crawl URLs)
- [x] **DATA-02**: Config supports multiple MDX source directories (not just single path)
- [x] **DATA-03**: Full ingestion pipeline runs successfully against all 6 real sources
- [x] **DATA-04**: Ingestion supports resume/retry for interrupted large corpus processing
- [x] **DATA-05**: Configuration works in Docker via environment variables (not dependent on TOML file presence)
- [x] **DATA-06**: Ingestion orchestration script runs all 6 parsers in sequence with a single command

### REST Retrieval API

- [ ] **API-01**: `/search` endpoint accepts query string, returns ranked chunks from hybrid search (dense + BM25 + RRF)
- [ ] **API-02**: `/search` supports `generation` filter parameter (e.g., `?generation=dwc`)
- [ ] **API-03**: `/search` normalizes generation input (`bbj-gui` → `bbj_gui`) to match database format
- [ ] **API-04**: Search results include `context_header` and `deprecated` fields alongside content, title, source_url, score
- [ ] **API-05**: `/health` endpoint checks database and Ollama connectivity
- [ ] **API-06**: `/stats` endpoint returns corpus metrics (chunk count, source distribution, generation distribution)

### MCP Server

- [ ] **MCP-01**: `search_bbj_knowledge` tool implemented matching Chapter 2's JSON schema definition
- [ ] **MCP-02**: MCP server uses stdio transport (Claude Desktop spawns it as local process)
- [ ] **MCP-03**: Tool returns formatted text responses optimized for LLM consumption (not raw JSON)
- [ ] **MCP-04**: Tool supports `generation` parameter for filtering by BBj product generation

### End-to-End Validation

- [ ] **E2E-01**: Query the running REST API and receive relevant BBj documentation chunks
- [ ] **E2E-02**: Query via MCP server from Claude Desktop and receive relevant BBj documentation chunks

## Future Requirements

Deferred to later milestones. Tracked but not in v1.4 roadmap.

### Additional MCP Tools

- **MCP-F01**: `generate_bbj_code` tool (requires fine-tuned model — separate milestone)
- **MCP-F02**: `validate_bbj_syntax` tool (requires bbjcpl integration — separate milestone)

### Production Deployment

- **PROD-F01**: CI/CD pipeline for automated ingestion
- **PROD-F02**: Cloud hosting (beyond local Docker Compose)
- **PROD-F03**: Authentication/authorization for API access

### Quality & Optimization

- **QUAL-F01**: Embedding fine-tuning based on retrieval quality baselines
- **QUAL-F02**: Agentic RAG (query routing, multi-step reasoning)
- **QUAL-F03**: Incremental ingestion (update changed documents only)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Containerized Ollama | Host Ollama provides macOS Metal GPU acceleration; duplicating in Docker wastes resources |
| Streamable HTTP MCP transport | stdio sufficient for local Claude Desktop; HTTP transport adds complexity for no current benefit |
| Async database operations | Corpus is <50K chunks; sync psycopg3 with connection pooling is sufficient |
| Web-based search UI | v1.4 delivers API + MCP; UI is a separate concern |
| Automated scheduled ingestion | Manual trigger sufficient; corpus changes infrequently |
| Multi-user concurrent access | Local development tool; single-user is fine |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DOCK-01 | Phase 20 | Complete |
| DOCK-02 | Phase 20 | Complete |
| DOCK-03 | Phase 20 | Complete |
| DOCK-04 | Phase 20 | Complete |
| DOCK-05 | Phase 20 | Complete |
| DOCK-06 | Phase 20 | Complete |
| DATA-01 | Phase 21 | Complete |
| DATA-02 | Phase 21 | Complete |
| DATA-03 | Phase 21 | Complete |
| DATA-04 | Phase 21 | Complete |
| DATA-05 | Phase 20 | Complete |
| DATA-06 | Phase 21 | Complete |
| API-01 | Phase 22 | Pending |
| API-02 | Phase 22 | Pending |
| API-03 | Phase 22 | Pending |
| API-04 | Phase 22 | Pending |
| API-05 | Phase 22 | Pending |
| API-06 | Phase 22 | Pending |
| MCP-01 | Phase 23 | Pending |
| MCP-02 | Phase 23 | Pending |
| MCP-03 | Phase 23 | Pending |
| MCP-04 | Phase 23 | Pending |
| E2E-01 | Phase 24 | Pending |
| E2E-02 | Phase 24 | Pending |

**Coverage:**
- v1.4 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

---
*Requirements defined: 2026-02-01*
*Last updated: 2026-02-01 after phase 21 completion*
