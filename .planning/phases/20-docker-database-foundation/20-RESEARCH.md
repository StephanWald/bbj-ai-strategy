# Phase 20: Docker + Database Foundation - Research

**Researched:** 2026-02-01
**Domain:** Docker Compose, pgvector, Python containerization, Pydantic Settings
**Confidence:** HIGH

## Summary

This phase creates the containerized infrastructure foundation: Docker Compose orchestrates a pgvector PostgreSQL container and a Python app container, with schema auto-initialization, host Ollama connectivity, volume-mounted source data, and environment-variable-driven configuration.

The standard approach is well-established: the `pgvector/pgvector:0.8.0-pg17` image extends the official PostgreSQL image (all standard Postgres env vars work), schema SQL files go into `/docker-entrypoint-initdb.d/` for first-run initialization and are also applied idempotently by the app on every startup, and the Python app is built on `python:3.12-slim-bookworm` with `uv` copied from `ghcr.io/astral-sh/uv`. The existing codebase already has `schema.py` (reads `sql/schema.sql` and runs it idempotently), `db.py` (psycopg3 with pgvector), and `config.py` (pydantic-settings with TOML source). The main work is: (1) writing `docker-compose.yml` and `Dockerfile`, (2) refactoring `config.py` to work without TOML and with separate DB credentials, (3) adding a `/health` endpoint, (4) wiring up Ollama host configuration, and (5) creating a startup summary logger.

**Primary recommendation:** Use `depends_on` with `condition: service_healthy` and `pg_isready` for startup ordering. Mount source data read-only. Use `env_file` directive with a `.env` file. Refactor `config.py` to conditionally include TOML source only when the file exists, keeping backward compatibility for local dev while working purely from env vars in Docker.

## Standard Stack

### Core

| Library/Tool | Version | Purpose | Why Standard |
|---|---|---|---|
| `pgvector/pgvector` | `0.8.0-pg17` | PostgreSQL 17 + pgvector extension | Official image, extends postgres:17, pgvector pre-installed |
| `python` (Docker) | `3.12-slim-bookworm` | Python app base image | Lightweight Debian base, matches project's Python version |
| `uv` | Pin to `0.9.x` | Python dependency installer | 10-100x faster than pip, used in existing project Makefile |
| `psycopg[binary]` | `>=3.3,<4` | PostgreSQL driver | Already in pyproject.toml, supports keyword-arg connections |
| `pgvector` (Python) | `>=0.4,<0.5` | pgvector type registration | Already in pyproject.toml |
| `pydantic-settings` | `>=2.12,<3` | Configuration from env vars | Already in pyproject.toml, supports `settings_customise_sources` |
| `ollama` (Python) | `>=0.6,<1` | Embedding client | Already in pyproject.toml, reads `OLLAMA_HOST` env var |
| `httpx` | `>=0.28,<1` | HTTP client for health checks | Already in pyproject.toml |

### Supporting

| Library/Tool | Version | Purpose | When to Use |
|---|---|---|---|
| `uvicorn` | `>=0.34,<1` | ASGI server for health endpoint | **NEW dependency** -- needed to serve `/health` |
| `fastapi` | `>=0.115,<1` | Minimal API framework for `/health` | **NEW dependency** -- lightweight, standard for Python APIs |
| `psycopg.conninfo.make_conninfo` | (part of psycopg) | Build connection string from parts | When constructing DB URL from separate env vars |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|---|---|---|
| FastAPI for `/health` | Plain `http.server` | FastAPI is already the planned API framework for future phases; start with it now |
| `uv sync --frozen` | `pip install` | uv is 10-100x faster and already used in the project |
| Bind mount for PG data | Named Docker volume | User decision is bind mount for inspectability; named volume would be 3-10x faster on macOS (see Pitfalls) |

### Installation (new dependencies)

```bash
cd rag-ingestion
uv add "fastapi>=0.115,<1" "uvicorn[standard]>=0.34,<1"
```

## Architecture Patterns

### Recommended Project Structure

```
rag-ingestion/
├── docker-compose.yml          # Orchestrates db + app services
├── Dockerfile                  # Multi-stage build for Python app
├── .env.example                # Documented env var template (committed)
├── .env                        # Actual env vars (gitignored)
├── sql/
│   └── schema.sql              # Existing idempotent DDL
├── scripts/
│   └── reset-db.sh             # Wipe and reinitialize database
├── src/bbj_rag/
│   ├── config.py               # Refactored: optional TOML, env-only in Docker
│   ├── db.py                   # Refactored: accept keyword args or conninfo
│   ├── health.py               # NEW: FastAPI /health endpoint
│   ├── startup.py              # NEW: Startup summary + env validation
│   └── app.py                  # NEW: FastAPI app entrypoint
│   └── ...                     # Existing modules unchanged
└── ...
```

