# Contributing Training Examples

This guide walks you through adding new BBj training examples to the repository.

## Before You Start

1. Review the [FORMAT.md](FORMAT.md) specification
2. Look at existing examples in topic directories
3. Ensure you have Python 3.8+ with `frontmatter` and `jsonschema` packages

## Step-by-Step Workflow

### Step 1: Choose the Topic Directory

Select the directory that best fits your example:

| Directory       | Use For                                      |
|-----------------|----------------------------------------------|
| `gui/`          | Windows, controls, events, layouts           |
| `database/`     | File I/O, keyed files, SQL, ADO              |
| `strings/`      | String manipulation, formatting, parsing     |
| `file-io/`      | Sequential files, channels, direct access    |
| `control-flow/` | Loops, conditionals, GOSUB, error handling   |
| `oop/`          | Classes, methods, interfaces                 |
| `dwc/`          | DWC-specific patterns, web components        |

### Step 2: Create the File

Use a descriptive kebab-case filename:

```
gui/button-callback.md         # Good
gui/button_callback.md         # Avoid underscores
gui/001-button-callback.md     # Avoid numbered prefixes
gui/ButtonCallback.md          # Avoid camelCase
```

### Step 3: Add Required Front Matter

Every example must have these fields:

```yaml
---
title: "Creating a Button with Callback"
type: completion
generation: ["bbj-gui", "dwc"]
---
```

Add optional fields to improve discoverability:

```yaml
---
title: "Creating a Button with Callback"
type: completion
generation: ["bbj-gui", "dwc"]
difficulty: basic
tags: [gui, button, callback, events]
description: "Shows how to create a button and handle click events"
---
```

### Step 4: Add Content Sections

Follow this structure:

```markdown
## Code

```bbj
REM Your code here
```

## Expected Behavior

What happens when the code runs.

## Explanation

1. First point
2. Second point
3. Third point
```

See [FORMAT.md](FORMAT.md) for complete content guidelines.

### Step 5: Run Validation

From the project root:

```bash
python training-data/scripts/validate.py
```

The script checks:

- Front matter parses correctly
- Required fields are present
- Field values match allowed enums
- Content is not empty

Fix any errors before proceeding.

### Step 6: Submit a Pull Request

1. Create a feature branch
2. Add your example file(s)
3. Run validation locally
4. Push and open a PR
5. Ensure CI validation passes

## Common Mistakes

### Missing Required Fields

**Wrong:**
```yaml
---
title: "My Example"
type: completion
# Missing: generation
---
```

**Right:**
```yaml
---
title: "My Example"
type: completion
generation: all
---
```

### Invalid Type Value

**Wrong:**
```yaml
type: code  # Not a valid type
```

**Right:**
```yaml
type: completion  # Or: comprehension, migration, explanation
```

### Invalid Generation Value

**Wrong:**
```yaml
generation: BBj-GUI  # Case-sensitive, wrong case
generation: bbj      # Not a valid value
```

**Right:**
```yaml
generation: bbj-gui              # Single value
generation: ["bbj-gui", "dwc"]   # Array for multiple
generation: all                  # Universal pattern
```

### Wrong Code Fence Language

**Wrong:**
````markdown
```basic
PRINT "Hello"
```
````

**Right:**
````markdown
```bbj
PRINT "Hello"
```
````

### Empty Content

**Wrong:**
```markdown
---
title: "Placeholder"
type: completion
generation: all
---

<!-- TODO: Add content later -->
```

**Right:**
Add actual code, expected behavior, and explanation sections.

## Quality Guidelines

### What Makes a Good Example

- **Complete**: Can be run as-is (or clearly shows which parts are snippets)
- **Correct**: Uses proper BBj syntax and idioms
- **Clear**: Purpose is obvious from the title and REM comment
- **Concise**: 10-50 lines of code typically, longer for complex topics
- **Commented**: REM comments explain non-obvious parts

### What to Avoid

- Examples that only work with specific data files
- Code with syntax errors
- Overly complex examples that try to show too much
- Duplicate examples (check existing files first)
- Examples using deprecated patterns without noting the deprecation

## Getting Help

- Review existing examples in the repository
- Check [FORMAT.md](FORMAT.md) for format questions
- Open an issue for questions about BBj patterns
