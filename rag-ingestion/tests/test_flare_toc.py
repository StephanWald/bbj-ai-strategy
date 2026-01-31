"""Tests for the TOC index builder.

Includes both unit tests using synthetic XML and integration tests
against the real Flare project at /Users/beff/bbjdocs/.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from bbj_rag.parsers.flare_toc import (
    build_toc_index,
    directory_fallback_path,
)

FLARE_SOURCE = Path("/Users/beff/bbjdocs")
skip_no_flare = pytest.mark.skipif(
    not FLARE_SOURCE.exists(),
    reason="Flare source not available",
)


# ---------------------------------------------------------------------------
# Unit tests with synthetic XML (no file dependency)
# ---------------------------------------------------------------------------


def _write_toc(tmp_path: Path, filename: str, xml: str) -> None:
    """Write a .fltoc file to tmp_path."""
    (tmp_path / filename).write_text(xml, encoding="utf-8")


class TestBuildTocIndexSynthetic:
    """Unit tests using in-memory .fltoc XML."""

    def test_empty_toc(self, tmp_path):
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<CatapultToc Version="1"></CatapultToc>'
        )
        _write_toc(tmp_path, "basishelp.fltoc", xml)
        index = build_toc_index(tmp_path)
        assert index == {}

    def test_single_entry(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <CatapultToc Version="1">
              <TocEntry Title="Home" Link="/Content/index.htm"/>
            </CatapultToc>
        """)
        _write_toc(tmp_path, "basishelp.fltoc", xml)
        index = build_toc_index(tmp_path)
        assert index == {"index.htm": "Home"}

    def test_nested_breadcrumbs(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <CatapultToc Version="1">
              <TocEntry Title="Language">
                <TocEntry Title="Objects">
                  <TocEntry Title="BBjWindow"
                    Link="/Content/bbjobjects/Window/bbjwindow.htm"/>
                </TocEntry>
              </TocEntry>
            </CatapultToc>
        """)
        _write_toc(tmp_path, "basishelp.fltoc", xml)
        index = build_toc_index(tmp_path)
        key = "bbjobjects/Window/bbjwindow.htm"
        assert index[key] == "Language > Objects > BBjWindow"

    def test_section_only_entries_no_link(self, tmp_path):
        """Section-only entries (no Link) contribute breadcrumbs only."""
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <CatapultToc Version="1">
              <TocEntry Title="Section Header">
                <TocEntry Title="Topic" Link="/Content/topic.htm"/>
              </TocEntry>
            </CatapultToc>
        """)
        _write_toc(tmp_path, "basishelp.fltoc", xml)
        index = build_toc_index(tmp_path)
        # The section header itself has no link, so no index entry for it
        assert len(index) == 1
        assert index["topic.htm"] == "Section Header > Topic"

    def test_priority_first_found_wins(self, tmp_path):
        """basishelp wins over pro5toc for the same topic path."""
        xml_basis = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <CatapultToc Version="1">
              <TocEntry Title="Basis Path" Link="/Content/shared.htm"/>
            </CatapultToc>
        """)
        xml_pro5 = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <CatapultToc Version="1">
              <TocEntry Title="Pro5 Path" Link="/Content/shared.htm"/>
            </CatapultToc>
        """)
        _write_toc(tmp_path, "basishelp.fltoc", xml_basis)
        _write_toc(tmp_path, "pro5toc.fltoc", xml_pro5)
        index = build_toc_index(tmp_path)
        assert index["shared.htm"] == "Basis Path"

    def test_linked_title_resolution(self, tmp_path):
        """[%=System.LinkedTitle%] resolves from the topic <title> tag."""
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <CatapultToc Version="1">
              <TocEntry Title="[%=System.LinkedTitle%]" Link="/Content/topic.htm"
                xmlns:MadCap="http://www.madcapsoftware.com/Schemas/MadCap.xsd"/>
            </CatapultToc>
        """)
        _write_toc(tmp_path, "basishelp.fltoc", xml)

        # Create the topic file with a <title>
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        topic = content_dir / "topic.htm"
        topic.write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<html><head><title>Resolved Title</title></head><body></body></html>",
            encoding="utf-8",
        )

        index = build_toc_index(tmp_path, content_dir=content_dir)
        assert index["topic.htm"] == "Resolved Title"

    def test_linked_title_fallback_to_h1(self, tmp_path):
        """[%=System.LinkedTitle%] falls back to <h1> when no <title>."""
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <CatapultToc Version="1">
              <TocEntry Title="[%=System.LinkedTitle%]" Link="/Content/topic.htm"
                xmlns:MadCap="http://www.madcapsoftware.com/Schemas/MadCap.xsd"/>
            </CatapultToc>
        """)
        _write_toc(tmp_path, "basishelp.fltoc", xml)

        content_dir = tmp_path / "content"
        content_dir.mkdir()
        topic = content_dir / "topic.htm"
        topic.write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<html><head></head><body><h1>H1 Title</h1></body></html>",
            encoding="utf-8",
        )

        index = build_toc_index(tmp_path, content_dir=content_dir)
        assert index["topic.htm"] == "H1 Title"

    def test_linked_title_fallback_to_filename(self, tmp_path):
        """[%=System.LinkedTitle%] falls back to filename stem when file missing."""
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <CatapultToc Version="1">
              <TocEntry Title="[%=System.LinkedTitle%]" Link="/Content/my_topic.htm"
                xmlns:MadCap="http://www.madcapsoftware.com/Schemas/MadCap.xsd"/>
            </CatapultToc>
        """)
        _write_toc(tmp_path, "basishelp.fltoc", xml)

        content_dir = tmp_path / "content"
        content_dir.mkdir()
        # Don't create the topic file

        index = build_toc_index(tmp_path, content_dir=content_dir)
        assert index["my_topic.htm"] == "my topic"

    def test_missing_toc_files_skipped(self, tmp_path):
        """Missing TOC files are silently skipped."""
        index = build_toc_index(tmp_path)
        assert index == {}

    def test_arrow_separator_in_breadcrumb(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="utf-8"?>
            <CatapultToc Version="1">
              <TocEntry Title="A">
                <TocEntry Title="B" Link="/Content/b.htm"/>
              </TocEntry>
            </CatapultToc>
        """)
        _write_toc(tmp_path, "basishelp.fltoc", xml)
        index = build_toc_index(tmp_path)
        assert " > " in index["b.htm"]