### Pattern 1: Multi-Stage Docker Build with uv

**What:** Separate dependency installation from source code copying for optimal layer caching.
**When to use:** Always for Python Docker images with uv.

```dockerfile
# Stage 1: Build dependencies
FROM python:3.12-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1

WORKDIR /app

# Install dependencies first (layer cache)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Copy project source and install
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Stage 2: Runtime
FROM python:3.12-slim-bookworm

# Install curl for Docker health check
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "bbj_rag.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 2: Docker Compose with Health-Based Startup Ordering

**What:** Use `depends_on` with `condition: service_healthy` so the app waits for PostgreSQL to accept connections.
**When to use:** Always when app depends on database availability.

```yaml
services:
  db:
    image: pgvector/pgvector:0.8.0-pg17
    restart: unless-stopped
    shm_size: 256mb
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    ports:
      - "${DB_PORT_EXTERNAL:-10432}:5432"
    volumes:
      - ./pgdata:/var/lib/postgresql/data
      - ./sql/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  app:
    build: .
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
        restart: true
    env_file:
      - path: .env
        required: true
    environment:
      - DB_HOST=db
      - OLLAMA_HOST=http://host.docker.internal:11434
    ports:
      - "${APP_PORT_EXTERNAL:-10800}:8000"
    volumes:
      - ${INGESTION_DATA_PATH:-./_data}:/data:ro
    extra_hosts:
      - "host.docker.internal:host-gateway"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s
```

### Pattern 3: Conditional TOML Source in Pydantic Settings

**What:** Settings work from env vars alone (Docker) but still support TOML for local development.
**When to use:** When the same Settings class must work in both containerized and local environments.

```python
from pathlib import Path
from pydantic_settings import (
    BaseSettings, PydanticBaseSettingsSource,
    SettingsConfigDict, TomlConfigSettingsSource,
)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BBJ_RAG_",
        toml_file="config.toml",
    )

    # Separate DB credentials (not a single URL)
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "bbj_rag"

    # ... other fields ...

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        sources: list[PydanticBaseSettingsSource] = [
            init_settings,
            env_settings,
        ]
        # Only add TOML if file exists (skip in Docker)
        toml_path = Path("config.toml")
        if toml_path.exists():
            sources.append(TomlConfigSettingsSource(settings_cls))
        return tuple(sources)

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
```

### Pattern 4: Fail-Fast Environment Validation

**What:** Validate all required env vars at startup before attempting connections.
**When to use:** Always in containerized apps. Print exactly which vars are missing.

```python
import sys
import os

REQUIRED_VARS = ["DB_USER", "DB_PASSWORD", "DB_NAME"]

def validate_environment() -> None:
    missing = [v for v in REQUIRED_VARS if not os.getenv(f"BBJ_RAG_{v}")]
    if missing:
        prefixed = [f"BBJ_RAG_{v}" for v in missing]
        print(f"FATAL: Missing required environment variables: {', '.join(prefixed)}", file=sys.stderr)
        sys.exit(1)
```

Note: Pydantic Settings will also raise `ValidationError` if required fields have no default and no env var. The explicit check above provides a cleaner error message. However, since all fields in the current Settings have defaults, the explicit validation may be needed for fields like `DB_PASSWORD` that should not have a usable default in production.

### Pattern 5: Health Endpoint with Dependency Checks

**What:** `/health` endpoint that checks DB connectivity and Ollama reachability.
**When to use:** Required by Docker HEALTHCHECK and for operational visibility.

```python
from fastapi import FastAPI
import psycopg
import httpx

app = FastAPI()

@app.get("/health")
async def health():
    checks = {}

    # Check database
    try:
        settings = get_settings()
        conn = psycopg.connect(settings.database_url)
        conn.execute("SELECT 1")
        conn.close()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Check Ollama
    try:
        ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ollama_host}/api/tags", timeout=5.0)
            resp.raise_for_status()
        checks["ollama"] = "ok"
    except Exception as e:
        checks["ollama"] = f"error: {e}"

    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

### Anti-Patterns to Avoid

