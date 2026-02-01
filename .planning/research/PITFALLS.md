# Domain Pitfalls: RAG Pipeline Docker Deployment, Retrieval API, and MCP Server

**Domain:** Deploying an existing Python RAG ingestion pipeline as Docker-based services with retrieval API and MCP server
**Researched:** 2026-02-01
**Focus:** Common mistakes when moving from "tested components" (310 tests, 4,906 lines) to "running service" with Docker, pgvector, Ollama-from-container, and MCP transport

---

## Critical Pitfalls

Mistakes that cause deployment failure, data corruption, or require architectural rework.

### 1. TOML Config File Missing in Docker Container Crashes Settings

**What goes wrong:** The existing `Settings` class (in `config.py`) hardcodes `toml_file="config.toml"` in `SettingsConfigDict`. When the container starts without a `config.toml` file at its working directory, `TomlConfigSettingsSource` raises a `FileNotFoundError` during `Settings()` construction. The entire application fails to start, even though every setting has a sensible default or could be provided via `BBJ_RAG_` environment variables.

**Why it happens:**
- The `settings_customise_sources` method correctly includes both `env_settings` and `TomlConfigSettingsSource`, but `TomlConfigSettingsSource` does not have a built-in "file optional" mode -- unlike `.env` files, missing TOML files raise hard errors
- In development, `config.toml` always exists in the project root where commands are run
- In Docker, the working directory is typically `/app` and only the Python package is installed -- no config files unless explicitly `COPY`'d
- The 12-factor app pattern says "use env vars in containers," but the current implementation requires the TOML file to exist even if all values come from env vars

**Consequences:**
- Container crashes on startup with a confusing `FileNotFoundError` traceback
- Developers waste time debugging why env vars "aren't working" when the real issue is a missing file
- If the workaround is to always COPY config.toml into the image, you bake dev-specific defaults (like `postgresql://localhost:5432/bbj_rag`) into the production image

**Prevention:**
- Modify `settings_customise_sources` to conditionally include `TomlConfigSettingsSource` only when the TOML file exists:
  ```python
  from pathlib import Path

  @classmethod
  def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
      sources = [init_settings, env_settings]
      if Path("config.toml").exists():
          sources.append(TomlConfigSettingsSource(settings_cls))
      return tuple(sources)
  ```
- Alternatively, make the TOML path configurable via an env var: `BBJ_RAG_CONFIG_FILE=/app/config.toml`
- Test the Settings class with no TOML file present as a unit test before Dockerizing

**Detection:** Application fails on first `Settings()` call in the container. Stack trace points to `TomlConfigSettingsSource.__init__`.

**Confidence:** HIGH -- verified against the actual `config.py` source code and pydantic-settings documentation. TomlConfigSettingsSource does not silently skip missing files.

**Phase:** Docker containerization (address during Dockerfile and config refactoring)

---

### 2. Ollama Unreachable from Docker Container on macOS

**What goes wrong:** The `OllamaEmbedder` uses `ollama_client.embed()` which defaults to `http://127.0.0.1:11434`. Inside a Docker container on macOS, `127.0.0.1` refers to the container itself, not the host where Ollama is running. Every embedding call fails with a connection refused error. The entire ingestion pipeline is dead.

**Why it happens:**
- Docker on macOS runs containers inside a Linux VM -- containers have their own network namespace
- The `ollama` Python library reads `OLLAMA_HOST` env var for its default, falling back to `http://127.0.0.1:11434`
- The current `OllamaEmbedder.__init__` accepts `model` and `dimensions` but has no `host` parameter -- it relies entirely on library defaults
- Ollama on macOS binds to `127.0.0.1:11434` by default, which is only accessible from the host, not from Docker containers
- Even `host.docker.internal` may fail if Ollama is not configured to accept connections from non-localhost origins

**Consequences:**
- Pipeline hangs or errors on the first `embed_batch()` call
- Error messages from httpx/ollama may be confusing (timeouts vs connection refused depend on timing)
- If not caught early, you discover this only after the parse + chunk phases complete for 7,087 files, wasting significant processing time

**Prevention:**
1. Set `OLLAMA_HOST=0.0.0.0:11434` on the macOS host so Ollama listens on all interfaces
2. Set `OLLAMA_ORIGINS="*"` on the host to allow cross-origin requests from Docker
3. Pass `OLLAMA_HOST=http://host.docker.internal:11434` as an env var to the Docker container
4. Add a health check that verifies Ollama connectivity before starting the pipeline:
   ```python
   import httpx
   resp = httpx.get(f"{ollama_host}")
   assert resp.text == "Ollama is running"
   ```
5. Consider adding an `ollama_host` field to `Settings` (with `BBJ_RAG_OLLAMA_HOST` env var override) rather than relying on the library's own env var mechanism

**Detection:** Connection refused or timeout on first `ollama_client.embed()` call. Verify with `curl http://host.docker.internal:11434` from inside the container.

