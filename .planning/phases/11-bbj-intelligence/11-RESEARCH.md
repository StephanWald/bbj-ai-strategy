# Phase 11: BBj Intelligence - Research

**Researched:** 2026-01-31
**Domain:** Rule-based document classification, generation tagging, contextual header generation for BBj documentation
**Confidence:** HIGH

## Summary

This phase adds the BBj-specific intelligence layer that transforms raw parsed documents into richly-tagged, context-aware chunks. Three components must be built: (1) a generation tagger that classifies each document/chunk by BBj product generation using multiple signal types, (2) a document type classifier that categorizes content by its structural purpose, and (3) a contextual header generator that prepends hierarchy-derived breadcrumbs to each chunk for improved retrieval.

The actual Flare content at `/Users/beff/bbjdocs/` was analyzed thoroughly. Key findings: 7,083 topic files across ~40 top-level directories; 5,990 files tagged `Primary.BASISHelp` (84.6%); only 290 files have no condition tag at all; the existing condition-to-generation mapping defaults everything to `["bbj"]` which is not granular enough. File paths, heading structures, code block language hints, and in-content syntax patterns all provide strong signals for both generation tagging and document type classification. The API reference content in `bbjobjects/` is remarkably consistent (93.7% have Description+Syntax headings), making structural classification highly reliable.

No external libraries are needed -- this is pure Python rule-based classification using the existing data model and parser infrastructure. The standard approach is a signal-scoring architecture where multiple signal sources (condition tags, file paths, heading patterns, content patterns, code block analysis) each vote on classification, with a deterministic resolution strategy.

**Primary recommendation:** Implement generation tagging and document type classification as pure Python modules using StrEnum for type safety, a signal-based scoring pattern for multi-signal classification, and the existing TOC breadcrumbs plus heading structure for contextual headers. Modify the Document/Chunk models to add `context_header` and `deprecated` fields.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `enum.StrEnum` | 3.11+ | Type-safe generation and doc_type enums | Built-in, serializes to string automatically, supports `auto()` for lowercase names |
| Python stdlib `re` | 3.12 | Regex pattern matching for content signals | Standard for text pattern matching; no need for external regex engines |
| Python stdlib `dataclasses` | 3.12 | Signal result containers | Lightweight frozen dataclasses for immutable signal results, consistent with existing ConditionTag pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lxml | >=5.3,<6 | XML tree access (already installed) | Accessing heading structures in parsed XHTML for contextual headers |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| StrEnum | Plain string constants | StrEnum gives type safety, auto-completion, and validation at the boundary; free since Python 3.11 |
| Signal-scoring pattern | ML-based classifier | ML would be overkill for 7K docs with clear structural patterns; rule-based is transparent, debuggable, and deterministic |
| Dataclass signal containers | Pydantic models | Dataclasses are lighter for internal data; Pydantic reserved for boundary validation (Document/Chunk models) |

**Installation:**
```bash
# No new dependencies needed -- all standard library + existing lxml
```

## Architecture Patterns

### Recommended Project Structure
```
src/bbj_rag/
├── models.py              # Add context_header, deprecated fields to Document/Chunk
├── intelligence/
│   ├── __init__.py        # Public API: tag_generation(), classify_doc_type(), build_context_header()
│   ├── generations.py     # Generation StrEnum + multi-signal tagger
│   ├── doc_types.py       # DocType StrEnum + structural classifier
│   ├── context_headers.py # Contextual header builder from TOC + headings
│   └── report.py          # Summary report printer (counts by generation, type, flags)
├── parsers/
│   ├── flare.py           # Updated to call intelligence layer after parsing
│   ├── flare_cond.py      # Existing (unchanged, signals consumed by intelligence layer)
│   ├── flare_toc.py       # Existing (unchanged, breadcrumbs consumed by context_headers)
│   └── web_crawl.py       # Updated to call intelligence layer after parsing
```

### Pattern 1: StrEnum for Type-Safe Classification Labels

**What:** Define canonical generation and document type labels as StrEnum members. These serialize directly to their string value for database storage and JSON serialization, while providing type checking during development.

**When to use:** Everywhere generation labels or document type labels are produced or consumed.

