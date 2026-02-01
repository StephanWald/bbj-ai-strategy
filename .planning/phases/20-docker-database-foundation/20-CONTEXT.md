# Phase 20: Docker + Database Foundation - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

`docker compose up` starts pgvector and Python app containers with schema applied, Ollama reachable from the app container, source data mounted, and configuration driven by environment variables. Host Ollama (not containerized) for macOS Metal GPU acceleration. No ingestion, no API endpoints, no MCP -- just the running infrastructure foundation.

</domain>

<decisions>
## Implementation Decisions

### Container startup & health
- Restart policy: `unless-stopped` -- auto-restart on failure, stays down when manually stopped
- App container exposes `/health` endpoint that Docker monitors -- reports DB + Ollama connectivity status
- Startup summary logged on boot: versions, DB connection status, Ollama reachability, mounted paths

### Schema initialization
- Schema checked/applied every startup (idempotent) -- creates tables if missing, skips if present
- Plain SQL scripts, no Alembic -- simple `.sql` files run at startup
- No schema drift detection -- assume schema is correct if tables exist
- Provide an explicit reset script/command to wipe and reinitialize (not just `docker compose down -v`)

### Volume mount & data layout
- All source data assumed to be organized under a single "ingestion" parent directory on the host, mounted as one volume into the container
- pgvector database data persists via host-mounted directory (bind mount), not a named Docker volume -- easy to inspect and backup directly

### Configuration & secrets
- Fail fast on missing required env vars -- app refuses to start, prints exactly which vars are missing
- `.env.example` file checked into repo with all vars documented -- user copies to `.env`
- Database credentials as separate env vars: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` (not a single connection string)
- Ollama host URL defaults to `host.docker.internal:11434` -- works out of the box on macOS Docker
- External port mapped above 10000 (e.g., 10800) to avoid conflicts with common services; internal port can be standard (e.g., 8000)
- Dev mode via `ENV=development` -- enables verbose logging, auto-reload, debug endpoints

### Claude's Discretion
- Container startup ordering strategy (depends_on health check vs internal retry)
- Source data mount read-only vs read-write
- .env loading method (auto-load vs explicit env_file directive)
- Embedding model name: configurable env var vs hardcoded
- Exact reset script implementation
- Startup summary format and detail level

</decisions>

<specifics>
## Specific Ideas

- External port should be above 10000 to avoid conflicts (user specified this explicitly)
- Single ingestion directory assumption: all 6 sources should be subdirectories under one mountable parent, rather than scattered across the host filesystem
- Host-mounted DB directory preference is for easy direct inspection and backup

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 20-docker-database-foundation*
*Context gathered: 2026-02-01*
