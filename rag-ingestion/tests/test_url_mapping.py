"""Unit tests for URL mapping: source type classification and display URL generation."""

from __future__ import annotations

import pytest

from bbj_rag.url_mapping import classify_source_type, map_display_url

# -- classify_source_type tests --


@pytest.mark.parametrize(
    "source_url, expected",
    [
        ("flare://Content/bbjobjects/bbjapi/bbjapi.htm", "flare"),
        ("pdf://GuideToGuiProgrammingInBBj.pdf#some-slug", "pdf"),
        ("file://samples/DWCNavigator.bbj", "bbj_source"),
        ("mdx-dwc://components/button.mdx", "mdx"),
        ("mdx-beginner://intro/getting-started.mdx", "mdx"),
        ("mdx-db-modernization://overview.mdx", "mdx"),
        ("https://basis.cloud/advantage/some-article/", "wordpress"),
        ("https://basis.cloud/knowledge-base/kb01220/", "wordpress"),
        (
            "https://documentation.basis.cloud/BASISHelp/WebHelp/gridctrl/grid.htm",
            "web_crawl",
        ),
        ("some://other", "unknown"),
        ("", "unknown"),
    ],
    ids=[
        "flare",
        "pdf",
        "bbj_source",
        "mdx-dwc",
        "mdx-beginner",
        "mdx-db-modernization",
        "wordpress-advantage",
        "wordpress-kb",
        "web_crawl",
        "unknown-scheme",
        "empty-string",
    ],
)
def test_classify_source_type(source_url: str, expected: str) -> None:
    """classify_source_type returns correct label for each source prefix."""
    assert classify_source_type(source_url) == expected


# -- map_display_url tests --


def test_display_url_flare():
    """Flare URLs are mapped to documentation.basis.cloud HTTPS URLs."""
    result = map_display_url("flare://Content/bbjobjects/bbjapi/bbjapi.htm")
    assert (
        result
        == "https://documentation.basis.cloud/BASISHelp/WebHelp/bbjobjects/bbjapi/bbjapi.htm"
    )


def test_display_url_flare_nested():
    """Flare URLs with deep paths are mapped correctly."""
    result = map_display_url(
        "flare://Content/gridctrl/BBjGridExWidget/BBjGridExWidget.htm"
    )
    assert (
        result
        == "https://documentation.basis.cloud/BASISHelp/WebHelp/gridctrl/BBjGridExWidget/BBjGridExWidget.htm"
    )


def test_display_url_https_passthrough_wordpress():
    """WordPress HTTPS URLs are returned as-is."""
    url = "https://basis.cloud/advantage/some-article/"
    assert map_display_url(url) == url


def test_display_url_https_passthrough_kb():
    """Knowledge base HTTPS URLs are returned as-is."""
    url = "https://basis.cloud/knowledge-base/kb01220/"
    assert map_display_url(url) == url


def test_display_url_https_passthrough_web_crawl():
    """Web crawl HTTPS URLs are returned as-is."""
    url = "https://documentation.basis.cloud/BASISHelp/WebHelp/gridctrl/grid.htm"
    assert map_display_url(url) == url


def test_display_url_pdf_bracketed():
    """PDF URLs are returned wrapped in brackets."""
    url = "pdf://GuideToGuiProgrammingInBBj.pdf#some-slug"
    assert map_display_url(url) == f"[{url}]"


def test_display_url_file_bracketed():
    """BBj source file:// URLs are returned wrapped in brackets."""
    url = "file://samples/DWCNavigator.bbj"
    assert map_display_url(url) == f"[{url}]"


def test_display_url_mdx_bracketed():
    """MDX URLs are returned wrapped in brackets."""
    for url in [
        "mdx-dwc://components/button.mdx",
        "mdx-beginner://intro/getting-started.mdx",
        "mdx-db-modernization://overview.mdx",
    ]:
        assert map_display_url(url) == f"[{url}]"


def test_display_url_unknown_bracketed():
    """Unknown scheme URLs are returned wrapped in brackets."""
    url = "some://other"
    assert map_display_url(url) == f"[{url}]"
