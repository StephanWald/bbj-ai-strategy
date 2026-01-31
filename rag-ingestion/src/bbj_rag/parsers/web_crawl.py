"""Web crawl parser for documentation.basis.cloud.

Provides a fallback ingestion path when engineers don't have access to the
local MadCap Flare project files.  Crawls the published documentation site,
strips navigation chrome, and yields ``Document`` objects compatible with
the same pipeline as the Flare XHTML parser.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Iterator
from typing import Final
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from bbj_rag.models import Document

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL: Final[str] = "https://documentation.basis.cloud/BASISHelp/WebHelp/"

# Selectors for Flare navigation chrome to remove before content extraction.
_CHROME_SELECTORS: Final[list[str]] = [
    "nav",
    "script",
    "style",
    "noscript",
    "iframe",
    "header",
    "footer",
    # MadCap Flare-specific chrome classes
    ".sidenav",
    ".side-content",
    ".nav-wrapper",
    ".search-bar",
    ".search-container",
    ".breadcrumbs",
    ".breadcrumb",
    ".topic-navigation",
    "#navigation",
    "#search-container",
    "#search-bar",
    # Previous/Next navigation links
    ".previous-next-buttons",
    ".topic-footer",
    # Skip-to-content links and menus
    ".skip-to-content",
    ".menu-container",
    ".off-canvas-content",
    # MadCap generated containers
    "[data-mc-module-version]",
    ".nocontent",
    ".MCWebHelpFramesetLink",
]

# Content container selectors tried in priority order.
_CONTENT_SELECTORS: Final[list[str]] = [
    ".body-container",
    ".topic-content",
    "#mc-main-content",
    "#body",
    "main",
    "article",
    "[role='main']",
]

# Suffix patterns stripped from <title> text.
_TITLE_SUFFIXES: Final[list[str]] = [
    " - BASISHelp",
    " - BASIS Help",
    " - WebHelp",
    " | BASISHelp",
]


class WebCrawlParser:
    """Crawl documentation.basis.cloud and yield ``Document`` objects.

    Implements the ``DocumentParser`` protocol.  Uses *httpx* for HTTP
    and *BeautifulSoup* for HTML parsing.

    Args:
        base_url: Root URL of the documentation site.
        rate_limit: Minimum seconds between HTTP requests.
        max_retries: Number of retries on transient errors.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        rate_limit: float = 0.5,
        *,
        max_retries: int = 1,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.rate_limit = rate_limit
        self.max_retries = max_retries

    # ------------------------------------------------------------------
    # Public API (DocumentParser protocol)
    # ------------------------------------------------------------------

    def parse(self) -> Iterator[Document]:
        """Crawl the site and yield one ``Document`` per topic page."""
        visited: set[str] = set()
        queue: list[str] = [self.base_url]

        disallowed = _fetch_disallowed_paths(self.base_url)

        with httpx.Client(
            timeout=30.0,
            headers={"User-Agent": "bbj-rag-crawler/0.1 (+bbj-ai-strategy)"},
            follow_redirects=True,
        ) as client:
            while queue:
                url = queue.pop(0)
                canonical = _canonicalize(url)
                if canonical in visited:
                    continue
                visited.add(canonical)

                if _is_disallowed(canonical, disallowed):
                    logger.debug("Skipped (robots.txt): %s", canonical)
                    continue

                html = _fetch_page(client, canonical, self.max_retries)
                if html is None:
                    continue

                soup = BeautifulSoup(html, "lxml")

                # Discover new links before modifying the tree.
                for link_url in _extract_internal_links(soup, canonical, self.base_url):
                    link_canon = _canonicalize(link_url)
                    if link_canon not in visited:
                        queue.append(link_canon)

                # Strip navigation chrome.
                _strip_chrome(soup)

                # Extract main content container.
                content_root = _find_content_root(soup)
                if content_root is None:
                    logger.debug("No content container found: %s", canonical)
                    continue

                content = _html_to_markdown(content_root)
                if not content.strip():
                    continue

                title = _extract_title(soup, content_root, canonical)
                section_path = url_to_hierarchy(canonical, self.base_url)

                yield Document(
                    source_url=canonical,
                    title=title,
                    doc_type="web_crawl",
                    content=content,
                    generations=["bbj"],
                    metadata={
                        "section_path": section_path,
                        "source": "web_crawl",
                    },
                )

                time.sleep(self.rate_limit)


# ------------------------------------------------------------------
# URL helpers
# ------------------------------------------------------------------


