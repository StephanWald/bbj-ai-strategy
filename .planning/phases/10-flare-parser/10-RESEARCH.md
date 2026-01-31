# Phase 10: Flare Parser - Research

**Researched:** 2026-01-31
**Domain:** MadCap Flare XHTML parsing, XML processing, web crawling
**Confidence:** HIGH

## Summary

This phase builds three parsers that produce `Document` objects for the existing `rag-ingestion` pipeline: (1) a MadCap Flare XHTML parser reading raw project files from the local `Content/` directory, (2) a TOC/condition-tag extractor building hierarchy paths and extracting generation metadata, and (3) a web-crawl fallback parser for `documentation.basis.cloud`.

The Flare source at `/Users/beff/bbjdocs/` is a well-structured MadCap Flare project with 7,083 topic `.htm` files (55 MB of XHTML), 205 snippet `.flsnp` files, 4 TOC files (`.fltoc`), and 1 condition tag set (`Primary.flcts`). All topic files use a single consistent namespace (`xmlns:MadCap="http://www.madcapsoftware.com/Schemas/MadCap.xsd"`) and are valid XML (UTF-8, some with BOM). The standard approach is to use `lxml.etree` for XML parsing (not HTML parsing), walk the element tree to extract content while handling MadCap namespace tags per-type, and combine TOC-derived hierarchy with filesystem-based fallback paths for orphan topics.

**Primary recommendation:** Use `lxml.etree` as the XML parser (not BeautifulSoup), parse each topic file independently, resolve snippets by loading `.flsnp` files on demand, and build a `TocIndex` from all 4 `.fltoc` files for hierarchy resolution.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| lxml | >=5.3,<6 | XHTML/XML parsing | The only performant namespace-aware XML parser for Python; handles the MadCap namespace correctly; etree API is ideal for tree walking |
| httpx | >=0.28,<1 | HTTP client for web crawl fallback | Modern async-capable HTTP client; better than requests for crawling; already the direction for modern Python |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| beautifulsoup4 | >=4.13,<5 | HTML parsing for crawled pages | Web crawl fallback only -- crawled pages are rendered HTML (not XHTML), where BS4 shines |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| lxml.etree | BeautifulSoup with lxml-xml parser | BS4 adds abstraction overhead; for valid XML (which these files are), lxml.etree is faster and more direct |
| httpx | requests | requests works fine but httpx is more modern, supports async if needed later |
| httpx | crawl4ai | Decision already made: use HTTP requests + BeautifulSoup, not crawl4ai |

**Installation:**
```bash
uv add "lxml>=5.3,<6" "httpx>=0.28,<1" "beautifulsoup4>=4.13,<5"
```

## Architecture Patterns

### Recommended Project Structure
```
src/bbj_rag/
├── models.py           # Existing Document/Chunk models
├── config.py           # Existing Settings
├── parsers/
│   ├── __init__.py
│   ├── flare.py        # PARSE-01: XHTML topic parser + snippet resolution
│   ├── flare_toc.py    # PARSE-01 (TOC): .fltoc parser -> hierarchy index
│   ├── flare_cond.py   # PARSE-02: Condition tag extractor
│   └── web_crawl.py    # PARSE-03: Web crawl fallback parser
```

### Pattern 1: Parser Protocol / Base Class
**What:** All parsers implement a common interface producing `Iterator[Document]`.
**When to use:** Every parser module.
**Example:**
```python
from collections.abc import Iterator
from typing import Protocol
from bbj_rag.models import Document

class DocumentParser(Protocol):
    def parse(self) -> Iterator[Document]:
        """Yield Document objects from the configured source."""
        ...
```