- **Single connection string env var for DB**: The user decided on separate `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` vars. Do not combine into `DATABASE_URL`. Construct the conninfo at runtime.
- **Hardcoding Ollama URL**: The `ollama` Python library reads `OLLAMA_HOST` env var automatically. Set it in `docker-compose.yml` environment section; do not hardcode in Python code.
- **Installing curl in builder stage**: Only install curl in the runtime stage (for Docker HEALTHCHECK). Keep the builder stage minimal.
- **Using `uv sync --locked` instead of `--frozen`**: Use `--frozen` in Docker builds to fail if lockfile is stale rather than updating it.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Connection string construction | Manual f-string with password | `psycopg.conninfo.make_conninfo()` | Handles special chars in passwords, proper escaping |
| PostgreSQL readiness check | TCP socket probe | `pg_isready` (built into postgres image) | Official tool, checks actual PG protocol, not just TCP |
| Python dependency install in Docker | `pip install -r requirements.txt` | `uv sync --frozen` | 10-100x faster, lockfile ensures reproducibility |
| Schema initialization | Custom Python init script | `docker-entrypoint-initdb.d/` + app-level `schema.py` | PG entrypoint handles first-run; `schema.py` handles subsequent startups |
| TOML-absent crash handling | try/except around file read | Conditional `TomlConfigSettingsSource` in `settings_customise_sources` | Clean, no exception handling needed, pydantic-settings native pattern |
| Docker health check | Custom script | `curl -f http://localhost:PORT/health` | Standard, lightweight, built into curl |

**Key insight:** The pgvector image inherits all PostgreSQL Docker image behaviors, including `/docker-entrypoint-initdb.d/` processing and `pg_isready`. Do not reimplement these capabilities.

## Common Pitfalls

### Pitfall 1: TOML Config Crash in Docker

**What goes wrong:** The current `config.py` unconditionally creates `TomlConfigSettingsSource(settings_cls)` which reads `config.toml`. Inside the Docker container, `config.toml` does not exist, causing a `FileNotFoundError` crash on startup.
**Why it happens:** `SettingsConfigDict(toml_file="config.toml")` combined with `TomlConfigSettingsSource(settings_cls)` in `settings_customise_sources` attempts to read the file.
**How to avoid:** Wrap `TomlConfigSettingsSource` in a `Path("config.toml").exists()` check. Only include it in the sources tuple when the file is present.
**Warning signs:** App container exits immediately with a traceback mentioning `config.toml` or `FileNotFoundError`.

### Pitfall 2: Bind Mount PG Data on macOS is 3-10x Slower

**What goes wrong:** The user decided to use bind mounts for PG data (`./pgdata:/var/lib/postgresql/data`) for inspectability. On macOS, bind mounts go through the VirtioFS/gRPC-FUSE virtualization layer, making database I/O 3-10x slower than named volumes.
**Why it happens:** Docker on macOS runs inside a Linux VM; bind mounts cross the host-VM boundary. Named volumes stay entirely within the VM.
**How to avoid:** This is an accepted tradeoff per user decision. Document the performance impact. If performance becomes an issue, switching to a named volume is a one-line change in `docker-compose.yml`. For this foundation phase (no real data yet), performance is not a concern.
**Warning signs:** Slow ingestion times, high CPU from Docker VM processes.

### Pitfall 3: `docker-entrypoint-initdb.d` Only Runs on Empty Data Dir

**What goes wrong:** Schema SQL mounted into `/docker-entrypoint-initdb.d/` only executes when the PG data directory is empty (first startup). Subsequent startups skip it entirely, even if schema changed.
**Why it happens:** This is by design in the official PostgreSQL Docker image. It prevents re-initialization of an existing database.
**How to avoid:** Use dual initialization: (1) mount SQL in `docker-entrypoint-initdb.d/` for first run, and (2) run `schema.py` (apply_schema) from the app on every startup for idempotent updates. The existing `schema.sql` uses `IF NOT EXISTS` throughout, making it safe.
**Warning signs:** Schema changes not appearing after restart (without volume wipe).

### Pitfall 4: `host.docker.internal` Requires Ollama Bound to 0.0.0.0

**What goes wrong:** App container cannot reach host Ollama even with `host.docker.internal:11434` configured.
**Why it happens:** By default, Ollama binds to `127.0.0.1` (localhost only). Docker containers access the host via a virtual network interface, not localhost. The connection is refused because Ollama is not listening on the interface Docker uses.
**How to avoid:** Require `OLLAMA_HOST=0.0.0.0:11434` on the host machine before starting Ollama. On macOS, set via `launchctl setenv OLLAMA_HOST "0.0.0.0"` and restart Ollama. Document this requirement prominently.
**Warning signs:** Connection refused errors from the app container to `host.docker.internal:11434`.

