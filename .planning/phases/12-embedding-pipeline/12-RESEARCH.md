# Phase 12: Embedding Pipeline - Research

**Researched:** 2026-02-01
**Domain:** Embedding generation, vector storage, chunking, hybrid search validation
**Confidence:** HIGH

## Summary

This phase implements the full end-to-end ingestion pipeline: parse Flare documentation (already built), apply BBj intelligence (already built), chunk content, embed via a configurable model, and store in pgvector with hybrid search validation. The existing codebase provides `Document` objects from `FlareParser`, intelligence functions (`tag_generation`, `classify_doc_type`, `build_context_header`), a `Chunk` model with `from_content()` factory, and basic `insert_chunk`/`insert_chunks_batch` database operations. The schema already defines the `chunks` table with `vector(1536)`, `search_vector` tsvector, `generations` array, and all necessary indexes.

The key new work is: (1) a heading-aware chunker that splits `Document.content` (markdown) into `Chunk` objects, (2) an embedding client abstraction over Ollama (primary) and OpenAI (fallback) with batch processing, (3) replacing the existing `executemany` insert with psycopg3's binary COPY protocol for bulk performance, (4) a CLI that orchestrates the full pipeline, and (5) a YAML-driven search validation suite.

**Primary recommendation:** Use Qwen3-Embedding-0.6B (1024 dimensions) via Ollama as the default embedding model, implement heading-aware markdown chunking with a 400-token target, bulk-insert via psycopg3 binary COPY protocol, orchestrate with Click CLI, and validate with a YAML-driven pytest assertion suite covering both dense vector and BM25 keyword search.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ollama | >=0.6,<1 | Local embedding inference via Ollama API | Official Python client; supports batch embed, async, `dimensions` param for MRL models |
| click | >=8.1,<9 | CLI framework | Mature, zero type-hint magic, explicit decorators; already used across ecosystem (Flask, etc.) |
| psycopg[binary] | >=3.3,<4 | PostgreSQL driver (already installed) | Binary COPY protocol for bulk vector inserts; register_vector already in use |
| pgvector | >=0.4,<0.5 | Vector type adapter (already installed) | Provides `register_vector()` and COPY-compatible vector type serialization |
| pydantic | >=2.12,<3 | Data models (already installed) | `Chunk` and `Document` models already defined |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openai | >=1.0,<2 | API fallback embedding provider | When Ollama unavailable or user prefers cloud inference |
| pyyaml | >=6.0,<7 | Parse YAML validation cases file | Loading search validation test cases |
| numpy | >=1.26,<3 | Vector operations (optional) | Only if needed for embedding array manipulation; pgvector handles numpy arrays natively in COPY |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| click | typer | Typer is built on Click; adds type-hint magic and rich dependency. Click is more explicit, no extra deps, and the project already avoids unnecessary abstractions |
| click | argparse | argparse is stdlib but verbose for multi-command CLIs. Click's decorator model is cleaner for `bbj-rag ingest` + sub-stage commands |
| openai (fallback) | voyageai | Voyage AI has strong retrieval performance but adds a vendor-specific SDK. OpenAI is more universal and the existing config already references `text-embedding-3-small` |
| Qwen3-Embedding-0.6B | nomic-embed-text | nomic-embed-text has good long-context performance (8K tokens) but Qwen3-Embedding-0.6B scores higher on MTEB (64.33 vs ~53 retrieval), has 32K context, MRL support for flexible dimensions, and is the model referenced in the success criteria |

**Installation:**
```bash
cd rag-ingestion
uv add ollama click pyyaml
uv add --group dev openai  # fallback provider, dev-only unless configured
```

## Architecture Patterns

