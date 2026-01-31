"""Unit tests for Settings configuration loading."""

from __future__ import annotations

import os

from bbj_rag.config import Settings


def test_settings_default_values():
    """Settings() loads with expected defaults from config.toml."""
    # Run from rag-ingestion/ so config.toml is found
    original_cwd = os.getcwd()
    try:
        os.chdir(
            os.path.join(os.path.dirname(__file__), os.pardir),
        )
        s = Settings()
        assert s.database_url == "postgresql://localhost:5432/bbj_rag"
        assert s.embedding_model == "text-embedding-3-small"
        assert s.embedding_dimensions == 1536
        assert s.chunk_size == 512
        assert s.chunk_overlap == 64
        assert s.flare_source_path == ""
        assert s.crawl_source_urls == []
    finally:
        os.chdir(original_cwd)


def test_settings_env_override(monkeypatch):
    """BBJ_RAG_ env vars override TOML/default values."""
    monkeypatch.setenv("BBJ_RAG_CHUNK_SIZE", "1024")
    s = Settings()
    assert s.chunk_size == 1024


def test_settings_env_override_database_url(monkeypatch):
    """BBJ_RAG_DATABASE_URL env var overrides the database URL."""
    monkeypatch.setenv("BBJ_RAG_DATABASE_URL", "postgresql://test:5432/x")
    s = Settings()
    assert s.database_url == "postgresql://test:5432/x"
