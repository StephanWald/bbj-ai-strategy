# Phase 9: Schema & Data Models - Research

**Researched:** 2026-01-31
**Domain:** PostgreSQL pgvector schema, Pydantic data models, configuration management, content deduplication
**Confidence:** HIGH

## Summary

This phase establishes the stable interfaces that every downstream component (parsers, taggers, embedders) depends on. The work spans four distinct areas: (1) PostgreSQL DDL with pgvector for vector storage and tsvector for full-text search, (2) Pydantic v2 data models as the common contract between parsers and the database layer, (3) a configuration system using pydantic-settings to externalize all runtime parameters, and (4) content-hash deduplication to make re-ingestion idempotent.

The standard stack is well-established: psycopg 3.x for database access, pgvector 0.4.x for Python-side vector type registration, Pydantic 2.12.x for validation, and pydantic-settings 2.12.x for configuration from TOML files with environment variable overrides. All libraries are mature, actively maintained, and have official documentation covering the exact patterns needed.

**Primary recommendation:** Define the schema DDL as a standalone SQL file (not ORM migrations), use Pydantic BaseModel with strict validation for Document/Chunk contracts, load config from TOML via pydantic-settings, and enforce idempotency with a UNIQUE constraint on content_hash combined with `INSERT ... ON CONFLICT DO NOTHING`.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `psycopg[binary]` | 3.3.2 | PostgreSQL adapter (connection, queries, COPY) | Official psycopg3; binary protocol, native async, COPY support |
| `pgvector` (Python) | 0.4.2 | Register vector type with psycopg3 | Official pgvector Python bindings; handles serialization/deserialization |
| `pydantic` | 2.12.5 | Data model validation and serialization | Industry standard for Python data contracts; Rust-core validation |
| `pydantic-settings` | 2.12.0 | Configuration from TOML + env vars | First-party Pydantic companion; built-in TOML support via tomllib |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `psycopg_pool` | (bundled with `psycopg[pool]`) | Connection pooling | When running the pipeline as a long-lived process |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw psycopg3 DDL | SQLAlchemy + alembic migrations | More abstraction but overkill for a single-table schema; this project does not need an ORM |
| pydantic-settings TOML | python-dotenv + manual parsing | pydantic-settings gives typed validation for free; TOML support is built-in with Python 3.11+ tomllib |
| SHA-256 content hash | MD5 or xxhash | SHA-256 is standard, collision-resistant, in stdlib; speed is not a bottleneck for document-level hashing |

**Installation (add to pyproject.toml dependencies):**
```toml
dependencies = [
    "psycopg[binary]>=3.3,<4",
    "pgvector>=0.4,<0.5",
    "pydantic>=2.12,<3",
    "pydantic-settings>=2.12,<3",
]
```

## Architecture Patterns

### Recommended Project Structure
```
src/bbj_rag/
├── __init__.py
├── models.py          # Pydantic Document and Chunk models
├── schema.py          # Python helper to apply DDL, verify schema
├── config.py          # pydantic-settings Settings class
├── db.py              # Connection management, insert/query helpers
└── hashing.py         # Content hash computation
sql/
└── schema.sql         # Standalone DDL file (CREATE EXTENSION, tables, indexes)
config.toml            # Default configuration file
```

### Pattern 1: Schema DDL as Standalone SQL File
**What:** Keep the DDL in a plain `.sql` file, not embedded in Python strings. A Python helper reads and executes it.
**When to use:** Always for this project. The schema is the contract; it should be readable without Python.
**Example:**
```sql
-- sql/schema.sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id              BIGSERIAL PRIMARY KEY,
    source_url      TEXT NOT NULL,
    title           TEXT NOT NULL,
    doc_type        TEXT NOT NULL,
    content         TEXT NOT NULL,
    content_hash    VARCHAR(64) NOT NULL UNIQUE,
    generations     TEXT[] NOT NULL DEFAULT '{}',
    embedding       vector(1536),
    search_vector   tsvector GENERATED ALWAYS AS (
                        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))
                    ) STORED,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- HNSW index for cosine similarity vector search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- GIN index on tsvector generated column for full-text search
CREATE INDEX IF NOT EXISTS idx_chunks_search_vector_gin
    ON chunks USING GIN (search_vector);

-- GIN index on generations array for filtering by BBj generation
CREATE INDEX IF NOT EXISTS idx_chunks_generations_gin
    ON chunks USING GIN (generations);

-- Unique index on content_hash (already created by UNIQUE constraint, but named explicitly)
-- The UNIQUE constraint on content_hash column handles this automatically.
```

