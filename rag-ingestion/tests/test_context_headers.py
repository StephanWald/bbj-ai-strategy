"""Tests for the BBj Intelligence contextual header builder.

Covers build_context_header() with various input combinations,
extract_heading_hierarchy() for markdown parsing, and
url_path_to_hierarchy() for web crawl delegation.
"""

from __future__ import annotations

from bbj_rag.intelligence.context_headers import (
    build_context_header,
    extract_heading_hierarchy,
    url_path_to_hierarchy,
)

# ---------------------------------------------------------------------------
# build_context_header tests
# ---------------------------------------------------------------------------


class TestBuildContextHeader:
    def test_build_header_full(self):
        """section_path + title + heading_path -> full arrow chain."""
        result = build_context_header("A > B", "C", "D")
        assert result == "A > B > C > D"

    def test_build_header_no_heading_path(self):
        """section_path + title -> two-level chain."""
        result = build_context_header("Language > BBjAPI > BBjWindow", "addButton")
        assert result == "Language > BBjAPI > BBjWindow > addButton"

    def test_build_header_title_dedup(self):
        """section_path ending with title -> title not repeated."""
        result = build_context_header("A > B > C", "C", "")
        assert result == "A > B > C"

    def test_build_header_no_section_path(self):
        """Empty section_path + title -> just title."""
        result = build_context_header("", "MyPage", "")
        assert result == "MyPage"

    def test_build_header_all_empty(self):
        """All empty inputs -> empty string."""
        result = build_context_header("", "", "")
        assert result == ""

    def test_build_header_web_crawl_style(self):
        """URL-derived section path + title -> arrow-separated."""
        result = build_context_header(
            "bbjobjects > Window > bbjwindow", "addButton", ""
        )
        assert result == "bbjobjects > Window > bbjwindow > addButton"

    def test_build_header_heading_path_only(self):
        """Empty section_path + empty title + heading_path -> just heading."""
        result = build_context_header("", "", "Parameters")
        assert result == "Parameters"

    def test_build_header_title_with_heading(self):
        """Empty section_path + title + heading_path -> title > heading."""
        result = build_context_header("", "MyPage", "Parameters")
        assert result == "MyPage > Parameters"


# ---------------------------------------------------------------------------
# extract_heading_hierarchy tests
# ---------------------------------------------------------------------------


class TestExtractHeadingHierarchy:
    def test_extract_heading_hierarchy_basic(self):
        """Markdown with ## headings -> list of heading text."""
        content = "## Description\n\nSome text\n\n## Syntax\n\n## Parameters\n"
        result = extract_heading_hierarchy(content)
        assert result == ["Description", "Syntax", "Parameters"]

    def test_extract_heading_hierarchy_mixed_levels(self):
        """Mixed heading levels -> flat list preserving order."""
        content = "# Title\n\nIntro\n\n## Section\n\nText\n\n### Subsection\n"
        result = extract_heading_hierarchy(content)
        assert result == ["Title", "Section", "Subsection"]

    def test_extract_heading_hierarchy_no_headings(self):
        """Plain text without headings -> empty list."""
        content = "This is plain text.\nNo headings here.\n"
        result = extract_heading_hierarchy(content)
        assert result == []

    def test_extract_heading_hierarchy_strips_whitespace(self):
        """Headings with trailing spaces -> cleaned text."""
        content = "## Description   \n\n## Syntax  \n"
        result = extract_heading_hierarchy(content)
        assert result == ["Description", "Syntax"]

    def test_extract_heading_hierarchy_h4_through_h6(self):
        """Deep headings (h4-h6) are also extracted."""
        content = "#### Deep\n##### Deeper\n###### Deepest\n"
        result = extract_heading_hierarchy(content)
        assert result == ["Deep", "Deeper", "Deepest"]


# ---------------------------------------------------------------------------
# url_path_to_hierarchy tests
# ---------------------------------------------------------------------------

_BASE = "https://documentation.basis.cloud/BASISHelp/WebHelp/"


class TestUrlPathToHierarchy:
    def test_url_path_to_hierarchy(self):
        """Full URL -> arrow-separated path (delegates to web_crawl)."""
        url = _BASE + "bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm"
        result = url_path_to_hierarchy(url, _BASE)
        assert result == "bbjobjects > Window > bbjwindow"

    def test_url_path_to_hierarchy_root(self):
        """Base URL itself -> empty string."""
        result = url_path_to_hierarchy(_BASE, _BASE)
        assert result == ""
