"""Tests for the BBj Intelligence document type classifier.

Covers DocType enum values, the rule-based scoring system, and
classify_doc_type() across all 7 document categories.
"""

from __future__ import annotations

from bbj_rag.intelligence.doc_types import (
    _RULES,
    DocType,
    DocTypeRule,
    classify_doc_type,
)

# ---------------------------------------------------------------------------
# DocType enum tests
# ---------------------------------------------------------------------------


class TestDocTypeEnum:
    def test_doctype_enum_values(self):
        """All 7 DocType values are hyphenated strings."""
        expected = {
            "api-reference",
            "concept",
            "example",
            "migration",
            "language-reference",
            "best-practice",
            "version-note",
        }
        actual = {str(dt) for dt in DocType}
        assert actual == expected
        assert len(DocType) == 7


# ---------------------------------------------------------------------------
# API reference classification
# ---------------------------------------------------------------------------


class TestApiReference:
    def test_api_reference_full_headings(self):
        """Description+Syntax+Parameters+Return Value -> api-reference."""
        result = classify_doc_type(
            headings=["Description", "Syntax", "Parameters", "Return Value"],
            content_relative_path="bbjobjects/Window/bbjwindow.htm",
            content="",
        )
        assert result == "api-reference"

    def test_api_reference_minimal(self):
        """Description+Syntax (no params) in bbjobjects path -> api-reference."""
        result = classify_doc_type(
            headings=["Description", "Syntax"],
            content_relative_path="bbjobjects/Window/bbjwindow.htm",
            content="",
        )
        assert result == "api-reference"

    def test_api_reference_without_syntax(self):
        """Description only -> NOT api-reference (falls to concept)."""
        result = classify_doc_type(
            headings=["Description"],
            content_relative_path="bbjobjects/Window/overview.htm",
            content="General overview of the window system.",
        )
        assert result != "api-reference"

    def test_classify_bbjobjects_path_boost(self):
        """bbjobjects/ path with Description+Syntax -> high-confidence api-reference."""
        result = classify_doc_type(
            headings=["Description", "Syntax"],
            content_relative_path="bbjobjects/Window/bbjwindow_addbutton.htm",
            content="",
        )
        assert result == "api-reference"


# ---------------------------------------------------------------------------
# Language reference classification
# ---------------------------------------------------------------------------


class TestLanguageReference:
    def test_language_reference_syntax_only(self):
        """Syntax without Parameters, in commands/ path -> language-reference."""
        result = classify_doc_type(
            headings=["Syntax", "Examples"],
            content_relative_path="commands/print_verb.htm",
            content="",
        )
        assert result == "language-reference"

    def test_language_reference_vs_api_reference(self):
        """Syntax+Parameters -> api-reference (not language-reference)."""
        result = classify_doc_type(
            headings=["Description", "Syntax", "Parameters"],
            content_relative_path="bbjobjects/SysGui/sysgui_sendmsg.htm",
            content="",
        )
        assert result == "api-reference"


# ---------------------------------------------------------------------------
# Migration classification
# ---------------------------------------------------------------------------


class TestMigration:
    def test_migration_headings(self):
        """'BBj-Specific Information' heading -> migration."""
        result = classify_doc_type(
            headings=["BBj-Specific Information", "Description"],
            content_relative_path="commands/open_verb.htm",
            content="",
        )
        assert result == "migration"

    def test_migration_content_pattern(self):
        """Content with 'migrating from' -> migration."""
        result = classify_doc_type(
            headings=["Overview"],
            content_relative_path="guides/upgrade.htm",
            content="This guide covers migrating from Visual PRO/5 to BBj.",
        )
        assert result == "migration"


# ---------------------------------------------------------------------------
# Version note classification
# ---------------------------------------------------------------------------


class TestVersionNote:
    def test_version_note_headings(self):
        """'Version History' heading -> version-note."""
        result = classify_doc_type(
            headings=["Version History", "Changes"],
            content_relative_path="release/notes.htm",
            content="",
        )
        assert result == "version-note"


# ---------------------------------------------------------------------------
# Example classification
# ---------------------------------------------------------------------------


class TestExample:
    def test_example_path(self):
        """Path with 'sample' and tutorial content -> example."""
        result = classify_doc_type(
            headings=["Example"],
            content_relative_path="samples/grid_tutorial.htm",
            content="In this tutorial we will build a data grid step 1...",
        )
        assert result == "example"


# ---------------------------------------------------------------------------
# Best practice classification
# ---------------------------------------------------------------------------


class TestBestPractice:
    def test_best_practice_content(self):
        """Content with 'best practice' keyword -> best-practice."""
        result = classify_doc_type(
            headings=["Guidelines"],
            content_relative_path="guides/coding_standards.htm",
            content="It is a best practice to always use explicit variable typing.",
        )
        assert result == "best-practice"


# ---------------------------------------------------------------------------
# Concept fallback
# ---------------------------------------------------------------------------


class TestConceptFallback:
    def test_concept_fallback(self):
        """No matching signals -> concept."""
        result = classify_doc_type(
            headings=["Introduction"],
            content_relative_path="overview/intro.htm",
            content="Welcome to the BBj documentation.",
        )
        assert result == "concept"


# ---------------------------------------------------------------------------
# Extensibility
# ---------------------------------------------------------------------------


class TestExtensibility:
    def test_extensibility_new_rule(self):
        """Adding a DocTypeRule to the registry works (data-driven design)."""
        # Save original rules
        original_len = len(_RULES)

        # Create a hypothetical new rule
        new_rule = DocTypeRule(
            doc_type=DocType.CONCEPT,  # reuse existing type for testing
            required_headings=frozenset({"Custom Heading"}),
            optional_headings=frozenset(),
            path_patterns=(),
            content_patterns=(),
            min_score=0.3,
        )

        # Verify the rule object is valid and frozen
        assert new_rule.doc_type == DocType.CONCEPT
        assert new_rule.min_score == 0.3
        assert isinstance(new_rule.required_headings, frozenset)

        # Verify we can add to registry without restructuring
        _RULES.append(new_rule)
        assert len(_RULES) == original_len + 1

        # Clean up
        _RULES.pop()
        assert len(_RULES) == original_len