### Pattern 2: Pydantic Models as Parser Contracts
**What:** All parsers produce `Document` objects; the pipeline splits documents into `Chunk` objects. Validation happens at the boundary.
**When to use:** Every parser (Flare, web crawl, future parsers) returns `Document` instances.
**Example:**
```python
# src/bbj_rag/models.py
from pydantic import BaseModel, ConfigDict, Field, field_validator
import hashlib

class Document(BaseModel):
    """Parsed document produced by any parser."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_url: str
    title: str
    doc_type: str          # e.g., "flare", "web", "api"
    content: str
    generations: list[str] # e.g., ["BBj 24", "BBj 25"]
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be empty")
        return v

    @field_validator("generations")
    @classmethod
    def generations_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("generations must contain at least one entry")
        return v


class Chunk(BaseModel):
    """Individual chunk ready for embedding and storage."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_url: str
    title: str
    doc_type: str
    content: str
    content_hash: str
    generations: list[str]
    metadata: dict[str, str] = Field(default_factory=dict)
    embedding: list[float] | None = None

    @classmethod
    def from_content(
        cls,
        source_url: str,
        title: str,
        doc_type: str,
        content: str,
        generations: list[str],
        metadata: dict[str, str] | None = None,
    ) -> "Chunk":
        """Create a Chunk with auto-computed content hash."""
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return cls(
            source_url=source_url,
            title=title,
            doc_type=doc_type,
            content=content,
            content_hash=content_hash,
            generations=generations,
            metadata=metadata or {},
        )
```

### Pattern 3: Configuration via pydantic-settings with TOML
**What:** A single Settings class loads from TOML file, overridable by environment variables.
**When to use:** All runtime configuration (DB connection, embedding model, chunk sizes).
**Example:**
```python
# src/bbj_rag/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource
from pydantic_settings import PydanticBaseSettingsSource

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        toml_file="config.toml",
        env_prefix="BBJ_RAG_",
    )

    # Database
    database_url: str = Field(description="PostgreSQL connection string")

    # Embedding
    embedding_model: str = Field(default="text-embedding-3-small")
    embedding_dimensions: int = Field(default=1536)

    # Chunking
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=64)

    # Source paths
    flare_source_path: str = Field(default="")
    crawl_source_urls: list[str] = Field(default_factory=list)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls),
        )
```

```toml
# config.toml
database_url = "postgresql://localhost:5432/bbj_rag"
embedding_model = "text-embedding-3-small"
embedding_dimensions = 1536
chunk_size = 512
chunk_overlap = 64
flare_source_path = "/Users/beff/bbjdocs/"
crawl_source_urls = []
```

### Pattern 4: Idempotent Upsert via Content Hash
**What:** Compute SHA-256 of chunk content, use UNIQUE constraint + ON CONFLICT DO NOTHING.
**When to use:** Every insert operation into the chunks table.
**Example:**
```python
# src/bbj_rag/db.py
import hashlib
import psycopg
from pgvector.psycopg import register_vector

def insert_chunk(conn: psycopg.Connection, chunk) -> bool:
    """Insert a chunk idempotently. Returns True if inserted, False if duplicate."""
    result = conn.execute(
        """
        INSERT INTO chunks (source_url, title, doc_type, content, content_hash,
                           generations, embedding, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (content_hash) DO NOTHING
        RETURNING id
        """,
        (
            chunk.source_url,
            chunk.title,
            chunk.doc_type,
            chunk.content,
            chunk.content_hash,
            chunk.generations,
            chunk.embedding,
            chunk.metadata,  # will need Json() adapter for JSONB
        ),
    )
    return result.fetchone() is not None

def insert_chunks_batch(conn: psycopg.Connection, chunks) -> int:
    """Insert multiple chunks using executemany. Returns count of inserted."""
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO chunks (source_url, title, doc_type, content, content_hash,
                               generations, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (content_hash) DO NOTHING
            """,
            [
                (c.source_url, c.title, c.doc_type, c.content, c.content_hash,
                 c.generations, c.embedding, c.metadata)
                for c in chunks
            ],
        )
        return cur.rowcount
```

