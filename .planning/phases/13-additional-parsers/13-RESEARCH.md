# Phase 13: Additional Parsers - Research

**Researched:** 2026-02-01
**Domain:** PDF extraction, WordPress web crawling, Docusaurus MDX parsing, BBj source code parsing
**Confidence:** HIGH (core libraries verified via official docs and PyPI)

## Summary

This phase adds five new parsers to the proven Flare pipeline (parse -> tag -> chunk -> embed -> store): PDF, WordPress/Advantage articles, WordPress/Knowledge Base lessons, Docusaurus MDX (DWC-Course), and BBj source code. The pipeline architecture is settled from Phase 12 -- each new parser must implement the `DocumentParser` protocol (yielding `Document` objects with `source_url`, `title`, `doc_type`, `content`, `generations`, `context_header`, `metadata`).

The standard approach uses **pymupdf4llm 0.2.9** for PDF-to-Markdown conversion (with `TocHeaders` for chapter/section detection), **httpx + BeautifulSoup** (already in the project) for WordPress crawling, **python-frontmatter 1.1.0** with regex-based JSX stripping for MDX parsing, and a custom text-based parser for BBj source code files. All parsers plug into the existing `run_pipeline()` orchestrator via the `DocumentParser` protocol, and the existing intelligence module (generation tagger, doc type classifier, chunker) handles downstream processing.

The key challenge is that each parser needs a different approach to generation tagging. The PDF parser should use content-based signals (since there are no file paths or conditions), WordPress parsers rely on the generation tagger for classification, DWC-Course content is uniformly tagged `dwc` (user decision), and BBj source code requires API-pattern analysis to distinguish `dwc` from `bbj_gui`.

**Primary recommendation:** Implement parsers as independent modules in `parsers/` following the same `DocumentParser` protocol pattern. Each parser is self-contained and testable in isolation. The pipeline and intelligence modules handle all downstream processing unchanged.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pymupdf4llm | 0.2.9 | PDF to Markdown conversion | Official PyMuPDF companion for RAG/LLM use cases; handles headers, tables, code blocks, images natively |
| python-frontmatter | 1.1.0 | Parse YAML frontmatter from MDX/MD files | Standard Python library for frontmatter (111K+ weekly downloads); extracts metadata dict + content body |
| httpx | >=0.28 (already installed) | HTTP client for WordPress crawling | Already in project; async-capable, HTTP/2 support |
| beautifulsoup4 | >=4.13 (already installed) | HTML parsing for WordPress pages | Already in project with lxml parser; decision locked |
| pymupdf | (auto-installed with pymupdf4llm) | Underlying PDF engine | PyMuPDF is the standard Python PDF library for text extraction |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib (stdlib) | N/A | File path handling for local MDX/BBj files | All local file parsers |
| re (stdlib) | N/A | Regex for JSX stripping, BBj code pattern detection | MDX JSX removal, source code analysis |
| logging (stdlib) | N/A | Parser progress and error reporting | All parsers for consistency with existing pattern |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pymupdf4llm | pdfplumber / pdfminer | pymupdf4llm is purpose-built for LLM/RAG markdown output; others require manual markdown conversion |
| python-frontmatter | pyyaml + manual splitting | python-frontmatter handles edge cases (missing frontmatter, different delimiters); not worth hand-rolling |
| regex JSX stripping | Node.js @mdx-js/mdx via subprocess | Massive over-engineering; MDX files in DWC-Course use simple JSX components that regex handles cleanly |

**Installation:**
```bash
# Add to pyproject.toml dependencies
pip install pymupdf4llm>=0.2.9 python-frontmatter>=1.1
```

**Note on pymupdf4llm licensing:** Dual-licensed under GNU AGPL 3.0 or Artifex Commercial License. The AGPL applies to the pymupdf4llm package itself. Since this is an internal ingestion tool (not distributed as a service), AGPL is acceptable. Verify with project owner if uncertain.

## Architecture Patterns

### Recommended Project Structure
```
src/bbj_rag/parsers/
    __init__.py          # DocumentParser protocol (existing)
    flare.py             # Flare XHTML parser (existing)
    flare_cond.py        # Flare conditions (existing)
    flare_toc.py         # Flare TOC (existing)
    web_crawl.py         # Web crawl parser (existing, reusable patterns)
    pdf.py               # NEW: PDF parser (pymupdf4llm)
    wordpress.py         # NEW: WordPress parsers (Advantage + Knowledge Base)
    mdx.py               # NEW: Docusaurus MDX parser
    bbj_source.py        # NEW: BBj source code parser
```

