# Requirements: BBj AI Strategy — v1.5 Alpha-Ready RAG System

**Defined:** 2026-02-03
**Core Value:** Engineers can evaluate the BBj RAG system through a usable chat interface with source citations, compiler-validated code, and shared server access.

## v1.5 Requirements

### Ingestion Performance

- [ ] **PERF-01**: Concurrent embedding workers process multiple chunks in parallel via asyncio
- [ ] **PERF-02**: Persistent HTTP connection reuse for Ollama embedding calls across batches
- [ ] **PERF-03**: `bbj-ingest-all --parallel` flag enables concurrent mode with configurable worker count

### Result Quality

- [x] **QUAL-01**: Source-balanced ranking reserves slots in top-k results for minority sources (PDF, BBj Source, MDX)
- [x] **QUAL-02**: source_url mapped to clickable HTTP links (flare:// → https://documentation.basis.cloud/..., WordPress and Web Crawl already HTTP)
- [x] **QUAL-03**: Search results include clickable `display_url` field alongside internal `source_url`

### Chat Interface

- [x] **CHAT-01**: Web chat page served from FastAPI with question input and streamed response display
- [x] **CHAT-02**: Claude API (Anthropic SDK) generates answers using RAG search results as context
- [x] **CHAT-03**: Responses include source citations with clickable links to documentation
- [x] **CHAT-04**: Response streaming via SSE with proper handling of multi-line content (code blocks)
- [x] **CHAT-05**: Chat page accessible without authentication on LAN

### Compiler Validation

- [x] **COMP-01**: `validate_bbj_syntax` MCP tool validates BBj code via bbjcpl compiler on host
- [x] **COMP-02**: Chat responses automatically validate BBj code blocks via bbjcpl
- [x] **COMP-03**: Validated code blocks show visual indicator (valid/invalid/not-validated)
- [x] **COMP-04**: bbjcpl stderr output parsed for error details (compiler exits 0 even on errors)

### Remote Access

- [x] **REMOTE-01**: MCP server supports Streamable HTTP transport for remote Claude Desktop connections
- [x] **REMOTE-02**: Chat UI accessible from other machines on local network
- [x] **REMOTE-03**: Docker Compose configuration supports shared server deployment (bind to 0.0.0.0)

## Future Requirements

Deferred to later milestones. Tracked but not in v1.5 roadmap.

### Chat Enhancements

- **CHAT-F01**: Generation filtering in chat (filter by BBj product generation)
- **CHAT-F02**: Multi-turn conversation context within session
- **CHAT-F03**: Chat history persistence across sessions

### Compiler Enhancements

- **COMP-F01**: Validation error feedback loop (send bbjcpl errors back to LLM for self-correction)

### Production Deployment

- **PROD-F01**: User authentication for shared deployment
- **PROD-F02**: Cloud hosting (beyond LAN server)
- **PROD-F03**: CI/CD pipeline for automated ingestion

### Quality & Optimization

- **QUAL-F01**: Embedding fine-tuning based on alpha retrieval quality feedback
- **QUAL-F02**: Agentic RAG (query routing, multi-step reasoning)
- **QUAL-F03**: Incremental ingestion (update changed documents only)

## Out of Scope

| Feature | Reason |
|---------|--------|
| User authentication | Internal alpha on trusted network; no sensitive data |
| Chat history persistence | Alpha phase — ephemeral conversations are fine for evaluation |
| generate_bbj_code MCP tool | Requires fine-tuned BBj model (separate milestone) |
| Cloud/production hosting | v1.5 targets LAN server, not cloud |
| Mobile-optimized chat UI | Engineers use desktop browsers |
| Embedding fine-tuning | Requires baseline quality measurement from alpha feedback |
| Multi-user session isolation | Single shared instance; engineers evaluate sequentially or accept shared context |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| QUAL-01 | Phase 25 | Complete |
| QUAL-02 | Phase 25 | Complete |
| QUAL-03 | Phase 25 | Complete |
| CHAT-01 | Phase 26 | Complete |
| CHAT-02 | Phase 26 | Complete |
| CHAT-03 | Phase 26 | Complete |
| CHAT-04 | Phase 26 | Complete |
| CHAT-05 | Phase 26 | Complete |
| REMOTE-01 | Phase 27 | Complete |
| REMOTE-02 | Phase 27 | Complete |
| REMOTE-03 | Phase 27 | Complete |
| COMP-01 | Phase 28 | Complete |
| COMP-02 | Phase 28 | Complete |
| COMP-03 | Phase 28 | Complete |
| COMP-04 | Phase 28 | Complete |
| PERF-01 | Phase 29 | Pending |
| PERF-02 | Phase 29 | Pending |
| PERF-03 | Phase 29 | Pending |

**Coverage:**
- v1.5 requirements: 18 total
- Mapped to phases: 18/18
- Unmapped: 0

---
*Requirements defined: 2026-02-03*
*Last updated: 2026-02-04 after Phase 28 completion*
