"""Condition tag extraction for MadCap Flare topics.

Parses the Primary.flcts condition tag set file to identify all defined
condition tags and their generation relevance. Extracts per-topic
conditions from the ``<html>`` root element's ``MadCap:conditions``
attribute and maps them to generation labels for the Document model.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from bbj_rag.parsers import MADCAP_NS

logger = logging.getLogger(__name__)

# Mapping of condition tag names to their generation semantic meaning.
# Only conditions that affect which product generation a topic belongs to
# (or its lifecycle status) are listed here.
GENERATION_RELEVANT_CONDITIONS: dict[str, str] = {
    "Primary.BASISHelp": "bbj",
    "Primary.BDTHelp": "bdt",
    "Primary.EMHelp": "em",
    "Primary.Deprecated": "deprecated",
    "Primary.Superseded": "superseded",
    "Primary.NotImplemented": "not_implemented",
}


@dataclass(frozen=True, slots=True)
class ConditionTag:
    """A single condition tag definition from a .flcts file."""

    name: str
    generation_relevant: bool


def parse_condition_tag_set(flcts_path: Path) -> list[ConditionTag]:
    """Parse a MadCap Flare condition tag set (.flcts) file.

    Args:
        flcts_path: Path to the .flcts XML file
            (e.g., ``Project/ConditionTagSets/Primary.flcts``).

    Returns:
        List of ConditionTag objects for all defined tags.
    """
    parser = etree.XMLParser(remove_comments=True)
    tree = etree.parse(str(flcts_path), parser)
    root = tree.getroot()

    tags: list[ConditionTag] = []
    # Derive the tag set name from the filename (e.g., "Primary")
    tag_set_name = flcts_path.stem

    for elem in root.iter("ConditionTag"):
        name = elem.get("Name", "").strip()
        if not name:
            continue
        qualified_name = f"{tag_set_name}.{name}"
        is_relevant = qualified_name in GENERATION_RELEVANT_CONDITIONS
        tags.append(ConditionTag(name=qualified_name, generation_relevant=is_relevant))

    logger.info(
        "Parsed %d condition tags from %s (%d generation-relevant)",
        len(tags),
        flcts_path.name,
        sum(1 for t in tags if t.generation_relevant),
    )
    return tags


def extract_topic_conditions(root: etree._Element) -> list[str]:
    """Extract condition strings from a topic's root ``<html>`` element.

    Reads the ``MadCap:conditions`` attribute and splits the
    comma-separated values into a flat list.

    Args:
        root: The parsed XML root element (``<html>``).

    Returns:
        List of condition strings (e.g., ``["Primary.BASISHelp",
        "Primary.Deprecated"]``). Empty list if no conditions present.
    """
    cond_attr = root.get(f"{{{MADCAP_NS}}}conditions", "")
    if not cond_attr:
        return []
    return [c.strip() for c in cond_attr.split(",") if c.strip()]


def extract_inline_conditions(body: etree._Element) -> dict[str, list[str]]:
    """Extract per-element conditions from inline ``MadCap:conditions`` attributes.

    Walks the body tree looking for any element with a
    ``MadCap:conditions`` attribute. Returns a mapping of element
    tag-plus-position identifiers to their condition lists.

    Args:
        body: The ``<body>`` element of a parsed topic.

    Returns:
        Mapping of element identifiers to condition string lists.
        Empty dict if no inline conditions found.
    """
    cond_attr_name = f"{{{MADCAP_NS}}}conditions"
    result: dict[str, list[str]] = {}
    counter: dict[str, int] = {}

    for elem in body.iter():
        cond_val = elem.get(cond_attr_name, "")
        if not cond_val:
            continue

        # Build a human-readable identifier: tag[index]
        if isinstance(elem.tag, str):
            tag = etree.QName(elem.tag).localname
        else:
            tag = "unknown"
        count = counter.get(tag, 0)
        counter[tag] = count + 1
        identifier = f"{tag}[{count}]"

        conditions = [c.strip() for c in cond_val.split(",") if c.strip()]
        if conditions:
            result[identifier] = conditions

    return result


def map_conditions_to_generations(conditions: list[str]) -> list[str]:
    """Map condition strings to generation labels.

    Uses ``GENERATION_RELEVANT_CONDITIONS`` to translate condition tag
    names into short generation labels. Non-generation conditions
    (cosmetic tags like ``Primary.Navigation``, ``Primary.*_chm``)
    are filtered out.

    If no conditions are provided or none match a generation-relevant
    tag, defaults to ``["bbj"]`` since the vast majority of content
    is BBj documentation.

    Args:
        conditions: List of condition strings from a topic
            (e.g., ``["Primary.BASISHelp", "Primary.Deprecated"]``).

    Returns:
        List of generation labels (e.g., ``["bbj", "deprecated"]``).
    """
    generations: list[str] = []
    for cond in conditions:
        label = GENERATION_RELEVANT_CONDITIONS.get(cond)
        if label is not None:
            generations.append(label)

    if not generations:
        return ["bbj"]

    return generations


__all__ = [
    "GENERATION_RELEVANT_CONDITIONS",
    "ConditionTag",
    "extract_inline_conditions",
    "extract_topic_conditions",
    "map_conditions_to_generations",
    "parse_condition_tag_set",
]
