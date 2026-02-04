"""Embedding client abstraction for the RAG ingestion pipeline.

Provides a Protocol-based interface with Ollama (primary/local) and
OpenAI (API fallback) implementations.  The ``create_embedder`` factory
selects the provider based on Settings.

Also includes ``AsyncOllamaEmbedder`` for concurrent embedding with
persistent HTTP connections via httpx.AsyncClient.
"""

from __future__ import annotations

import os
from typing import Any, Protocol

import httpx
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


class AsyncOllamaEmbedder:
    """Async embedding via Ollama HTTP API with persistent connections.

    Uses httpx.AsyncClient with connection pooling for efficient concurrent
    embedding. The client is reused across all embed_batch calls within a
    session, eliminating per-batch connection setup overhead.

    Usage::

        async with AsyncOllamaEmbedder() as embedder:
            vectors = await embedder.embed_batch(["text1", "text2"])
    """

    def __init__(
        self,
        model: str = "qwen3-embedding:0.6b",
        dimensions: int = 1024,
        host: str | None = None,
    ) -> None:
        self._model = model
        self._dimensions = dimensions
        # Check env vars: prefer BBJ_RAG_OLLAMA_HOST, fall back to OLLAMA_HOST
        self._host = host or os.environ.get(
            "BBJ_RAG_OLLAMA_HOST",
            os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
        )
        self._client: httpx.AsyncClient | None = None

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def __aenter__(self) -> AsyncOllamaEmbedder:
        """Initialize the HTTP client with connection pooling."""
        limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
        self._client = httpx.AsyncClient(
            base_url=self._host,
            limits=limits,
            timeout=httpx.Timeout(300.0),  # 5 min for large batches
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts via Ollama HTTP API.

        Requires the embedder to be used as an async context manager.
        """
        if self._client is None:
            raise RuntimeError(
                "AsyncOllamaEmbedder must be used as an async context manager"
            )
        response = await self._client.post(
            "/api/embed",
            json={"model": self._model, "input": texts},
        )
        response.raise_for_status()
        data: dict[str, list[list[float]]] = response.json()
        return data["embeddings"]


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


def create_async_embedder(settings: Settings) -> AsyncOllamaEmbedder:
    """Factory: create an AsyncOllamaEmbedder for concurrent embedding.

    Uses settings.ollama_host for the Ollama server URL.
    """
    return AsyncOllamaEmbedder(
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        host=settings.ollama_host,
    )


__all__ = [
    "AsyncOllamaEmbedder",
    "Embedder",
    "OllamaEmbedder",
    "OpenAIEmbedder",
    "create_async_embedder",
    "create_embedder",
]
