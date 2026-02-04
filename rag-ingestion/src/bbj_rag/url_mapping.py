"""URL mapping utilities for source classification and display URL generation.

Classifies source URLs into semantic source types and maps them to
user-facing display URLs suitable for clickable links in search results.
"""

from __future__ import annotations

import re

__all__ = ["classify_source_type", "map_display_url"]

# Ordered list of (prefix, source_type) pairs. Checked in order so more
# specific prefixes (e.g. https://basis.cloud/advantage) match before
# broader ones (e.g. https://documentation.basis.cloud/).
# Labels are user-facing display names shown in the chat UI.
_SOURCE_TYPE_RULES: list[tuple[str, str]] = [
    ("flare://", "BASIS BBj Documentation"),
    ("pdf://", "PDF Manual"),
    ("file://", "BBj Source Code"),
    ("mdx-dwc://", "DWC Tutorial"),
    ("mdx-beginner://", "BBj Beginner Tutorial"),
    ("mdx-db-modernization://", "DB Modernization Guide"),
    ("https://basis.cloud/advantage", "BASIS Advantage Blog"),
    ("https://basis.cloud/knowledge-base", "BASIS Knowledge Base"),
    ("https://documentation.basis.cloud/", "BASIS BBj Documentation"),
]

_FLARE_CONTENT_PREFIX = "flare://Content/"
_FLARE_DISPLAY_BASE = "https://documentation.basis.cloud/BASISHelp/WebHelp/"

# MDX tutorial URL mappings
_MDX_DWC_PREFIX = "mdx-dwc://"
_MDX_DWC_BASE = "https://basishub.github.io/DWC-Course/"

_MDX_BEGINNER_PREFIX = "mdx-beginner://"
_MDX_BEGINNER_BASE = "https://basishub.github.io/BBj-Beginner-Tutorial/"

_MDX_DB_MOD_PREFIX = "mdx-db-modernization://"
_MDX_DB_MOD_BASE = "https://basishub.github.io/Database-Modernization-Tutorial/"


def classify_source_type(source_url: str) -> str:
    """Return a semantic source-type label for the given source URL.

    Checks the URL prefix against known source patterns and returns a
    user-friendly label like "BASIS BBj Documentation", "DWC Tutorial",
    "PDF Manual", etc.
    """
    for prefix, label in _SOURCE_TYPE_RULES:
        if source_url.startswith(prefix):
            return label
    return "Documentation"


def _mdx_path_to_slug(path: str) -> str:
    """Convert MDX internal path to URL slug.

    Example: "01-gui-to-bui-to-dwc/03-gui-to-bui-to-dwc.md" -> "gui-to-bui-to-dwc"

    The MDX paths use numbered prefixes for ordering (01-, 02-, etc.) which
    are stripped in the published URL. The .md extension is also removed.
    """
    # Take the last path component (the actual page)
    parts = path.rstrip("/").split("/")
    slug = parts[-1] if parts else path

    # Remove .md extension
    if slug.endswith(".md"):
        slug = slug[:-3]

    # Remove leading number prefix (e.g., "03-" from "03-gui-to-bui-to-dwc")
    slug = re.sub(r"^\d+-", "", slug)

    return slug


def map_display_url(source_url: str) -> str:
    """Return a user-facing display URL for the given source URL.

    - Flare ``flare://Content/...`` URLs are mapped to their public
      ``https://documentation.basis.cloud/BASISHelp/WebHelp/...``
      equivalent.
    - MDX tutorial URLs are mapped to their GitHub Pages equivalents.
    - ``https://`` URLs (WordPress, web crawl) are passed through as-is.
    - PDF and file:// URLs return empty string (no web equivalent).
    """
    if source_url.startswith(_FLARE_CONTENT_PREFIX):
        return _FLARE_DISPLAY_BASE + source_url[len(_FLARE_CONTENT_PREFIX) :]

    if source_url.startswith(_MDX_DWC_PREFIX):
        path = source_url[len(_MDX_DWC_PREFIX) :]
        slug = _mdx_path_to_slug(path)
        return _MDX_DWC_BASE + slug

    if source_url.startswith(_MDX_BEGINNER_PREFIX):
        path = source_url[len(_MDX_BEGINNER_PREFIX) :]
        slug = _mdx_path_to_slug(path)
        return _MDX_BEGINNER_BASE + slug

    if source_url.startswith(_MDX_DB_MOD_PREFIX):
        path = source_url[len(_MDX_DB_MOD_PREFIX) :]
        slug = _mdx_path_to_slug(path)
        return _MDX_DB_MOD_BASE + slug

    if source_url.startswith("https://"):
        return source_url

    # PDF and file:// have no web equivalent - return empty
    # (chat fallback will use source_url for display)
    return ""
