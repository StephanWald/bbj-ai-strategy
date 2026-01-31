"""Rule-based document type classifier for BBj documentation.

Classifies documents into one of 7 semantic categories based on heading
structure, file path patterns, and content patterns.  The classifier uses
a data-driven rule registry: adding a new document type requires only adding
a new ``DocTypeRule`` entry to ``_RULES``, not restructuring the classifier.

The public API is ``classify_doc_type(headings, content_relative_path, content)``
which returns a hyphenated type string like ``"api-reference"``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum


class DocType(StrEnum):
    """Semantic document type categories.

    Values are hyphenated strings suitable for storage and filtering.
    """

    API_REFERENCE = "api-reference"
    CONCEPT = "concept"
    EXAMPLE = "example"
    MIGRATION = "migration"
    LANGUAGE_REFERENCE = "language-reference"
    BEST_PRACTICE = "best-practice"
    VERSION_NOTE = "version-note"


@dataclass(frozen=True)
class DocTypeRule:
    """A single classification rule in the rule registry.

    Rules are scored against document features (headings, path, content).
    The highest-scoring rule above its ``min_score`` wins.  If no rule
    exceeds its threshold, the document defaults to ``DocType.CONCEPT``.
    """

    doc_type: DocType
    required_headings: frozenset[str] = field(default_factory=frozenset)
    optional_headings: frozenset[str] = field(default_factory=frozenset)
    path_patterns: tuple[str, ...] = ()
    content_patterns: tuple[str, ...] = ()
    min_score: float = 0.5


# ---------------------------------------------------------------------------
# Rule registry -- ordered by specificity (most specific first)
# ---------------------------------------------------------------------------

_RULES: list[DocTypeRule] = [
    # API reference: Description + Syntax + optional Parameters/Return Value
    # Matches 93.7% of bbjobjects content.
    DocTypeRule(
        doc_type=DocType.API_REFERENCE,
        required_headings=frozenset({"Description", "Syntax"}),
        optional_headings=frozenset(
            {"Parameters", "Return Value", "Example", "Remarks"}
        ),
        path_patterns=(r"bbjobjects/", r"bbjinterfaces/", r"bbjevents/", r"API/"),
    ),
    # Version note: release notes, changelogs, version history
    # Lower min_score (0.15) -- no required headings, relies on optional + path/content.
    DocTypeRule(
        doc_type=DocType.VERSION_NOTE,
        required_headings=frozenset(),
        optional_headings=frozenset(
            {"Version History", "What's New", "Release Notes", "Changes"}
        ),
        path_patterns=(r"release", r"whatsnew", r"version"),
        content_patterns=(r"(?i)version\s+\d+\.\d+",),
        min_score=0.15,
    ),
    # Migration: converting from other products / BBj-specific information
    # Lower min_score (0.15) -- no required headings, relies on optional + content.
    DocTypeRule(
        doc_type=DocType.MIGRATION,
        required_headings=frozenset(),
        optional_headings=frozenset(
            {"BBj-Specific Information", "Converting", "Migration", "Migrating"}
        ),
        content_patterns=(
            r"(?i)migrat",
            r"(?i)convert.*from",
            r"(?i)bbj-specific",
        ),
        min_score=0.15,
    ),
    # Example / tutorial: sample code, step-by-step guides
    # Lower min_score (0.15) -- no required headings, relies on optional + path/content.
    DocTypeRule(
        doc_type=DocType.EXAMPLE,
        required_headings=frozenset(),
        optional_headings=frozenset({"Example", "Sample", "Tutorial"}),
        path_patterns=(r"sample", r"example", r"tutorial", r"demo"),
        content_patterns=(r"(?i)step\s*\d", r"(?i)tutorial"),
        min_score=0.15,
    ),
    # Best practice: recommendations, guidelines, tips
    # Lower min_score (0.15) -- no required headings, relies on optional + content.
    DocTypeRule(
        doc_type=DocType.BEST_PRACTICE,
        required_headings=frozenset(),
        optional_headings=frozenset(
            {"Best Practice", "Recommendation", "Guidelines", "Tips"}
        ),
        content_patterns=(
            r"(?i)best\s*practice",
            r"(?i)recommend",
            r"(?i)guideline",
        ),
        min_score=0.15,
    ),
    # Language reference: Syntax present but NOT Parameters/Return Value
    # (distinguishes from API reference)
    DocTypeRule(
        doc_type=DocType.LANGUAGE_REFERENCE,
        required_headings=frozenset({"Syntax"}),
        optional_headings=frozenset({"Examples", "Description"}),
        path_patterns=(r"commands/", r"events/", r"sendmsg/", r"mnemonic/"),
    ),
    # Concept: catch-all default (no requirements)
    DocTypeRule(
        doc_type=DocType.CONCEPT,
        required_headings=frozenset(),
        optional_headings=frozenset(),
        min_score=0.0,  # always matches as fallback
    ),
]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _score_rule(
    rule: DocTypeRule,
    headings: list[str],
    path: str,
    content: str,
) -> float:
    """Score a rule against document features.

    Returns 0.0 immediately if any required heading is missing (hard fail).
    Otherwise accumulates points from optional headings, path patterns,
    and content patterns.
    """
    heading_set = set(headings)

    # Hard fail: all required headings must be present
    if rule.required_headings and not rule.required_headings.issubset(heading_set):
        return 0.0

    score = 0.0

    # Required headings present: +0.4
    if rule.required_headings:
        score += 0.4

    # Optional headings: +0.15 each, capped at 0.45
    optional_bonus = 0.0
    for h in rule.optional_headings:
        if h in heading_set:
            optional_bonus += 0.15
    score += min(optional_bonus, 0.45)

    # Path pattern match: +0.2
    for pat in rule.path_patterns:
        if re.search(pat, path):
            score += 0.2
            break

    # Content pattern match: +0.15
    for pat in rule.content_patterns:
        if re.search(pat, content):
            score += 0.15
            break

    return score


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_doc_type(
    headings: list[str],
    content_relative_path: str,
    content: str,
) -> str:
    """Classify a document into one of 7 semantic categories.

    Uses a data-driven rule registry with weighted scoring.  The
    highest-scoring rule above its ``min_score`` threshold wins.
    Falls back to ``DocType.CONCEPT`` if nothing matches.

    Args:
        headings: List of heading text strings extracted from the document
            (e.g. ``["Description", "Syntax", "Parameters"]``).
        content_relative_path: Path relative to the Flare Content/ directory
            (e.g. ``"bbjobjects/Window/bbjwindow.htm"``).
        content: Plain-text or markdown content of the document.

    Returns:
        Hyphenated type string (e.g. ``"api-reference"``).
    """
    heading_set = set(headings)

    best_type = DocType.CONCEPT
    best_score = 0.0

    for rule in _RULES:
        score = _score_rule(rule, headings, content_relative_path, content)

        # API reference boost: when Parameters or Return Value present
        # alongside Syntax, boost API_REFERENCE to ensure it wins over
        # LANGUAGE_REFERENCE.
        if rule.doc_type == DocType.API_REFERENCE and (
            {"Parameters", "Return Value"} & heading_set and "Syntax" in heading_set
        ):
            score += 0.2

        if score > best_score and score >= rule.min_score:
            best_score = score
            best_type = rule.doc_type

    return str(best_type)


__all__ = [
    "DocType",
    "DocTypeRule",
    "classify_doc_type",
]
