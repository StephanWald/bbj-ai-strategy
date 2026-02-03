# Roadmap: BBj AI Strategy v1.5 Alpha-Ready RAG System

## Milestones

- v1.0 Documentation Site (Phases 1-5) — shipped 2026-01-31
- v1.1 Code Corrections & Branding (Phases 6-7) — shipped 2026-01-31
- v1.2 RAG Ingestion Pipeline (Phases 8-14) — shipped 2026-02-01
- v1.3 MCP Architecture Integration (Phases 15-19) — shipped 2026-02-01
- v1.4 RAG Deployment (Phases 20-24 + 23.1) — shipped 2026-02-02
- **v1.5 Alpha-Ready RAG System (Phases 25-29)** — in progress

## Overview

v1.5 transforms the working v1.4 RAG system into an alpha product engineers can evaluate. The roadmap builds outward from zero-risk quality improvements (URL mapping, balanced ranking), through the marquee chat interface with Claude API, to remote access and compiler validation, finishing with ingestion performance. Each phase delivers a complete, verifiable capability. The dependency chain ensures citations have clickable links before the chat UI ships, and remote access enables shared deployment before compiler validation requires host-side MCP connectivity.

## Phases

**Phase Numbering:**
- Integer phases (25, 26, 27...): Planned milestone work
- Decimal phases (25.1, 25.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 25: Result Quality Foundation** — Clickable source links and source-balanced ranking
- [ ] **Phase 26: Chat Interface** — Web chat with Claude API, streaming responses, and source citations
- [ ] **Phase 27: Remote Access** — Streamable HTTP MCP and network-accessible deployment
- [ ] **Phase 28: Compiler Validation** — bbjcpl integration for BBj code syntax checking in chat responses
- [ ] **Phase 29: Ingestion Performance** — Concurrent workers and persistent connections for faster rebuilds

## Phase Details

### Phase 25: Result Quality Foundation
**Goal**: Search results link to real documentation and surface all source types, not just Flare
**Depends on**: v1.4 complete (Phase 24)
**Requirements**: QUAL-01, QUAL-02, QUAL-03
**Success Criteria** (what must be TRUE):
  1. A search result from Flare source includes a clickable HTTPS link to documentation.basis.cloud that opens the correct page in a browser
  2. A top-10 search query that previously returned only Flare results now includes at least one result from a minority source (PDF, BBj Source, or MDX) when relevant content exists
  3. Every search result returned by the API includes both a `source_url` (internal) and a `display_url` (clickable HTTPS link) field
**Plans**: 3 plans

Plans:
- [x] 25-01-PLAN.md -- URL mapping module, schema migration, models/DB, backfill script
- [x] 25-02-PLAN.md -- Search/API/MCP response enrichment with diversity reranking
- [x] 25-03-PLAN.md -- Pipeline/chunker integration and E2E validation updates

### Phase 26: Chat Interface
**Goal**: Engineers can ask BBj questions in a browser and get Claude-generated answers grounded in RAG results with source citations
**Depends on**: Phase 25 (URL mapping needed for citation links)
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05
**Success Criteria** (what must be TRUE):
  1. An engineer opens `http://localhost:10800/chat` in a browser, types a BBj question, and receives a coherent answer with cited sources
  2. The response streams visibly (text appears incrementally, not all at once after a delay)
  3. Source citations in the response are clickable links that open the correct documentation page on documentation.basis.cloud or the original source site
  4. Multi-line content including BBj code blocks renders correctly in the streamed response (no broken formatting from SSE newline handling)
  5. The chat page loads without requiring any login or authentication
**Plans**: 3 plans

Plans:
- [ ] 26-01-PLAN.md -- Backend chat module: dependencies, config, prompt construction, Claude API streaming, SSE endpoint
- [ ] 26-02-PLAN.md -- Chat page frontend: HTML template, CSS styling, vanilla JS SSE client with markdown rendering
- [ ] 26-03-PLAN.md -- Docker integration and end-to-end verification checkpoint

### Phase 27: Remote Access
**Goal**: Engineers on the local network can access both the chat UI and MCP server from their own machines without running Docker locally
**Depends on**: Phase 25 (independent of Phase 26; can parallelize)
**Requirements**: REMOTE-01, REMOTE-02, REMOTE-03
**Success Criteria** (what must be TRUE):
  1. Claude Desktop on a different machine connects to the MCP server via Streamable HTTP URL (e.g., `http://server:10800/mcp`) and successfully executes `search_bbj_knowledge`
  2. A browser on a different machine on the LAN opens `http://server:10800/chat` and can submit queries
  3. `docker compose up` with the shared-server configuration binds all services to 0.0.0.0 and is accessible from other machines
**Plans**: TBD

Plans:
- [ ] 27-01: TBD
- [ ] 27-02: TBD

### Phase 28: Compiler Validation
**Goal**: BBj code in chat responses is automatically validated against the real BBj compiler, giving engineers confidence that code examples are syntactically correct
**Depends on**: Phase 26 (chat responses that contain BBj code blocks)
**Requirements**: COMP-01, COMP-02, COMP-03, COMP-04
**Success Criteria** (what must be TRUE):
  1. The `validate_bbj_syntax` MCP tool accepts a BBj code string and returns whether it compiled successfully, with error details if it failed
  2. A chat response containing a BBj code block shows a visual indicator (checkmark, X, or neutral) reflecting whether bbjcpl validated the syntax
  3. A known-bad BBj code snippet (e.g., missing END statement) is correctly identified as invalid with the specific error message from bbjcpl stderr
  4. bbjcpl stderr output is parsed for error details rather than relying on exit code (which is always 0)
**Plans**: TBD

Plans:
- [ ] 28-01: TBD
- [ ] 28-02: TBD

### Phase 29: Ingestion Performance
**Goal**: Corpus rebuilds run significantly faster through concurrent processing, reducing wait time for re-ingestion during development
**Depends on**: Nothing (independent of Phases 25-28)
**Requirements**: PERF-01, PERF-02, PERF-03
**Success Criteria** (what must be TRUE):
  1. `bbj-ingest-all --parallel` completes a full corpus ingestion measurably faster than sequential mode (targeting 1.5-2x speedup)
  2. Multiple embedding workers process chunks concurrently without Ollama GPU saturation or errors
  3. HTTP connections to Ollama are reused across batches within a worker (no per-batch connection setup overhead)
**Plans**: TBD

Plans:
- [ ] 29-01: TBD
- [ ] 29-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 25 → 26 → 27 → 28 → 29
(Phase 27 could parallelize with Phase 26 if needed, but sequential is simpler for one builder.)

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 25. Result Quality Foundation | v1.5 | 3/3 | Complete | 2026-02-03 |
| 26. Chat Interface | v1.5 | 0/3 | Not started | - |
| 27. Remote Access | v1.5 | 0/TBD | Not started | - |
| 28. Compiler Validation | v1.5 | 0/TBD | Not started | - |
| 29. Ingestion Performance | v1.5 | 0/TBD | Not started | - |

## Coverage

| Requirement | Phase | Category |
|-------------|-------|----------|
| QUAL-01 | 25 | Result Quality |
| QUAL-02 | 25 | Result Quality |
| QUAL-03 | 25 | Result Quality |
| CHAT-01 | 26 | Chat Interface |
| CHAT-02 | 26 | Chat Interface |
| CHAT-03 | 26 | Chat Interface |
| CHAT-04 | 26 | Chat Interface |
| CHAT-05 | 26 | Chat Interface |
| REMOTE-01 | 27 | Remote Access |
| REMOTE-02 | 27 | Remote Access |
| REMOTE-03 | 27 | Remote Access |
| COMP-01 | 28 | Compiler Validation |
| COMP-02 | 28 | Compiler Validation |
| COMP-03 | 28 | Compiler Validation |
| COMP-04 | 28 | Compiler Validation |
| PERF-01 | 29 | Ingestion Performance |
| PERF-02 | 29 | Ingestion Performance |
| PERF-03 | 29 | Ingestion Performance |

**Mapped: 18/18 -- all v1.5 requirements covered, no orphans.**

---
*Roadmap created: 2026-02-03*
*Milestone: v1.5 Alpha-Ready RAG System*
