# BBj Training Data Repository

Curated BBj code examples for fine-tuning language models.

## Why This Exists

Large language models have near-zero BBj training data in their base models. To improve LLM assistance for BBj developers, we need a high-quality corpus of examples that demonstrate:

- Correct BBj syntax and idioms
- Best practices across all BBj generations (Character, Visual PRO/5, BBj GUI, DWC)
- Common patterns for GUI, database, file I/O, and string handling
- Migration patterns between generations

## What's Here

Markdown files with YAML front matter, organized by topic:

| Directory      | Contents                                    |
|----------------|---------------------------------------------|
| `gui/`         | Windows, controls, events, callbacks        |
| `database/`    | File I/O, keyed files, SQL, ADO             |
| `strings/`     | String manipulation, parsing, formatting    |
| `file-io/`     | Sequential files, direct access, channels   |
| `control-flow/`| Loops, conditionals, GOSUBs, error handling |
| `oop/`         | Classes, methods, interfaces, inheritance   |
| `dwc/`         | DWC-specific patterns and web components    |

## Quick Start

### Running Validation

From the project root:

```bash
python training-data/scripts/validate.py
```

This discovers all example files and validates their front matter against the schema.

### Adding an Example

1. Create a markdown file in the appropriate topic directory
2. Add required front matter (title, type, generation)
3. Add Code, Expected Behavior/Output, and Explanation sections
4. Run validation
5. Submit a PR

See [FORMAT.md](FORMAT.md) for the complete format specification.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor workflow.

## Format Overview

Each example follows this structure:

```markdown
---
title: "Descriptive Title"
type: completion
generation: ["bbj-gui", "dwc"]
difficulty: basic
tags: [topic, keywords]
---

## Code

```bbj
REM Your BBj code here
```

## Expected Behavior

What happens when the code runs.

## Explanation

Step-by-step breakdown of the code.
```

## Schema

Front matter is validated against `schema/example.schema.json`. See [FORMAT.md](FORMAT.md) for field details.

## Future

Once we have sufficient examples, this corpus will be converted to JSONL format for fine-tuning. The markdown format enables human editing and GitHub rendering while maintaining the structured metadata needed for training data generation.
