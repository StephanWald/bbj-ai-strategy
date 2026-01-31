"""Unit tests for Document and Chunk Pydantic models."""

from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from bbj_rag.models import Chunk, Document

# -- Document validation tests --


def test_document_valid():
    """Construct Document with all required fields successfully."""
    doc = Document(
        source_url="https://docs.example.com/page",
        title="Test Page",
        doc_type="web",
        content="Some documentation content.",
        generations=["BBj 25.00"],
    )
    assert doc.source_url == "https://docs.example.com/page"
    assert doc.title == "Test Page"
    assert doc.content == "Some documentation content."
    assert doc.generations == ["BBj 25.00"]
    assert doc.metadata == {}


def test_document_empty_content_rejected():
    """Empty content string must raise ValidationError."""
    with pytest.raises(ValidationError, match="content must not be empty"):
        Document(
            source_url="https://x",
            title="T",
            doc_type="web",
            content="",
            generations=["v1"],
        )


def test_document_whitespace_content_rejected():
    """Whitespace-only content must raise ValidationError."""
    with pytest.raises(ValidationError, match="content must not be empty"):
        Document(
            source_url="https://x",
            title="T",
            doc_type="web",
            content="   ",
            generations=["v1"],
        )


def test_document_empty_generations_rejected():
    """Empty generations list must raise ValidationError."""
    with pytest.raises(
        ValidationError, match="generations must contain at least one entry"
    ):
        Document(
            source_url="https://x",
            title="T",
            doc_type="web",
            content="hello",
            generations=[],
        )


def test_document_extra_fields_rejected():
    """Unknown fields must raise ValidationError (extra='forbid')."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Document(
            source_url="https://x",
            title="T",
            doc_type="web",
            content="hello",
            generations=["v1"],
            unknown_field="bad",  # type: ignore[call-arg]
        )


def test_document_strips_whitespace():
    """Leading/trailing whitespace on string fields is stripped."""
    doc = Document(
        source_url="  https://x  ",
        title="  My Title  ",
        doc_type="web",
        content="  some content  ",
        generations=["v1"],
    )
    assert doc.source_url == "https://x"
    assert doc.title == "My Title"
    assert doc.content == "some content"


# -- Chunk validation tests --


def test_chunk_from_content_computes_hash():
    """from_content() must compute SHA-256 of stripped content."""
    content = "hello world"
    chunk = Chunk.from_content(
        source_url="https://x",
        title="T",
        doc_type="web",
        content=content,
        generations=["v1"],
    )
    expected = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
    assert chunk.content_hash == expected


def test_chunk_from_content_deterministic():
    """Same content must always produce the same hash."""
    kwargs = {
        "source_url": "https://x",
        "title": "T",
        "doc_type": "web",
        "content": "deterministic test",
        "generations": ["v1"],
    }
    c1 = Chunk.from_content(**kwargs)
    c2 = Chunk.from_content(**kwargs)
    assert c1.content_hash == c2.content_hash


def test_chunk_from_content_different_content_different_hash():
    """Different content must produce different hashes."""
    base = {
        "source_url": "https://x",
        "title": "T",
        "doc_type": "web",
        "generations": ["v1"],
    }
    c1 = Chunk.from_content(content="alpha", **base)
    c2 = Chunk.from_content(content="beta", **base)
    assert c1.content_hash != c2.content_hash


def test_chunk_embedding_optional():
    """Chunk created without embedding defaults to None."""
    chunk = Chunk.from_content(
        source_url="https://x",
        title="T",
        doc_type="web",
        content="hello",
        generations=["v1"],
    )
    assert chunk.embedding is None


def test_chunk_empty_content_rejected():
    """Chunk.from_content with empty content must raise ValidationError."""
    with pytest.raises(ValidationError, match="content must not be empty"):
        Chunk.from_content(
            source_url="https://x",
            title="T",
            doc_type="web",
            content="",
            generations=["v1"],
        )