### Pattern 2: lxml.etree for XHTML Parsing (NOT HTML parser)
**What:** Parse Flare `.htm` files as XML (they are valid XML with `<?xml?>` declaration), using `lxml.etree.parse()` with namespace-aware XPath.
**When to use:** Every local Flare topic file.
**Why:** These files declare `xmlns:MadCap` and have proper XML structure. Using an HTML parser would mangle the namespace handling.
**Example:**
```python
from lxml import etree

MADCAP_NS = "http://www.madcapsoftware.com/Schemas/MadCap.xsd"
NSMAP = {"mc": MADCAP_NS}

def parse_topic(path: Path) -> etree._Element:
    parser = etree.XMLParser(
        remove_comments=True,
        encoding="utf-8",
    )
    tree = etree.parse(str(path), parser)
    return tree.getroot()
```

### Pattern 3: TOC Index (Pre-built Lookup)
**What:** Parse all `.fltoc` files up front into a dict mapping `Content/`-relative paths to their hierarchy breadcrumb strings. Build once, look up per-topic.
**When to use:** Before iterating topics.
**Example:**
```python
# toc_index: dict[str, str]
# Key: "bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm"
# Value: "Language > BBj Objects > BBjWindow > Methods of BBjWindow"
```

### Pattern 4: Directory-Based Fallback for Orphan Topics
**What:** For the 5,526 orphan topics (78% of all topics!) not in any TOC, derive hierarchy from the file's directory path.
**When to use:** When `toc_index.get(relative_path)` returns None.
**Example:**
```python
# File: Content/bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm
# Fallback path: "bbjobjects > Window > bbjwindow"
```

### Pattern 5: Tag Handler Dispatch
**What:** A dict mapping MadCap tag local names to handler functions. Walk the tree, and when encountering a MadCap namespace element, dispatch to the appropriate handler.
**When to use:** Core of the XHTML parser.
**Example:**
```python
TAG_HANDLERS: dict[str, Callable] = {
    "keyword": handle_keyword,      # Strip entirely (index metadata only)
    "concept": handle_concept,       # Strip entirely (index metadata only)
    "snippetBlock": handle_snippet_block,  # Replace with snippet content
    "snippetText": handle_snippet_text,    # Replace with inline snippet content
    "xref": handle_xref,            # Keep text content, strip tag
    "toggler": handle_toggler,      # Keep text content, strip tag
    "popup": handle_popup,          # Keep popupHead text, strip rest
    "variable": handle_variable,    # Replace with literal or strip
    "miniTocProxy": handle_strip,   # Strip entirely
    "indexProxy": handle_strip,     # Strip entirely
    "conceptLink": handle_strip,    # Strip entirely
    "microContent": handle_strip,   # Strip entirely
}
```

### Anti-Patterns to Avoid
- **Parsing XHTML as HTML:** Using `lxml.html` or BeautifulSoup's HTML parser for the local Flare files will break namespace handling. These are valid XML; parse them as XML.
- **Loading all 7,083 files into memory at once:** Process files one at a time, yielding Document objects. Each file is independent.
- **Ignoring orphan topics:** 78% of topics are not in any TOC. They must still be parsed with directory-based hierarchy.
- **Resolving snippets via filesystem path manipulation only:** Snippet `src` attributes use relative paths (`../../../Resources/Snippets/foo.flsnp`). Resolve against the topic file's location, not against Content root.
- **Building one giant TOC tree in memory:** Build a flat lookup dict (path -> breadcrumb string), not a recursive tree structure.

## Actual MadCap Namespace Tags Found

Analysis of all 7,083 topic files revealed these MadCap namespace tags (by frequency):

