# Roadmap: BBj AI Strategy v1.6 Data Expansion

## Milestones

- v1.0 Documentation Site (Phases 1-5) — shipped 2026-01-31
- v1.1 Code Corrections & Branding (Phases 6-7) — shipped 2026-01-31
- v1.2 RAG Ingestion Pipeline (Phases 8-14) — shipped 2026-02-01
- v1.3 MCP Architecture Integration (Phases 15-19) — shipped 2026-02-01
- v1.4 RAG Deployment (Phases 20-24 + 23.1) — shipped 2026-02-02
- v1.5 Alpha-Ready RAG System (Phases 25-29) — shipped 2026-02-05
- **v1.6 Data Expansion (Phases 30-31)** — in progress

## Overview

v1.6 expands the RAG knowledge base with structured API documentation and establishes infrastructure for collecting curated training data. The JavaDoc ingestion adds 359 classes and 4,438 methods of BBjAPI documentation — highly structured data that will significantly improve API-related queries. The training data repository creates a foundation for systematic collection of annotated BBj code examples that can later be converted to fine-tuning datasets.

## Phases

**Phase Numbering:**
- Integer phases (30, 31...): Planned milestone work
- Decimal phases (30.1, 30.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 30: BBjAPI JavaDoc Ingestion** — Parser, chunking, and ingestion pipeline for structured API documentation
- [ ] **Phase 31: Training Data Repository** — Infrastructure, format specification, and seed examples for curated BBj code

## Phase Details

### Phase 30: BBjAPI JavaDoc Ingestion
**Goal**: Search results include BBjAPI method documentation, improving accuracy for API-related queries
**Depends on**: v1.5 complete (existing parser infrastructure)
**Requirements**: API-01, API-02, API-03, API-04, API-05
**Success Criteria** (what must be TRUE):
  1. A search for "BBjWindow addButton" returns results from JavaDoc source with method signature and documentation
  2. Each JavaDoc result includes a clickable `display_url` linking to documentation.basis.cloud
  3. `bbj-ingest-all --source javadoc` completes without errors, adding ~4,000+ chunks to the corpus
  4. Method chunks include parent class name in context header for disambiguation
  5. E2E validation passes with new JavaDoc-specific test queries
**Plans:** 2 plans

Plans:
- [x] 30-01-PLAN.md — Create JavaDoc JSON parser (class reference card format)
- [x] 30-02-PLAN.md — Wire parser into ingestion pipeline and validate E2E

Data source:
- Location: `/Users/beff/bbx/documentation/javadoc/*.json`
- Format: Structured JSON with class hierarchies, method signatures, parameters, documentation
- Size: 7 files, 359 classes, 4,438 methods
- Links: Each method includes `[Docs](https://documentation.basis.cloud/...)` URL

### Phase 31: Training Data Repository
**Goal**: Infrastructure exists for systematically collecting and validating curated BBj code examples
**Depends on**: Nothing (independent of Phase 30)
**Requirements**: TRAIN-01, TRAIN-02, TRAIN-03, TRAIN-04
**Success Criteria** (what must be TRUE):
  1. Repository structure exists with README, format specification, and directory layout
  2. Markdown format for training examples is documented (front matter schema, code block conventions, explanation sections)
  3. At least 2 seed examples demonstrate the format and pass validation
  4. Contributor documentation explains how to add new examples
**Plans**: TBD (estimate 1-2 plans)

Format considerations:
- Markdown with YAML front matter (human-readable, version-controllable)
- Convertible to JSONL for fine-tuning (future tooling)
- Code blocks with BBj syntax highlighting
- Annotations explaining what the code does and why

## Progress

**Execution Order:**
Phases execute in order: 30 → 31
(Phase 31 could parallelize with Phase 30 if needed.)

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 30. BBjAPI JavaDoc Ingestion | v1.6 | 2/2 | Complete | 2026-02-05 |
| 31. Training Data Repository | v1.6 | 0/? | Not started | - |

## Coverage

| Requirement | Phase | Category |
|-------------|-------|----------|
| API-01 | 30 | JavaDoc Ingestion |
| API-02 | 30 | JavaDoc Ingestion |
| API-03 | 30 | JavaDoc Ingestion |
| API-04 | 30 | JavaDoc Ingestion |
| API-05 | 30 | JavaDoc Ingestion |
| TRAIN-01 | 31 | Training Data |
| TRAIN-02 | 31 | Training Data |
| TRAIN-03 | 31 | Training Data |
| TRAIN-04 | 31 | Training Data |

**Mapped: 9/9 — all v1.6 requirements covered, no orphans.**

---
*Roadmap created: 2026-02-05*
*Milestone: v1.6 Data Expansion*
