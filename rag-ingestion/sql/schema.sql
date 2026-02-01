-- BBj RAG Ingestion Pipeline: pgvector Schema DDL
--
-- This schema defines the chunks table for storing documentation fragments
-- with vector embeddings (pgvector), full-text search (tsvector), and
-- content-hash deduplication.
--
-- Pitfalls avoided:
--   1. Two-arg to_tsvector('english', ...) used instead of single-arg form.
--      Single-arg is STABLE (depends on default_text_search_config GUC),
--      which PostgreSQL rejects in GENERATED ALWAYS columns.
--   2. String concatenation uses the || operator, NOT concat() / concat_ws().
--      Those functions are STABLE, not IMMUTABLE, and fail in generated columns.
--   3. Columns wrapped with coalesce(col, '') because NULL || 'text' returns NULL.
--   4. UNIQUE on content_hash auto-creates a btree index; no separate index needed.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id              BIGSERIAL       PRIMARY KEY,
    source_url      TEXT            NOT NULL,
    title           TEXT            NOT NULL,
    doc_type        TEXT            NOT NULL,
    content         TEXT            NOT NULL,
    content_hash    VARCHAR(64)     NOT NULL UNIQUE,
    context_header  TEXT            NOT NULL DEFAULT '',
    generations     TEXT[]          NOT NULL DEFAULT '{}',
    deprecated      BOOLEAN         NOT NULL DEFAULT false,
    -- 1024 dimensions matches Qwen3-Embedding-0.6B default output.
    embedding       vector(1024),
    search_vector   tsvector        GENERATED ALWAYS AS (
                        to_tsvector('english', coalesce(context_header, '') || ' ' || coalesce(title, '') || ' ' || coalesce(content, ''))
                    ) STORED,
    metadata        JSONB           NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- HNSW index for approximate nearest-neighbor cosine similarity search.
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- GIN index for full-text search on the generated tsvector column.
CREATE INDEX IF NOT EXISTS idx_chunks_search_vector_gin
    ON chunks USING GIN (search_vector);

-- GIN index for array containment queries on the generations column.
CREATE INDEX IF NOT EXISTS idx_chunks_generations_gin
    ON chunks USING GIN (generations);
