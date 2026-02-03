"""Heading-aware markdown chunker for BBj documentation.

Splits Document.content at heading boundaries (## and ###), preserves
fenced code blocks as atomic units, sub-splits oversized sections at
paragraph and sentence boundaries, and prepends context headers for
richer embeddings.
"""

from __future__ import annotations

import re

from bbj_rag.intelligence.context_headers import build_context_header
from bbj_rag.models import Chunk, Document

# Regex for fenced code blocks (``` ... ```).  DOTALL so . matches newlines.
_CODE_FENCE_RE = re.compile(r"```[^\n]*\n.*?```", re.DOTALL)

# Heading pattern matching ## and ### (not # which is the page title).
_HEADING_RE = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)

# Sentence boundary: period/question/exclamation followed by space or end.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _estimate_tokens(text: str) -> int:
    """Approximate token count: word count / 0.75.

    This is sufficient for chunking boundaries with 32K context models.
    """
    words = len(text.split())
    return int(words / 0.75)


def _split_at_headings(
    content: str,
) -> list[tuple[str, str]]:
    """Split markdown at ## and ### heading boundaries.

    Returns a list of (heading_path, section_text) tuples.  The heading_path
    is the heading text for that section (e.g. "Parameters").  Content before
    the first heading gets an empty heading_path.
    """
    # Protect code blocks from heading detection by replacing them with
    # placeholders, then restoring after splitting.
    code_blocks: list[str] = []

    def _replace_code(match: re.Match[str]) -> str:
        idx = len(code_blocks)
        code_blocks.append(match.group(0))
        return f"\x00CODEBLOCK{idx}\x00"

    protected = _CODE_FENCE_RE.sub(_replace_code, content)

    # Find all heading positions.
    matches = list(_HEADING_RE.finditer(protected))

    sections: list[tuple[str, str]] = []

    if not matches:
        # No headings -- treat entire content as one section.
        restored = _restore_code_blocks(protected, code_blocks)
        return [("", restored)]

    # Content before first heading.
    if matches[0].start() > 0:
        pre_text = protected[: matches[0].start()]
        restored = _restore_code_blocks(pre_text, code_blocks)
        if restored.strip():
            sections.append(("", restored))

    for i, match in enumerate(matches):
        heading_text = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(protected)
        section_text = protected[start:end]
        restored = _restore_code_blocks(section_text, code_blocks)
        # Include the heading line in the section text for context.
        heading_line = match.group(0)
        heading_line = _restore_code_blocks(heading_line, code_blocks)
        full_section = heading_line + restored
        if full_section.strip():
            sections.append((heading_text, full_section))

    return sections


def _restore_code_blocks(text: str, code_blocks: list[str]) -> str:
    """Replace code block placeholders with original content."""
    for i, block in enumerate(code_blocks):
        text = text.replace(f"\x00CODEBLOCK{i}\x00", block)
    return text


def _split_oversized(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    """Sub-split text that exceeds max_tokens.

    First attempts to split at paragraph boundaries (double newline).
    If paragraphs are still too large, splits at sentence boundaries.
    Code blocks are never split -- if a single code block exceeds
    max_tokens it is kept as one chunk.
    """
    if _estimate_tokens(text) <= max_tokens:
        return [text]

    # Extract code blocks as atomic units.
    parts = _split_around_code_blocks(text)
    chunks: list[str] = []
    current = ""

    for part_text, is_code in parts:
        if is_code:
            # Code block is atomic.  Flush current accumulator first.
            if current.strip():
                chunks.extend(_split_plain_text(current, max_tokens, overlap_tokens))
                current = ""
            chunks.append(part_text)
        else:
            current += part_text

    if current.strip():
        chunks.extend(_split_plain_text(current, max_tokens, overlap_tokens))

    return [c for c in chunks if c.strip()]


def _split_around_code_blocks(text: str) -> list[tuple[str, bool]]:
    """Split text into alternating (plain, is_code) segments."""
    parts: list[tuple[str, bool]] = []
    last_end = 0

    for match in _CODE_FENCE_RE.finditer(text):
        if match.start() > last_end:
            parts.append((text[last_end : match.start()], False))
        parts.append((match.group(0), True))
        last_end = match.end()

    if last_end < len(text):
        parts.append((text[last_end:], False))

    return parts


def _split_plain_text(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    """Split plain text at paragraph then sentence boundaries."""
    if _estimate_tokens(text) <= max_tokens:
        return [text]

    # Try paragraph splitting first.
    paragraphs = text.split("\n\n")
    if len(paragraphs) > 1:
        return _merge_segments(paragraphs, max_tokens, overlap_tokens, "\n\n")

    # Fall back to sentence splitting.
    sentences = _SENTENCE_RE.split(text)
    if len(sentences) > 1:
        return _merge_segments(sentences, max_tokens, overlap_tokens, " ")

    # Cannot split further -- return as-is.
    return [text]


def _merge_segments(
    segments: list[str],
    max_tokens: int,
    overlap_tokens: int,
    separator: str,
) -> list[str]:
    """Merge small segments into chunks up to max_tokens, with overlap."""
    chunks: list[str] = []
    current_segments: list[str] = []
    current_tokens = 0

    for seg in segments:
        seg_tokens = _estimate_tokens(seg)
        if current_segments and current_tokens + seg_tokens > max_tokens:
            chunks.append(separator.join(current_segments))
            # Overlap: keep trailing segments whose tokens sum to ~overlap_tokens.
            overlap_segs: list[str] = []
            overlap_count = 0
            for s in reversed(current_segments):
                s_tok = _estimate_tokens(s)
                if overlap_count + s_tok > overlap_tokens:
                    break
                overlap_segs.insert(0, s)
                overlap_count += s_tok
            current_segments = overlap_segs
            current_tokens = overlap_count

        current_segments.append(seg)
        current_tokens += seg_tokens

    if current_segments:
        chunks.append(separator.join(current_segments))

    return chunks


def chunk_document(
    doc: Document,
    max_tokens: int = 400,
    overlap_tokens: int = 50,
) -> list[Chunk]:
    """Split a Document into Chunks using heading-aware strategy.

    1. Split content at heading boundaries (##, ###).
    2. Sub-split oversized sections at paragraph/sentence boundaries.
    3. Keep fenced code blocks intact (never split inside ``` fences).
    4. Prepend context_header to chunk content for richer embeddings.
    5. Create Chunk via ``from_content()`` factory (auto-computes content_hash).

    Each chunk inherits source_url, title, doc_type, generations,
    deprecated, and metadata from the parent Document.
    """
    sections = _split_at_headings(doc.content)
    chunks: list[Chunk] = []

    section_path = doc.metadata.get("section_path", "")

    for heading_path, section_text in sections:
        sub_texts = _split_oversized(section_text, max_tokens, overlap_tokens)

        for text in sub_texts:
            # Build context header for this chunk.
            header = build_context_header(
                section_path,
                doc.title,
                heading_path,
            )

            # Prepend context header to content for embedding.
            if header:
                embeddable_content = f"{header}\n\n{text}"
            else:
                embeddable_content = text

            chunk = Chunk.from_content(
                source_url=doc.source_url,
                title=doc.title,
                doc_type=doc.doc_type,
                content=embeddable_content,
                generations=doc.generations,
                context_header=header,
                deprecated=doc.deprecated,
                source_type=doc.source_type,
                display_url=doc.display_url,
                metadata=doc.metadata,
            )
            chunks.append(chunk)

    return chunks


__all__ = ["chunk_document"]
