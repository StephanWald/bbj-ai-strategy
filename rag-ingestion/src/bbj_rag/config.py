"""Configuration system for the RAG ingestion pipeline.

Loads settings from config.toml with BBJ_RAG_ environment variable overrides.
Priority: constructor args > env vars > TOML file > field defaults.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class Settings(BaseSettings):
    """Pipeline configuration loaded from TOML with env var overrides."""

    model_config = SettingsConfigDict(
        toml_file="config.toml",
        env_prefix="BBJ_RAG_",
    )

    database_url: str = Field(
        default="postgresql://localhost:5432/bbj_rag",
    )
    embedding_model: str = Field(default="qwen3-embedding:0.6b")
    embedding_dimensions: int = Field(default=1024)
    embedding_provider: str = Field(default="ollama")
    embedding_batch_size: int = Field(default=64)
    chunk_size: int = Field(default=400)
    chunk_overlap: int = Field(default=50)
    flare_source_path: str = Field(default="")
    crawl_source_urls: list[str] = Field(default_factory=list)

    # Suppress mypy error for pydantic-settings classmethod override
    _toml_source: ClassVar[type] = TomlConfigSettingsSource

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Set source priority: init > env > TOML > defaults."""
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls),
        )