### Pattern 1: DocumentParser Protocol Compliance
**What:** Every parser implements `parse() -> Iterator[Document]` yielding validated Document objects.
**When to use:** Always -- this is the existing contract from Phase 12.
**Example:**
```python
# Source: existing parsers/__init__.py
@runtime_checkable
class DocumentParser(Protocol):
    def parse(self) -> Iterator[Document]: ...

# Each new parser follows this pattern:
class PdfParser:
    def __init__(self, pdf_path: Path) -> None:
        self._pdf_path = pdf_path

    def parse(self) -> Iterator[Document]:
        # Extract sections, yield Document objects
        ...
```

### Pattern 2: Parser-Specific Intelligence Override
**What:** The pipeline currently applies intelligence (generation tagging, doc_type classification) assuming Flare content paths. New parsers need custom intelligence adaptation since they lack Flare-specific metadata (conditions, Content-relative paths).
**When to use:** For parsers whose content does not map to the Flare path/condition signal system.
**Approach:** New parsers should set `generations` and `doc_type` directly on the Document object before yielding, bypassing the pipeline's `_apply_intelligence()` step. The pipeline should be adapted to skip intelligence when documents already have non-placeholder generations.

Alternatively, the simpler approach: each parser pre-populates `generations` and `doc_type` fields, and the pipeline's `_apply_intelligence()` is wrapped with a guard:
```python
# In pipeline.py, modify _apply_intelligence usage:
if doc.doc_type != "placeholder":  # parser already classified
    generations = doc.generations
    deprecated = doc.deprecated
    doc_type = doc.doc_type
    header = doc.context_header
else:
    generations, deprecated, doc_type, header = _apply_intelligence(...)
```

### Pattern 3: Index-Page-Then-Article Crawl Pattern
**What:** For WordPress sites, first crawl the index page to discover article URLs, then fetch each article individually.
**When to use:** Advantage (index at `/advantage-index/`) and Knowledge Base (index at `/knowledge-base/`).
**Why:** Unlike the Flare web crawl which follows links recursively, WordPress sites have clear index pages listing all content. Targeted crawling is more reliable than recursive link-following on WordPress sites with plugins, navigation, and non-content pages.
```python
class WordPressParser:
    def __init__(self, index_url: str, ...) -> None:
        self._index_url = index_url

    def parse(self) -> Iterator[Document]:
        article_urls = self._discover_article_urls()
        for url in article_urls:
            doc = self._fetch_and_parse_article(url)
            if doc is not None:
                yield doc
```

### Pattern 4: Local File Iterator Pattern
**What:** For MDX and BBj source code, iterate over local files matching glob patterns.
**When to use:** DWC-Course repo clone (MDX) and BBj source files from mixed locations.
```python
class MdxParser:
    def __init__(self, docs_dir: Path) -> None:
        self._docs_dir = docs_dir

    def parse(self) -> Iterator[Document]:
        for mdx_path in sorted(self._docs_dir.rglob("*.md")):
            doc = self._parse_file(mdx_path)
            if doc is not None:
                yield doc
        for mdx_path in sorted(self._docs_dir.rglob("*.mdx")):
            doc = self._parse_file(mdx_path)
            if doc is not None:
                yield doc
```

