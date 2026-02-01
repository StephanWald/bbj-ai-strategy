"""Summary report for BBj Intelligence generation tagging.

Prints and builds structured reports showing generation distribution,
deprecated/superseded counts, and untagged document counts.

Also provides post-ingestion quality reporting via database queries:
chunk distributions by source, generation, and document type with
automated anomaly warnings.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import click
import psycopg

from bbj_rag.intelligence.generations import Generation
from bbj_rag.models import Document


def build_report(documents: list[Document]) -> dict[str, Any]:
    """Build a structured report of generation and lifecycle distribution.

    Returns:
        Dictionary with keys:
            total: int
            generation_counts: dict mapping generation label -> count
            untagged_count: int
            deprecated_count: int
            superseded_count: int
    """
    total = len(documents)

    # Count generation occurrences (a document can have multiple generations)
    gen_counter: Counter[str] = Counter()
    untagged = 0
    deprecated = 0
    superseded = 0

    for doc in documents:
        if doc.generations == ["untagged"]:
            untagged += 1
        else:
            for g in doc.generations:
                gen_counter[g] += 1

        # Check conditions in metadata for deprecated/superseded
        conditions_str = doc.metadata.get("conditions", "")
        if "Primary.Deprecated" in conditions_str:
            deprecated += 1
        if "Primary.Superseded" in conditions_str:
            superseded += 1

        # Also check the deprecated field if present
        if doc.deprecated and deprecated == 0:
            deprecated += 1

    # Build ordered generation counts (canonical order + untagged)
    generation_counts: dict[str, int] = {}
    for gen in Generation:
        count = gen_counter.get(str(gen), 0)
        if count > 0:
            generation_counts[str(gen)] = count
    if untagged > 0:
        generation_counts["untagged"] = untagged

    return {
        "total": total,
        "generation_counts": generation_counts,
        "untagged_count": untagged,
        "deprecated_count": deprecated,
        "superseded_count": superseded,
    }


def print_report(documents: list[Document]) -> None:
    """Print a formatted summary report to stdout.

    Shows total documents, generation distribution with percentages,
    and deprecated/superseded counts.
    """
    report = build_report(documents)
    total = report["total"]

    print("=== BBj Intelligence Report ===")
    print(f"Documents processed: {total:,}")
    print()

    if total == 0:
        print("No documents to report on.")
        return

    print("Generation distribution:")
    for gen_label, count in report["generation_counts"].items():
        pct = (count / total) * 100
        print(f"  {gen_label:<14} {count:>6,}  ({pct:.1f}%)")

    print()
    print(
        f"Deprecated: {report['deprecated_count']}  |  "
        f"Superseded: {report['superseded_count']}"
    )
    print(f"Untagged (no generation resolved): {report['untagged_count']}")


def _query_report_data(
    conn: psycopg.Connection[object],
) -> tuple[dict[str, int], dict[str, int], dict[str, int], int]:
    """Query chunk distribution from the database.

    Returns (by_source, by_generation, by_doc_type, total).
    """
    with conn.cursor() as cur:
        # Total count
        cur.execute("SELECT COUNT(*) FROM chunks")
        row = cur.fetchone()
        total = int(row[0]) if row else 0  # type: ignore[index]

        # By source (derived from source_url prefix)
        cur.execute("""
            SELECT
                CASE
                    WHEN source_url LIKE 'flare://%%' THEN 'flare'
                    WHEN source_url LIKE '%%basis.cloud/advantage%%' THEN 'advantage'
                    WHEN source_url LIKE '%%basis.cloud/knowledge%%' THEN 'kb'
                    WHEN source_url LIKE 'pdf://%%' THEN 'pdf'
                    WHEN source_url LIKE 'file://%%' THEN 'bbj-source'
                    WHEN source_url LIKE 'mdx://%%' THEN 'mdx'
                    ELSE 'unknown'
                END AS source,
                COUNT(*) AS cnt
            FROM chunks
            GROUP BY source
            ORDER BY cnt DESC
        """)
        by_source = {
            str(r[0]): int(r[1])  # type: ignore[index]
            for r in cur.fetchall()
        }

        # By generation (unnest array)
        cur.execute("""
            SELECT g, COUNT(*) AS cnt
            FROM chunks, unnest(generations) AS g
            GROUP BY g
            ORDER BY cnt DESC
        """)
        by_generation = {
            str(r[0]): int(r[1])  # type: ignore[index]
            for r in cur.fetchall()
        }

        # By doc_type
        cur.execute("""
            SELECT doc_type, COUNT(*) AS cnt
            FROM chunks
            GROUP BY doc_type
            ORDER BY cnt DESC
        """)
        by_doc_type = {
            str(r[0]): int(r[1])  # type: ignore[index]
            for r in cur.fetchall()
        }

    return by_source, by_generation, by_doc_type, total


def _check_anomalies(
    by_source: dict[str, int],
    by_generation: dict[str, int],
    by_doc_type: dict[str, int],
    total: int,
) -> list[str]:
    """Generate warning messages for quality anomalies."""
    warnings: list[str] = []

    # Empty expected sources
    expected_sources = {"flare", "advantage", "kb", "pdf", "mdx", "bbj-source"}
    for src in sorted(expected_sources):
        if by_source.get(src, 0) == 0:
            warnings.append(f'No chunks from source "{src}" -- verify configuration')

    # Suspiciously low counts
    for src, count in by_source.items():
        if 0 < count < 10:
            warnings.append(f'Only {count} chunks from "{src}" -- expected more')

    # Untagged generation percentage (>5%)
    untagged = by_generation.get("untagged", 0)
    if total > 0 and untagged / total > 0.05:
        pct = (untagged / total) * 100
        warnings.append(f'{untagged} chunks ({pct:.1f}%) have generation "untagged"')

    # Unknown doc types
    known_types = {
        "api-reference",
        "concept",
        "example",
        "migration",
        "language-reference",
        "best-practice",
        "version-note",
        "article",
        "tutorial",
    }
    for dt in by_doc_type:
        if dt not in known_types:
            warnings.append(f'Unknown doc_type "{dt}" ({by_doc_type[dt]} chunks)')

    # Dominant source (>90%)
    if total > 0:
        for src, count in by_source.items():
            if count / total > 0.90:
                warnings.append(
                    f'Source "{src}" has {count / total * 100:.0f}% of all chunks'
                    f" -- verify other sources ingested"
                )

    return warnings


def print_quality_report(conn: psycopg.Connection[object]) -> None:
    """Print a post-ingestion quality report from database contents.

    Queries chunk distributions by source, generation, and document type.
    Includes automated anomaly warnings for empty sources, low counts,
    high untagged percentage, unknown doc types, and dominant sources.
    """
    by_source, by_generation, by_doc_type, total = _query_report_data(conn)

    if total == 0:
        click.echo("No chunks in database. Run ingestion first.")
        return

    click.echo("=== BBj RAG Quality Report ===")
    click.echo()

    # --- By Source ---
    click.echo("Chunks by Source:")
    # Determine column widths
    max_label = max((len(k) for k in by_source), default=0)
    max_count = max((len(f"{v:,}") for v in by_source.values()), default=0)
    for src, count in by_source.items():
        pct = (count / total) * 100
        click.echo(f"  {src:<{max_label}}  {count:>{max_count},}  ({pct:.1f}%)")
    sep_width = max_label + max_count + 12
    click.echo(f"  {'─' * sep_width}")
    click.echo(f"  {'Total':<{max_label}}  {total:>{max_count},}")
    click.echo()

    # --- By Generation ---
    click.echo("Chunks by Generation:")
    if by_generation:
        max_label_g = max(len(k) for k in by_generation)
        max_count_g = max(len(f"{v:,}") for v in by_generation.values())
        for gen, count in by_generation.items():
            # Note: generation totals can exceed chunk total (multi-gen chunks)
            pct = (count / total) * 100
            click.echo(f"  {gen:<{max_label_g}}  {count:>{max_count_g},}  ({pct:.1f}%)")
    click.echo()

    # --- By Doc Type ---
    click.echo("Chunks by Document Type:")
    if by_doc_type:
        max_label_d = max(len(k) for k in by_doc_type)
        max_count_d = max(len(f"{v:,}") for v in by_doc_type.values())
        for dt, count in by_doc_type.items():
            pct = (count / total) * 100
            click.echo(f"  {dt:<{max_label_d}}  {count:>{max_count_d},}  ({pct:.1f}%)")
    click.echo()

    # --- Warnings ---
    warnings = _check_anomalies(by_source, by_generation, by_doc_type, total)
    if warnings:
        click.echo("Warnings:")
        for w in warnings:
            click.echo(f"  [!] {w}")
        click.echo()


__all__ = [
    "_check_anomalies",
    "_query_report_data",
    "build_report",
    "print_quality_report",
    "print_report",
]
