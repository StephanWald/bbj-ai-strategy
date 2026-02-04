"""Configuration system for the RAG ingestion pipeline.

Loads settings from environment variables with BBJ_RAG_ prefix. When
config.toml is present (local dev), it is included as a source with
lower priority than env vars. When absent (Docker), settings come
purely from env vars and field defaults -- no crash.

Priority: constructor args > env vars > TOML file (if present) > field defaults.

NOTE: The TOML file historically used a single ``database_url`` field.
That field has been replaced with separate ``db_host``, ``db_port``,
``db_user``, ``db_password``, ``db_name`` fields. A computed ``database_url``
property maintains backward compatibility for callers that read
``settings.database_url``. The old TOML ``database_url`` key is silently
ignored (it no longer maps to a Settings field).
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class Settings(BaseSettings):
    """Pipeline configuration loaded from env vars (and TOML when present)."""

    model_config = SettingsConfigDict(
        toml_file="config.toml",
        env_prefix="BBJ_RAG_",
        extra="ignore",
    )

    # -- Database credentials (separate fields for Docker env injection) --
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_user: str = Field(default="postgres")
    db_password: str = Field(default="postgres")
    db_name: str = Field(default="bbj_rag")

    # -- Embedding configuration --
    embedding_model: str = Field(default="qwen3-embedding:0.6b")
    embedding_dimensions: int = Field(default=1024)
    embedding_provider: str = Field(default="ollama")
    embedding_batch_size: int = Field(default=64)

    # -- Chunking --
    chunk_size: int = Field(default=400)
    chunk_overlap: int = Field(default=50)

    # -- Chat (Claude API) --
    chat_model: str = Field(default="claude-sonnet-4-5-20250929")
    chat_max_tokens: int = Field(default=2048)
    chat_max_history: int = Field(default=20)
    chat_confidence_min_results: int = Field(default=2)
    chat_confidence_min_score: float = Field(default=0.025)

    # -- BBj compiler validation --
    compiler_timeout: float = Field(default=10.0)
    compiler_path: str = Field(default="bbjcpl")

    # -- Parallel ingestion --
    ingest_workers: int = Field(default=4)
    ingest_max_workers: int = Field(default=8)
    ingest_batch_retries: int = Field(default=3)
    ingest_failure_log: str = Field(default=".ingestion-failures.json")
    ollama_host: str = Field(default="http://localhost:11434")

    @field_validator("ollama_host", mode="before")
    @classmethod
    def _ollama_host_from_env(cls, v: str | None) -> str:
        """Fall back to OLLAMA_HOST env var if BBJ_RAG_OLLAMA_HOST not set.

        Priority: BBJ_RAG_OLLAMA_HOST > OLLAMA_HOST > default
        """
        # If BBJ_RAG_OLLAMA_HOST was explicitly set, use it
        if v and v != "http://localhost:11434":
            return v
        # Check legacy OLLAMA_HOST env var as fallback
        return os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    # -- Source paths --
    flare_source_path: str = Field(default="")
    crawl_source_urls: list[str] = Field(default_factory=list)
    pdf_source_path: str = Field(default="")
    mdx_source_path: str = Field(default="")
    bbj_source_dirs: list[str] = Field(default_factory=list)
    advantage_index_url: str = Field(default="https://basis.cloud/advantage-index/")
    kb_index_url: str = Field(default="https://basis.cloud/knowledge-base/")

    @property
    def database_url(self) -> str:
        """Build a PostgreSQL connection URL from the individual DB fields.

        Maintains backward compatibility -- any code that reads
        ``settings.database_url`` still works.
        """
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Set source priority: init > env > TOML (if present) > defaults.

        The TOML source is only included when config.toml exists on disk.
        This prevents a crash in Docker where no TOML file is mounted.
        """
        sources: list[PydanticBaseSettingsSource] = [
            init_settings,
            env_settings,
        ]
        if Path("config.toml").exists():
            sources.append(TomlConfigSettingsSource(settings_cls))
        return tuple(sources)