### Recommended Project Structure
```
src/bbj_rag/
├── __init__.py
├── config.py              # Settings (extend with embedding/chunking config)
├── models.py              # Document, Chunk (already exist)
├── db.py                  # get_connection, insert_chunk (extend with COPY bulk)
├── schema.py              # DDL application (already exists)
├── chunker.py             # NEW: heading-aware markdown chunker
├── embedder.py            # NEW: embedding client abstraction (Ollama + API fallback)
├── pipeline.py            # NEW: orchestrator wiring parse -> tag -> chunk -> embed -> store
├── cli.py                 # NEW: Click CLI entry point
├── intelligence/          # (already exists)
├── parsers/               # (already exists)
sql/
├── schema.sql             # DDL (update vector dimension)
tests/
├── test_chunker.py        # NEW: chunker unit tests
├── test_embedder.py       # NEW: embedder unit tests (mocked)
├── test_pipeline.py       # NEW: pipeline integration tests
├── test_search_validation.py  # NEW: hybrid search validation assertions
├── validation_cases.yaml  # NEW: search test cases data file
```

### Pattern 1: Heading-Aware Markdown Chunker

**What:** Split Document.content (markdown produced by FlareParser) at heading boundaries, then sub-split oversized sections at paragraph/sentence boundaries. Preserve code blocks intact. Prepend context_header to chunk text before embedding.

**When to use:** Always -- this is the chunking strategy for the pipeline.

**Design:**
```python
# Source: Chunking best practices research (Firecrawl, Weaviate, Unstructured)
import re
from bbj_rag.models import Document, Chunk

# Phase 1: Split by markdown headings (## and ###)
# Phase 2: If a section exceeds max_tokens, sub-split at paragraph (\n\n) boundaries
# Phase 3: Never split inside a code fence (``` ... ```)
# Each chunk inherits Document metadata + heading path for context

def chunk_document(
    doc: Document,
    max_tokens: int = 400,
    overlap_tokens: int = 50,
) -> list[Chunk]:
    """Split a Document into Chunks using heading-aware strategy.

    1. Split content at heading boundaries (##, ###)
    2. Sub-split oversized sections at paragraph boundaries
    3. Keep code blocks intact (never split inside ``` fences)
    4. Prepend context_header to chunk content for embedding
    5. Create Chunk via from_content() factory (auto-computes content_hash)
    """
    sections = _split_at_headings(doc.content)
    chunks = []
    for heading_path, section_text in sections:
        # Build per-chunk context header with heading path
        full_header = build_context_header(
            doc.metadata.get("section_path", ""),
            doc.title,
            heading_path,
        )
        sub_chunks = _split_oversized(section_text, max_tokens, overlap_tokens)
        for text in sub_chunks:
            # Prepend context header to content for richer embedding
            embeddable_content = f"{full_header}\n\n{text}" if full_header else text
            chunk = Chunk.from_content(
                source_url=doc.source_url,
                title=doc.title,
                doc_type=doc.doc_type,
                content=embeddable_content,
                generations=doc.generations,
                context_header=full_header,
                deprecated=doc.deprecated,
                metadata=doc.metadata,
            )
            chunks.append(chunk)
    return chunks
```

**Token counting:** Use a simple whitespace tokenizer (word count / 0.75) for chunking boundaries. Exact token counts vary by model but a word-based approximation is sufficient for chunking since the embedding models all have context lengths >> 400 tokens.

### Pattern 2: Embedding Client Abstraction

**What:** A protocol-based embedding interface with Ollama and OpenAI implementations. Batch processing with configurable batch size.

**When to use:** Decouples embedding generation from the pipeline so the model/provider can be swapped via config.

**Design:**
```python
# embedder.py
from __future__ import annotations
from typing import Protocol
import ollama as ollama_client

class Embedder(Protocol):
    """Embedding provider contract."""
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
    @property
    def dimensions(self) -> int: ...

class OllamaEmbedder:
    """Local embedding via Ollama API."""
    def __init__(self, model: str = "qwen3-embedding:0.6b", dimensions: int = 1024):
        self._model = model
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = ollama_client.embed(model=self._model, input=texts)
        return response.embeddings

class OpenAIEmbedder:
    """API fallback embedding via OpenAI."""
    def __init__(self, model: str = "text-embedding-3-small", dimensions: int = 1024):
        from openai import OpenAI
        self._client = OpenAI()
        self._model = model
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(
            model=self._model,
            input=texts,
            dimensions=self._dimensions,
        )
        return [e.embedding for e in response.data]
```

### Pattern 3: Binary COPY Bulk Insert

**What:** Replace `executemany` INSERT with psycopg3 binary COPY protocol for bulk vector storage.

**When to use:** For the embed-and-store stage when inserting many chunks at once.

**Design:**
```python
# Source: pgvector-python/examples/loading/example.py (official)
import psycopg
from pgvector.psycopg import register_vector
from psycopg.types.json import Json
from bbj_rag.models import Chunk

def bulk_insert_chunks(conn: psycopg.Connection[object], chunks: list[Chunk]) -> int:
    """Bulk insert chunks using binary COPY protocol.

    Uses psycopg3's COPY FROM STDIN with FORMAT BINARY for maximum
    throughput. Falls back gracefully on content_hash conflicts by
    using a temp table + INSERT ... ON CONFLICT pattern.
    """
    if not chunks:
        return 0

    # Strategy: COPY into temp table, then INSERT ... ON CONFLICT from temp
    # This preserves idempotent dedup while using fast COPY ingestion.
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TEMP TABLE _chunks_staging (LIKE chunks INCLUDING DEFAULTS)
            ON COMMIT DROP
        """)

        with cur.copy(
            "COPY _chunks_staging (source_url, title, doc_type, content, "
            "content_hash, context_header, generations, deprecated, "
            "embedding, metadata) FROM STDIN WITH (FORMAT BINARY)"
        ) as copy:
            copy.set_types([
                'text', 'text', 'text', 'text',
                'varchar', 'text', 'text[]', 'bool',
                'vector', 'jsonb',
            ])
            for chunk in chunks:
                copy.write_row([
                    chunk.source_url,
                    chunk.title,
                    chunk.doc_type,
                    chunk.content,
                    chunk.content_hash,
                    chunk.context_header,
                    chunk.generations,
                    chunk.deprecated,
                    chunk.embedding,
                    Json(chunk.metadata),
                ])

        cur.execute("""
            INSERT INTO chunks (source_url, title, doc_type, content,
                content_hash, context_header, generations, deprecated,
                embedding, metadata)
            SELECT source_url, title, doc_type, content,
                content_hash, context_header, generations, deprecated,
                embedding, metadata
            FROM _chunks_staging
            ON CONFLICT (content_hash) DO NOTHING
        """)
        count = cur.rowcount

    conn.commit()
    return count