### Anti-Patterns to Avoid
- **Embedding the DDL in Python string literals:** Loses SQL syntax highlighting, makes DBA review impossible. Keep DDL in `.sql` files.
- **Using ORM for a single table:** SQLAlchemy + Alembic add massive complexity for a schema this simple. Raw SQL DDL is the right choice.
- **Hashing after insertion:** The content hash must be computed before insert so it can serve as the conflict target. Never rely on database-side hashing.
- **Using `concat()` or `concat_ws()` in generated columns:** These are STABLE, not IMMUTABLE. Use the `||` operator instead.
- **Calling `to_tsvector()` with one argument:** The single-argument form uses `default_text_search_config` and is STABLE. Always pass the regconfig explicitly: `to_tsvector('english', ...)`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Vector type serialization | Custom binary encoding for vectors | `pgvector` Python package + `register_vector()` | Handles psycopg3 type adaptation automatically |
| Configuration parsing | Custom TOML loader + env var merger | `pydantic-settings` `TomlConfigSettingsSource` | Built-in priority chain, typed validation, env override |
| Connection pooling | Custom connection cache | `psycopg_pool.ConnectionPool` | Handles reconnection, health checks, max connections |
| Content hashing | Custom hash function | `hashlib.sha256` from stdlib | Cryptographic, collision-resistant, zero dependencies |
| Full-text search column | Trigger-based tsvector update | PostgreSQL GENERATED ALWAYS AS stored column | Auto-maintained by database engine, no application code |
| Schema migration | Python-based table creation | Standalone SQL DDL file executed via `psycopg` | Readable by DBAs, testable independently, version-controlled |

**Key insight:** The PostgreSQL engine already provides generated columns and expression indexes for tsvector maintenance, GIN indexes for array containment queries, and UNIQUE constraints for deduplication. Leverage the database; do not reimplement these in application code.

## Common Pitfalls

### Pitfall 1: to_tsvector Immutability in Generated Columns
**What goes wrong:** Using `to_tsvector(content)` (one argument) in a GENERATED ALWAYS AS expression fails with `ERROR: generation expression is not immutable`.
**Why it happens:** The single-argument `to_tsvector()` depends on the `default_text_search_config` GUC, making it STABLE, not IMMUTABLE. PostgreSQL requires IMMUTABLE functions in generated column expressions.
**How to avoid:** Always use the two-argument form: `to_tsvector('english', ...)`. Use `||` for string concatenation (not `concat` or `concat_ws`, which are also STABLE). Wrap values with `coalesce(col, '')` to handle NULLs since `NULL || 'text'` returns NULL.
**Warning signs:** `ERROR 42P17: generation expression is not immutable`

### Pitfall 2: Vector Dimension Mismatch
**What goes wrong:** Inserting a vector with wrong dimensions (e.g., 768-dim into a `vector(1536)` column) causes a runtime error.
**Why it happens:** pgvector enforces dimension at insert time, not schema creation time. Changing embedding models mid-project silently breaks.
**How to avoid:** Store the embedding dimension in config (`embedding_dimensions`). Validate vector length in the Pydantic Chunk model before insert. Use a named constant or config value when defining the schema column size.
**Warning signs:** `ERROR: expected 1536 dimensions, not 768`

### Pitfall 3: Forgetting to Register pgvector Types
**What goes wrong:** Inserting or querying vectors raises serialization errors like `can't adapt type 'list'` or `column "embedding" is of type vector but expression is of type text`.
**Why it happens:** psycopg3 does not natively know about the `vector` type. The `pgvector` Python package must register custom type adapters.
**How to avoid:** Call `register_vector(conn)` immediately after opening every connection. For connection pools, pass it as the `configure` callback.
**Warning signs:** Type adaptation errors on insert or query

### Pitfall 4: content_hash Computed on Wrong Data
**What goes wrong:** Re-ingesting the same document produces different hashes, defeating deduplication.
**Why it happens:** Hashing includes whitespace variations, metadata, or other non-content fields that change between runs.
**How to avoid:** Hash only the normalized content string. Strip whitespace before hashing. Document exactly what goes into the hash. Consider including source_url in the hash if the same content from different sources should be stored separately.
**Warning signs:** Duplicate rows appearing after re-ingestion

### Pitfall 5: HNSW Index on Empty Table Performance
**What goes wrong:** Creating an HNSW index on an empty table works (unlike IVFFlat) but the index is trivially small. After bulk loading, the index must be rebuilt for optimal recall.
**Why it happens:** HNSW builds the graph incrementally. Bulk-loading after index creation results in suboptimal graph structure compared to building the index after data is loaded.
**How to avoid:** For initial bulk loads, either (a) create the HNSW index after loading data, or (b) accept slightly suboptimal recall until a `REINDEX` is done. The DDL uses `CREATE INDEX IF NOT EXISTS` so it is safe to run at any time.
**Warning signs:** Lower-than-expected recall on vector similarity queries

