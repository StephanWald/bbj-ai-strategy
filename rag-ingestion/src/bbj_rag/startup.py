"""Environment validation and startup summary logging.

Called during FastAPI lifespan to validate critical settings and
log a structured overview of the runtime configuration. Never logs
the database password.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bbj_rag.config import Settings

logger = logging.getLogger("bbj_rag.startup")


def validate_environment() -> None:
    """Check that critical environment variables are set.

    In Docker (no config.toml present and ENV != "development"), warn
    if BBJ_RAG_DB_PASSWORD is still the default "postgres" value.
    This is a soft warning -- the defaults are technically functional,
    and pydantic handles hard validation of missing required fields.
    """
    env = os.environ.get("ENV", "production")
    has_toml = Path("config.toml").exists()

    if not has_toml and env != "development":
        db_password = os.environ.get("BBJ_RAG_DB_PASSWORD", "")
        if not db_password or db_password == "postgres":
            logger.warning(
                "BBJ_RAG_DB_PASSWORD is unset or using the default 'postgres' value. "
                "Set a strong password for production deployments."
            )


def log_startup_summary(settings: Settings) -> None:
    """Log a structured startup summary at INFO level.

    Includes Python version, database connection info (without password),
    Ollama URL, embedding configuration, environment label, and data
    mount status.
    """
    ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    env = os.environ.get("ENV", "production")

    # Check data mount
    data_path = Path("/data")
    if data_path.is_dir():
        subdirs = sorted(p.name for p in data_path.iterdir() if p.is_dir())
        data_status = ", ".join(subdirs) if subdirs else "(empty)"
    else:
        data_status = "(not mounted)"

    summary = (
        "\n"
        "=" * 60 + "\n"
        "  BBJ RAG -- Startup Summary\n"
        "=" * 60 + "\n"
        f"  Python:     {sys.version.split()[0]}\n"
        f"  DB Host:    {settings.db_host}:{settings.db_port}\n"
        f"  DB Name:    {settings.db_name}\n"
        f"  DB User:    {settings.db_user}\n"
        f"  Ollama:     {ollama_host}\n"
        f"  Embedding:  {settings.embedding_model} ({settings.embedding_dimensions}d)\n"
        f"  Environment:{env}\n"
        f"  Data mount: {data_status}\n"
        "=" * 60
    )
    logger.info(summary)