class TestDirectoryFallbackPath:
    """Unit tests for directory-based fallback hierarchy."""

    def test_nested_path(self):
        result = directory_fallback_path(
            "bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm"
        )
        assert result == "bbjobjects > Window > bbjwindow"

    def test_single_directory(self):
        result = directory_fallback_path("commands/abs_function.htm")
        assert result == "commands"

    def test_root_level_file(self):
        result = directory_fallback_path("index.htm")
        assert result == ""

    def test_two_levels(self):
        result = directory_fallback_path("em/EM-Introduction.htm")
        assert result == "em"


# ---------------------------------------------------------------------------
# Integration tests with real Flare project files
# ---------------------------------------------------------------------------


@skip_no_flare
class TestBuildTocIndexReal:
    """Integration tests against /Users/beff/bbjdocs/."""

    def test_build_toc_index_returns_dict(self):
        toc_dir = FLARE_SOURCE / "Project" / "TOCs"
        content_dir = FLARE_SOURCE / "Content"
        index = build_toc_index(toc_dir, content_dir)
        assert isinstance(index, dict)
        assert len(index) > 1000, f"Expected >1000 entries, got {len(index)}"

    def test_toc_priority_basishelp_wins(self):
        """Topics appearing in both basishelp and pro5toc get basishelp breadcrumb."""
        toc_dir = FLARE_SOURCE / "Project" / "TOCs"
        content_dir = FLARE_SOURCE / "Content"
        index = build_toc_index(toc_dir, content_dir)

        # intro_commands.htm appears in both basishelp and pro5toc
        path = "commands/intro_commands.htm"
        if path in index:
            # Should not start with "PRO/5" (which would be from pro5toc)
            assert "PRO/5 and Visual PRO/5 Manual Set" not in index[path]

    def test_toc_entry_has_arrow_separator(self):
        toc_dir = FLARE_SOURCE / "Project" / "TOCs"
        content_dir = FLARE_SOURCE / "Content"
        index = build_toc_index(toc_dir, content_dir)

        # Find an entry with depth > 1
        deep_entries = [v for v in index.values() if " > " in v]
        assert len(deep_entries) > 100, "Expected many entries with arrow separators"

    def test_section_only_entries_contribute_breadcrumbs(self):
        """Section-only entries (no Link) contribute to child breadcrumbs."""
        toc_dir = FLARE_SOURCE / "Project" / "TOCs"
        content_dir = FLARE_SOURCE / "Content"
        index = build_toc_index(toc_dir, content_dir)

        # "Earlier Versions" is a section-only entry in basishelp.fltoc
        # Its children should include it in their breadcrumb
        path = "sysadmin/install/bbj/installing_bbj_5_x_unix.htm"
        if path in index:
            assert "Earlier Versions" in index[path]

    def test_linked_title_resolution_real(self):
        """[%=System.LinkedTitle%] entries are resolved from topic files."""
        toc_dir = FLARE_SOURCE / "Project" / "TOCs"
        content_dir = FLARE_SOURCE / "Content"
        index = build_toc_index(toc_dir, content_dir)

        # basismans/Using_BASIS_Help.htm has [%=System.LinkedTitle%] in basishelp.fltoc
        path = "basismans/Using_BASIS_Help.htm"
        assert path in index
        # Should be resolved to the actual title, not the pattern
        assert "[%=System.LinkedTitle%]" not in index[path]

    def test_orphan_topic_count(self):
        """Roughly 78% of topics should be orphans (not in any TOC)."""
        toc_dir = FLARE_SOURCE / "Project" / "TOCs"
        content_dir = FLARE_SOURCE / "Content"
        index = build_toc_index(toc_dir, content_dir)

        # Count all .htm files in Content/ excluding Resources/
        all_topics = [
            p for p in content_dir.rglob("*.htm") if "Resources" not in p.parts
        ]
        total = len(all_topics)
        in_toc = sum(1 for p in all_topics if str(p.relative_to(content_dir)) in index)
        orphan_count = total - in_toc
        orphan_pct = orphan_count / total * 100 if total else 0

        assert total > 5000, f"Expected >5000 topics, got {total}"
        assert orphan_pct > 60, f"Expected >60% orphans, got {orphan_pct:.1f}%"