### Pitfall 6: psycopg3 JSONB Handling
**What goes wrong:** Passing a Python dict to a JSONB column fails or stores as string instead of JSON.
**Why it happens:** psycopg3 needs the `Json` adapter to properly serialize Python dicts to PostgreSQL JSONB.
**How to avoid:** Use `psycopg.types.json.Json(metadata_dict)` when passing dicts to JSONB columns, or register the JSON adapter globally.
**Warning signs:** Metadata stored as stringified dict instead of queryable JSONB

## Code Examples

### Complete DDL with All Required Components
```sql
-- Source: PostgreSQL 18 docs, pgvector 0.8.x README
-- Verified against success criteria requirements

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id              BIGSERIAL PRIMARY KEY,
    source_url      TEXT NOT NULL,
    title           TEXT NOT NULL,
    doc_type        TEXT NOT NULL,
    content         TEXT NOT NULL,
    content_hash    VARCHAR(64) NOT NULL UNIQUE,
    generations     TEXT[] NOT NULL DEFAULT '{}',
    embedding       vector(1536),
    search_vector   tsvector GENERATED ALWAYS AS (
                        to_tsvector('english',
                            coalesce(title, '') || ' ' || coalesce(content, ''))
                    ) STORED,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- HNSW for cosine similarity (vector search)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- GIN on generated tsvector (full-text / BM25-style search)
CREATE INDEX IF NOT EXISTS idx_chunks_search_vector_gin
    ON chunks USING GIN (search_vector);

-- GIN on generations array (filter by BBj version)
CREATE INDEX IF NOT EXISTS idx_chunks_generations_gin
    ON chunks USING GIN (generations);
```

### Register pgvector with psycopg3 Connection
```python
# Source: pgvector-python README (https://github.com/pgvector/pgvector-python)
import psycopg
from pgvector.psycopg import register_vector

conn = psycopg.connect("postgresql://localhost:5432/bbj_rag")
conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
register_vector(conn)

# Now vectors can be passed as Python lists
conn.execute(
    "INSERT INTO chunks (source_url, title, doc_type, content, content_hash, "
    "generations, embedding) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    ("https://example.com", "Title", "web", "content", "abc123",
     ["BBj 25"], [0.1, 0.2, ...]),  # 1536-dim list
)
```

### Content Hash Computation
```python
# Source: Python stdlib hashlib docs
import hashlib

def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hex digest of normalized content."""
    normalized = content.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
```

### pydantic-settings TOML Configuration
```python
# Source: pydantic-settings 2.12 docs (https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource
from pydantic_settings import PydanticBaseSettingsSource

class Settings(BaseSettings):
    model_config = SettingsConfigDict(toml_file="config.toml", env_prefix="BBJ_RAG_")

    database_url: str
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    chunk_size: int = 512
    chunk_overlap: int = 64
    flare_source_path: str = ""
    crawl_source_urls: list[str] = []

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,       # highest priority: constructor args
            env_settings,        # BBJ_RAG_DATABASE_URL, etc.
            TomlConfigSettingsSource(settings_cls),  # config.toml
        )

# Usage:
# settings = Settings()                          # from TOML + env
# settings = Settings(database_url="override")   # constructor wins
# BBJ_RAG_DATABASE_URL=... overrides TOML value
```

