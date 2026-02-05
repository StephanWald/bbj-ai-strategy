# Training Example Format Specification

This document defines the format for BBj training examples in this repository.

## File Structure

Each example is a Markdown file with:

1. YAML front matter (metadata)
2. `## Code` section with BBj code
3. `## Expected Behavior` or `## Expected Output` section
4. `## Explanation` section

## Front Matter Schema

Front matter is validated against `schema/example.schema.json`.

### Required Fields

| Field       | Type            | Description                          |
|-------------|-----------------|--------------------------------------|
| `title`     | string          | Human-readable title (min 1 char)    |
| `type`      | enum            | Example type (see below)             |
| `generation`| string or array | Target BBj generation(s) (see below) |

#### Type Values

| Value          | Description                                      |
|----------------|--------------------------------------------------|
| `completion`   | Code completion example (instruction + code)     |
| `comprehension`| Code understanding (input code + explanation)    |
| `migration`    | Converting between generations                   |
| `explanation`  | Concept explanation with code examples           |

#### Generation Values

| Value       | Description                                       |
|-------------|---------------------------------------------------|
| `all`       | Universal pattern (works across all generations) |
| `character` | Character-based terminal UI (legacy)              |
| `vpro5`     | Visual PRO/5 (Windows GUI, legacy)                |
| `bbj-gui`   | BBj native GUI (Java-based)                       |
| `dwc`       | Dynamic Web Client (browser-based)                |

Use a single string for universal patterns or single-generation code:

```yaml
generation: all
generation: dwc
```

Use an array for code that works in multiple (but not all) generations:

```yaml
generation: ["bbj-gui", "dwc"]
```

### Optional Fields

| Field             | Type            | Description                           |
|-------------------|-----------------|---------------------------------------|
| `difficulty`      | enum            | `basic`, `intermediate`, or `advanced`|
| `tags`            | array of string | Topic keywords for organization       |
| `description`     | string          | One-sentence description              |
| `requires_version`| string          | Minimum BBj version, e.g., `"23.04"`  |
| `from_generation` | string          | Source generation (migration only)    |
| `to_generation`   | string or array | Target generation(s) (migration only) |

## Content Sections

Structure your content following the "code first, explanation after" principle.

### Code Section

Always use the `bbj` language fence for syntax highlighting:

````markdown
## Code

```bbj
REM Description of what this code does
sysgui! = BBjAPI().getSysGui()
window! = sysgui!.addWindow(100, 100, 400, 300, "Hello")
```
````

Start code with a `REM` comment describing the purpose.

### Expected Behavior / Expected Output

Use "Expected Behavior" for GUI or interactive programs:

```markdown
## Expected Behavior

A 400x300 pixel window appears at screen position (100,100) with the title "Hello". The window remains open until the user closes it.
```

Use "Expected Output" for console or data-processing programs:

```markdown
## Expected Output

```
Customer: Acme Corp
Balance: 1250.00
```
```

### Explanation Section

Provide a step-by-step breakdown:

```markdown
## Explanation

1. **Get GUI manager**: `BBjAPI().getSysGui()` returns the system GUI interface
2. **Create window**: `addWindow(x, y, width, height, title)` creates a top-level window
3. **Handle close**: `setCallback()` connects the close event to a label
```

## Multi-File Programs

For examples spanning multiple files, use multiple code blocks with filename comments:

````markdown
## Code

<!-- filename: main.bbj -->
```bbj
REM Main program
use Customer
cust! = new Customer()
print cust!.getName()
```

<!-- filename: Customer.bbj -->
```bbj
REM Customer class definition
class public Customer
    field private BBjString name!

    method public BBjString getName()
        methodret #name!
    methodend
classend
```
````

## BBj Code Conventions

1. **Always use `bbj` fence** for code blocks (not `basic` or plain)
2. **Start with REM comment** describing the code's purpose
3. **Include error handling** where appropriate
4. **Show complete runnable examples** when possible
5. **Use meaningful variable names** (`window!` not `w!`)

## Example Templates

### Completion Example

```markdown
---
title: "Creating a Button with Callback"
type: completion
generation: ["bbj-gui", "dwc"]
difficulty: basic
tags: [gui, button, callback, events]
description: "Shows how to create a button and handle click events"
---

## Code

```bbj
REM Create button with click handler
sysgui! = BBjAPI().getSysGui()
window! = sysgui!.addWindow(100, 100, 400, 300, "Button Demo")
button! = window!.addButton(1, 50, 50, 100, 30, "Click Me")
button!.setCallback(button!.ON_BUTTON_PUSH, "onButtonClick")
window!.setCallback(window!.ON_CLOSE, "onClose")

process_events

onButtonClick:
    i = msgbox("Button clicked!")
    return

onClose:
    release
```

## Expected Behavior

A window appears with a "Click Me" button. Clicking the button shows a message box. Closing the window exits the program.

## Explanation

1. **Get GUI manager**: `BBjAPI().getSysGui()` provides access to the GUI system
2. **Create window**: The window hosts all controls
3. **Add button**: `addButton(id, x, y, width, height, text)` creates a button control
4. **Set callbacks**: Event handlers are registered via `setCallback()`
5. **Event loop**: `process_events` starts the BBj event processing
```

### Migration Example

```markdown
---
title: "Migrating INPUT to BBjInputE"
type: migration
generation: dwc
from_generation: character
to_generation: ["bbj-gui", "dwc"]
difficulty: intermediate
tags: [migration, input, controls]
description: "Convert legacy INPUT statement to GUI input control"
---

## Code

### Before (Character Mode)

```bbj
REM Legacy character mode input
INPUT "Enter name: ", name$
PRINT "Hello, "; name$
```

### After (BBj GUI/DWC)

```bbj
REM Modern GUI input
sysgui! = BBjAPI().getSysGui()
window! = sysgui!.addWindow(100, 100, 400, 200, "Input Demo")
window!.addStaticText(1, 20, 20, 100, 25, "Enter name:")
input! = window!.addInputE(2, 120, 20, 200, 25, "")
button! = window!.addButton(3, 120, 60, 100, 30, "Submit")
button!.setCallback(button!.ON_BUTTON_PUSH, "onSubmit")
window!.setCallback(window!.ON_CLOSE, "onClose")

process_events

onSubmit:
    name$ = input!.getText()
    i = msgbox("Hello, " + name$)
    return

onClose:
    release
```

## Expected Behavior

The character mode version prompts in the terminal. The GUI version shows a window with a text field and button. Both achieve the same result: greeting the user by name.

## Explanation

1. **Terminal to window**: Replace terminal I/O with a window container
2. **Label for prompt**: Static text replaces the INPUT prompt string
3. **Input control**: BBjInputE provides text entry with validation options
4. **Button for action**: Explicit submit button replaces Enter key
5. **Event handling**: Callback pattern replaces sequential execution
```
