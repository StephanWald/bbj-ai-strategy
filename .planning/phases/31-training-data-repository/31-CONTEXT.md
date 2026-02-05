# Phase 31: Training Data Repository - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Infrastructure for systematically collecting and validating curated BBj code examples. Repository structure, format specification, and seed examples. Conversion to JSONL for fine-tuning is a future phase.

</domain>

<decisions>
## Implementation Decisions

### Example Format
- Front matter: Standard metadata (title, tags, difficulty, description)
- Structure: Code first, then explanation after
- Types: Both code snippets (10-50 lines) and complete runnable programs
- Output: Include expected output/behavior when relevant to the example

### Directory Organization
- Top-level: Organized by topic (gui/, database/, file-io/, strings/, etc.)
- Depth: Flat within topics (no nested subtopics)

### Claude's Discretion
- Repository location (in bbj-ai-strategy vs separate repo)
- File naming convention (descriptive slugs vs numbered)
- Validation approach and tooling
- Contributor workflow and templates

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for documentation repositories.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 31-training-data-repository*
*Context gathered: 2026-02-05*
