"""Tests for the PDF parser.

Unit tests mock pymupdf4llm calls to avoid requiring the actual PDF file.
Validates section splitting, generation tagging, doc_type classification,
source_url formatting, and protocol compliance.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from bbj_rag.parsers import DocumentParser
from bbj_rag.parsers.pdf import PdfParser

# ---------------------------------------------------------------------------
# Fixture markdown strings simulating pymupdf4llm output
# ---------------------------------------------------------------------------

MULTI_SECTION_MD = """\
# Section One

This is introductory content about GUI programming concepts.

## Section Two

Here is more detailed content about event handling and callbacks.

## Section Three With Code

Example code block:

```bbj
SYSGUI = UNT
OPEN (SYSGUI)"X0"
PROCESS_EVENTS
```

This demonstrates basic GUI setup.
"""

DWC_SECTION_MD = """\
## DWC Content Section

This section covers BBjHtmlView and setCss for styling web components.
"""

GUI_SECTION_MD = """\
## GUI Content Section

Use SYSGUI and PROCESS_EVENTS to manage the GUI event loop.
"""

APPBUILDER_SECTION_MD = """\
## Using AppBuilder

Step-by-step tutorial for building applications with Barista tools.
"""

EMPTY_SECTION_MD = """\
## Section With Content

Real content here.

## Empty Section

"""

# Combine TOC page (page 0, should be skipped) + content pages
TOC_PAGE_MD = """\
# Table of Contents

