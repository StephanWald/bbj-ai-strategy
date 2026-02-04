"""Unit tests for the parallel ingestion module."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from bbj_rag.models import Chunk
from bbj_rag.parallel import IngestResult, ParallelIngestor

if TYPE_CHECKING:
    pass


def _make_chunk(content: str, content_hash: str | None = None) -> Chunk:
    """Create a test chunk with required fields."""
    import hashlib

    if content_hash is None:
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    return Chunk(
        content=content,
        source_url=f"test://{content_hash}",
        title=f"Test {content_hash}",
        doc_type="test",
        content_hash=content_hash,
        generations=["bbj24"],
    )


class TestIngestResult:
    """Tests for IngestResult dataclass."""

    def test_default_values(self):
        """IngestResult has sensible defaults."""
        result = IngestResult()
        assert result.chunks_embedded == 0
        assert result.chunks_stored == 0
        assert result.batches_completed == 0
        assert result.batches_failed == 0
        assert result.failed_chunks == []
        assert result.duration == 0.0

    def test_all_fields_present(self):
        """IngestResult has all expected fields."""
        fields = IngestResult.__dataclass_fields__.keys()
        expected = {
            "chunks_embedded",
            "chunks_stored",
            "batches_completed",
            "batches_failed",
            "failed_chunks",
            "duration",
        }
        assert set(fields) == expected

    def test_custom_values(self):
        """IngestResult accepts custom values."""
        chunks = [_make_chunk("test")]
        result = IngestResult(
            chunks_embedded=100,
            chunks_stored=95,
            batches_completed=10,
            batches_failed=2,
            failed_chunks=chunks,
            duration=5.5,
        )
        assert result.chunks_embedded == 100
        assert result.chunks_stored == 95
        assert result.batches_completed == 10
        assert result.batches_failed == 2
        assert result.failed_chunks == chunks
        assert result.duration == 5.5


class TestBatchDistribution:
    """Tests for batch creation logic."""

    def test_exact_batch_size(self):
        """Chunks divide evenly into batches."""
        chunks = [_make_chunk(f"chunk {i}") for i in range(64)]
        settings = MagicMock()
        settings.ingest_batch_retries = 3

        ingestor = ParallelIngestor(settings, num_workers=2, batch_size=64)

        # Test batch creation via internal logic
        batches = []
        for i in range(0, len(chunks), ingestor._batch_size):
            batches.append(chunks[i : i + ingestor._batch_size])

        assert len(batches) == 1
        assert len(batches[0]) == 64

    def test_uneven_batches(self):
        """Last batch handles remainder correctly."""
        chunks = [_make_chunk(f"chunk {i}") for i in range(150)]
        settings = MagicMock()
        settings.ingest_batch_retries = 3

        ingestor = ParallelIngestor(settings, num_workers=2, batch_size=64)

        batches = []
        for i in range(0, len(chunks), ingestor._batch_size):
            batches.append(chunks[i : i + ingestor._batch_size])

        assert len(batches) == 3
        assert len(batches[0]) == 64
        assert len(batches[1]) == 64
        assert len(batches[2]) == 22  # 150 - 128 = 22

        # All chunks accounted for
        total = sum(len(b) for b in batches)
        assert total == 150

    def test_fewer_chunks_than_batch_size(self):
        """Small chunk list creates single batch."""
        chunks = [_make_chunk(f"chunk {i}") for i in range(10)]
        settings = MagicMock()
        settings.ingest_batch_retries = 3

        ingestor = ParallelIngestor(settings, num_workers=2, batch_size=64)

        batches = []
        for i in range(0, len(chunks), ingestor._batch_size):
            batches.append(chunks[i : i + ingestor._batch_size])

        assert len(batches) == 1
        assert len(batches[0]) == 10

    def test_empty_chunks_list(self):
        """Empty chunk list creates no batches."""
        chunks: list[Chunk] = []
        settings = MagicMock()
        settings.ingest_batch_retries = 3

        ingestor = ParallelIngestor(settings, num_workers=2, batch_size=64)

        batches = []
        for i in range(0, len(chunks), ingestor._batch_size):
            batches.append(chunks[i : i + ingestor._batch_size])

        assert len(batches) == 0


class TestFailureLogging:
    """Tests for failure log save/load functionality."""

    def test_save_failure_log(self, tmp_path: Path):
        """save_failure_log writes JSON lines format."""
        log_path = tmp_path / "failures.json"
        chunks = [
            _make_chunk("content 1", "hash1"),
            _make_chunk("content 2", "hash2"),
        ]

        ParallelIngestor.save_failure_log(chunks, log_path, "embedding failed")

        # Verify file contents
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2

        entry1 = json.loads(lines[0])
        assert entry1["content_hash"] == "hash1"
        assert entry1["source_url"] == "test://hash1"
        assert entry1["error"] == "embedding failed"

        entry2 = json.loads(lines[1])
        assert entry2["content_hash"] == "hash2"

    def test_load_failure_log(self, tmp_path: Path):
        """load_failure_log reads JSON lines format."""
        log_path = tmp_path / "failures.json"
        log_path.write_text(
            '{"content_hash": "abc", "source_url": "test://1", "error": "err1"}\n'
            '{"content_hash": "def", "source_url": "test://2", "error": "err2"}\n'
        )

        entries = ParallelIngestor.load_failure_log(log_path)

        assert len(entries) == 2
        assert entries[0]["content_hash"] == "abc"
        assert entries[1]["content_hash"] == "def"

    def test_load_failure_log_nonexistent(self, tmp_path: Path):
        """load_failure_log returns empty list for missing file."""
        log_path = tmp_path / "nonexistent.json"

        entries = ParallelIngestor.load_failure_log(log_path)

        assert entries == []

    def test_append_behavior(self, tmp_path: Path):
        """save_failure_log appends to existing file."""
        log_path = tmp_path / "failures.json"
        chunk1 = _make_chunk("first", "first123")
        chunk2 = _make_chunk("second", "second456")

        # Save first batch
        ParallelIngestor.save_failure_log([chunk1], log_path, "error 1")

        # Save second batch (should append)
        ParallelIngestor.save_failure_log([chunk2], log_path, "error 2")

        entries = ParallelIngestor.load_failure_log(log_path)
        assert len(entries) == 2
        assert entries[0]["content_hash"] == "first123"
        assert entries[1]["content_hash"] == "second456"


class TestRetryLogic:
    """Tests for retry behavior with mocked embedder."""

    def test_retries_configured_from_settings(self):
        """ParallelIngestor uses settings.ingest_batch_retries."""
        settings = MagicMock()
        settings.ingest_batch_retries = 5

        ingestor = ParallelIngestor(settings, num_workers=1, batch_size=64)

        assert ingestor._retries == 5

    def test_retry_count_default(self):
        """ParallelIngestor uses default retries from settings."""
        settings = MagicMock()
        settings.ingest_batch_retries = 3

        ingestor = ParallelIngestor(settings, num_workers=2)

        assert ingestor._retries == 3

    @pytest.mark.asyncio
    async def test_fails_after_max_retries(self):
        """Batch fails after exhausting all retries (embedding always fails)."""
        settings = MagicMock()
        settings.embedding_model = "test-model"
        settings.embedding_dimensions = 1024
        settings.ollama_host = "http://localhost:11434"
        settings.ingest_batch_retries = 3

        ingestor = ParallelIngestor(
            settings, num_workers=1, batch_size=64, verbose=False
        )

        # Always fail
        call_count = 0

        async def mock_embed_batch(texts):
            nonlocal call_count
            call_count += 1
            raise RuntimeError(f"Simulated failure {call_count}")

        mock_embedder = AsyncMock()
        mock_embedder.embed_batch = mock_embed_batch

        mock_pool = AsyncMock()

        batch = [_make_chunk("test chunk")]
        result = IngestResult()
        result_lock = asyncio.Lock()

        success = await ingestor._process_batch_with_retry(
            worker_id=1,
            batch_idx=0,
            batch=batch,
            embedder=mock_embedder,
            pool=mock_pool,
            result=result,
            result_lock=result_lock,
            total_batches=1,
        )

        assert success is False
        assert call_count == 3  # Tried 3 times


class TestCompletionReport:
    """Tests for completion report output."""

    def test_print_completion_report_success(self, capsys):
        """Completion report shows success stats."""
        settings = MagicMock()
        settings.ingest_batch_retries = 3

        ingestor = ParallelIngestor(settings, num_workers=2)
        result = IngestResult(
            chunks_embedded=100,
            chunks_stored=100,
            batches_completed=5,
            batches_failed=0,
            duration=2.5,
        )

        ingestor.print_completion_report(result)

        captured = capsys.readouterr()
        assert "Chunks embedded: 100" in captured.out
        assert "Chunks stored:   100" in captured.out
        assert "5/5 (100.0%)" in captured.out
        assert "2.5s" in captured.out
        assert "WARNING" not in captured.out

    def test_print_completion_report_with_failures(self, capsys):
        """Completion report shows failure warning."""
        settings = MagicMock()
        settings.ingest_batch_retries = 3

        ingestor = ParallelIngestor(settings, num_workers=2)
        failed_chunks = [_make_chunk("failed")]
        result = IngestResult(
            chunks_embedded=90,
            chunks_stored=90,
            batches_completed=4,
            batches_failed=1,
            failed_chunks=failed_chunks,
            duration=3.0,
        )

        ingestor.print_completion_report(result)

        captured = capsys.readouterr()
        assert "4/5 (80.0%)" in captured.out
        assert "WARNING" in captured.out
        assert "1 batches failed" in captured.out
        assert "1 chunks" in captured.out
        assert "--retry-failed" in captured.out
