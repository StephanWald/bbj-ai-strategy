"""System prompt construction with RAG context and citation instructions.

Builds a grounded system prompt that instructs Claude to answer using
only the provided reference material, citing sources inline with
[Source N](url) markdown link notation.
"""

from __future__ import annotations

from bbj_rag.search import SearchResult


def build_rag_system_prompt(
    results: list[SearchResult],
    low_confidence: bool = False,
) -> str:
    """Build a system prompt grounding Claude in RAG search results.

    Parameters
    ----------
    results:
        Ranked search results to include as reference material.
    low_confidence:
        When True, adds a caveat instructing Claude to be transparent
        about limited reference material.

    Returns
    -------
    str
        The assembled system prompt string.
    """
    sections: list[str] = []

    # Role
    sections.append(
        "You are a BBj programming assistant embedded in the official "
        "BBj documentation site."
    )

    # Citation instructions
    sections.append(
        "Answer questions using ONLY the reference material provided below. "
        "Cite sources inline using [Source N](url) markdown link notation, "
        "where N matches the source number and url is the source URL. "
        "For each claim, cite the 1-3 most relevant sources. When citing, "
        "mention the source type label naturally, for example: "
        '"according to the Flare Docs [Source 1](url)..." or '
        '"the PDF Manual notes [Source 2](url)...".'
    )

    # Low confidence caveat
    if low_confidence:
        sections.append(
            "Note: Limited reference material was found for this query. "
            "Indicate this to the user and be transparent about what you "
            "can and cannot confirm from the available sources."
        )

    # Formatting instructions
    sections.append(
        "Format your response using Markdown. Use ```bbj for BBj code "
        "blocks. Keep answers focused and practical."
    )

    # Reference material
    if results:
        context_blocks: list[str] = []
        for i, r in enumerate(results, 1):
            url = r.display_url or r.source_url
            source_type = r.source_type or "Documentation"
            block = f"[Source {i}: {r.title}]\n"
            block += f"URL: {url}\n"
            block += f"Type: {source_type}\n"
            if r.context_header:
                block += f"Context: {r.context_header}\n"
            block += f"\n{r.content}"
            context_blocks.append(block)

        context_text = "\n---\n".join(context_blocks)
        sections.append(f"Reference Material:\n{context_text}")
    else:
        sections.append(
            "No reference material was found for this query. "
            "Let the user know you could not find relevant documentation."
        )

    return "\n\n".join(sections)
