"""Summary report for BBj Intelligence generation tagging.

Prints and builds structured reports showing generation distribution,
deprecated/superseded counts, and untagged document counts.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

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


__all__ = [
    "build_report",
    "print_report",
]