| Tag | Count | Recommendation | Rationale |
|-----|-------|----------------|-----------|
| `MadCap:keyword` | 12,857 | **Strip entirely** | Index keywords only; not content text. Found inside `<h1>` tags as metadata. |
| `MadCap:snippetBlock` | 3,627 | **Resolve and inline** | Block-level content inclusion. Load the referenced `.flsnp` file and insert its body content. |
| `MadCap:snippetText` | 2,320 | **Resolve and inline** | Inline content inclusion (e.g., logo images, short text). Load and insert inline. |
| `MadCap:xref` | 1,416 | **Keep text content, strip tag** | Cross-reference links. The inner text is the link label (e.g., "Installing the BASIS License Service"). Keep as plain text. |
| `MadCap:concept` | 930 | **Strip entirely** | Concept markers for Flare's concept linking feature. Not content. |
| `MadCap:toggler` | 360 | **Keep text content, strip tag** | Expandable section labels. The inner text is the visible label (e.g., "Version History"). |
| `MadCap:popup` / `popupHead` / `popupBody` | 31 each | **Keep popupHead text only** | Popup definitions. `popupHead` contains the visible term (e.g., "PRO/5"), `popupBody` is the tooltip definition. Keep the head, drop the body. |
| `MadCap:miniTocProxy` | 5 | **Strip entirely** | Generates mini-TOC at build time. No content. |
| `MadCap:microContent` | 3 | **Strip entirely** | Micro content containers. Negligible count. |
| `MadCap:variable` | 2 | **Strip or replace** | System variables (`System.LongDate`, `System.LongTime`). Replace with placeholder or strip. |
| `MadCap:indexProxy` | 1 | **Strip entirely** | Index rendering proxy. No content. |
| `MadCap:conceptLink` | 1 | **Strip entirely** | Concept link navigation. No content. |

### MadCap Attributes on Standard HTML Elements

| Attribute | Count | Recommendation |
|-----------|-------|----------------|
| `MadCap:conditions` | ~6,843 (on `<html>` and inline elements) | **Extract for metadata**, do not render |
| `MadCap:autosort` / `autosortPriority` / `autosortDirection` | ~1,358 (on `<col>`, `<table>`) | **Strip** -- table sorting metadata, irrelevant for content |
| `MadCap:targetName` | present on some `<p>`, `<li>` | **Strip** -- toggler target anchors |

## Condition Tags Analysis

### Primary.flcts Contents (12 condition tags)

| Condition Tag | Semantics | Generation-Relevant? |
|---------------|-----------|---------------------|
| `Primary.BASISHelp` | Main BBj documentation target | YES -- identifies BBj docs generation |
| `Primary.BDTHelp` | BDT (Eclipse tools) target | YES -- identifies BDT generation |
| `Primary.EMHelp` | Enterprise Manager target | YES -- identifies EM generation |
| `Primary.Deprecated` | Deprecated content marker | YES -- critical for deprecation signals |
| `Primary.Superseded` | Superseded content marker | YES -- critical for supersession signals |
| `Primary.NotImplemented` | Not-yet-implemented content | YES -- content that should be flagged or excluded |
| `Primary.Navigation` | Navigation-only elements | NO -- cosmetic/structural |
| `Primary.bwu` | BWU-specific content | MAYBE -- product subset |
| `Primary.config_chm` | Config CHM target | NO -- build output target |
| `Primary.ddbuild_chm` | DDBuild CHM target | NO -- build output target |
| `Primary.guibuild_chm` | GUIBuild CHM target | NO -- build output target |
| `Primary.resbuild_chm` | ResBuild CHM target | NO -- build output target |

### Condition Tag Distribution (on `<html>` root)

| Condition | File Count | Notes |
|-----------|-----------|-------|
| `Primary.BASISHelp` | 5,961 | Vast majority of topics |
| `Primary.resbuild_chm` | 287 | Resource Builder docs |
| `Primary.ddbuild_chm` | 170 | Data Dictionary Builder docs |
| `Primary.guibuild_chm` | 119 | GUI Builder docs |
| `Primary.Deprecated` | 108 | Deprecated topics |
| `Primary.config_chm` | 50 | Config tool docs |
| `Primary.NotImplemented` | 49 | Not implemented features |
| `Primary.Superseded` | ~35 (combined) | Superseded content |

### Inline Conditions (on `<p>`, `<h2>`, `<table>`, `<li>`, etc.)
Inline conditions appear primarily for `Primary.NotImplemented` content blocks within otherwise-active topics. These mark individual paragraphs, headings, or list items as not yet implemented.

### Condition Recommendation

