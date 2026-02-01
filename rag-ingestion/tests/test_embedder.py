"""Unit tests for embedding client abstraction with mocked backends."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from bbj_rag.config import Settings
from bbj_rag.embedder import (
    OllamaEmbedder,
    OpenAIEmbedder,
    create_embedder,
)


class TestOllamaEmbedder:
    """OllamaEmbedder calls ollama.embed correctly."""

    @patch("bbj_rag.embedder.ollama_client")
    def test_embed_batch_calls_ollama(self, mock_ollama):
        mock_response = MagicMock()
        mock_response.embeddings = [[0.1, 0.2], [0.3, 0.4]]
        mock_ollama.embed.return_value = mock_response

        embedder = OllamaEmbedder(model="test-model", dimensions=2)
        result = embedder.embed_batch(["hello", "world"])

        mock_ollama.embed.assert_called_once_with(
            model="test-model", input=["hello", "world"]
        )
        assert result == [[0.1, 0.2], [0.3, 0.4]]

    @patch("bbj_rag.embedder.ollama_client")
    def test_embed_batch_with_default_model(self, mock_ollama):
        mock_response = MagicMock()
        mock_response.embeddings = [[0.5]]
        mock_ollama.embed.return_value = mock_response

        embedder = OllamaEmbedder()
        embedder.embed_batch(["test"])

        mock_ollama.embed.assert_called_once_with(
            model="qwen3-embedding:0.6b", input=["test"]
        )

    def test_dimensions_property(self):
        embedder = OllamaEmbedder(dimensions=1024)
        assert embedder.dimensions == 1024

    def test_dimensions_custom_value(self):
        embedder = OllamaEmbedder(dimensions=512)
        assert embedder.dimensions == 512


class TestOpenAIEmbedder:
    """OpenAIEmbedder calls openai client correctly."""

    @patch("bbj_rag.embedder.OpenAIEmbedder.__init__", return_value=None)
    def test_embed_batch_calls_openai(self, mock_init):
        embedder = OpenAIEmbedder.__new__(OpenAIEmbedder)
        embedder._model = "text-embedding-3-small"
        embedder._dimensions = 1024

        mock_client = MagicMock()
        embedder._client = mock_client

        mock_embedding_1 = MagicMock()
        mock_embedding_1.embedding = [0.1, 0.2, 0.3]
        mock_embedding_2 = MagicMock()
        mock_embedding_2.embedding = [0.4, 0.5, 0.6]
        mock_client.embeddings.create.return_value = MagicMock(
            data=[mock_embedding_1, mock_embedding_2]
        )

        result = embedder.embed_batch(["hello", "world"])

        mock_client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input=["hello", "world"],
            dimensions=1024,
        )
        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    @patch("bbj_rag.embedder.OpenAIEmbedder.__init__", return_value=None)
    def test_dimensions_property(self, mock_init):
        embedder = OpenAIEmbedder.__new__(OpenAIEmbedder)
        embedder._dimensions = 1024
        assert embedder.dimensions == 1024


class TestCreateEmbedder:
    """Factory function selects the correct provider."""

    @patch("bbj_rag.embedder.ollama_client")
    def test_ollama_provider(self, _mock_ollama):
        settings = Settings(
            embedding_provider="ollama",
            embedding_model="qwen3-embedding:0.6b",
            embedding_dimensions=1024,
        )
        embedder = create_embedder(settings)
        assert isinstance(embedder, OllamaEmbedder)
        assert embedder.dimensions == 1024

    @patch("bbj_rag.embedder.OpenAIEmbedder.__init__", return_value=None)
    def test_openai_provider(self, _mock_init):
        settings = Settings(
            embedding_provider="openai",
            embedding_model="text-embedding-3-small",
            embedding_dimensions=1024,
        )
        embedder = create_embedder(settings)
        assert isinstance(embedder, OpenAIEmbedder)

    @patch("bbj_rag.embedder.ollama_client")
    def test_default_provider_is_ollama(self, _mock_ollama):
        settings = Settings()
        embedder = create_embedder(settings)
        assert isinstance(embedder, OllamaEmbedder)

    @patch("bbj_rag.embedder.ollama_client")
    def test_embedder_uses_configured_model(self, _mock_ollama):
        settings = Settings(
            embedding_provider="ollama",
            embedding_model="custom-model:latest",
            embedding_dimensions=768,
        )
        embedder = create_embedder(settings)
        assert isinstance(embedder, OllamaEmbedder)
        assert embedder.dimensions == 768

    @patch("bbj_rag.embedder.ollama_client")
    def test_embedder_dimensions_from_settings(self, _mock_ollama):
        settings = Settings(embedding_dimensions=512)
        embedder = create_embedder(settings)
        assert embedder.dimensions == 512
