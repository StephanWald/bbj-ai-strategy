"""Click CLI entry point for the BBj RAG ingestion pipeline.

Provides commands for full pipeline execution (ingest), parse-only
debugging (parse), and search validation (validate, placeholder).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import NoReturn

import click

from bbj_rag.config import Settings
from bbj_rag.parsers import DocumentParser

logger = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose: bool) -> None:
    """BBj RAG ingestion pipeline."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@cli.command()
@click.option(
    "--source",
    type=click.Choice(["flare"]),
    required=True,
    help="Documentation source",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Skip already-stored chunks (dev mode)",
)
@click.option(
    "--batch-size",
    default=64,
    type=int,
    help="Embedding batch size",
)
def ingest(source: str, resume: bool, batch_size: int) -> None:
    """Run the full ingestion pipeline."""
    from bbj_rag.db import get_connection
    from bbj_rag.embedder import create_embedder
    from bbj_rag.pipeline import run_pipeline

    settings = Settings()

    # Create parser.
    parser = _create_parser(source, settings)

    # Create embedder.
    try:
        embedder = create_embedder(settings)
    except Exception as exc:
        click.echo(
            f"Error creating embedder: {exc}\n"
            f"If using Ollama, ensure it is running and the model is pulled:\n"
            f"  ollama pull {settings.embedding_model}",
            err=True,
        )
        sys.exit(1)

    # Open database connection.
    try:
        conn = get_connection(settings.database_url)
    except Exception as exc:
        # Mask password in URL for error output.
        safe_url = _mask_password(settings.database_url)
        click.echo(
            f"Database connection failed: {exc}\nConnection URL: {safe_url}",
            err=True,
        )
        sys.exit(1)

    try:
        stats = run_pipeline(
            parser=parser,
            embedder=embedder,
            conn=conn,
            batch_size=batch_size,
            resume=resume,
            max_tokens=settings.chunk_size,
            overlap_tokens=settings.chunk_overlap,
        )
        click.echo(
            f"\nIngestion complete:\n"
            f"  Documents parsed: {stats['docs_parsed']}\n"
            f"  Chunks created:   {stats['chunks_created']}\n"
            f"  Chunks embedded:  {stats['chunks_embedded']}\n"
            f"  Chunks stored:    {stats['chunks_stored']}"
        )
    except Exception as exc:
        logger.exception("Pipeline failed")
        # Check for common Ollama errors.
        exc_str = str(exc)
        if "not found" in exc_str.lower() or "model" in exc_str.lower():
            click.echo(
                f"Ollama error: {exc}\nRun: ollama pull {settings.embedding_model}",
                err=True,
            )
        else:
            click.echo(f"Pipeline error: {exc}", err=True)
        sys.exit(1)
    finally:
        conn.close()


@cli.command()
@click.option(
    "--source",
    type=click.Choice(["flare"]),
    required=True,
    help="Documentation source",
)
def parse(source: str) -> None:
    """Parse source documents (no embedding)."""
    settings = Settings()
    parser = _create_parser(source, settings)

    count = 0
    sample_titles: list[str] = []
    for doc in parser.parse():
        count += 1
        if count <= 5:
            sample_titles.append(doc.title)

    click.echo(f"Parsed {count} documents from '{source}'")
    if sample_titles:
        click.echo("Sample titles:")
        for title in sample_titles:
            click.echo(f"  - {title}")


@cli.command()
@click.option(
    "--verbose",
    "-v",
    "val_verbose",
    is_flag=True,
    help="Show detailed results",
)
def validate(val_verbose: bool) -> None:
    """Run search validation assertions against embedded data."""
    import subprocess

    args = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_search_validation.py",
        "-v",
        "-m",
        "search_validation",
    ]
    if val_verbose:
        args.append("-s")
    result = subprocess.run(
        args,
        cwd=str(Path(__file__).resolve().parents[2]),
    )
    sys.exit(result.returncode)


def _create_parser(source: str, settings: Settings) -> DocumentParser:
    """Create a DocumentParser for the given source.

    Currently only supports 'flare'. The FlareParser needs a content_dir
    (Content/ inside the Flare project) and a project_dir (the Flare
    project root).
    """
    if source == "flare":
        from bbj_rag.parsers.flare import FlareParser

        flare_path = settings.flare_source_path
        if not flare_path:
            _fatal(
                "Error: flare_source_path not configured.\n"
                "Set BBJ_RAG_FLARE_SOURCE_PATH or add to config.toml."
            )

        project_dir = Path(flare_path)
        content_dir = project_dir / "Content"
        if not content_dir.is_dir():
            _fatal(
                f"Error: Content directory not found: {content_dir}\n"
                f"Ensure flare_source_path points to the Flare project root."
            )

        return FlareParser(content_dir=content_dir, project_dir=project_dir)

    _fatal(f"Unknown source: {source}")


def _fatal(message: str) -> NoReturn:
    """Print an error message and exit with code 1."""
    click.echo(message, err=True)
    sys.exit(1)


def _mask_password(url: str) -> str:
    """Replace password in a database URL with asterisks."""
    # postgresql://user:password@host:port/db -> postgresql://user:****@host:port/db
    if "@" in url and ":" in url.split("@")[0]:
        parts = url.split("@", 1)
        cred_parts = parts[0].rsplit(":", 1)
        if len(cred_parts) == 2:
            return f"{cred_parts[0]}:****@{parts[1]}"
    return url


__all__ = ["cli"]