**Extract all conditions** from both the `<html>` root `MadCap:conditions` attribute and inline element `MadCap:conditions` attributes. Store as:
- Topic-level conditions in `Document.metadata["conditions"]` (comma-separated string from root `<html>`)
- Inline conditions: flag their content but include it (do not exclude content based on conditions -- let downstream decide)

**Generation-relevant tags** (map to `Document.generations`):
- `Primary.BASISHelp` -> `"bbj"`
- `Primary.BDTHelp` -> `"bdt"`
- `Primary.EMHelp` -> `"em"`
- `Primary.Deprecated` -> add `"deprecated"` flag to metadata
- `Primary.Superseded` -> add `"superseded"` flag to metadata
- `Primary.NotImplemented` -> add `"not_implemented"` flag to metadata
- `Primary.*_chm` tags -> map to the product subsection (e.g., `"resbuild"`, `"ddbuild"`)

**Topics with no conditions:** Default to `generations=["bbj"]` since the vast majority of content is BBj documentation.

**Condition expressions (Boolean combinations):** The actual data shows only simple comma-separated lists (e.g., `"Primary.BASISHelp,Primary.Deprecated"`). No Boolean operators (AND/OR/NOT) were found. Store as flat list.

## TOC File Analysis

### Structure
4 TOC files in `Project/TOCs/`:
| File | Unique Links | Total Entries | Max Depth |
|------|-------------|---------------|-----------|
| `basishelp.fltoc` | 1,368 | 2,246 (2,098 with links + 148 headers) | 7 levels |
| `pro5toc.fltoc` | 293 | ~350 | ~6 levels |
| `bdthelp.fltoc` | 10 | ~12 | 4 levels |
| `emhelp.fltoc` | 60 | ~75 | 5 levels |
| **Total unique** | **1,581** | | |

### Key TOC Characteristics
- **XML format:** `<CatapultToc Version="1">` root, nested `<TocEntry>` elements
- **Attributes:** `Title` (display name), `Link` (path to topic, starts with `/Content/`)
- **No conditions in TOCs** -- zero `MadCap:conditions` attributes in any TOC file
- **`[%=System.LinkedTitle%]`** entries: 48 in basishelp.fltoc -- title derived from the linked topic's `<title>` element at build time. Parser must resolve these from the topic file.
- **Section-only entries (no Link):** 148 in basishelp.fltoc -- act as grouping headers (e.g., "Earlier Versions", "Servers")
- **140 files appear in both basishelp and pro5toc** -- same topic in two hierarchies. Use basishelp hierarchy as primary.
- **5,526 orphan topics** (78% of 7,083 topic files) not in any TOC

### TOC Strategy Recommendation
1. Parse all 4 TOC files
2. Build a unified lookup: `dict[str, str]` mapping Content-relative path to arrow-separated breadcrumb
3. Priority: `basishelp.fltoc` > `emhelp.fltoc` > `bdthelp.fltoc` > `pro5toc.fltoc` (if same topic in multiple TOCs)
4. For `[%=System.LinkedTitle%]` entries, resolve from the linked topic's `<title>` tag
5. For orphans, derive path from directory structure

## Code Block Detection

### Patterns Found
| Pattern | Count | Description |
|---------|-------|-------------|
| `<pre><code class="language-*">` | 3,029 | Primary code block pattern, inside `class="Code_Table"` tables |
| `class="language-bbj"` | 2,951 | BBj code examples (dominant) |
| `class="language-css"` | 42 | CSS examples |
| `class="language-bbjconsole"` | 29 | Console/terminal output |
| `class="language-xml"` | 17 | XML examples |
| `class="language-java"` | 6 | Java interop examples |
| `class="language-sql"` | 2 | SQL examples |
| Other (`json`, `html`, `bbjconfig`, `bbjarc`) | 5 | Rare languages |

### Code Block Extraction Strategy
1. Detect `<pre><code>` combinations
2. Extract language from `class="language-XXX"` attribute
3. Preserve code text as-is (no HTML entity decoding beyond standard XML)
4. Wrap in markdown fenced code blocks: `` ```bbj ... ``` ``
5. Also detect `class="Code"` on `<p>` elements (used for single-line code, not full blocks)

