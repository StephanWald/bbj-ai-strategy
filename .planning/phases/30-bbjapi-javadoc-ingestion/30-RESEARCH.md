# Phase 30: BBjAPI JavaDoc Ingestion - Research

**Researched:** 2026-02-05
**Domain:** JSON parsing, HTML-to-Markdown conversion, RAG document chunking
**Confidence:** HIGH

## Summary

This phase adds a new parser to ingest BBj API documentation from structured JSON files located in `$BBJ_HOME/documentation/javadoc/`. The JSON files contain 359 classes with 4,438 methods across 7 package files. The parser will produce "class reference card" chunks that provide API structure at a glance.

The existing codebase provides a clear pattern for adding new parsers: implement the `DocumentParser` protocol (a single `parse()` method yielding `Document` objects), add the parser type to `source_config.py`, and register it in `ingest_all.py`'s factory function. The project already has utilities for HTML-to-Markdown conversion (`_html_to_markdown` in `web_crawl.py`) and BeautifulSoup for parsing HTML fragments embedded in documentation strings.

**Primary recommendation:** Create a new `javadoc.py` parser following the `BbjSourceParser` pattern, using BeautifulSoup for HTML-to-Markdown conversion of `docu` fields, and producing one Document per class with all methods listed.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| stdlib `json` | 3.12 | Parse JSON files | Standard library, no dependencies |
| `beautifulsoup4` | >=4.13 | HTML fragment parsing | Already in project dependencies |
| `pydantic` | >=2.12 | Document model validation | Project standard for data models |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `re` | stdlib | Regex for URL extraction | Extract `[Docs](https://...)` patterns |
| `pathlib` | stdlib | Path handling | Consistent with project style |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| BeautifulSoup | lxml directly | BS4 simpler for fragments, already imported elsewhere |
| Custom HTML parser | markdownify library | Project already has `_html_to_markdown`, no new dep |

**Installation:**
No new dependencies required. All needed libraries already in `pyproject.toml`.

## Architecture Patterns

### Recommended Project Structure
```
rag-ingestion/src/bbj_rag/
├── parsers/
│   ├── javadoc.py        # NEW: JavaDoc JSON parser
│   └── ...
├── source_config.py      # Add "javadoc" to _KNOWN_PARSERS
├── ingest_all.py         # Add parser factory case
└── url_mapping.py        # Add bbj_api:// prefix mapping
```

### Pattern 1: Parser Protocol Implementation
**What:** Single class implementing `DocumentParser` protocol with `parse()` generator
**When to use:** All documentation source parsers
**Example:**
```python
# Source: bbj_rag/parsers/__init__.py
@runtime_checkable
class DocumentParser(Protocol):
    def parse(self) -> Iterator[Document]:
        """Yield Document objects from the configured source."""
        ...
```

### Pattern 2: Lazy Parser Imports
**What:** Import parsers only when their source type is selected
**When to use:** In `_create_parser_for_source()` factory function
**Example:**
```python
# Source: bbj_rag/ingest_all.py lines 133-138
if parser_type == "bbj-source":
    from bbj_rag.parsers.bbj_source import BbjSourceParser
    return BbjSourceParser(
        source_dirs=[data_dir / p for p in source.paths],
    )
```

### Pattern 3: Environment Variable Path Configuration
**What:** Use env var for path that varies between installations
**When to use:** Paths that depend on BBj installation location
**Example:**
```python
# Pattern from existing BBJ_RAG_COMPILER_PATH
# New: BBJ_HOME env var, default derived path
import os
bbj_home = os.environ.get("BBJ_HOME", "/usr/local/bbj")
javadoc_path = Path(bbj_home) / "documentation" / "javadoc"
```

### Pattern 4: One Document Per Logical Unit
**What:** Create one Document per class, not per method or per file
**When to use:** API documentation where class is the navigable unit
**Rationale:** User query "what methods does BBjWindow have?" returns one chunk with complete method listing

