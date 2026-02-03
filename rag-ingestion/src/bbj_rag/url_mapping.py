"""URL mapping utilities for source classification and display URL generation.

Classifies source URLs into semantic source types and maps them to
user-facing display URLs suitable for clickable links in search results.
"""

from __future__ import annotations

__all__ = ["classify_source_type", "map_display_url"]

# Ordered list of (prefix, source_type) pairs. Checked in order so more
# specific prefixes (e.g. https://basis.cloud/advantage) match before
# broader ones (e.g. https://documentation.basis.cloud/).
_SOURCE_TYPE_RULES: list[tuple[str, str]] = [
    ("flare://", "flare"),
    ("pdf://", "pdf"),
    ("file://", "bbj_source"),
    ("mdx-dwc://", "mdx"),
    ("mdx-beginner://", "mdx"),
    ("mdx-db-modernization://", "mdx"),
    ("https://basis.cloud/advantage", "wordpress"),
    ("https://basis.cloud/knowledge-base", "wordpress"),
    ("https://documentation.basis.cloud/", "web_crawl"),
]

_FLARE_CONTENT_PREFIX = "flare://Content/"
_FLARE_DISPLAY_BASE = "https://documentation.basis.cloud/BASISHelp/WebHelp/"


def classify_source_type(source_url: str) -> str:
    """Return a semantic source-type label for the given source URL.

    Checks the URL prefix against known source patterns and returns a
    short label: ``flare``, ``pdf``, ``bbj_source``, ``mdx``,
    ``wordpress``, ``web_crawl``, or ``unknown``.
    """
    for prefix, label in _SOURCE_TYPE_RULES:
        if source_url.startswith(prefix):
            return label
    return "unknown"


def map_display_url(source_url: str) -> str:
    """Return a user-facing display URL for the given source URL.

    - Flare ``flare://Content/...`` URLs are mapped to their public
      ``https://documentation.basis.cloud/BASISHelp/WebHelp/...``
      equivalent.
    - ``https://`` URLs (WordPress, web crawl) are passed through as-is.
    - All other schemes (``pdf://``, ``file://``, ``mdx-*://``) are
      returned wrapped in brackets as a non-clickable fallback.
    """
    if source_url.startswith(_FLARE_CONTENT_PREFIX):
        return _FLARE_DISPLAY_BASE + source_url[len(_FLARE_CONTENT_PREFIX) :]

    if source_url.startswith("https://"):
        return source_url

    return f"[{source_url}]"