## Table Handling

### Table Classes Found
| Class | Purpose | Handling |
|-------|---------|---------|
| `Methods_Table` | API method signatures (Return Value / Method) | Convert to markdown table |
| `Parameter_Table` | Parameter descriptions (Variable / Description) | Convert to markdown table |
| `Flag_Table` | Flag values and descriptions | Convert to markdown table |
| `Code_Table` | Code example wrapper (single cell with `<pre><code>`) | Extract code block, not as table |

### Table Conversion Strategy
Convert HTML tables to markdown tables. Skip `Code_Table` class (handle as code blocks instead). Preserve header rows. For nested tables (found in parameter docs), flatten to single-level.

## Snippet Resolution

### Structure
- 205 `.flsnp` files in `Content/Resources/Snippets/`
- Each is a minimal XHTML file with `<html><body>` containing the snippet content
- Referenced via relative `src` attributes: `src="../../../Resources/Snippets/Unspecified_xywh.flsnp"`
- Two types: `snippetBlock` (block-level, full paragraphs) and `snippetText` (inline, small fragments)

### Resolution Strategy
1. Pre-load all 205 snippets into a dict: `dict[str, etree._Element]` keyed by canonical path
2. When encountering `MadCap:snippetBlock` or `MadCap:snippetText`, resolve the `src` against the topic file's directory
3. Replace the snippet tag with the snippet's `<body>` children (block) or text content (inline)
4. Some snippets contain only images (e.g., logos) -- these produce empty text, which is fine

## Web Crawl Fallback (PARSE-03)

### Site Structure
- URL: `https://documentation.basis.cloud/BASISHelp/WebHelp/`
- Redirects from `documentation.basis.cloud` and `www.basis.cloud/documentation`
- Path after `/BASISHelp/WebHelp/` mirrors the `Content/` directory structure
  - e.g., `Content/bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm` -> `https://documentation.basis.cloud/BASISHelp/WebHelp/bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm`
- MadCap Flare rendered HTML5 output (not XHTML) -- use BeautifulSoup HTML parser
- Navigation added by Flare build (sidebar, breadcrumbs, search bar) needs to be stripped

### Crawl Strategy
1. Start from index page, discover all topic links
2. Use `httpx` for HTTP requests (respecting rate limits)
3. Parse with `BeautifulSoup(html, "lxml")` (HTML parser, not XML)
4. Extract `div.page-content` or `<body>` content (strip Flare navigation chrome)
5. Derive hierarchy from URL path structure
6. No condition metadata available from crawled content -- default to `generations=["bbj"]`, `metadata={"source": "web_crawl"}`

### Rate Limiting
Be polite: 1-2 requests per second, respect robots.txt. Use `httpx.AsyncClient` for efficient crawling with concurrency limits.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| XML parsing | Custom regex-based tag extraction | `lxml.etree` | XML has edge cases (CDATA, entities, namespaces) that regex cannot handle |
| HTML table to markdown | Custom string formatting | `markdownify` or simple converter function | Table alignment, colspan, nested tables are tricky |
| URL normalization | Manual path joining | `urllib.parse.urljoin` | Handles relative paths, `..`, fragments correctly |
| Encoding detection | Manual BOM sniffing | `lxml.etree.XMLParser(encoding="utf-8")` | lxml handles BOM and encoding declarations |
| Web crawl link discovery | Custom regex href extraction | BeautifulSoup `soup.find_all("a", href=True)` | BS4 handles malformed HTML, relative URLs |

**Key insight:** The Flare files are valid XML with a well-defined structure. Using lxml.etree gives proper namespace handling, XPath support, and fast parsing. Trying to use regex or HTML parsers on XML with namespaces will create subtle, hard-to-debug failures.

## Common Pitfalls

