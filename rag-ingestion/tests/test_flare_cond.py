"""Tests for the condition tag extraction module.

Includes both unit tests using synthetic XML and integration tests
against the real Flare project at /Users/beff/bbjdocs/.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from bbj_rag.parsers import MADCAP_NS
from bbj_rag.parsers.flare_cond import (
    extract_inline_conditions,
    extract_topic_conditions,
    map_conditions_to_generations,
    parse_condition_tag_set,
)

FLARE_SOURCE = Path("/Users/beff/bbjdocs")
skip_no_flare = pytest.mark.skipif(
    not FLARE_SOURCE.exists(),
    reason="Flare source not available",
)


# ---------------------------------------------------------------------------
# Unit tests with synthetic XML (no file dependency)
# ---------------------------------------------------------------------------


class TestExtractTopicConditionsSynthetic:
    """Unit tests for condition extraction from XML roots."""

    def test_single_condition(self):
        xml = (
            '<?xml version="1.0"?>'
            f'<html xmlns:MadCap="{MADCAP_NS}"'
            ' MadCap:conditions="Primary.BASISHelp">'
            "<head/><body/></html>"
        )
        root = etree.fromstring(xml.encode("utf-8"))
        result = extract_topic_conditions(root)
        assert result == ["Primary.BASISHelp"]

    def test_multiple_conditions(self):
        xml = (
            '<?xml version="1.0"?>'
            f'<html xmlns:MadCap="{MADCAP_NS}"'
            ' MadCap:conditions="Primary.BASISHelp,Primary.Deprecated">'
            "<head/><body/></html>"
        )
        root = etree.fromstring(xml.encode("utf-8"))
        result = extract_topic_conditions(root)
        assert result == ["Primary.BASISHelp", "Primary.Deprecated"]

    def test_no_conditions(self):
        xml = '<?xml version="1.0"?><html><head/><body/></html>'
        root = etree.fromstring(xml.encode("utf-8"))
        result = extract_topic_conditions(root)
        assert result == []

    def test_whitespace_handling(self):
        xml = (
            '<?xml version="1.0"?>'
            f'<html xmlns:MadCap="{MADCAP_NS}"'
            ' MadCap:conditions=" Primary.BASISHelp , Primary.EMHelp ">'
            "<head/><body/></html>"
        )
        root = etree.fromstring(xml.encode("utf-8"))
        result = extract_topic_conditions(root)
        assert result == ["Primary.BASISHelp", "Primary.EMHelp"]

    def test_empty_conditions_attribute(self):
        xml = (
            '<?xml version="1.0"?>'
            f'<html xmlns:MadCap="{MADCAP_NS}"'
            ' MadCap:conditions="">'
            "<head/><body/></html>"
        )
        root = etree.fromstring(xml.encode("utf-8"))
        result = extract_topic_conditions(root)
        assert result == []


class TestExtractInlineConditionsSynthetic:
    """Unit tests for inline condition extraction from body elements."""

    def test_inline_conditions_found(self):
        xml = (
            '<?xml version="1.0"?>'
            f'<html xmlns:MadCap="{MADCAP_NS}">'
            "<head/><body>"
            '<p MadCap:conditions="Primary.NotImplemented">Not ready</p>'
            "<p>Normal text</p>"
            "</body></html>"
        )
        root = etree.fromstring(xml.encode("utf-8"))
        body = root.find(".//body")
        assert body is not None
        result = extract_inline_conditions(body)
        assert len(result) == 1
        values = list(result.values())
        assert values[0] == ["Primary.NotImplemented"]

    def test_no_inline_conditions(self):
        xml = '<?xml version="1.0"?><html><head/><body><p>Normal text</p></body></html>'
        root = etree.fromstring(xml.encode("utf-8"))
        body = root.find(".//body")
        assert body is not None
        result = extract_inline_conditions(body)
        assert result == {}


class TestMapConditionsToGenerations:
    """Unit tests for condition-to-generation mapping."""

    def test_basishelp(self):
        result = map_conditions_to_generations(["Primary.BASISHelp"])
        assert result == ["bbj"]

    def test_deprecated(self):
        result = map_conditions_to_generations(
            ["Primary.BASISHelp", "Primary.Deprecated"]
        )
        assert result == ["bbj", "deprecated"]

    def test_no_conditions_defaults_to_bbj(self):
        result = map_conditions_to_generations([])
        assert result == ["bbj"]

    def test_cosmetic_only_defaults_to_bbj(self):
        result = map_conditions_to_generations(["Primary.Navigation"])
        assert result == ["bbj"]

    def test_chm_conditions_cosmetic(self):
        """CHM build targets are cosmetic, not generation-relevant."""
        result = map_conditions_to_generations(
            ["Primary.config_chm", "Primary.ddbuild_chm"]
        )
        assert result == ["bbj"]

    def test_bdt_generation(self):
        result = map_conditions_to_generations(["Primary.BDTHelp"])
        assert result == ["bdt"]

    def test_em_generation(self):
        result = map_conditions_to_generations(["Primary.EMHelp"])
        assert result == ["em"]

    def test_superseded(self):
        result = map_conditions_to_generations(["Primary.Superseded"])
        assert result == ["superseded"]

    def test_not_implemented(self):
        result = map_conditions_to_generations(["Primary.NotImplemented"])
        assert result == ["not_implemented"]

    def test_mixed_relevant_and_cosmetic(self):
        result = map_conditions_to_generations(
            ["Primary.BASISHelp", "Primary.Navigation", "Primary.Deprecated"]
        )
        assert result == ["bbj", "deprecated"]


class TestParseConditionTagSetSynthetic:
    """Unit tests for .flcts parsing with synthetic XML."""

    def test_parse_tags(self, tmp_path):
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<CatapultConditionTagSet>\n"
            '  <ConditionTag Name="BASISHelp" BackgroundColor="#0000ff"/>\n'
            '  <ConditionTag Name="Navigation" BackgroundColor="#00e8ff"/>\n'
            "</CatapultConditionTagSet>"
        )
        flcts_path = tmp_path / "Primary.flcts"
        flcts_path.write_text(xml, encoding="utf-8")

        tags = parse_condition_tag_set(flcts_path)
        assert len(tags) == 2
        names = [t.name for t in tags]
        assert "Primary.BASISHelp" in names
        assert "Primary.Navigation" in names

        basis_tag = next(t for t in tags if t.name == "Primary.BASISHelp")
        nav_tag = next(t for t in tags if t.name == "Primary.Navigation")
        assert basis_tag.generation_relevant is True
        assert nav_tag.generation_relevant is False

    def test_empty_name_skipped(self, tmp_path):
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<CatapultConditionTagSet>\n"
            '  <ConditionTag Name="" BackgroundColor="#000"/>\n'
            '  <ConditionTag Name="BASISHelp" BackgroundColor="#0000ff"/>\n'
            "</CatapultConditionTagSet>"
        )
        flcts_path = tmp_path / "Primary.flcts"
        flcts_path.write_text(xml, encoding="utf-8")

        tags = parse_condition_tag_set(flcts_path)
        assert len(tags) == 1


# ---------------------------------------------------------------------------
# Integration tests with real Flare project files
# ---------------------------------------------------------------------------


@skip_no_flare
class TestParseConditionTagSetReal:
    """Integration tests against /Users/beff/bbjdocs/."""

    def test_parse_primary_flcts(self):
        flcts_path = FLARE_SOURCE / "Project" / "ConditionTagSets" / "Primary.flcts"
        tags = parse_condition_tag_set(flcts_path)
        assert len(tags) == 12, f"Expected 12 tags, got {len(tags)}"

        names = {t.name for t in tags}
        assert "Primary.BASISHelp" in names
        assert "Primary.BDTHelp" in names
        assert "Primary.EMHelp" in names
        assert "Primary.Deprecated" in names
        assert "Primary.NotImplemented" in names
        assert "Primary.Navigation" in names

    def test_generation_relevant_count(self):
        flcts_path = FLARE_SOURCE / "Project" / "ConditionTagSets" / "Primary.flcts"
        tags = parse_condition_tag_set(flcts_path)
        relevant = [t for t in tags if t.generation_relevant]
        assert len(relevant) == 6, (
            f"Expected 6 generation-relevant, got {len(relevant)}"
        )


@skip_no_flare
class TestExtractTopicConditionsReal:
    """Integration tests for condition extraction from real topic files."""

    def test_extract_from_basishelp_topic(self):
        """Parse a known topic with BASISHelp condition."""
        topic = FLARE_SOURCE / "Content" / "basismans" / "Using_BASIS_Help.htm"
        parser = etree.XMLParser(remove_comments=True)
        tree = etree.parse(str(topic), parser)
        root = tree.getroot()

        conditions = extract_topic_conditions(root)
        assert "Primary.BASISHelp" in conditions

    def test_extract_from_topic_with_no_conditions(self):
        """Find a topic without MadCap:conditions and verify empty list."""
        # Search for a topic without conditions (some exist)
        content_dir = FLARE_SOURCE / "Content"
        parser = etree.XMLParser(remove_comments=True)

        for topic_path in list(content_dir.rglob("*.htm"))[:200]:
            if "Resources" in topic_path.parts:
                continue
            try:
                tree = etree.parse(str(topic_path), parser)
                root = tree.getroot()
                conditions = extract_topic_conditions(root)
                if not conditions:
                    # Found one with no conditions - test passes
                    return
            except etree.XMLSyntaxError:
                continue

        # If all first 200 topics have conditions, skip
        pytest.skip("No topic without conditions found in first 200 files")

    def test_map_real_topic_conditions(self):
        """Map conditions from a real BASISHelp topic to generations."""
        topic = FLARE_SOURCE / "Content" / "basismans" / "Using_BASIS_Help.htm"
        parser = etree.XMLParser(remove_comments=True)
        tree = etree.parse(str(topic), parser)
        root = tree.getroot()

        conditions = extract_topic_conditions(root)
        generations = map_conditions_to_generations(conditions)
        assert "bbj" in generations