```

### Pattern 4: Pipeline Orchestrator

**What:** A pipeline function that wires parse -> intelligence -> chunk -> embed -> store with stage-by-stage logging.

**When to use:** Called by both CLI and tests.

**Design:**
```python
# pipeline.py
import logging
from bbj_rag.parsers.flare import FlareParser
from bbj_rag.chunker import chunk_document
from bbj_rag.embedder import Embedder
from bbj_rag.db import bulk_insert_chunks

logger = logging.getLogger(__name__)

def run_pipeline(
    parser,           # DocumentParser protocol
    embedder,         # Embedder protocol
    conn,             # psycopg connection
    batch_size: int = 64,
    resume: bool = False,
) -> dict[str, int]:
    """Execute the full ingestion pipeline.

    Returns stats dict: {docs_parsed, chunks_created, chunks_embedded, chunks_stored}
    """
    stats = {"docs_parsed": 0, "chunks_created": 0, "chunks_embedded": 0, "chunks_stored": 0}

    batch: list[Chunk] = []

    for doc in parser.parse():
        stats["docs_parsed"] += 1
        doc_chunks = chunk_document(doc)
        stats["chunks_created"] += len(doc_chunks)
        batch.extend(doc_chunks)

        if len(batch) >= batch_size:
            stored = _embed_and_store(batch, embedder, conn)
            stats["chunks_embedded"] += len(batch)
            stats["chunks_stored"] += stored
            logger.info(
                "Batch stored: %d/%d chunks (total: %d docs)",
                stored, len(batch), stats["docs_parsed"],
            )
            batch = []

    # Final partial batch
    if batch:
        stored = _embed_and_store(batch, embedder, conn)
        stats["chunks_embedded"] += len(batch)
        stats["chunks_stored"] += stored

    return stats