def url_to_hierarchy(url: str, base_url: str) -> str:
    """Derive an arrow-separated section path from a URL.

    >>> url_to_hierarchy(
    ...     "https://documentation.basis.cloud/BASISHelp/WebHelp/"
    ...     "bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm",
    ...     "https://documentation.basis.cloud/BASISHelp/WebHelp/",
    ... )
    'bbjobjects > Window > bbjwindow'
    """
    base = base_url.rstrip("/") + "/"
    relative = url
    if relative.startswith(base):
        relative = relative[len(base) :]

    # Strip extension
    relative = re.sub(r"\.[^./]+$", "", relative)

    parts = [p for p in relative.split("/") if p]
    if len(parts) <= 1:
        return ""
    # Section path is everything except the last component.
    return " > ".join(parts[:-1])


def _canonicalize(url: str) -> str:
    """Normalise a URL by removing fragments and trailing slashes on path."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") if not parsed.path.endswith(".htm") else parsed.path
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _is_disallowed(url: str, disallowed: list[str]) -> bool:
    """Check whether *url* matches any robots.txt Disallow path."""
    parsed = urlparse(url)
    for pattern in disallowed:
        if parsed.path.startswith(pattern):
            return True
    return False


def _fetch_disallowed_paths(base_url: str) -> list[str]:
    """Fetch and parse robots.txt Disallow directives for ``*`` user-agent."""
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        resp = httpx.get(robots_url, timeout=10.0)
        if resp.status_code != 200:
            return []
    except httpx.HTTPError:
        return []

    disallowed: list[str] = []
    in_star_block = False
    for line in resp.text.splitlines():
        line = line.strip()
        if line.lower().startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
            in_star_block = agent == "*"
        elif in_star_block and line.lower().startswith("disallow:"):
            path = line.split(":", 1)[1].strip()
            if path:
                disallowed.append(path)
    return disallowed


# ------------------------------------------------------------------
# HTTP helpers
# ------------------------------------------------------------------


def _fetch_page(
    client: httpx.Client,
    url: str,
    max_retries: int,
) -> str | None:
    """Fetch a page, retrying on transient errors.  Returns HTML or None."""
    for attempt in range(1 + max_retries):
        try:
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.text
            logger.warning(
                "HTTP %d for %s (attempt %d)", resp.status_code, url, attempt + 1
            )
        except httpx.HTTPError as exc:
            logger.warning("HTTP error for %s: %s (attempt %d)", url, exc, attempt + 1)
        if attempt < max_retries:
            time.sleep(1.0 * (attempt + 1))
    return None


# ------------------------------------------------------------------
# Link discovery
# ------------------------------------------------------------------


def _extract_internal_links(
    soup: BeautifulSoup,
    current_url: str,
    base_url: str,
) -> list[str]:
    """Return absolute URLs of internal .htm links found in *soup*."""
    links: list[str] = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if isinstance(href, list):
            href = href[0]
        # Skip anchors, javascript, mailto
        if href.startswith(("#", "javascript:", "mailto:")):
            continue
        absolute = urljoin(current_url, href)
        # Strip fragment
        absolute = absolute.split("#")[0]
        if not absolute.startswith(base_url):
            continue
        # Only .htm files
        parsed = urlparse(absolute)
        if parsed.path.endswith(".htm"):
            links.append(absolute)
    return links


# ------------------------------------------------------------------
# Chrome stripping
# ------------------------------------------------------------------


def _strip_chrome(soup: BeautifulSoup) -> None:
    """Remove Flare navigation chrome from *soup* in place."""
    for selector in _CHROME_SELECTORS:
        for elem in soup.select(selector):
            elem.decompose()


def _find_content_root(soup: BeautifulSoup) -> Tag | None:
    """Locate the main content container in *soup*."""
    for selector in _CONTENT_SELECTORS:
        tag = soup.select_one(selector)
        if tag is not None and isinstance(tag, Tag):
            return tag
    body = soup.find("body")
    if body is not None and isinstance(body, Tag):
        return body
    return None


# ------------------------------------------------------------------
# Title extraction
# ------------------------------------------------------------------


def _extract_title(
    soup: BeautifulSoup,
    content_root: Tag,
    url: str,
) -> str:
    """Extract a clean page title."""
    # Try <title> tag first
    title_tag = soup.find("title")
    if title_tag is not None:
        raw = title_tag.get_text(strip=True)
        if raw:
            title = _strip_title_suffix(raw)
            if title:
                return title

    # Fallback: first <h1> in content
    h1 = content_root.find("h1")
    if h1 is not None:
        text = h1.get_text(strip=True)
        if text:
            return text

    # Fallback: last URL path component
    parsed = urlparse(url)
    stem = parsed.path.rsplit("/", 1)[-1]
    stem = re.sub(r"\.[^.]+$", "", stem)
    return stem.replace("_", " ").replace("-", " ") or "Untitled"


def _strip_title_suffix(title: str) -> str:
    """Remove known site-name suffixes from a title string."""
    for suffix in _TITLE_SUFFIXES:
        if title.endswith(suffix):
            title = title[: -len(suffix)]
    return title.strip()


# ------------------------------------------------------------------
# HTML-to-Markdown conversion
# ------------------------------------------------------------------


def _html_to_markdown(root: Tag) -> str:
    """Convert an HTML element tree to Markdown text.

    Handles headings, paragraphs, code blocks, tables, and lists.
    """
    parts: list[str] = []
    _walk(root, parts)
    # Collapse excessive blank lines.
    text = "\n".join(parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _walk(tag: Tag, parts: list[str]) -> None:
    """Recursively walk *tag* and append Markdown fragments to *parts*."""
    for child in tag.children:
        if isinstance(child, Tag):
            name = child.name

            # Headings
            if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                level = int(name[1])
                text = child.get_text(strip=True)
                if text:
                    parts.append("")
                    parts.append(f"{'#' * level} {text}")
                    parts.append("")
                continue

            # Preformatted / code blocks
            if name == "pre":
                code_tag = child.find("code")
                if code_tag is not None and isinstance(code_tag, Tag):
                    lang = _detect_language(code_tag)
                    code_text = code_tag.get_text()
                else:
                    lang = ""
                    code_text = child.get_text()
                parts.append("")
                parts.append(f"```{lang}")
                parts.append(code_text.rstrip())
                parts.append("```")
                parts.append("")
                continue

            # Tables
            if name == "table":
                table_md = _table_to_markdown(child)
                if table_md:
                    parts.append("")
                    parts.append(table_md)
                    parts.append("")
                continue

            # Unordered lists
            if name == "ul":
                _list_to_markdown(child, parts, ordered=False)
                continue

            # Ordered lists
            if name == "ol":
                _list_to_markdown(child, parts, ordered=True)
                continue

            # Paragraphs
            if name == "p":
                text = child.get_text(strip=True)
                if text:
                    parts.append("")
                    parts.append(text)
                continue

            # Images: skip
            if name == "img":
                continue

            # Everything else: recurse
            _walk(child, parts)
        else:
            # NavigableString -- only emit if non-whitespace and direct child
            text = str(child).strip()
            if text:
                parts.append(text)


def _detect_language(code_tag: Tag) -> str:
    """Detect language hint from a ``<code>`` element's class attribute."""
    raw = code_tag.get("class")
    if raw is None:
        return ""
    if isinstance(raw, str):
        class_list = raw.split()
    elif isinstance(raw, list):
        class_list = [str(c) for c in raw]
    else:
        return ""
    for cls in class_list:
        if cls.startswith("language-"):
            return cls[len("language-") :]
    return ""


