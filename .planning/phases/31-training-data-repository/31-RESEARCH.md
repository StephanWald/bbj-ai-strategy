# Phase 31: Training Data Repository - Research

**Researched:** 2026-02-05
**Domain:** Training data infrastructure, markdown documentation, front matter validation
**Confidence:** HIGH

## Summary

This phase establishes infrastructure for systematically collecting and validating curated BBj code examples that will eventually be converted to JSONL for fine-tuning. The phase focuses on repository structure, format specification, and validation tooling -- not the actual JSONL conversion (deferred to future phases per requirements).

The decision context specifies: (1) markdown files with YAML front matter for metadata, (2) "code first, explanation after" structure, (3) topic-based flat directory organization (e.g., `gui/`, `database/`), and (4) both snippets (10-50 lines) and complete runnable programs. The format aligns with the training data schema defined in `bbj-llm-strategy.md` Appendix B, which specifies fields like `type`, `generation`, `difficulty`, `instruction`, `input/prefix`, and `output/completion`.

The project already has `python-frontmatter>=1.1` in dependencies (for MDX parsing), and the existing `mdx.py` parser demonstrates the pattern for loading and validating markdown with front matter. Validation can leverage `jsonschema>=4.26` to ensure front matter conforms to the training example schema.

**Primary recommendation:** Create a `training-data/` directory at project root (separate from `rag-ingestion/` which is for RAG content), with topic subdirectories, a JSON Schema for front matter validation, and a simple Python validation script.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `python-frontmatter` | >=1.1 | Parse YAML front matter from markdown | Already in project, used by MDX parser |
| `jsonschema` | 4.26 | Validate front matter against schema | Python standard for JSON/YAML validation |
| `pyyaml` | >=6.0 | YAML parsing (frontmatter dependency) | Already in project dependencies |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pathlib` | stdlib | Path handling | File discovery and traversal |
| `ruff` | >=0.14 | Python linting (for validation script) | Already configured in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON Schema validation | Pydantic model | JSON Schema more portable, shareable with non-Python tools |
| Separate training-data repo | Subdirectory in bbj-ai-strategy | Single repo simpler for v1.6; can extract later if needed |
| Numbered file naming | Descriptive slugs | Slugs more readable, no ordering conflicts |

**Installation:**
No new dependencies required. All needed libraries already in `pyproject.toml`.

## Architecture Patterns

### Recommended Project Structure
```
bbj-ai-strategy/
├── training-data/
│   ├── README.md              # Overview and contributor guide
│   ├── FORMAT.md              # Detailed format specification
│   ├── CONTRIBUTING.md        # How to add new examples
│   ├── schema/
│   │   └── example.schema.json    # JSON Schema for validation
│   ├── scripts/
│   │   └── validate.py            # Validation script
│   ├── gui/                   # GUI examples (windows, controls, events)
│   │   ├── hello-window.md
│   │   └── button-callback.md
│   ├── database/              # Database/file I/O examples
│   │   └── keyed-file-read.md
│   ├── strings/               # String manipulation
│   ├── file-io/               # File operations
│   ├── control-flow/          # Loops, conditionals
│   ├── oop/                   # Classes, methods
│   └── dwc/                   # DWC-specific patterns
```

### Pattern 1: Markdown Training Example Format
**What:** Each training example is a markdown file with YAML front matter and structured content sections
**When to use:** All training examples
**Example:**
```markdown
---
title: "Creating a Hello World Window"
type: completion
generation: ["bbj-gui", "dwc"]
difficulty: basic
tags: [gui, window, sysgui]
description: "Shows how to create and display a basic window in BBj"
---

## Code

```bbj
sysgui! = BBjAPI().getSysGui()
window! = sysgui!.addWindow(100, 100, 400, 300, "Hello World")
window!.setCallback(window!.ON_CLOSE, "handleClose")

process_events

handleClose:
    release
```

## Expected Behavior

