"""Tests for the BBj Intelligence generation tagger.

Covers signal extractors (path, condition, content), signal resolution,
the tag_generation() integration function, model field updates, and
the report module.
"""

from __future__ import annotations

from bbj_rag.intelligence.generations import (
    Generation,
    Signal,
    resolve_signals,
    signal_from_conditions,
    signal_from_content,
    signal_from_path,
    tag_generation,
)
from bbj_rag.intelligence.report import build_report
from bbj_rag.models import Chunk, Document

# ---------------------------------------------------------------------------
# Path signal extractor tests
# ---------------------------------------------------------------------------


class TestSignalFromPath:
    def test_bbjobjects(self):
        """Path starting with bbjobjects/ yields bbj_gui signal."""
        signals = signal_from_path("bbjobjects/Window/bbjwindow.htm")
        assert len(signals) == 1
        assert signals[0].generation == Generation.BBJ_GUI
        assert signals[0].weight == 0.6
        assert signals[0].source == "file_path"

    def test_dwc(self):
        """Path starting with dwc/ yields dwc signal."""
        signals = signal_from_path("dwc/overview.htm")
        assert len(signals) == 1
        assert signals[0].generation == Generation.DWC

    def test_commands_bbj_override(self):
        """commands/bbj-commands/ overrides general commands/ -> bbj_gui."""
        signals = signal_from_path("commands/bbj-commands/bbjapi.htm")
        assert len(signals) == 1
        assert signals[0].generation == Generation.BBJ_GUI

    def test_commands_general(self):
        """Plain commands/ path yields all."""
        signals = signal_from_path("commands/let.htm")
        assert len(signals) == 1
        assert signals[0].generation == Generation.ALL

    def test_unknown_path(self):
        """Path not matching any known prefix yields empty list."""
        signals = signal_from_path("unknown/dir/file.htm")
        assert signals == []

    def test_vpro5_guibuild(self):
        """guibuild/ path yields vpro5."""
        signals = signal_from_path("guibuild/toolbar.htm")
        assert len(signals) == 1
        assert signals[0].generation == Generation.VPRO5

    def test_character_terminal(self):
        """mnemonic/terminal/ path yields character."""
        signals = signal_from_path("mnemonic/terminal/bell.htm")
        assert len(signals) == 1
        assert signals[0].generation == Generation.CHARACTER

    def test_bbj_variables_override(self):
        """commands/bbj-variables/ overrides commands/ -> bbj_gui."""
        signals = signal_from_path("commands/bbj-variables/bbjapi.htm")
        assert len(signals) == 1
        assert signals[0].generation == Generation.BBJ_GUI

    def test_bbutil(self):
        """bbutil/ path yields all."""
        signals = signal_from_path("bbutil/somefile.htm")
        assert len(signals) == 1
        assert signals[0].generation == Generation.ALL


# ---------------------------------------------------------------------------
# Condition signal extractor tests
# ---------------------------------------------------------------------------


class TestSignalFromConditions:
    def test_guibuild_chm(self):
        """Primary.guibuild_chm yields vpro5."""
        signals = signal_from_conditions(["Primary.guibuild_chm"])
        assert len(signals) == 1
        assert signals[0].generation == Generation.VPRO5
        assert signals[0].weight == 0.5
        assert signals[0].source == "condition_tag"

    def test_basis_help_no_signal(self):
        """Primary.BASISHelp alone yields empty list (not discriminating)."""
        signals = signal_from_conditions(["Primary.BASISHelp"])
        assert signals == []

    def test_empty_conditions(self):
        """Empty condition list yields empty signals."""
        signals = signal_from_conditions([])
        assert signals == []

    def test_deprecated_not_signal(self):
        """Primary.Deprecated is not a generation signal."""
        signals = signal_from_conditions(["Primary.Deprecated"])
        assert signals == []

    def test_superseded_not_signal(self):
        """Primary.Superseded is not a generation signal."""
        signals = signal_from_conditions(["Primary.Superseded"])
        assert signals == []

    def test_config_chm(self):
        """Primary.config_chm yields all with weight 0.3."""
        signals = signal_from_conditions(["Primary.config_chm"])
        assert len(signals) == 1
        assert signals[0].generation == Generation.ALL
        assert signals[0].weight == 0.3

    def test_multiple_conditions(self):
        """Multiple relevant conditions produce multiple signals."""
        signals = signal_from_conditions(
            ["Primary.BASISHelp", "Primary.guibuild_chm", "Primary.resbuild_chm"]
        )
        # BASISHelp produces nothing; both chm tags produce vpro5
        assert len(signals) == 2
        assert all(s.generation == Generation.VPRO5 for s in signals)


# ---------------------------------------------------------------------------
# Content pattern signal extractor tests
# ---------------------------------------------------------------------------


