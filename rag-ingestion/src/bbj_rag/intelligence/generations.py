"""Multi-signal generation tagger for BBj documentation.

Classifies documents by BBj product generation (character, vpro5, bbj_gui,
dwc, all) using three signal sources: file path prefixes, condition tags,
and content regex patterns.  Each signal source emits weighted Signal
objects that are aggregated and thresholded by ``resolve_signals`` to
produce the final generation list.

The public API is ``tag_generation(path, conditions, content)`` which
returns ``(generations, deprecated)`` ready for the Document model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum, auto


class Generation(StrEnum):
    """Canonical BBj product generation labels.

    Values auto-generate as lowercase member names (e.g. ALL -> "all").
    """

    ALL = auto()  # cross-generation content
    CHARACTER = auto()  # green-screen / terminal
    VPRO5 = auto()  # Visual PRO/5
    BBJ_GUI = auto()  # BBj GUI / Swing
    DWC = auto()  # Dynamic Web Client


@dataclass(frozen=True, slots=True)
class Signal:
    """A single generation tagging signal with source attribution."""

    generation: Generation
    weight: float  # 0.0 .. 1.0
    source: str  # e.g. "file_path", "condition_tag", "content_pattern"


# ---------------------------------------------------------------------------
# Path signal extractor
# ---------------------------------------------------------------------------

# Maps Content-relative path prefixes to generation sets.
# More specific (longer) prefixes override shorter ones because we sort
# by length descending before matching.
_PATH_GENERATION_MAP: dict[str, set[Generation]] = {
    # BBj GUI (Swing)
    "bbjobjects/": {Generation.BBJ_GUI},
    "bbjevents/": {Generation.BBJ_GUI},
    "bbjinterfaces/": {Generation.BBJ_GUI},
    "gridmethods/": {Generation.BBJ_GUI},
    "gridctrl/": {Generation.BBJ_GUI},
    "bui/": {Generation.BBJ_GUI},
    "appbuildingblocks/": {Generation.BBJ_GUI},
    "mnemonic/sysgui/": {Generation.BBJ_GUI},
    # DWC
    "dwc/": {Generation.DWC},
    # Character / terminal
    "mnemonic/terminal/": {Generation.CHARACTER},
    # Visual PRO/5
    "guibuild/": {Generation.VPRO5},
    "formbuilder/": {Generation.VPRO5},
    "resbuild/": {Generation.VPRO5},
    "rescomp/": {Generation.VPRO5},
    "resprops/": {Generation.VPRO5},
    "ddbuild/": {Generation.VPRO5},
    # Cross-generation ("all")
    "commands/": {Generation.ALL},
    "events/": {Generation.ALL},
    "sendmsg/": {Generation.ALL},
    "sysadmin/": {Generation.ALL},
    "config/": {Generation.ALL},
    "usr/": {Generation.ALL},
    "dataserv/": {Generation.ALL},
    "b3odbc/": {Generation.ALL},
    "bbutil/": {Generation.ALL},
    "util/": {Generation.ALL},
    "eus/": {Generation.ALL},
    # Overrides -- more specific than parent "commands/"
    "commands/bbj-commands/": {Generation.BBJ_GUI},
    "commands/bbj-variables/": {Generation.BBJ_GUI},
}

# Pre-sorted once by key length descending for specificity matching.
_PATH_KEYS_SORTED = sorted(_PATH_GENERATION_MAP, key=len, reverse=True)


def signal_from_path(content_relative_path: str) -> list[Signal]:
    """Extract generation signals from a file's Content-relative path.

    Longer (more specific) path prefixes take priority.
    """
    for prefix in _PATH_KEYS_SORTED:
        if content_relative_path.startswith(prefix):
            return [
                Signal(generation=gen, weight=0.6, source="file_path")
                for gen in _PATH_GENERATION_MAP[prefix]
            ]
    return []


# ---------------------------------------------------------------------------
# Condition tag signal extractor
# ---------------------------------------------------------------------------

# Maps condition tag strings to (generation, weight) pairs.
# Primary.Deprecated / Primary.Superseded are lifecycle flags, NOT generation
# signals -- they are handled separately in tag_generation().
# Primary.BASISHelp is informational ("include in BASISHelp build") and not
# a discriminating generation signal.
_CONDITION_GENERATION_MAP: dict[str, tuple[Generation, float]] = {
    "Primary.guibuild_chm": (Generation.VPRO5, 0.5),
    "Primary.resbuild_chm": (Generation.VPRO5, 0.5),
    "Primary.ddbuild_chm": (Generation.VPRO5, 0.5),
    "Primary.config_chm": (Generation.ALL, 0.3),
    "Primary.EMHelp": (Generation.ALL, 0.3),
    "Primary.BDTHelp": (Generation.ALL, 0.3),
}


def signal_from_conditions(conditions: list[str]) -> list[Signal]:
    """Extract generation signals from MadCap condition tags.

    Lifecycle conditions (Deprecated, Superseded) are ignored here --
    they are handled as a boolean flag in ``tag_generation()``.
    """
    signals: list[Signal] = []
    for cond in conditions:
        mapping = _CONDITION_GENERATION_MAP.get(cond)
        if mapping is not None:
            gen, weight = mapping
            signals.append(
                Signal(generation=gen, weight=weight, source="condition_tag")
            )
    return signals


# ---------------------------------------------------------------------------
# Content pattern signal extractor
# ---------------------------------------------------------------------------

_CONTENT_GENERATION_PATTERNS: dict[Generation, list[re.Pattern[str]]] = {
    Generation.BBJ_GUI: [
        re.compile(r"PROCESS_EVENTS", re.IGNORECASE),
        re.compile(r"BBjAPI\(\)"),
        re.compile(r"BBjSysGui"),
        re.compile(r"SysGUI", re.IGNORECASE),
    ],
    Generation.DWC: [
        re.compile(r"Dynamic Web Client"),
        re.compile(r"\bDWC\b"),
        re.compile(r"BBjWebComponent"),
        re.compile(r"web\s*component", re.IGNORECASE),
    ],
    Generation.CHARACTER: [
        re.compile(r"character\s*mode", re.IGNORECASE),
        re.compile(r"green.screen", re.IGNORECASE),
        re.compile(r"terminal\s*emulat", re.IGNORECASE),
    ],
    Generation.VPRO5: [
        re.compile(r"Visual\s*PRO/5", re.IGNORECASE),
        re.compile(r"\bVPRO/?5\b", re.IGNORECASE),
        re.compile(r"GUI\s*Builder", re.IGNORECASE),
        re.compile(r"Resource\s*Compiler", re.IGNORECASE),
    ],
}


def signal_from_content(content: str) -> list[Signal]:
    """Extract generation signals from document content patterns.

    Only emits one signal per generation per call, even when multiple
    patterns for the same generation match.
    """
    signals: list[Signal] = []
    for gen, patterns in _CONTENT_GENERATION_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(content):
                signals.append(
                    Signal(generation=gen, weight=0.4, source="content_pattern")
                )
                break  # one signal per generation
    return signals


# ---------------------------------------------------------------------------
# Signal resolver
# ---------------------------------------------------------------------------


def resolve_signals(signals: list[Signal]) -> list[str]:
    """Aggregate weighted signals into a final generation list.

    Sums weights per generation. Generations with aggregate weight >= 0.3
    are included. Returns sorted list of generation string values.
    If nothing exceeds the threshold, returns ``["untagged"]``.

    Returns ``list[str]`` (not ``list[Generation]``) because downstream
    models store generation labels as plain strings.
    """
    scores: dict[Generation, float] = {}
    for sig in signals:
        scores[sig.generation] = scores.get(sig.generation, 0.0) + sig.weight

    threshold = 0.3
    result = sorted(str(g) for g, score in scores.items() if score >= threshold)

    if not result:
        return ["untagged"]
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def tag_generation(
    content_relative_path: str,
    conditions: list[str],
    content: str,
) -> tuple[list[str], bool]:
    """Classify a document by BBj product generation.

    Combines signals from file path, condition tags, and content patterns
    to produce a generation list and deprecation flag.

    Args:
        content_relative_path: Path relative to Flare Content/ directory
            (e.g. ``"bbjobjects/Window/bbjwindow.htm"``).
        conditions: MadCap condition tag strings from the topic root.
        content: Plain-text or markdown content of the document.

    Returns:
        Tuple of (generations, deprecated) where generations is a sorted
        list of generation label strings and deprecated is True when
        ``Primary.Deprecated`` or ``Primary.Superseded`` is present.
    """
    signals: list[Signal] = []
    signals.extend(signal_from_path(content_relative_path))
    signals.extend(signal_from_conditions(conditions))
    signals.extend(signal_from_content(content))

    generations = resolve_signals(signals)
    deprecated = (
        "Primary.Deprecated" in conditions or "Primary.Superseded" in conditions
    )

    return generations, deprecated


__all__ = [
    "Generation",
    "Signal",
    "resolve_signals",
    "signal_from_conditions",
    "signal_from_content",
    "signal_from_path",
    "tag_generation",
]