```

### Pattern 5: YAML-Driven Search Validation

**What:** Validation test cases in a YAML file, loaded by pytest, asserting search relevance.

**Design:**
```yaml
# tests/validation_cases.yaml
dense_search:
  - query: "How to add a button to a BBjWindow"
    expect_in_top_5:
      - url_contains: "bbjobjects/Window"
      - title_contains: "addButton"

  - query: "BBj string functions"
    expect_in_top_5:
      - doc_type: "language-reference"

bm25_search:
  - query: "BBjWindow addButton"
    expect_in_top_5:
      - url_contains: "addButton"

  - query: "PROCESS_EVENTS callback"
    expect_in_top_5:
      - content_contains: "PROCESS_EVENTS"

filtered_search:
  - query: "GUI window creation"
    filter_generation: "bbj_gui"
    expect_in_top_5:
      - generations_contains: "bbj_gui"
    expect_not_in_top_5:
      - generations_contains: "vpro5"
```

```python
# tests/test_search_validation.py
import yaml
import pytest

def load_cases(section: str):
    with open("tests/validation_cases.yaml") as f:
        data = yaml.safe_load(f)
    return data.get(section, [])

@pytest.mark.parametrize("case", load_cases("dense_search"), ids=lambda c: c["query"][:40])
def test_dense_search(db_conn, embedder, case):
    """Assert dense vector search returns expected results."""
    query_embedding = embedder.embed_batch([case["query"]])[0]
    results = execute_dense_search(db_conn, query_embedding, limit=5)
    for expectation in case["expect_in_top_5"]:
        assert_result_matches(results, expectation)
```

### Anti-Patterns to Avoid

- **Embedding before chunking:** Always chunk first, then embed. Embedding full documents wastes context and produces poor retrieval.
- **Splitting inside code blocks:** Never split a chunk in the middle of a ``` fenced code block. This destroys code examples and produces nonsensical embeddings.
- **Hardcoded vector dimensions:** Make the vector column dimension configurable via settings. The DDL should use a parameter, not a literal.
- **One-at-a-time embedding calls:** Always batch embedding requests. Ollama's `/api/embed` supports array input; use batch_size=64 as default.
- **Using executemany for bulk inserts:** The psycopg3 COPY protocol is 5-10x faster. Use COPY -> staging table -> INSERT ON CONFLICT for idempotent bulk loads.
- **Hardcoded test assertions:** Put search validation cases in a YAML file so engineers can add cases without writing code.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Embedding inference | Custom HTTP client to Ollama | `ollama` Python package | Handles connection, serialization, batch input, truncation, normalization |
| Token counting for chunking | BPE tokenizer | Word count / 0.75 approximation | Exact token counts vary by model; approximation is sufficient for chunking boundaries with 32K context models |
| Vector type serialization for COPY | Manual binary encoding | `pgvector.psycopg` + `register_vector()` | Handles vector <-> Python list/numpy conversion for both INSERT and COPY protocols |
| JSONB serialization | Manual JSON encoding | `psycopg.types.json.Json()` | Already in use; handles None, nested dicts, proper escaping |
| CLI argument parsing | Manual argparse setup | Click decorators | Multi-command CLI (`bbj-rag ingest`, `bbj-rag validate`) with automatic help, error handling |
| Full-text search scoring | Custom TF-IDF | PostgreSQL `ts_rank_cd()` on stored `search_vector` tsvector | Already computed as GENERATED ALWAYS column; GIN index already created |
| Content deduplication | Custom hash tracking | `ON CONFLICT (content_hash) DO NOTHING` | Already in schema; works with COPY via staging table pattern |

**Key insight:** The existing codebase already solves many hard problems (content hashing, tsvector generation, GIN/HNSW indexes, dedup). This phase wires existing pieces together rather than building from scratch.

## Common Pitfalls