class TestSignalFromContent:
    def test_bbj_gui_pattern(self):
        """Content with BBjAPI() yields bbj_gui."""
        signals = signal_from_content("Call BBjAPI() to get the API.")
        assert len(signals) == 1
        assert signals[0].generation == Generation.BBJ_GUI
        assert signals[0].weight == 0.4
        assert signals[0].source == "content_pattern"

    def test_dwc_pattern(self):
        """Content with Dynamic Web Client yields dwc."""
        signals = signal_from_content("The Dynamic Web Client renders components.")
        assert len(signals) == 1
        assert signals[0].generation == Generation.DWC

    def test_no_match(self):
        """Plain text without patterns yields empty list."""
        signals = signal_from_content("This is plain documentation text.")
        assert signals == []

    def test_multiple_same_gen_single_signal(self):
        """Multiple bbj_gui patterns yield only one bbj_gui signal."""
        signals = signal_from_content(
            "BBjAPI() returns BBjSysGui and uses PROCESS_EVENTS"
        )
        bbj_gui_signals = [s for s in signals if s.generation == Generation.BBJ_GUI]
        assert len(bbj_gui_signals) == 1

    def test_vpro5_pattern(self):
        """Content with Visual PRO/5 yields vpro5."""
        signals = signal_from_content("Visual PRO/5 GUI Builder window.")
        vpro5_signals = [s for s in signals if s.generation == Generation.VPRO5]
        assert len(vpro5_signals) == 1

    def test_character_mode_pattern(self):
        """Content with character mode yields character."""
        signals = signal_from_content("Run in character mode for legacy.")
        assert len(signals) == 1
        assert signals[0].generation == Generation.CHARACTER

    def test_case_insensitive_process_events(self):
        """PROCESS_EVENTS is case-insensitive."""
        signals = signal_from_content("process_events loop runs.")
        assert any(s.generation == Generation.BBJ_GUI for s in signals)


# ---------------------------------------------------------------------------
# Signal resolution tests
# ---------------------------------------------------------------------------


class TestResolveSignals:
    def test_single_above_threshold(self):
        """One signal above threshold returns its generation."""
        signals = [Signal(generation=Generation.DWC, weight=0.6, source="path")]
        result = resolve_signals(signals)
        assert result == ["dwc"]

    def test_multiple_generations(self):
        """Signals for two different generations returns both sorted."""
        signals = [
            Signal(generation=Generation.DWC, weight=0.6, source="path"),
            Signal(generation=Generation.BBJ_GUI, weight=0.5, source="cond"),
        ]
        result = resolve_signals(signals)
        assert result == ["bbj_gui", "dwc"]

    def test_below_threshold(self):
        """Signal with weight below 0.3 returns untagged."""
        signals = [Signal(generation=Generation.ALL, weight=0.1, source="x")]
        result = resolve_signals(signals)
        assert result == ["untagged"]

    def test_empty_signals(self):
        """No signals at all returns untagged."""
        result = resolve_signals([])
        assert result == ["untagged"]

    def test_aggregation(self):
        """Two signals for same generation aggregate weights."""
        signals = [
            Signal(generation=Generation.VPRO5, weight=0.2, source="a"),
            Signal(generation=Generation.VPRO5, weight=0.2, source="b"),
        ]
        # Aggregated: 0.4 >= 0.3 threshold
        result = resolve_signals(signals)
        assert result == ["vpro5"]

    def test_returns_strings_not_enums(self):
        """resolve_signals returns list[str], not list[Generation]."""
        signals = [Signal(generation=Generation.ALL, weight=0.6, source="path")]
        result = resolve_signals(signals)
        assert isinstance(result[0], str)
        assert result[0] == "all"


# ---------------------------------------------------------------------------
# Integration: tag_generation() tests
# ---------------------------------------------------------------------------


class TestTagGeneration:
    def test_bbjobjects_path(self):
        """BBj objects path + BASISHelp + BBjAPI content -> bbj_gui."""
        gens, deprecated = tag_generation(
            "bbjobjects/Window/bbjwindow.htm",
            ["Primary.BASISHelp"],
            "BBjAPI() demo",
        )
        assert gens == ["bbj_gui"]
        assert deprecated is False

    def test_deprecated_flag(self):
        """Primary.Deprecated condition sets deprecated=True."""
        _gens, deprecated = tag_generation(
            "commands/let.htm",
            ["Primary.Deprecated"],
            "LET statement docs.",
        )
        assert deprecated is True

    def test_superseded_flag(self):
        """Primary.Superseded condition sets deprecated=True."""
        _gens, deprecated = tag_generation(
            "commands/open.htm",
            ["Primary.Superseded"],
            "OPEN statement docs.",
        )
        assert deprecated is True

    def test_unknown_path_no_content(self):
        """Unrecognized path, no conditions, no content patterns -> untagged."""
        gens, deprecated = tag_generation(
            "misc/random.htm",
            [],
            "Just some text with no patterns.",
        )
        assert gens == ["untagged"]
        assert deprecated is False

    def test_dwc_content_only(self):
        """Unrecognized path but content mentions DWC -> dwc."""
        gens, deprecated = tag_generation(
            "misc/something.htm",
            [],
            "The DWC component renders in the browser.",
        )
        assert gens == ["dwc"]
        assert deprecated is False

    def test_combined_path_and_content(self):
        """DWC path + DWC content combine for strong dwc signal."""
        gens, deprecated = tag_generation(
            "dwc/bbjwebcomponent.htm",
            ["Primary.BASISHelp"],
            "BBjWebComponent in the Dynamic Web Client.",
        )
        assert "dwc" in gens
        assert deprecated is False


