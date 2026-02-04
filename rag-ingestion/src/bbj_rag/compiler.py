"""BBj compiler validation module.

Validates BBj code syntax via the bbjcpl compiler subprocess.
This module provides the foundation for automatic validation of
BBj code snippets in chat responses.

Key functions:
- detect_bbj_code(): Heuristic detection of BBj code vs other languages
- validate_bbj_syntax(): Async validation via bbjcpl subprocess
"""

from __future__ import annotations

import asyncio
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of BBj syntax validation via bbjcpl.

    Attributes:
        valid: True if code compiled without syntax errors
        errors: Raw bbjcpl stderr output (empty string if valid)
        timed_out: True if validation exceeded timeout
        unavailable: True if bbjcpl was not found on the system
    """

    valid: bool
    errors: str  # Raw bbjcpl stderr output
    timed_out: bool = False
    unavailable: bool = False  # bbjcpl not found


# BBj keywords (lowercase, case-insensitive matching)
_BBJ_KEYWORDS = frozenset(
    [
        "rem",
        "let",
        "print",
        "open",
        "close",
        "read",
        "write",
        "input",
        "if",
        "then",
        "else",
        "endif",
        "while",
        "wend",
        "for",
        "next",
        "gosub",
        "return",
        "end",
        "dim",
        "def",
        "fn",
        "call",
        "enter",
        "exit",
        "begin",
        "process_events",
        "setcallback",
        "fi",
        "switch",
        "swend",
        "case",
        "default",
        "on",
        "goto",
        "extract",
        "remove",
        "release",
        "repeat",
        "until",
        "readrecord",
        "writerecord",
    ]
)

# Pattern for BBj-style comment: ! at line start (after optional whitespace)
_COMMENT_PATTERN = re.compile(r"^\s*!", re.MULTILINE)

# Pattern for channel syntax: #0, #1, etc.
_CHANNEL_PATTERN = re.compile(r"#\d+")

# Pattern for scope operator: ::
_SCOPE_PATTERN = re.compile(r"::")

# Pattern for BBj class prefix
_BBJ_PREFIX_PATTERN = re.compile(r"\bBBj\w+", re.IGNORECASE)

# Pattern for label: digits at start of line
_LABEL_PATTERN = re.compile(r"^\s*\d+\s+\w", re.MULTILINE)

# Pattern for BASIC-style print/input (keyword + string literal, no parens)
_BASIC_STATEMENT_PATTERN = re.compile(r'\b(print|input)\s+"', re.IGNORECASE)


def detect_bbj_code(code: str) -> bool:
    """Heuristically detect if code is likely BBj/BASIC.

    Uses multiple indicators to identify BBj code while avoiding
    false positives on other languages. Returns True if 2+ BBj
    indicators are found.

    Be conservative: when in doubt, return True and let bbjcpl decide.

    Args:
        code: Source code string to analyze

    Returns:
        True if code appears to be BBj, False otherwise
    """
    indicators = 0
    code_lower = code.lower()

    # Check for BBj keywords (must be word-bounded)
    # Each BBj keyword counts as an indicator
    words = set(re.findall(r"\b\w+\b", code_lower))
    keyword_matches = words & _BBJ_KEYWORDS
    indicators += len(keyword_matches)

    # Check for BBj-style comment (! at line start)
    if _COMMENT_PATTERN.search(code):
        indicators += 1

    # Check for channel syntax (#0, #1, etc.)
    if _CHANNEL_PATTERN.search(code):
        indicators += 1

    # Check for scope operator (::)
    if _SCOPE_PATTERN.search(code):
        indicators += 1

    # Check for BBj class prefix (BBjWindow, BBjString, etc.)
    if _BBJ_PREFIX_PATTERN.search(code):
        indicators += 1

    # Check for line labels (classic BASIC style: 100 PRINT "Hello")
    if _LABEL_PATTERN.search(code):
        indicators += 1

    # Check for BASIC-style statements (print "..." or input "...")
    if _BASIC_STATEMENT_PATTERN.search(code):
        indicators += 1

    # Require 2+ indicators to avoid false positives
    return indicators >= 2


async def validate_bbj_syntax(
    code: str, timeout: float | None = None
) -> ValidationResult:
    """Validate BBj code syntax via the bbjcpl compiler.

    Creates a temporary .bbj file, runs bbjcpl -N (syntax check only),
    and returns the result. The bbjcpl compiler always exits 0; errors
    are reported via stderr.

    Args:
        code: BBj source code to validate
        timeout: Maximum seconds to wait (defaults to BBJ_RAG_COMPILER_TIMEOUT
                 env var, then 10.0)

    Returns:
        ValidationResult with validation status and any errors
    """
    # Get configuration from env vars (avoid circular import with config.py)
    if timeout is None:
        timeout = float(os.environ.get("BBJ_RAG_COMPILER_TIMEOUT", "10.0"))
    compiler_path = os.environ.get("BBJ_RAG_COMPILER_PATH", "bbjcpl")

    # Create temp file with .bbj extension
    temp_path: Path | None = None
    try:
        # Use delete=False so we control cleanup
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".bbj",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write(code)
            temp_path = Path(f.name)

        # Run bbjcpl -N <file> (syntax check only, no output file)
        try:
            process = await asyncio.create_subprocess_exec(
                compiler_path,
                "-N",
                str(temp_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            # bbjcpl not found
            return ValidationResult(
                valid=False,
                errors="",
                unavailable=True,
            )

        # Wait with timeout
        try:
            _, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except TimeoutError:
            # Kill the process if it times out
            process.kill()
            await process.wait()
            return ValidationResult(
                valid=False,
                errors="",
                timed_out=True,
            )

        # Parse stderr: empty = valid, non-empty = errors
        stderr_text = stderr.decode("utf-8", errors="replace").strip()
        if stderr_text:
            return ValidationResult(
                valid=False,
                errors=stderr_text,
            )
        else:
            return ValidationResult(
                valid=True,
                errors="",
            )

    finally:
        # Clean up temp file
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
