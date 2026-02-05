"""JavaDoc JSON parser for BBj API documentation.

Parses structured JSON files containing BBj API class documentation from
the JavaDoc export at ``$BBJ_HOME/documentation/javadoc/``. Produces one
``Document`` per class, formatted as a "class reference card" with all
methods listed.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from bbj_rag.models import Document

logger = logging.getLogger(__name__)

# Regex to extract [Docs](https://documentation.basis.cloud/...) URLs
_DOCS_LINK_RE = re.compile(r"\[Docs\]\((https://documentation\.basis\.cloud/[^)]+)\)")


def _extract_display_url(docu: str) -> str:
    """Extract the documentation.basis.cloud URL from a docu field."""
    match = _DOCS_LINK_RE.search(docu)
    return match.group(1) if match else ""


def _html_to_text(html: str) -> str:
    """Convert an HTML fragment to plain text.

    Uses BeautifulSoup to parse HTML and extract text content. This handles
    HTML entity decoding (``&#160;`` -> space) automatically.
    """
    if not html:
        return ""
    # Parse HTML fragment
    soup = BeautifulSoup(html, "html.parser")
    # Get text, preserving some whitespace
    text = soup.get_text(separator=" ")
    # Normalize line endings (handle Windows \r\n and old Mac \r)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple spaces
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clean_description(docu: str) -> str:
    """Extract and clean the description text from a docu field.

    Removes the [Docs](url) link suffix and converts HTML to plain text.
    """
    if not docu:
        return ""
    # Remove the [Docs](url) link before converting
    cleaned = _DOCS_LINK_RE.sub("", docu)
    return _html_to_text(cleaned)


def _format_method_signature(method: dict[str, Any]) -> str:
    """Format a method signature as name(param1, param2, ...).

    Args:
        method: Method dict with 'name' and optional 'params' list.

    Returns:
        Formatted signature like ``addButton(p_id, p_x, p_y)``.
    """
    name = method.get("name", "")
    params = method.get("params", [])
    param_names = [p.get("name", "") for p in params if p.get("name")]
    return f"{name}({', '.join(param_names)})"


def _format_method_line(method: dict[str, Any]) -> str:
    """Format a method as a Markdown list item.

    Format: ``- `methodName(param1, param2)` - description``

    If the method has no description, omits the description part.
    """
    signature = _format_method_signature(method)
    description = _clean_description(method.get("docu", ""))

    if description:
        # Truncate long descriptions to first sentence or 100 chars
        first_sentence = description.split(".")[0]
        if len(first_sentence) > 100:
            first_sentence = first_sentence[:97] + "..."
        return f"- `{signature}` - {first_sentence}"
    return f"- `{signature}`"


def _format_class_content(
    class_name: str,
    class_description: str,
    package_name: str,
    display_url: str,
    methods: list[dict[str, Any]],
) -> str:
    """Format a class as a Markdown reference card.

    Structure:
        # ClassName

        description

        **Package:** package_name
        **Documentation:** url

        ## Methods

        - `method1(params)` - description
        - `method2()` - description
    """
    parts: list[str] = [f"# {class_name}"]

    if class_description:
        parts.append("")
        parts.append(class_description)

    parts.append("")
    parts.append(f"**Package:** {package_name}")
    if display_url:
        parts.append(f"**Documentation:** {display_url}")

    if methods:
        parts.append("")
        parts.append("## Methods")
        parts.append("")
        for method in methods:
            parts.append(_format_method_line(method))

    return "\n".join(parts)


class JavaDocParser:
    """Parse BBj API JavaDoc JSON files into ``Document`` objects.

    Reads all ``*.json`` files in the specified directory, parses each
    class definition, and yields one ``Document`` per class formatted as
    a reference card.

    Implements the ``DocumentParser`` protocol.

    Args:
        javadoc_dir: Directory containing the JavaDoc JSON files.
    """

    def __init__(self, javadoc_dir: Path) -> None:
        self._javadoc_dir = javadoc_dir

    def parse(self) -> Iterator[Document]:
        """Yield one ``Document`` per class from all JSON files."""
        if not self._javadoc_dir.is_dir():
            logger.warning("JavaDoc directory does not exist: %s", self._javadoc_dir)
            return

        json_files = sorted(self._javadoc_dir.glob("*.json"))
        if not json_files:
            logger.warning("No JSON files found in: %s", self._javadoc_dir)
            return

        total_classes = 0
        for json_path in json_files:
            try:
                with open(json_path, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Failed to read %s: %s", json_path, exc)
                continue

            package_name = data.get("name", json_path.stem)
            classes = data.get("classes", [])

            for class_data in classes:
                class_name = class_data.get("name", "")
                if not class_name:
                    continue

                class_docu = class_data.get("docu", "")
                class_description = _clean_description(class_docu)
                display_url = _extract_display_url(class_docu)
                methods = class_data.get("methods", [])

                content = _format_class_content(
                    class_name=class_name,
                    class_description=class_description,
                    package_name=package_name,
                    display_url=display_url,
                    methods=methods,
                )

                yield Document(
                    source_url=f"bbj_api://{class_name}",
                    title=class_name,
                    doc_type="api_reference",
                    content=content,
                    generations=["bbj_gui", "dwc"],
                    context_header=f"BBj API Reference > {class_name}",
                    display_url=display_url,
                    metadata={
                        "source_type": "bbj_api",
                        "package": package_name,
                    },
                    deprecated=False,
                    source_type="bbj_api",
                )
                total_classes += 1

        logger.info(
            "JavaDoc parser: processed %d classes from %d JSON files",
            total_classes,
            len(json_files),
        )


__all__ = ["JavaDocParser"]
