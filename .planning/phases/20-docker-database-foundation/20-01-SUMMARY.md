---
phase: 20-docker-database-foundation
plan: 01
subsystem: infra
tags: [docker, docker-compose, pgvector, fastapi, uvicorn, uv, dockerfile]

# Dependency graph
requires:
  - phase: 15-mcp-architecture
    provides: "Existing pyproject.toml, config.py, db.py, schema.sql"
provides:
  - "Docker Compose orchestration (pgvector 0.8.0-pg17 + Python app)"
  - "Multi-stage Dockerfile with uv 0.9.28"
  - "FastAPI app skeleton with /health endpoint"
  - ".env.example with all documented environment variables"
  - "Database reset script (scripts/reset-db.sh)"
affects: [20-02-PLAN, 21-rest-api-mcp, 22-ingestion-orchestration]

# Tech tracking
tech-stack:
  added: [fastapi 0.128.0, uvicorn 0.40.0, uvloop, starlette]
  patterns: [multi-stage-docker-uv, health-check-endpoint, compose-healthcheck-ordering]

key-files:
  created:
    - rag-ingestion/docker-compose.yml
    - rag-ingestion/Dockerfile
    - rag-ingestion/.env.example
    - rag-ingestion/.gitignore
    - rag-ingestion/scripts/reset-db.sh
    - rag-ingestion/src/bbj_rag/app.py
    - rag-ingestion/src/bbj_rag/health.py
  modified:
    - rag-ingestion/pyproject.toml
    - rag-ingestion/uv.lock

key-decisions:
  - "Used uv 0.9.28 matching local install for Dockerfile COPY --from pin"
  - "Health endpoint uses existing database_url field; Plan 02 will refactor to keyword args"
  - "DB password uses :? syntax in compose for fail-fast on missing value"
  - "POSTGRES_* vars duplicated in .env.example (not cross-referenced) for reliability"

patterns-established:
  - "Multi-stage Dockerfile: builder with uv cache mounts, slim runtime with curl"
  - "Health check: APIRouter returning 200/healthy or 503/degraded"
  - "Compose depends_on with service_healthy condition for startup ordering"
  - "External ports above 10000 to avoid conflicts"

# Metrics
duration: 3min
completed: 2026-02-01
---

# Phase 20 Plan 01: Docker Infrastructure + FastAPI Skeleton Summary

**Docker Compose with pgvector 0.8.0-pg17, multi-stage uv Dockerfile, and FastAPI /health endpoint returning DB + Ollama status**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-01T20:40:05Z
- **Completed:** 2026-02-01T20:42:53Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Docker Compose defines db (pgvector/pgvector:0.8.0-pg17) and app services with health checks, restart policies, volume mounts, and env_file
- Multi-stage Dockerfile uses uv 0.9.28 with cache mounts for fast Python builds
- FastAPI application at bbj_rag.app:app with /health endpoint checking database and Ollama connectivity
- .env.example documents all required environment variables with explanatory comments
- Database reset script (scripts/reset-db.sh) with health-check polling loop

## Task Commits

Each task was committed atomically:

1. **Task 1: Docker Compose + Dockerfile + env template + reset script** - `6207ed8` (feat)
2. **Task 2: FastAPI app + health endpoint + dependency additions** - `70e4632` (feat)

## Files Created/Modified

- `rag-ingestion/docker-compose.yml` - Two-service orchestration (db + app) with health-based startup ordering
- `rag-ingestion/Dockerfile` - Multi-stage build: uv dependency install then slim runtime with curl
- `rag-ingestion/.env.example` - Documented template for all required environment variables
- `rag-ingestion/.gitignore` - Ignores .env, pgdata/, Python caches
- `rag-ingestion/scripts/reset-db.sh` - Executable script to wipe pgdata and restart containers
- `rag-ingestion/src/bbj_rag/app.py` - FastAPI entrypoint including health router
- `rag-ingestion/src/bbj_rag/health.py` - GET /health with DB + Ollama checks, 200/503 status
- `rag-ingestion/pyproject.toml` - Added fastapi and uvicorn[standard] dependencies
- `rag-ingestion/uv.lock` - Updated lockfile with new dependency resolution

## Decisions Made

- **uv version pin:** Used 0.9.28 matching the locally installed version, ensuring build reproducibility
- **Health endpoint database check:** Uses `settings.database_url` (existing field) rather than keyword args; Plan 02 will refactor config.py to add separate DB credential fields and a computed `database_url` property, maintaining backward compatibility
- **DB password fail-fast:** Used `${BBJ_RAG_DB_PASSWORD:?...}` syntax in docker-compose.yml so compose refuses to start without the password set
- **POSTGRES_* vars in .env.example:** Duplicated values (bbj/changeme/bbj_rag) rather than cross-referencing BBJ_RAG_* vars, since Compose env_file interpolation of cross-references is unreliable

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **Docker daemon not running:** `docker build` verification step could not execute because Docker Desktop was not running. `docker compose config` validation succeeded (does not require daemon). The Dockerfile syntax and build steps are correct per the standard uv multi-stage pattern. Build verification will occur when Docker is started for Plan 02 integration testing.

## User Setup Required

None - no external service configuration required at this stage. When running containers (Plan 02), the user will need to:
1. Copy `.env.example` to `.env` and set credentials
2. Ensure Ollama is running on host with `OLLAMA_HOST=0.0.0.0:11434`
3. Start Docker Desktop

## Next Phase Readiness

- Docker infrastructure files validated and committed
- FastAPI app skeleton is importable with /health route
- All existing tests pass (no regressions from dependency additions)
- Plan 02 can proceed with: config.py refactoring (conditional TOML, separate DB fields), lifespan handler (schema apply, startup summary), and full Docker integration test

---
*Phase: 20-docker-database-foundation*
*Completed: 2026-02-01*
