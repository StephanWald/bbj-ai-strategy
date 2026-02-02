"""PDF parser for the RAG ingestion pipeline.

Extracts section-level ``Document`` objects from a PDF file using
pymupdf4llm for Markdown conversion.  Each major heading boundary
(``#`` / ``##``) produces a separate Document with per-section
generation tagging.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path

import pymupdf  # type: ignore[import-untyped]
import pymupdf4llm  # type: ignore[import-untyped]

from bbj_rag.models import Document

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Generation tagging patterns (PDF-specific, content-based)
# ---------------------------------------------------------------------------

_DWC_CONTENT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"BBjHtmlView", re.IGNORECASE),
    re.compile(r"setCss|addStyle|getStyle", re.IGNORECASE),
    re.compile(r"webManager|getWebManager"),
    re.compile(r"BBjWebComponent"),
]

_GUI_CONTENT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"SYSGUI"),
    re.compile(r"BBjAPI\(\)"),
    re.compile(r"getSysGui"),
    re.compile(r"PROCESS_EVENTS"),
    re.compile(r"addWindow|addButton|addEditBox"),
    re.compile(r"setCallback"),
    re.compile(r"BBjTopLevelWindow"),
]

_CHARACTER_CONTENT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"character\s*mode", re.IGNORECASE),
    re.compile(r"green.screen", re.IGNORECASE),
    re.compile(r"terminal\s*emulat", re.IGNORECASE),
]

# Sections matching these patterns get doc_type="tutorial"
_TUTORIAL_TITLE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"AppBuilder", re.IGNORECASE),
    re.compile(r"Barista", re.IGNORECASE),
]


def _classify_generation(content: str) -> list[str]:
    """Classify a PDF section by generation based on content patterns."""
    if any(p.search(content) for p in _DWC_CONTENT_PATTERNS):
        return ["dwc"]
    if any(p.search(content) for p in _GUI_CONTENT_PATTERNS):
        return ["bbj_gui"]
    if any(p.search(content) for p in _CHARACTER_CONTENT_PATTERNS):
        return ["character"]
    return ["all"]


def _classify_doc_type(title: str, content: str) -> str:
    """Classify a PDF section's doc_type."""
    if any(p.search(title) for p in _TUTORIAL_TITLE_PATTERNS):
        return "tutorial"
    if "```" in content:
        return "example"
    return "concept"


def _strip_bold(text: str) -> str:
    """Remove markdown bold markers (``**...**``) from heading text."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text).strip()


def _slugify(text: str) -> str:
    """Convert heading text to a URL-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


# ---------------------------------------------------------------------------
# Section splitter
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


def _split_sections(markdown: str) -> list[tuple[str, str]]:
    """Split concatenated markdown at heading boundaries.

    Returns a list of ``(heading_text, section_body)`` tuples.
    Sections with only whitespace content are excluded.
    """
    matches = list(_HEADING_RE.finditer(markdown))
    if not matches:
        return []

    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        heading_text = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        if body:
            sections.append((heading_text, body))

    return sections


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class PdfParser:
    """Parse a PDF file into section-level ``Document`` objects.

    Uses *pymupdf4llm* for Markdown conversion and splits at heading
    boundaries so that each Document represents a logical section.

    Implements the ``DocumentParser`` protocol.

    Args:
        pdf_path: Path to the PDF file.
    """

    def __init__(self, pdf_path: Path) -> None:
        self._pdf_path = pdf_path

    def parse(self) -> Iterator[Document]:
        """Yield one ``Document`` per heading-delimited section."""
        pdf_filename = self._pdf_path.name

        doc = pymupdf.open(str(self._pdf_path))

        # Convert to a single markdown string (not page_chunks).
        # page_chunks=True suppresses heading detection in pymupdf4llm,
        # producing bold text instead of # headings.  A single-string
        # conversion preserves heading markers that _split_sections needs.
        full_markdown: str = pymupdf4llm.to_markdown(doc, write_images=False)

        # Split at heading boundaries
        sections = _split_sections(full_markdown)

        # Fallback: if no heading-delimited sections were found, treat the
        # entire document as a single section so content is never silently
        # dropped.
        if not sections:
            logger.warning(
                "PDF %s: no heading sections found, using full text as single doc",
                pdf_filename,
            )
            sections = [(pdf_filename.replace(".pdf", ""), full_markdown)]

        logger.info(
            "PDF %s: extracted %d sections from %d pages",
            pdf_filename,
            len(sections),
            len(doc),
        )

        for heading, body in sections:
            heading = _strip_bold(heading)
            slug = _slugify(heading)
            generations = _classify_generation(body)
            doc_type = _classify_doc_type(heading, body)

            yield Document(
                source_url=f"pdf://{pdf_filename}#{slug}",
                title=heading,
                doc_type=doc_type,
                content=body,
                generations=generations,
                context_header=f"Guide to GUI Programming > {heading}",
                metadata={"source": "pdf", "pdf_file": pdf_filename},
                deprecated=False,
            )


__all__ = ["PdfParser"]
