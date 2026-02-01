"""BBj source code parser for the RAG ingestion pipeline.

Processes ``.bbj``, ``.txt``, and ``.src`` files from configurable
directories.  Validates that files contain BBj code, extracts leading
``rem`` comment blocks as description context, and classifies content
by generation (DWC vs GUI vs general) using API pattern analysis.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path

from bbj_rag.models import Document

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# BBj keyword validation
# ---------------------------------------------------------------------------

_BBJ_KEYWORDS: list[re.Pattern[str]] = [
    re.compile(r"\brem\b", re.IGNORECASE),
    re.compile(r"\bopen\b", re.IGNORECASE),
    re.compile(r"\bprint\b", re.IGNORECASE),
    re.compile(r"PROCESS_EVENTS"),
    re.compile(r"\bclass\s+public\b", re.IGNORECASE),
    re.compile(r"\bmethod\s+public\b", re.IGNORECASE),
    re.compile(r"BBjAPI"),
    re.compile(r"SYSGUI"),
]

# ---------------------------------------------------------------------------
# Generation classification patterns
# ---------------------------------------------------------------------------

_DWC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"BBjHtmlView", re.IGNORECASE),
    re.compile(r"BBjWebComponent"),
    re.compile(r"setCss|addStyle|getStyle", re.IGNORECASE),
    re.compile(r"setResponsive|getComputedStyle"),
    re.compile(r"BBjNavigator"),
    re.compile(r"webManager|getWebManager"),
    re.compile(r'setAttribute\s*\(\s*"dwc-'),
    re.compile(r"\.css\("),
]

_GUI_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"BBjAPI\(\)"),
    re.compile(r"getSysGui"),
    re.compile(r"PROCESS_EVENTS"),
    re.compile(r"addWindow|addButton|addEditBox"),
    re.compile(r"setCallback"),
    re.compile(r"BBjTopLevelWindow"),
    re.compile(r"SYSGUI"),
]

DEFAULT_EXTENSIONS: list[str] = [".bbj", ".txt", ".src"]


def classify_source_generation(content: str) -> list[str]:
    """Classify BBj source code by generation based on API patterns.

    DWC is a superset of GUI: ``bbj_gui`` code is relevant to DWC users,
    but ``dwc``-specific code does NOT apply to traditional GUI users.
    """
    if any(p.search(content) for p in _DWC_PATTERNS):
        return ["dwc"]
    if any(p.search(content) for p in _GUI_PATTERNS):
        return ["bbj_gui"]
    return ["all"]


def extract_header_comment(content: str) -> str:
    """Extract the leading ``rem`` comment block from BBj source code.

    BBj comments start with ``rem`` (case-insensitive).  The first
    contiguous block of ``rem`` lines at the start of the file forms
    the description.
    """
    lines = content.splitlines()
    comment_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if comment_lines:
                break  # end of comment block
            continue
        if stripped.lower().startswith("rem"):
            text = stripped[3:].lstrip(" '")
            if text:
                comment_lines.append(text)
        else:
            break  # non-comment line ends the header block

    return " ".join(comment_lines)


def _is_bbj_code(content: str) -> bool:
    """Return True if *content* contains at least one BBj keyword."""
    return any(p.search(content) for p in _BBJ_KEYWORDS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class BbjSourceParser:
    """Parse BBj source code files into ``Document`` objects.

    Recursively scans the given directories for files matching the
    configured extensions, validates they contain BBj code, and yields
    one ``Document`` per file.

    Implements the ``DocumentParser`` protocol.

    Args:
        source_dirs: Directories to scan for BBj source files.
        extensions: File extensions to include (default ``.bbj``,
            ``.txt``, ``.src``).
    """

    def __init__(
        self,
        source_dirs: list[Path],
        extensions: list[str] | None = None,
    ) -> None:
        self._source_dirs = source_dirs
        self._extensions = extensions or DEFAULT_EXTENSIONS

    def parse(self) -> Iterator[Document]:
        """Yield one ``Document`` per valid BBj source file."""
        for source_dir in self._source_dirs:
            if not source_dir.is_dir():
                logger.warning("Source directory does not exist: %s", source_dir)
                continue

            file_count = 0
            for ext in self._extensions:
                for file_path in sorted(source_dir.rglob(f"*{ext}")):
                    if not file_path.is_file():
                        continue

                    try:
                        content = file_path.read_text(
                            encoding="utf-8", errors="replace"
                        )
                    except OSError:
                        logger.warning("Could not read file: %s", file_path)
                        continue

                    if not content.strip():
                        continue

                    if not _is_bbj_code(content):
                        logger.debug(
                            "Skipping non-BBj file: %s (no BBj keywords found)",
                            file_path,
                        )
                        continue

                    header_comment = extract_header_comment(content)
                    generations = classify_source_generation(content)
                    relative_path = file_path.relative_to(source_dir)
                    filename = file_path.name
                    file_ext = file_path.suffix

                    context_header = f"BBj Source Code > {filename}"
                    if header_comment:
                        context_header = (
                            f"BBj Source Code > {filename} -- {header_comment}"
                        )

                    yield Document(
                        source_url=f"file://{relative_path}",
                        title=file_path.stem,
                        doc_type="example",
                        content=content,
                        generations=generations,
                        context_header=context_header,
                        metadata={
                            "source": "bbj_source",
                            "file_ext": file_ext,
                            "header_comment": header_comment,
                        },
                        deprecated=False,
                    )
                    file_count += 1

            logger.info(
                "BBj source parser: processed %d files from %s",
                file_count,
                source_dir,
            )


__all__ = [
    "BbjSourceParser",
    "classify_source_generation",
    "extract_header_comment",
]
