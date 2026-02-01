"""Tests for the BBj source code parser.

Uses temporary directories with sample files to test file discovery,
content validation, generation classification, header comment extraction,
and protocol compliance.
"""

from __future__ import annotations

from pathlib import Path

from bbj_rag.parsers import DocumentParser
from bbj_rag.parsers.bbj_source import (
    BbjSourceParser,
    classify_source_generation,
    extract_header_comment,
)

# ---------------------------------------------------------------------------
# Protocol compliance
# ---------------------------------------------------------------------------


class TestBbjSourceParserProtocol:
    def test_bbj_source_parser_implements_protocol(self):
        parser = BbjSourceParser([Path("dummy")])
        assert isinstance(parser, DocumentParser)


# ---------------------------------------------------------------------------
# Document yielding
# ---------------------------------------------------------------------------


class TestBbjSourceParserYields:
    def test_bbj_source_parser_yields_documents(self, tmp_path: Path):
        src = tmp_path / "sample.bbj"
        src.write_text("rem Sample\nPROCESS_EVENTS\n")

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].title == "sample"
        assert docs[0].content.strip() != ""

    def test_bbj_source_parser_multiple_files(self, tmp_path: Path):
        (tmp_path / "one.bbj").write_text("rem One\nPROCESS_EVENTS\n")
        (tmp_path / "two.txt").write_text("rem Two\nSYSGUI = UNT\n")
        (tmp_path / "three.src").write_text('rem Three\nopen (1)"test"\n')

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 3


# ---------------------------------------------------------------------------
# Header comment extraction
# ---------------------------------------------------------------------------


class TestBbjSourceParserHeaderComment:
    def test_extracts_header_comment(self, tmp_path: Path):
        content = "rem This is a description\nrem More info\nPROCESS_EVENTS\n"
        src = tmp_path / "demo.bbj"
        src.write_text(content)

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].metadata["header_comment"] == ("This is a description More info")

    def test_extract_header_comment_function(self):
        content = "rem First line\nrem Second line\ncode here\n"
        assert extract_header_comment(content) == "First line Second line"

    def test_extract_header_comment_empty_when_no_rem(self):
        content = 'PROCESS_EVENTS\nPRINT "hello"\n'
        assert extract_header_comment(content) == ""

    def test_extract_header_comment_stops_at_blank_line(self):
        content = "rem First block\n\nrem Second block\ncode\n"
        assert extract_header_comment(content) == "First block"


# ---------------------------------------------------------------------------
# Generation classification
# ---------------------------------------------------------------------------


class TestBbjSourceParserClassification:
    def test_classifies_dwc(self, tmp_path: Path):
        src = tmp_path / "dwc-demo.bbj"
        src.write_text(
            "rem DWC demo\n"
            "use ::BBjHtmlView.bbj::BBjHtmlView\n"
            'htmlView! = window!.addHtmlView(101, 0, 0, 800, 600, "")\n'
        )

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].generations == ["dwc"]

    def test_classifies_gui(self, tmp_path: Path):
        src = tmp_path / "gui-demo.bbj"
        src.write_text(
            'rem GUI demo\nSYSGUI = UNT\nOPEN (SYSGUI)"X0"\nPROCESS_EVENTS\n'
        )

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].generations == ["bbj_gui"]

    def test_classifies_all(self, tmp_path: Path):
        src = tmp_path / "utility.bbj"
        src.write_text('rem A utility module\nprint "hello world"\n')

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].generations == ["all"]

    def test_classify_source_generation_dwc(self):
        assert classify_source_generation("BBjHtmlView stuff") == ["dwc"]

    def test_classify_source_generation_gui(self):
        assert classify_source_generation("SYSGUI = UNT") == ["bbj_gui"]

    def test_classify_source_generation_all(self):
        assert classify_source_generation("just some text") == ["all"]


# ---------------------------------------------------------------------------
# Non-BBj file skipping
# ---------------------------------------------------------------------------


class TestBbjSourceParserSkipping:
    def test_skips_non_bbj_files(self, tmp_path: Path):
        src = tmp_path / "readme.txt"
        src.write_text(
            "This is a readme file with no BBj keywords whatsoever.\n"
            "It just describes the project.\n"
        )

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 0

    def test_skips_empty_files(self, tmp_path: Path):
        src = tmp_path / "empty.bbj"
        src.write_text("")

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 0


# ---------------------------------------------------------------------------
# Multiple extensions
# ---------------------------------------------------------------------------


class TestBbjSourceParserExtensions:
    def test_multiple_extensions(self, tmp_path: Path):
        (tmp_path / "a.bbj").write_text("rem bbj\nPROCESS_EVENTS\n")
        (tmp_path / "b.txt").write_text("rem txt\nSYSGUI = UNT\n")
        (tmp_path / "c.src").write_text('rem src\nopen (1)"test"\n')
        # This extension is not in default list
        (tmp_path / "d.bas").write_text('rem bas\nPRINT "hello"\n')

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        extensions_found = {d.metadata["file_ext"] for d in docs}
        assert ".bbj" in extensions_found
        assert ".txt" in extensions_found
        assert ".src" in extensions_found
        assert ".bas" not in extensions_found

    def test_custom_extensions(self, tmp_path: Path):
        (tmp_path / "test.bas").write_text('rem test\nPRINT "hello"\n')

        parser = BbjSourceParser([tmp_path], extensions=[".bas"])
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].metadata["file_ext"] == ".bas"


# ---------------------------------------------------------------------------
# Doc type and context header
# ---------------------------------------------------------------------------


class TestBbjSourceParserDocTypeAndHeader:
    def test_sets_doc_type_example(self, tmp_path: Path):
        src = tmp_path / "demo.bbj"
        src.write_text("rem Demo\nPROCESS_EVENTS\n")

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].doc_type == "example"

    def test_context_header_with_description(self, tmp_path: Path):
        src = tmp_path / "cust-gui.bbj"
        src.write_text("rem Customer GUI application\nPROCESS_EVENTS\n")

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].context_header == (
            "BBj Source Code > cust-gui.bbj -- Customer GUI application"
        )

    def test_context_header_without_description(self, tmp_path: Path):
        src = tmp_path / "minimal.bbj"
        # No rem comment, just code
        src.write_text("PROCESS_EVENTS\n")

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].context_header == "BBj Source Code > minimal.bbj"


# ---------------------------------------------------------------------------
# Source URL and metadata
# ---------------------------------------------------------------------------


class TestBbjSourceParserMetadata:
    def test_source_url(self, tmp_path: Path):
        sub = tmp_path / "samples"
        sub.mkdir()
        src = sub / "demo.bbj"
        src.write_text("rem test\nPROCESS_EVENTS\n")

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].source_url == "file://samples/demo.bbj"

    def test_metadata_fields(self, tmp_path: Path):
        src = tmp_path / "test.bbj"
        src.write_text("rem A test file\nPROCESS_EVENTS\n")

        parser = BbjSourceParser([tmp_path])
        docs = list(parser.parse())

        assert len(docs) == 1
        assert docs[0].metadata["source"] == "bbj_source"
        assert docs[0].metadata["file_ext"] == ".bbj"
        assert docs[0].metadata["header_comment"] == "A test file"
        assert docs[0].deprecated is False
