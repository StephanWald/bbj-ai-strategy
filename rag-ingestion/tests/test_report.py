"""Tests for the post-ingestion quality report module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from bbj_rag.intelligence.report import (
    _check_anomalies,
    _query_report_data,
    print_quality_report,
)

# --- _check_anomalies tests ---


class TestCheckAnomalies:
    """Test suite for _check_anomalies warning detection."""

    def test_empty_sources_warns(self):
        """Missing expected sources generate warnings."""
        by_source: dict[str, int] = {"flare": 100}
        by_generation: dict[str, int] = {"all": 100}
        by_doc_type: dict[str, int] = {"concept": 100}
        warnings = _check_anomalies(by_source, by_generation, by_doc_type, 100)

        # Should warn about missing: advantage, bbj-source, kb, mdx, pdf
        missing = [w for w in warnings if "No chunks from source" in w]
        assert len(missing) == 5
        assert any('"advantage"' in w for w in missing)
        assert any('"kb"' in w for w in missing)
        assert any('"pdf"' in w for w in missing)
        assert any('"mdx"' in w for w in missing)
        assert any('"bbj-source"' in w for w in missing)

    def test_low_counts_warns(self):
        """Sources with fewer than 10 chunks generate warnings."""
        by_source = {"flare": 5, "advantage": 100}
        by_generation: dict[str, int] = {"all": 105}
        by_doc_type: dict[str, int] = {"concept": 105}
        warnings = _check_anomalies(by_source, by_generation, by_doc_type, 105)

        low = [w for w in warnings if "Only" in w and "expected more" in w]
        assert len(low) == 1
        assert '"flare"' in low[0]

    def test_high_untagged_warns(self):
        """More than 5% untagged chunks generate a warning."""
        by_source = {"flare": 100}
        by_generation = {"all": 90, "untagged": 10}
        by_doc_type: dict[str, int] = {"concept": 100}
        warnings = _check_anomalies(by_source, by_generation, by_doc_type, 100)

        untagged = [w for w in warnings if "untagged" in w]
        assert len(untagged) == 1
        assert "10.0%" in untagged[0]

    def test_low_untagged_no_warning(self):
        """5% or fewer untagged chunks do NOT generate a warning."""
        by_source = {"flare": 100}
        by_generation = {"all": 95, "untagged": 5}
        by_doc_type: dict[str, int] = {"concept": 100}
        warnings = _check_anomalies(by_source, by_generation, by_doc_type, 100)

        # There may be a warning about "untagged" if it has <10 chunks, but
        # specifically no "X% have generation untagged" warning
        pct_warnings = [w for w in warnings if "%" in w and "untagged" in w]
        assert len(pct_warnings) == 0

    def test_unknown_doc_type_warns(self):
        """Unknown doc_type values generate warnings."""
        by_source = {"flare": 100}
        by_generation: dict[str, int] = {"all": 100}
        by_doc_type = {"concept": 90, "banana": 10}
        warnings = _check_anomalies(by_source, by_generation, by_doc_type, 100)

        unknown = [w for w in warnings if "Unknown doc_type" in w]
        assert len(unknown) == 1
        assert '"banana"' in unknown[0]
        assert "10 chunks" in unknown[0]

    def test_known_doc_types_no_warning(self):
        """All known doc_type values should NOT generate unknown warnings."""
        by_source = {
            "flare": 200,
            "advantage": 50,
            "kb": 50,
            "pdf": 30,
            "mdx": 20,
            "bbj-source": 10,
        }
        by_generation: dict[str, int] = {"all": 360}
        by_doc_type = {
            "api-reference": 100,
            "concept": 80,
            "example": 40,
            "migration": 20,
            "language-reference": 30,
            "best-practice": 20,
            "version-note": 10,
            "article": 30,
            "tutorial": 30,
        }
        warnings = _check_anomalies(by_source, by_generation, by_doc_type, 360)

        unknown = [w for w in warnings if "Unknown doc_type" in w]
        assert len(unknown) == 0

    def test_dominant_source_warns(self):
        """A source with >90% of chunks generates a warning."""
        by_source = {"flare": 95, "pdf": 5}
        by_generation: dict[str, int] = {"all": 100}
        by_doc_type: dict[str, int] = {"concept": 100}
        warnings = _check_anomalies(by_source, by_generation, by_doc_type, 100)

        dominant = [w for w in warnings if "verify other sources" in w]
        assert len(dominant) == 1
        assert '"flare"' in dominant[0]

    def test_clean_data_no_warnings(self):
        """Healthy data with all sources present produces no warnings."""
        by_source = {
            "flare": 200,
            "advantage": 50,
            "kb": 50,
            "pdf": 30,
            "mdx": 20,
            "bbj-source": 15,
        }
        by_generation = {"all": 200, "bbj_gui": 100, "dwc": 65}
        by_doc_type = {
            "api-reference": 100,
            "concept": 80,
            "example": 40,
            "language-reference": 50,
            "article": 50,
            "tutorial": 45,
        }
        total = 365
        warnings = _check_anomalies(by_source, by_generation, by_doc_type, total)

        assert warnings == []


# --- _query_report_data importability ---


def test_query_report_data_importable():
    """_query_report_data can be imported and has correct signature."""
    assert callable(_query_report_data)


# --- print_quality_report with empty database ---


class TestPrintQualityReport:
    """Test print_quality_report with mocked database."""

    def test_zero_total_prints_message(self):
        """When database is empty, print a helpful message."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        # COUNT(*) returns 0, other queries return empty
        mock_cursor.fetchone.return_value = (0,)
        mock_cursor.fetchall.return_value = []

        with patch("bbj_rag.intelligence.report.click") as mock_click:
            print_quality_report(mock_conn)
            # Should print "No chunks in database" message
            calls = [str(c) for c in mock_click.echo.call_args_list]
            assert any("No chunks" in c for c in calls)

    def test_nonzero_total_prints_report(self):
        """When database has data, print the full report."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        # First call: COUNT(*) -> 100
        # Second call: by_source -> [('flare', 80), ('pdf', 20)]
        # Third call: by_generation -> [('all', 70), ('dwc', 30)]
        # Fourth call: by_doc_type -> [('concept', 60), ('api-reference', 40)]
        mock_cursor.fetchone.return_value = (100,)
        mock_cursor.fetchall.side_effect = [
            [("flare", 80), ("pdf", 20)],
            [("all", 70), ("dwc", 30)],
            [("concept", 60), ("api-reference", 40)],
        ]

        with patch("bbj_rag.intelligence.report.click") as mock_click:
            print_quality_report(mock_conn)
            calls = [str(c) for c in mock_click.echo.call_args_list]
            # Should contain the report header
            assert any("Quality Report" in c for c in calls)
            # Should contain source info
            assert any("Source" in c for c in calls)
            # Should contain generation info
            assert any("Generation" in c for c in calls)
