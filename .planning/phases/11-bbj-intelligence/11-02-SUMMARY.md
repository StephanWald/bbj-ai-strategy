---
phase: 11-bbj-intelligence
plan: 02
subsystem: intelligence
tags: [strenum, classifier, rule-engine, context-header, heading-extraction, markdown, dedup]

# Dependency graph
requires:
  - phase: 11-01
    provides: Intelligence package with Generation tagger, __init__.py exports
  - phase: 10-flare-parser
    provides: web_crawl.url_to_hierarchy(), Document/Chunk models, TOC breadcrumbs
provides:
  - DocType StrEnum with 7 semantic document categories
  - Rule-based document type classifier (data-driven, extensible)
  - Contextual header builder with TOC breadcrumb + title deduplication
  - Heading hierarchy extractor from markdown content
  - URL-path hierarchy adapter for web crawl documents
  - Complete intelligence package public API (8 exports)
affects:
  - phase: 12
    needs: classify_doc_type() for type-filtered retrieval, build_context_header() for chunk enrichment, extract_heading_hierarchy() for classifier input

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Data-driven rule registry with frozen dataclass rules and weighted scoring
    - StrEnum with explicit hyphenated string values for storage compatibility
    - Arrow-separated context strings for embedding hierarchy context

# File tracking
key-files:
  created:
    - rag-ingestion/src/bbj_rag/intelligence/doc_types.py
    - rag-ingestion/src/bbj_rag/intelligence/context_headers.py
    - rag-ingestion/tests/test_doc_types.py
    - rag-ingestion/tests/test_context_headers.py
  modified:
    - rag-ingestion/src/bbj_rag/intelligence/__init__.py

# Decisions
decisions:
  - id: d11-02-01
    decision: "Rules without required_headings use min_score=0.15 (not 0.5)"
    rationale: "Without required headings (+0.4 bonus), rules relying solely on optional headings/path/content signals cannot reach 0.5. Lower threshold prevents false negatives for migration, example, best-practice, and version-note types."
  - id: d11-02-02
    decision: "API reference boost of +0.2 when Parameters or Return Value present alongside Syntax"
    rationale: "Ensures API reference wins over language reference when both have Syntax heading but API reference has the distinguishing Parameters/Return Value headings."
  - id: d11-02-03
    decision: "url_path_to_hierarchy delegates to web_crawl.url_to_hierarchy rather than reimplementing"
    rationale: "Single source of truth for URL-to-hierarchy logic. Intelligence package provides a convenience re-export for consistent import paths."

# Metrics
metrics:
  duration: 4min
  completed: 2026-01-31
---

# Phase 11 Plan 02: Doc Type Classifier / Context Headers Summary

Rule-based 7-type document classifier with extensible frozen-dataclass rule registry, plus contextual header builder combining TOC breadcrumbs with page titles for embedding hierarchy context.

## What Was Built

### Document Type Classifier (`doc_types.py`)
- **DocType StrEnum** with 7 members: `api-reference`, `concept`, `example`, `migration`, `language-reference`, `best-practice`, `version-note`
- **DocTypeRule frozen dataclass** with required/optional headings, path/content regex patterns, and per-rule min_score thresholds
- **Rule registry** (`_RULES` list) ordered by specificity -- adding a new type means adding a new rule, not restructuring the classifier
- **Scoring function** (`_score_rule`) accumulates points: +0.4 for required headings, +0.15/optional (capped 0.45), +0.2 for path match, +0.15 for content match
- **API reference boost**: +0.2 when Parameters/Return Value + Syntax detected, ensuring separation from language-reference
- **Concept fallback**: min_score=0.0, always matches when nothing else does

### Contextual Header Builder (`context_headers.py`)
- **`build_context_header()`**: Combines section_path + title + heading_path with ` > ` separator and title deduplication
- **`extract_heading_hierarchy()`**: Parses markdown `#`-headings into flat text list for classifier input
- **`url_path_to_hierarchy()`**: Delegates to `web_crawl.url_to_hierarchy()` for web crawl documents

### Updated Package API (`__init__.py`)
Full public API now exports 8 symbols: `DocType`, `Generation`, `build_context_header`, `build_report`, `classify_doc_type`, `extract_heading_hierarchy`, `print_report`, `tag_generation`

## Test Coverage

- **test_doc_types.py**: 14 tests -- enum values, all 7 classification types, API/language reference discrimination, extensibility verification
- **test_context_headers.py**: 15 tests -- header building with full/partial inputs, title deduplication, heading extraction at all levels, URL hierarchy delegation

**Full suite**: 206 passed, 1 skipped (pre-existing slow test)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Rules without required headings had unreachable min_score**
- **Found during:** Task 1 test execution
- **Issue:** Migration, example, best-practice, and version-note rules had default min_score=0.5, but without required headings they could only score max 0.45 (optional) + 0.2 (path) + 0.15 (content) = 0.80 with all signals, and typically scored 0.15-0.30 with realistic inputs
- **Fix:** Set min_score=0.15 for rules that have no required_headings
- **Files modified:** `rag-ingestion/src/bbj_rag/intelligence/doc_types.py`
- **Commit:** 0107fea

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 0107fea | feat | Document type classifier with extensible rule registry |
| df8260c | feat | Contextual header builder and heading extractor |

## Next Phase Readiness

Phase 11 (BBj Intelligence) is now complete with all 2 plans executed:
- **11-01**: Generation tagger (5 generations, multi-signal scoring)
- **11-02**: Doc type classifier (7 types) + context headers

The intelligence package provides the full classification and enrichment pipeline needed by the chunker (Phase 12): `tag_generation()` for generation labels, `classify_doc_type()` for semantic type filtering, `build_context_header()` for embedding hierarchy context, and `extract_heading_hierarchy()` for feeding headings to the classifier.