**Example:**
```python
from enum import StrEnum, auto

class Generation(StrEnum):
    """Canonical BBj product generation labels."""
    ALL = auto()           # "all" - cross-generation content
    CHARACTER = auto()     # "character" - green-screen / terminal
    VPRO5 = auto()         # "vpro5" - Visual PRO/5
    BBJ_GUI = auto()       # "bbj_gui" - BBj GUI / Swing
    DWC = auto()           # "dwc" - Dynamic Web Client

class DocType(StrEnum):
    """Document type classification labels."""
    API_REFERENCE = "api-reference"
    CONCEPT = "concept"
    EXAMPLE = "example"
    MIGRATION = "migration"
    LANGUAGE_REFERENCE = "language-reference"
    BEST_PRACTICE = "best-practice"
    VERSION_NOTE = "version-note"
```

**Note on StrEnum auto():** `auto()` produces lowercase member names (e.g., `Generation.ALL` -> `"all"`, `Generation.BBJ_GUI` -> `"bbj_gui"`). For DocType, explicit string values are used to produce hyphenated names matching the spec (e.g., `"api-reference"`).

### Pattern 2: Signal-Based Scoring for Generation Tagging

**What:** Each signal source (condition tags, file path, heading patterns, code patterns, API name patterns) produces a set of candidate generations with confidence weights. A resolver combines all signals into the final generation list.

**When to use:** Generation tagging. This is the core pattern for the multi-signal classification requirement.

**Example:**
```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Signal:
    """A single generation tagging signal."""
    generation: Generation
    weight: float  # 0.0..1.0
    source: str    # e.g., "file_path", "condition_tag", "heading_pattern"

def resolve_signals(signals: list[Signal]) -> list[Generation]:
    """Combine weighted signals into final generation list.

    Strategy: union of all signals that exceed a confidence threshold,
    with condition_tag signals given highest authority.
    """
    # Aggregate weights per generation
    scores: dict[Generation, float] = {}
    for sig in signals:
        scores[sig.generation] = scores.get(sig.generation, 0.0) + sig.weight

    # Filter by threshold
    threshold = 0.3
    result = [g for g, score in scores.items() if score >= threshold]

    if not result:
        return []  # Flag as untagged
    return sorted(result)
```

### Pattern 3: Structural Rule Registry for Document Type Classification

**What:** Each document type has a set of structural rules (presence of specific headings, heading patterns, content patterns). Rules are defined declaratively and checked sequentially with the first high-confidence match winning.

**When to use:** Document type classification. Extensible -- adding a new type means adding a new rule set.

**Example:**
```python
@dataclass(frozen=True)
class DocTypeRule:
    """A single classification rule for a document type."""
    doc_type: DocType
    required_headings: frozenset[str] = frozenset()  # Must be present
    optional_headings: frozenset[str] = frozenset()   # Boost confidence
    path_patterns: tuple[str, ...] = ()               # File path regex patterns
    content_patterns: tuple[str, ...] = ()            # Content regex patterns
    min_score: float = 0.5                            # Threshold to classify

# API Reference rule: high confidence from heading structure
API_REFERENCE_RULE = DocTypeRule(
    doc_type=DocType.API_REFERENCE,
    required_headings=frozenset({"Description", "Syntax"}),
    optional_headings=frozenset({"Parameters", "Return Value", "Example", "Remarks"}),
    path_patterns=(r"bbjobjects/", r"bbjinterfaces/", r"bbjevents/", r"API/"),
)
```

### Pattern 4: Contextual Header from TOC + Heading Structure

**What:** Combine the TOC-derived breadcrumb (already available from `flare_toc.build_toc_index`) with the within-page heading hierarchy to produce a full context path. For web crawl pages, URL path segments provide the breadcrumb.

**When to use:** Every chunk produced by any parser.

**Example:**
```python
def build_context_header(
    section_path: str,     # TOC breadcrumb: "Language > BBjAPI > BBjWindow"
    title: str,            # Page title: "BBjWindow::addButton"
    heading_path: str = "" # Within-page: "Parameters" (from chunker later)
) -> str:
    """Build arrow-separated contextual header for a chunk."""
    parts = [p for p in [section_path, title, heading_path] if p]
    return " > ".join(parts)
# Result: "Language > BBjAPI > BBjWindow > BBjWindow::addButton > Parameters"
```