### Pitfall 1: Vector Dimension Mismatch
**What goes wrong:** Schema defines `vector(1536)` but embedding model outputs 1024 dimensions. INSERT/COPY fails with a dimension mismatch error.
**Why it happens:** The existing schema was sized for OpenAI `text-embedding-3-small` (1536d). Qwen3-Embedding-0.6B outputs 1024d by default.
**How to avoid:** Update `sql/schema.sql` to use a configurable dimension matching the chosen model. Change HNSW index accordingly. Update `config.toml` defaults to 1024.
**Warning signs:** `ERROR: expected 1536 dimensions, not 1024` on first insert.

### Pitfall 2: COPY Protocol Type Mismatch
**What goes wrong:** Binary COPY fails silently or throws cryptic errors when column types don't exactly match.
**Why it happens:** PostgreSQL's binary COPY applies no implicit casts. A Python `list[float]` won't auto-cast to `vector` without `register_vector()` and `set_types(['vector'])`.
**How to avoid:** Always call `register_vector(conn)` first, always use `set_types()` in the COPY context, and test with a small batch before full pipeline run.
**Warning signs:** `UntypedDataError` or `BadCopyFileFormat` from psycopg3.

### Pitfall 3: Splitting Code Blocks Mid-Chunk
**What goes wrong:** A BBj code example gets split across two chunks, making both chunks semantically incomplete.
**Why it happens:** Naive character/token-count splitters don't understand markdown fence boundaries.
**How to avoid:** The chunker must detect ``` fences and treat the entire block as atomic. If a code block + surrounding text exceeds max_tokens, the code block stays in its own chunk.
**Warning signs:** Chunks that start or end with partial ``` fences.

### Pitfall 4: Missing context_header in Embeddings
**What goes wrong:** Search for "BBjWindow addButton" fails because the chunk content says "Adds a button control" without mentioning BBjWindow -- that context lives in the heading hierarchy.
**Why it happens:** context_header is stored separately (to avoid content_hash mutation) but not included in the text sent to the embedding model.
**How to avoid:** Prepend `context_header` to chunk content before embedding. Store the raw content in the `content` column (with header prepended) so the tsvector also benefits.
**Warning signs:** Dense search misses obviously relevant chunks; BM25 search works better than dense (because tsvector includes context_header).

### Pitfall 5: Ollama Model Not Pulled
**What goes wrong:** Pipeline crashes immediately with a connection error or model-not-found error.
**Why it happens:** User hasn't run `ollama pull qwen3-embedding:0.6b` before running the pipeline.
**How to avoid:** Check model availability at pipeline start. Log a clear error message with the pull command if model is missing.
**Warning signs:** `ResponseError: model 'qwen3-embedding:0.6b' not found` from ollama client.

### Pitfall 6: Content Hash Changes When Context Header Is Prepended
**What goes wrong:** Re-running the pipeline produces all-new chunks (no dedup) because content now includes the context header, changing the hash.
**Why it happens:** `Chunk.from_content()` hashes `content.strip()`. If context_header is prepended to content, the hash changes.
**How to avoid:** Two options: (a) hash only the raw section text before prepending header, or (b) accept that the embeddable content IS the canonical content and hash that. Recommendation: include context_header in content and accept the hash includes it -- this means changing context_header layout triggers re-embedding, which is correct behavior.
**Warning signs:** Pipeline stores duplicate chunks on re-run; chunk count doubles.

## Code Examples

### Ollama Batch Embedding (Verified)
```python
# Source: https://docs.ollama.com/capabilities/embeddings
# Source: https://github.com/ollama/ollama-python
import ollama

# Single text
response = ollama.embed(
    model='qwen3-embedding:0.6b',
    input='BBjWindow addButton method',
)
# response.embeddings is a list with one vector (list[list[float]])

# Batch of texts
response = ollama.embed(
    model='qwen3-embedding:0.6b',
    input=[
        'BBjWindow addButton method',
        'PROCESS_EVENTS callback handling',
        'BBj string manipulation functions',
    ],
)
# response.embeddings is a list of 3 vectors
```

