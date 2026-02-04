# Phase 28: Compiler Validation - Context

**Gathered:** 2026-02-04
**Status:** Ready for planning

<domain>
## Phase Boundary

BBj code in chat responses is automatically validated against the real BBj compiler (bbjcpl), giving engineers confidence that code examples are syntactically correct. Validation happens before code is shown to users, with automatic retry/fix attempts. This phase focuses on the validation loop and error presentation — not on improving Claude's code generation quality.

</domain>

<decisions>
## Implementation Decisions

### Validation flow
- Validation is a **pre-output filter**, not a post-render indicator
- Invalid code triggers automatic fix attempts — Claude sees the error, attempts correction, re-validates
- Up to **3 attempts** (original + 2 fixes) before showing code with warning
- On success after retries: **silent success** — user sees working code with no indication of iteration

### Visual feedback
- When code passes: no visual indicator (clean output)
- When code fails after all retries: warning banner **above** the code block
- Warning text: "⚠️ Could not verify syntax — use with caution" (or similar)
- Warning is **always visible** (not dismissible)

### Error presentation
- Warning includes **full bbjcpl stderr output** (all errors, not just first)
- Error displayed alongside the warning banner above the code block
- No summarization — show raw compiler output for technical users

### Validation scope
- Validate fenced code blocks only (```), **not inline code** (single backticks)
- **Auto-detect** BBj code in unmarked/generic code blocks
- Validate **all code blocks** regardless of whether they're complete programs or fragments
- Multiple code blocks in one response: validate **each independently**

### Failure behavior
- bbjcpl unavailable: show code with note "Syntax validation unavailable"
- bbjcpl timeout: show code with note "Validation timed out"
- Timeout threshold: **10 seconds**
- Ambiguous code (could be BBj or not): **try validation** — if it fails, treat as non-BBj and show without warning

### Claude's Discretion
- Exact wording of warning messages
- How to detect BBj code in unmarked blocks
- Fix attempt strategy (what Claude tries when correcting errors)
- Temp file handling for bbjcpl invocation

</decisions>

<specifics>
## Specific Ideas

- The goal is that users **never see invalid BBj code** in chat responses (unless validation itself fails)
- Validation should be invisible when it works — no success badges or indicators
- Engineers can trust that if code is shown without warning, it compiled

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 28-compiler-validation*
*Context gathered: 2026-02-04*