### Anti-Patterns to Avoid
- **Giant if/elif chains for classification:** Use data-driven rule definitions, not procedural code. Each new document type should be a new rule declaration, not a new branch.
- **Baking context headers into content:** Store as a separate field (`context_header`). The content hash must remain stable regardless of header changes. Concatenation happens at embedding time, not storage time.
- **Defaulting unresolvable content to "all":** Per CONTEXT.md decision, flag as untagged (empty list) rather than defaulting. This surfaces tagger gaps rather than hiding them.
- **Treating condition tags as sole generation signal:** Only 5,990 of 7,083 files have `Primary.BASISHelp` condition, and this maps to a single undifferentiated generation. File paths and content patterns are far more discriminating.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| String enum with serialization | Custom string constants dict | `enum.StrEnum` (stdlib 3.11+) | Auto-serializes, type-safe, works with match/case |
| Breadcrumb paths from TOC | New TOC parser | Existing `flare_toc.build_toc_index()` | Already returns arrow-separated breadcrumbs, handles LinkedTitle resolution |
| Condition tag extraction | New condition parser | Existing `flare_cond.extract_topic_conditions()` + `map_conditions_to_generations()` | Already parses MadCap:conditions attribute, handles whitespace |
| Deprecated/Superseded detection | Custom parser | Check for `Primary.Deprecated`/`Primary.Superseded` in existing condition list | Already extracted by flare_cond module |

**Key insight:** Phase 10 already built the signal extraction infrastructure (TOC breadcrumbs, condition tags, heading structures). Phase 11 adds the classification logic that consumes those signals -- it should not re-parse XML or re-extract raw data.

## Common Pitfalls

### Pitfall 1: Condition Tag Blindness
**What goes wrong:** Relying solely on `MadCap:conditions` for generation tagging results in nearly everything being tagged the same way. 84.6% of files have `Primary.BASISHelp` which currently maps to `["bbj"]` -- a single undifferentiated bucket.
**Why it happens:** Condition tags were designed for Flare build filtering (which help targets to include/exclude), not for semantic generation classification.
**How to avoid:** Treat condition tags as just one signal among five (condition, file path, heading/title, code patterns, API name patterns). File paths like `bbjobjects/`, `dwc/`, `mnemonic/terminal/` are far more discriminating than condition tags.
**Warning signs:** If >80% of content is tagged with the same generation, the tagger is not using enough signal sources.

### Pitfall 2: Overly Broad "all" Classification
**What goes wrong:** Content that genuinely belongs to a specific generation gets tagged "all" because the tagger defaults to "all" when signals are ambiguous.
**Why it happens:** Conservative fallback behavior. The `commands/` directory has 385 files that look cross-generation, but 86 of them are in `commands/bbj-commands/` and should be tagged bbj-gui/all, not just "all".
**How to avoid:** Per CONTEXT.md decision, flag as untagged when signals are insufficient rather than defaulting to "all". Use the "all" label intentionally for content that is explicitly cross-generation (like language syntax that works in all modes).
**Warning signs:** >50% tagged "all" means signal extraction is too weak.

### Pitfall 3: Mutating Content Hash by Baking in Context Headers
**What goes wrong:** If context headers are prepended directly to `content`, the `content_hash` changes every time the TOC structure changes, breaking deduplication.
**Why it happens:** Natural instinct is to store the "complete" chunk as a single string.
**How to avoid:** Store `context_header` as a separate field. Compute content_hash from `content` only. At embedding time, concatenate `context_header + "\n\n" + content` for the vector.
**Warning signs:** Re-running ingestion produces duplicate chunks with different hashes.

