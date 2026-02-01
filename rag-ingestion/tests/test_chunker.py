"""Unit tests for the heading-aware markdown chunker."""

from __future__ import annotations

from bbj_rag.chunker import chunk_document
from bbj_rag.models import Document


def _make_doc(
    content: str,
    title: str = "TestPage",
    source_url: str = "flare://Content/test.htm",
    doc_type: str = "concept",
    generations: list[str] | None = None,
    metadata: dict[str, str] | None = None,
    deprecated: bool = False,
) -> Document:
    """Helper to build a Document for testing."""
    return Document(
        source_url=source_url,
        title=title,
        doc_type=doc_type,
        content=content,
        generations=generations or ["bbj"],
        metadata=metadata or {},
        deprecated=deprecated,
    )


class TestSingleSection:
    """Documents with no headings or a single section."""

    def test_small_document_produces_single_chunk(self):
        doc = _make_doc("This is a small document with just one paragraph.")
        chunks = chunk_document(doc)
        assert len(chunks) == 1
        assert "small document" in chunks[0].content

    def test_document_with_no_headings(self):
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        doc = _make_doc(content)
        chunks = chunk_document(doc)
        assert len(chunks) >= 1
        # All text should appear across all chunks.
        combined = " ".join(c.content for c in chunks)
        assert "First paragraph" in combined
        assert "Third paragraph" in combined

    def test_very_small_document_single_chunk(self):
        doc = _make_doc("Hello world.")
        chunks = chunk_document(doc)
        assert len(chunks) == 1


class TestHeadingSplitting:
    """Documents split at heading boundaries."""

    def test_multi_heading_produces_multiple_chunks(self):
        content = (
            "## Description\n\n"
            "This method adds a button.\n\n"
            "## Syntax\n\n"
            "```bbj\nwindow.addButton(id, x, y, w, h, title$)\n```\n\n"
            "## Parameters\n\n"
            "- id: control ID\n- x: x position"
        )
        doc = _make_doc(content)
        chunks = chunk_document(doc)
        assert len(chunks) >= 3
        # Each section should be in a separate chunk.
        contents = [c.content for c in chunks]
        assert any("Description" in c for c in contents)
        assert any("Syntax" in c for c in contents)
        assert any("Parameters" in c for c in contents)

    def test_empty_sections_skipped(self):
        content = (
            "## Description\n\n"
            "Some text here.\n\n"
            "## Empty Section\n\n"
            "## Another Section\n\n"
            "More text here."
        )
        doc = _make_doc(content)
        chunks = chunk_document(doc)
        # Empty Section heading line alone should still produce a chunk
        # since we include the heading line itself.
        contents = [c.content for c in chunks]
        assert any("Description" in c for c in contents)
        assert any("Another Section" in c for c in contents)


class TestCodeBlockPreservation:
    """Fenced code blocks are never split."""

    def test_code_block_stays_intact(self):
        # Create a document where the code block is large but should not split.
        code_lines = "\n".join(f"line {i}" for i in range(100))
        content = f"## Example\n\n```bbj\n{code_lines}\n```"
        doc = _make_doc(content)
        chunks = chunk_document(doc, max_tokens=50)
        # The code block should appear intact in one chunk.
        found_code = False
        for chunk in chunks:
            if "```bbj" in chunk.content and "line 99" in chunk.content:
                found_code = True
                # Verify the fence is properly closed.
                assert chunk.content.count("```") >= 2
        assert found_code, "Code block should be intact in at least one chunk"

    def test_code_block_not_split_at_heading_inside(self):
        content = (
            "## Example\n\n```python\n## This is a comment, not a heading\nx = 1\n```"
        )
        doc = _make_doc(content)
        chunks = chunk_document(doc)
        # The ## inside the code block should not cause a split.
        assert len(chunks) == 1


class TestOversizedSections:
    """Sections exceeding max_tokens are sub-split."""

    def test_oversized_section_splits_at_paragraphs(self):
        # Create a section with many paragraphs.
        paragraphs = [f"Paragraph {i} with enough words to matter." for i in range(20)]
        content = "## LargeSection\n\n" + "\n\n".join(paragraphs)
        doc = _make_doc(content)
        chunks = chunk_document(doc, max_tokens=30, overlap_tokens=5)
        assert len(chunks) > 1
        # All paragraphs should appear across chunks.
        combined = " ".join(c.content for c in chunks)
        assert "Paragraph 0" in combined
        assert "Paragraph 19" in combined


class TestContextHeader:
    """Context headers are prepended to chunk content."""

    def test_context_header_prepended(self):
        doc = _make_doc(
            content="## Description\n\nSome text.",
            title="addButton",
            metadata={"section_path": "Language > BBjAPI > BBjWindow"},
        )
        chunks = chunk_document(doc)
        assert len(chunks) >= 1
        # The context header should appear at the start of content.
        assert chunks[0].content.startswith(
            "Language > BBjAPI > BBjWindow > addButton > Description"
        )

    def test_context_header_stored_separately(self):
        doc = _make_doc(
            content="## Syntax\n\nSome syntax.",
            title="MyMethod",
            metadata={"section_path": "API > Class"},
        )
        chunks = chunk_document(doc)
        assert len(chunks) >= 1
        assert chunks[0].context_header == "API > Class > MyMethod > Syntax"


class TestMetadataInheritance:
    """Chunks inherit Document metadata."""

    def test_chunk_inherits_source_url(self):
        doc = _make_doc("Some content.", source_url="flare://Content/test.htm")
        chunks = chunk_document(doc)
        assert chunks[0].source_url == "flare://Content/test.htm"

    def test_chunk_inherits_generations(self):
        doc = _make_doc("Some content.", generations=["bbj_gui", "dwc"])
        chunks = chunk_document(doc)
        assert chunks[0].generations == ["bbj_gui", "dwc"]

    def test_chunk_inherits_doc_type(self):
        doc = _make_doc("Some content.", doc_type="api-reference")
        chunks = chunk_document(doc)
        assert chunks[0].doc_type == "api-reference"

    def test_chunk_inherits_deprecated(self):
        doc = _make_doc("Some content.", deprecated=True)
        chunks = chunk_document(doc)
        assert chunks[0].deprecated is True

    def test_chunk_inherits_metadata(self):
        doc = _make_doc(
            "Some content.",
            metadata={"section_path": "A > B", "conditions": "Primary.BASISHelp"},
        )
        chunks = chunk_document(doc)
        assert chunks[0].metadata["conditions"] == "Primary.BASISHelp"


class TestContentHash:
    """Content hash is deterministic."""

    def test_same_content_same_hash(self):
        doc = _make_doc("## Heading\n\nSame content here.")
        chunks_a = chunk_document(doc)
        chunks_b = chunk_document(doc)
        assert chunks_a[0].content_hash == chunks_b[0].content_hash

    def test_different_content_different_hash(self):
        doc_a = _make_doc("## A\n\nContent A.")
        doc_b = _make_doc("## B\n\nContent B.")
        chunks_a = chunk_document(doc_a)
        chunks_b = chunk_document(doc_b)
        assert chunks_a[0].content_hash != chunks_b[0].content_hash