**Confidence:** HIGH -- well-documented across Ollama GitHub issues, Open-WebUI discussions, and Docker documentation. The `0.0.0.0` binding requirement is confirmed in Ollama's official FAQ.

**Phase:** Docker containerization (must be validated in the very first container smoke test)

---

### 3. Docker `--shm-size` Too Small for Parallel HNSW Index Build

**What goes wrong:** pgvector's parallel HNSW index builder allocates shared memory under `/dev/shm` proportional to `maintenance_work_mem`. Docker's default `--shm-size` is 64MB. If `maintenance_work_mem` is set higher (to make the index build faster), the index creation fails with: `could not resize shared memory segment "/PostgreSQL.xxx" to N bytes: No space left on device`.

**Why it happens:**
- pgvector v0.6+ uses dynamic shared memory for parallel HNSW builds
- PostgreSQL creates files under `/dev/shm` for shared memory, and Docker limits this to 64MB by default
- The `schema.sql` creates HNSW with `m = 16, ef_construction = 64` on `vector(1024)` -- this is the default configuration but at 1024 dimensions, the per-vector storage is ~4KB
- For the expected corpus (~7,087 Flare files producing an estimated 20,000-40,000 chunks), the HNSW graph needs roughly 100-200MB of `maintenance_work_mem` for an efficient in-memory build
- Without raising `--shm-size`, parallel index builds fail at the PostgreSQL level with a cryptic "No space left on device" error on a filesystem most developers have never heard of

**Consequences:**
- Index creation fails partway through, leaving the database without a working HNSW index
- Error message ("No space left on device") is misleading -- it looks like a disk space issue when it is actually a shared memory issue
- Fallback to non-parallel build works but is dramatically slower
- If the error occurs during the initial data load, you may need to DROP and recreate the index

**Prevention:**
- In `docker-compose.yml`, set `shm_size: '256mb'` (or higher) for the PostgreSQL/pgvector container
- Or use `docker run --shm-size=256m` for manual runs
- Configure PostgreSQL with: `maintenance_work_mem = '128MB'` and `max_parallel_maintenance_workers = 4`
- Verify the relationship: `--shm-size` must be >= `maintenance_work_mem`
- Add a comment in the docker-compose.yml explaining why `shm_size` is set

**Detection:** PostgreSQL error log: `could not resize shared memory segment`. The `NOTICE: hnsw graph no longer fits into maintenance_work_mem` message is a warning but not a failure -- the "No space left" error is the failure.

