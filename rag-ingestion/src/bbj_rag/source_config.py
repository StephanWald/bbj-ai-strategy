"""Source configuration loader for the RAG ingestion pipeline.

Loads ``sources.toml`` via stdlib ``tomllib``, validates entries through
Pydantic models, resolves the base data directory from environment or
config, and checks that local paths actually exist on disk.

The ``get_source_url_prefix`` helper returns the URL prefix each parser
uses for ``source_url`` values, enabling deterministic ``--clean``
deletion and report SQL pattern matching.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, field_validator

# Known parser types -- must match the parsers/ module names.
_KNOWN_PARSERS: frozenset[str] = frozenset(
    {
        "flare",
        "pdf",
        "mdx",
        "bbj-source",
        "wordpress-advantage",
        "wordpress-kb",
        "web-crawl",
    }
)

# Parsers whose paths reference local directories.
_DIR_PARSERS: frozenset[str] = frozenset({"flare", "mdx", "bbj-source"})

# Parsers whose paths reference local files.
_FILE_PARSERS: frozenset[str] = frozenset({"pdf"})

# Static source_url prefix map for non-MDX parsers.
_SOURCE_URL_PREFIXES: dict[str, str] = {
    "flare": "flare://",
    "pdf": "pdf://",
    "bbj-source": "file://",
    "wordpress-advantage": "https://basis.cloud/advantage",
    "wordpress-kb": "https://basis.cloud/knowledge-base",
    "web-crawl": "https://documentation.basis.cloud",
}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SourceEntry(BaseModel):
    """A single documentation source from ``sources.toml``."""

    name: str
    parser: str
    paths: list[str] = []
    generation_tag: str = "bbj"
    enabled: bool = True

    @field_validator("parser")
    @classmethod
    def parser_must_be_known(cls, v: str) -> str:
        if v not in _KNOWN_PARSERS:
            raise ValueError(
                f"Unknown parser: {v!r}. Must be one of: {sorted(_KNOWN_PARSERS)}"
            )
        return v


class SourcesConfig(BaseModel):
    """Top-level ``sources.toml`` structure."""

    data_dir: str = ""
    sources: list[SourceEntry]


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def load_sources_config(config_path: Path) -> SourcesConfig:
    """Load and validate ``sources.toml``.

    Args:
        config_path: Path to the TOML file.

    Returns:
        Validated :class:`SourcesConfig` instance.
    """
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)
    return SourcesConfig.model_validate(raw)


def resolve_data_dir(config: SourcesConfig) -> Path:
    """Determine the base data directory.

    Resolution order:
        1. ``DATA_DIR`` environment variable
        2. ``data_dir`` value from the config file

    Raises:
        ValueError: If neither source provides a non-empty value.
    """
    env_val = os.environ.get("DATA_DIR", "").strip()
    if env_val:
        return Path(env_val)

    if config.data_dir.strip():
        return Path(config.data_dir)

    raise ValueError(
        "Cannot resolve data directory. "
        "Set the DATA_DIR environment variable or provide a non-empty "
        "data_dir value in sources.toml."
    )


def validate_sources(
    sources: list[SourceEntry],
    data_dir: Path,
) -> list[str]:
    """Validate that local paths exist for all enabled sources.

    Args:
        sources: List of source entries to check (typically only enabled ones).
        data_dir: Resolved base directory for relative path resolution.

    Returns:
        List of human-readable error strings.  Empty list means all valid.
    """
    errors: list[str] = []
    for src in sources:
        if not src.enabled:
            continue

        if src.parser in _DIR_PARSERS:
            for rel_path in src.paths:
                full_path = data_dir / rel_path
                if not full_path.is_dir():
                    errors.append(f"{src.name}: directory not found: {full_path}")

        elif src.parser in _FILE_PARSERS:
            for rel_path in src.paths:
                full_path = data_dir / rel_path
                if not full_path.is_file():
                    errors.append(f"{src.name}: file not found: {full_path}")

        # URL-based parsers (wordpress-*, web-crawl) -- skip path validation.

    return errors


def get_source_url_prefix(source: SourceEntry) -> str:
    """Return the ``source_url`` prefix a parser produces for this source.

    For MDX sources the prefix is derived from the source name
    (e.g. ``"mdx-dwc://"``), ensuring each MDX directory has a unique
    namespace.  For all other parsers a static mapping is used.
    """
    if source.parser == "mdx":
        return f"{source.name}://"
    return _SOURCE_URL_PREFIXES[source.parser]


__all__ = [
    "SourceEntry",
    "SourcesConfig",
    "get_source_url_prefix",
    "load_sources_config",
    "resolve_data_dir",
    "validate_sources",
]
