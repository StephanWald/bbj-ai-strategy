"""Database connection and chunk insert operations for the RAG pipeline.

Provides connection management with pgvector type registration, and
idempotent chunk insertion with ON CONFLICT content_hash deduplication.
"""

from __future__ import annotations

import psycopg
from pgvector.psycopg import register_vector  # type: ignore[import-untyped]
from psycopg.types.json import Json

from bbj_rag.models import Chunk

# SQL for idempotent chunk insert. ON CONFLICT (content_hash) DO NOTHING
# skips duplicates, allowing safe re-ingestion of the same content.
_INSERT_CHUNK_SQL = """
INSERT INTO chunks (
    source_url, title, doc_type, content, content_hash,
    context_header, generations, deprecated, embedding, metadata
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (content_hash) DO NOTHING
RETURNING id
"""


def get_connection(database_url: str) -> psycopg.Connection[tuple[object, ...]]:
    """Open a psycopg connection with pgvector types registered.

    The caller owns the connection lifecycle -- use as a context manager
    or call close() explicitly.
    """
    conn: psycopg.Connection[tuple[object, ...]] = psycopg.connect(database_url)
    register_vector(conn)
    return conn


def _chunk_to_params(chunk: Chunk) -> tuple[object, ...]:
    """Convert a Chunk model to a parameter tuple for the INSERT statement."""
    return (
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
    )


def insert_chunk(conn: psycopg.Connection[object], chunk: Chunk) -> bool:
    """Insert a single chunk, returning True if inserted, False if duplicate.

    Uses ON CONFLICT (content_hash) DO NOTHING for idempotent deduplication.
    The JSONB metadata column is serialized via psycopg Json() adapter.
    """
    with conn.cursor() as cur:
        cur.execute(_INSERT_CHUNK_SQL, _chunk_to_params(chunk))
        inserted = cur.fetchone() is not None
    conn.commit()
    return inserted


def insert_chunks_batch(conn: psycopg.Connection[object], chunks: list[Chunk]) -> int:
    """Insert multiple chunks, returning the count of newly inserted rows.

    Duplicates (by content_hash) are silently skipped via ON CONFLICT DO NOTHING.
    Uses executemany for batch efficiency.
    """
    if not chunks:
        return 0
    params_list = [_chunk_to_params(c) for c in chunks]
    with conn.cursor() as cur:
        cur.executemany(_INSERT_CHUNK_SQL, params_list)
        count: int = cur.rowcount
    conn.commit()
    return count


def bulk_insert_chunks(conn: psycopg.Connection[object], chunks: list[Chunk]) -> int:
    """Bulk insert chunks using psycopg3 binary COPY protocol.

    Uses a staging table + INSERT ... ON CONFLICT pattern to combine
    fast COPY throughput with idempotent content_hash deduplication.

    Returns the number of newly inserted rows (excludes duplicates).
    """
    if not chunks:
        return 0

    with conn.cursor() as cur:
        cur.execute(
            "CREATE TEMP TABLE _chunks_staging "
            "(LIKE chunks INCLUDING DEFAULTS) ON COMMIT DROP"
        )

        with cur.copy(
            "COPY _chunks_staging ("
            "source_url, title, doc_type, content, content_hash, "
            "context_header, generations, deprecated, embedding, metadata"
            ") FROM STDIN WITH (FORMAT BINARY)"
        ) as copy:
            copy.set_types(
                [
                    "text",
                    "text",
                    "text",
                    "text",
                    "varchar",
                    "text",
                    "text[]",
                    "bool",
                    "vector",
                    "jsonb",
                ]
            )
            for chunk in chunks:
                copy.write_row(
                    [
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
                    ]
                )

        cur.execute(
            "INSERT INTO chunks ("
            "source_url, title, doc_type, content, content_hash, "
            "context_header, generations, deprecated, embedding, metadata"
            ") SELECT "
            "source_url, title, doc_type, content, content_hash, "
            "context_header, generations, deprecated, embedding, metadata "
            "FROM _chunks_staging "
            "ON CONFLICT (content_hash) DO NOTHING"
        )
        count: int = cur.rowcount

    conn.commit()
    return count
