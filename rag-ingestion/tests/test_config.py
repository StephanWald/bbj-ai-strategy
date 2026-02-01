"""Unit tests for Settings configuration loading."""

from __future__ import annotations

import os

from bbj_rag.config import Settings


def test_settings_default_values():
    """Settings() loads with expected defaults from config.toml (when present).

    Note: database_url is now a computed property built from separate
    db_host/db_port/db_user/db_password/db_name fields. The TOML file's
    old ``database_url`` key is silently ignored.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(
            os.path.join(os.path.dirname(__file__), os.pardir),
        )
        s = Settings()
        # database_url is computed from individual fields (defaults)
        assert s.database_url == "postgresql://postgres:postgres@localhost:5432/bbj_rag"
        # TOML still overrides embedding fields
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


def test_settings_env_override_db_fields(monkeypatch):
    """BBJ_RAG_DB_* env vars control database_url property."""
    monkeypatch.setenv("BBJ_RAG_DB_HOST", "myhost")
    monkeypatch.setenv("BBJ_RAG_DB_PORT", "9999")
    monkeypatch.setenv("BBJ_RAG_DB_USER", "alice")
    monkeypatch.setenv("BBJ_RAG_DB_PASSWORD", "secret")
    monkeypatch.setenv("BBJ_RAG_DB_NAME", "testdb")
    s = Settings()
    assert s.db_host == "myhost"
    assert s.db_port == 9999
    assert s.db_user == "alice"
    assert s.db_password == "secret"
    assert s.db_name == "testdb"
    assert s.database_url == "postgresql://alice:secret@myhost:9999/testdb"


def test_settings_separate_db_fields_defaults():
    """Individual DB fields have expected defaults."""
    s = Settings()
    assert s.db_host == "localhost"
    assert s.db_port == 5432
    assert s.db_user == "postgres"
    assert s.db_password == "postgres"
    assert s.db_name == "bbj_rag"


def test_settings_without_toml(tmp_path, monkeypatch):
    """Settings loads from env vars alone when config.toml is absent."""
    monkeypatch.chdir(tmp_path)  # No config.toml in tmp_path
    monkeypatch.setenv("BBJ_RAG_DB_HOST", "docker-db")
    monkeypatch.setenv("BBJ_RAG_DB_PORT", "5433")
    s = Settings()
    assert s.db_host == "docker-db"
    assert s.db_port == 5433
    assert s.database_url == "postgresql://postgres:postgres@docker-db:5433/bbj_rag"