A 400x300 pixel window appears at screen position (100,100) with the title "Hello World". The window remains open until closed by the user, at which point the program terminates.

## Explanation

1. `BBjAPI().getSysGui()` returns the system GUI manager
2. `addWindow()` creates a top-level window with position, size, and title
3. `setCallback()` registers a handler for the close event
4. `process_events` enters the BBj event loop
5. The `handleClose` label releases resources when the window closes
```

### Pattern 2: Front Matter Schema Alignment
**What:** Front matter fields map to the TrainingExample TypeScript interface from bbj-llm-strategy.md
**When to use:** Schema design
**Example:**
```yaml
# Required fields
title: string          # Human-readable title
type: enum             # completion | comprehension | migration | explanation
generation: string|array  # "all" | "character" | "vpro5" | "bbj-gui" | "dwc" | array

# Optional fields
difficulty: enum       # basic | intermediate | advanced
tags: array            # Topic tags for organization
description: string    # One-sentence description
requires_version: string  # e.g., "23.04" for version-specific features
from_generation: string   # For migration type only
to_generation: string|array  # For migration type only
```

### Pattern 3: Validation Script Structure
**What:** Python script that discovers all .md files, parses front matter, validates against schema
**When to use:** CI and local validation
**Example:**
```python
#!/usr/bin/env python3
"""Validate training example front matter against schema."""
import sys
from pathlib import Path
import frontmatter
import jsonschema
import json

def validate_examples(data_dir: Path, schema_path: Path) -> int:
    schema = json.loads(schema_path.read_text())
    errors = 0
    for md_file in data_dir.rglob("*.md"):
        if md_file.name in ("README.md", "FORMAT.md", "CONTRIBUTING.md"):
            continue
        try:
            post = frontmatter.load(str(md_file))
            jsonschema.validate(instance=post.metadata, schema=schema)
        except jsonschema.ValidationError as e:
            print(f"ERROR: {md_file}: {e.message}")
            errors += 1
    return errors
```

### Anti-Patterns to Avoid
- **Nested directories:** Keep topics flat per decision context; no `gui/windows/toplevel/`
- **Numbered file prefixes:** Use descriptive slugs like `button-callback.md`, not `001-button-callback.md`
- **JSONL in markdown:** Don't put JSON in the files; markdown converts to JSONL later
- **Complex content structure:** Keep it simple: code block, output/behavior, explanation

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom parser | `python-frontmatter` | Handles edge cases, encoding, BOM |
| Schema validation | Manual field checks | `jsonschema.validate()` | Standard, portable, good error messages |
| File discovery | Manual glob | `pathlib.rglob("*.md")` | Already used in project patterns |
| Markdown structure | Custom format | Standard fenced code blocks | Renders in GitHub, editors, docs |

**Key insight:** The project already uses `python-frontmatter` for MDX parsing (see `parsers/mdx.py`). Follow that pattern for consistency. The validation script can be minimal because `jsonschema` handles all the heavy lifting.

## Common Pitfalls

### Pitfall 1: Inconsistent Generation Labels
**What goes wrong:** Using "BBj GUI" vs "bbj-gui" vs "bbj_gui" inconsistently
**Why it happens:** Natural language variation in contributor submissions
**How to avoid:** Enum constraint in JSON Schema; only allow: `"all"`, `"character"`, `"vpro5"`, `"bbj-gui"`, `"dwc"`
**Warning signs:** Validation script catches, but review before merge

### Pitfall 2: Code Blocks Without Language Tag
**What goes wrong:** Fenced code blocks lack `bbj` language identifier
**Why it happens:** Contributors forget to specify language
**How to avoid:** Document in FORMAT.md; optionally add content validation
**Warning signs:** Code blocks render without syntax highlighting

### Pitfall 3: Missing Required Fields
**What goes wrong:** Examples lack `type` or `generation` which are needed for JSONL conversion
**Why it happens:** Format not enforced during editing
**How to avoid:** JSON Schema with `required` array; validation in CI
**Warning signs:** Validation errors on PR

### Pitfall 4: Output Field Ambiguity
**What goes wrong:** Strategy doc uses both `output` and `completion` for similar purposes
**Why it happens:** Different names in comprehension vs completion types
**How to avoid:** In markdown format, always use "Expected Behavior" or "Expected Output" section; normalize during JSONL conversion
**Warning signs:** Confusion in contributor guide

### Pitfall 5: No Content After Front Matter
**What goes wrong:** File has front matter but empty or minimal content
**Why it happens:** Placeholder files created but never filled in
**How to avoid:** Validation script checks for non-empty content section
**Warning signs:** Examples without code blocks

## Code Examples

Verified patterns from the existing codebase and official documentation:

### Front Matter Parsing (from mdx.py)
```python
# Source: bbj_rag/parsers/mdx.py lines 136-137
import frontmatter
post = frontmatter.load(str(path))
metadata = post.metadata  # dict of YAML fields
content = post.content    # markdown content
```

### JSON Schema Validation
```python
# Source: https://python-jsonschema.readthedocs.io/
from jsonschema import validate