def _table_to_markdown(table: Tag) -> str:
    """Convert an HTML ``<table>`` to a Markdown table string."""
    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        if not isinstance(tr, Tag):
            continue
        cells: list[str] = []
        for cell in tr.find_all(["th", "td"]):
            if isinstance(cell, Tag):
                cells.append(cell.get_text(strip=True).replace("|", "\\|"))
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    # Normalise column count.
    max_cols = max(len(r) for r in rows)
    for row in rows:
        while len(row) < max_cols:
            row.append("")

    lines: list[str] = []
    # Header row
    lines.append("| " + " | ".join(rows[0]) + " |")
    lines.append("| " + " | ".join("---" for _ in rows[0]) + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _list_to_markdown(
    list_tag: Tag,
    parts: list[str],
    *,
    ordered: bool,
) -> None:
    """Append Markdown list items from a ``<ul>`` or ``<ol>`` to *parts*."""
    parts.append("")
    for idx, li in enumerate(list_tag.find_all("li", recursive=False), start=1):
        if not isinstance(li, Tag):
            continue
        text = li.get_text(strip=True)
        if text:
            prefix = f"{idx}. " if ordered else "- "
            parts.append(f"{prefix}{text}")
    parts.append("")


__all__ = ["WebCrawlParser", "url_to_hierarchy"]
