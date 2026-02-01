"""WordPress parsers for Advantage magazine and Knowledge Base content.

Provides two parsers that crawl the published WordPress sites at basis.cloud,
strip navigation chrome, and yield ``Document`` objects compatible with the
same pipeline as the Flare XHTML and web crawl parsers.

AdvantageParser targets the Advantage magazine index at
``https://basis.cloud/advantage-index/``.

KnowledgeBaseParser targets the Knowledge Base at
``https://basis.cloud/knowledge-base/``, handling the ECKB (Echo Knowledge Base)
plugin layout used on that section.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Iterator
from typing import Final
from xml.etree import ElementTree

import httpx
from bs4 import BeautifulSoup, Tag

from bbj_rag.models import Document
from bbj_rag.parsers.web_crawl import _html_to_markdown

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# WordPress chrome selectors
# ---------------------------------------------------------------------------

_WP_CHROME_SELECTORS: Final[list[str]] = [
    "nav",
    "script",
    "style",
    "noscript",
    "iframe",
    "header",
    "footer",
    ".site-header",
    ".site-footer",
    ".breadcrumb",
    ".breadcrumbs",
    ".sidebar",
    ".widget-area",
    ".comments-area",
    ".post-navigation",
    "#secondary",
    "#comments",
    ".wp-block-separator",
]

# Media tags to strip (text-only decision).
_MEDIA_TAGS: Final[list[str]] = ["img", "video", "audio", "iframe", "figure", "svg"]

# Content selectors for Advantage articles, tried in priority order.
_ADVANTAGE_CONTENT_SELECTORS: Final[list[str]] = [
    ".entry-content",
    "article .post-content",
    "article",
    "[role='main']",
    "main",
]

# Content selectors for Knowledge Base (ECKB plugin), tried in priority order.
_KB_CONTENT_SELECTORS: Final[list[str]] = [
    "#eckb-article-body",
    ".eckb-article-content-body",
    "article .entry-content",
    "article",
    "main",
]

# Suffix patterns stripped from <title> text.
_WP_TITLE_SUFFIXES: Final[list[str]] = [
    " - BASIS International",
    " - BASIS",
    " | BASIS International",
    " | BASIS",
    " - Advantage",
    " | Advantage",
]

_USER_AGENT: Final[str] = "bbj-rag-crawler/0.1 (+bbj-ai-strategy)"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _strip_wp_chrome(soup: BeautifulSoup) -> None:
    """Remove WordPress navigation chrome and media from *soup* in place."""
    for selector in _WP_CHROME_SELECTORS:
        for elem in soup.select(selector):
            elem.decompose()
    # Strip all media elements (text-only).
    for tag_name in _MEDIA_TAGS:
        for elem in soup.find_all(tag_name):
            elem.decompose()


def _fetch_page(
    client: httpx.Client,
    url: str,
    max_retries: int,
) -> str | None:
    """Fetch a page, retrying on transient errors.  Returns HTML or *None*."""
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


def _extract_title_from_soup(soup: BeautifulSoup) -> str:
    """Extract a clean page title from *soup*.

    Strips known WordPress site-name suffixes. Falls back to the first
    ``<h1>`` if ``<title>`` is absent or empty.
    """
    title_tag = soup.find("title")
    if title_tag is not None:
        raw = title_tag.get_text(strip=True)
        if raw:
            title = _strip_wp_title_suffix(raw)
            if title:
                return title

    h1 = soup.find("h1")
    if h1 is not None and isinstance(h1, Tag):
        text = h1.get_text(strip=True)
        if text:
            return _strip_wp_title_suffix(text)

    return "Untitled"


def _strip_wp_title_suffix(title: str) -> str:
    """Remove known site-name suffixes from a WordPress title string."""
    for suffix in _WP_TITLE_SUFFIXES:
        if title.endswith(suffix):
            title = title[: -len(suffix)]
    return title.strip()


def _find_content(soup: BeautifulSoup, selectors: list[str]) -> Tag | None:
    """Locate the main content container using *selectors* in priority order."""
    for selector in selectors:
        tag = soup.select_one(selector)
        if tag is not None and isinstance(tag, Tag):
            return tag
    body = soup.find("body")
    if body is not None and isinstance(body, Tag):
        return body
    return None


# ---------------------------------------------------------------------------
# AdvantageParser
# ---------------------------------------------------------------------------


class AdvantageParser:
    """Crawl Advantage magazine articles and yield ``Document`` objects.

    Implements the ``DocumentParser`` protocol.  Discovers article URLs
    from the index page, then fetches each article individually.

    Args:
        index_url: URL of the Advantage magazine index page.
        rate_limit: Minimum seconds between HTTP requests.
        max_retries: Number of retries on transient errors.
    """

    def __init__(
        self,
        index_url: str = "https://basis.cloud/advantage-index/",
        rate_limit: float = 1.0,
        max_retries: int = 1,
    ) -> None:
        self.index_url = index_url
        self.rate_limit = rate_limit
        self.max_retries = max_retries

    def parse(self) -> Iterator[Document]:
        """Crawl Advantage articles and yield one ``Document`` per article."""
        with httpx.Client(
            timeout=30.0,
            headers={"User-Agent": _USER_AGENT},
            follow_redirects=True,
        ) as client:
            urls = self._discover_article_urls(client, self.index_url)

            # Sitemap fallback when HTML parsing finds nothing.
            if not urls:
                logger.info("No article URLs from index page; trying sitemap fallback")
                urls = self._sitemap_fallback(client)

            logger.info("Advantage: discovered %d article URLs", len(urls))

            for i, url in enumerate(urls, 1):
                logger.debug("Advantage: fetching %d/%d %s", i, len(urls), url)
                html = _fetch_page(client, url, self.max_retries)
                if html is None:
                    logger.warning("Advantage: failed to fetch %s", url)
                    continue

                soup = BeautifulSoup(html, "lxml")
                title = _extract_title_from_soup(soup)
                _strip_wp_chrome(soup)

                content_root = _find_content(soup, list(_ADVANTAGE_CONTENT_SELECTORS))
                if content_root is None:
                    logger.debug("Advantage: no content container for %s", url)
                    continue

                content = _html_to_markdown(content_root)
                if not content.strip():
                    logger.debug("Advantage: empty content for %s", url)
                    continue

                yield Document(
                    source_url=url,
                    title=title,
                    doc_type="article",
                    content=content,
                    generations=["bbj"],
                    context_header=f"Advantage Magazine > {title}",
                    metadata={"source": "advantage"},
                    deprecated=False,
                )

                if i < len(urls):
                    time.sleep(self.rate_limit)

    # ------------------------------------------------------------------
    # URL discovery
    # ------------------------------------------------------------------

    @staticmethod
    def _discover_article_urls(
        client: httpx.Client,
        index_url: str,
    ) -> list[str]:
        """Discover article URLs from the Advantage index page."""
        html = _fetch_page(client, index_url, max_retries=1)
        if html is None:
            logger.warning("Advantage: could not fetch index page %s", index_url)
            return []

        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()
        urls: list[str] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if isinstance(href, list):
                href = href[0]
            href = str(href)
            if "/advantage/" not in href:
                continue
            # Skip the index page itself.
            if href.rstrip("/") == index_url.rstrip("/"):
                continue
            # Normalise.
            canonical = href.split("#")[0]
            if canonical not in seen:
                seen.add(canonical)
                urls.append(canonical)

        logger.info("Advantage: found %d article links on index page", len(urls))
        return sorted(urls)

    def _sitemap_fallback(self, client: httpx.Client) -> list[str]:
        """Try to discover article URLs from the post sitemap."""
        from urllib.parse import urlparse

        parsed = urlparse(self.index_url)
        sitemap_url = f"{parsed.scheme}://{parsed.netloc}/post-sitemap.xml"
        html = _fetch_page(client, sitemap_url, max_retries=1)
        if html is None:
            return []

        urls: list[str] = []
        try:
            root = ElementTree.fromstring(html)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root.findall(".//sm:loc", ns):
                if loc.text and "/advantage/" in loc.text:
                    urls.append(loc.text)
        except ElementTree.ParseError:
            logger.warning("Advantage: failed to parse sitemap at %s", sitemap_url)

        logger.info("Advantage: sitemap fallback found %d URLs", len(urls))
        return sorted(urls)


# ---------------------------------------------------------------------------
# KnowledgeBaseParser
# ---------------------------------------------------------------------------


class KnowledgeBaseParser:
    """Crawl Knowledge Base articles and yield ``Document`` objects.

    Implements the ``DocumentParser`` protocol.  Handles the ECKB
    (Echo Knowledge Base) plugin layout used on the KB section.

    Args:
        index_url: URL of the Knowledge Base index page.
        rate_limit: Minimum seconds between HTTP requests.
        max_retries: Number of retries on transient errors.
    """

    def __init__(
        self,
        index_url: str = "https://basis.cloud/knowledge-base/",
        rate_limit: float = 1.0,
        max_retries: int = 1,
    ) -> None:
        self.index_url = index_url
        self.rate_limit = rate_limit
        self.max_retries = max_retries

    def parse(self) -> Iterator[Document]:
        """Crawl Knowledge Base articles and yield one ``Document`` per lesson."""
        with httpx.Client(
            timeout=30.0,
            headers={"User-Agent": _USER_AGENT},
            follow_redirects=True,
        ) as client:
            urls = self._discover_kb_urls(client, self.index_url)

            # Sitemap fallback when HTML parsing finds nothing.
            if not urls:
                logger.info("KB: no URLs from index page; trying sitemap fallback")
                urls = self._sitemap_fallback(client)

            logger.info("KB: discovered %d article URLs", len(urls))

            for i, url in enumerate(urls, 1):
                logger.debug("KB: fetching %d/%d %s", i, len(urls), url)
                html = _fetch_page(client, url, self.max_retries)
                if html is None:
                    logger.warning("KB: failed to fetch %s", url)
                    continue

                soup = BeautifulSoup(html, "lxml")
                title = _extract_title_from_soup(soup)
                _strip_wp_chrome(soup)

                content_root = _find_content(soup, list(_KB_CONTENT_SELECTORS))
                if content_root is None:
                    logger.debug("KB: no content container for %s", url)
                    continue

                content = _html_to_markdown(content_root)
                if not content.strip():
                    logger.debug("KB: empty content after extraction for %s", url)
                    continue

                yield Document(
                    source_url=url,
                    title=title,
                    doc_type="concept",
                    content=content,
                    generations=["bbj"],
                    context_header=f"Knowledge Base > {title}",
                    metadata={"source": "knowledge_base"},
                    deprecated=False,
                )

                if i < len(urls):
                    time.sleep(self.rate_limit)

    # ------------------------------------------------------------------
    # URL discovery
    # ------------------------------------------------------------------

    @staticmethod
    def _discover_kb_urls(
        client: httpx.Client,
        index_url: str,
    ) -> list[str]:
        """Discover KB article URLs from the Knowledge Base index page."""
        html = _fetch_page(client, index_url, max_retries=1)
        if html is None:
            logger.warning("KB: could not fetch index page %s", index_url)
            return []

        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()
        urls: list[str] = []

        # KB articles follow /knowledge-base/kb{number}/ pattern.
        kb_pattern = re.compile(r"/knowledge-base/kb\d+", re.IGNORECASE)

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if isinstance(href, list):
                href = href[0]
            href = str(href)
            if not kb_pattern.search(href):
                continue
            canonical = href.split("#")[0]
            if canonical not in seen:
                seen.add(canonical)
                urls.append(canonical)

        logger.info("KB: found %d article links on index page", len(urls))
        return sorted(urls)

    def _sitemap_fallback(self, client: httpx.Client) -> list[str]:
        """Try to discover KB URLs from sitemaps."""
        from urllib.parse import urlparse

        parsed = urlparse(self.index_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        sitemap_candidates = [f"{base}/kb-sitemap.xml", f"{base}/sitemap.xml"]

        kb_pattern = re.compile(r"/knowledge-base/kb\d+", re.IGNORECASE)

        for sitemap_url in sitemap_candidates:
            xml_text = _fetch_page(client, sitemap_url, max_retries=1)
            if xml_text is None:
                continue

            urls: list[str] = []
            try:
                root = ElementTree.fromstring(xml_text)
                ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                for loc in root.findall(".//sm:loc", ns):
                    if loc.text and kb_pattern.search(loc.text):
                        urls.append(loc.text)
            except ElementTree.ParseError:
                logger.warning("KB: failed to parse sitemap at %s", sitemap_url)
                continue

            if urls:
                logger.info(
                    "KB: sitemap fallback found %d URLs from %s",
                    len(urls),
                    sitemap_url,
                )
                return sorted(urls)

        return []


__all__ = ["AdvantageParser", "KnowledgeBaseParser"]
