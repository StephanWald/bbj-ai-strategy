"""Pipeline orchestrator: parse -> intelligence -> chunk -> embed -> store.

Wires together the Flare parser, intelligence classifiers, heading-aware
chunker, embedding client, and bulk database insert into a single
end-to-end pipeline with batch processing and progress logging.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import psycopg

from bbj_rag.chunker import chunk_document
from bbj_rag.db import bulk_insert_chunks
from bbj_rag.intelligence import (
    build_context_header,
    classify_doc_type,
    extract_heading_hierarchy,
    tag_generation,
)
from bbj_rag.models import Chunk
from bbj_rag.url_mapping import classify_source_type, map_display_url

if TYPE_CHECKING:
    from bbj_rag.embedder import Embedder
    from bbj_rag.parsers import DocumentParser

logger = logging.getLogger(__name__)


def _get_existing_hashes(
    conn: psycopg.Connection[object], hashes: list[str]
) -> set[str]:
    """Query the database for content_hashes that already exist."""
    if not hashes:
        return set()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT content_hash FROM chunks WHERE content_hash = ANY(%s)",
            (hashes,),
        )
        rows = cur.fetchall()
        return {str(row[0]) for row in rows}  # type: ignore[index]


def _apply_intelligence(
    doc_source_url: str,
    doc_content: str,
    doc_metadata: dict[str, str],
) -> tuple[list[str], bool, str, str]:
    """Apply intelligence to derive generations, deprecated, doc_type.

    Returns (generations, deprecated, doc_type, context_header).
    """
    # Extract content-relative path from flare:// URL.
    # e.g. "flare://Content/bbjobjects/Window/bbjwindow.htm"
    #    -> "bbjobjects/Window/bbjwindow.htm"
    content_relative_path = ""
    if doc_source_url.startswith("flare://Content/"):
        content_relative_path = doc_source_url[len("flare://Content/") :]

    # Parse conditions from metadata.
    conditions_str = doc_metadata.get("conditions", "")
    conditions = [c.strip() for c in conditions_str.split(",") if c.strip()]

    # Tag generation.
    generations, deprecated = tag_generation(
        content_relative_path, conditions, doc_content
    )

    # Classify doc type.
    headings = extract_heading_hierarchy(doc_content)
    doc_type = classify_doc_type(headings, content_relative_path, doc_content)

    # Build context header.
    section_path = doc_metadata.get("section_path", "")
    context_header = build_context_header(section_path, "", "")

    return generations, deprecated, doc_type, context_header


def run_pipeline(
    parser: DocumentParser,
    embedder: Embedder,
    conn: psycopg.Connection[object],
    batch_size: int = 64,
    resume: bool = False,
    max_tokens: int = 400,
    overlap_tokens: int = 50,
) -> dict[str, int]:
    """Execute the full ingestion pipeline.

    Iterates documents from the parser, applies intelligence enrichment,
    chunks content, embeds in batches, and bulk-inserts into pgvector.

    Args:
        parser: DocumentParser yielding Document objects.
        embedder: Embedding provider (Ollama or OpenAI).
        conn: psycopg database connection with pgvector registered.
        batch_size: Number of chunks per embedding batch.
        resume: If True, skip chunks whose content_hash already exists.
        max_tokens: Target chunk size in approximate tokens.
        overlap_tokens: Overlap between consecutive chunks.

    Returns:
        Stats dict with keys: docs_parsed, chunks_created,
        chunks_embedded, chunks_stored.
    """
    stats = {
        "docs_parsed": 0,
        "chunks_created": 0,
        "chunks_embedded": 0,
        "chunks_stored": 0,
    }

    batch: list[Chunk] = []

    for doc in parser.parse():
        stats["docs_parsed"] += 1

        # Non-Flare parsers pre-populate doc_type, generations, etc.
        # Only apply Flare intelligence when doc_type is empty (Flare parser)
        # or "web_crawl" (web crawl parser).  Pre-populated values from new
        # parsers (e.g. "example", "concept", "article", "tutorial") are used
        # as-is.
        if doc.doc_type and doc.doc_type != "web_crawl":
            logger.debug(
                "Skipping intelligence for pre-populated doc: %s (doc_type=%s)",
                doc.source_url,
                doc.doc_type,
            )
        else:
            # Apply intelligence enrichment.
            generations, deprecated, doc_type, _header = _apply_intelligence(
                doc.source_url, doc.content, doc.metadata
            )

            # Update document fields with intelligence results.
            doc = doc.model_copy(
                update={
                    "generations": generations,
                    "deprecated": deprecated,
                    "doc_type": doc_type,
                }
            )

        # Compute source_type and display_url for URL mapping.
        source_type = classify_source_type(doc.source_url)
        display_url = map_display_url(doc.source_url)
        doc = doc.model_copy(
            update={
                "source_type": source_type,
                "display_url": display_url,
            }
        )

        # Chunk the document.
        doc_chunks = chunk_document(doc, max_tokens, overlap_tokens)
        stats["chunks_created"] += len(doc_chunks)
        batch.extend(doc_chunks)

        if len(batch) >= batch_size:
            stored = _embed_and_store(batch, embedder, conn, resume)
            stats["chunks_embedded"] += len(batch)
            stats["chunks_stored"] += stored
            logger.info(
                "Batch stored: %d/%d chunks (total: %d docs parsed)",
                stored,
                len(batch),
                stats["docs_parsed"],
            )
            batch = []

    # Process final partial batch.
    if batch:
        stored = _embed_and_store(batch, embedder, conn, resume)
        stats["chunks_embedded"] += len(batch)
        stats["chunks_stored"] += stored

    logger.info(
        "Pipeline complete: %d docs -> %d chunks -> %d embedded -> %d stored",
        stats["docs_parsed"],
        stats["chunks_created"],
        stats["chunks_embedded"],
        stats["chunks_stored"],
    )

    return stats


def _embed_and_store(
    batch: list[Chunk],
    embedder: Embedder,
    conn: psycopg.Connection[object],
    resume: bool = False,
) -> int:
    """Embed a batch of chunks and bulk-insert into the database.

    If resume=True, filters out chunks whose content_hash already
    exists in the database before embedding.
    """
    if resume:
        hashes = [c.content_hash for c in batch]
        existing = _get_existing_hashes(conn, hashes)
        if existing:
            batch = [c for c in batch if c.content_hash not in existing]
            if not batch:
                return 0

    # Generate embeddings.
    texts = [c.content for c in batch]
    vectors = embedder.embed_batch(texts)

    # Assign embeddings to chunks.
    for chunk, vector in zip(batch, vectors, strict=True):
        chunk.embedding = vector

    # Bulk insert.
    return bulk_insert_chunks(conn, batch)


__all__ = ["run_pipeline"]