### Pitfall 1: Parsing XHTML as HTML
**What goes wrong:** HTML parsers ignore XML namespaces, converting `MadCap:keyword` to a string literal tag instead of a namespaced element. Tags are silently lost or mangled.
**Why it happens:** Flare files use `.htm` extension, tempting HTML parser use.
**How to avoid:** Always use `etree.parse()` or `etree.fromstring()` for local Flare files. Check that the file starts with `<?xml version=`.
**Warning signs:** MadCap tags not found during extraction; empty keyword/snippet results.

### Pitfall 2: Ignoring Orphan Topics
**What goes wrong:** Only parsing topics in TOC files produces 1,581 documents instead of 7,083.
**Why it happens:** Assuming TOC is comprehensive. In this project, 78% of topics are orphans.
**How to avoid:** Iterate `Content/` directory for all `.htm` files (excluding `Resources/`), look up TOC path with directory fallback.
**Warning signs:** BBjWindow methods, events, interfaces missing from output.

### Pitfall 3: BOM in UTF-8 Files
**What goes wrong:** BOM bytes (`\xef\xbb\xbf`) at start of file cause XML parsing errors if not handled.
**Why it happens:** Many Flare files have UTF-8 BOM (Windows-originated).
**How to avoid:** Open files in binary mode and let lxml handle encoding, or strip BOM when reading. `lxml.etree.parse()` with a file path handles this automatically.
**Warning signs:** `XMLSyntaxError` on the first character of certain files.

### Pitfall 4: Snippet Resolution Path Errors
**What goes wrong:** Snippet references use relative paths like `../../../Resources/Snippets/foo.flsnp`. If resolved against the wrong base directory, file-not-found errors occur.
**Why it happens:** Confusing Content/ root with the topic file's directory.
**How to avoid:** Resolve snippet `src` relative to the topic file's parent directory using `pathlib.Path.resolve()`.
**Warning signs:** Snippet content missing; `FileNotFoundError` during parsing.

### Pitfall 5: Massive Topic Files
**What goes wrong:** Some topic files are extremely large (e.g., `bbjwindow.htm` is 76,000+ tokens). Trying to hold too many parsed trees in memory causes issues.
**Why it happens:** Method reference pages list hundreds of methods with signatures.
**How to avoid:** Process one file at a time, yield Document objects, let garbage collection work. Do not accumulate all parsed trees.
**Warning signs:** High memory usage during parsing; slow processing.

### Pitfall 6: Multiple TOC Entries for Same File
**What goes wrong:** Same topic appears in multiple TOCs with different hierarchy paths.
**Why it happens:** 140 topics appear in both `basishelp.fltoc` and `pro5toc.fltoc`.
**How to avoid:** Build TOC index with priority order. Use first-found (basishelp wins).
**Warning signs:** Duplicate Document objects with different section paths.

## Code Examples

### Parsing a Flare XHTML Topic File
```python
from pathlib import Path
from lxml import etree

MADCAP_NS = "http://www.madcapsoftware.com/Schemas/MadCap.xsd"

def parse_topic_file(path: Path) -> etree._Element:
    """Parse a Flare XHTML topic file as XML."""
    parser = etree.XMLParser(remove_comments=True)
    tree = etree.parse(str(path), parser)
    return tree.getroot()

def extract_title(root: etree._Element) -> str:
    """Extract title from <head><title> element."""
    ns = {"xhtml": "http://www.w3.org/1999/xhtml"}
    # Files don't use XHTML namespace on html/head/title
    title_elem = root.find(".//head/title")
    if title_elem is not None and title_elem.text:
        return title_elem.text.strip()
    # Fallback: first <h1> text
    h1 = root.find(".//body//h1")
    if h1 is not None:
        return "".join(h1.itertext()).strip()
    return ""

def extract_conditions(root: etree._Element) -> list[str]:
    """Extract MadCap:conditions from root <html> element."""
    cond_attr = root.get(f"{{{MADCAP_NS}}}conditions", "")
    if not cond_attr:
        return []
    return [c.strip() for c in cond_attr.split(",") if c.strip()]
```

