"""Parser package for the RAG ingestion pipeline.

Defines the DocumentParser protocol and shared constants for all parsers
(Flare XHTML, web crawl, etc.).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from bbj_rag.models import Document

MADCAP_NS = "http://www.madcapsoftware.com/Schemas/MadCap.xsd"
"""MadCap Flare XML namespace URI used on all custom elements and attributes."""


@runtime_checkable
class DocumentParser(Protocol):
    """Contract for all documentation source parsers.

    Every parser must implement ``parse()`` yielding validated
    ``Document`` objects. Parsers are expected to handle their own
    I/O (file reads, HTTP requests) internally.
    """

    def parse(self) -> Iterator[Document]:
        """Yield Document objects from the configured source."""
        ...


__all__ = ["MADCAP_NS", "DocumentParser"]
