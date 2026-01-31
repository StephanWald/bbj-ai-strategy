"""TOC index builder for MadCap Flare .fltoc files.

Parses all four .fltoc files in priority order, building a flat lookup
from Content-relative topic paths to arrow-separated breadcrumb strings.
Topics not found in any TOC get a directory-based fallback path.
"""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)

# TOC files parsed in priority order: first-found wins for duplicate topics.
TOC_PRIORITY = [
    "basishelp.fltoc",
    "emhelp.fltoc",
    "bdthelp.fltoc",
    "pro5toc.fltoc",
]

LINKED_TITLE_PATTERN = "[%=System.LinkedTitle%]"


def build_toc_index(
    toc_dir: Path,
    content_dir: Path | None = None,
) -> dict[str, str]:
    """Build a path-to-breadcrumb index from all .fltoc files.

    Args:
        toc_dir: Directory containing the .fltoc files
            (e.g., ``/Users/beff/bbjdocs/Project/TOCs/``).
        content_dir: Optional Content directory for resolving
            ``[%=System.LinkedTitle%]`` entries from topic ``<title>`` tags.

    Returns:
        Mapping of Content-relative paths (e.g.,
        ``"bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm"``)
        to arrow-separated breadcrumb strings (e.g.,
        ``"Language > BBj Objects > BBjWindow > Methods of BBjWindow"``).
    """
    index: dict[str, str] = {}

    for toc_name in TOC_PRIORITY:
        toc_path = toc_dir / toc_name
        if not toc_path.exists():
            logger.debug("TOC file not found, skipping: %s", toc_path)
            continue

        parser = etree.XMLParser(remove_comments=True)
        tree = etree.parse(str(toc_path), parser)
        root = tree.getroot()
        _walk_toc(root, [], index, content_dir)

    logger.info("TOC index built: %d entries from %s", len(index), toc_dir)
    return index


def directory_fallback_path(content_relative_path: str) -> str:
    """Derive an arrow-separated hierarchy path from a file's directory.

    Used for orphan topics not present in any TOC file.

    Args:
        content_relative_path: Path relative to the Content directory,
            e.g., ``"bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm"``.

    Returns:
        Arrow-separated directory path, e.g.,
        ``"bbjobjects > Window > bbjwindow"``.
        Returns an empty string if the file is at the Content root.
    """
    parts = Path(content_relative_path).parent.parts
    if not parts or parts == (".",):
        return ""
    return " > ".join(parts)


def _resolve_linked_title(
    link_path: str,
    content_dir: Path,
) -> str:
    """Resolve a topic's title from its ``<head><title>`` element.

    Args:
        link_path: Content-relative path to the topic file.
        content_dir: Root Content directory.

    Returns:
        The resolved title string, or the filename stem as fallback.
    """
    topic_path = content_dir / link_path
    if not topic_path.exists():
        return Path(link_path).stem.replace("_", " ")

    try:
        parser = etree.XMLParser(remove_comments=True)
        tree = etree.parse(str(topic_path), parser)
        root = tree.getroot()
        title_elem = root.find(".//head/title")
        if title_elem is not None and title_elem.text and title_elem.text.strip():
            return title_elem.text.strip()
        # Fallback: first <h1> text
        h1 = root.find(".//body//h1")
        if h1 is not None:
            text = "".join(str(t) for t in h1.itertext()).strip()
            if text:
                return text
    except etree.XMLSyntaxError:
        logger.warning("Failed to parse topic for title: %s", topic_path)

    return Path(link_path).stem.replace("_", " ")


def _walk_toc(
    elem: etree._Element,
    breadcrumbs: list[str],
    index: dict[str, str],
    content_dir: Path | None,
) -> None:
    """Recursively walk TocEntry elements, building breadcrumbs.

    Args:
        elem: Current XML element (root or TocEntry).
        breadcrumbs: Accumulated breadcrumb titles from ancestors.
        index: Mutable mapping being populated with path -> breadcrumb.
        content_dir: Content directory for LinkedTitle resolution.
    """
    for entry in elem:
        if entry.tag != "TocEntry":
            continue

        title = (entry.get("Title") or "").strip()
        link = entry.get("Link", "")

        # Resolve [%=System.LinkedTitle%] from the topic file's <title>
        if title == LINKED_TITLE_PATTERN and link and content_dir is not None:
            rel_path = link.removeprefix("/Content/")
            title = _resolve_linked_title(rel_path, content_dir)

        current_crumbs = [*breadcrumbs, title] if title else breadcrumbs

        if link:
            rel_path = link.removeprefix("/Content/")
            if rel_path not in index:  # First-found wins (priority order)
                index[rel_path] = " > ".join(current_crumbs)

        # Recurse into child TocEntry elements
        _walk_toc(entry, current_crumbs, index, content_dir)


__all__ = ["build_toc_index", "directory_fallback_path"]
