"""Standalone orchestration CLI for all-source ingestion.

Reads ``sources.toml``, validates all paths and dependencies up front,
then runs the existing ``run_pipeline()`` for each enabled source.
Tracks progress for resume capability and prints a summary table.

Registered as the ``bbj-ingest-all`` console script in pyproject.toml.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import click

from bbj_rag.config import Settings
from bbj_rag.db import get_connection_from_settings
from bbj_rag.embedder import create_embedder
from bbj_rag.pipeline import run_pipeline
from bbj_rag.source_config import (
    SourceEntry,
    get_source_url_prefix,
    load_sources_config,
    resolve_data_dir,
    validate_sources,
)

logger = logging.getLogger(__name__)

_STATE_FILE = Path(".ingestion-state.json")


# ---------------------------------------------------------------------------
# Resume state helpers
# ---------------------------------------------------------------------------


def _load_resume_state(state_file: Path) -> dict[str, Any]:
    """Load resume state from JSON file.

    Returns a default dict if the file does not exist or is invalid.
    """
    if state_file.exists():
        try:
            with open(state_file) as f:
                return json.load(f)  # type: ignore[no-any-return]
        except (json.JSONDecodeError, OSError):
            pass
    return {"completed_sources": [], "failed_sources": {}}


def _save_resume_state(state_file: Path, state: dict[str, Any]) -> None:
    """Write resume state to JSON with indent=2."""
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Clean helper
# ---------------------------------------------------------------------------


def _clean_source_chunks(conn: Any, prefix: str) -> int:
    """Delete all chunks whose source_url starts with *prefix*.

    Returns the number of deleted rows.
    """
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM chunks WHERE source_url LIKE %s",
            (f"{prefix}%",),
        )
        count: int = cur.rowcount
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Parser factory
# ---------------------------------------------------------------------------


def _create_parser_for_source(
    source: SourceEntry,
    data_dir: Path,
    settings: Settings,
) -> Any:
    """Instantiate the correct parser for a source config entry.

    Uses lazy imports so that unused parser dependencies are never loaded.
    """
    parser_type = source.parser

    if parser_type == "flare":
        from bbj_rag.parsers.flare import FlareParser

        return FlareParser(
            content_dir=data_dir / source.paths[0] / "Content",
            project_dir=data_dir / source.paths[0],
        )

    if parser_type == "pdf":
        from bbj_rag.parsers.pdf import PdfParser

        return PdfParser(pdf_path=data_dir / source.paths[0])

    if parser_type == "mdx":
        from bbj_rag.parsers.mdx import MdxParser

        return MdxParser(
            docs_dir=data_dir / source.paths[0],
            source_prefix=source.name,
        )

    if parser_type == "bbj-source":
        from bbj_rag.parsers.bbj_source import BbjSourceParser

        return BbjSourceParser(
            source_dirs=[data_dir / p for p in source.paths],
        )

    if parser_type == "wordpress-advantage":
        from bbj_rag.parsers.wordpress import AdvantageParser

        return AdvantageParser(index_url=settings.advantage_index_url)

    if parser_type == "wordpress-kb":
        from bbj_rag.parsers.wordpress import KnowledgeBaseParser

        return KnowledgeBaseParser(index_url=settings.kb_index_url)

    if parser_type == "web-crawl":
        from bbj_rag.parsers.web_crawl import WebCrawlParser

        return WebCrawlParser()

    # Should never happen thanks to Pydantic validation, but guard anyway.
    msg = f"No parser implementation for type: {parser_type!r}"
    raise ValueError(msg)


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------


def _print_summary_table(
    results: list[dict[str, Any]],
    failures: list[str],
) -> None:
    """Print a formatted summary table of per-source ingestion results."""
    click.echo("")
    click.echo("=" * 70)
    click.echo(
        f"  {'Source':<28} {'Files':>7} {'Chunks':>8} {'Duration':>10}   {'Status':<8}"
    )
    click.echo("-" * 70)

    total_docs = 0
    total_chunks = 0
    total_duration = 0.0

    for r in results:
        docs = r.get("docs_parsed", 0)
        chunks = r.get("chunks_created", 0)
        duration = r.get("duration", 0.0)
        status = r.get("status", "OK")
        name = r.get("name", "?")

        total_docs += docs
        total_chunks += chunks
        total_duration += duration

        click.echo(
            f"  {name:<28} {docs:>7} {chunks:>8} {duration:>9.1f}s   {status:<8}"
        )

    click.echo("=" * 70)
    click.echo(
        f"  Total: {total_docs} docs, {total_chunks} chunks, {total_duration:.1f}s"
    )
    if failures:
        click.echo(f"  Failures: {', '.join(failures)}")
    click.echo("")


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------


@click.command()
@click.option(
    "--config",
    default="sources.toml",
    type=click.Path(exists=True),
    help="Path to sources.toml config file",
)
@click.option(
    "--clean",
    is_flag=True,
    help="Wipe existing chunks before re-ingesting each source",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Skip sources completed in a previous interrupted run",
)
@click.option(
    "--parallel",
    is_flag=True,
    help="Run file-based sources in parallel (experimental)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Per-file progress output",
)
@click.option(
    "--source",
    "source_names",
    multiple=True,
    help="Run only named sources (repeatable, e.g., --source flare --source pdf)",
)
@click.option(
    "--data-dir",
    "data_dir_override",
    default=None,
    type=click.Path(exists=True),
    help="Override data_dir from config",
)
def ingest_all(
    config: str,
    clean: bool,
    resume: bool,
    parallel: bool,
    verbose: bool,
    source_names: tuple[str, ...],
    data_dir_override: str | None,
) -> None:
    """Ingest all enabled documentation sources into pgvector.

    Reads sources.toml, validates paths and infrastructure, then runs
    the pipeline for each enabled source sequentially. Failed sources
    do not stop remaining sources.
    """
    # ---- 1. Configure logging ----
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # ---- 2. Load config ----
    if data_dir_override:
        os.environ["DATA_DIR"] = data_dir_override

    cfg = load_sources_config(Path(config))
    try:
        data_dir = resolve_data_dir(cfg)
    except ValueError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Config: {config}")
    click.echo(f"Data dir: {data_dir}")

    # ---- 3. Filter sources ----
    enabled_sources = [s for s in cfg.sources if s.enabled]

    if source_names:
        known_names = {s.name for s in cfg.sources}
        for name in source_names:
            if name not in known_names:
                click.echo(
                    f"ERROR: Unknown source name: {name!r}. "
                    f"Available: {sorted(known_names)}",
                    err=True,
                )
                sys.exit(1)
        enabled_sources = [s for s in enabled_sources if s.name in source_names]

    if not enabled_sources:
        click.echo("No enabled sources to ingest.", err=True)
        sys.exit(1)

    click.echo(f"Sources: {', '.join(s.name for s in enabled_sources)}")

    # ---- 4. Fail-fast validation ----
    errors = validate_sources(enabled_sources, data_dir)
    if errors:
        click.echo("Validation errors:", err=True)
        for err in errors:
            click.echo(f"  - {err}", err=True)
        sys.exit(1)

    settings = Settings()

    # Test database connectivity.
    try:
        test_conn = get_connection_from_settings(settings)
        test_conn.close()
    except Exception as exc:
        click.echo(f"ERROR: Database connection failed: {exc}", err=True)
        click.echo(
            "  Ensure PostgreSQL is running and BBJ_RAG_DB_* env vars are set.",
            err=True,
        )
        sys.exit(1)

    # Test embedder connectivity.
    try:
        embedder = create_embedder(settings)
        embedder.embed_batch(["test"])
    except Exception as exc:
        click.echo(f"ERROR: Embedder test failed: {exc}", err=True)
        click.echo(
            f"  Ensure Ollama is running with the model pulled: "
            f"ollama pull {settings.embedding_model}",
            err=True,
        )
        sys.exit(1)

    click.echo(
        f"Validation OK: {len(enabled_sources)} sources, "
        f"database connected, embedder ready"
    )

    # ---- 5. Resume state ----
    if resume:
        state = _load_resume_state(_STATE_FILE)
        completed = set(state.get("completed_sources", []))
        pre_skip = [s.name for s in enabled_sources if s.name in completed]
        if pre_skip:
            click.echo(f"Resuming -- skipping completed: {', '.join(pre_skip)}")
        enabled_sources = [s for s in enabled_sources if s.name not in completed]
    else:
        state = {"completed_sources": [], "failed_sources": {}}
        if _STATE_FILE.exists():
            _STATE_FILE.unlink()

    if not enabled_sources:
        click.echo("All sources already completed (resume mode). Nothing to do.")
        sys.exit(0)

    # ---- 6. Parallel mode check ----
    if parallel:
        click.echo(
            "WARNING: --parallel is not yet implemented. "
            "Falling back to sequential execution."
        )

    # ---- 7. Run ingestion loop ----
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    total = len(enabled_sources)

    for idx, source in enumerate(enabled_sources, 1):
        click.echo(f"\n[{idx}/{total}] {source.name} ...")
        t0 = time.monotonic()

        conn = get_connection_from_settings(settings)
        try:
            # Clean if requested.
            if clean:
                prefix = get_source_url_prefix(source)
                deleted = _clean_source_chunks(conn, prefix)
                click.echo(f"  Cleaned {deleted} existing chunks (prefix={prefix})")

            # Create parser.
            parser = _create_parser_for_source(source, data_dir, settings)

            # Run pipeline.
            stats = run_pipeline(
                parser=parser,
                embedder=embedder,
                conn=conn,
                batch_size=settings.embedding_batch_size,
                resume=False,
                max_tokens=settings.chunk_size,
                overlap_tokens=settings.chunk_overlap,
            )

            duration = time.monotonic() - t0
            click.echo(
                f"  Done: {stats['docs_parsed']} docs, "
                f"{stats['chunks_created']} chunks, "
                f"{duration:.1f}s"
            )

            results.append(
                {
                    "name": source.name,
                    "docs_parsed": stats["docs_parsed"],
                    "chunks_created": stats["chunks_created"],
                    "chunks_embedded": stats.get("chunks_embedded", 0),
                    "chunks_stored": stats.get("chunks_stored", 0),
                    "duration": duration,
                    "status": "OK",
                }
            )

            # Update resume state.
            state["completed_sources"].append(source.name)
            _save_resume_state(_STATE_FILE, state)

        except Exception as exc:
            duration = time.monotonic() - t0
            click.echo(f"  FAILED: {exc}", err=True)
            logger.exception("Source %s failed", source.name)

            failures.append(source.name)
            results.append(
                {
                    "name": source.name,
                    "docs_parsed": 0,
                    "chunks_created": 0,
                    "duration": duration,
                    "status": "FAILED",
                }
            )

            state["failed_sources"][source.name] = str(exc)
            _save_resume_state(_STATE_FILE, state)

        finally:
            conn.close()

    # ---- 8. Print summary table ----
    _print_summary_table(results, failures)

    # ---- 9. Exit code ----
    if failures:
        click.echo(
            f"{len(failures)} source(s) failed: {', '.join(failures)}",
            err=True,
        )
        sys.exit(1)

    click.echo("All sources ingested successfully.")
    sys.exit(0)


__all__ = ["ingest_all"]

if __name__ == "__main__":
    ingest_all()