### Building TOC Index
```python
from pathlib import Path
from lxml import etree

def build_toc_index(toc_dir: Path) -> dict[str, str]:
    """Parse all .fltoc files into a path -> breadcrumb lookup."""
    index: dict[str, str] = {}
    # Priority order
    toc_files = ["basishelp.fltoc", "emhelp.fltoc", "bdthelp.fltoc", "pro5toc.fltoc"]

    for toc_name in toc_files:
        toc_path = toc_dir / toc_name
        if not toc_path.exists():
            continue
        tree = etree.parse(str(toc_path))
        root = tree.getroot()
        _walk_toc(root, [], index)

    return index

def _walk_toc(
    elem: etree._Element,
    breadcrumbs: list[str],
    index: dict[str, str],
) -> None:
    for entry in elem:
        if entry.tag != "TocEntry":
            continue
        title = entry.get("Title", "")
        link = entry.get("Link", "")

        current_crumbs = breadcrumbs + [title] if title else breadcrumbs

        if link:
            # Normalize: strip leading /Content/
            rel_path = link.removeprefix("/Content/")
            if rel_path not in index:  # First-found wins (priority order)
                index[rel_path] = " > ".join(current_crumbs)

        _walk_toc(entry, current_crumbs, index)
```

### Extracting Text with MadCap Tag Handling
```python
from lxml import etree

MADCAP_NS = "http://www.madcapsoftware.com/Schemas/MadCap.xsd"
STRIP_TAGS = {"keyword", "concept", "miniTocProxy", "indexProxy", "conceptLink", "microContent"}
KEEP_TEXT_TAGS = {"xref", "toggler"}

def extract_body_text(body: etree._Element, snippets: dict[str, etree._Element]) -> str:
    """Recursively extract text from body, handling MadCap tags."""
    parts: list[str] = []
    _walk_element(body, parts, snippets)
    return "\n".join(parts)

def _walk_element(
    elem: etree._Element,
    parts: list[str],
    snippets: dict[str, etree._Element],
) -> None:
    tag = etree.QName(elem.tag) if isinstance(elem.tag, str) else None
    if tag and tag.namespace == MADCAP_NS:
        local = tag.localname
        if local in STRIP_TAGS:
            return  # Skip entirely
        if local in KEEP_TEXT_TAGS:
            text = "".join(elem.itertext())
            if text.strip():
                parts.append(text.strip())
            return
        if local == "snippetBlock":
            _resolve_snippet(elem, parts, snippets, block=True)
            return
        if local == "snippetText":
            _resolve_snippet(elem, parts, snippets, block=False)
            return
        if local == "popup":
            # Keep popupHead text only
            head = elem.find(f"{{{MADCAP_NS}}}popupHead")
            if head is not None:
                text = "".join(head.itertext())
                if text.strip():
                    parts.append(text.strip())
            return
    # Standard HTML element -- process children
    if elem.text and elem.text.strip():
        parts.append(elem.text.strip())
    for child in elem:
        _walk_element(child, parts, snippets)
        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())
```

### Converting Tables to Markdown
```python
def table_to_markdown(table_elem: etree._Element) -> str:
    """Convert an HTML table element to markdown table format."""
    rows = table_elem.findall(".//tr")
    if not rows:
        return ""

    md_rows: list[list[str]] = []
    for row in rows:
        cells = row.findall("th") + row.findall("td")
        md_rows.append(["".join(cell.itertext()).strip() for cell in cells])

    if not md_rows:
        return ""

    # Header row
    header = md_rows[0]
    separator = ["---"] * len(header)
    body = md_rows[1:]

    lines = [" | ".join(header), " | ".join(separator)]
    lines.extend(" | ".join(row) for row in body)
    return "\n".join(lines)
```

## File System Details

