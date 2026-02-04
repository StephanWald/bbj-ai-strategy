"""Chat response validation module for BBj code blocks.

Extracts fenced code blocks from chat responses, validates BBj code
via bbjcpl, and provides fix prompt generation for automatic repair.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bbj_rag.compiler import ValidationResult, detect_bbj_code, validate_bbj_syntax


@dataclass
class CodeBlock:
    """Represents a fenced code block extracted from text.

    Attributes:
        code: The code content (without fences)
        language: Language tag from fence (e.g., 'bbj', 'python') or None
        start_pos: Position in original text where block starts (including fence)
        end_pos: Position in original text where block ends (after closing fence)
        is_bbj: Whether this block is identified as BBj code
        validation_result: Result from bbjcpl validation (None if not validated)
        attempts: Number of validation/fix attempts made
    """

    code: str
    language: str | None
    start_pos: int
    end_pos: int
    is_bbj: bool
    validation_result: ValidationResult | None = field(default=None)
    attempts: int = field(default=0)


# Regex to match fenced code blocks: ```lang\ncode\n```
# Captures: (1) optional language tag, (2) code content
# Uses non-greedy match for code to handle multiple blocks
_CODE_BLOCK_PATTERN = re.compile(
    r"```(\w*)\n(.*?)```",
    re.DOTALL,
)


def extract_code_blocks(text: str) -> list[CodeBlock]:
    """Extract all fenced code blocks from text.

    Identifies BBj code blocks by:
    1. Explicit language tag: 'bbj' or 'basic'
    2. Heuristic detection via detect_bbj_code() for untagged/generic blocks

    Args:
        text: Text containing potential code blocks

    Returns:
        List of CodeBlock objects with position and language info
    """
    blocks: list[CodeBlock] = []

    for match in _CODE_BLOCK_PATTERN.finditer(text):
        language_tag = match.group(1) or None
        code = match.group(2)
        start_pos = match.start()
        end_pos = match.end()

        # Determine if this is BBj code
        if language_tag:
            language_lower = language_tag.lower()
            # Explicit BBj/BASIC tag
            is_bbj = language_lower in ("bbj", "basic")
        else:
            # No tag or empty tag - use heuristic detection
            is_bbj = detect_bbj_code(code)

        blocks.append(
            CodeBlock(
                code=code,
                language=language_tag,
                start_pos=start_pos,
                end_pos=end_pos,
                is_bbj=is_bbj,
            )
        )

    return blocks


async def validate_code_blocks(
    blocks: list[CodeBlock],
    timeout: float = 10.0,
) -> list[CodeBlock]:
    """Validate BBj code blocks via bbjcpl.

    Only validates blocks where is_bbj is True. Stores results
    in each block's validation_result field and increments attempts.

    Args:
        blocks: List of CodeBlock objects to validate
        timeout: Timeout per validation call in seconds

    Returns:
        The same list with validation_result populated for BBj blocks
    """
    for block in blocks:
        if block.is_bbj:
            result = await validate_bbj_syntax(block.code, timeout)
            block.validation_result = result
            block.attempts += 1

    return blocks


def build_fix_prompt(code: str, errors: str) -> str:
    """Build a prompt asking Claude to fix BBj syntax errors.

    Args:
        code: The BBj code with syntax errors
        errors: The compiler error output from bbjcpl

    Returns:
        A prompt string for Claude to fix the code
    """
    return f"""The following BBj code has syntax errors:

```bbj
{code}
```

Compiler errors:
{errors}

Please fix the syntax errors and return ONLY the corrected BBj code.
Do not include explanations or markdown formatting."""


def replace_code_block(text: str, old_block: CodeBlock, new_code: str) -> str:
    """Replace a code block in text with new code.

    Preserves the original fence formatting (language tag, backticks).

    Args:
        text: Original text containing the code block
        old_block: The CodeBlock to replace
        new_code: New code content to insert

    Returns:
        Text with the code block replaced
    """
    # Build the replacement with original language tag
    lang_tag = old_block.language or ""
    replacement = f"```{lang_tag}\n{new_code}```"

    # Replace at exact position
    return text[: old_block.start_pos] + replacement + text[old_block.end_pos :]