### Pitfall 4: Breaking the Document Model Validator
**What goes wrong:** The existing `Document.generations` validator requires at least one entry (`generations_must_not_be_empty`). Changing the default from `["bbj"]` to empty list for "untagged" would break validation.
**Why it happens:** Phase 10 made a valid assumption that every document has at least one generation.
**How to avoid:** Either (a) keep the validator but use a sentinel value like `["untagged"]` for unresolvable documents, or (b) relax the validator to allow empty lists and use a separate `is_tagged` property. Recommendation: use `["untagged"]` sentinel to avoid cascading model changes.
**Warning signs:** Validation errors when running tagger on real content.

### Pitfall 5: Heading Extraction Race Condition
**What goes wrong:** The contextual header builder needs heading structure from the parsed document, but the parser currently extracts content as flat text (headings are converted to `# Heading` markdown strings during parsing). The heading hierarchy is lost.
**Why it happens:** Phase 10's parser converts headings to markdown inline. The original XML heading hierarchy is not preserved as structured metadata.
**How to avoid:** Either (a) extract heading hierarchy before content flattening (during XML parsing, before `_walk_element`), or (b) reconstruct heading hierarchy from the markdown output using regex on `# `, `## `, etc. patterns. Recommendation: extract heading hierarchy from XML during parsing as a separate metadata field, since the XML tree is available at that point.
**Warning signs:** Context headers only contain the TOC breadcrumb but not the within-page heading path.

## Code Examples

Verified patterns from the actual Flare content analysis:

### Generation Tagging: File Path Signal
```python
# Source: Analysis of /Users/beff/bbjdocs/Content/ directory structure
# 7,083 topic files analyzed across 40+ directories

_PATH_GENERATION_MAP: dict[str, set[Generation]] = {
    # BBj GUI (Swing) -- largest category: ~3,800 files
    "bbjobjects/": {Generation.BBJ_GUI},
    "bbjevents/": {Generation.BBJ_GUI},
    "bbjinterfaces/": {Generation.BBJ_GUI},
    "gridmethods/": {Generation.BBJ_GUI},
    "gridctrl/": {Generation.BBJ_GUI},
    "bui/": {Generation.BBJ_GUI},  # BUI is GUI-era deployment
    "appbuildingblocks/": {Generation.BBJ_GUI},
    "mnemonic/sysgui/": {Generation.BBJ_GUI},

    # DWC-specific
    "dwc/": {Generation.DWC},

    # Character/terminal
    "mnemonic/terminal/": {Generation.CHARACTER},

    # Visual PRO/5
    "guibuild/": {Generation.VPRO5},
    "formbuilder/": {Generation.VPRO5},
    "resbuild/": {Generation.VPRO5},
    "rescomp/": {Generation.VPRO5},
    "resprops/": {Generation.VPRO5},

    # Cross-generation ("all")
    "commands/": {Generation.ALL},
    "events/": {Generation.ALL},
    "sendmsg/": {Generation.ALL},
    "sysadmin/": {Generation.ALL},
    "config/": {Generation.ALL},
    "usr/": {Generation.ALL},
    "dataserv/": {Generation.ALL},
    "b3odbc/": {Generation.ALL},

    # BBj-specific commands (override parent commands/ = all)
    "commands/bbj-commands/": {Generation.BBJ_GUI},
    "commands/bbj-variables/": {Generation.BBJ_GUI},
}

def signal_from_path(content_relative_path: str) -> list[Signal]:
    """Extract generation signals from a file's Content-relative path.

    Longer (more specific) path prefixes take priority.
    """
    signals = []
    # Sort by key length descending so more specific paths match first
    for prefix, gens in sorted(_PATH_GENERATION_MAP.items(), key=lambda x: -len(x[0])):
        if content_relative_path.startswith(prefix):
            for gen in gens:
                signals.append(Signal(generation=gen, weight=0.6, source="file_path"))
            break  # First (most specific) match wins
    return signals
```

