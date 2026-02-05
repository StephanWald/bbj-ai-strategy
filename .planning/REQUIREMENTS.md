# Requirements: BBj AI Strategy — v1.6 Data Expansion

**Defined:** 2026-02-05
**Core Value:** Expand RAG knowledge with structured API documentation and establish infrastructure for collecting curated training data that enables future BBj model fine-tuning.

## v1.6 Requirements

### BBjAPI JavaDoc Ingestion

- [x] **API-01**: JavaDoc JSON parser extracts classes, methods, parameters, and documentation from `/Users/beff/bbx/documentation/javadoc/*.json`
- [x] **API-02**: Chunking preserves class-method relationships (each method chunk includes parent class context)
- [x] **API-03**: Documentation links (`[Docs](https://documentation.basis.cloud/...)`) extracted as `display_url` for citation
- [x] **API-04**: `bbj-ingest-all --source javadoc` ingests all 7 JSON files (359 classes, 4,438 methods)
- [x] **API-05**: Search queries for BBj API methods (e.g., "BBjWindow addButton") return relevant JavaDoc results

### Training Data Infrastructure

- [x] **TRAIN-01**: Training data repository structure created (directory layout, README, format specification)
- [x] **TRAIN-02**: Markdown format defined for annotated code examples (front matter, code blocks, explanations)
- [x] **TRAIN-03**: 1-2 seed examples created to validate format and workflow
- [x] **TRAIN-04**: Documentation for contributors on how to add new training examples

## Future Requirements

Deferred to later milestones. Tracked but not in v1.6 roadmap.

### Additional Data Sources

- **DATA-F01**: Expanded BBj source code ingestion (internal codebases, open-source projects)
- **DATA-F02**: Stack Overflow / community forum content
- **DATA-F03**: Third-party BBj tutorials and guides

### Training Data Expansion

- **TRAIN-F01**: Automated extraction of good examples from chat responses
- **TRAIN-F02**: Q&A pair collection for supervised fine-tuning
- **TRAIN-F03**: Conversion pipeline from Markdown to JSONL training format

### Fine-Tuning Pipeline

- **FINETUNE-F01**: JSONL conversion tooling for training data
- **FINETUNE-F02**: QLoRA training pipeline setup
- **FINETUNE-F03**: Model evaluation framework for BBj code generation

## Out of Scope

| Feature | Reason |
|---------|--------|
| Actual fine-tuning | v1.6 focuses on data collection infrastructure, not model training |
| Full BBj source code ingestion | Requires access controls and curation; start with training repo instead |
| JSONL conversion | Build when there's enough training data to justify it |
| Community content scraping | Legal/ethical review needed; defer to v1.7+ |
| Chat response extraction | Requires alpha usage first; defer until feedback loop established |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| API-01 | Phase 30 | Complete |
| API-02 | Phase 30 | Complete |
| API-03 | Phase 30 | Complete |
| API-04 | Phase 30 | Complete |
| API-05 | Phase 30 | Complete |
| TRAIN-01 | Phase 31 | Complete |
| TRAIN-02 | Phase 31 | Complete |
| TRAIN-03 | Phase 31 | Complete |
| TRAIN-04 | Phase 31 | Complete |

**Coverage:**
- v1.6 requirements: 9 total
- Mapped to phases: 9/9
- Unmapped: 0

---
*Requirements defined: 2026-02-05*
