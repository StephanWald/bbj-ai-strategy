#!/usr/bin/env python3
"""Validate training example front matter against JSON Schema.

Discovers all .md files in the training-data directory (excluding
documentation files), parses YAML front matter, and validates against
the example schema.

Usage:
    python training-data/scripts/validate.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import frontmatter  # type: ignore[import-untyped]
import jsonschema

# Files to skip (documentation, not training examples)
SKIP_FILES = {"README.md", "FORMAT.md", "CONTRIBUTING.md"}

# Pattern to detect fenced code blocks
CODE_BLOCK_RE = re.compile(r"```\w*\n[\s\S]*?```", re.MULTILINE)


def load_schema(script_dir: Path) -> dict:
    """Load the JSON Schema from the schema directory."""
    schema_path = script_dir.parent / "schema" / "example.schema.json"
    if not schema_path.exists():
        print(f"ERROR: Schema not found at {schema_path}")
        sys.exit(1)
    return json.loads(schema_path.read_text())


def has_code_block(content: str) -> bool:
    """Check if content contains at least one fenced code block."""
    return bool(CODE_BLOCK_RE.search(content))


def validate_example(file_path: Path, schema: dict) -> tuple[bool, str]:
    """Validate a single training example file.

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        post = frontmatter.load(str(file_path))
    except Exception as e:
        return False, f"Failed to parse front matter: {e}"

    # Validate front matter against schema
    try:
        jsonschema.validate(instance=post.metadata, schema=schema)
    except jsonschema.ValidationError as e:
        return False, f"Schema validation failed: {e.message}"

    # Check for non-empty content with code block
    if not post.content.strip():
        return False, "Content is empty"

    if not has_code_block(post.content):
        return False, "No code block found in content"

    return True, "OK"


def main() -> int:
    """Run validation on all training examples.

    Returns:
        Exit code: 0 if all pass, 1 if any fail
    """
    script_dir = Path(__file__).resolve().parent
    training_dir = script_dir.parent

    schema = load_schema(script_dir)

    # Find all markdown files
    md_files = sorted(training_dir.rglob("*.md"))

    valid_count = 0
    error_count = 0
    skipped_count = 0

    print(f"Validating training examples in {training_dir}")
    print("-" * 60)

    for md_file in md_files:
        # Skip documentation files
        if md_file.name in SKIP_FILES:
            skipped_count += 1
            continue

        # Skip files in schema or scripts directories
        relative = md_file.relative_to(training_dir)
        if relative.parts[0] in ("schema", "scripts"):
            skipped_count += 1
            continue

        is_valid, message = validate_example(md_file, schema)
        relative_path = md_file.relative_to(training_dir)

        if is_valid:
            print(f"  OK: {relative_path}")
            valid_count += 1
        else:
            print(f"  ERROR: {relative_path}")
            print(f"         {message}")
            error_count += 1

    print("-" * 60)
    print(f"Validated: {valid_count} OK, {error_count} errors, {skipped_count} skipped")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
