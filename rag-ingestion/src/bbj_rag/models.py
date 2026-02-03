"""Pydantic data models for the RAG ingestion pipeline.

Document represents parsed content from Flare or web sources.
Chunk represents a storage-ready text fragment with content-hash deduplication.
"""

from __future__ import annotations

import hashlib

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Document(BaseModel):
    """Parser output contract: validated parsed content from a documentation source."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_url: str
    title: str
    doc_type: str
    content: str
    generations: list[str]
    context_header: str = ""
    deprecated: bool = False
    source_type: str = ""
    display_url: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be empty")
        return v

    @field_validator("generations")
    @classmethod
    def generations_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("generations must contain at least one entry")
        return v


class Chunk(BaseModel):
    """Storage-ready contract: text fragment with content-hash dedup."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_url: str
    title: str
    doc_type: str
    content: str
    content_hash: str
    generations: list[str]
    context_header: str = ""
    deprecated: bool = False
    source_type: str = ""
    display_url: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)
    embedding: list[float] | None = None

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be empty")
        return v

    @field_validator("generations")
    @classmethod
    def generations_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("generations must contain at least one entry")
        return v

    @classmethod
    def from_content(
        cls,
        source_url: str,
        title: str,
        doc_type: str,
        content: str,
        generations: list[str],
        metadata: dict[str, str] | None = None,
        context_header: str = "",
        deprecated: bool = False,
        source_type: str = "",
        display_url: str = "",
    ) -> Chunk:
        """Create a Chunk with auto-computed SHA-256 content hash.

        This is the canonical way to create Chunk instances. The hash is
        computed on stripped content to avoid whitespace-only duplicates.
        The ``context_header`` is stored separately so it does not affect
        the content hash (avoids dedup breakage when TOC changes).
        """
        content_hash = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
        return cls(
            source_url=source_url,
            title=title,
            doc_type=doc_type,
            content=content,
            content_hash=content_hash,
            generations=generations,
            context_header=context_header,
            deprecated=deprecated,
            source_type=source_type,
            display_url=display_url,
            metadata=metadata or {},
        )