### Idempotent Insert with ON CONFLICT
```python
# Source: PostgreSQL 18 INSERT docs
import psycopg

def insert_chunk_idempotent(conn: psycopg.Connection, chunk) -> bool:
    """Returns True if row was inserted, False if already existed."""
    row = conn.execute(
        """
        INSERT INTO chunks (source_url, title, doc_type, content, content_hash,
                           generations, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (content_hash) DO NOTHING
        RETURNING id
        """,
        (chunk.source_url, chunk.title, chunk.doc_type, chunk.content,
         chunk.content_hash, chunk.generations,
         psycopg.types.json.Json(chunk.metadata)),
    ).fetchone()
    return row is not None
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| IVFFlat indexes only | HNSW indexes (better recall/speed tradeoff) | pgvector 0.5.0 (2023) | HNSW is now the default recommendation for ANN search |
| psycopg2 (C wrapper) | psycopg 3.x (pure Python + optional C accel) | 2021-2024 | Native async, binary protocol, COPY improvements |
| Pydantic v1 Config inner class | Pydantic v2 `model_config = ConfigDict(...)` | Pydantic 2.0 (2023) | Rust-core validation, 5-50x faster, new API surface |
| Trigger-based tsvector | GENERATED ALWAYS AS stored column | PostgreSQL 12 (2019) | No trigger code needed; database maintains column automatically |
| `parse_raw` / `from_orm` | `model_validate_json` / `model_validate` | Pydantic 2.0 (2023) | Old methods deprecated, new ones are the standard |

**Deprecated/outdated:**
- `psycopg2`: Still maintained but no new features. Use `psycopg` (v3) for new projects.
- Pydantic v1 `Config` inner class: Use `model_config = ConfigDict(...)` instead.
- `parse_raw` / `parse_file` / `from_orm`: Use `model_validate_json` / `model_validate` with `from_attributes=True`.
- IVFFlat as default index: HNSW is superior for most workloads (no training step, better recall).
- Trigger-based tsvector maintenance: Generated columns are the modern replacement.

## Open Questions

1. **Embedding model dimensions (config vs. DDL)**
   - What we know: The DDL hardcodes `vector(1536)` matching text-embedding-3-small. The config stores `embedding_dimensions`.
   - What's unclear: If the embedding model changes, the DDL column must also change. PostgreSQL does not support `ALTER COLUMN ... TYPE vector(N)` on existing data.
   - Recommendation: Accept 1536 as the initial dimension. If the model changes, a migration script that drops and recreates the embedding column (and HNSW index) is needed. This is acceptable because embeddings must be recomputed anyway when the model changes.

2. **What exactly to include in the content hash**
   - What we know: Hashing just the content string is the simplest approach.
   - What's unclear: Should source_url be included? If the same paragraph appears in two different pages, should it be stored twice?
   - Recommendation: Hash content only (not source_url) for true content deduplication. If per-source tracking is needed later, add a separate `chunk_sources` junction table. Start simple.

3. **TOML file location resolution**
   - What we know: pydantic-settings TomlConfigSettingsSource uses the `toml_file` path relative to CWD.
   - What's unclear: When the pipeline is invoked from different directories, the config file may not be found.
   - Recommendation: Allow `BBJ_RAG_CONFIG_PATH` env var to override the TOML file location, and default to `config.toml` in the project root.

## Sources

### Primary (HIGH confidence)
- pgvector README (https://github.com/pgvector/pgvector) - DDL syntax, HNSW index parameters, distance operators
- pgvector-python README (https://github.com/pgvector/pgvector-python) - register_vector() for psycopg3 integration
- psycopg3 official docs (https://www.psycopg.org/psycopg3/docs/basic/copy.html) - COPY protocol, write_row(), binary format
- psycopg3 usage docs (https://www.psycopg.org/psycopg3/docs/basic/usage.html) - Connection management, executemany, parameterized queries
- Pydantic official docs (https://docs.pydantic.dev/latest/concepts/models/) - BaseModel, ConfigDict, field_validator, model_construct
- pydantic-settings docs (https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - TomlConfigSettingsSource, settings_customise_sources
- PostgreSQL 18 docs on generated columns (https://www.postgresql.org/docs/current/ddl-generated-columns.html) - IMMUTABLE requirement, limitations
- PostgreSQL 18 docs on text search (https://www.postgresql.org/docs/current/textsearch-tables.html) - tsvector generated columns, GIN indexes
- PostgreSQL INSERT docs (https://www.postgresql.org/docs/current/sql-insert.html) - ON CONFLICT DO NOTHING syntax
- Python hashlib docs (https://docs.python.org/3/library/hashlib.html) - SHA-256 usage

### Secondary (MEDIUM confidence)
- Jonathan Katz hybrid search post (https://jkatz05.com/post/postgres/hybrid-search-postgres-pgvector/) - Hybrid search patterns verified against official pgvector docs
- Crunchy Data HNSW blog (https://www.crunchydata.com/blog/hnsw-indexes-with-postgres-and-pgvector) - HNSW tuning parameters cross-referenced with pgvector README
- PyPI package pages - Version numbers for psycopg 3.3.2, pgvector 0.4.2, pydantic 2.12.5, pydantic-settings 2.12.0

### Tertiary (LOW confidence)
- None - all findings verified with primary or secondary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified on PyPI with current versions; official documentation reviewed
- Architecture: HIGH - Patterns drawn from official docs for each library; DDL verified against PostgreSQL and pgvector documentation
- Pitfalls: HIGH - Each pitfall verified against official documentation (immutability requirement, pgvector dimension enforcement, psycopg3 type registration)

**Research date:** 2026-01-31
**Valid until:** 2026-03-01 (stable domain; all libraries are mature with slow release cadences)