### Generation Tagging: Content Pattern Signal
```python
import re

# Source: Analysis of 7,083 BBj topics for generation-specific patterns
# Occurrence counts from actual content scan:
#   PROCESS_EVENTS: 1,899 files
#   BBjAPI(): 1,692 files
#   BBjWindow: 1,676 files
#   REM statement: 1,694 files (but common across all generations)
#   PRO/5: 817 files
#   VPRO5: 334 files
#   DWC: 258 files
#   BUI: 333 files
#   character_terminal: 312 files

_CONTENT_GENERATION_PATTERNS: dict[Generation, list[re.Pattern[str]]] = {
    Generation.BBJ_GUI: [
        re.compile(r"PROCESS_EVENTS", re.IGNORECASE),
        re.compile(r"BBjAPI\(\)"),
        re.compile(r"BBjSysGui"),
        re.compile(r"SysGUI", re.IGNORECASE),
    ],
    Generation.DWC: [
        re.compile(r"Dynamic Web Client"),
        re.compile(r"\bDWC\b"),
        re.compile(r"BBjWebComponent"),
        re.compile(r"web\s*component", re.IGNORECASE),
    ],
    Generation.CHARACTER: [
        re.compile(r"character\s*mode", re.IGNORECASE),
        re.compile(r"green.screen", re.IGNORECASE),
        re.compile(r"terminal\s*emulat", re.IGNORECASE),
    ],
    Generation.VPRO5: [
        re.compile(r"Visual\s*PRO/5", re.IGNORECASE),
        re.compile(r"\bVPRO/?5\b", re.IGNORECASE),
        re.compile(r"GUI\s*Builder", re.IGNORECASE),
        re.compile(r"Resource\s*Compiler", re.IGNORECASE),
    ],
}
```

### Document Type Classification: Heading-Based Rules
```python
# Source: Analysis of h2 heading patterns across actual content
# bbjobjects (2,570 files): 93.7% have Description+Syntax headings
# commands (385 files): 82.6% have Syntax heading

# Strong signals for each document type:
_API_REF_HEADINGS = {"Description", "Syntax", "Parameters", "Return Value", "Remarks"}
_LANG_REF_HEADINGS = {"Syntax", "Examples", "Description"}  # Without Parameters/Return Value
_MIGRATION_HEADINGS = {"BBj-Specific Information", "Converting", "Migration"}
_VERSION_NOTE_HEADINGS = {"Version History", "What's New", "Release Notes"}

def classify_doc_type_by_headings(headings: list[str]) -> tuple[DocType, float]:
    """Classify document type by heading structure.

    Returns (doc_type, confidence) where confidence is 0.0..1.0.
    """
    heading_set = {h.strip() for h in headings}

    # API Reference: strongest signal is Description + Syntax + Parameters/Return Value
    api_hits = heading_set & _API_REF_HEADINGS
    if "Description" in heading_set and "Syntax" in heading_set:
        if "Parameters" in heading_set or "Return Value" in heading_set:
            return (DocType.API_REFERENCE, 0.95)
        return (DocType.API_REFERENCE, 0.7)

    # Version notes
    if heading_set & _VERSION_NOTE_HEADINGS:
        return (DocType.VERSION_NOTE, 0.8)

    # Migration content
    if heading_set & _MIGRATION_HEADINGS:
        return (DocType.MIGRATION, 0.8)

    # Language reference: Syntax without API-style headings
    if "Syntax" in heading_set and "Parameters" not in heading_set:
        return (DocType.LANGUAGE_REFERENCE, 0.6)

    # Default to concept
    return (DocType.CONCEPT, 0.3)
```

### Contextual Header Generation
```python
# Source: flare_toc.build_toc_index() produces breadcrumbs like:
#   "Language > BBjAPI > BBjSysGui > BBjWindow > BBjControl > BBjGroupBox"
# TOC covers 1,595 of 7,083 topics (22.5%)
# Orphan topics use directory_fallback_path(): "bbjobjects > Window > bbjwindow"

def build_context_header(
    section_path: str,
    title: str,
    heading_path: str = "",
) -> str:
    """Build contextual header for a chunk.

    Args:
        section_path: TOC breadcrumb or directory-based fallback.
        title: Page title (e.g., "BBjWindow::addButton").
        heading_path: Within-page heading context (populated during chunking).

    Returns:
        Arrow-separated context string, e.g.:
        "Language > BBjAPI > BBjWindow > BBjWindow::addButton"
    """
    parts = []
    if section_path:
        parts.append(section_path)
    if title and title not in section_path:
        parts.append(title)
    if heading_path:
        parts.append(heading_path)
    return " > ".join(parts)
```