schema = {
    "type": "object",
    "required": ["title", "type", "generation"],
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "type": {
            "type": "string",
            "enum": ["completion", "comprehension", "migration", "explanation"]
        },
        "generation": {
            "oneOf": [
                {"type": "string", "enum": ["all", "character", "vpro5", "bbj-gui", "dwc"]},
                {"type": "array", "items": {"type": "string", "enum": ["character", "vpro5", "bbj-gui", "dwc"]}}
            ]
        },
        "difficulty": {
            "type": "string",
            "enum": ["basic", "intermediate", "advanced"]
        },
        "tags": {"type": "array", "items": {"type": "string"}},
        "description": {"type": "string"}
    }
}

validate(instance=post.metadata, schema=schema)
```

### Complete Seed Example: GUI Window
```markdown
---
title: "Hello World Window"
type: completion
generation: ["bbj-gui", "dwc"]
difficulty: basic
tags: [gui, window, sysgui, hello-world]
description: "Create and display a basic BBj window"
---

## Code

```bbj
REM Hello World Window - Modern BBj
sysgui! = BBjAPI().getSysGui()
window! = sysgui!.addWindow(100, 100, 400, 300, "Hello World")
window!.setCallback(window!.ON_CLOSE, "handleClose")

process_events

handleClose:
    release
```

## Expected Behavior

A 400x300 pixel window appears at screen position (100,100) with title "Hello World". Window stays open until user closes it, then program exits cleanly.

## Explanation

This is the minimal BBj GUI application:

1. **Get GUI manager**: `BBjAPI().getSysGui()` returns the system GUI interface
2. **Create window**: `addWindow(x, y, width, height, title)` creates a top-level window
3. **Handle close**: `setCallback()` connects the close event to a label
4. **Event loop**: `process_events` starts the BBj event processing loop
5. **Cleanup**: The `release` statement frees resources when closing
```

### Complete Seed Example: Keyed File Read
```markdown
---
title: "Reading from a Keyed File"
type: comprehension
generation: all
difficulty: basic
tags: [file-io, keyed-file, read]
description: "Read a record by key from a BBj data file"
---

## Code

```bbj
REM Read customer record by ID
custId$ = "CUST001"

OPEN (1)"customers.dat"
READ (1, KEY=custId$, ERR=NOT_FOUND) name$, address$, balance
CLOSE (1)
PRINT "Customer: ", name$
PRINT "Balance: ", balance
END

NOT_FOUND:
    PRINT "Customer not found: ", custId$
    CLOSE (1, ERR=*NEXT)
END
```

## Expected Output

If customer exists:
```
Customer: Acme Corp
Balance: 1250.00
```

If customer not found:
```
Customer not found: CUST001
```

## Explanation

BBj keyed file operations work across all generations:

