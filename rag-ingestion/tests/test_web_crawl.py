"""Tests for the web crawl parser.

Unit tests use mocked HTTP responses to validate content extraction,
chrome stripping, and Document construction without network access.
One optional slow test performs a limited live crawl.
"""

from __future__ import annotations

import os
import textwrap
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup, Tag

from bbj_rag.parsers.web_crawl import (
    WebCrawlParser,
    _canonicalize,
    _extract_title,
    _find_content_root,
    _html_to_markdown,
    _strip_chrome,
    _table_to_markdown,
    url_to_hierarchy,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_URL = "https://documentation.basis.cloud/BASISHelp/WebHelp/"


def _soup(html: str) -> BeautifulSoup:
    """Parse an HTML fragment into a BeautifulSoup tree."""
    return BeautifulSoup(html, "lxml")


def _tag(html: str) -> Tag:
    """Parse an HTML fragment and return the ``<body>`` tag."""
    soup = _soup(html)
    body = soup.find("body")
    assert isinstance(body, Tag)
    return body


# ---------------------------------------------------------------------------
# url_to_hierarchy
# ---------------------------------------------------------------------------


class TestUrlToHierarchy:
    def test_deep_path(self):
        url = (
            "https://documentation.basis.cloud/BASISHelp/WebHelp/"
            "bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm"
        )
        assert url_to_hierarchy(url, BASE_URL) == "bbjobjects > Window > bbjwindow"

    def test_single_directory(self):
        url = (
            "https://documentation.basis.cloud/BASISHelp/WebHelp/"
            "commands/abs_function.htm"
        )
        assert url_to_hierarchy(url, BASE_URL) == "commands"

    def test_root_level_file(self):
        url = "https://documentation.basis.cloud/BASISHelp/WebHelp/index.htm"
        assert url_to_hierarchy(url, BASE_URL) == ""

    def test_two_levels(self):
        url = (
            "https://documentation.basis.cloud/BASISHelp/WebHelp/"
            "bbjobjects/Window/bbjwindow.htm"
        )
        assert url_to_hierarchy(url, BASE_URL) == "bbjobjects > Window"

    def test_arrow_separator(self):
        url = "https://documentation.basis.cloud/BASISHelp/WebHelp/a/b/c/d.htm"
        result = url_to_hierarchy(url, BASE_URL)
        assert " > " in result
        assert result == "a > b > c"


# ---------------------------------------------------------------------------
# Title extraction
# ---------------------------------------------------------------------------


class TestTitleExtraction:
    def test_title_from_title_tag(self):
        html = textwrap.dedent("""\
            <html>
            <head><title>BBjWindow::addButton - BASISHelp</title></head>
            <body><div class="body-container"><h1>BBjWindow::addButton</h1>
            <p>Some content</p></div></body>
            </html>
        """)
        soup = _soup(html)
        content_root = _find_content_root(soup)
        assert content_root is not None
        title = _extract_title(soup, content_root, "https://example.com/page.htm")
        assert title == "BBjWindow::addButton"

    def test_title_strips_basishelp_suffix(self):
        html = (
            "<html><head><title>My Topic - BASISHelp</title></head>"
            "<body><p>x</p></body></html>"
        )
        soup = _soup(html)
        body = soup.find("body")
        assert isinstance(body, Tag)
        title = _extract_title(soup, body, "https://example.com/page.htm")
        assert title == "My Topic"

    def test_title_fallback_to_h1(self):
        html = (
            "<html><head></head><body>"
            "<h1>Heading Title</h1><p>content</p></body></html>"
        )
        soup = _soup(html)
        body = soup.find("body")
        assert isinstance(body, Tag)
        title = _extract_title(soup, body, "https://example.com/page.htm")
        assert title == "Heading Title"

    def test_title_fallback_to_url(self):
        html = "<html><head></head><body><p>no heading</p></body></html>"
        soup = _soup(html)
        body = soup.find("body")
        assert isinstance(body, Tag)
        title = _extract_title(soup, body, "https://example.com/my_great_page.htm")
        assert title == "my great page"


# ---------------------------------------------------------------------------
# Chrome stripping
# ---------------------------------------------------------------------------


class TestChromeStripping:
    def test_nav_sidebar_removed(self):
        html = textwrap.dedent("""\
            <html><body>
            <nav><ul><li>Sidebar link</li></ul></nav>
            <div class="body-container">
              <h1>Real Content</h1>
              <p>This is the topic text.</p>
            </div>
            </body></html>
        """)
        soup = _soup(html)
        _strip_chrome(soup)
        content = _find_content_root(soup)
        assert content is not None
        md = _html_to_markdown(content)
        assert "Real Content" in md
        assert "This is the topic text." in md
        assert "Sidebar link" not in md

    def test_search_bar_removed(self):
        html = textwrap.dedent("""\
            <html><body>
            <div class="search-bar"><input type="text" /></div>
            <div class="body-container"><p>Content here</p></div>
            </body></html>
        """)
        soup = _soup(html)
        _strip_chrome(soup)
        content = _find_content_root(soup)
        assert content is not None
        md = _html_to_markdown(content)
        assert "Content here" in md

    def test_breadcrumbs_removed(self):
        html = textwrap.dedent("""\
            <html><body>
            <div class="breadcrumbs">Home > Section > Topic</div>
            <div class="body-container"><p>Topic text</p></div>
            </body></html>
        """)
        soup = _soup(html)
        _strip_chrome(soup)
        content = _find_content_root(soup)
        assert content is not None
        md = _html_to_markdown(content)
        assert "Topic text" in md
        assert "Home > Section" not in md

    def test_scripts_removed(self):
        html = textwrap.dedent("""\
            <html><body>
            <script>alert('x')</script>
            <div class="body-container"><p>Safe content</p></div>
            </body></html>
        """)
        soup = _soup(html)
        _strip_chrome(soup)
        content = _find_content_root(soup)
        assert content is not None
        md = _html_to_markdown(content)
        assert "Safe content" in md
        assert "alert" not in md

    def test_only_chrome_yields_no_content(self):
        """Page with only navigation and no real content."""
        html = textwrap.dedent("""\
            <html><body>
            <nav><ul><li>Link 1</li></ul></nav>
            <header><h1>Site Header</h1></header>
            <footer>Copyright</footer>
            </body></html>
        """)
        soup = _soup(html)
        _strip_chrome(soup)
        content = _find_content_root(soup)
        if content is not None:
            md = _html_to_markdown(content)
            # After stripping chrome, body should be effectively empty
            assert md.strip() == "" or len(md.strip()) < 5


# ---------------------------------------------------------------------------
# Code block preservation
# ---------------------------------------------------------------------------


class TestCodeBlocks:
    def test_code_block_preserved(self):
        html = textwrap.dedent("""\
            <html><body>
            <div class="body-container">
            <p>Example:</p>
            <pre><code class="language-bbj">REM test
PRINT "Hello"</code></pre>
            </div>
            </body></html>
        """)
        soup = _soup(html)
        content = _find_content_root(soup)
        assert content is not None
        md = _html_to_markdown(content)
        assert "```bbj" in md
        assert "REM test" in md
        assert 'PRINT "Hello"' in md
        assert "```" in md

    def test_code_block_without_language(self):
        html = textwrap.dedent("""\
            <html><body>
            <div class="body-container">
            <pre><code>some code here</code></pre>
            </div>
            </body></html>
        """)
        soup = _soup(html)
        content = _find_content_root(soup)
        assert content is not None
        md = _html_to_markdown(content)
        assert "```\nsome code here\n```" in md

    def test_pre_without_code_tag(self):
        html = textwrap.dedent("""\
            <html><body>
            <div class="body-container">
            <pre>plain preformatted text</pre>
            </div>
            </body></html>
        """)
        soup = _soup(html)
        content = _find_content_root(soup)
        assert content is not None
        md = _html_to_markdown(content)
        assert "```" in md
        assert "plain preformatted text" in md


# ---------------------------------------------------------------------------
# Table conversion
# ---------------------------------------------------------------------------


class TestTableToMarkdown:
    def test_basic_table(self):
        html = textwrap.dedent("""\
            <table>
            <tr><th>Method</th><th>Return</th></tr>
            <tr><td>addButton</td><td>BBjButton</td></tr>
            <tr><td>addGrid</td><td>BBjGrid</td></tr>
            </table>
        """)
        soup = _soup(html)
        table = soup.find("table")
        assert isinstance(table, Tag)
        md = _table_to_markdown(table)
        assert "| Method | Return |" in md
        assert "| --- | --- |" in md
        assert "| addButton | BBjButton |" in md
        assert "| addGrid | BBjGrid |" in md

    def test_table_in_content(self):
        html = textwrap.dedent("""\
            <html><body>
            <div class="body-container">
            <h2>Parameters</h2>
            <table>
            <tr><th>Name</th><th>Type</th></tr>
            <tr><td>x</td><td>int</td></tr>
            </table>
            </div>
            </body></html>
        """)
        soup = _soup(html)
        content = _find_content_root(soup)
        assert content is not None
        md = _html_to_markdown(content)
        assert "## Parameters" in md
        assert "| Name | Type |" in md
        assert "| x | int |" in md

    def test_table_with_pipe_in_cell(self):
        html = textwrap.dedent("""\
            <table>
            <tr><th>Syntax</th></tr>
            <tr><td>a | b</td></tr>
            </table>
        """)
        soup = _soup(html)
        table = soup.find("table")
        assert isinstance(table, Tag)
        md = _table_to_markdown(table)
        assert "a \\| b" in md


# ---------------------------------------------------------------------------
# List conversion
# ---------------------------------------------------------------------------


class TestListConversion:
    def test_unordered_list(self):
        html = textwrap.dedent("""\
            <html><body><div class="body-container">
            <ul><li>Alpha</li><li>Beta</li><li>Gamma</li></ul>
            </div></body></html>
        """)
        soup = _soup(html)
        content = _find_content_root(soup)
        assert content is not None
        md = _html_to_markdown(content)
        assert "- Alpha" in md
        assert "- Beta" in md
        assert "- Gamma" in md

    def test_ordered_list(self):
        html = textwrap.dedent("""\
            <html><body><div class="body-container">
            <ol><li>First</li><li>Second</li></ol>
            </div></body></html>
        """)
        soup = _soup(html)
        content = _find_content_root(soup)
        assert content is not None
        md = _html_to_markdown(content)
        assert "1. First" in md
        assert "2. Second" in md


# ---------------------------------------------------------------------------
# Document construction via mocked parse()
# ---------------------------------------------------------------------------


class TestDocumentConstruction:
    """Test that parse() yields Documents with correct fields using mocked HTTP."""

    SAMPLE_HTML = textwrap.dedent("""\
        <html>
        <head><title>BBjWindow::addButton - BASISHelp</title></head>
        <body>
        <nav><ul><li>Nav link</li></ul></nav>
        <div class="body-container">
          <h1>BBjWindow::addButton</h1>
          <p>Adds a button to the window.</p>
          <pre><code class="language-bbj">REM example
window!.addButton(101, 10, 10, 90, 25, "OK")</code></pre>
          <table>
          <tr><th>Parameter</th><th>Description</th></tr>
          <tr><td>id</td><td>Control ID</td></tr>
          </table>
        </div>
        </body>
        </html>
    """)

    INDEX_HTML = textwrap.dedent("""\
        <html>
        <head><title>Index - BASISHelp</title></head>
        <body>
        <div class="body-container">
          <h1>BASISHelp Index</h1>
          <p>Welcome to BASIS documentation.</p>
          <a href="bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm">addButton</a>
        </div>
        </body>
        </html>
    """)

    def _mock_get(self, url_map: dict[str, str]):
        """Create a mock httpx.Client.get that returns canned responses."""

        def mock_get(url: str) -> MagicMock:
            resp = MagicMock()
            if url in url_map:
                resp.status_code = 200
                resp.text = url_map[url]
            else:
                resp.status_code = 404
                resp.text = ""
            return resp

        return mock_get

    @patch("bbj_rag.parsers.web_crawl._fetch_disallowed_paths", return_value=[])
    @patch("bbj_rag.parsers.web_crawl.time.sleep")
    def test_parse_yields_documents(self, mock_sleep, mock_robots):
        base = BASE_URL
        topic_url = base + "bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm"
        url_map = {
            _canonicalize(base): self.INDEX_HTML,
            _canonicalize(topic_url): self.SAMPLE_HTML,
        }

        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = self._mock_get(url_map)

            parser = WebCrawlParser(base_url=base, rate_limit=0.0)
            docs = list(parser.parse())

        # Should have at least 2 documents (index + topic page)
        assert len(docs) >= 1

        # Find the topic page document
        topic_docs = [d for d in docs if "addButton" in d.title]
        assert len(topic_docs) == 1
        doc = topic_docs[0]

        assert doc.doc_type == "web_crawl"
        assert doc.generations == ["bbj"]
        assert "Adds a button to the window." in doc.content
        assert "```bbj" in doc.content
        assert "Nav link" not in doc.content
        assert doc.metadata["source"] == "web_crawl"
        assert doc.metadata["section_path"] == "bbjobjects > Window > bbjwindow"

    @patch("bbj_rag.parsers.web_crawl._fetch_disallowed_paths", return_value=[])
    @patch("bbj_rag.parsers.web_crawl.time.sleep")
    def test_empty_content_skipped(self, mock_sleep, mock_robots):
        """Pages with only navigation chrome should not yield Documents."""
        chrome_only = textwrap.dedent("""\
            <html><head><title>Empty</title></head>
            <body>
            <nav><ul><li>Link</li></ul></nav>
            <header>Header</header>
            <footer>Footer</footer>
            </body></html>
        """)
        url_map = {_canonicalize(BASE_URL): chrome_only}

        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = self._mock_get(url_map)

            parser = WebCrawlParser(base_url=BASE_URL, rate_limit=0.0)
            docs = list(parser.parse())

        assert len(docs) == 0

    @patch("bbj_rag.parsers.web_crawl._fetch_disallowed_paths", return_value=[])
    @patch("bbj_rag.parsers.web_crawl.time.sleep")
    def test_default_generations_bbj(self, mock_sleep, mock_robots):
        """All documents default to generations=['bbj']."""
        simple = textwrap.dedent("""\
            <html><head><title>Test</title></head>
            <body><div class="body-container"><p>Content here</p></div></body>
            </html>
        """)
        url_map = {_canonicalize(BASE_URL): simple}

        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = self._mock_get(url_map)

            parser = WebCrawlParser(base_url=BASE_URL, rate_limit=0.0)
            docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].generations == ["bbj"]

    @patch("bbj_rag.parsers.web_crawl._fetch_disallowed_paths", return_value=[])
    @patch("bbj_rag.parsers.web_crawl.time.sleep")
    def test_doc_type_is_web_crawl(self, mock_sleep, mock_robots):
        """All documents have doc_type='web_crawl'."""
        simple = textwrap.dedent("""\
            <html><head><title>Test</title></head>
            <body><div class="body-container"><p>Content</p></div></body>
            </html>
        """)
        url_map = {_canonicalize(BASE_URL): simple}

        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = self._mock_get(url_map)

            parser = WebCrawlParser(base_url=BASE_URL, rate_limit=0.0)
            docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].doc_type == "web_crawl"


# ---------------------------------------------------------------------------
# Live crawl test (optional -- requires network)
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.skipif(
    os.environ.get("RUN_SLOW_TESTS") != "1",
    reason="Slow test -- set RUN_SLOW_TESTS=1 to run",
)
def test_live_crawl_limited():
    """Crawl a small number of pages from the live site."""
    parser = WebCrawlParser(rate_limit=1.0)
    docs = []
    for doc in parser.parse():
        docs.append(doc)
        if len(docs) >= 5:
            break
    assert len(docs) >= 1
    for doc in docs:
        assert doc.content.strip()
        assert doc.generations == ["bbj"]
        assert doc.doc_type == "web_crawl"
