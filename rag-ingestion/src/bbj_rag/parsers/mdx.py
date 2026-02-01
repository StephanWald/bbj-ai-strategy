"""Docusaurus MDX parser for DWC-Course content.

Extracts ``Document`` objects from ``.md`` and ``.mdx`` files in a
Docusaurus-style docs directory.  YAML frontmatter is parsed for
metadata and JSX/import statements are stripped, leaving clean
Markdown content suitable for chunking and embedding.

All DWC-Course content is uniformly tagged with the ``dwc`` generation.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path

import frontmatter  # type: ignore[import-untyped]

from bbj_rag.models import Document

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JSX stripping patterns
# ---------------------------------------------------------------------------

_IMPORT_RE = re.compile(r"^import\s+.+$", re.MULTILINE)
_SELF_CLOSING_JSX_RE = re.compile(r"<[A-Z][A-Za-z]*\s*/>")
_JSX_OPEN_TAG_RE = re.compile(r"<[A-Z][A-Za-z]*[^>]*>")
_JSX_CLOSE_TAG_RE = re.compile(r"</[A-Z][A-Za-z]*>")
_DIV_CLASS_OPEN_RE = re.compile(r'<div\s+className="[^"]*"[^>]*>')
_DIV_CLOSE_RE = re.compile(r"</div>")
_EXCESS_BLANKS_RE = re.compile(r"\n{3,}")


def _strip_jsx(content: str) -> str:
    """Remove JSX and import statements from MDX content.

    Preserves Markdown (including fenced code blocks like Mermaid)
    while stripping React component syntax.
    """
    content = _IMPORT_RE.sub("", content)
    content = _SELF_CLOSING_JSX_RE.sub("", content)
    content = _JSX_OPEN_TAG_RE.sub("", content)
    content = _JSX_CLOSE_TAG_RE.sub("", content)
    content = _DIV_CLASS_OPEN_RE.sub("", content)
    content = _DIV_CLOSE_RE.sub("", content)
    content = _EXCESS_BLANKS_RE.sub("\n\n", content)
    return content.strip()


def _extract_title(post: frontmatter.Post, content: str, path: Path) -> str:
    """Extract the best available title for an MDX document.

    Priority: frontmatter ``title`` > first ``# `` heading > filename stem.
    """
    fm_title = post.metadata.get("title")
    if fm_title and str(fm_title).strip():
        return str(fm_title).strip()

    # Look for first level-1 heading.
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("##"):
            return stripped[2:].strip()

    return path.stem.replace("-", " ").replace("_", " ").title()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class MdxParser:
    """Parse Docusaurus MDX/Markdown files into ``Document`` objects.

    Recursively scans ``docs_dir`` for ``.md`` and ``.mdx`` files, parses
    YAML frontmatter, strips JSX, and yields one ``Document`` per file.

    All documents are tagged with generation ``["dwc"]`` and
    doc_type ``"tutorial"`` since DWC-Course is tutorial content.

    Implements the ``DocumentParser`` protocol.

    Args:
        docs_dir: Root directory of the Docusaurus docs folder.
    """

    def __init__(self, docs_dir: Path) -> None:
        self._docs_dir = docs_dir

    def parse(self) -> Iterator[Document]:
        """Yield one ``Document`` per valid MDX/Markdown file."""
        md_files = sorted(self._docs_dir.rglob("*.md"))
        mdx_files = sorted(self._docs_dir.rglob("*.mdx"))
        all_files = md_files + mdx_files

        logger.info(
            "MDX parser: found %d files (%d .md, %d .mdx) in %s",
            len(all_files),
            len(md_files),
            len(mdx_files),
            self._docs_dir,
        )

        processed = 0
        skipped = 0

        for path in all_files:
            if not path.is_file():
                continue

            try:
                post = frontmatter.load(str(path))
            except Exception:
                logger.warning("MDX parser: failed to load %s", path)
                skipped += 1
                continue

            raw_content: str = post.content
            cleaned = _strip_jsx(raw_content)

            if not cleaned.strip():
                logger.debug("MDX parser: skipping empty file %s", path)
                skipped += 1
                continue

            title = _extract_title(post, raw_content, path)
            relative_path = path.relative_to(self._docs_dir)

            # Derive chapter from parent directory name.
            chapter_dir = relative_path.parent.name if relative_path.parent.name else ""
            if chapter_dir:
                chapter_label = chapter_dir.replace("-", " ").replace("_", " ").title()
                context_header = f"DWC Course > {chapter_label} > {title}"
            else:
                context_header = f"DWC Course > {title}"

            # Build metadata.
            metadata: dict[str, str] = {"source": "dwc_course"}
            sidebar_position = post.metadata.get("sidebar_position")
            if sidebar_position is not None:
                metadata["sidebar_position"] = str(sidebar_position)

            yield Document(
                source_url=f"dwc-course://{relative_path}",
                title=title,
                doc_type="tutorial",
                content=cleaned,
                generations=["dwc"],
                context_header=context_header,
                metadata=metadata,
                deprecated=False,
            )
            processed += 1

        logger.info(
            "MDX parser: processed %d files, skipped %d",
            processed,
            skipped,
        )


__all__ = ["MdxParser"]
