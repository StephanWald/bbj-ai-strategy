"""Embedding client abstraction for the RAG ingestion pipeline.

Provides a Protocol-based interface with Ollama (primary/local) and
OpenAI (API fallback) implementations.  The ``create_embedder`` factory
selects the provider based on Settings.
"""

from __future__ import annotations

from typing import Protocol

import ollama as ollama_client

from bbj_rag.config import Settings


class Embedder(Protocol):
    """Contract for embedding providers."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts."""
        ...

    @property
    def dimensions(self) -> int:
        """Number of dimensions in the output vectors."""
        ...


class OllamaEmbedder:
    """Local embedding via Ollama API.

    Uses the ``ollama.embed()`` function which accepts batch input
    and returns a list of embedding vectors.
    """

    def __init__(
        self,
        model: str = "qwen3-embedding:0.6b",
        dimensions: int = 1024,
    ) -> None:
        self._model = model
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts via Ollama."""
        response = ollama_client.embed(model=self._model, input=texts)
        return response.embeddings  # type: ignore[return-value]


class OpenAIEmbedder:
    """API fallback embedding via OpenAI.

    Lazy-imports the ``openai`` package so it is only required when
    this provider is actually used.
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimensions: int = 1024,
    ) -> None:
        from openai import OpenAI

        self._client = OpenAI()
        self._model = model
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts via OpenAI API."""
        response = self._client.embeddings.create(
            model=self._model,
            input=texts,
            dimensions=self._dimensions,
        )
        return [e.embedding for e in response.data]


def create_embedder(settings: Settings) -> Embedder:
    """Factory: create an Embedder based on the configured provider.

    Returns an ``OllamaEmbedder`` by default.  Set
    ``settings.embedding_provider = "openai"`` to use the OpenAI API.
    """
    if settings.embedding_provider == "openai":
        return OpenAIEmbedder(
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
        )
    return OllamaEmbedder(
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )


__all__ = ["Embedder", "OllamaEmbedder", "OpenAIEmbedder", "create_embedder"]
