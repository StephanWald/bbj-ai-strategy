# Milestone v1.4: RAG Deployment

**Status:** IN PROGRESS
**Phases:** 20-24 (+23.1)
**Total Plans:** 13

## Overview

Transform the battle-tested RAG ingestion pipeline (310 tests, 6 parsers, hybrid search) into a running Docker-based service. Docker Compose orchestrates pgvector and the Python app, all 6 BBj documentation sources are ingested against real corpus data, a FastAPI REST endpoint exposes hybrid retrieval, and a thin MCP server provides the `search_bbj_knowledge` tool for Claude Desktop. Phases follow the critical path: Docker foundation, data ingestion, REST API, MCP server, end-to-end validation.

## Phases

- [x] **Phase 20: Docker + Database Foundation** - Containerized pgvector and Python app with schema initialization, Ollama connectivity, and env-based config
- [x] **Phase 21: Data Configuration + Ingestion** - All 6 real sources wired and ingested into pgvector via Docker
- [x] **Phase 22: REST Retrieval API** - FastAPI endpoints for search, health, and stats over the populated corpus
- [x] **Phase 23: MCP Server** - `search_bbj_knowledge` tool via stdio transport for Claude Desktop
- [ ] **Phase 23.1: WordPress Parser Fix** - PDF handling fix, batch embeddings, full re-ingest, README update (INSERTED)
- [ ] **Phase 24: End-to-End Validation** - Prove the full pipeline works: query in, relevant BBj docs out, through both interfaces

## Phase Details

### Phase 20: Docker + Database Foundation

**Goal**: `docker compose up` starts pgvector and Python app containers with schema applied, Ollama reachable, source data mounted, and configuration driven by environment variables
**Depends on**: Nothing (foundation phase)
**Requirements**: DOCK-01, DOCK-02, DOCK-03, DOCK-04, DOCK-05, DOCK-06, DATA-05
**Plans**: 2 plans

**Success Criteria** (what must be TRUE):
1. `docker compose up` starts both containers and they reach healthy state without manual intervention
2. pgvector schema (tables, indexes, extensions) exists in the database after first startup
3. App container can reach host Ollama and pull an embedding for a test string
4. App container can read mounted source data directories (Flare, PDF, MDX, BBj source files visible)
5. Settings load entirely from environment variables with no TOML file present in the container

Plans:
- [x] 20-01-PLAN.md -- Docker Compose + Dockerfile + FastAPI skeleton + health endpoint
- [x] 20-02-PLAN.md -- Config refactor + startup wiring + Docker integration verification

### Phase 21: Data Configuration + Ingestion

**Goal**: All 6 BBj documentation sources are configured with real data paths and successfully ingested into pgvector, producing a searchable corpus
**Depends on**: Phase 20 (containers running, schema applied, Ollama reachable)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-06
**Plans**: 2 plans

**Success Criteria** (what must be TRUE):
1. A single command triggers ingestion of all 6 sources in sequence (Flare, PDF, MDX, BBj source, WordPress, web crawl)
2. Multiple MDX tutorial directories (DWC, beginner, DB modernization) are all ingested -- not just one
3. Chunks from all 6 sources exist in the database with correct source attribution and generation tags
4. An interrupted ingestion run can be resumed without re-processing already-completed sources

Plans:
- [x] 21-01-PLAN.md -- Source config infrastructure: sources.toml, config loader, multi-MDX prefix support, report fix
- [x] 21-02-PLAN.md -- Ingestion orchestration CLI: bbj-ingest-all with fail-fast, resume, clean, summary table

### Phase 22: REST Retrieval API

**Goal**: A FastAPI server inside the Docker app container serves hybrid search over the ingested corpus with health and stats endpoints
**Depends on**: Phase 21 (populated database with real corpus)
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06
**Plans**: 2 plans

**Success Criteria** (what must be TRUE):
1. `curl localhost:8000/search -d '{"query": "BBjGrid"}'` returns ranked documentation chunks with content, title, source_url, and score
2. Searching with `?generation=dwc` returns only DWC-generation results; `bbj-gui` is normalized to `bbj_gui` automatically
3. `/health` returns component status for database and Ollama connectivity (200 when healthy, 503 when not)
4. `/stats` returns chunk counts broken down by source and generation

Plans:
- [x] 22-01-PLAN.md -- Async search infrastructure + /search endpoint + connection pooling + embedder warm-up
- [x] 22-02-PLAN.md -- /stats endpoint + generation filtering normalization + /health pool-based readiness

