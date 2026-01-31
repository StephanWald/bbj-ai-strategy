---
phase: 09-schema-data-models
plan: 01
subsystem: database
tags: [pydantic, config, toml, sha256, validation]
requires:
  - phase: 08-project-scaffold-readme
    provides: Python project scaffold with uv
provides:
  - Document and Chunk Pydantic models with validation
  - Settings configuration system (TOML + env vars)
  - Content-hash deduplication via SHA-256
affects: [09-schema-data-models plan 02, 10-flare-parser, 11-bbj-intelligence, 12-embedding-pipeline]
tech-stack:
  added: [pydantic, pydantic-settings, psycopg, pgvector]
  patterns: [Pydantic model validation, content hashing, TOML config]
key-files:
  created: [models.py, config.py, config.toml, test_models.py, test_config.py]
  modified: [pyproject.toml]
key-decisions:
  - "Field defaults in Settings serve as fallbacks when TOML/env are absent (useful for tests)"
  - "str_strip_whitespace=True on both models to normalize input at boundary"
  - "Chunk.from_content() is the canonical factory -- hash computed on stripped content to prevent whitespace-only duplicates"
  - "settings_customise_sources override required for TomlConfigSettingsSource in pydantic-settings 2.12"
  - "ClassVar _toml_source used to satisfy mypy strict mode for the TomlConfigSettingsSource reference"
patterns-established:
  - "Pydantic models with extra='forbid' and str_strip_whitespace as data contracts"
  - "Content-hash deduplication via SHA-256 on normalized text"
  - "TOML + env var configuration with BBJ_RAG_ prefix and clear priority chain"
duration: 4min
completed: 2026-01-31
---

# Phase 09 Plan 01: Pydantic Data Models and Configuration Summary

**One-liner:** Document/Chunk Pydantic models with SHA-256 content-hash dedup and TOML+env var Settings via pydantic-settings.

## What Was Done

### Task 1: Add runtime dependencies and create Pydantic data models
- Added `psycopg[binary]>=3.3`, `pgvector>=0.4`, `pydantic>=2.12`, `pydantic-settings>=2.12` to pyproject.toml
- Created `models.py` with Document and Chunk models
- Document validates: non-empty content, non-empty generations, forbids extra fields, strips whitespace
- Chunk adds `content_hash` and optional `embedding` fields
- `Chunk.from_content()` factory computes SHA-256 hash on `content.strip()` for dedup consistency
- **Commit:** `3f0ad17`

### Task 2: Create configuration system with TOML and env var support
- Created `config.py` with Settings class extending pydantic-settings BaseSettings
- Created `config.toml` with all default values (database_url, embedding_model, dimensions, chunk sizes, source paths)
- Priority chain: constructor args > BBJ_RAG_ env vars > config.toml > field defaults
- Required `settings_customise_sources` override to register TomlConfigSettingsSource
- **Commit:** `a02ebe8`

### Task 3: Add unit tests for models, config, and content hashing
- 11 model tests: valid construction, empty content/generations rejected, extra fields rejected, whitespace stripping, hash computation/determinism/uniqueness, optional embedding, empty content in from_content
- 3 config tests: default values loaded, BBJ_RAG_CHUNK_SIZE override, BBJ_RAG_DATABASE_URL override
- Removed scaffold placeholder test
- All 14 tests pass, ruff clean, mypy strict clean
- **Commit:** `3976e26`

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Field defaults in Settings as fallbacks | Allows Settings() instantiation without TOML in tests |
| str_strip_whitespace=True on models | Normalizes all string input at the pipeline boundary |
| from_content() as canonical Chunk factory | Ensures hash consistency -- direct construction would allow hash/content mismatch |
| settings_customise_sources override | Required by pydantic-settings 2.12 to actually load TOML sources |

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

| Check | Result |
|-------|--------|
| `uv sync` | 33 packages resolved, 31 audited |
| `pytest -v` | 14/14 passed |
| `ruff check src/ tests/` | All checks passed |
| `mypy src/bbj_rag/` | No issues found (3 source files) |
| All imports succeed | Document, Chunk, Settings importable |
| No hardcoded values in models.py | Config values only in config.py defaults and config.toml |

## Artifacts Produced

| File | Purpose |
|------|---------|
| `rag-ingestion/src/bbj_rag/models.py` | Document and Chunk Pydantic models |
| `rag-ingestion/src/bbj_rag/config.py` | Settings class with TOML + env var loading |
| `rag-ingestion/config.toml` | Default configuration values |
| `rag-ingestion/tests/test_models.py` | 11 unit tests for model validation and hashing |
| `rag-ingestion/tests/test_config.py` | 3 unit tests for config loading and overrides |
| `rag-ingestion/pyproject.toml` | Updated with runtime dependencies |

## Next Phase Readiness

Plan 09-02 (database schema and pgvector setup) can proceed. The Document and Chunk models provide stable contracts for:
- Parser output (Document) used by 10-flare-parser and web crawl ingestion
- Storage format (Chunk) used by 12-embedding-pipeline and database layer
- Configuration (Settings) used by all pipeline components

No blockers or concerns.