### Summary Report
```python
# The report should print after tagging a batch, e.g.:
#
# === BBj Intelligence Report ===
# Documents processed: 7,083
#
# Generation distribution:
#   bbj_gui:    3,842  (54.2%)
#   all:        1,523  (21.5%)
#   vpro5:        493  (7.0%)
#   character:    312  (4.4%)
#   dwc:          258  (3.6%)
#   untagged:     655  (9.2%)
#
# Document type distribution:
#   api-reference:       2,570  (36.3%)
#   language-reference:    385  (5.4%)
#   concept:             3,200  (45.2%)
#   ...
#
# Deprecated: 114  |  Superseded: 44
# Untagged (no generation resolved): 655
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `["bbj"]` default for all docs (Phase 10) | Multi-signal generation tagging with 5 canonical labels | Phase 11 | Content now distinguishable by generation for filtered retrieval |
| `doc_type="flare"` / `doc_type="web_crawl"` (Phase 10) | Semantic document type classification (7 types) | Phase 11 | Enables type-filtered search (e.g., "show me only API references") |
| No context beyond title | Contextual header breadcrumb from TOC + headings | Phase 11 | Embedding includes hierarchy context, improving retrieval relevance |

**Superseded decisions from Phase 10:**
- `map_conditions_to_generations()` currently defaults to `["bbj"]` -- this will be replaced by the multi-signal tagger output
- `GENERATION_RELEVANT_CONDITIONS` mapping will need updating: `Primary.BASISHelp` should no longer map to `"bbj"` directly; instead it means "included in BASISHelp build" which is informational but not a generation signal
- `doc_type` field on Document currently stores source type ("flare", "web_crawl"); this should be repurposed for semantic type

## Open Questions

Things that couldn't be fully resolved:

1. **Within-page heading hierarchy for chunking context**
   - What we know: The Flare parser converts headings to markdown strings during content extraction. The XML heading hierarchy is available at parse time but not preserved as structured metadata.
   - What's unclear: Should heading hierarchy be extracted during parsing (Phase 11, touching parser code) or reconstructed from markdown output later (Phase 12, during chunking)?
   - Recommendation: Extract during parsing in Phase 11. The XML tree has perfect heading structure; reconstructing from markdown is lossy (markdown headings lose nesting context when flattened). Store as `heading_hierarchy: list[tuple[int, str]]` in document metadata (list of (level, text) pairs).

2. **Web crawl generation tagging**
   - What we know: Web crawl documents get `generations=["bbj"]` currently. URL path segments provide some signal (e.g., `bbjobjects/`, `dwc/`) but the published site may reorganize URLs.
   - What's unclear: How reliable are URL paths as generation signals for the web crawl path?
   - Recommendation: Apply the same path-based signal logic to URL path segments (after stripping the base URL prefix). The published site mirrors the Flare Content directory structure closely.

3. **"untagged" sentinel vs. empty list for generations**
   - What we know: The Document model validates that `generations` is non-empty. CONTEXT.md says "flag as untagged (empty/unknown) rather than defaulting."
   - What's unclear: Whether to relax the validator or use a sentinel.
   - Recommendation: Use `["untagged"]` as a sentinel value (preserves backward compatibility with the validator). This is more explicit than an empty list and easier to query (`WHERE 'untagged' = ANY(generations)`).

4. **Exact weight tuning for signal scoring**
   - What we know: The relative authority of signals should be condition_tag > file_path > content_pattern > heading_pattern.
   - What's unclear: Exact weight values require iteration against real data.
   - Recommendation: Start with condition_tag=0.8, file_path=0.6, content_pattern=0.4, heading_pattern=0.3. Run against full corpus, check distribution report, and adjust. The success criterion is <50% tagged "all".

## Sources

### Primary (HIGH confidence)
- `/Users/beff/bbjdocs/` - Direct analysis of 7,083 Flare topic files for content patterns, heading structures, condition tags, file path distribution, and code block language hints
- `/Users/beff/_workspace/bbj-ai-strategy/rag-ingestion/src/bbj_rag/` - Existing codebase: models.py, parsers/flare.py, parsers/flare_cond.py, parsers/flare_toc.py, parsers/web_crawl.py, db.py, schema.py
- Python 3.12 stdlib documentation for `enum.StrEnum`, `dataclasses`, `re`

### Secondary (MEDIUM confidence)
- [Python Enum documentation](https://docs.python.org/3/library/enum.html) - StrEnum behavior with auto(), serialization
- [Dataclasses documentation](https://docs.python.org/3/library/dataclasses.html) - frozen=True, slots=True for signal containers
- Registry/Strategy pattern analysis from [Python Patterns - Registry](https://charlesreid1.github.io/python-patterns-the-registry.html) and community sources

### Tertiary (LOW confidence)
- None -- all findings verified against actual codebase and content analysis

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Pure Python stdlib, no new dependencies, verified against existing project setup
- Architecture: HIGH - Signal-scoring pattern derived from actual content analysis; heading consistency measured at 93.7% for API reference; file path mappings derived from complete directory listing
- Pitfalls: HIGH - Each pitfall identified from direct analysis of existing code and data (e.g., condition tag distribution measured, content_hash behavior verified in models.py, heading extraction confirmed from parser source)

**Research date:** 2026-01-31
**Valid until:** 2026-03-31 (stable -- no external dependencies to go stale; data patterns from Flare content are structural)

---

## Appendix: Actual Content Analysis Data

### Condition Tag Distribution (root `<html>` element)
| Condition | Count | % of 7,083 |
|-----------|-------|------------|
| Primary.BASISHelp | 5,990 | 84.6% |
| Primary.resbuild_chm | 324 | 4.6% |
| NO CONDITION | 290 | 4.1% |
| Primary.ddbuild_chm | 170 | 2.4% |
| Primary.guibuild_chm | 119 | 1.7% |
| Primary.Deprecated | 114 | 1.6% |
| Primary.config_chm | 50 | 0.7% |
| Primary.Superseded | 44 | 0.6% |
| Primary.Navigation | 29 | 0.4% |
| Primary.NotImplemented | 13 | 0.2% |
| Primary.EMHelp | 5 | 0.1% |
| Primary.BDTHelp | 1 | <0.1% |

### File Count by Top-Level Content Directory
| Directory | Files | Likely Generation |
|-----------|-------|-------------------|
| bbjobjects | 2,570 | bbj-gui |
| bbjevents | 472 | bbj-gui |
| gridmethods | 466 | bbj-gui |
| commands | 385 | all (86 bbj-specific) |
| mnemonic | 347 | mixed (95 terminal, 121 sysgui) |
| usr | 328 | all/mixed |
| sendmsg | 217 | all |
| bbutil | 184 | all |
| b3odbc | 179 | all |
| ddbuild | 170 | vpro5-era tools |
| resbuild | 167 | vpro5 |
| events | 167 | all |
| bbjinterfaces | 156 | bbj-gui |
| guibuild | 119 | vpro5 |
| sysadmin | 118 | all |
| resprops | 117 | vpro5 |
| eus | 114 | all |
| util | 108 | all |
| gridctrl | 90 | bbj-gui |
| bui | 77 | bbj-gui |
| formbuilder | 67 | vpro5 |
| dwc | 4 | dwc |

### API Reference Heading Consistency (bbjobjects/)
- 93.7% of 2,570 files have both `Description` and `Syntax` h2 headings
- Top h2 headings: See Also (2,557), Description (2,556), Parameters (2,416), Syntax (2,414), Example (2,410), Return Value (2,393), Remarks (2,124), Version History (260)

### TOC Coverage
- 1,595 topics in TOC (22.5% of 7,083)
- Breadcrumb depth distribution: 1-level (13), 2-level (37), 3-level (316), 4-level (585), 5-level (452), 6-level (185), 7-level (7)
- 77.5% of topics are orphans (not in any TOC) and use directory-based fallback paths

### Code Block Languages
- `language-bbj`: 2,948 occurrences (dominant)
- `language-css`: 42
- `language-bbjconsole`: 29
- `language-xml`: 17
- Others: java (6), sql (2), html (1), json (1), bbjconfig (2), bbjarc (1)