### psycopg3 Binary COPY with Vectors (Verified)
```python
# Source: https://github.com/pgvector/pgvector-python/blob/master/examples/loading/example.py
import psycopg
from pgvector.psycopg import register_vector

conn = psycopg.connect(dbname='bbj_rag', autocommit=True)
register_vector(conn)

cur = conn.cursor()
with cur.copy('COPY items (embedding) FROM STDIN WITH (FORMAT BINARY)') as copy:
    copy.set_types(['vector'])
    for embedding in embeddings:
        copy.write_row([embedding])
```

### Hybrid Search SQL (Verified Pattern)
```sql
-- Source: https://jkatz05.com/post/postgres/hybrid-search-postgres-pgvector/

-- Reciprocal Rank Fusion function
CREATE OR REPLACE FUNCTION rrf_score(rank int, rrf_k int DEFAULT 50)
RETURNS numeric AS $$
    SELECT COALESCE(1.0 / ($1 + $2), 0.0);
$$ LANGUAGE sql IMMUTABLE;

-- Hybrid search combining dense vector + BM25 keyword
SELECT id, source_url, title, content,
    sum(rrf_score) AS score
FROM (
    -- Dense vector search
    (SELECT id, source_url, title, content,
        rank() OVER (ORDER BY embedding <=> $1::vector) AS rank,
        1.0 / (rank() OVER (ORDER BY embedding <=> $1::vector) + 50) AS rrf_score
     FROM chunks
     ORDER BY embedding <=> $1::vector
     LIMIT 20)
    UNION ALL
    -- BM25 keyword search
    (SELECT id, source_url, title, content,
        rank() OVER (ORDER BY ts_rank_cd(search_vector, query) DESC) AS rank,
        1.0 / (rank() OVER (ORDER BY ts_rank_cd(search_vector, query) DESC) + 50) AS rrf_score
     FROM chunks, plainto_tsquery('english', $2) query
     WHERE search_vector @@ query
     LIMIT 20)
) searches
GROUP BY id, source_url, title, content
ORDER BY score DESC
LIMIT $3;
```

### Generation-Filtered Search
```sql
-- Dense vector search filtered by generation
SELECT id, source_url, title, content,
    1 - (embedding <=> $1::vector) AS similarity
FROM chunks
WHERE generations @> ARRAY[$2::text]  -- uses GIN index on generations
ORDER BY embedding <=> $1::vector
LIMIT $3;
```

