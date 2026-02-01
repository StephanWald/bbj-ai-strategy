"""Tests for the WordPress parsers (Advantage and Knowledge Base).

All tests mock HTTP calls -- no real network requests are made.
"""

from __future__ import annotations

import textwrap
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup

from bbj_rag.parsers import DocumentParser
from bbj_rag.parsers.wordpress import (
    AdvantageParser,
    KnowledgeBaseParser,
    _strip_wp_chrome,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

INDEX_URL_ADV = "https://basis.cloud/advantage-index/"
INDEX_URL_KB = "https://basis.cloud/knowledge-base/"

_ADV_ART1 = "https://basis.cloud/advantage/article-one/"
_ADV_ART2 = "https://basis.cloud/advantage/article-two/"
_ADV_EMPTY = "https://basis.cloud/advantage/empty-article/"
_ADV_SM1 = "https://basis.cloud/advantage/sitemap-article-one/"
_ADV_SM2 = "https://basis.cloud/advantage/sitemap-article-two/"
_ADV_SITEMAP = "https://basis.cloud/post-sitemap.xml"

_KB_ART1 = "https://basis.cloud/knowledge-base/kb01069/getting-started/"
_KB_ART2 = "https://basis.cloud/knowledge-base/kb01070/advanced-topics/"
_KB_MEDIA = "https://basis.cloud/knowledge-base/kb99999/media-test/"


def _soup(html: str) -> BeautifulSoup:
    """Parse an HTML fragment into a BeautifulSoup tree."""
    return BeautifulSoup(html, "lxml")


def _mock_get(url_map: dict[str, str]):
    """Create a mock ``httpx.Client.get`` returning canned responses."""

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


# ---------------------------------------------------------------------------
# Sample HTML fixtures
# ---------------------------------------------------------------------------

ADVANTAGE_INDEX_HTML = textwrap.dedent(f"""\
    <html>
    <head><title>Advantage Index - BASIS International</title></head>
    <body>
    <nav><ul><li>Nav link</li></ul></nav>
    <div class="entry-content">
      <h1>Advantage Magazine Articles</h1>
      <a href="{_ADV_ART1}">Article One</a>
      <a href="{_ADV_ART2}">Article Two</a>
      <a href="{INDEX_URL_ADV}">Index</a>
    </div>
    </body>
    </html>
""")

ADVANTAGE_ARTICLE_HTML = textwrap.dedent("""\
    <html>
    <head><title>Article One - BASIS International</title></head>
    <body>
    <header><div class="site-header">Site Header</div></header>
    <nav><ul><li>Menu</li></ul></nav>
    <div class="entry-content">
      <h1>Article One</h1>
      <p>This is the article content about BBj development.</p>
      <p>It has multiple paragraphs of useful information.</p>
    </div>
    <footer><div class="site-footer">Site Footer</div></footer>
    </body>
    </html>
""")

ADVANTAGE_ARTICLE_TWO_HTML = textwrap.dedent("""\
    <html>
    <head><title>Article Two - BASIS International</title></head>
    <body>
    <div class="entry-content">
      <h1>Article Two</h1>
      <p>Second article content here.</p>
    </div>
    </body>
    </html>
""")

ADVANTAGE_EMPTY_ARTICLE_HTML = textwrap.dedent("""\
    <html>
    <head><title>Empty - BASIS International</title></head>
    <body>
    <header>Header</header>
    <nav>Nav</nav>
    <footer>Footer</footer>
    </body>
    </html>
""")

KB_INDEX_HTML = textwrap.dedent(f"""\
    <html>
    <head><title>Knowledge Base - BASIS International</title></head>
    <body>
    <nav><ul><li>Nav</li></ul></nav>
    <main>
      <h1>Knowledge Base</h1>
      <a href="{_KB_ART1}">Getting Started</a>
      <a href="{_KB_ART2}">Advanced Topics</a>
    </main>
    </body>
    </html>
""")

KB_ARTICLE_HTML = textwrap.dedent("""\
    <html>
    <head><title>Getting Started - BASIS International</title></head>
    <body>
    <header><div class="site-header">Site Header</div></header>
    <div id="eckb-article-body">
      <h1>Getting Started</h1>
      <p>This is a Knowledge Base lesson about getting started.</p>
      <p>Follow these steps to begin.</p>
    </div>
    <div class="sidebar">Sidebar Content</div>
    <footer>Footer</footer>
    </body>
    </html>
""")

KB_ARTICLE_TWO_HTML = textwrap.dedent("""\
    <html>
    <head><title>Advanced Topics - BASIS International</title></head>
    <body>
    <div id="eckb-article-body">
      <h1>Advanced Topics</h1>
      <p>Advanced content for experienced users.</p>
    </div>
    </body>
    </html>
""")

KB_ARTICLE_WITH_MEDIA_HTML = textwrap.dedent("""\
    <html>
    <head><title>Media Test - BASIS International</title></head>
    <body>
    <div id="eckb-article-body">
      <h1>Media Test</h1>
      <p>Text before media.</p>
      <img src="screenshot.png" alt="Screenshot" />
      <video src="demo.mp4">Video</video>
      <audio src="audio.mp3">Audio</audio>
      <p>Text after media.</p>
    </div>
    </body>
    </html>
""")

SITEMAP_XML_ADVANTAGE = textwrap.dedent(f"""\
    <?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>{_ADV_SM1}</loc></url>
      <url><loc>{_ADV_SM2}</loc></url>
      <url><loc>https://basis.cloud/about/</loc></url>
    </urlset>
""")

SITEMAP_ARTICLE_HTML = textwrap.dedent("""\
    <html>
    <head><title>Sitemap Article One - BASIS International</title></head>
    <body>
    <div class="entry-content">
      <h1>Sitemap Article One</h1>
      <p>Discovered via sitemap fallback.</p>
    </div>
    </body>
    </html>
""")


def _adv_url_map() -> dict[str, str]:
    """Standard Advantage URL map with 2 articles."""
    return {
        INDEX_URL_ADV: ADVANTAGE_INDEX_HTML,
        _ADV_ART1: ADVANTAGE_ARTICLE_HTML,
        _ADV_ART2: ADVANTAGE_ARTICLE_TWO_HTML,
    }


def _kb_url_map() -> dict[str, str]:
    """Standard KB URL map with 2 articles."""
    return {
        INDEX_URL_KB: KB_INDEX_HTML,
        _KB_ART1: KB_ARTICLE_HTML,
        _KB_ART2: KB_ARTICLE_TWO_HTML,
    }


# ---------------------------------------------------------------------------
# AdvantageParser tests
# ---------------------------------------------------------------------------


class TestAdvantageProtocol:
    def test_advantage_parser_implements_protocol(self):
        """AdvantageParser satisfies the DocumentParser protocol."""
        assert isinstance(AdvantageParser(), DocumentParser)


class TestAdvantageDiscovery:
    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_advantage_discovers_article_urls(self, _mock_sleep):
        """Index page links with /advantage/ are discovered."""
        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(
                {
                    INDEX_URL_ADV: ADVANTAGE_INDEX_HTML,
                }
            )

            # Access static method to test discovery
            urls = AdvantageParser._discover_article_urls(instance, INDEX_URL_ADV)

        assert len(urls) == 2
        assert _ADV_ART1 in urls
        assert _ADV_ART2 in urls

    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_advantage_sitemap_fallback(self, _mock_sleep):
        """When index page has no links, sitemap.xml is tried."""
        empty_index = textwrap.dedent("""\
            <html><body>
            <div class="entry-content"><p>No links here.</p></div>
            </body></html>
        """)

        url_map = {
            INDEX_URL_ADV: empty_index,
            _ADV_SITEMAP: SITEMAP_XML_ADVANTAGE,
            _ADV_SM1: SITEMAP_ARTICLE_HTML,
            _ADV_SM2: SITEMAP_ARTICLE_HTML,
        }

        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(url_map)

            parser = AdvantageParser(index_url=INDEX_URL_ADV, rate_limit=0.0)
            docs = list(parser.parse())

        assert len(docs) == 2
        urls = [d.source_url for d in docs]
        assert _ADV_SM1 in urls
        assert _ADV_SM2 in urls


class TestAdvantageContent:
    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_advantage_strips_chrome(self, _mock_sleep):
        """Nav, header, footer, sidebar are stripped from article."""
        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(_adv_url_map())

            parser = AdvantageParser(index_url=INDEX_URL_ADV, rate_limit=0.0)
            docs = list(parser.parse())

        article_one = next(d for d in docs if d.title == "Article One")
        assert "article content about BBj" in article_one.content
        assert "Site Header" not in article_one.content
        assert "Site Footer" not in article_one.content
        assert "Menu" not in article_one.content

    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_advantage_yields_documents(self, _mock_sleep):
        """Full parse flow yields correct number of Documents."""
        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(_adv_url_map())

            parser = AdvantageParser(index_url=INDEX_URL_ADV, rate_limit=0.0)
            docs = list(parser.parse())

        assert len(docs) == 2
        titles = {d.title for d in docs}
        assert "Article One" in titles
        assert "Article Two" in titles

    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_advantage_sets_doc_type_article(self, _mock_sleep):
        """Advantage documents have doc_type='article'."""
        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(_adv_url_map())

            parser = AdvantageParser(index_url=INDEX_URL_ADV, rate_limit=0.0)
            docs = list(parser.parse())

        for doc in docs:
            assert doc.doc_type == "article"

    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_advantage_context_header(self, _mock_sleep):
        """Context header follows 'Advantage Magazine > {title}'."""
        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(_adv_url_map())

            parser = AdvantageParser(index_url=INDEX_URL_ADV, rate_limit=0.0)
            docs = list(parser.parse())

        article_one = next(d for d in docs if d.title == "Article One")
        assert article_one.context_header == ("Advantage Magazine > Article One")

    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_advantage_skips_empty_articles(self, _mock_sleep):
        """Articles with no content after stripping yield nothing."""
        index_with_empty = textwrap.dedent(f"""\
            <html><body>
            <div class="entry-content">
              <a href="{_ADV_EMPTY}">Empty</a>
            </div>
            </body></html>
        """)

        url_map = {
            INDEX_URL_ADV: index_with_empty,
            _ADV_EMPTY: ADVANTAGE_EMPTY_ARTICLE_HTML,
        }

        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(url_map)

            parser = AdvantageParser(index_url=INDEX_URL_ADV, rate_limit=0.0)
            docs = list(parser.parse())

        assert len(docs) == 0


# ---------------------------------------------------------------------------
# KnowledgeBaseParser tests
# ---------------------------------------------------------------------------


class TestKBProtocol:
    def test_kb_parser_implements_protocol(self):
        """KnowledgeBaseParser satisfies the DocumentParser protocol."""
        assert isinstance(KnowledgeBaseParser(), DocumentParser)


class TestKBDiscovery:
    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_kb_discovers_article_urls(self, _mock_sleep):
        """Index page links with /knowledge-base/kb{N}/ found."""
        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(
                {
                    INDEX_URL_KB: KB_INDEX_HTML,
                }
            )

            urls = KnowledgeBaseParser._discover_kb_urls(instance, INDEX_URL_KB)

        assert len(urls) == 2
        assert any("kb01069" in u for u in urls)
        assert any("kb01070" in u for u in urls)


class TestKBContent:
    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_kb_uses_eckb_content_selector(self, _mock_sleep):
        """Content extracted from #eckb-article-body container."""
        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(_kb_url_map())

            parser = KnowledgeBaseParser(index_url=INDEX_URL_KB, rate_limit=0.0)
            docs = list(parser.parse())

        gs = next(d for d in docs if d.title == "Getting Started")
        assert "getting started" in gs.content.lower()
        # Sidebar should be stripped
        assert "Sidebar Content" not in gs.content

    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_kb_yields_documents(self, _mock_sleep):
        """Full parse flow yields correct number of Documents."""
        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(_kb_url_map())

            parser = KnowledgeBaseParser(index_url=INDEX_URL_KB, rate_limit=0.0)
            docs = list(parser.parse())

        assert len(docs) == 2
        titles = {d.title for d in docs}
        assert "Getting Started" in titles
        assert "Advanced Topics" in titles

    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_kb_sets_doc_type_concept(self, _mock_sleep):
        """KB documents have doc_type='concept'."""
        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(_kb_url_map())

            parser = KnowledgeBaseParser(index_url=INDEX_URL_KB, rate_limit=0.0)
            docs = list(parser.parse())

        for doc in docs:
            assert doc.doc_type == "concept"

    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_kb_context_header(self, _mock_sleep):
        """Context header follows 'Knowledge Base > {title}'."""
        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(_kb_url_map())

            parser = KnowledgeBaseParser(index_url=INDEX_URL_KB, rate_limit=0.0)
            docs = list(parser.parse())

        gs = next(d for d in docs if d.title == "Getting Started")
        assert gs.context_header == ("Knowledge Base > Getting Started")

    @patch("bbj_rag.parsers.wordpress.time.sleep")
    def test_kb_strips_media(self, _mock_sleep):
        """Image, video, and audio tags are removed."""
        kb_index_media = textwrap.dedent(f"""\
            <html><body><main>
            <a href="{_KB_MEDIA}">Media Test</a>
            </main></body></html>
        """)

        url_map = {
            INDEX_URL_KB: kb_index_media,
            _KB_MEDIA: KB_ARTICLE_WITH_MEDIA_HTML,
        }

        with patch("httpx.Client") as MockClient:
            instance = MockClient.return_value.__enter__.return_value
            instance.get.side_effect = _mock_get(url_map)

            parser = KnowledgeBaseParser(index_url=INDEX_URL_KB, rate_limit=0.0)
            docs = list(parser.parse())

        assert len(docs) == 1
        content = docs[0].content
        assert "Text before media" in content
        assert "Text after media" in content
        assert "screenshot.png" not in content
        assert "demo.mp4" not in content
        assert "audio.mp3" not in content


# ---------------------------------------------------------------------------
# Shared helper tests
# ---------------------------------------------------------------------------


class TestStripWpChrome:
    def test_strip_wp_chrome_removes_boilerplate(self):
        """_strip_wp_chrome removes nav, header, footer, sidebar."""
        html = textwrap.dedent("""\
            <html><body>
            <nav><ul><li>Nav link</li></ul></nav>
            <header><div class="site-header">Header</div></header>
            <div class="sidebar">Sidebar stuff</div>
            <div class="entry-content"><p>Real content here.</p></div>
            <footer><div class="site-footer">Footer</div></footer>
            <div class="comments-area">Comments</div>
            <div class="widget-area">Widgets</div>
            </body></html>
        """)
        soup = _soup(html)
        _strip_wp_chrome(soup)
        text = soup.get_text()

        assert "Real content here" in text
        assert "Nav link" not in text
        assert "Header" not in text
        assert "Sidebar stuff" not in text
        assert "Footer" not in text
        assert "Comments" not in text
        assert "Widgets" not in text
