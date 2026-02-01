---
phase: 20-docker-database-foundation
plan: 02
subsystem: infra
tags: [pydantic-settings, config, docker, fastapi, lifespan, health-check, pgvector, startup]

# Dependency graph
requires:
  - phase: 20-docker-database-foundation
    provides: "Docker Compose, Dockerfile, FastAPI skeleton, health endpoint, .env.example"
provides:
  - "Settings class loading from env vars alone (no TOML crash in Docker)"
  - "Separate DB credential fields (db_host, db_port, db_user, db_password, db_name) with computed database_url property"
  - "FastAPI lifespan handler that validates env, logs startup summary, and applies schema idempotently"
  - "Startup validation and summary logging module (startup.py)"
  - "get_connection supporting keyword args or URL string"
  - "Docker stack verified: both containers healthy, schema applied, health endpoint serving"
affects: [21-data-config-ingestion, 22-rest-retrieval-api, 23-mcp-server]

# Tech tracking
tech-stack:
  added: []
  patterns: [conditional-toml-source, lifespan-schema-apply, keyword-arg-connections, startup-validation-logging]

key-files:
  created:
    - rag-ingestion/src/bbj_rag/startup.py
  modified:
    - rag-ingestion/src/bbj_rag/config.py
    - rag-ingestion/src/bbj_rag/db.py
    - rag-ingestion/src/bbj_rag/app.py
    - rag-ingestion/src/bbj_rag/health.py
    - rag-ingestion/tests/test_config.py

key-decisions:
  - "extra='ignore' in Settings model_config to silently skip old TOML database_url key"
  - "Conditional Path('config.toml').exists() check for TOML source inclusion"
  - "Soft warning for default password in production (not hard fail)"
  - "Imports inside lifespan function to avoid circular imports and side effects"

patterns-established:
  - "Conditional TOML source: only include TomlConfigSettingsSource when config.toml exists on disk"
  - "Lifespan schema apply: validate env, log startup, apply schema idempotently on every app start"
  - "Keyword-arg connections: get_connection accepts URL string or keyword args, get_connection_from_settings bridges Settings"
  - "Startup summary: bordered log block with Python version, DB host, Ollama URL, embedding model, environment"

# Metrics
duration: 5min
completed: 2026-02-01
---

# Phase 20 Plan 02: Config Refactor + Startup Wiring Summary

**Pydantic Settings with conditional TOML source and separate DB fields, FastAPI lifespan applying schema idempotently, and Docker stack verified healthy with startup summary logging**

## Performance

- **Duration:** ~5 min (across two sessions with checkpoint)
- **Started:** 2026-02-01T20:45:00Z
- **Completed:** 2026-02-01T21:18:00Z
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 6

## Accomplishments

- Config.py loads from environment variables alone when config.toml is absent (fixes Docker crash), with conditional TOML source for backward compatibility in local dev
- Separate DB credential fields (db_host, db_port, db_user, db_password, db_name) with computed database_url property maintaining full backward compatibility
- FastAPI lifespan validates environment, logs structured startup summary, and applies pgvector schema idempotently on every app start
- db.py get_connection supports both URL string and keyword args; get_connection_from_settings bridges Settings object cleanly
- startup.py provides validate_environment() and log_startup_summary() for production-ready startup behavior
- Docker stack verified: both containers reach healthy state, schema applied, health endpoint returns DB status, startup summary logged

## Task Commits

Each task was committed atomically:

1. **Task 1: Refactor config.py + update db.py + create startup.py** - `e922243` (feat)
2. **Task 2: Wire app.py lifespan + update health.py** - `24ace70` (feat)
3. **Task 3: Docker verification checkpoint** - (human-verify, approved)

## Files Created/Modified

- `rag-ingestion/src/bbj_rag/config.py` - Settings with conditional TOML source, separate DB credential fields, computed database_url property, extra="ignore"
- `rag-ingestion/src/bbj_rag/db.py` - get_connection with URL or keyword args, get_connection_from_settings convenience function
- `rag-ingestion/src/bbj_rag/startup.py` - (new) validate_environment() and log_startup_summary() with bordered output
- `rag-ingestion/src/bbj_rag/app.py` - FastAPI lifespan handler calling validate_environment, log_startup_summary, apply_schema
- `rag-ingestion/src/bbj_rag/health.py` - Updated to use keyword args from Settings, JSONResponse with 503 for degraded
- `rag-ingestion/tests/test_config.py` - 2 new tests for separate DB fields and computed database_url property

## Decisions Made

- **extra="ignore" in model_config:** Existing config.toml has `database_url` as a single field. Since database_url is now a computed property (not a Field), the TOML key is silently ignored via extra="ignore". This avoids breaking local dev setups that still have the old TOML format.
- **Conditional TOML source:** `Path("config.toml").exists()` check ensures Docker containers (which lack config.toml) never attempt TOML loading. Local dev with config.toml present continues to work normally.
- **Soft warning for default password:** validate_environment() warns but does not fail when DB_PASSWORD is the default "postgres" in production. Hard fail would break development workflows; the Docker Compose :? syntax already enforces password presence at compose level.
- **Imports inside lifespan:** All heavy imports (config, startup, schema, db) are inside the lifespan function to keep the module importable without side effects, important for test isolation.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no additional external service configuration required beyond what Plan 01 documented.

## Next Phase Readiness

- Phase 20 is complete: Docker + Database foundation fully operational
- Both containers start to healthy state via `docker compose up`
- pgvector schema applied automatically on app startup
- Settings work purely from environment variables (Docker) or TOML (local dev)
- Health endpoint reports DB and Ollama connectivity status
- Ready for Phase 21: Data Configuration + Ingestion (real source path wiring and corpus ingestion)
- All 312 tests pass (310 original + 2 new config tests)

---
*Phase: 20-docker-database-foundation*
*Completed: 2026-02-01*
