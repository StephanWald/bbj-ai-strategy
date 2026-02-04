"""Standalone orchestration CLI for all-source ingestion.

Reads ``sources.toml``, validates all paths and dependencies up front,
then runs the existing ``run_pipeline()`` for each enabled source.
Tracks progress for resume capability and prints a summary table.

Registered as the ``bbj-ingest-all`` console script in pyproject.toml.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import click

from bbj_rag.chunker import chunk_document
from bbj_rag.config import Settings
from bbj_rag.db import get_connection_from_settings
from bbj_rag.embedder import create_embedder
from bbj_rag.intelligence import (
    build_context_header,
    classify_doc_type,
    extract_heading_hierarchy,
    tag_generation,
)
from bbj_rag.models import Chunk
from bbj_rag.parallel import IngestResult, ParallelIngestor
from bbj_rag.pipeline import run_pipeline
from bbj_rag.source_config import (
    SourceEntry,
    get_source_url_prefix,
    load_sources_config,
    resolve_data_dir,
    validate_sources,
)
from bbj_rag.url_mapping import classify_source_type, map_display_url

logger = logging.getLogger(__name__)

_STATE_FILE = Path(".ingestion-state.json")
_FAILURE_LOG = Path(".ingestion-failures.json")


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
# Chunk collection (for parallel mode)
# ---------------------------------------------------------------------------


def _apply_intelligence(
    doc_source_url: str,
    doc_content: str,
    doc_metadata: dict[str, str],
) -> tuple[list[str], bool, str, str]:
    """Apply intelligence to derive generations, deprecated, doc_type.

    Returns (generations, deprecated, doc_type, context_header).
    """
    content_relative_path = ""
    if doc_source_url.startswith("flare://Content/"):
        content_relative_path = doc_source_url[len("flare://Content/") :]

    conditions_str = doc_metadata.get("conditions", "")
    conditions = [c.strip() for c in conditions_str.split(",") if c.strip()]

    generations, deprecated = tag_generation(
        content_relative_path, conditions, doc_content
    )

    headings = extract_heading_hierarchy(doc_content)
    doc_type = classify_doc_type(headings, content_relative_path, doc_content)

    section_path = doc_metadata.get("section_path", "")
    context_header = build_context_header(section_path, "", "")

    return generations, deprecated, doc_type, context_header


def _collect_chunks_from_source(
    parser: Any,
    max_tokens: int,
    overlap_tokens: int,
) -> tuple[list[Chunk], int]:
    """Parse and chunk a source without embedding.

    Returns (chunks, docs_parsed).
    """
    chunks: list[Chunk] = []
    docs_parsed = 0

    for doc in parser.parse():
        docs_parsed += 1

        # Apply intelligence if needed (same logic as pipeline.py)
        if doc.doc_type and doc.doc_type != "web_crawl":
            pass
        else:
            generations, deprecated, doc_type, _ = _apply_intelligence(
                doc.source_url, doc.content, doc.metadata
            )
            doc = doc.model_copy(
                update={
                    "generations": generations,
                    "deprecated": deprecated,
                    "doc_type": doc_type,
                }
            )

        # Compute source_type and display_url
        source_type = classify_source_type(doc.source_url)
        display_url = map_display_url(doc.source_url)
        doc = doc.model_copy(
            update={
                "source_type": source_type,
                "display_url": display_url,
            }
        )

        # Chunk the document
        doc_chunks = chunk_document(doc, max_tokens, overlap_tokens)
        chunks.extend(doc_chunks)

    return chunks, docs_parsed


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------


def _print_summary_table(
    results: list[dict[str, Any]],
    failures: list[str],
    mode: str,
) -> None:
    """Print a formatted summary table of per-source ingestion results."""
    click.echo("")
    click.echo("=" * 80)
    click.echo(
        f"  {'Source':<24} {'Files':>7} {'Chunks':>8} "
        f"{'Duration':>10}   {'Mode':<14} {'Status':<8}"
    )
    click.echo("-" * 80)

    total_docs = 0
    total_chunks = 0
    total_duration = 0.0

    for r in results:
        docs = r.get("docs_parsed", 0)
        chunks = r.get("chunks_created", 0)
        duration = r.get("duration", 0.0)
        status = r.get("status", "OK")
        name = r.get("name", "?")
        result_mode = r.get("mode", mode)

        total_docs += docs
        total_chunks += chunks
        total_duration += duration

        click.echo(
            f"  {name:<24} {docs:>7} {chunks:>8} "
            f"{duration:>9.1f}s   {result_mode:<14} {status:<8}"
        )

    click.echo("=" * 80)
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
    "--sequential",
    is_flag=True,
    help="Run sources sequentially instead of parallel (default: parallel)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Per-file progress output",
)
@click.option(
    "--workers",
    default=None,
    type=int,
    help="Number of parallel workers (default: 4, max: 8)",
)
@click.option(
    "--retry-failed",
    is_flag=True,
    help="Only process items from previous failure log",
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
    sequential: bool,
    verbose: bool,
    source_names: tuple[str, ...],
    data_dir_override: str | None,
    workers: int | None,
    retry_failed: bool,
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

    # ---- 6. Handle --retry-failed mode ----
    failure_log_path = Path(settings.ingest_failure_log)
    if retry_failed:
        if not failure_log_path.exists():
            click.echo("No failure log found. Nothing to retry.")
            sys.exit(0)
        failed_entries = ParallelIngestor.load_failure_log(failure_log_path)
        if not failed_entries:
            click.echo("Failure log is empty. Nothing to retry.")
            sys.exit(0)
        click.echo(f"Retrying {len(failed_entries)} failed chunks...")
        # For retry mode, we'll filter chunks by content_hash from failure log
        failed_hashes = {e["content_hash"] for e in failed_entries}
    else:
        failed_hashes = set()

    # ---- 7. Resolve worker count ----
    num_workers = workers or settings.ingest_workers
    if num_workers > settings.ingest_max_workers:
        click.echo(
            f"Warning: Capping workers at {settings.ingest_max_workers}",
            err=True,
        )
        num_workers = settings.ingest_max_workers

    mode_label = "sequential" if sequential else f"parallel ({num_workers}w)"
    click.echo(f"Mode: {mode_label}")

    # ---- 8. Run ingestion loop ----
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    total = len(enabled_sources)
    any_batches_failed = False

    for idx, source in enumerate(enabled_sources, 1):
        click.echo(f"\n[{idx}/{total}] {source.name} ...")
        t0 = time.monotonic()

        conn = get_connection_from_settings(settings)
        try:
            # Clean if requested (not in retry mode).
            if clean and not retry_failed:
                prefix = get_source_url_prefix(source)
                deleted = _clean_source_chunks(conn, prefix)
                click.echo(f"  Cleaned {deleted} existing chunks (prefix={prefix})")

            # Create parser.
            parser = _create_parser_for_source(source, data_dir, settings)

            if sequential:
                # ---- Sequential mode: use existing run_pipeline ----
                click.echo("  (sequential mode)")
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
                        "mode": "sequential",
                        "status": "OK",
                    }
                )

            else:
                # ---- Parallel mode: collect chunks then use ParallelIngestor ----
                # Step 1: Collect all chunks from source (parse + chunk, no embed)
                chunks, docs_parsed = _collect_chunks_from_source(
                    parser,
                    max_tokens=settings.chunk_size,
                    overlap_tokens=settings.chunk_overlap,
                )

                # Filter to failed chunks only if in retry mode
                if retry_failed:
                    chunks = [c for c in chunks if c.content_hash in failed_hashes]
                    if not chunks:
                        click.echo(f"  No failed chunks for {source.name}, skipping")
                        duration = time.monotonic() - t0
                        results.append(
                            {
                                "name": source.name,
                                "docs_parsed": docs_parsed,
                                "chunks_created": 0,
                                "duration": duration,
                                "mode": f"parallel ({num_workers}w)",
                                "status": "SKIP",
                            }
                        )
                        continue

                click.echo(f"  Collected {len(chunks)} chunks from {docs_parsed} docs")

                # Step 2: Run parallel ingestion
                ingestor = ParallelIngestor(
                    settings=settings,
                    num_workers=num_workers,
                    batch_size=settings.embedding_batch_size,
                    verbose=verbose,
                )

                # Close sync connection before async work
                conn.close()

                result: IngestResult = asyncio.run(
                    ingestor.ingest_chunks(chunks, settings.database_url)
                )

                duration = time.monotonic() - t0
                click.echo(
                    f"  Done: {docs_parsed} docs, "
                    f"{result.chunks_embedded} embedded, "
                    f"{result.chunks_stored} stored, "
                    f"{duration:.1f}s"
                )

                # Handle failures
                if result.batches_failed > 0:
                    any_batches_failed = True
                    ParallelIngestor.save_failure_log(
                        result.failed_chunks,
                        failure_log_path,
                        "batch_failed",
                    )
                    click.echo(
                        f"  WARNING: {result.batches_failed} batches failed "
                        f"({len(result.failed_chunks)} chunks)",
                        err=True,
                    )

                results.append(
                    {
                        "name": source.name,
                        "docs_parsed": docs_parsed,
                        "chunks_created": len(chunks),
                        "chunks_embedded": result.chunks_embedded,
                        "chunks_stored": result.chunks_stored,
                        "duration": duration,
                        "mode": f"parallel ({num_workers}w)",
                        "status": "PARTIAL" if result.batches_failed > 0 else "OK",
                    }
                )

                # Reopen connection for resume state update
                conn = get_connection_from_settings(settings)

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
                    "mode": mode_label,
                    "status": "FAILED",
                }
            )

            state["failed_sources"][source.name] = str(exc)
            _save_resume_state(_STATE_FILE, state)

        finally:
            try:
                conn.close()
            except Exception:
                pass  # May already be closed in parallel mode

    # ---- 9. Print summary table ----
    _print_summary_table(results, failures, mode_label)

    # ---- 10. Exit code ----
    if failures:
        click.echo(
            f"{len(failures)} source(s) failed: {', '.join(failures)}",
            err=True,
        )
        sys.exit(1)

    if any_batches_failed:
        click.echo(
            "Some batches failed. Re-run with --retry-failed to process failed chunks.",
            err=True,
        )
        sys.exit(1)

    # Clear failure log on complete success (including retry mode)
    if retry_failed and failure_log_path.exists():
        failure_log_path.unlink()
        click.echo("Cleared failure log after successful retry.")

    click.echo("All sources ingested successfully.")
    sys.exit(0)


__all__ = ["ingest_all"]

if __name__ == "__main__":
    ingest_all()
