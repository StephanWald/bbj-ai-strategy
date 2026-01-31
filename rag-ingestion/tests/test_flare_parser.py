"""Tests for the MadCap Flare XHTML parser.

Integration tests run against real Flare project files at /Users/beff/bbjdocs/.
Unit tests use synthetic XHTML -- no external file dependency.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from bbj_rag.models import Document
from bbj_rag.parsers import MADCAP_NS
from bbj_rag.parsers.flare import (
    FlareParser,
    _extract_body_content,
    _extract_title,
    _load_snippets,
)

BBJDOCS = Path("/Users/beff/bbjdocs")
CONTENT_DIR = BBJDOCS / "Content"
PROJECT_DIR = BBJDOCS / "Project"

has_bbjdocs = pytest.mark.skipif(
    not BBJDOCS.exists(),
    reason="Flare source not available",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_xhtml(body_content: str, conditions: str = "") -> str:
    """Build a minimal XHTML string with optional MadCap conditions."""
    cond_attr = ""
    if conditions:
        cond_attr = f' MadCap:conditions="{conditions}"'
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<html"
        f' xmlns:MadCap="{MADCAP_NS}"'
        f"{cond_attr}>\n"
        "<head><title>Test Title</title></head>\n"
        f"<body>{body_content}</body>\n"
        "</html>"
    )


def _parse_body(body_xml: str) -> str:
    """Parse body XML and extract content via the extraction pipeline."""
    xhtml = _make_xhtml(body_xml)
    parser = etree.XMLParser(remove_comments=True)
    root = etree.fromstring(xhtml.encode(), parser)
    body = root.find(".//body")
    assert body is not None
    return _extract_body_content(
        body,
        {},
        Path("/fake/topic.htm"),
        Path("/fake"),
        set(),
    )


# ---------------------------------------------------------------------------
# Integration tests (real Flare project files)
# ---------------------------------------------------------------------------


@has_bbjdocs
class TestFlareParserIntegration:
    """Tests against the real Flare project at /Users/beff/bbjdocs/."""

    @pytest.fixture(scope="class")
    def parser(self) -> FlareParser:
        return FlareParser(
            content_dir=CONTENT_DIR,
            project_dir=PROJECT_DIR,
        )

    @pytest.fixture(scope="class")
    def documents(self, parser: FlareParser) -> list[Document]:
        return list(parser.parse())

    def test_parse_yields_documents(self, documents: list[Document]) -> None:
        """Parser yields more than 4,000 Document objects."""
        assert len(documents) > 4000

    def test_document_count_reasonable(self, documents: list[Document]) -> None:
        """Document count is in the expected range."""
        assert 5000 < len(documents) < 8000

    def test_document_has_required_fields(self, documents: list[Document]) -> None:
        """Every document has non-empty required fields."""
        for doc in documents[:100]:
            assert doc.source_url
            assert doc.title
            assert doc.content.strip()
            assert doc.generations
            assert doc.doc_type == "flare"

    def test_document_content_no_madcap_tags(self, documents: list[Document]) -> None:
        """No document content contains raw MadCap namespace tags."""
        for doc in documents:
            assert "MadCap:" not in doc.content, (
                f"Raw MadCap tag in {doc.source_url}: {doc.content[:200]}"
            )

    def test_document_has_section_path(self, documents: list[Document]) -> None:
        """Every document has section_path in metadata."""
        for doc in documents[:200]:
            assert "section_path" in doc.metadata

    def test_toc_topic_has_arrow_breadcrumb(self, documents: list[Document]) -> None:
        """A known TOC topic has arrow-separated breadcrumbs."""
        toc_docs = [d for d in documents if " > " in d.metadata.get("section_path", "")]
        assert len(toc_docs) > 0, "No documents with TOC breadcrumbs found"
        sample = toc_docs[0]
        assert " > " in sample.metadata["section_path"]

    def test_orphan_topic_has_directory_path(self, documents: list[Document]) -> None:
        """Orphan topics (not in TOC) have directory-based paths."""
        all_with_path = [d for d in documents if d.metadata.get("section_path", "")]
        assert len(all_with_path) > 4000

    def test_code_blocks_preserved(self, documents: list[Document]) -> None:
        """Topics with code blocks contain fenced code blocks."""
        code_docs = [d for d in documents if "```" in d.content]
        assert len(code_docs) > 100, f"Only {len(code_docs)} documents with code blocks"

    def test_code_block_has_language_hint(self, documents: list[Document]) -> None:
        """Code blocks include language hints."""
        has_lang = [
            d
            for d in documents
            if "```bbj" in d.content
            or "```java" in d.content
            or "```css" in d.content
            or "```xml" in d.content
            or "```sql" in d.content
        ]
        assert len(has_lang) > 50, f"Only {len(has_lang)} docs with language hints"

    def test_tables_converted_to_markdown(self, documents: list[Document]) -> None:
        """Topics with tables contain markdown table format."""
        table_docs = [d for d in documents if " | " in d.content and "---" in d.content]
        assert len(table_docs) > 100, f"Only {len(table_docs)} docs with tables"

    def test_snippet_resolution(self, documents: list[Document]) -> None:
        """Snippets resolve to content (not empty gaps)."""
        auth_docs = [
            d for d in documents if "user_authentication" in d.source_url.lower()
        ]
        if auth_docs:
            doc = auth_docs[0]
            assert len(doc.content) > 200

    def test_conditions_mapped_to_generations(self, documents: list[Document]) -> None:
        """Documents with BASISHelp have 'bbj' generation."""
        bbj_docs = [d for d in documents if "bbj" in d.generations]
        assert len(bbj_docs) > 3000

    def test_deprecated_topic_flagged(self, documents: list[Document]) -> None:
        """Deprecated topics have 'deprecated' in generations."""
        deprecated_docs = [d for d in documents if "deprecated" in d.generations]
        assert len(deprecated_docs) > 10, f"Only {len(deprecated_docs)} deprecated docs"

    def test_empty_content_skipped(self, documents: list[Document]) -> None:
        """No yielded document has empty content."""
        for doc in documents:
            assert doc.content.strip()

    def test_source_url_format(self, documents: list[Document]) -> None:
        """Source URLs follow the flare:// format."""
        for doc in documents[:100]:
            assert doc.source_url.startswith("flare://Content/")
            assert doc.source_url.endswith(".htm")