### Anti-Patterns to Avoid
- **Modifying existing intelligence module for new source types:** The generation tagger's path/condition signals are Flare-specific. Do NOT add WordPress URL patterns to `_PATH_GENERATION_MAP`. Instead, let parsers pre-populate generations.
- **Re-implementing HTML-to-Markdown conversion:** The existing `web_crawl.py` already has `_html_to_markdown()`. Reuse it for WordPress content extraction rather than writing a new converter.
- **Fetching DWC-Course via HTTP:** User decision locks this to local file parsing. Do not add web crawl fallback for MDX.
- **Treating the PDF as a single Document:** The PDF is 47 pages with multiple chapters/sections. It must be split into section-level Documents for meaningful chunking.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF text extraction with layout | Custom PyMuPDF page iteration + manual markdown | `pymupdf4llm.to_markdown()` | Handles headers, tables, code blocks, multi-column layouts, fonts; months of edge cases already solved |
| PDF heading detection | Font-size heuristics | `pymupdf4llm.TocHeaders(doc)` or `IdentifyHeaders(doc)` | PDF has a TOC (page 1 is a full table of contents); TocHeaders maps TOC entries to heading levels automatically |
| YAML frontmatter parsing | Manual `---` splitting + yaml.safe_load | `python-frontmatter.load()` | Handles edge cases (missing frontmatter, trailing whitespace, multiple `---` blocks) |
| WordPress boilerplate removal | Manual HTML parsing | Reuse `web_crawl.py` patterns: `_strip_chrome()` + `_find_content_root()` + `_html_to_markdown()` | Already tested against WordPress/Astra theme; just add WordPress-specific selectors |
| HTML to Markdown | Custom converter | Reuse `web_crawl._html_to_markdown()` | Already handles headings, paragraphs, code blocks, tables, lists |

**Key insight:** The PDF is the trickiest source because it mixes text, tables, code blocks, and images in a non-structured format. pymupdf4llm solves this comprehensively. For all other sources, the existing codebase provides reusable building blocks.

## Common Pitfalls

