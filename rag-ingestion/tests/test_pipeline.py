"""Tests for the pipeline intelligence bypass logic.

Verifies that pre-populated Documents (from non-Flare parsers) skip
the Flare intelligence enrichment, while Flare and web crawl
Documents still go through it.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

from bbj_rag.models import Document
from bbj_rag.pipeline import run_pipeline

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _StubParser:
    """Yields a fixed list of Documents."""

    def __init__(self, docs: list[Document]) -> None:
        self._docs = docs

    def parse(self) -> Iterator[Document]:
        yield from self._docs


def _make_doc(
    *,
    doc_type: str = "",
    generations: list[str] | None = None,
    source_url: str = "test://doc",
    content: str = "Test content for pipeline.",
) -> Document:
    return Document(
        source_url=source_url,
        title="Test Doc",
        doc_type=doc_type,
        content=content,
        generations=generations or ["all"],
        context_header="Test > Doc",
        deprecated=False,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPipelineIntelligenceBypass:
    @patch("bbj_rag.pipeline._embed_and_store", return_value=1)
    @patch("bbj_rag.pipeline._apply_intelligence")
    def test_pipeline_skips_intelligence_for_prepopulated_docs(
        self, mock_intel: MagicMock, mock_store: MagicMock
    ):
        """Documents with pre-populated doc_type skip _apply_intelligence."""
        doc = _make_doc(
            doc_type="example",
            generations=["dwc"],
            source_url="file://sample.bbj",
        )
        parser = _StubParser([doc])
        embedder = MagicMock()
        conn = MagicMock()

        run_pipeline(parser, embedder, conn, batch_size=100)

        mock_intel.assert_not_called()

    @patch("bbj_rag.pipeline._embed_and_store", return_value=1)
    @patch(
        "bbj_rag.pipeline._apply_intelligence",
        return_value=(["bbj"], False, "reference", "BBj > Doc"),
    )
    def test_pipeline_applies_intelligence_for_flare_docs(
        self, mock_intel: MagicMock, mock_store: MagicMock
    ):
        """Flare Documents (doc_type='') go through _apply_intelligence."""
        doc = _make_doc(
            doc_type="",
            source_url="flare://Content/test.htm",
        )
        parser = _StubParser([doc])
        embedder = MagicMock()
        conn = MagicMock()

        run_pipeline(parser, embedder, conn, batch_size=100)

        mock_intel.assert_called_once()

    @patch("bbj_rag.pipeline._embed_and_store", return_value=1)
    @patch(
        "bbj_rag.pipeline._apply_intelligence",
        return_value=(["bbj"], False, "web_crawl", "Web > Page"),
    )
    def test_pipeline_applies_intelligence_for_web_crawl_docs(
        self, mock_intel: MagicMock, mock_store: MagicMock
    ):
        """Web crawl Documents (doc_type='web_crawl') go through _apply_intelligence."""
        doc = _make_doc(
            doc_type="web_crawl",
            source_url="https://example.com/page",
        )
        parser = _StubParser([doc])
        embedder = MagicMock()
        conn = MagicMock()

        run_pipeline(parser, embedder, conn, batch_size=100)

        mock_intel.assert_called_once()