### Click CLI Structure
```python
# Source: Click documentation
import click
import logging

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable debug logging')
def cli(verbose: bool) -> None:
    """BBj RAG ingestion pipeline."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

@cli.command()
@click.option('--source', type=click.Choice(['flare']), required=True)
@click.option('--resume', is_flag=True, help='Skip already-stored chunks')
@click.option('--batch-size', default=64, type=int, help='Embedding batch size')
def ingest(source: str, resume: bool, batch_size: int) -> None:
    """Run the full ingestion pipeline."""
    click.echo(f"Starting ingestion for source: {source}")
    # ... wire up pipeline

@cli.command()
@click.option('--source', type=click.Choice(['flare']), required=True)
def parse(source: str) -> None:
    """Parse source documents (no embedding)."""
    # ... parse only

@cli.command()
def validate() -> None:
    """Run search validation assertions."""
    # ... run validation suite

# Entry point in pyproject.toml:
# [project.scripts]
# bbj-rag = "bbj_rag.cli:cli"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| text-embedding-ada-002 (1536d) | text-embedding-3-small (1536d) or Qwen3-Embedding (1024d) | 2024-2025 | Higher MTEB scores, flexible dimensions via MRL, local-first option |
| Fixed-size chunking (500 chars) | Heading-aware + recursive sub-splitting | 2024-2025 | 5-10% retrieval accuracy improvement for structured docs |
| Row-by-row INSERT | psycopg3 binary COPY protocol | psycopg3 3.x | 5-10x throughput improvement for bulk loads |
| Separate Elasticsearch for BM25 | PostgreSQL tsvector + pgvector in same DB | 2024-2025 | Single database, ACID consistency, no sync issues |
| Custom RRF implementation | SQL-based RRF with UNION ALL + window functions | Established pattern | Pure SQL, no application-layer reranking needed |

**Deprecated/outdated:**
- `ollama.embeddings()` (single prompt): Replaced by `ollama.embed()` (batch input) -- the older endpoint still works but the newer one is recommended
- OpenAI `text-embedding-ada-002`: Superseded by `text-embedding-3-small` with better performance at same price

## Embedding Model Recommendation

**Primary: Qwen3-Embedding-0.6B via Ollama** (Claude's Discretion)

| Property | Value |
|----------|-------|
| Model ID | `qwen3-embedding:0.6b` |
| Default Dimensions | 1024 |
| MRL Support | Yes (32-1024 configurable) |
| Context Length | 32K tokens |
| MTEB Score | 64.33 (multilingual) |
| File Size | 639 MB |
| Speed | Fast on GPU hardware |

**Rationale:**
- Referenced in success criteria as target model
- 1024 dimensions is optimal for a corpus of 2-5K docs: enough for fine-grained semantic distinction without excessive storage/index overhead
- 32K context length handles even the largest BBj documentation pages without truncation
- MRL support means dimensions can be adjusted later without changing models
- User has strong GPU hardware; local inference avoids API costs and latency
- MTEB 64.33 is competitive with nomic-embed-text (53 retrieval) and approaches mxbai-embed-large (64.68) while being newer and having much longer context

**Fallback: OpenAI text-embedding-3-small** with `dimensions=1024`
- Supports MRL-style dimension reduction via API `dimensions` parameter
- $0.02/1M tokens (estimated ~$0.05 for full 2-5K doc corpus)
- Same 1024 dimensions for compatibility with same pgvector schema

**Schema impact:** Change `vector(1536)` to `vector(1024)` in `sql/schema.sql`. Update `config.toml` defaults.

## Chunking Recommendation

**Strategy: Heading-aware with recursive sub-splitting** (Claude's Discretion)

| Parameter | Recommended Value | Rationale |
|-----------|-------------------|-----------|
| Primary split | Markdown headings (##, ###) | BBj docs have clear heading structure from FlareParser |
| Max chunk tokens | 400 | Sweet spot for dense retrieval (research shows 200-400 optimal) |
| Overlap tokens | 50 | ~12% overlap preserves cross-boundary context |
| Sub-split boundary | Paragraph (\n\n), then sentence | Preserves paragraph coherence |
| Code block handling | Keep intact, never split | Code examples are atomic units |
| Context header | Prepend to chunk content | Ensures embedding captures hierarchy context |

**Why not fixed-size:** BBj documentation has strong heading structure (Description, Syntax, Parameters, Return Value). Heading-aware splitting preserves these semantic sections as chunks, which is 5-10% more effective for retrieval than blind character splitting.

**Why not semantic chunking:** Semantic chunking (using embeddings to find split points) adds a second embedding pass and complexity. Heading-aware splitting captures the same boundaries more efficiently since the structure is already explicit in the markdown.

## CLI Framework Recommendation

**Click** (Claude's Discretion)

- Mature, stable, well-documented
- Explicit decorator syntax -- no type-hint magic
- Multi-command groups (`bbj-rag ingest`, `bbj-rag parse`, `bbj-rag validate`)
- No extra dependencies beyond Click itself (typer pulls in rich, shellingham)
- Consistent with the project's style: explicit over implicit

## Validation Cases Recommendation

**YAML format with ~15 initial cases** (Claude's Discretion)

| Category | Initial Count | Coverage |
|----------|---------------|----------|
| Dense vector search | 5 cases | Core API docs, language reference, concepts |
| BM25 keyword search | 5 cases | BBj-specific terms, method names, code patterns |
| Generation-filtered search | 3 cases | bbj_gui filter, dwc filter, cross-gen "all" |
| Negative cases | 2 cases | Ensure irrelevant results NOT in top-5 |

**Why YAML over TOML:** YAML handles nested structures (expect_in_top_5 lists) more naturally and is the standard format for test data files. TOML's array-of-tables syntax is awkward for this use case.

**Batch size recommendation:** 64 chunks per embedding batch. This balances Ollama throughput (GPU utilization) with memory usage. Can be tuned via `--batch-size` CLI flag.

## Open Questions

1. **HNSW index rebuild after dimension change**
   - What we know: Changing `vector(1536)` to `vector(1024)` requires dropping and recreating the HNSW index
   - What's unclear: Whether `IF NOT EXISTS` on index creation handles dimension change gracefully
   - Recommendation: Include explicit `DROP INDEX IF EXISTS` + `CREATE INDEX` in schema migration for this phase

2. **Ollama batch size limits**
   - What we know: Ollama `/api/embed` accepts array input; no documented hard limit
   - What's unclear: Whether very large batches (>100 items) cause OOM on the Ollama server
   - Recommendation: Start with batch_size=64; configurable via CLI. If OOM occurs, reduce automatically with retry

3. **Content hash stability across re-runs**
   - What we know: `Chunk.from_content()` hashes `content.strip()`. If context_header is prepended to content, the hash changes
   - What's unclear: Whether the user wants context_header changes to trigger re-embedding (correct behavior) or not (optimization)
   - Recommendation: Include context_header in content (and therefore in hash). Document that changing heading structure triggers re-embedding, which is the correct behavior for search quality

## Sources

### Primary (HIGH confidence)
- [pgvector-python loading example](https://github.com/pgvector/pgvector-python/blob/master/examples/loading/example.py) - Binary COPY with vectors
- [psycopg3 COPY documentation](https://www.psycopg.org/psycopg3/docs/basic/copy.html) - write_row, set_types, binary format
- [Ollama embed API docs](https://docs.ollama.com/capabilities/embeddings) - /api/embed endpoint, batch input, truncate, dimensions
- [Ollama Python client](https://github.com/ollama/ollama-python) - embed() function, async support
- [Qwen3-Embedding on Ollama](https://ollama.com/library/qwen3-embedding) - Model specs, dimension ranges, context lengths
- [pgvector-python README](https://github.com/pgvector/pgvector-python) - register_vector(), psycopg3 integration

### Secondary (MEDIUM confidence)
- [Qwen3-Embedding-0.6B on HuggingFace](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) - 1024 default dimensions, MRL support, MTEB 64.33
- [Hybrid search with pgvector](https://jkatz05.com/post/postgres/hybrid-search-postgres-pgvector/) - RRF scoring pattern, UNION ALL approach
- [Chunking best practices (Firecrawl)](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025) - Heading-aware splitting, 400 token target
- [Chunking strategies (Weaviate)](https://weaviate.io/blog/chunking-strategies-for-rag) - Hybrid two-pass approach
- [OpenAI embeddings API](https://platform.openai.com/docs/api-reference/embeddings) - Batch input, dimensions parameter
- [nomic-embed-text vs mxbai-embed-large benchmarks](https://www.tigerdata.com/blog/finding-the-best-open-source-embedding-model-for-rag) - MTEB retrieval comparison

### Tertiary (LOW confidence)
- [Click vs Typer comparison](https://johal.in/click-vs-typer-comparison-choosing-cli-frameworks-for-python-application-distribution/) - Framework comparison (single source, opinion piece)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified via official docs and PyPI; pgvector/psycopg3 already in use in codebase
- Architecture: HIGH - COPY protocol pattern from official pgvector examples; chunking patterns from multiple authoritative sources
- Embedding model: HIGH - Qwen3-Embedding-0.6B specs verified on Ollama library page and HuggingFace; dimensions confirmed at 1024
- Pitfalls: HIGH - Vector dimension mismatch is a concrete, verifiable issue; COPY type requirements verified in psycopg3 docs
- Hybrid search: MEDIUM - RRF pattern verified from blog post by pgvector maintainer (Jonathan Katz) but not from official PostgreSQL docs

**Research date:** 2026-02-01
**Valid until:** 2026-03-01 (30 days - libraries are stable; Ollama model library changes weekly but Qwen3 is established)
