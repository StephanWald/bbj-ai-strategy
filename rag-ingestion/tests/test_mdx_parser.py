"""Tests for the Docusaurus MDX parser.

Uses ``tmp_path`` to create temporary MDX files for testing.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from bbj_rag.parsers import DocumentParser
from bbj_rag.parsers.mdx import MdxParser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_file(tmp_path: Path, name: str, content: str) -> Path:
    """Write a file under *tmp_path* and return the path."""
    file_path = tmp_path / name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


# ---------------------------------------------------------------------------
# Protocol compliance
# ---------------------------------------------------------------------------


class TestMdxProtocol:
    def test_mdx_parser_implements_protocol(self, tmp_path: Path):
        """MdxParser satisfies the DocumentParser protocol."""
        assert isinstance(MdxParser(docs_dir=tmp_path), DocumentParser)


# ---------------------------------------------------------------------------
# Document yield tests
# ---------------------------------------------------------------------------


class TestMdxParsing:
    def test_mdx_parser_yields_documents(self, tmp_path: Path):
        """A .md file with frontmatter yields a Document."""
        _write_file(
            tmp_path,
            "intro.md",
            textwrap.dedent("""\
                ---
                title: Introduction
                sidebar_position: 1
                ---

                # Introduction

                Welcome to the DWC Course.
            """),
        )
        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 1
        doc = docs[0]
        assert doc.title == "Introduction"
        assert "Welcome to the DWC Course" in doc.content
        assert doc.source_url == "dwc-course://intro.md"
        assert doc.metadata["source"] == "dwc_course"
        assert doc.metadata["sidebar_position"] == "1"

    def test_mdx_parser_strips_imports(self, tmp_path: Path):
        """Import statements are removed from content."""
        _write_file(
            tmp_path,
            "components.md",
            textwrap.dedent("""\
                ---
                title: Components
                ---

                import Tabs from '@theme/Tabs';
                import TabItem from '@theme/TabItem';

                Here is some content after imports.
            """),
        )
        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 1
        assert "import Tabs" not in docs[0].content
        assert "import TabItem" not in docs[0].content
        assert "Here is some content after" in docs[0].content

    def test_mdx_parser_strips_self_closing_jsx(self, tmp_path: Path):
        """Self-closing JSX components like <Hero /> are removed."""
        _write_file(
            tmp_path,
            "hero.md",
            textwrap.dedent("""\
                ---
                title: Hero Page
                ---

                <Hero />

                Some content below the hero.
            """),
        )
        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 1
        assert "<Hero />" not in docs[0].content
        assert "Some content below the hero" in docs[0].content

    def test_mdx_parser_strips_wrapper_jsx_keeps_text(self, tmp_path: Path):
        """JSX wrapper tags are stripped but inner text is preserved."""
        _write_file(
            tmp_path,
            "links.md",
            textwrap.dedent("""\
                ---
                title: Links
                ---

                Click <Link to="/foo">this link</Link> to continue.
            """),
        )
        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 1
        assert "this link" in docs[0].content
        assert "<Link" not in docs[0].content
        assert "</Link>" not in docs[0].content

    def test_mdx_parser_preserves_mermaid(self, tmp_path: Path):
        """Mermaid code blocks are preserved in content."""
        _write_file(
            tmp_path,
            "diagram.md",
            textwrap.dedent("""\
                ---
                title: Architecture
                ---

                Here is the architecture:

                ```mermaid
                graph LR
                    A --> B
                    B --> C
                ```

                And some more text.
            """),
        )
        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 1
        assert "```mermaid" in docs[0].content
        assert "graph LR" in docs[0].content
        assert "A --> B" in docs[0].content

    def test_mdx_parser_uses_frontmatter_title(self, tmp_path: Path):
        """Frontmatter title takes priority over heading."""
        _write_file(
            tmp_path,
            "titled.md",
            textwrap.dedent("""\
                ---
                title: My Custom Title
                ---

                # Different Heading

                Content here.
            """),
        )
        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].title == "My Custom Title"

    def test_mdx_parser_falls_back_to_heading_title(self, tmp_path: Path):
        """Without frontmatter title, first heading is used."""
        _write_file(
            tmp_path,
            "headonly.md",
            textwrap.dedent("""\
                ---
                sidebar_position: 3
                ---

                # Heading as Title

                Some content.
            """),
        )
        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].title == "Heading as Title"

    def test_mdx_parser_uniform_dwc_generation(self, tmp_path: Path):
        """All DWC-Course documents get generations=["dwc"]."""
        for name in ["file1.md", "file2.md", "file3.md"]:
            _write_file(
                tmp_path,
                name,
                textwrap.dedent(f"""\
                    ---
                    title: {name}
                    ---

                    Content for {name}.
                """),
            )

        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 3
        for doc in docs:
            assert doc.generations == ["dwc"]

    def test_mdx_parser_doc_type_tutorial(self, tmp_path: Path):
        """All DWC-Course documents have doc_type='tutorial'."""
        _write_file(
            tmp_path,
            "lesson.md",
            textwrap.dedent("""\
                ---
                title: A Lesson
                ---

                This is a tutorial lesson.
            """),
        )
        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].doc_type == "tutorial"

    def test_mdx_parser_context_header(self, tmp_path: Path):
        """Context header includes 'Dwc Course > chapter > title'."""
        _write_file(
            tmp_path,
            "getting-started/setup.md",
            textwrap.dedent("""\
                ---
                title: Setup Guide
                ---

                How to set up the project.
            """),
        )
        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].context_header == "Dwc Course > Getting Started > Setup Guide"

    def test_mdx_parser_custom_prefix(self, tmp_path: Path):
        """Custom source_prefix controls source_url, metadata, and header."""
        _write_file(
            tmp_path,
            "chapter/lesson.md",
            textwrap.dedent("""\
                ---
                title: My Lesson
                ---

                Content here.
            """),
        )
        parser = MdxParser(docs_dir=tmp_path, source_prefix="mdx-beginner")
        docs = list(parser.parse())

        assert len(docs) == 1
        doc = docs[0]
        assert doc.source_url == "mdx-beginner://chapter/lesson.md"
        assert doc.metadata["source"] == "mdx_beginner"
        assert doc.context_header == "Mdx Beginner > Chapter > My Lesson"

    def test_mdx_parser_skips_empty_files(self, tmp_path: Path):
        """Files that are empty after JSX stripping are skipped."""
        _write_file(
            tmp_path,
            "empty.md",
            textwrap.dedent("""\
                ---
                title: Empty Page
                ---

                import Something from './Something';

                <SomeComponent />
            """),
        )
        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 0

    def test_mdx_parser_handles_mdx_extension(self, tmp_path: Path):
        """Files with .mdx extension are processed."""
        _write_file(
            tmp_path,
            "component.mdx",
            textwrap.dedent("""\
                ---
                title: MDX Component
                ---

                This is an MDX file with real content.
            """),
        )
        parser = MdxParser(docs_dir=tmp_path)
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].title == "MDX Component"
        assert "dwc-course://component.mdx" == docs[0].source_url