1. **Channel number**: `(1)` is the file channel - an integer identifying the open file
2. **KEY clause**: Reads the record matching the specified key value
3. **ERR clause**: Branches to label if key not found (error 11)
4. **Field list**: Variables receive values in order they were written
5. **CLOSE**: Always close files to release system resources
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| JSONL-first format | Markdown-first format | Phase 31 decision | Human-editable, GitHub-renderable |
| Single flat directory | Topic-based directories | Phase 31 decision | Better organization, discoverability |

**Deprecated/outdated:**
- N/A - This is a new feature, no legacy approaches

## Open Questions

Things that couldn't be fully resolved:

1. **Multi-file programs**
   - What we know: Some examples span multiple files (main + class files)
   - What's unclear: How to represent multi-file examples in single markdown
   - Recommendation: Use multiple fenced code blocks with comments indicating filename; document in FORMAT.md

2. **Version-specific features**
   - What we know: `requires_version` field exists in schema
   - What's unclear: How to handle version matrix across generations
   - Recommendation: Start simple with optional field; evolve based on actual needs

3. **Output capture automation**
   - What we know: Expected output section is manual currently
   - What's unclear: Whether to automate running examples and capturing output
   - Recommendation: Defer automation; focus on manual curation for quality

## Discretionary Recommendations

Per the CONTEXT.md "Claude's Discretion" section:

### Repository Location
**Recommendation:** Create `training-data/` directory at project root, NOT in a separate repository.

**Rationale:**
- Single repo simplifies initial contribution workflow
- Training data is closely tied to strategy documentation
- Can extract to separate repo later if scale requires
- Consistent with project's single-repo monolith structure

### File Naming Convention
**Recommendation:** Use descriptive kebab-case slugs (e.g., `hello-window.md`, `button-callback.md`)

**Rationale:**
- More readable than numbered prefixes
- Self-documenting without needing to open file
- No ordering conflicts when adding new examples
- Consistent with web conventions

### Validation Approach
**Recommendation:** JSON Schema for front matter + Python script for validation

**Rationale:**
- JSON Schema is portable (can use in CI, editors, other languages)
- `jsonschema` library already tested pattern (see pypi docs)
- Python script fits existing project tooling (ruff, pytest)
- Can run in CI via GitHub Actions

### Contributor Workflow
**Recommendation:** PR-based workflow with validation check

**Rationale:**
- Validation script runs on PR (add to GitHub Actions)
- README.md provides quick start
- CONTRIBUTING.md provides detailed instructions
- FORMAT.md is the authoritative format reference

## Sources

### Primary (HIGH confidence)
- `/Users/beff/_workspace/bbj-ai-strategy/bbj-llm-strategy.md` - Training data schema (Appendix B)
- `/Users/beff/_workspace/bbj-ai-strategy/rag-ingestion/src/bbj_rag/parsers/mdx.py` - Front matter parsing pattern
- `/Users/beff/_workspace/bbj-ai-strategy/rag-ingestion/pyproject.toml` - Existing dependencies
- [python-frontmatter PyPI](https://pypi.org/project/python-frontmatter/) - v1.1.0 documentation
- [jsonschema PyPI](https://pypi.org/project/jsonschema/) - v4.26.0, released 2026-01-07

### Secondary (MEDIUM confidence)
- [GitHub Docs - YAML Frontmatter](https://docs.github.com/en/contributing/writing-for-github-docs/using-yaml-frontmatter) - Front matter best practices
- [GitHub Docs - PR Templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository) - Contributor workflow

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project, verified via pyproject.toml
- Architecture: HIGH - Based on existing project patterns and strategy doc
- Pitfalls: MEDIUM - Based on general markdown/YAML experience, may discover more during implementation
- Discretionary recommendations: MEDIUM - Reasonable defaults that can be adjusted

**Research date:** 2026-02-05
**Valid until:** 2026-03-05 (30 days - stable requirements)