### Pitfall 5: shm_size Too Small for HNSW Index Builds

**What goes wrong:** Parallel HNSW index builds fail or degrade when `shm_size` is smaller than `maintenance_work_mem`.
**Why it happens:** PostgreSQL uses shared memory for parallel workers. Docker's default `shm_size` is 64MB, which is insufficient for HNSW graph construction.
**How to avoid:** Set `shm_size: 256mb` in `docker-compose.yml` for the db service. This matches the blocker note in the phase requirements. For real corpus builds, consider increasing to 512mb or 1gb.
**Warning signs:** `ERROR: could not resize shared memory segment` or index builds that are extremely slow.

### Pitfall 6: Ollama Python Client Ignores OLLAMA_HOST in Module-Level Calls

**What goes wrong:** The current `embedder.py` uses `ollama_client.embed()` (module-level function). The `ollama` library reads `OLLAMA_HOST` env var at client initialization time. If the env var is set in the Docker container, the module-level functions should respect it.
**Why it happens:** The module-level functions in the `ollama` package create an implicit default client that reads `OLLAMA_HOST`. This should work, but testing is needed to confirm.
**How to avoid:** Verify that `OLLAMA_HOST` env var is read by `ollama.embed()`. If not, switch to explicit `Client(host=...)` initialization.
**Warning signs:** Embedding calls fail with connection refused to `127.0.0.1:11434` despite `OLLAMA_HOST` being set.

### Pitfall 7: PG Data Volume Mount Path Must Be Exact

**What goes wrong:** Mounting to `/var/lib/postgresql` instead of `/var/lib/postgresql/data` causes data loss on container recreation.
**Why it happens:** PostgreSQL stores data in the `data` subdirectory. Mounting at the parent directory interferes with the entrypoint script's directory structure expectations.
**How to avoid:** Always mount to `/var/lib/postgresql/data` exactly.
**Warning signs:** Database appears empty after container restart despite volume being present.

## Code Examples

### Docker Compose env_file with .env

```yaml
# docker-compose.yml
services:
  app:
    env_file:
      - path: .env
        required: true
    environment:
      # Override DB_HOST for inter-container networking
      - BBJ_RAG_DB_HOST=db
```

### .env.example Template

```bash
# Database credentials
BBJ_RAG_DB_HOST=localhost
BBJ_RAG_DB_PORT=5432
BBJ_RAG_DB_USER=bbj
BBJ_RAG_DB_PASSWORD=changeme
BBJ_RAG_DB_NAME=bbj_rag

# Ollama (host machine)
OLLAMA_HOST=http://host.docker.internal:11434

# Embedding
BBJ_RAG_EMBEDDING_MODEL=qwen3-embedding:0.6b
BBJ_RAG_EMBEDDING_DIMENSIONS=1024
BBJ_RAG_EMBEDDING_PROVIDER=ollama

# Application
ENV=production
APP_PORT_EXTERNAL=10800

# Source data path (host machine)
INGESTION_DATA_PATH=./data

# Postgres container vars (used by pgvector image directly)
POSTGRES_USER=${BBJ_RAG_DB_USER}
POSTGRES_PASSWORD=${BBJ_RAG_DB_PASSWORD}
POSTGRES_DB=${BBJ_RAG_DB_NAME}
```

### Constructing Connection String from Separate Vars

```python
# Using psycopg.conninfo.make_conninfo for safe escaping
from psycopg.conninfo import make_conninfo

def build_conninfo(settings: Settings) -> str:
    return make_conninfo(
        "",
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        dbname=settings.db_name,
    )
```

Or use keyword arguments directly with `psycopg.connect()`:

```python
conn = psycopg.connect(
    host=settings.db_host,
    port=settings.db_port,
    user=settings.db_user,
    password=settings.db_password,
    dbname=settings.db_name,
)
```

### Reset Script

```bash
#!/usr/bin/env bash
# scripts/reset-db.sh -- Wipe and reinitialize the database
set -euo pipefail

COMPOSE_CMD="docker compose"

echo "Stopping containers..."
$COMPOSE_CMD down

echo "Removing pgdata directory..."
rm -rf ./pgdata

echo "Starting fresh (schema will be applied on first run)..."
$COMPOSE_CMD up -d

echo "Waiting for healthy state..."
$COMPOSE_CMD exec app curl -sf http://localhost:8000/health || echo "Waiting..."
sleep 5
$COMPOSE_CMD exec app curl -sf http://localhost:8000/health

echo "Reset complete."
```

