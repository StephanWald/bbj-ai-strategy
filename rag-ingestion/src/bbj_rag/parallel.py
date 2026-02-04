"""Parallel ingestion worker module for concurrent embedding.

Provides a ParallelIngestor class that processes chunks in batches using
multiple asyncio workers, with retry logic and failure tracking for
partial failure recovery.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pgvector.psycopg import register_vector_async  # type: ignore[import-untyped]
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from bbj_rag.embedder import AsyncOllamaEmbedder

if TYPE_CHECKING:
    from bbj_rag.config import Settings
    from bbj_rag.models import Chunk


@dataclass
class IngestResult:
    """Result of a parallel ingestion run."""

    chunks_embedded: int = 0
    chunks_stored: int = 0
    batches_completed: int = 0
    batches_failed: int = 0
    failed_chunks: list[Chunk] = field(default_factory=list)
    duration: float = 0.0


class ParallelIngestor:
    """Parallel chunk ingestion with asyncio worker pool.

    Uses multiple workers to embed and store chunks concurrently.
    Each worker has its own AsyncOllamaEmbedder for connection pool isolation.

    Usage::

        ingestor = ParallelIngestor(settings, num_workers=4)
        result = await ingestor.ingest_chunks(chunks, db_url)
        if result.failed_chunks:
            path = Path(".failures.json")
            ingestor.save_failure_log(result.failed_chunks, path, "embed failed")
    """

    def __init__(
        self,
        settings: Settings,
        num_workers: int = 4,
        batch_size: int = 64,
        verbose: bool = False,
    ) -> None:
        self._settings = settings
        self._num_workers = num_workers
        self._batch_size = batch_size
        self._verbose = verbose
        self._retries = settings.ingest_batch_retries

    async def ingest_chunks(
        self,
        chunks: list[Chunk],
        db_url: str,
    ) -> IngestResult:
        """Process chunks in parallel using asyncio worker pool.

        Distributes chunks into batches and processes them concurrently.
        Failed batches are retried with exponential backoff.

        Args:
            chunks: List of Chunk objects to embed and store.
            db_url: PostgreSQL connection URL.

        Returns:
            IngestResult with stats and any failed chunks.
        """
        start_time = time.monotonic()

        # Create batches
        batches: list[list[Chunk]] = []
        for i in range(0, len(chunks), self._batch_size):
            batches.append(chunks[i : i + self._batch_size])

        total_batches = len(batches)
        if self._verbose:
            n, b, w = len(chunks), total_batches, self._num_workers
            print(f"[Ingestor] {n} chunks / {b} batches / {w} workers")

        # Set up work queue
        queue: asyncio.Queue[tuple[int, list[Chunk]]] = asyncio.Queue()
        for idx, batch in enumerate(batches):
            await queue.put((idx, batch))

        # Stats tracking (thread-safe via asyncio single-threaded nature)
        result = IngestResult()
        result_lock = asyncio.Lock()

        # Create connection pool
        async with AsyncConnectionPool(
            db_url, min_size=1, max_size=self._num_workers + 1
        ) as pool:
            # Register pgvector on pool connections
            async with pool.connection() as conn:
                await register_vector_async(conn)

            # Spawn workers
            workers = [
                asyncio.create_task(
                    self._worker(
                        worker_id=i + 1,
                        queue=queue,
                        pool=pool,
                        result=result,
                        result_lock=result_lock,
                        total_batches=total_batches,
                    )
                )
                for i in range(self._num_workers)
            ]

            # Wait for all workers to complete
            await asyncio.gather(*workers)

        result.duration = time.monotonic() - start_time
        return result

    async def _worker(
        self,
        worker_id: int,
        queue: asyncio.Queue[tuple[int, list[Chunk]]],
        pool: AsyncConnectionPool,
        result: IngestResult,
        result_lock: asyncio.Lock,
        total_batches: int,
    ) -> None:
        """Worker coroutine that processes batches from the queue."""
        async with AsyncOllamaEmbedder(
            model=self._settings.embedding_model,
            dimensions=self._settings.embedding_dimensions,
            host=self._settings.ollama_host,
        ) as embedder:
            while True:
                try:
                    batch_idx, batch = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

                success = await self._process_batch_with_retry(
                    worker_id=worker_id,
                    batch_idx=batch_idx,
                    batch=batch,
                    embedder=embedder,
                    pool=pool,
                    result=result,
                    result_lock=result_lock,
                    total_batches=total_batches,
                )

                if not success:
                    async with result_lock:
                        result.batches_failed += 1
                        result.failed_chunks.extend(batch)

                queue.task_done()

    async def _process_batch_with_retry(
        self,
        worker_id: int,
        batch_idx: int,
        batch: list[Chunk],
        embedder: AsyncOllamaEmbedder,
        pool: AsyncConnectionPool,
        result: IngestResult,
        result_lock: asyncio.Lock,
        total_batches: int,
    ) -> bool:
        """Process a single batch with retry logic."""
        for attempt in range(self._retries):
            try:
                # Embed the batch
                texts = [c.content for c in batch]
                vectors = await embedder.embed_batch(texts)

                # Assign embeddings
                for chunk, vector in zip(batch, vectors, strict=True):
                    chunk.embedding = vector

                # Store to database
                async with pool.connection() as conn:
                    await register_vector_async(conn)
                    stored = await self._bulk_insert_async(conn, batch)

                async with result_lock:
                    result.chunks_embedded += len(batch)
                    result.chunks_stored += stored
                    result.batches_completed += 1
                    completed = result.batches_completed

                if self._verbose:
                    n = len(batch)
                    print(f"[W{worker_id}] {completed}/{total_batches} ({n} chunks)")

                return True

            except Exception as e:
                if attempt < self._retries - 1:
                    backoff = 2**attempt  # 1s, 2s, 4s
                    if self._verbose:
                        b, a = batch_idx + 1, attempt + 1
                        print(f"[W{worker_id}] batch {b} retry {a}: {e}")
                    await asyncio.sleep(backoff)
                else:
                    if self._verbose:
                        print(f"[W{worker_id}] batch {batch_idx + 1} FAILED: {e}")

        return False

    async def _bulk_insert_async(
        self,
        conn: AsyncConnection[Any],
        chunks: list[Chunk],
    ) -> int:
        """Async bulk insert using psycopg3 async interface."""
        from psycopg.types.json import Json

        if not chunks:
            return 0

        # Use executemany for async compatibility (COPY not easily available in async)
        insert_sql = """
            INSERT INTO chunks (
                source_url, title, doc_type, content, content_hash,
                context_header, generations, deprecated,
                source_type, display_url, embedding, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (content_hash) DO NOTHING
        """

        params_list = [
            (
                chunk.source_url,
                chunk.title,
                chunk.doc_type,
                chunk.content,
                chunk.content_hash,
                chunk.context_header,
                chunk.generations,
                chunk.deprecated,
                chunk.source_type,
                chunk.display_url,
                chunk.embedding,
                Json(chunk.metadata),
            )
            for chunk in chunks
        ]

        # Use the connection's cursor for executemany
        async with conn.cursor() as cur:
            for params in params_list:
                await cur.execute(insert_sql, params)
            count = cur.rowcount

        await conn.commit()
        return count if count > 0 else len(chunks)

    @staticmethod
    def save_failure_log(
        failed_chunks: list[Chunk],
        filepath: Path,
        error: str,
    ) -> None:
        """Save failed chunks to a JSON lines file.

        Appends to existing file if present (doesn't overwrite prior failures).

        Args:
            failed_chunks: List of Chunk objects that failed.
            filepath: Path to the failure log file.
            error: Error message describing the failure.
        """
        with filepath.open("a") as f:
            for chunk in failed_chunks:
                entry = {
                    "content_hash": chunk.content_hash,
                    "source_url": chunk.source_url,
                    "error": error,
                }
                f.write(json.dumps(entry) + "\n")

    @staticmethod
    def load_failure_log(filepath: Path) -> list[dict[str, str]]:
        """Load failed chunk entries from a JSON lines file.

        Returns:
            List of dicts with content_hash, source_url, and error fields.
        """
        if not filepath.exists():
            return []

        entries: list[dict[str, str]] = []
        with filepath.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def print_completion_report(self, result: IngestResult) -> None:
        """Print a summary of the ingestion results."""
        total_batches = result.batches_completed + result.batches_failed
        success_rate = (
            result.batches_completed / total_batches * 100 if total_batches > 0 else 0
        )

        print("\n=== Ingestion Complete ===")
        print(f"Chunks embedded: {result.chunks_embedded}")
        print(f"Chunks stored:   {result.chunks_stored}")
        completed = result.batches_completed
        print(f"Batches:         {completed}/{total_batches} ({success_rate:.1f}%)")
        print(f"Duration:        {result.duration:.1f}s")

        if result.batches_failed > 0:
            failed = result.batches_failed
            n_failed = len(result.failed_chunks)
            print(f"\nWARNING: {failed} batches failed ({n_failed} chunks)")
            print("Re-run with --retry-failed to process failed chunks")


__all__ = ["IngestResult", "ParallelIngestor"]
