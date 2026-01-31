"""Contextual header builder for BBj documentation chunks.

Combines TOC breadcrumbs, page titles, and within-page heading paths
into arrow-separated context strings.  These headers are stored alongside
chunk content to provide hierarchy context for embeddings and vector search.

Also provides heading extraction from markdown content and a URL-path
hierarchy adapter for web crawl documents.
"""

from __future__ import annotations

import re

from bbj_rag.parsers.web_crawl import url_to_hierarchy


def build_context_header(
    section_path: str,
    title: str,
    heading_path: str = "",
) -> str:
    """Build an arrow-separated context header string.

    Combines ``section_path`` (TOC breadcrumb or directory fallback),
    ``title`` (page title), and optional ``heading_path`` (within-page
    section heading) into a single hierarchy string.

    Deduplicates ``title`` when it already appears at the end of
    ``section_path``.  Returns empty string when all inputs are empty.

    Args:
        section_path: Arrow-separated breadcrumb from TOC or directory
            (e.g. ``"Language > BBjAPI > BBjWindow"``).
        title: Page title (e.g. ``"addButton"``).
        heading_path: Optional within-page heading context for chunking
            (e.g. ``"Parameters"``).  Pass empty string when not applicable.

    Returns:
        Arrow-separated context string
        (e.g. ``"Language > BBjAPI > BBjWindow > addButton > Parameters"``).

    Examples:
        >>> build_context_header("Language > BBjAPI > BBjWindow", "addButton", "")
        'Language > BBjAPI > BBjWindow > addButton'
        >>> build_context_header("A > B > C", "C", "")
        'A > B > C'
        >>> build_context_header("", "MyPage", "")
        'MyPage'
    """
    sep = " > "
    parts: list[str] = []

    section_stripped = section_path.strip()
    title_stripped = title.strip()
    heading_stripped = heading_path.strip()

    if section_stripped:
        parts.append(section_stripped)

    # Deduplicate: skip title if section_path already ends with it
    if title_stripped:
        if not section_stripped or not section_stripped.endswith(title_stripped):
            parts.append(title_stripped)

    if heading_stripped:
        parts.append(heading_stripped)

    return sep.join(parts)


def extract_heading_hierarchy(content: str) -> list[str]:
    """Extract heading text from markdown content.

    Parses lines starting with ``# ``, ``## ``, ``### ``, etc. and
    returns a flat list of heading text strings.

    Args:
        content: Markdown content (as produced by parsers).

    Returns:
        List of heading text strings
        (e.g. ``["Description", "Syntax", "Parameters"]``).

    Examples:
        >>> extract_heading_hierarchy("## Description\\n\\nText\\n\\n## Syntax")
        ['Description', 'Syntax']
    """
    headings: list[str] = []
    for match in re.finditer(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE):
        text = match.group(2).strip()
        if text:
            headings.append(text)
    return headings


def url_path_to_hierarchy(url: str, base_url: str) -> str:
    """Derive an arrow-separated section path from a URL.

    Provides a single entry point in the intelligence package for
    web crawl hierarchy paths.  Delegates to
    :func:`bbj_rag.parsers.web_crawl.url_to_hierarchy`.

    Args:
        url: Full URL of the crawled page.
        base_url: Base URL of the documentation site.

    Returns:
        Arrow-separated section path (e.g. ``"bbjobjects > Window > bbjwindow"``).
        Returns empty string for the root URL.
    """
    return url_to_hierarchy(url, base_url)


__all__ = [
    "build_context_header",
    "extract_heading_hierarchy",
    "url_path_to_hierarchy",
]