- Section One
- Section Two
"""


def _make_page_chunks(*pages: str) -> list[dict[str, object]]:
    """Build a list of page chunk dicts as pymupdf4llm.to_markdown returns."""
    return [{"text": page} for page in pages]


# ---------------------------------------------------------------------------
# Protocol compliance
# ---------------------------------------------------------------------------


class TestPdfParserProtocol:
    def test_pdf_parser_implements_protocol(self):
        parser = PdfParser(Path("dummy.pdf"))
        assert isinstance(parser, DocumentParser)


# ---------------------------------------------------------------------------
# Section splitting
# ---------------------------------------------------------------------------


class TestPdfParserSplitting:
    @patch("bbj_rag.parsers.pdf.pymupdf4llm")
    @patch("bbj_rag.parsers.pdf.pymupdf")
    def test_pdf_parser_yields_documents(self, mock_pymupdf, mock_pymupdf4llm):
        mock_pymupdf.open.return_value = MagicMock()
        mock_pymupdf4llm.TocHeaders.return_value = None
        mock_pymupdf4llm.to_markdown.return_value = _make_page_chunks(
            TOC_PAGE_MD,  # page 0 -- skipped
            MULTI_SECTION_MD,
        )

        parser = PdfParser(Path("test.pdf"))
        docs = list(parser.parse())

        assert len(docs) > 0
        for doc in docs:
            assert doc.content.strip()

    @patch("bbj_rag.parsers.pdf.pymupdf4llm")
    @patch("bbj_rag.parsers.pdf.pymupdf")
    def test_pdf_parser_splits_at_headings(self, mock_pymupdf, mock_pymupdf4llm):
        mock_pymupdf.open.return_value = MagicMock()
        mock_pymupdf4llm.TocHeaders.return_value = None
        mock_pymupdf4llm.to_markdown.return_value = _make_page_chunks(
            TOC_PAGE_MD,
            MULTI_SECTION_MD,
        )

        parser = PdfParser(Path("test.pdf"))
        docs = list(parser.parse())

        # MULTI_SECTION_MD has 3 sections (Section One, Two, Three With Code)
        assert len(docs) == 3

    @patch("bbj_rag.parsers.pdf.pymupdf4llm")
    @patch("bbj_rag.parsers.pdf.pymupdf")
    def test_pdf_parser_skips_empty_sections(self, mock_pymupdf, mock_pymupdf4llm):
        mock_pymupdf.open.return_value = MagicMock()
        mock_pymupdf4llm.TocHeaders.return_value = None
        mock_pymupdf4llm.to_markdown.return_value = _make_page_chunks(
            TOC_PAGE_MD,
            EMPTY_SECTION_MD,
        )

        parser = PdfParser(Path("test.pdf"))
        docs = list(parser.parse())

        # Only "Section With Content" should yield; "Empty Section" has no body
        titles = [d.title for d in docs]
        assert "Section With Content" in titles
        assert "Empty Section" not in titles


# ---------------------------------------------------------------------------
# Source URL formatting
# ---------------------------------------------------------------------------


class TestPdfParserSourceUrl:
    @patch("bbj_rag.parsers.pdf.pymupdf4llm")
    @patch("bbj_rag.parsers.pdf.pymupdf")
    def test_pdf_parser_sets_source_url(self, mock_pymupdf, mock_pymupdf4llm):
        mock_pymupdf.open.return_value = MagicMock()
        mock_pymupdf4llm.TocHeaders.return_value = None
        mock_pymupdf4llm.to_markdown.return_value = _make_page_chunks(
            TOC_PAGE_MD,
            MULTI_SECTION_MD,
        )

        parser = PdfParser(Path("GuideToGuiProgrammingInBBj.pdf"))
        docs = list(parser.parse())

        for doc in docs:
            assert doc.source_url.startswith("pdf://GuideToGuiProgrammingInBBj.pdf#")

        # Check specific slug
        section_one = next(d for d in docs if d.title == "Section One")
        assert section_one.source_url == (
            "pdf://GuideToGuiProgrammingInBBj.pdf#section-one"
        )


# ---------------------------------------------------------------------------
# Context header
# ---------------------------------------------------------------------------


class TestPdfParserContextHeader:
    @patch("bbj_rag.parsers.pdf.pymupdf4llm")
    @patch("bbj_rag.parsers.pdf.pymupdf")
    def test_pdf_parser_sets_context_header(self, mock_pymupdf, mock_pymupdf4llm):
        mock_pymupdf.open.return_value = MagicMock()
        mock_pymupdf4llm.TocHeaders.return_value = None
        mock_pymupdf4llm.to_markdown.return_value = _make_page_chunks(
            TOC_PAGE_MD,
            MULTI_SECTION_MD,
        )

        parser = PdfParser(Path("test.pdf"))
        docs = list(parser.parse())

        section_one = next(d for d in docs if d.title == "Section One")
        assert section_one.context_header == "Guide to GUI Programming > Section One"


# ---------------------------------------------------------------------------
# Doc type classification
# ---------------------------------------------------------------------------


class TestPdfParserDocType:
    @patch("bbj_rag.parsers.pdf.pymupdf4llm")
    @patch("bbj_rag.parsers.pdf.pymupdf")
    def test_pdf_parser_detects_code_sections(self, mock_pymupdf, mock_pymupdf4llm):
        mock_pymupdf.open.return_value = MagicMock()
        mock_pymupdf4llm.TocHeaders.return_value = None
        mock_pymupdf4llm.to_markdown.return_value = _make_page_chunks(
            TOC_PAGE_MD,
            MULTI_SECTION_MD,
        )

        parser = PdfParser(Path("test.pdf"))
        docs = list(parser.parse())

        # Section One and Two have no code blocks -> concept
        concept_docs = [d for d in docs if "Code" not in d.title]
        for doc in concept_docs:
            assert doc.doc_type == "concept"

        # Section Three With Code has a code block -> example
        code_docs = [d for d in docs if "Code" in d.title]
        assert len(code_docs) == 1
        assert code_docs[0].doc_type == "example"

    @patch("bbj_rag.parsers.pdf.pymupdf4llm")
    @patch("bbj_rag.parsers.pdf.pymupdf")
    def test_pdf_parser_detects_tutorial_sections(self, mock_pymupdf, mock_pymupdf4llm):
        mock_pymupdf.open.return_value = MagicMock()
        mock_pymupdf4llm.TocHeaders.return_value = None
        mock_pymupdf4llm.to_markdown.return_value = _make_page_chunks(
            TOC_PAGE_MD,
            APPBUILDER_SECTION_MD,
        )

        parser = PdfParser(Path("test.pdf"))
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].doc_type == "tutorial"


# ---------------------------------------------------------------------------
# Generation tagging
# ---------------------------------------------------------------------------


class TestPdfParserGeneration:
    @patch("bbj_rag.parsers.pdf.pymupdf4llm")
    @patch("bbj_rag.parsers.pdf.pymupdf")
    def test_pdf_parser_generation_tagging(self, mock_pymupdf, mock_pymupdf4llm):
        """Test per-section generation tagging."""
        combined_md = DWC_SECTION_MD + "\n" + GUI_SECTION_MD
        mock_pymupdf.open.return_value = MagicMock()
        mock_pymupdf4llm.TocHeaders.return_value = None
        mock_pymupdf4llm.to_markdown.return_value = _make_page_chunks(
            TOC_PAGE_MD,
            combined_md,
        )

        parser = PdfParser(Path("test.pdf"))
        docs = list(parser.parse())

        assert len(docs) == 2

        dwc_doc = next(d for d in docs if "DWC" in d.title)
        assert dwc_doc.generations == ["dwc"]

        gui_doc = next(d for d in docs if "GUI" in d.title)
        assert gui_doc.generations == ["bbj_gui"]

    @patch("bbj_rag.parsers.pdf.pymupdf4llm")
    @patch("bbj_rag.parsers.pdf.pymupdf")
    def test_pdf_parser_generation_all_for_generic(
        self, mock_pymupdf, mock_pymupdf4llm
    ):
        """Sections without DWC/GUI/character patterns get ['all']."""
        generic_md = """\
## General Programming

This section covers basic data types and string handling.
"""
        mock_pymupdf.open.return_value = MagicMock()
        mock_pymupdf4llm.TocHeaders.return_value = None
        mock_pymupdf4llm.to_markdown.return_value = _make_page_chunks(
            TOC_PAGE_MD,
            generic_md,
        )

        parser = PdfParser(Path("test.pdf"))
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].generations == ["all"]


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class TestPdfParserMetadata:
    @patch("bbj_rag.parsers.pdf.pymupdf4llm")
    @patch("bbj_rag.parsers.pdf.pymupdf")
    def test_pdf_parser_metadata(self, mock_pymupdf, mock_pymupdf4llm):
        mock_pymupdf.open.return_value = MagicMock()
        mock_pymupdf4llm.TocHeaders.return_value = None
        mock_pymupdf4llm.to_markdown.return_value = _make_page_chunks(
            TOC_PAGE_MD,
            MULTI_SECTION_MD,
        )

        parser = PdfParser(Path("my-guide.pdf"))
        docs = list(parser.parse())

        for doc in docs:
            assert doc.metadata["source"] == "pdf"
            assert doc.metadata["pdf_file"] == "my-guide.pdf"
            assert doc.deprecated is False