### Pitfall 1: pymupdf4llm Header Detection on this Specific PDF
**What goes wrong:** The GuideToGuiProgrammingInBBj.pdf uses styled headings (bold, larger font) but the TOC on page 1 uses hyperlinks, not headings. pymupdf4llm's default `IdentifyHeaders` uses font-size popularity, which may misclassify TOC entries as headings.
**Why it happens:** The PDF has a flat structure where the TOC page itself contains the same font sizes as section headers in the body.
**How to avoid:** Use `TocHeaders` (which reads the PDF's internal TOC metadata via `Document.get_toc()`) rather than font-size-based detection. If the PDF lacks internal TOC metadata, fall back to `IdentifyHeaders` with `max_levels=3` to limit header depth.
**Warning signs:** Test by converting page 1 and checking if TOC entries become markdown headings (they should not -- they are body text on the TOC page).

### Pitfall 2: WordPress Dynamic Content Loading
**What goes wrong:** The Advantage index page (`/advantage-index/`) uses JavaScript/AJAX for dynamic content loading. Simple `httpx.get()` returns shell HTML without article links.
**Why it happens:** WordPress + LearnPress uses AJAX endpoints for content loading (visible in page source as `lpData` configuration).
**How to avoid:** Two approaches: (1) Parse the rendered HTML more aggressively -- look for `<a>` tags in the initial HTML that link to individual articles (WordPress often includes article links even on JS-heavy pages), or (2) use the WordPress REST API at `/wp-json/wp/v2/posts` to discover article URLs programmatically despite the decision to crawl (use API only for URL discovery, then crawl each article page).
**Warning signs:** If `_discover_article_urls()` returns 0 URLs, the content is dynamically loaded. Add a fallback URL discovery method.

### Pitfall 3: MDX JSX Component Stripping Destroys Content
**What goes wrong:** Naively stripping all JSX tags removes meaningful inner text. Example: `<Link to="/foo">Click here</Link>` should preserve "Click here" but strip the `<Link>` wrapper.
**Why it happens:** Regex-based JSX removal that strips everything between `<Component>` and `</Component>`.
**How to avoid:** Two-pass approach: (1) Remove self-closing components entirely (`<Hero />`, `<HomepageFeatures />`), (2) For wrapper components (`<Link>...</Link>`, `<div>...</div>`), strip the tags but keep inner content. This is what BeautifulSoup does naturally with `get_text()`.
**Warning signs:** Empty documents after parsing MDX files that contain JSX components wrapping text content.

### Pitfall 4: BBj Source Code Files Without Standard Extensions
**What goes wrong:** BBj source files use `.bbj`, `.txt`, `.src`, and other extensions. A glob for `*.bbj` misses most samples.
**Why it happens:** BBj has historical file format variety (see PDF: cust-cui.txt, cust-gui.src, cust-bbj.txt, cust-obj.txt).
**How to avoid:** Accept a configurable list of extensions (default: `.bbj`, `.txt`, `.src`) and/or accept an explicit list of file paths. The parser should validate content looks like BBj code (check for BBj keywords: `rem`, `open`, `print`, `PROCESS_EVENTS`, `class public`, `method public`) before processing.
**Warning signs:** Parser returns 0 documents, or processes non-BBj text files as code.

### Pitfall 5: PDF Code Block Detection
**What goes wrong:** pymupdf4llm may not detect BBj code blocks correctly because BBj is not a mainstream language. Code blocks in the PDF use monospace fonts but may not be wrapped in standard `<pre>` elements.
**Why it happens:** pymupdf4llm detects code blocks via monospace font detection, which works for this PDF. However, some code examples in the PDF are embedded in tables (like the mnemonic vs. object-oriented syntax comparison on page 9).
**How to avoid:** Use `ignore_code=False` (default) to enable code block detection. For table-embedded code, the markdown table output will preserve the code text adequately for chunking. Post-process if needed to extract code from single-cell tables.
**Warning signs:** Code blocks appearing as plain text or table content in the markdown output.

### Pitfall 6: Knowledge Base vs Advantage Chrome Selectors
**What goes wrong:** Using the same chrome stripping selectors for both WordPress sites, but they use different themes/plugins. Advantage uses standard WordPress/Astra, Knowledge Base uses the ECKB (Echo Knowledge Base) plugin with `#eckb-article-page-container-v2` and `#eckb-article-body` layouts.
**Why it happens:** Different WordPress plugins generate different HTML structures.
**How to avoid:** Create separate content selector lists for each site. Advantage content is in standard WordPress `article` or `.entry-content` containers. Knowledge Base content is in the ECKB grid's middle column within `#eckb-article-body`.
**Warning signs:** Empty content or entire page chrome appearing in parsed output.

## Code Examples

### PDF Parser: pymupdf4llm with TocHeaders
```python
# Source: pymupdf4llm official docs (https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html)
import pymupdf4llm
import pymupdf

doc = pymupdf.open("GuideToGuiProgrammingInBBj.pdf")

# Use TOC-based header detection (best for this PDF which has a TOC)
hdr_info = pymupdf4llm.TocHeaders(doc)

# Convert with page chunks for per-section processing
data = pymupdf4llm.to_markdown(
    doc,
    hdr_info=hdr_info,
    page_chunks=True,       # list of dicts, one per page
    write_images=False,      # decision: strip images
    table_strategy="lines_strict",  # default, best for bordered tables
    show_progress=True,
)

# data is list[dict] -- each dict has 'text' key with markdown content
for page_data in data:
    page_md = page_data["text"]
    # Split at heading boundaries for section-level Documents
    ...
```

### PDF Parser: IdentifyHeaders fallback
```python
# If TocHeaders fails (PDF lacks internal TOC metadata)
hdr_info = pymupdf4llm.IdentifyHeaders(doc, max_levels=3)
md_text = pymupdf4llm.to_markdown(doc, hdr_info=hdr_info)
```

### MDX Parser: Frontmatter + JSX Stripping
```python
# Source: python-frontmatter docs (https://python-frontmatter.readthedocs.io/)
import frontmatter
import re
from pathlib import Path

def parse_mdx_file(path: Path) -> tuple[dict, str]:
    """Parse MDX file, returning (metadata, content)."""
    post = frontmatter.load(str(path))
    metadata = dict(post.metadata)  # e.g. {'sidebar_position': 1, 'title': '...'}
    content = post.content

    # Strip import statements (import X from '@site/...')
    content = re.sub(r"^import\s+.+$", "", content, flags=re.MULTILINE)

    # Strip self-closing JSX components: <Hero />, <HomepageFeatures />
    content = re.sub(r"<[A-Z][A-Za-z]*\s*/>", "", content)

    # Strip JSX wrapper tags but keep inner content:
    # <Link className="..." to="/...">text</Link> -> text
    content = re.sub(r"<[A-Z][A-Za-z]*[^>]*>", "", content)
    content = re.sub(r"</[A-Z][A-Za-z]*>", "", content)

    # Strip HTML div/span wrappers with className (Docusaurus-specific)
    content = re.sub(r'<div\s+className="[^"]*"[^>]*>', "", content)
    content = re.sub(r"</div>", "", content)

    # Collapse excessive blank lines
    content = re.sub(r"\n{3,}", "\n\n", content)

    return metadata, content.strip()
```

### WordPress Parser: Article Content Extraction
```python
# Reuses patterns from existing web_crawl.py
from bs4 import BeautifulSoup, Tag

# WordPress-specific chrome selectors (extend existing _CHROME_SELECTORS)
_WP_CHROME_SELECTORS: list[str] = [
    "nav", "script", "style", "noscript", "iframe",
    "header", "footer",
    ".site-header", ".site-footer",
    ".breadcrumb", ".breadcrumbs",
    ".sidebar", ".widget-area",
    ".comments-area", ".post-navigation",
    "#secondary", "#comments",
    ".wp-block-separator",
]

# Advantage article content selectors (try in order)
_ADVANTAGE_CONTENT_SELECTORS: list[str] = [
    ".entry-content",
    "article .post-content",
    "article",
    "[role='main']",
    "main",
]

# Knowledge Base content selectors (ECKB plugin)
_KB_CONTENT_SELECTORS: list[str] = [
    "#eckb-article-body",
    ".eckb-article-content-body",
    "article .entry-content",
    "article",
    "main",
]
```

### BBj Source Code Parser: Generation Detection
```python
import re

# DWC-specific patterns (content tagged as "dwc")
_DWC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"BBjHtmlView", re.IGNORECASE),
    re.compile(r"BBjWebComponent"),
    re.compile(r"setCss|addStyle|getStyle", re.IGNORECASE),
    re.compile(r"setResponsive|getComputedStyle"),
    re.compile(r"BBjNavigator"),
    re.compile(r"webManager|getWebManager"),
    re.compile(r'setAttribute\s*\(\s*"dwc-'),  # DWC custom attributes
    re.compile(r"\.css\("),  # CSS method calls
]

# General GUI patterns (content tagged as "bbj_gui")
_GUI_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"BBjAPI\(\)"),
    re.compile(r"getSysGui"),
    re.compile(r"PROCESS_EVENTS"),
    re.compile(r"addWindow|addButton|addEditBox"),
    re.compile(r"setCallback"),
    re.compile(r"BBjTopLevelWindow"),
    re.compile(r"SYSGUI"),
]

def classify_source_generation(content: str) -> list[str]:
    """Classify BBj source code by generation based on API patterns.

    DWC is a superset of GUI: bbj_gui content is ~95% relevant to DWC users,
    but dwc-specific content does NOT apply to traditional GUI.
    """
    has_dwc = any(p.search(content) for p in _DWC_PATTERNS)
    has_gui = any(p.search(content) for p in _GUI_PATTERNS)

    if has_dwc:
        return ["dwc"]  # DWC-specific code
    if has_gui:
        return ["bbj_gui"]  # General GUI code (95% DWC-relevant)
    return ["all"]  # Non-GUI code (utilities, data access, etc.)
```

### BBj Source Code: Leading Comment Extraction
```python
def extract_header_comment(content: str) -> str:
    """Extract leading comment block from BBj source code.

    BBj comments start with 'rem' (case-insensitive) or are preceded
    by 'rem' keyword. The first contiguous block of rem lines forms
    the description.
    """
    lines = content.splitlines()
    comment_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if comment_lines:
                break  # End of comment block
            continue
        # BBj comments: rem or REM followed by text
        if stripped.lower().startswith("rem"):
            # Strip the 'rem' prefix and optional apostrophe
            text = stripped[3:].lstrip(" '")
            if text:
                comment_lines.append(text)
        else:
            break  # Non-comment line ends the header block

    return " ".join(comment_lines)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pdfminer + manual conversion | pymupdf4llm `to_markdown()` | 2024 (v0.1.0) | Single function call replaces hundreds of lines of layout detection |
| pdf4llm (deprecated alias) | pymupdf4llm (canonical name) | 2024 | Same package, renamed for clarity |
| Custom YAML parsing for frontmatter | python-frontmatter 1.1.0 | Stable since 2023 | Standard library, no changes needed |
| Node.js MDX compilation for Python | Regex-based JSX stripping | N/A | For content extraction (not rendering), regex is sufficient and avoids Node.js dependency |

**Deprecated/outdated:**
- `pdf4llm`: Old alias for `pymupdf4llm`. Still works but PyPI page redirects to pymupdf4llm.
- PyMuPDF's `page.get_text("text")`: Outputs raw text without structure. Use pymupdf4llm instead for markdown.
- WordPress REST API for content access: Decision explicitly locks to web crawl approach; do not use `/wp-json/wp/v2/posts`.

## PDF-Specific Analysis

### GuideToGuiProgrammingInBBj.pdf Characteristics
From examining the actual PDF (47 pages, 1.4MB):

**Structure:**
- Page 1: Full table of contents with hyperlinks to sections
- Pages 2-11: Conceptual content (Introduction, Historical Background, GUI concepts, Event Driven Programming, BBjSysGui Object, Callbacks, Custom Objects)
- Pages 12-33: Sample programs (7 complete code examples with explanations)
- Pages 34-39: AppBuilder/Barista tutorials (screenshots + step instructions)
- Pages 40-47: Barista integration (screenshots + workflow)

**Content types present:**
- Prose text (historical background, concepts)
- Code blocks (BBj source code -- PRINT, OPEN, SYSGUI commands, class definitions)
- Tables (event codes table on page 8, mnemonic vs object comparison on page 9, term definitions on page 3)
- Screenshots/images (pages 15-16, 34-47 -- GUI forms, IDE screenshots)
- Hyperlinks (TOC links, "Back to top" links, external references)

**Generation tagging implications:**
- Pages 1-9: Mixed content (character, GUI, general concepts) -- tagger should classify per section
- Pages 10-11: BBj custom objects -- `bbj_gui` generation
- Pages 12-33: Sample code -- mixed generations (character CUI through GUI OO)
- Pages 34-47: Barista/AppBuilder content -- `bbj_gui` (or potentially `all`)

**Recommended granularity:** Split at major section headings (## level). The PDF has ~15 major sections which will yield ~15 Documents, each further split into chunks by the existing chunker.

## WordPress-Specific Analysis

### Advantage Articles (basis.cloud/advantage-index/)
- WordPress + Astra theme + LearnPress LMS plugin
- Article index page may use dynamic loading (AJAX)
- Articles span many years (2002-2024+) across 6 categories
- Some older articles are PDFs on `documentation.basis.cloud/advantage/` (separate domain)
- Content is text-heavy with occasional code examples
- Boilerplate: site header, navigation, breadcrumbs, footer, sidebar widgets

### Knowledge Base (basis.cloud/knowledge-base/)
- WordPress + ECKB (Echo Knowledge Base) plugin
- Article URLs follow pattern: `/knowledge-base/kb{number}/` (e.g., `kb01069`, `kb01083`)
- ECKB uses 3-column grid: `#eckb-article-body` with `grid-template-columns: 20% 60% 20%`
- Main content is in the center column
- Articles have metadata: author, date, categories (e.g., "BBj" category)
- Lessons are standalone (no course hierarchy per user decision)

### Crawl Strategy for Both Sites
1. Fetch index page, extract all article links
2. If index page yields no links (JS rendering), fall back to sitemap.xml or WP REST API for URL discovery only
3. Fetch each article page individually with rate limiting
4. Strip WordPress chrome, extract content from appropriate container
5. Convert HTML to markdown using existing `_html_to_markdown()`

## MDX-Specific Analysis

### DWC-Course Repository Content
From examining the repo (github.com/BasisHub/DWC-Course):

**Structure:**
- `docs/` contains 12 numbered chapter directories + 4 standalone files
- Files are `.md` and `.mdx` format (Docusaurus supports both)
- `samples/` contains BBj source code examples (handled by BBj source parser)

**Frontmatter fields observed:**
- `sidebar_position: <int>` -- ordering in sidebar
- `title: "<string>"` -- page title
- `slug: "/<path>"` -- URL slug (optional)
- `hide_table_of_contents: true|false` -- display flag (optional)

**Relevant fields for Document model:**
- `title` -> `Document.title`
- `sidebar_position` -> `Document.metadata["sidebar_position"]` (for ordering)
- `slug` -> can inform `Document.source_url`

**JSX components observed:**
- Self-closing (strip entirely): `<Hero />`, `<HomepageFeatures />`, `<ChapterCards />`
- Wrapper with content (strip tags, keep text): `<Link to="...">text</Link>`
- HTML-in-MDX (strip className, keep content): `<div className="text--center" style={{...}}>...</div>`
- Import statements: `import X from '@site/src/components/X'` (strip entirely)
- Mermaid code blocks: ````mermaid ... ``` `` (keep as-is, these are text content)

**Uniform tagging:** All DWC-Course content tagged as `dwc` generation (user decision). No per-file tagger needed.

## Open Questions

1. **Advantage article URL discovery**
   - What we know: The index page at `/advantage-index/` may dynamically load article links
   - What's unclear: Whether `httpx.get()` of the index page returns article links in the raw HTML or if they are AJAX-loaded
   - Recommendation: Implement with HTML parsing first; add sitemap.xml fallback (`/sitemap.xml` or `/post-sitemap.xml`) if zero URLs found. Some older articles live as PDFs on `documentation.basis.cloud/advantage/` which is a different domain -- these should be out of scope for this parser.

2. **BBj source file locations**
   - What we know: Files come from "mixed locations" (BBj installation samples + DWC-Course samples/ dir + other repos)
   - What's unclear: The exact set of directories/files to process
   - Recommendation: Make the parser accept a list of directories/file paths via configuration. DWC-Course `samples/` directory is a known starting point.

3. **pymupdf4llm table handling for this PDF**
   - What we know: Page 8-9 of the PDF contains tables (event codes, mnemonic comparison)
   - What's unclear: Whether `table_strategy="lines_strict"` correctly detects these specific tables
   - Recommendation: Test with a quick prototype. If tables are missed, try `table_strategy="lines"` or `"text"`.

4. **Pipeline integration for non-Flare parsers**
   - What we know: `run_pipeline()` calls `_apply_intelligence()` which assumes Flare content paths
   - What's unclear: Cleanest way to bypass Flare-specific intelligence for new parser types
   - Recommendation: Have parsers pre-populate `generations`, `doc_type`, and `context_header` on Documents. Add a guard in pipeline to skip intelligence if these are already set. The simplest signal: check if `doc.doc_type != "placeholder"` or create a new sentinel value.

## Sources

### Primary (HIGH confidence)
- [pymupdf4llm PyPI](https://pypi.org/project/pymupdf4llm/) - Version 0.2.9 confirmed, release date Jan 10, 2026
- [pymupdf4llm API documentation](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html) - Full `to_markdown()` signature with all parameters
- [pymupdf4llm overview](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/) - TocHeaders, IdentifyHeaders, page_chunks documentation
- [python-frontmatter PyPI](https://pypi.org/project/python-frontmatter/) - Version 1.1.0, 111K weekly downloads
- [python-frontmatter docs](https://python-frontmatter.readthedocs.io/) - API reference and usage examples
- Existing codebase: `parsers/__init__.py`, `web_crawl.py`, `pipeline.py`, `models.py`, `intelligence/` -- verified by reading source files
- GuideToGuiProgrammingInBBj.pdf -- read directly (47 pages, full content analyzed)
- [DWC-Course GitHub repo](https://github.com/BasisHub/DWC-Course) -- structure and sample files verified via WebFetch

### Secondary (MEDIUM confidence)
- [basis.cloud/knowledge-base/kb01069/](https://basis.cloud/knowledge-base/kb01069/) - Knowledge Base page structure analyzed (ECKB plugin identified)
- [basis.cloud/knowledge-base/kb01083/](https://basis.cloud/knowledge-base/kb01083/) - KB HTML selectors confirmed (#eckb-article-body grid layout)
- [basis.cloud/advantage-index/](https://basis.cloud/advantage-index/) - Advantage index page structure analyzed (Astra + LearnPress themes)
- DWC-Course `docs/index.md` raw content -- frontmatter fields and JSX patterns confirmed

### Tertiary (LOW confidence)
- WordPress article URL discovery approach -- actual link availability in raw HTML unverified (may require sitemap fallback)
- pymupdf4llm `TocHeaders` availability for this specific PDF -- PDF internal TOC metadata not yet confirmed (needs prototype test)
- Older Advantage articles on documentation.basis.cloud/advantage/ -- different domain, may be PDF format only

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified via PyPI and official docs with current versions
- Architecture: HIGH - Based on deep analysis of existing codebase patterns (DocumentParser protocol, pipeline, intelligence)
- Pitfalls: HIGH/MEDIUM - PDF and MDX pitfalls verified via docs; WordPress pitfalls identified from HTML analysis but article discovery needs runtime validation
- Code examples: HIGH - pymupdf4llm API verified; existing codebase patterns directly referenced

**Research date:** 2026-02-01
**Valid until:** 2026-03-01 (30 days -- all libraries are stable)
