"""Pydantic request/response models for the BBJ RAG REST API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Inbound search query with optional generation filter and limit."""

    query: str = Field(..., min_length=1, description="Search query text")
    generation: str | None = Field(
        default=None,
        description="Filter by BBj generation tag (e.g. dwc, bbj_gui)",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return",
    )


class SearchResultItem(BaseModel):
    """A single ranked search result returned to the caller."""

    content: str
    title: str
    source_url: str
    doc_type: str
    generations: list[str]
    context_header: str
    deprecated: bool
    score: float


class SearchResponse(BaseModel):
    """Envelope containing search results and metadata."""

    query: str
    results: list[SearchResultItem]
    count: int