### Startup Summary Logger

```python
import logging
import sys

logger = logging.getLogger("bbj_rag.startup")

def log_startup_summary(settings: Settings) -> None:
    logger.info("=" * 60)
    logger.info("BBJ RAG - Startup Summary")
    logger.info("=" * 60)
    logger.info(f"  Python:     {sys.version.split()[0]}")
    logger.info(f"  DB Host:    {settings.db_host}:{settings.db_port}")
    logger.info(f"  DB Name:    {settings.db_name}")
    logger.info(f"  DB User:    {settings.db_user}")
    logger.info(f"  Ollama:     {os.getenv('OLLAMA_HOST', '127.0.0.1:11434')}")
    logger.info(f"  Model:      {settings.embedding_model}")
    logger.info(f"  Dimensions: {settings.embedding_dimensions}")
    logger.info(f"  ENV:        {os.getenv('ENV', 'production')}")
    logger.info("=" * 60)
```

### Linux extra_hosts Compatibility

```yaml
# Required for Linux Docker (not Docker Desktop)
# macOS Docker Desktop resolves host.docker.internal automatically
services:
  app:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

## Discretion Recommendations

These are areas marked as Claude's Discretion in CONTEXT.md:

### Container Startup Ordering: `depends_on` with health check (RECOMMENDED)

**Recommendation:** Use `depends_on` with `condition: service_healthy` rather than internal retry logic.

**Rationale:** The `pg_isready` health check on the db service is lightweight, authoritative, and built into the postgres image. The app container will not start until PG is actually ready. The `restart: true` option ensures the app restarts if the db is restarted. This is simpler and more reliable than implementing retry/backoff logic in the Python app.

No internal retry logic is needed for the database. The app may still want retry logic for Ollama (since it is external and may not be running), but that is a graceful degradation concern, not a startup ordering concern.

### Source Data Mount: Read-Only (RECOMMENDED)

**Recommendation:** Mount source data as read-only (`:ro` suffix or `read_only: true`).

**Rationale:** The app container only reads source data for ingestion. Write access would be a security risk and could lead to accidental modification. Using `:ro` in the short syntax is the simplest approach: `${INGESTION_DATA_PATH}:/data:ro`.

### .env Loading: `env_file` Directive (RECOMMENDED)

**Recommendation:** Use `env_file` directive in `docker-compose.yml` rather than relying on auto-loading.

**Rationale:** Explicit `env_file` is self-documenting in the compose file. Using `required: true` (Compose 2.24.0+) fails fast with a clear error if `.env` is missing. Auto-loading the `.env` file (default Compose behavior) is implicit and can cause confusing behavior when the file is absent.

### Embedding Model Name: Configurable via Env Var (RECOMMENDED)

**Recommendation:** Keep `BBJ_RAG_EMBEDDING_MODEL` as a configurable env var with the current default (`qwen3-embedding:0.6b`).

**Rationale:** The model is already configurable via `settings.embedding_model`. Making it an env var in Docker is trivial (it already works via `BBJ_RAG_EMBEDDING_MODEL`). Hardcoding would reduce flexibility for no benefit.

### Reset Script: Shell Script that Removes pgdata and Restarts (RECOMMENDED)

**Recommendation:** `scripts/reset-db.sh` that runs `docker compose down`, removes `./pgdata`, and runs `docker compose up -d`.

**Rationale:** Simpler than a SQL-based reset. Because the schema is applied both via `docker-entrypoint-initdb.d` (first run) and `schema.py` (every startup), a fresh data directory triggers clean initialization. The script is explicit about what it does and cannot leave partial state.

### Startup Summary: Structured Log Lines (RECOMMENDED)

**Recommendation:** Log key configuration values as structured INFO lines on startup, after successful env validation but before serving requests.

**Rationale:** Plain structured log lines (not JSON) are easy to read in `docker compose logs`. Include: Python version, DB connection info (host/port/name, never password), Ollama URL, embedding model, dimensions, and environment mode. This aids debugging without requiring interactive access to the container.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| `pip install -r requirements.txt` | `uv sync --frozen` | 2024 | 10-100x faster builds, lockfile integrity |
| `depends_on` (no condition) | `depends_on` with `condition: service_healthy` | Docker Compose v2 | Reliable startup ordering based on actual readiness |
| `docker-compose` (hyphenated) | `docker compose` (space, plugin) | 2023 | V1 deprecated, V2 is standard |
| gRPC-FUSE for macOS mounts | VirtioFS (default since Docker Desktop 4.15) | 2023 | ~2x faster bind mounts on macOS |
| pgvector 0.7.x | pgvector 0.8.0+ (iterative index scans) | 2024 | Better filtered query results without manual tuning |

**Deprecated/outdated:**
- `docker-compose` (v1, hyphenated command): Use `docker compose` (v2, plugin) instead
- `-v` volume syntax in Compose: Long syntax (`type: bind`) is preferred for clarity
- `gRPC-FUSE` for macOS mounts: VirtioFS is now default and faster

## Open Questions

1. **`ollama.embed()` module-level function and `OLLAMA_HOST`**
   - What we know: The `ollama` Python library reads `OLLAMA_HOST` env var for the default client. Module-level functions like `ollama.embed()` use this default client.
   - What's unclear: Whether module-level functions reliably pick up `OLLAMA_HOST` set in the Docker environment section of compose. The source code suggests they should, but runtime verification is needed.
   - Recommendation: Test during implementation. If module-level functions do not respect the env var, switch to explicit `ollama.Client(host=os.getenv("OLLAMA_HOST"))` in the `OllamaEmbedder` constructor.

2. **`uv` Version Pinning**
   - What we know: The `COPY --from=ghcr.io/astral-sh/uv:0.9.28` pattern pins to a specific version. uv is releasing frequently.
   - What's unclear: The exact latest stable version at implementation time.
   - Recommendation: Check `ghcr.io/astral-sh/uv` tags at implementation time and pin to the latest `0.9.x` or `0.10.x` release. Use a specific version, never `latest`.

3. **Compose `env_file` `required: true` Minimum Version**
   - What we know: The `required` field for `env_file` was added in Docker Compose v2.24.0 (December 2023).
   - What's unclear: Whether the user's Docker Desktop version includes this.
   - Recommendation: Use `required: true` and document the minimum Docker Compose version requirement. Docker Desktop on macOS auto-updates, so this should not be an issue.

## Sources

### Primary (HIGH confidence)
- [Docker Compose startup-order docs](https://docs.docker.com/compose/how-tos/startup-order/) -- `depends_on`, `condition`, `restart`
- [uv Docker integration guide](https://docs.astral.sh/uv/guides/integration/docker/) -- multi-stage build, cache mounts, env vars
- [pydantic-settings docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) -- `settings_customise_sources`, env_prefix, TOML
- [psycopg3 conninfo API](https://www.psycopg.org/psycopg3/docs/api/conninfo.html) -- `make_conninfo()` function
- [pgvector GitHub](https://github.com/pgvector/pgvector) -- HNSW tuning, maintenance_work_mem, shm_size
- [Docker Compose env vars best practices](https://docs.docker.com/compose/how-tos/environment-variables/best-practices/) -- `env_file`, precedence, security
- [Ollama FAQ](https://docs.ollama.com/faq) -- `OLLAMA_HOST` configuration

### Secondary (MEDIUM confidence)
- [Docker Hub pgvector/pgvector](https://hub.docker.com/r/pgvector/pgvector) -- image tags, base image verification
- [Ollama Python DeepWiki](https://deepwiki.com/ollama/ollama-python/5.2-configuration-and-options) -- host resolution logic
- [Open WebUI troubleshooting](https://docs.openwebui.com/troubleshooting/connection-error/) -- `host.docker.internal` patterns
- [Docker macOS bind mount performance](https://www.paolomainardi.com/posts/docker-performance-macos-2025/) -- VirtioFS benchmarks

### Tertiary (LOW confidence)
- Various Medium/DEV.to articles on Docker + pgvector setup patterns (used for cross-verification only)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries are already in the project or well-documented official tools
- Architecture: HIGH -- Docker Compose + multi-stage builds is the established pattern; pgvector image behavior verified against official docs
- Pitfalls: HIGH -- identified from official docs, known issues, and macOS-specific Docker behavior research
- Discretion items: HIGH -- recommendations based on Docker best practices and project constraints

**Research date:** 2026-02-01
**Valid until:** 2026-04-01 (90 days -- Docker/pgvector ecosystem is stable)