### Anti-Patterns to Avoid
- **Splitting methods into separate chunks:** Loses class context, can't answer "what methods does X have?"
- **Including HTML tags in output:** Must convert to Markdown for consistent rendering
- **Skipping undocumented items:** Empty `docu` fields still have valuable signature info
- **Hard-coding paths:** Use env var for portability across installations

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML to Markdown | Custom converter | `_html_to_markdown` from `web_crawl.py` | Already handles tables, links, code blocks |
| URL extraction | Manual string parsing | Regex for `[Docs](url)` pattern | Reliable, handles edge cases |
| Document model | Custom dict | `Document` from `bbj_rag.models` | Pydantic validation, protocol compliance |
| Content hashing | Custom implementation | `Chunk.from_content()` factory | Auto-computes SHA-256 hash |

**Key insight:** The project has mature utilities for HTML-to-Markdown conversion. The web_crawl parser's `_html_to_markdown` function handles headings, paragraphs, code blocks, tables, and lists -- exactly what appears in JavaDoc HTML.

## Common Pitfalls

### Pitfall 1: HTML Entity Encoding in JSON
**What goes wrong:** JSON contains HTML entities like `&#160;` and encoded characters
**Why it happens:** JavaDoc HTML was embedded in JSON without normalization
**How to avoid:** Parse HTML through BeautifulSoup which handles entity decoding
**Warning signs:** `&#160;` or `&nbsp;` appearing in output

### Pitfall 2: Carriage Returns in Documentation
**What goes wrong:** Documentation contains `\r\n` and `\r\r` line endings
**Why it happens:** Windows-style line endings in original documentation
**How to avoid:** Normalize line endings: `text.replace('\r\n', '\n').replace('\r', '\n')`
**Warning signs:** Double blank lines or `^M` characters in output

### Pitfall 3: Missing Return Types in Signatures
**What goes wrong:** Method signatures lack return type info
**Why it happens:** JSON structure only has `name` and `params`, no return type
**How to avoid:** Accept this limitation; document signature format as `methodName(param1, param2)`
**Warning signs:** N/A - this is a data limitation, not a bug

### Pitfall 4: Overloaded Methods with Same Name
**What goes wrong:** Multiple methods with same name have different parameter counts
**Why it happens:** Java method overloading is common in BBjAPI
**How to avoid:** List each overload separately with full parameter list
**Warning signs:** Methods appearing to be duplicated in output

### Pitfall 5: Relative URLs in Documentation
**What goes wrong:** Some `href` values are relative paths like `../bbjwindow.htm`
**Why it happens:** JavaDoc cross-references use relative paths
**How to avoid:** Keep only the `[Docs](https://documentation.basis.cloud/...)` absolute links
**Warning signs:** Broken links in chunk content

## Code Examples

Verified patterns from the existing codebase:

### JSON Structure (from actual files)
```python
# Source: /Users/beff/bbx/documentation/javadoc/*.json
{
    "name": "com.basis.bbj.proxies.sysgui",
    "version": "com.basis.bbj.proxies.sysgui",
    "docu": "BBjAPI Class Hierarchy",
    "classes": [
        {
            "name": "BBjWindow",
            "docu": "A BBjWindow is an object...[Docs](https://...)",
            "fields": [],
            "constructors": [],
            "methods": [
                {
                    "name": "addButton",
                    "docu": "Adds a button...[Docs](https://...)",
                    "params": [{"name": "p_id"}, {"name": "p_x"}]
                }
            ]
        }
    ]
}
```

### Document Creation Pattern
```python
# Source: bbj_rag/parsers/bbj_source.py lines 178-191
yield Document(
    source_url=f"bbj_api://{class_name}",
    title=class_name,
    doc_type="api_reference",
    content=content,
    generations=["bbj_gui", "dwc"],  # BBjAPI is BBj-specific
    context_header=f"BBj API Reference > {class_name}",
    metadata={
        "source_type": "bbj_api",
        "package": package_name,
    },
    deprecated=False,
    source_type="bbj_api",
    display_url=class_doc_url,
)
```