### Phase 23: MCP Server

**Goal**: Claude Desktop can invoke `search_bbj_knowledge` to retrieve relevant BBj documentation from the running system
**Depends on**: Phase 22 (REST API validates search integration patterns that MCP reuses)
**Requirements**: MCP-01, MCP-02, MCP-03, MCP-04
**Plans**: 1 plan

**Success Criteria** (what must be TRUE):
1. `search_bbj_knowledge` tool appears in Claude Desktop's tool list after configuring the MCP server
2. Invoking the tool with query "BBjGrid" returns formatted text blocks (not raw JSON) with documentation content
3. The tool accepts an optional `generation` parameter that filters results by BBj product generation
4. MCP server runs on the host via stdio transport (not inside Docker)

Plans:
- [x] 23-01-PLAN.md -- MCP server module + stdio transport + Claude Desktop config

### Phase 23.1: WordPress Parser Fix (INSERTED)

**Goal**: Fix WordPress parser PDF handling (binary garbage bug), add Content-Type detection, full re-ingest all sources, and update README with Docker + API + MCP documentation
**Depends on**: Phase 23
**Plans**: 4 plans (3 original + 1 gap closure)

Plans:
- [x] 23.1-01-PLAN.md -- WordPress parser Content-Type PDF detection fix + tests
- [x] 23.1-02-PLAN.md -- README Docker/API/MCP documentation update
- [x] 23.1-03-PLAN.md -- Full clean re-ingest via Docker with verification
- [ ] 23.1-04-PLAN.md -- Gap closure: Re-ingest Advantage source + database verification

### Phase 24: End-to-End Validation

**Goal**: The complete system is proven to work -- a user query enters through either REST API or MCP, hits real ingested BBj documentation, and returns relevant results
**Depends on**: Phases 22 and 23 (both interfaces operational)
**Requirements**: E2E-01, E2E-02
**Plans**: TBD

**Success Criteria** (what must be TRUE):
1. A REST API query about a known BBj topic (e.g., "How do I create a BBjGrid?") returns chunks from the real corpus that answer the question
2. The same query via Claude Desktop's MCP tool returns relevant BBj documentation that Claude can use to answer the question
3. Results from both interfaces include chunks from multiple sources (not just one parser's output)

Plans:
- [ ] 24-01: REST API validation + MCP validation + cross-source verification

---

## Coverage

| Requirement | Phase | Category |
|-------------|-------|----------|
| DOCK-01 | 20 | Docker Infrastructure |
| DOCK-02 | 20 | Docker Infrastructure |
| DOCK-03 | 20 | Docker Infrastructure |
| DOCK-04 | 20 | Docker Infrastructure |
| DOCK-05 | 20 | Docker Infrastructure |
| DOCK-06 | 20 | Docker Infrastructure |
| DATA-05 | 20 | Data Configuration |
| DATA-01 | 21 | Data Configuration |
| DATA-02 | 21 | Data Configuration |
| DATA-03 | 21 | Data Configuration |
| DATA-04 | 21 | Data Configuration |
| DATA-06 | 21 | Data Configuration |
| API-01 | 22 | REST API |
| API-02 | 22 | REST API |
| API-03 | 22 | REST API |
| API-04 | 22 | REST API |
| API-05 | 22 | REST API |
| API-06 | 22 | REST API |
| MCP-01 | 23 | MCP Server |
| MCP-02 | 23 | MCP Server |
| MCP-03 | 23 | MCP Server |
| MCP-04 | 23 | MCP Server |
| E2E-01 | 24 | End-to-End Validation |
| E2E-02 | 24 | End-to-End Validation |

**Mapped: 24/24 -- no orphans, no duplicates**

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 20. Docker + Database Foundation | v1.4 | 2/2 | Complete | 2026-02-01 |
| 21. Data Configuration + Ingestion | v1.4 | 2/2 | Complete | 2026-02-01 |
| 22. REST Retrieval API | v1.4 | 2/2 | Complete | 2026-02-01 |
| 23. MCP Server | v1.4 | 1/1 | Complete | 2026-02-02 |
| 23.1. WordPress Parser Fix | v1.4 | 3/4 | Gap closure | 2026-02-02 |
| 24. End-to-End Validation | v1.4 | 0/1 | Not started | - |

---

_Created: 2026-02-01_
_Last updated: 2026-02-02 (Phase 23.1 inserted)_
