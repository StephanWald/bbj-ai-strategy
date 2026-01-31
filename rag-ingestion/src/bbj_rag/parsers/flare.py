"""MadCap Flare XHTML parser.

Reads raw Flare project files from a local Content/ directory and produces
Document objects with extracted text, code blocks, markdown tables,
hierarchy paths, and generation metadata.

Handles 12 MadCap namespace tag types, 205 snippets, code block
preservation, and table-to-markdown conversion.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from lxml import etree

from bbj_rag.models import Document
from bbj_rag.parsers import MADCAP_NS
from bbj_rag.parsers.flare_cond import (
    extract_inline_conditions,
    extract_topic_conditions,
    map_conditions_to_generations,
)
from bbj_rag.parsers.flare_toc import (
    build_toc_index,
    directory_fallback_path,
)

logger = logging.getLogger(__name__)

# Type alias for the pre-loaded snippets dictionary.
_SnippetMap = dict[str, etree._Element]

# MadCap namespace tags to strip entirely (no content value).
_STRIP_TAGS: frozenset[str] = frozenset(
    {
        "keyword",
        "concept",
        "miniTocProxy",
        "indexProxy",
        "conceptLink",
        "microContent",
        "variable",
    }
)

# MadCap namespace tags whose inner text should be kept.
_KEEP_TEXT_TAGS: frozenset[str] = frozenset({"xref", "toggler"})

# Block-level HTML containers that recurse into children.
_BLOCK_CONTAINERS: frozenset[str] = frozenset(
    {
        "div",
        "section",
        "body",
        "article",
        "aside",
        "main",
        "nav",
        "header",
        "footer",
        "figure",
    }
)


class FlareParser:
    """Parse MadCap Flare XHTML files into Document objects.

    Implements the ``DocumentParser`` protocol. Yields one Document per
    topic file, processing files one at a time (generator pattern).
    """

    def __init__(self, content_dir: Path, project_dir: Path) -> None:
        self._content_dir = content_dir
        self._project_dir = project_dir

        # Build TOC index for hierarchy lookup.
        toc_dir = project_dir / "TOCs"
        self._toc_index: dict[str, str] = build_toc_index(
            toc_dir, content_dir=content_dir
        )

        # Pre-load all snippets keyed by Content-relative path.
        self._snippets: _SnippetMap = _load_snippets(content_dir)

    def parse(self) -> Iterator[Document]:
        """Yield Document objects from all .htm topic files."""
        resources = self._content_dir / "Resources"
        for htm_path in sorted(self._content_dir.rglob("*.htm")):
            # Exclude Resources/ directory.
            try:
                htm_path.relative_to(resources)
                continue
            except ValueError:
                pass

            try:
                doc = self._parse_topic(htm_path)
            except etree.XMLSyntaxError:
                logger.warning("XML parse error, skipping: %s", htm_path)
                continue
            except Exception:
                logger.warning(
                    "Unexpected error parsing %s",
                    htm_path,
                    exc_info=True,
                )
                continue

            if doc is not None:
                yield doc

    def _parse_topic(self, htm_path: Path) -> Document | None:
        """Parse a single topic file, or return None if empty."""
        parser = etree.XMLParser(remove_comments=True)
        tree = etree.parse(str(htm_path), parser)
        root = tree.getroot()

        title = _extract_title(root, htm_path)
        conditions = extract_topic_conditions(root)
        generations = map_conditions_to_generations(conditions)

        content_rel = str(htm_path.relative_to(self._content_dir))
        section_path = self._toc_index.get(
            content_rel,
            directory_fallback_path(content_rel),
        )

        body = root.find(".//body")
        if body is None:
            return None

        content = _extract_body_content(
            body,
            self._snippets,
            htm_path,
            self._content_dir,
            set(),
        )
        if not content.strip():
            return None

        inline_conds = extract_inline_conditions(body)
        source_url = f"flare://Content/{content_rel}"

        metadata: dict[str, str] = {}
        metadata["section_path"] = section_path
        if conditions:
            metadata["conditions"] = ",".join(conditions)
        if inline_conds:
            metadata["inline_conditions"] = str(inline_conds)

        return Document(
            source_url=source_url,
            title=title,
            doc_type="flare",
            content=content,
            generations=generations,
            metadata=metadata,
        )


def _extract_title(root: etree._Element, htm_path: Path) -> str:
    """Extract title from <head><title>, <h1>, or filename."""
    title_elem = root.find(".//head/title")
    if title_elem is not None and title_elem.text and title_elem.text.strip():
        return title_elem.text.strip()

    h1 = root.find(".//body//h1")
    if h1 is not None:
        text = "".join(str(t) for t in h1.itertext()).strip()
        if text:
            return text

    return htm_path.stem.replace("_", " ")


def _load_snippets(content_dir: Path) -> _SnippetMap:
    """Pre-load .flsnp files keyed by Content-relative path."""
    snippets: _SnippetMap = {}
    snippet_dir = content_dir / "Resources" / "Snippets"
    if not snippet_dir.exists():
        logger.warning("Snippets directory not found: %s", snippet_dir)
        return snippets

    parser = etree.XMLParser(remove_comments=True)
    for flsnp_path in snippet_dir.rglob("*.flsnp"):
        try:
            tree = etree.parse(str(flsnp_path), parser)
            root = tree.getroot()
            body = root.find(".//body")
            if body is not None:
                rel = str(flsnp_path.relative_to(content_dir))
                snippets[rel] = body
        except etree.XMLSyntaxError:
            logger.warning("Failed to parse snippet: %s", flsnp_path)

    logger.info(
        "Loaded %d snippets from %s",
        len(snippets),
        snippet_dir,
    )
    return snippets


def _extract_body_content(
    body: etree._Element,
    snippets: _SnippetMap,
    topic_path: Path,
    content_dir: Path,
    seen_snippets: set[str],
) -> str:
    """Extract content from a <body> element."""
    parts: list[str] = []
    _walk_element(
        body,
        parts,
        snippets,
        topic_path,
        content_dir,
        seen_snippets,
    )
    return "\n\n".join(p for p in parts if p.strip())


def _walk_element(
    elem: etree._Element,
    parts: list[str],
    snippets: _SnippetMap,
    topic_path: Path,
    content_dir: Path,
    seen_snippets: set[str],
) -> None:
    """Recursively walk an element tree by tag type."""
    if not isinstance(elem.tag, str):
        return

    qname = etree.QName(elem.tag)

    # --- MadCap namespace elements ---
    if qname.namespace == MADCAP_NS:
        _handle_madcap(
            elem,
            qname.localname,
            parts,
            snippets,
            topic_path,
            content_dir,
            seen_snippets,
        )
        return

    local = qname.localname

    # --- Code blocks: <pre> with <code class="language-*"> ---
    if local == "pre":
        _handle_pre(elem, parts)
        return

    # --- Tables ---
    if local == "table":
        _handle_table(
            elem,
            parts,
            snippets,
            topic_path,
            content_dir,
            seen_snippets,
        )
        return

    # --- Headings ---
    if local in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(local[1])
        heading_parts: list[str] = []
        _collect_inline_text(
            elem,
            heading_parts,
            snippets,
            topic_path,
            content_dir,
            seen_snippets,
        )
        text = " ".join(heading_parts).strip()
        if text:
            parts.append(f"{'#' * level} {text}")
        return

    # --- Paragraphs ---
    if local == "p":
        _handle_paragraph(
            elem,
            parts,
            snippets,
            topic_path,
            content_dir,
            seen_snippets,
        )
        return

    # --- Lists ---
    if local in ("ul", "ol"):
        _extract_list(
            elem,
            parts,
            snippets,
            topic_path,
            content_dir,
            seen_snippets,
            ordered=(local == "ol"),
        )
        return

    # --- Block containers: recurse into children ---
    if local in _BLOCK_CONTAINERS:
        for child in elem:
            _walk_element(
                child,
                parts,
                snippets,
                topic_path,
                content_dir,
                seen_snippets,
            )
        return

    # --- Other: collect inline text ---
    inline_parts: list[str] = []
    _collect_inline_text(
        elem,
        inline_parts,
        snippets,
        topic_path,
        content_dir,
        seen_snippets,
    )
    inline_text = " ".join(inline_parts).strip()
    if inline_text:
        parts.append(inline_text)


def _handle_madcap(
    elem: etree._Element,
    local: str,
    parts: list[str],
    snippets: _SnippetMap,
    topic_path: Path,
    content_dir: Path,
    seen_snippets: set[str],
) -> None:
    """Dispatch MadCap namespace elements by local tag name."""
    if local in _STRIP_TAGS:
        return
    if local in _KEEP_TEXT_TAGS:
        text = "".join(str(t) for t in elem.itertext()).strip()
        if text:
            parts.append(text)
        return
    if local == "snippetBlock":
        _resolve_snippet(
            elem,
            parts,
            snippets,
            topic_path,
            content_dir,
            seen_snippets,
            block=True,
        )
        return
    if local == "snippetText":
        _resolve_snippet(
            elem,
            parts,
            snippets,
            topic_path,
            content_dir,
            seen_snippets,
            block=False,
        )
        return
    if local == "popup":
        head = elem.find(f"{{{MADCAP_NS}}}popupHead")
        if head is not None:
            text = "".join(str(t) for t in head.itertext()).strip()
            if text:
                parts.append(text)
        return
    # Unknown MadCap tag: strip silently.


def _handle_pre(elem: etree._Element, parts: list[str]) -> None:
    """Handle <pre> elements, preserving code blocks."""
    code_child = elem.find("code")
    if code_child is not None:
        cls = code_child.get("class", "")
        if "language-" in cls:
            lang = _extract_language(cls)
            code_text = "".join(str(t) for t in code_child.itertext()).rstrip()
            parts.append(f"```{lang}\n{code_text}\n```")
            return
    # <pre> without language-tagged code child.
    text = "".join(str(t) for t in elem.itertext()).strip()
    if text:
        parts.append(f"```\n{text}\n```")


def _handle_table(
    elem: etree._Element,
    parts: list[str],
    snippets: _SnippetMap,
    topic_path: Path,
    content_dir: Path,
    seen_snippets: set[str],
) -> None:
    """Dispatch tables: Code_Table vs markdown conversion."""
    table_class = elem.get("class", "")
    if "Code_Table" in table_class:
        _extract_code_table(elem, parts)
        return
    md = _table_to_markdown(
        elem,
        snippets,
        topic_path,
        content_dir,
        seen_snippets,
    )
    if md:
        parts.append(md)


def _handle_paragraph(
    elem: etree._Element,
    parts: list[str],
    snippets: _SnippetMap,
    topic_path: Path,
    content_dir: Path,
    seen_snippets: set[str],
) -> None:
    """Handle <p> elements, detecting single-line code."""
    p_class = elem.get("class", "")
    if "Code" in p_class and "Code_Table" not in p_class:
        text = "".join(str(t) for t in elem.itertext()).strip()
        if text:
            parts.append(f"`{text}`")
        return
    para_parts: list[str] = []
    _collect_inline_text(
        elem,
        para_parts,
        snippets,
        topic_path,
        content_dir,
        seen_snippets,
    )
    para_text = " ".join(para_parts).strip()
    if para_text:
        parts.append(para_text)


def _collect_inline_text(
    elem: etree._Element,
    parts: list[str],
    snippets: _SnippetMap,
    topic_path: Path,
    content_dir: Path,
    seen_snippets: set[str],
) -> None:
    """Collect inline text, handling MadCap and HTML tags."""
    if elem.text and elem.text.strip():
        parts.append(elem.text.strip())

    for child in elem:
        if not isinstance(child.tag, str):
            if child.tail and child.tail.strip():
                parts.append(child.tail.strip())
            continue

        cqname = etree.QName(child.tag)

        if cqname.namespace == MADCAP_NS:
            _collect_madcap_inline(
                child,
                cqname.localname,
                parts,
                snippets,
                topic_path,
                content_dir,
                seen_snippets,
            )
        else:
            _collect_inline_text(
                child,
                parts,
                snippets,
                topic_path,
                content_dir,
                seen_snippets,
            )

        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())


def _collect_madcap_inline(
    child: etree._Element,
    local: str,
    parts: list[str],
    snippets: _SnippetMap,
    topic_path: Path,
    content_dir: Path,
    seen_snippets: set[str],
) -> None:
    """Handle a MadCap element inside inline text collection."""
    if local in _STRIP_TAGS:
        return
    if local in _KEEP_TEXT_TAGS:
        text = "".join(str(t) for t in child.itertext()).strip()
        if text:
            parts.append(text)
    elif local == "snippetText":
        _resolve_snippet(
            child,
            parts,
            snippets,
            topic_path,
            content_dir,
            seen_snippets,
            block=False,
        )
    elif local == "snippetBlock":
        _resolve_snippet(
            child,
            parts,
            snippets,
            topic_path,
            content_dir,
            seen_snippets,
            block=True,
        )
    elif local == "popup":
        head = child.find(f"{{{MADCAP_NS}}}popupHead")
        if head is not None:
            text = "".join(str(t) for t in head.itertext()).strip()
            if text:
                parts.append(text)


def _resolve_snippet(
    elem: etree._Element,
    parts: list[str],
    snippets: _SnippetMap,
    topic_path: Path,
    content_dir: Path,
    seen_snippets: set[str],
    *,
    block: bool,
) -> None:
    """Resolve a snippetBlock or snippetText reference."""
    src = elem.get("src", "")
    if not src:
        return

    # Normalize Windows backslash separators.
    src = src.replace("\\", "/")

    resolved = (topic_path.parent / src).resolve()
    try:
        rel_key = str(resolved.relative_to(content_dir))
    except ValueError:
        logger.warning(
            "Snippet path outside Content dir: %s in %s",
            src,
            topic_path,
        )
        return

    if rel_key in seen_snippets:
        logger.warning(
            "Circular snippet reference: %s in %s",
            rel_key,
            topic_path,
        )
        return

    snippet_body = snippets.get(rel_key)
    if snippet_body is None:
        logger.warning(
            "Snippet not found: %s (resolved to %s)",
            src,
            rel_key,
        )
        return

    new_seen = seen_snippets | {rel_key}
    if block:
        _walk_element(
            snippet_body,
            parts,
            snippets,
            topic_path,
            content_dir,
            new_seen,
        )
    else:
        _collect_inline_text(
            snippet_body,
            parts,
            snippets,
            topic_path,
            content_dir,
            new_seen,
        )


def _extract_code_table(elem: etree._Element, parts: list[str]) -> None:
    """Extract code block content from a Code_Table."""
    for pre in elem.iter("pre"):
        code = pre.find("code")
        if code is not None:
            cls = code.get("class", "")
            if "language-" in cls:
                lang = _extract_language(cls)
            else:
                lang = ""
            code_text = "".join(str(t) for t in code.itertext()).rstrip()
            parts.append(f"```{lang}\n{code_text}\n```")
            return
    # Fallback: extract all text from the table.
    text = "".join(str(t) for t in elem.itertext()).strip()
    if text:
        parts.append(f"```\n{text}\n```")


def _table_to_markdown(
    table: etree._Element,
    snippets: _SnippetMap,
    topic_path: Path,
    content_dir: Path,
    seen_snippets: set[str],
) -> str:
    """Convert an HTML table to markdown format."""
    rows = table.findall(".//tr")
    if not rows:
        return ""

    md_rows: list[list[str]] = []
    for row in rows:
        cells: list[str] = []
        for cell in row:
            if not isinstance(cell.tag, str):
                continue
            tag_local = etree.QName(cell.tag).localname
            if tag_local in ("th", "td"):
                cell_parts: list[str] = []
                _collect_inline_text(
                    cell,
                    cell_parts,
                    snippets,
                    topic_path,
                    content_dir,
                    seen_snippets,
                )
                cell_text = " ".join(cell_parts).strip()
                cell_text = cell_text.replace("|", "\\|")
                cells.append(cell_text)
        if cells:
            md_rows.append(cells)

    if not md_rows:
        return ""

    max_cols = max(len(r) for r in md_rows)
    for md_row in md_rows:
        while len(md_row) < max_cols:
            md_row.append("")

    header = md_rows[0]
    separator = ["---"] * max_cols
    body = md_rows[1:]

    lines = [
        " | ".join(header),
        " | ".join(separator),
    ]
    lines.extend(" | ".join(r) for r in body)
    return "\n".join(lines)


def _extract_list(
    list_elem: etree._Element,
    parts: list[str],
    snippets: _SnippetMap,
    topic_path: Path,
    content_dir: Path,
    seen_snippets: set[str],
    *,
    ordered: bool,
) -> None:
    """Extract list items as markdown."""
    items: list[str] = []
    for idx, child in enumerate(list_elem):
        if not isinstance(child.tag, str):
            continue
        tag_local = etree.QName(child.tag).localname
        if tag_local == "li":
            li_parts: list[str] = []
            _collect_inline_text(
                child,
                li_parts,
                snippets,
                topic_path,
                content_dir,
                seen_snippets,
            )
            item_text = " ".join(li_parts).strip()
            if item_text:
                pfx = f"{idx + 1}. " if ordered else "- "
                items.append(f"{pfx}{item_text}")
    if items:
        parts.append("\n".join(items))


def _extract_language(cls: str) -> str:
    """Extract language hint from a class like 'language-bbj'."""
    for part in cls.split():
        if part.startswith("language-"):
            return part.removeprefix("language-")
    return ""


__all__ = ["FlareParser"]
