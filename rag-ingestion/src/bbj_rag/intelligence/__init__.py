"""BBj Intelligence: document classification and contextual enrichment.

Public API for the intelligence package. This module re-exports the
primary types and functions used by the ingestion pipeline.
"""

from bbj_rag.intelligence.context_headers import (
    build_context_header,
    extract_heading_hierarchy,
)
from bbj_rag.intelligence.doc_types import DocType, classify_doc_type
from bbj_rag.intelligence.generations import Generation, tag_generation
from bbj_rag.intelligence.report import build_report, print_quality_report, print_report

__all__ = [
    "DocType",
    "Generation",
    "build_context_header",
    "build_report",
    "classify_doc_type",
    "extract_heading_hierarchy",
    "print_quality_report",
    "print_report",
    "tag_generation",
]