# ---------------------------------------------------------------------------
# Model field update tests
# ---------------------------------------------------------------------------


class TestModelUpdates:
    def test_document_context_header_default(self):
        """Document without explicit context_header has empty string."""
        doc = Document(
            source_url="x",
            title="T",
            doc_type="flare",
            content="content",
            generations=["all"],
        )
        assert doc.context_header == ""

    def test_document_deprecated_default(self):
        """Document without explicit deprecated has False."""
        doc = Document(
            source_url="x",
            title="T",
            doc_type="flare",
            content="content",
            generations=["all"],
        )
        assert doc.deprecated is False

    def test_document_with_context_header(self):
        """Document accepts context_header field."""
        doc = Document(
            source_url="x",
            title="T",
            doc_type="flare",
            content="content",
            generations=["all"],
            context_header="Language > BBjAPI > BBjWindow",
        )
        assert doc.context_header == "Language > BBjAPI > BBjWindow"

    def test_document_with_deprecated(self):
        """Document accepts deprecated field."""
        doc = Document(
            source_url="x",
            title="T",
            doc_type="flare",
            content="content",
            generations=["all"],
            deprecated=True,
        )
        assert doc.deprecated is True

    def test_chunk_from_content_with_context_header(self):
        """Chunk.from_content() accepts context_header param."""
        chunk = Chunk.from_content(
            source_url="x",
            title="T",
            doc_type="flare",
            content="content",
            generations=["bbj_gui"],
            context_header="A > B",
        )
        assert chunk.context_header == "A > B"

    def test_chunk_from_content_with_deprecated(self):
        """Chunk.from_content() accepts deprecated param."""
        chunk = Chunk.from_content(
            source_url="x",
            title="T",
            doc_type="flare",
            content="content",
            generations=["bbj_gui"],
            deprecated=True,
        )
        assert chunk.deprecated is True

    def test_chunk_from_content_defaults_preserved(self):
        """Chunk.from_content() defaults context_header='' and deprecated=False."""
        chunk = Chunk.from_content(
            source_url="x",
            title="T",
            doc_type="flare",
            content="content",
            generations=["all"],
        )
        assert chunk.context_header == ""
        assert chunk.deprecated is False


# ---------------------------------------------------------------------------
# Report tests
# ---------------------------------------------------------------------------


class TestBuildReport:
    def _make_doc(
        self,
        generations: list[str],
        conditions: str = "",
        deprecated: bool = False,
    ) -> Document:
        return Document(
            source_url="x",
            title="T",
            doc_type="flare",
            content="content",
            generations=generations,
            deprecated=deprecated,
            metadata={"conditions": conditions} if conditions else {},
        )

    def test_counts_generations(self):
        """build_report counts generation distribution correctly."""
        docs = [
            self._make_doc(["bbj_gui"]),
            self._make_doc(["bbj_gui"]),
            self._make_doc(["dwc"]),
            self._make_doc(["all"]),
            self._make_doc(["untagged"]),
        ]
        report = build_report(docs)
        assert report["total"] == 5
        assert report["generation_counts"]["bbj_gui"] == 2
        assert report["generation_counts"]["dwc"] == 1
        assert report["generation_counts"]["all"] == 1
        assert report["generation_counts"]["untagged"] == 1
        assert report["untagged_count"] == 1

    def test_counts_deprecated(self):
        """build_report counts deprecated from metadata conditions."""
        docs = [
            self._make_doc(["all"], conditions="Primary.Deprecated", deprecated=True),
            self._make_doc(["bbj_gui"]),
        ]
        report = build_report(docs)
        assert report["deprecated_count"] == 1
        assert report["superseded_count"] == 0

    def test_counts_superseded(self):
        """build_report counts superseded from metadata conditions."""
        docs = [
            self._make_doc(["vpro5"], conditions="Primary.Superseded", deprecated=True),
        ]
        report = build_report(docs)
        assert report["superseded_count"] == 1

    def test_empty_documents(self):
        """build_report handles empty document list."""
        report = build_report([])
        assert report["total"] == 0
        assert report["generation_counts"] == {}
        assert report["untagged_count"] == 0