**Confidence:** HIGH -- this is explicitly documented in the pgvector README and confirmed by multiple GitHub issues (#800, #409). The relationship between `--shm-size` and `maintenance_work_mem` is a well-established Docker + PostgreSQL pattern.

**Phase:** Docker containerization (PostgreSQL container configuration)

---

### 4. psycopg[binary] Wheels Fail on Alpine-Based Docker Images

**What goes wrong:** The project depends on `psycopg[binary]>=3.3,<4`. The `[binary]` extra installs `psycopg-binary`, which ships precompiled `manylinux` wheels built against glibc. Alpine Linux uses musl libc, not glibc. The wheels silently fail to install or produce runtime errors.

**Why it happens:**
- Alpine is a common choice for "small Docker images" and many Dockerfiles start with `python:3.12-alpine`
- `manylinux` wheels (the standard binary distribution format) assume glibc, which Alpine does not have
- pip may fall back to compiling from source, which requires `libpq-dev`, `gcc`, and `musl-dev` -- none present in the base Alpine image
- The error messages vary: sometimes "no matching distribution," sometimes compilation errors about missing headers

**Consequences:**
- Docker build fails during `pip install` / `uv sync`
- If you install build tools to fix it, the image bloats from ~50MB to ~300MB, defeating the purpose of Alpine
- Developers may switch to `psycopg[c]` (compile from source) which works on Alpine but requires maintaining C build toolchain in the image

**Prevention:**
- Use `python:3.12-slim` (Debian-based) as the base image, not Alpine
- `python:3.12-slim` supports manylinux wheels natively -- `psycopg[binary]`, `lxml`, and `pymupdf` all install without compilation
- The slim image is ~45MB larger than Alpine but avoids hours of troubleshooting C compilation issues
- This also resolves identical issues with `lxml` (requires `libxml2`, `libxslt`) and PyMuPDF (requires glibc-based MuPDF binaries)

**Detection:** Build failure with `ERROR: Could not find a version that satisfies the requirement psycopg-binary` or compilation errors mentioning `pg_config`, `libpq-fe.h`, or `Python.h`.

**Confidence:** HIGH -- this is one of the most documented Docker + Python pitfalls. Confirmed by Docker docs issue #904, psycopg issues, and PyMuPDF issue #4841.

**Phase:** Docker containerization (base image selection -- decide this first, before writing any Dockerfile)

---

### 5. Synchronous Database Connections Under Async API Cause Deadlocks

**What goes wrong:** The current `db.py` uses synchronous `psycopg.connect()` and `psycopg.Connection`. If the retrieval API is built with FastAPI (async by default), calling synchronous database operations from async endpoints blocks the event loop. Under concurrent load, the application deadlocks or becomes extremely slow.

**Why it happens:**
- FastAPI runs `async def` endpoints on the asyncio event loop
- Synchronous `psycopg.connect()` and `cursor.execute()` block the calling thread
- With async endpoints, this blocks the entire event loop -- no other requests can be processed
- The existing code works perfectly in the CLI pipeline (single-threaded, synchronous) but breaks under concurrent API load
- FastAPI does run `def` (non-async) endpoints in a thread pool, but mixing sync DB calls with async code paths creates subtle deadlock scenarios

**Consequences:**
- API appears to work under single-request testing but degrades catastrophically under concurrent load
- Response times spike from milliseconds to seconds
- Connection pool exhaustion when many requests queue up waiting for blocked sync operations
- Difficult to diagnose because the API "works" in development (low concurrency) but fails in any realistic usage

**Prevention:**
- For the retrieval API, create a separate async database layer using `psycopg.AsyncConnection` and `psycopg.AsyncConnectionPool`
- Keep the synchronous pipeline code as-is (it runs as a batch job, not under an event loop)
- Use dependency injection to provide the async connection pool to FastAPI endpoints
- Alternatively, use FastAPI's `def` endpoints (not `async def`) for database operations -- FastAPI runs these in a thread pool automatically. This is the simpler approach for an initial deployment
- Test under concurrent load early (even 10 concurrent requests reveals the problem)

**Detection:** API latency increases linearly with concurrent requests. `asyncio` warnings about slow callbacks. Connection pool timeout errors under load.

**Confidence:** HIGH -- this is the single most common FastAPI + database pitfall. Well-documented in FastAPI discussions (#9097, #1800) and psycopg3 pool documentation.

**Phase:** Retrieval API (address during API design, before writing endpoints)

---

## Moderate Pitfalls

Mistakes that cause significant delays, data quality issues, or technical debt.

### 6. Batch Embedding Timeouts Kill Long-Running Ingestion

**What goes wrong:** The `OllamaEmbedder.embed_batch()` sends an entire batch of texts to Ollama in a single HTTP request. For large batches (the default `embedding_batch_size=64`), this can take 30-60+ seconds on consumer hardware. The `ollama` Python library or its underlying `httpx` client may timeout before the response arrives, causing the entire batch to fail with no retry.

**Why it happens:**
- Ollama processes embeddings sequentially within a single request (it is not a high-throughput embedding server)
- The `embed()` function in the ollama Python library uses httpx with a default timeout
- 64 chunks x ~400 tokens each = ~25,600 tokens per batch -- on a CPU-only macOS host, this can take 30-60 seconds
- Network latency is added when going through `host.docker.internal` vs localhost
- There is no retry logic in the current `_embed_and_store()` function
- If one batch fails, the pipeline has no way to resume from the failed batch

**Consequences:**
- Ingestion fails partway through the 7,087-file corpus
- All work for the failed batch (parsing, chunking, intelligence) is lost
- No checkpoint mechanism means restarting processes everything from scratch (though `resume=True` skips already-stored chunks)
- Intermittent failures make it impossible to complete a full ingestion run

**Prevention:**
- Reduce `embedding_batch_size` to 8-16 for Ollama (lower latency per request, faster failure detection)
- Add retry logic with exponential backoff to `_embed_and_store()`:
  ```python
  for attempt in range(max_retries):
      try:
          vectors = embedder.embed_batch(texts)
          break
      except Exception:
          if attempt == max_retries - 1:
              raise
          time.sleep(2 ** attempt)
  ```
- Configure explicit timeouts on the Ollama client: `ollama.Client(host=..., timeout=120.0)`
- Add per-batch progress logging so you know where failures occur
- Consider processing one document at a time for the initial full ingestion (slower but more resilient)
- The existing `resume=True` flag is critical -- always enable it for large corpus runs

**Detection:** `httpx.ReadTimeout` or `ollama._types.ResponseError: EOF` during `embed_batch()`. Monitor batch completion rate during ingestion.

**Confidence:** HIGH -- confirmed by multiple RAG framework issues (LightRAG #2300, Roo-Code #5733, RAGFlow #4934). Ollama embedding timeouts are a widely reported problem with large batch sizes.

**Phase:** Ingestion service (address before first real data run)

---

### 7. Volume Mount Performance Degrades Ingestion with 7,087 Files on macOS

**What goes wrong:** Mounting the local Flare source directory (7,087 XML files) into the Docker container via bind mount on macOS incurs a ~3x performance penalty compared to native filesystem access. For a corpus this size, what would take 5 minutes natively could take 15+ minutes through a bind mount. File-heavy operations like directory listing, stat calls, and reading many small files are disproportionately affected.

**Why it happens:**
- Docker on macOS runs inside a Linux VM (Docker Desktop uses Apple Virtualization Framework or QEMU)
- Bind mounts go through VirtioFS, which translates macOS filesystem calls to the Linux guest -- each file operation crosses the VM boundary
- The Flare parser iterates 7,087 files, each requiring open/read/close syscalls through VirtioFS
- `lxml` parsing of XML files involves multiple read calls per file
- VirtioFS is ~3x slower than native in current Docker Desktop (down from 5-6x in earlier versions, but still meaningful for thousands of files)

**Consequences:**
- Parse phase takes 3x longer than expected
- Developer feedback loop is slow (20+ minutes for a full ingestion run)
- May cause confusion about whether the parser or the filesystem is the bottleneck
- Particularly bad for iterative development and debugging

**Prevention:**
- Accept the performance hit for development -- 15 minutes for 7,087 files is tolerable for a batch process
- Use Docker volumes (not bind mounts) for any data that does not need live editing from the host:
  ```yaml
  volumes:
    - flare-data:/app/data/flare  # Docker volume, faster
  ```
  Pre-populate the volume with `docker cp` or a one-time init container
- If using Docker Desktop, enable VirtioFS (Settings > General > "Use VirtioFS for file sharing") -- it may not be the default on older installations
- Consider OrbStack as an alternative Docker runtime on macOS -- it has additional VirtioFS tuning
- Profile the parse phase separately to establish a baseline before optimizing

**Detection:** Ingestion progress logs showing the parse phase taking disproportionately long compared to embedding/storage phases. Compare parse times with `--network=host` vs bind-mounted source.

**Confidence:** MEDIUM -- the 3x overhead figure is from January 2025 benchmarks by Paolo Mainardi. Actual impact depends on file sizes, access patterns, and Docker Desktop version. The Flare files are XML (small, many files), which is the worst case for VirtioFS.

**Phase:** Docker containerization (acceptable for initial deployment, optimize later if ingestion time is a problem)

---

### 8. MCP Server Transport Mismatch Blocks Client Integration

**What goes wrong:** The MCP Python SDK supports two official transports: stdio (for local/desktop tools) and Streamable HTTP (for remote/network access). Choosing the wrong transport means your MCP server is unreachable from the intended client. stdio servers cannot be accessed over the network. Streamable HTTP servers cannot be spawned as subprocesses by Claude Desktop.

**Why it happens:**
- The MCP specification supports only these two transports; SSE is deprecated as of protocol version 2025-03-26
- Claude Desktop and similar desktop tools expect stdio transport (they spawn the server as a child process)
- Docker-based deployments naturally favor Streamable HTTP (the server runs as a network service)
- The MCP Python SDK (latest: v1.26.0, Jan 2026) defaults to stdio when you call `run()` without arguments
- Many tutorials and examples show stdio because it is simpler -- developers may not realize it cannot be accessed remotely
- If you build a Docker image with a stdio MCP server, it is useless unless the client spawns containers (which most do not)

**Consequences:**
- MCP server built but unreachable from the intended client
- Requires architectural rework to switch transports (not just a config change -- the deployment model differs)
- stdio in Docker requires the client to manage container lifecycle (spawn, attach stdin/stdout, terminate)
- Streamable HTTP requires handling authentication, session management, CORS headers

**Prevention:**
- Decide the transport based on the deployment target BEFORE writing any MCP code:
  - **If the MCP server runs in Docker alongside the RAG services:** Use Streamable HTTP with `stateless_http=True`
  - **If Claude Desktop needs to access it locally:** Use stdio, run outside Docker
  - **If both:** Consider two entry points or use `mcpo` (MCP-to-OpenAPI proxy) to bridge stdio servers to HTTP
- For this project (Docker-based deployment), Streamable HTTP is the correct choice:
  ```python
  from mcp.server.fastmcp import FastMCP
  mcp = FastMCP("bbj-rag", stateless_http=True)
  mcp.run(transport="streamable-http", host="0.0.0.0", port=8080)
  ```
- Pin MCP SDK version: `mcp>=1.25,<2` (v2 is expected Q1 2026 with potential breaking changes)
- Be aware that the MCP SDK is evolving rapidly (25+ releases in 2025 alone) -- expect API surface changes

**Detection:** Client cannot connect to MCP server. stdio server shows no activity when HTTP requests arrive. Streamable HTTP server produces no output on stdio.

**Confidence:** HIGH -- transport model is well-documented in MCP specification and SDK docs. The stdio vs HTTP distinction is the most fundamental architectural decision.

**Phase:** MCP server implementation (decide transport in architecture phase, not during coding)

---

### 9. MCP SDK Rapid Version Churn Creates Upgrade Fragility

**What goes wrong:** The MCP Python SDK released 25+ versions in 2025 alone (from early 1.x through 1.26.0 in January 2026). A v2.0 release is planned for Q1 2026. Unpinned dependencies or pinning to a narrow range means builds break when new versions are released. The SDK's API surface has changed significantly between minor versions.

**Why it happens:**
- MCP is a new protocol (2024-2025) still finding its API shape
- The Python SDK tracks the evolving specification closely
- SSE transport was deprecated and replaced by Streamable HTTP in a minor version
- Session management semantics changed between versions
- The v2.0 release may have breaking changes (the maintainers explicitly recommend pinning to `mcp>=1.25,<2`)

**Consequences:**
- Builds fail when a new MCP SDK version changes or removes an API you depend on
- Debugging "it worked yesterday" failures caused by dependency drift
- Difficulty finding documentation that matches your installed version
- Potential incompatibility between MCP server SDK version and client expectations

**Prevention:**
- Pin aggressively in `pyproject.toml`: `mcp>=1.25,<2`
- Lock versions via `uv.lock` (the project already uses uv)
- Write integration tests that verify MCP tool registration and invocation
- Monitor the MCP SDK changelog before upgrading
- Plan for a v2 migration as a separate task (not mid-feature)

**Detection:** Build failures after `uv sync` when new SDK versions are published. Runtime errors in MCP tool handlers that previously worked.

**Confidence:** HIGH -- version history is publicly visible on PyPI. The v2 plan is documented in the official SDK blog post (December 2025).

**Phase:** MCP server implementation (pin version on day one)

---

### 10. Database URL Contains `localhost` Which Resolves Differently in Container

**What goes wrong:** The default `database_url` in both `config.toml` and the `Settings` class is `postgresql://localhost:5432/bbj_rag`. Inside a Docker container, `localhost` resolves to the container itself, not the host machine where PostgreSQL may be running. If PostgreSQL is in a separate container (via docker-compose), the hostname should be the service name (e.g., `postgres` or `db`).

**Why it happens:**
- `localhost` is the correct default for local development (PostgreSQL on the host)
- Docker containers have isolated network namespaces
- In docker-compose, services communicate via service names on a shared bridge network
- The config.toml value takes precedence over the field default (per `settings_customise_sources` priority)
- Even if `BBJ_RAG_DATABASE_URL` is set as an env var, forgetting to remove `database_url` from a COPY'd config.toml means the TOML value wins (env vars have higher priority in the current implementation, but this is a common source of confusion)

**Consequences:**
- Container starts but cannot connect to database
- Error message: `could not connect to server: Connection refused` pointing at `127.0.0.1:5432`
- Developers may spend time debugging PostgreSQL when the issue is purely hostname resolution

**Prevention:**
- In docker-compose.yml, always set `BBJ_RAG_DATABASE_URL` explicitly:
  ```yaml
  environment:
    BBJ_RAG_DATABASE_URL: "postgresql://user:pass@db:5432/bbj_rag"
  ```
- Do NOT copy `config.toml` into the Docker image (see Pitfall #1 -- make TOML optional)
- Use the docker-compose service name (`db`) as the hostname, not `localhost` or `host.docker.internal`
- Add a startup health check that verifies database connectivity before proceeding

**Detection:** `psycopg.OperationalError: connection to server at "127.0.0.1", port 5432 failed: Connection refused`.

**Confidence:** HIGH -- this is the most common Docker networking mistake. Specific to this project because `config.toml` has `localhost` baked in and the Settings class loads it by default.

**Phase:** Docker containerization (docker-compose configuration)

---

### 11. PyMuPDF ARM64 Wheel Missing Breaks M1/M2 Mac Docker Builds

**What goes wrong:** When building Docker images on Apple Silicon Macs (M1/M2/M3), Docker defaults to `linux/arm64` platform. PyMuPDF intermittently lacks pre-built `linux/arm64` wheels on PyPI for certain versions. The build either fails outright or falls back to compiling MuPDF from source (which takes 10+ minutes and requires many system dependencies).

**Why it happens:**
- PyMuPDF wheel availability for `linux/arm64` is inconsistent across versions (documented in GitHub issues #3622, #4344)
- Docker Desktop on Apple Silicon defaults to `linux/arm64` to match the host architecture
- Building for `linux/amd64` on ARM requires QEMU emulation, which is 5-10x slower
- The `pymupdf4llm>=0.2.9` constraint in `pyproject.toml` allows any recent version, but not all versions have ARM64 wheels
- This is a recurring issue -- it gets fixed in one release and may regress in the next

**Consequences:**
- Docker build fails with "no matching distribution" or takes 15+ minutes compiling MuPDF from source
- Developers on Intel Macs do not see the issue, creating "works on my machine" scenarios
- CI/CD pipelines may use different architectures than developer machines

**Prevention:**
- Target `linux/amd64` explicitly in Docker builds: `docker build --platform linux/amd64 .`
- Or in docker-compose.yml: `platform: linux/amd64`
- This adds a small runtime overhead via Rosetta/QEMU on Apple Silicon but guarantees wheel availability
- Pin PyMuPDF to a version known to have ARM64 wheels if targeting native ARM64
- Test the Docker build on both architectures in CI
- If PDF parsing is not needed in the Docker deployment (i.e., PDFs are parsed locally and only chunks are stored), consider making `pymupdf4llm` an optional dependency

**Detection:** Docker build failure at `pip install pymupdf` step. Error varies: "no matching distribution" or compilation errors about missing MuPDF headers.

**Confidence:** MEDIUM -- the issue is well-documented but version-specific. The latest pymupdf4llm (0.2.9, Jan 2026) may have ARM64 wheels, but this needs verification at build time.

**Phase:** Docker containerization (decide target platform early)

---

### 12. Pydantic Settings v2.12 Nested Override Regression

**What goes wrong:** Pydantic-settings v2.12 introduced a regression where environment variables cannot override values that are set in nested objects within a TOML source. If the project later adds nested configuration (e.g., `[database]` and `[embedding]` sections in TOML), the `BBJ_RAG_DATABASE_URL` env var may silently fail to override the TOML value.

**Why it happens:**
- The project currently uses flat settings (no nested models), so this is not an immediate issue
- The `pyproject.toml` dependency is `pydantic-settings>=2.12,<3` -- the floor is exactly the affected version
- If nested configuration is added later (a natural evolution for complex settings), the regression bites
- The regression is tracked in pydantic-settings GitHub issue #714

**Consequences:**
- Environment variables silently fail to override nested TOML values
- Docker deployments using env vars get unexpected config values from the baked-in TOML file
- Debugging is extremely difficult because the env var appears to be set correctly

**Prevention:**
- Keep settings flat (as they currently are) for as long as practical
- If nesting is needed, test env var overrides explicitly for every nested field
- Monitor pydantic-settings releases for a fix to issue #714
- Consider pinning to a specific patch version if the regression is confirmed in your version

**Detection:** Settings values do not match environment variables despite correct `BBJ_RAG_` prefix. Only visible when nested TOML sections are used.

**Confidence:** MEDIUM -- the regression is reported in GitHub issue #714 but the exact affected versions and fix status need verification. Current flat settings are not affected.

**Phase:** Configuration management (awareness for future changes)

---

## Minor Pitfalls

Mistakes that cause annoyance, wasted time, or minor technical debt but are straightforward to fix.

### 13. uv.lock Not Committed or Mismatched Between Dev and Docker

**What goes wrong:** The Docker build uses `uv sync --frozen` which requires `uv.lock` to be present and up-to-date. If `uv.lock` is in `.gitignore` or was generated with a different platform's Python, the Docker build fails or installs different versions than development.

**Prevention:**
- Always commit `uv.lock` to version control (it is 155KB in this project -- worth it)
- Run `uv lock` on the same Python version used in Docker (3.12)
- Use `COPY uv.lock pyproject.toml ./` before `RUN uv sync --frozen --no-dev` in the Dockerfile
- The `--frozen` flag ensures reproducible builds by refusing to update the lockfile

**Detection:** Docker build fails with "lockfile is not up to date" or "resolution failed."

**Confidence:** HIGH -- standard uv Docker pattern documented in official uv docs.

**Phase:** Docker containerization (Dockerfile setup)

---

### 14. lxml Requires System Libraries at Runtime, Not Just Build Time

**What goes wrong:** In a multi-stage Docker build, developers install `libxml2-dev` and `libxslt1-dev` in the build stage, compile lxml, then copy only the Python packages to the runtime stage. But lxml dynamically links to `libxml2.so` and `libxslt.so` -- without the runtime libraries in the final stage, lxml crashes with `ImportError: libxml2.so.2: cannot open shared object file`.

**Prevention:**
- In the runtime stage, install runtime libraries (not -dev packages):
  ```dockerfile
  RUN apt-get update && apt-get install -y --no-install-recommends \
      libxml2 libxslt1.1 \
      && rm -rf /var/lib/apt/lists/*
  ```
- Or use `python:3.12-slim` which includes these runtime libraries (lxml binary wheels on PyPI are linked against standard Debian library versions)
- With `python:3.12-slim` and `psycopg[binary]`, most dependencies install from wheels and require no compilation at all -- the multi-stage build may be unnecessary

**Detection:** `ImportError` at runtime when importing lxml. Only appears in the final Docker image, not during build.

**Confidence:** HIGH -- standard shared library linking issue in multi-stage Docker builds.

**Phase:** Docker containerization (Dockerfile, if using multi-stage)

---

### 15. HNSW Index Created Before Data Load Is Inefficient

**What goes wrong:** If `CREATE INDEX ... USING hnsw` runs before data is loaded (as part of schema initialization), the index is built on an empty table and then incrementally maintained as rows are inserted. Incremental HNSW inserts are significantly slower than building the index after all data is loaded.

**Why it happens:**
- The `schema.sql` file includes `CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw` alongside the table creation
- Running `schema.sql` before ingestion creates the empty index
- Each subsequent `INSERT` must update the HNSW graph incrementally
- For 20,000-40,000 chunks, incremental inserts are measurably slower than a bulk load + single index build

**Prevention:**
- Split schema initialization: create the table and non-HNSW indexes first, load data, then create the HNSW index
- Or DROP the HNSW index before bulk loading and recreate it after:
  ```sql
  DROP INDEX IF EXISTS idx_chunks_embedding_hnsw;
  -- ... bulk load ...
  CREATE INDEX idx_chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
  ```
- Set `maintenance_work_mem = '128MB'` and `max_parallel_maintenance_workers = 4` before the index build
- For the expected corpus size (~20K-40K chunks at 1024 dimensions), the in-memory graph needs ~100-200MB -- well within a reasonable `maintenance_work_mem` setting

**Detection:** Ingestion takes hours instead of minutes. PostgreSQL shows continuous index maintenance activity during bulk insert.

**Confidence:** HIGH -- documented pgvector best practice: "It's faster to create an index after loading your initial data."

**Phase:** Ingestion service (schema initialization and data loading workflow)

---

### 16. Stray stdout in MCP stdio Server Corrupts Protocol Stream

**What goes wrong:** If the MCP server uses stdio transport and any code path writes to stdout (print statements, logging configured to stdout, library debug output), the stdout data mixes with the MCP protocol messages. The client receives malformed JSON and the session breaks.

**Why it happens:**
- MCP stdio transport uses stdin/stdout as the bidirectional communication channel
- Python's default `logging.StreamHandler` writes to stderr (safe), but `print()` goes to stdout
- Third-party libraries may write to stdout unexpectedly
- This is invisible during development if you test with HTTP transport or direct function calls

**Prevention:**
- Redirect all logging to stderr explicitly:
  ```python
  logging.basicConfig(stream=sys.stderr)
  ```
- Never use `print()` in MCP server code paths
- If using stdio transport, test by reading raw stdout output and validating it is valid MCP protocol JSON
- Consider using Streamable HTTP transport for Docker deployment (makes stdout a non-issue)

**Detection:** MCP client reports "malformed message" or "unexpected data" errors. Messages appear to be valid JSON but contain extra text.

**Confidence:** HIGH -- documented in MCP specification and SDK docs. One of the most frequently reported MCP integration issues.

**Phase:** MCP server implementation (relevant only if stdio transport is chosen)

---

### 17. No Connection Pooling in Retrieval API Creates Per-Request Overhead

**What goes wrong:** The current `db.py` uses `psycopg.connect()` which creates a new connection for each call. For a retrieval API handling multiple requests, this means connection setup (~5-50ms) on every request, plus risk of hitting PostgreSQL's `max_connections` limit.

**Prevention:**
- Use `psycopg_pool.ConnectionPool` (sync) or `psycopg_pool.AsyncConnectionPool` (async) for the retrieval API
- Configure pool with: `min_size=2, max_size=10` (appropriate for a local development service)
- Use FastAPI lifespan to manage pool lifecycle:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      pool = AsyncConnectionPool(conninfo=database_url, open=False)
      await pool.open()
      app.state.pool = pool
      yield
      await pool.close()
  ```
- Keep the existing `get_connection()` for the CLI pipeline (batch jobs do not need pooling)

**Detection:** Slow first request (connection setup) and PostgreSQL showing many short-lived connections in `pg_stat_activity`.

**Confidence:** HIGH -- standard production pattern for any database-backed API.

**Phase:** Retrieval API (implement during API scaffold)

---

### 18. Docker Build Cache Invalidated by Copying Source Before Dependencies

**What goes wrong:** A naive Dockerfile copies the entire project before installing dependencies. Any source code change invalidates the dependency install layer, causing a full `uv sync` on every build (30+ seconds with many dependencies).

**Prevention:**
- Separate dependency installation from application code:
  ```dockerfile
  FROM python:3.12-slim
  COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

  WORKDIR /app
  ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

  # Dependencies first (cached)
  COPY uv.lock pyproject.toml ./
  RUN uv sync --frozen --no-install-project --no-dev

  # Then application code
  COPY src/ src/
  RUN uv sync --frozen --no-dev
  ```
- Use `--mount=type=cache,target=/root/.cache/uv` for even faster rebuilds
- This pattern ensures dependency installation is cached until `uv.lock` or `pyproject.toml` changes

**Detection:** Every code change triggers a full dependency installation (visible in build output).

**Confidence:** HIGH -- documented in official uv Docker guide.

**Phase:** Docker containerization (Dockerfile optimization)

---

## Phase-Specific Warning Matrix

| Phase | Likely Pitfall | Severity | Mitigation |
|-------|---------------|----------|------------|
| Docker containerization | #4: Alpine vs slim base image | Critical | Use `python:3.12-slim`, decide before writing any Dockerfile |
| Docker containerization | #1: TOML config missing in container | Critical | Make TOML source conditional on file existence |
| Docker containerization | #2: Ollama unreachable from container | Critical | Use `host.docker.internal`, set `OLLAMA_HOST=0.0.0.0` on host |
| Docker containerization | #10: localhost in database URL | Critical | Override via env var, do not COPY config.toml |
| Docker containerization | #3: shm-size for HNSW builds | Critical | Set `shm_size: '256mb'` in docker-compose |
| Docker containerization | #11: PyMuPDF ARM64 wheels | Moderate | Target `linux/amd64` or pin version with known ARM64 wheel |
| Docker containerization | #18: Build cache invalidation | Minor | Separate deps from source in Dockerfile |
| Docker containerization | #13: uv.lock management | Minor | Commit uv.lock, use `--frozen` |
| Docker containerization | #14: lxml runtime libraries | Minor | Install `libxml2 libxslt1.1` in runtime stage |
| Ingestion service | #6: Embedding timeouts | Moderate | Reduce batch size, add retry logic |
| Ingestion service | #7: Volume mount performance | Moderate | Accept or use Docker volumes |
| Ingestion service | #15: HNSW before data load | Minor | Create HNSW index after bulk load |
| Retrieval API | #5: Sync DB under async API | Critical | Use async connections or sync endpoints |
| Retrieval API | #17: No connection pooling | Minor | Use `psycopg_pool` |
| MCP server | #8: Transport mismatch | Moderate | Decide transport (Streamable HTTP) before coding |
| MCP server | #9: SDK version churn | Moderate | Pin `mcp>=1.25,<2` |
| MCP server | #16: stdout corruption | Minor | Use stderr for logging, or choose HTTP transport |
| Configuration | #12: Nested override regression | Minor | Keep settings flat, monitor pydantic-settings issues |

---

## Pitfalls NOT Applicable to This Corpus Size

Some commonly cited pgvector pitfalls apply only at much larger scale:

| Pitfall | Typical Threshold | This Project | Verdict |
|---------|------------------|--------------|---------|
| HNSW build takes hours | >1M vectors | ~20K-40K chunks | Not a concern. Build should take < 1 minute |
| maintenance_work_mem exhausts RAM | >100K vectors at 1024d | ~40K at 1024d | Set 128MB, well within any dev machine |
| Need for halfvec/quantization | >1M vectors | ~40K | Not needed at this scale |
| PgBouncer as L2 pool | >1000 concurrent connections | Single-digit connections | Not needed |
| Table partitioning | >10M rows | ~40K rows | Not needed |

---

## Sources

### Docker + Python Packaging
- [psycopg binary wheels vs Alpine](https://github.com/docker-library/docs/issues/904)
- [PyMuPDF Docker build issues](https://github.com/pymupdf/PyMuPDF/issues/4841)
- [PyMuPDF ARM64 missing wheels](https://github.com/pymupdf/PyMuPDF/issues/4344)
- [lxml installation guide](https://lxml.de/installation.html)
- [uv Docker guide](https://docs.astral.sh/uv/guides/integration/docker/)
- [Production Python Docker with uv (Hynek)](https://hynek.me/articles/docker-uv/)
- [Optimal Dockerfile for Python with uv (Depot)](https://depot.dev/docs/container-builds/how-to-guides/optimal-dockerfiles/python-uv-dockerfile)

### pgvector + HNSW
- [pgvector README - HNSW](https://github.com/pgvector/pgvector)
- [HNSW indexes with pgvector (Crunchy Data)](https://www.crunchydata.com/blog/hnsw-indexes-with-postgres-and-pgvector)
- [HNSW memory estimation issue #745](https://github.com/pgvector/pgvector/issues/745)
- [shm-size and parallel builds issue #800 (Neon)](https://github.com/neondatabase/autoscaling/issues/800)
- [Parallel HNSW builds issue #409](https://github.com/pgvector/pgvector/issues/409)

### Ollama + Docker
- [Ollama FAQ - Docker setup](https://docs.ollama.com/faq)
- [host.docker.internal fix](https://openillumi.com/en/en-docker-ollama-localhost-connect-host-docker-internal/)
- [Ollama Python OLLAMA_HOST issue #407](https://github.com/ollama/ollama-python/issues/407)

### Embedding Timeouts
- [LightRAG embedding 500/EOF issue #2300](https://github.com/HKUDS/LightRAG/issues/2300)
- [Roo-Code timeout issue #5733](https://github.com/RooCodeInc/Roo-Code/issues/5733)

### Pydantic Settings
- [Settings management docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Nested override regression issue #714](https://github.com/pydantic/pydantic-settings/issues/714)
- [Runtime TOML path override issue #259](https://github.com/pydantic/pydantic-settings/issues/259)

### FastAPI + Database
- [FastAPI connection pool discussion #9097](https://github.com/fastapi/fastapi/discussions/9097)
- [psycopg3 connection pools docs](https://www.psycopg.org/psycopg3/docs/advanced/pool.html)
- [psycopg3 async docs](https://www.psycopg.org/psycopg3/docs/advanced/async.html)

### MCP Protocol + SDK
- [MCP Python SDK (GitHub)](https://github.com/modelcontextprotocol/python-sdk)
- [MCP transport future (blog)](http://blog.modelcontextprotocol.io/posts/2025-12-19-mcp-transport-future/)
- [MCP tips, tricks, and pitfalls (NearForm)](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/)
- [MCP Python SDK on PyPI](https://pypi.org/project/mcp/)

### Docker macOS Performance
- [Docker on macOS still slow? (2025 benchmarks)](https://www.paolomainardi.com/posts/docker-performance-macos-2025/)
- [OrbStack volumes docs](https://docs.orbstack.dev/docker/file-sharing)