### Project Structure Summary
```
/Users/beff/bbjdocs/
├── BASISHelp.flprj                    # Project file (minimal XML)
├── Content/                            # 137 MB total
│   ├── index.htm                       # Landing page
│   ├── Resources/                      # 26 MB (snippets, styles, images, templates)
│   │   ├── Snippets/ (205 .flsnp)
│   │   ├── MicroContent/ (3 .flmco)
│   │   ├── Images/
│   │   ├── Stylesheets/
│   │   └── Templates/
│   ├── images/                         # 46 MB (topic images)
│   ├── bbjobjects/                     # Largest section: 2,432+ orphan files
│   ├── commands/                       # Language commands
│   ├── events/                         # Event reference
│   ├── bbjevents/                      # BBj events
│   └── [40+ other topic directories]
└── Project/
    ├── TOCs/                           # 4 .fltoc files
    │   ├── basishelp.fltoc (7,025 lines, primary)
    │   ├── pro5toc.fltoc (1,057 lines)
    │   ├── emhelp.fltoc
    │   └── bdthelp.fltoc
    └── ConditionTagSets/
        └── Primary.flcts               # 12 condition tags
```

### Key Counts
| Item | Count |
|------|-------|
| Total `.htm` topic files (excl. Resources) | 7,083 |
| Topics in at least one TOC | 1,557 (22%) |
| Orphan topics (not in any TOC) | 5,526 (78%) |
| Snippet files (`.flsnp`) | 205 |
| TOC files (`.fltoc`) | 4 |
| Condition tag sets | 1 (12 tags) |
| Code examples (`<pre><code>`) | 3,029 |
| Total XHTML content size | ~55 MB |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| BeautifulSoup for all XML | lxml.etree for XML, BS4 for HTML only | Long-standing best practice | Proper namespace handling |
| `xml.etree.ElementTree` (stdlib) | `lxml.etree` | N/A (lxml has been preferred for years) | 10-20x faster, better namespace support |
| `requests` for HTTP | `httpx` | 2023+ | Better async support, modern API |

## Open Questions

1. **Table markdown conversion quality**
   - What we know: Tables use `Parameter_Table`, `Methods_Table`, `Flag_Table` classes with varying column counts and nested tables
   - What's unclear: How well simple markdown tables handle complex nested structures (e.g., parameter table with nested flag table)
   - Recommendation: Start with simple conversion; handle `Code_Table` separately as code blocks; test on representative files

2. **Snippet content that produces no text**
   - What we know: Some snippets contain only images (logos, icons) with no text content
   - What's unclear: Whether empty snippet resolution should leave a gap or be invisible
   - Recommendation: Skip silently (empty text after resolution is fine)

3. **`[%=System.LinkedTitle%]` resolution in TOCs**
   - What we know: 48 TOC entries use this variable instead of a literal title
   - What's unclear: Whether all 48 linked files have `<title>` elements
   - Recommendation: Resolve from topic `<title>` tag; fall back to filename-derived title

4. **Crawl scope and page count**
   - What we know: URL structure mirrors Content/ directory; site is publicly accessible
   - What's unclear: Whether all 7,000+ topics are published on the web, or only the TOC-linked ones
   - Recommendation: Start crawl from sitemap or index; follow all internal links; compare against local file count

## Sources

### Primary (HIGH confidence)
- Direct examination of `/Users/beff/bbjdocs/` -- all file counts, tag analysis, structure
- `lxml` documentation at https://lxml.de/parsing.html -- XML parsing patterns
- Existing codebase at `/Users/beff/_workspace/bbj-ai-strategy/rag-ingestion/` -- Document/Chunk models, config

### Secondary (MEDIUM confidence)
- BeautifulSoup documentation at https://www.crummy.com/software/BeautifulSoup/bs4/doc/ -- HTML parser usage
- Web crawl target at https://documentation.basis.cloud/BASISHelp/WebHelp/ -- site structure verified

### Tertiary (LOW confidence)
- Community patterns for lxml namespace handling (multiple Stack Overflow sources agree)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - lxml is the clear choice for namespace-aware XML; verified against actual file structure
- Architecture: HIGH - based on exhaustive analysis of actual source files, not hypothetical patterns
- Pitfalls: HIGH - pitfalls identified from actual data (BOM presence, orphan count, file sizes)

**Research date:** 2026-01-31
**Valid until:** 2026-03-31 (stable domain -- MadCap Flare format does not change frequently)