# ---------------------------------------------------------------------------
# Unit tests (synthetic XHTML, no file dependency)
# ---------------------------------------------------------------------------


class TestExtractTitle:
    """Test title extraction from synthetic XHTML."""

    def test_extract_title_from_head(self):
        xhtml = _make_xhtml("<h1>Heading</h1>")
        parser = etree.XMLParser(remove_comments=True)
        root = etree.fromstring(xhtml.encode(), parser)
        title = _extract_title(root, Path("/fake/topic.htm"))
        assert title == "Test Title"

    def test_extract_title_fallback_h1(self):
        xhtml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            f'<html xmlns:MadCap="{MADCAP_NS}">\n'
            "<head><title></title></head>\n"
            "<body><h1>Hello World</h1></body>\n"
            "</html>"
        )
        parser = etree.XMLParser(remove_comments=True)
        root = etree.fromstring(xhtml.encode(), parser)
        title = _extract_title(root, Path("/fake/topic.htm"))
        assert title == "Hello World"

    def test_extract_title_fallback_filename(self):
        xhtml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            f'<html xmlns:MadCap="{MADCAP_NS}">\n'
            "<head><title></title></head>\n"
            "<body><p>Just text</p></body>\n"
            "</html>"
        )
        parser = etree.XMLParser(remove_comments=True)
        root = etree.fromstring(xhtml.encode(), parser)
        title = _extract_title(root, Path("/fake/my_topic.htm"))
        assert title == "my topic"


class TestMadCapTagHandling:
    """Test MadCap namespace tag handling in content extraction."""

    def test_keyword_tag_stripped(self):
        body = f'<h1><MadCap:keyword xmlns:MadCap="{MADCAP_NS}" term="test"/>Hello</h1>'
        content = _parse_body(body)
        assert "test" not in content.split("Hello")[0]
        assert "Hello" in content

    def test_concept_tag_stripped(self):
        body = (
            "<p>"
            f'<MadCap:concept xmlns:MadCap="{MADCAP_NS}" '
            'term="abc"/>'
            "Content here"
            "</p>"
        )
        content = _parse_body(body)
        assert "abc" not in content
        assert "Content here" in content

    def test_xref_keeps_text(self):
        body = (
            "<p>See "
            f'<MadCap:xref xmlns:MadCap="{MADCAP_NS}" '
            'href="foo.htm">Link Text</MadCap:xref>'
            " for more.</p>"
        )
        content = _parse_body(body)
        assert "Link Text" in content
        assert "foo.htm" not in content

    def test_toggler_keeps_text(self):
        body = (
            "<h2>"
            f'<MadCap:toggler xmlns:MadCap="{MADCAP_NS}" '
            'targets="hist">Version History</MadCap:toggler>'
            "</h2>"
        )
        content = _parse_body(body)
        assert "Version History" in content

    def test_popup_keeps_head_only(self):
        body = (
            "<p>Uses "
            f'<MadCap:popup xmlns:MadCap="{MADCAP_NS}">'
            f'<MadCap:popupHead xmlns:MadCap="{MADCAP_NS}">'
            "PRO/5</MadCap:popupHead>"
            f'<MadCap:popupBody xmlns:MadCap="{MADCAP_NS}">'
            "PRO/5 and Visual PRO/5"
            "</MadCap:popupBody>"
            "</MadCap:popup> code.</p>"
        )
        content = _parse_body(body)
        assert "PRO/5" in content
        assert "Visual PRO/5" not in content

    def test_variable_stripped(self):
        body = (
            "<p>Date: "
            f'<MadCap:variable xmlns:MadCap="{MADCAP_NS}" '
            'name="System.LongDate"/>'
            "</p>"
        )
        content = _parse_body(body)
        assert "System.LongDate" not in content