### HTML to Markdown (Existing Implementation)
```python
# Source: bbj_rag/parsers/web_crawl.py lines 377-387
def _html_to_markdown(root: Tag) -> str:
    """Convert an HTML element tree to Markdown text."""
    parts: list[str] = []
    _walk(root, parts)
    text = "\n".join(parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
```

### Docs Link Extraction Pattern
```python
# Extract [Docs](url) from documentation string
import re
DOCS_LINK_RE = re.compile(r'\[Docs\]\((https://documentation\.basis\.cloud/[^)]+)\)')

def extract_display_url(docu: str) -> str:
    """Extract the documentation.basis.cloud URL from docu field."""
    match = DOCS_LINK_RE.search(docu)
    return match.group(1) if match else ""
```

### Class Reference Card Format
```markdown
# BBjWindow

A BBjWindow is an object that provides an interface to a GUI window.

**Package:** com.basis.bbj.proxies.sysgui
**Documentation:** https://documentation.basis.cloud/.../bbjwindow.htm

## Methods

- `addButton(p_id, p_x, p_y, p_width, p_height, p_text)` - Adds a button control
- `addButton(p_id, p_x, p_y, p_width, p_height, p_text, p_flags)` - Adds a button control
- `getControl(p_id)` - Returns the control with the specified ID
...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-method chunks | Per-class chunks | Phase 30 decision | Better API overview queries |
| Separate generations field | `bbj_gui,dwc` combined | Phase 30 decision | BBjAPI relevant to both |

**Deprecated/outdated:**
- N/A - This is a new feature, no legacy approaches

## Open Questions

Things that couldn't be fully resolved:

1. **Inheritance chain depth**
   - What we know: JSON does not contain inheritance info
   - What's unclear: Whether to derive it from class naming conventions
   - Recommendation: Skip inheritance for v1, document as future enhancement

2. **Package name metadata**
   - What we know: Package name is in the JSON filename and `name` field
   - What's unclear: Whether to add as separate metadata field
   - Recommendation: Add `package` to metadata dict for potential filtering

3. **Large class chunks**
   - What we know: BBjWindow has 100+ methods, chunk could be large
   - What's unclear: Whether to enforce max chunk size
   - Recommendation: Allow large chunks for API reference cards; semantic search doesn't require small chunks

## Data Statistics

From analysis of actual JSON files:

| Metric | Count |
|--------|-------|
| Total classes | 359 |
| Total methods | 4,438 |
| Classes without documentation | 39 (10.9%) |
| Methods without documentation | 883 (19.9%) |
| Methods with parameters | 2,429 (54.7%) |
| JSON files | 7 |
| Total file size | ~1.7 MB |

**File breakdown:**
- `com.basis.bbj.proxies.sysgui.json` - 97 classes (largest, GUI controls)
- `com.basis.bbj.proxies.json` - Core BBj API classes
- `com.basis.bbj.proxies.event.json` - Event classes
- `com.basis.bbj.proxies.servlet.json` - Servlet classes
- `com.basis.bbj.proxies.ldap.json` - LDAP classes (4 classes)
- `com.basis.util.json` - Utility classes
- `java.util.json` - Java utility proxies

## Sources

### Primary (HIGH confidence)
- `/Users/beff/_workspace/bbj-ai-strategy/rag-ingestion/src/bbj_rag/parsers/` - Existing parser implementations
- `/Users/beff/_workspace/bbj-ai-strategy/rag-ingestion/src/bbj_rag/models.py` - Document/Chunk models
- `/Users/beff/_workspace/bbj-ai-strategy/rag-ingestion/src/bbj_rag/ingest_all.py` - Parser factory pattern
- `/Users/beff/bbx/documentation/javadoc/*.json` - Actual source data

### Secondary (MEDIUM confidence)
- Project patterns extrapolated from multiple parser implementations

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project dependencies
- Architecture: HIGH - Clear patterns from existing 7 parsers
- Pitfalls: HIGH - Derived from actual data analysis
- Data format: HIGH - Analyzed actual JSON files

**Research date:** 2026-02-05
**Valid until:** 2026-03-05 (30 days - stable codebase)