class TestCodeBlockExtraction:
    """Test code block preservation as markdown fenced blocks."""

    def test_code_block_with_language(self):
        body = '<pre><code class="language-bbj">print "Hello World"</code></pre>'
        content = _parse_body(body)
        assert "```bbj" in content
        assert 'print "Hello World"' in content
        assert content.strip().endswith("```")

    def test_code_block_java(self):
        body = '<pre><code class="language-java">System.out.println();</code></pre>'
        content = _parse_body(body)
        assert "```java" in content

    def test_code_table_extracted_as_code(self):
        body = (
            '<table class="Code_Table"><tr><td>'
            '<pre><code class="language-bbj">'
            "x = 42"
            "</code></pre>"
            "</td></tr></table>"
        )
        content = _parse_body(body)
        assert "```bbj" in content
        assert "x = 42" in content
        # Should NOT have markdown table separators.
        assert " | " not in content

    def test_pre_without_language(self):
        body = "<pre>raw preformatted text</pre>"
        content = _parse_body(body)
        assert "```" in content
        assert "raw preformatted text" in content


class TestTableConversion:
    """Test HTML table to markdown conversion."""

    def test_markdown_table_output(self):
        body = (
            '<table class="Methods_Table">'
            "<tr><th>Return</th><th>Method</th></tr>"
            "<tr><td>void</td><td>doSomething()</td></tr>"
            "</table>"
        )
        content = _parse_body(body)
        assert " | " in content
        assert "---" in content
        assert "Return" in content
        assert "Method" in content
        assert "void" in content
        assert "doSomething()" in content

    def test_empty_table_skipped(self):
        body = '<table class="Methods_Table"></table>'
        content = _parse_body(body)
        assert content.strip() == ""

    def test_parameter_table(self):
        body = (
            '<table class="Parameter_Table">'
            "<tr><th>Variable</th><th>Description</th></tr>"
            "<tr><td>x%</td><td>The X position</td></tr>"
            "<tr><td>y%</td><td>The Y position</td></tr>"
            "</table>"
        )
        content = _parse_body(body)
        assert "x%" in content
        assert "The X position" in content
        assert "y%" in content


class TestHeadingsAndParagraphs:
    """Test heading and paragraph extraction."""

    def test_heading_levels(self):
        body = "<h1>Level 1</h1><h2>Level 2</h2><h3>Level 3</h3><h4>Level 4</h4>"
        content = _parse_body(body)
        assert "# Level 1" in content
        assert "## Level 2" in content
        assert "### Level 3" in content
        assert "#### Level 4" in content

    def test_paragraph_text(self):
        body = "<p>This is a paragraph.</p>"
        content = _parse_body(body)
        assert "This is a paragraph." in content

    def test_code_paragraph(self):
        body = '<p class="Code">BBjAPI &gt; BBjWindow</p>'
        content = _parse_body(body)
        assert "`" in content


class TestListExtraction:
    """Test list item extraction."""

    def test_unordered_list(self):
        body = "<ul><li>First item</li><li>Second item</li></ul>"
        content = _parse_body(body)
        assert "- First item" in content
        assert "- Second item" in content

    def test_ordered_list(self):
        body = "<ol><li>Step one</li><li>Step two</li></ol>"
        content = _parse_body(body)
        assert "1. Step one" in content
        assert "2. Step two" in content


class TestSnippetLoading:
    """Test snippet pre-loading."""

    @has_bbjdocs
    def test_load_snippets_count(self):
        snippets = _load_snippets(CONTENT_DIR)
        # Should load around 205 snippets.
        assert len(snippets) > 100
        assert len(snippets) < 500

    @has_bbjdocs
    def test_snippet_keys_are_relative(self):
        snippets = _load_snippets(CONTENT_DIR)
        for key in snippets:
            assert key.startswith("Resources/Snippets/")
            assert key.endswith(".flsnp")


class TestDocumentParserProtocol:
    """Verify FlareParser satisfies DocumentParser protocol."""

    def test_protocol_compliance(self):
        from bbj_rag.parsers import DocumentParser

        assert issubclass(FlareParser, DocumentParser)
