# Architecture Research: RAG Ingestion Sub-Project

**Milestone:** v1.2 -- RAG Getting Started & Ingestion Pipeline
**Researched:** 2026-01-31
**Confidence:** HIGH (directory structure, data flow) / MEDIUM (library versions, embedding model choice)

> **Supersedes:** Previous ARCHITECTURE.md covered the Docusaurus site structure (v1.0). That architecture is now built and deployed. This document covers the new `rag-ingestion/` Python sub-project and its integration with the existing repo.

---

## 1. Repo-Level Integration

### Current Repo Structure (Before)

```
bbj-ai-strategy/
├── docs/                       # Docusaurus content (7 chapters)
│   └── 06-rag-database/
│       ├── _category_.json
│       └── index.md            # Strategic RAG design (existing)
├── src/                        # Docusaurus React components
├── .planning/                  # Project management
├── .github/workflows/
│   └── deploy.yml              # GitHub Pages (Node.js only)
├── docusaurus.config.ts
├── package.json
└── ...
```

### Target Repo Structure (After)

```
bbj-ai-strategy/
├── docs/
│   └── 06-rag-database/
│       ├── _category_.json
│       ├── index.md            # Strategic RAG design (existing, unchanged)
│       └── getting-started.md  # NEW: ingestion runbook linking to rag-ingestion/
├── rag-ingestion/              # NEW: Python sub-project (entire directory)
│   ├── pyproject.toml          # Project metadata, dependencies
│   ├── README.md               # Setup/run instructions
│   ├── .python-version         # Python version pin (3.12)
│   ├── config/
│   │   ├── sources.toml        # Source URLs, paths, crawl settings
│   │   └── sources.example.toml # Template without secrets/local paths
│   ├── src/
│   │   └── rag_ingestion/
│   │       ├── __init__.py
│   │       ├── cli.py          # Entry point: orchestrates full pipeline
│   │       ├── models.py       # Pydantic data models (Document, Chunk, etc.)
│   │       ├── parsers/
│   │       │   ├── __init__.py
│   │       │   ├── base.py     # Abstract parser interface
│   │       │   ├── flare.py    # MadCap Flare XHTML parser
│   │       │   ├── pdf.py      # PDF text extraction (PyMuPDF)
│   │       │   ├── wordpress.py # WordPress/Advantage/KB HTML parser
│   │       │   ├── docusaurus.py # Docusaurus MDX parser (DWC-Course)
│   │       │   └── bbj_code.py # BBj source code parser
│   │       ├── pipeline/
│   │       │   ├── __init__.py
│   │       │   ├── chunker.py  # Document-type-aware chunking
│   │       │   ├── tagger.py   # Generation tagging logic
│   │       │   └── embedder.py # Embedding generation
│   │       ├── storage/
│   │       │   ├── __init__.py
│   │       │   ├── schema.sql  # pgvector table definitions
│   │       │   ├── db.py       # Database connection + operations
│   │       │   └── migrate.py  # Schema creation/migration
│   │       └── utils/
│   │           ├── __init__.py
│   │           ├── fetcher.py  # HTTP client for crawling
│   │           └── text.py     # Text cleaning, normalization
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_parsers/
│   │   │   └── ...
│   │   ├── test_pipeline/
│   │   │   └── ...
│   │   └── fixtures/           # Sample XHTML, PDF, HTML, MDX files
│   │       └── ...
│   └── scripts/
│       ├── setup_db.sh         # Create PostgreSQL database + enable pgvector
│       └── run_pipeline.sh     # Convenience wrapper around cli.py
├── src/                        # Docusaurus (unchanged)
├── .gitignore                  # MODIFIED: add Python patterns
├── ...
```

### Key Integration Points

| Integration Point | What Changes | Why |
|---|---|---|
| `.gitignore` | Add `__pycache__/`, `*.pyc`, `.venv/`, `rag-ingestion/.venv/`, `uv.lock` (if not committed) | Prevent Python artifacts from polluting the repo |
| `docs/06-rag-database/getting-started.md` | NEW file in existing Docusaurus docs | Links to scripts and config files in `rag-ingestion/` |
| `deploy.yml` | **No change needed** | GitHub Actions only builds `npm run build` from repo root; `rag-ingestion/` is ignored by Docusaurus build |
| `package.json` | **No change needed** | Node.js project is unaware of Python sub-project |
| `docusaurus.config.ts` | **No change needed** | `onBrokenLinks: 'throw'` does not check links to non-docs files |

### Boundary Rule: Two Completely Independent Build Toolchains

The Docusaurus site and the Python ingestion project share a git repository but share zero build dependencies. They have different package managers (npm vs uv), different runtimes (Node.js vs Python), and different output artifacts (static HTML vs database records). Neither project's build or test commands need to know about the other.

The only connection is **documentation**: the `getting-started.md` doc page references files in `rag-ingestion/` via GitHub links (absolute URLs to the repo), not relative filesystem paths. This is intentional -- Docusaurus cannot resolve links to files outside the `docs/` directory, and using absolute GitHub URLs (`https://github.com/StephanWald/bbj-ai-strategy/tree/main/rag-ingestion/...`) ensures links work both in the deployed site and when reading the source on GitHub.

---

## 2. Python Sub-Project Architecture

### Package Management: uv

**Recommendation: Use uv** as the Python package manager. uv is the current best practice for Python project management (as of January 2026), replacing pip/pip-tools/poetry for new projects. It provides fast dependency resolution, a lockfile (`uv.lock`), and a simple `pyproject.toml`-based workflow.

**Why uv over poetry or pip:**
- 10-100x faster dependency resolution than pip
- Native `pyproject.toml` support (no separate `requirements.txt` needed)
- Built-in virtual environment management (`uv run` auto-creates `.venv`)
- Single command to reproduce exact environment (`uv sync`)
- Active development by Astral (same team as Ruff)

**Confidence:** HIGH -- uv is the consensus recommendation for new Python projects in 2026.

### pyproject.toml Structure

```toml
[project]
name = "rag-ingestion"
version = "0.1.0"
description = "RAG ingestion pipeline for BBj documentation"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    # Parsing
    "beautifulsoup4>=4.12",    # HTML/XHTML parsing
    "lxml>=5.0",               # Fast XML parser backend for BS4
    "pymupdf>=1.25",           # PDF text extraction (PyMuPDF/fitz)
    "markdown-it-py>=3.0",     # MDX/Markdown parsing

    # Pipeline
    "pydantic>=2.0",           # Data models and validation
    "sentence-transformers>=3.0", # Embedding model loading + inference

    # Storage
    "psycopg[binary]>=3.1",    # PostgreSQL driver (psycopg3)
    "pgvector>=0.3",           # pgvector type support for psycopg

    # Utilities
    "httpx>=0.27",             # Async-capable HTTP client for crawling
    "tomli>=2.0; python_version < '3.11'",  # TOML config parsing (stdlib in 3.11+)
    "rich>=13.0",              # Terminal output formatting
    "click>=8.1",              # CLI framework
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.8",
]

[project.scripts]
rag-ingest = "rag_ingestion.cli:main"

[tool.ruff]
target-version = "py312"
line-length = 100
```

### Why These Libraries

| Library | Purpose | Why This One |
|---|---|---|
| **BeautifulSoup4 + lxml** | HTML/XHTML parsing | BS4 is the standard for HTML parsing in Python; lxml backend is fastest. Flare XHTML and WordPress HTML are both standard HTML -- no special parser needed. |
| **PyMuPDF (fitz)** | PDF text extraction | Fastest Python PDF library (benchmarked at 0.12s vs pdfplumber's 0.10s for simple extraction, but 5x faster for complex docs). Has `pymupdf4llm` variant optimized for RAG/LLM workflows. AGPL license is acceptable for internal tooling. |
| **markdown-it-py** | Markdown/MDX parsing | Python port of markdown-it (the standard JS markdown parser). Handles MDX frontmatter and content extraction without needing Node.js. |
| **Pydantic v2** | Data models | Type-safe models for Document, Chunk, EmbeddedChunk. Validates generation labels, ensures schema consistency. |
| **sentence-transformers** | Embedding generation | Standard Python framework for local embedding models. Supports BGE-M3, all-MiniLM, and any HuggingFace embedding model. |
| **psycopg3** | PostgreSQL driver | Modern Python PostgreSQL driver with native async support. Chosen over asyncpg because: (a) ingestion is a batch job, not a web server -- async throughput is not the bottleneck; (b) psycopg3 has better ergonomics (Row Factories, Pydantic integration); (c) better pgvector type registration. |
| **pgvector** | Vector type support | Provides `register_vector()` for psycopg3, enabling native `vector` column operations. |
| **httpx** | HTTP client | Modern Python HTTP client with async support. Better API than `requests` for crawling (connection pooling, timeouts, retries). |
| **click** | CLI framework | Standard Python CLI library. Lightweight, composable. Better than argparse for multi-command CLIs. |
| **rich** | Terminal output | Progress bars, tables, colored output for pipeline status reporting. |

**Confidence:** HIGH for BS4/lxml/PyMuPDF/psycopg3/Pydantic (established, stable libraries). MEDIUM for sentence-transformers version (active development, API may shift).

---

## 3. Data Flow: End-to-End Pipeline

```
                    ┌──────────────────────────────────────────────────────────┐
                    │                    SOURCE ACQUISITION                     │
                    │                                                          │
                    │  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌─────────┐ │
                    │  │  Flare   │  │  PDFs   │  │WordPress │  │  DWC    │ │
                    │  │  XHTML   │  │         │  │  HTML    │  │ Course  │ │
                    │  └────┬─────┘  └────┬────┘  └────┬─────┘  └────┬────┘ │
                    │       │             │            │              │       │
                    │       ▼             ▼            ▼              ▼       │
                    │  ┌────────────────────────────────────────────────────┐ │
                    │  │              Source-Specific Parsers               │ │
                    │  │  flare.py | pdf.py | wordpress.py | docusaurus.py │ │
                    │  └──────────────────────┬───────────────────────────┘ │
                    └──────────────────────────┼────────────────────────────┘
                                               │
                                               ▼  List[Document]
                    ┌──────────────────────────────────────────────────────────┐
                    │                    ENRICHMENT PIPELINE                    │
                    │                                                          │
                    │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
                    │  │  Generation │  │  Doc-Type    │  │   Chunking     │ │
                    │  │  Tagger     │──▶│  Classifier  │──▶│  (type-aware)  │ │
                    │  └─────────────┘  └──────────────┘  └───────┬────────┘ │
                    │                                              │          │
                    │                                              ▼          │
                    │                                    List[Chunk]          │
                    └──────────────────────────────────────┼──────────────────┘
                                                           │
                                                           ▼
                    ┌──────────────────────────────────────────────────────────┐
                    │                    EMBEDDING + STORAGE                    │
                    │                                                          │
                    │  ┌─────────────┐         ┌───────────────────────────┐  │
                    │  │  Embedding  │────────▶│  PostgreSQL + pgvector    │  │
                    │  │  Model      │         │  (doc_chunks table)       │  │
                    │  └─────────────┘         └───────────────────────────┘  │
                    └──────────────────────────────────────────────────────────┘
```

### Stage 1: Source Acquisition

Each parser implements a common interface and produces a list of `Document` objects:

```python
# parsers/base.py
from abc import ABC, abstractmethod
from rag_ingestion.models import Document

class BaseParser(ABC):
    @abstractmethod
    def parse(self, source_config: dict) -> list[Document]:
        """Parse a source and return a list of Documents."""
        ...
```

Every parser is responsible for:
1. Fetching or reading raw content (from filesystem or URL)
2. Extracting text content, stripping irrelevant markup
3. Extracting metadata (title, source URL, file path)
4. Returning `Document` objects with raw text and metadata

Parsers are NOT responsible for:
- Chunking (that is the pipeline's job)
- Generation tagging (that is the tagger's job)
- Embedding (that is the embedder's job)

### Stage 2: Enrichment Pipeline

The enrichment pipeline takes `Document` objects and produces `Chunk` objects:

1. **Generation Tagger** -- Assigns generation labels (`all`, `character`, `vpro5`, `bbj-gui`, `dwc`) based on content signals (API names, syntax patterns, file paths). Uses the same schema defined in Chapter 6 of the docs site.

2. **Document-Type Classifier** -- Classifies each document as `api-reference`, `concept`, `example`, `migration`, `language-reference`, `best-practice`, or `version-note`. This classification drives chunk size selection.

3. **Chunker** -- Splits documents into chunks using document-type-aware sizes (200-400 tokens for API refs, 400-600 for concepts, etc.). Prepends contextual headers. Manages overlap between adjacent chunks.

### Stage 3: Embedding + Storage

1. **Embedder** -- Loads a sentence-transformers model and generates vector embeddings for each chunk's text (with contextual header prepended).

2. **Storage** -- Upserts chunks with embeddings into PostgreSQL/pgvector. Each chunk is stored with its text, embedding vector, generation labels, document type, source metadata, and contextual header.

---

## 4. Data Models

```python
# models.py
from pydantic import BaseModel, Field
from enum import Enum

class SourceType(str, Enum):
    FLARE = "flare"
    PDF = "pdf"
    WORDPRESS = "wordpress"
    DOCUSAURUS = "docusaurus"
    BBJ_CODE = "bbj_code"

class Generation(str, Enum):
    ALL = "all"
    CHARACTER = "character"
    VPRO5 = "vpro5"
    BBJ_GUI = "bbj-gui"
    DWC = "dwc"

class DocType(str, Enum):
    API_REFERENCE = "api-reference"
    CONCEPT = "concept"
    EXAMPLE = "example"
    MIGRATION = "migration"
    LANGUAGE_REFERENCE = "language-reference"
    BEST_PRACTICE = "best-practice"
    VERSION_NOTE = "version-note"

class Document(BaseModel):
    """A parsed document before chunking."""
    source_type: SourceType
    source_url: str | None = None
    source_path: str | None = None
    title: str
    body: str                          # Full extracted text
    headings: list[str] = Field(default_factory=list)  # Section hierarchy
    metadata: dict = Field(default_factory=dict)        # Source-specific metadata

class Chunk(BaseModel):
    """A chunk ready for embedding."""
    document_title: str
    source_type: SourceType
    source_url: str | None = None
    doc_type: DocType
    generation: list[Generation]
    contextual_header: str             # "Section > Subsection > ..."
    content: str                       # The chunk text
    chunk_index: int                   # Position within parent document
    token_count: int
    metadata: dict = Field(default_factory=dict)

class EmbeddedChunk(Chunk):
    """A chunk with its embedding vector."""
    embedding: list[float]
    embedding_model: str               # Model name for provenance
    embedding_dim: int                 # Vector dimension
```

---

## 5. Database Schema

```sql
-- storage/schema.sql

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main chunks table
CREATE TABLE IF NOT EXISTS doc_chunks (
    id              BIGSERIAL PRIMARY KEY,

    -- Content
    content         TEXT NOT NULL,
    contextual_header TEXT NOT NULL DEFAULT '',

    -- Metadata
    document_title  TEXT NOT NULL,
    source_type     VARCHAR(20) NOT NULL,  -- flare, pdf, wordpress, docusaurus, bbj_code
    source_url      TEXT,
    doc_type        VARCHAR(30) NOT NULL,  -- api-reference, concept, etc.
    generation      TEXT[] NOT NULL,        -- ARRAY of generation labels
    chunk_index     INTEGER NOT NULL DEFAULT 0,
    token_count     INTEGER NOT NULL DEFAULT 0,
    metadata        JSONB DEFAULT '{}',

    -- Embedding
    embedding       vector(768),           -- Dimension matches chosen model
    embedding_model VARCHAR(100),

    -- Full-text search (BM25 via tsvector)
    search_vector   tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(contextual_header, '') || ' ' || content)
    ) STORED,

    -- Timestamps
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity search index (HNSW for <50K vectors)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON doc_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_chunks_search
    ON doc_chunks USING gin (search_vector);

-- Generation filter index (for WHERE generation @> ARRAY['dwc'])
CREATE INDEX IF NOT EXISTS idx_chunks_generation
    ON doc_chunks USING gin (generation);

-- Source type filter index
CREATE INDEX IF NOT EXISTS idx_chunks_source_type
    ON doc_chunks (source_type);

-- Document type filter index
CREATE INDEX IF NOT EXISTS idx_chunks_doc_type
    ON doc_chunks (doc_type);

-- Deduplication: unique constraint on content hash to prevent duplicate chunks
CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_content_hash
    ON doc_chunks (md5(content || contextual_header));
```

### Schema Design Rationale

**Single table, not document + chunks:** At the scale of BBj documentation (<50K chunks total), a single denormalized table is simpler and faster than a normalized two-table design. Every query only needs one table. The `document_title` and `source_url` fields are duplicated across chunks from the same document -- this is intentional and acceptable at this scale.

**`generation` as TEXT[]:** PostgreSQL arrays with GIN indexing support efficient containment queries (`WHERE generation @> ARRAY['dwc']`). This is more performant than a junction table for this use case and matches the data model in Chapter 6 where a chunk can have multiple generation labels.

**`search_vector` as GENERATED column:** The tsvector is automatically maintained by PostgreSQL when content is inserted or updated. No application-level code needed to keep it in sync.

**`vector(768)` dimension:** Matches BGE-base-en-v1.5 (768 dimensions) and many other common embedding models. If a different model with different dimensions is chosen, this must be updated before initial data load. The dimension cannot be changed after data is loaded without recreating the column.

**HNSW over IVFFlat:** HNSW provides better recall at low latency for datasets under 100K vectors. IVFFlat requires training on existing data, which complicates initial setup. HNSW works immediately after index creation.

**Confidence:** HIGH for schema structure. MEDIUM for vector dimension (depends on final embedding model choice).

---

## 6. Source-Specific Parser Architecture

### Source 1: MadCap Flare XHTML (Primary Source)

**Input:** Clean XHTML files from Flare export OR crawled HTML from `documentation.basis.cloud`

**Two ingestion paths:**

| Path | Input | When to Use |
|---|---|---|
| **Flare export** | Directory of `.htm` files from Clean XHTML build target | Engineer has Flare project access |
| **Crawl fallback** | HTML pages from `documentation.basis.cloud/BASISHelp/WebHelp/` | No Flare access; uses live site |

**Parser approach (both paths):**
- BeautifulSoup4 with lxml backend
- Extract `<title>` and `<body>` content
- Strip `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>` elements
- Extract heading hierarchy (`<h1>` through `<h4>`) for contextual headers
- Preserve code blocks (`<pre>`, `<code>`) as-is for BBj syntax detection

**Flare-specific considerations:**
- Clean XHTML strips MadCap namespace tags (`mc:*`, `data-mc-*`) -- no special handling needed
- Topic hierarchy is NOT in the files themselves -- it comes from TOC files (`.fltoc`) in the Flare project. For the crawl path, hierarchy must be inferred from URL paths and heading structure.
- Custom `<script>` tags are not auto-removed in Clean XHTML -- parser must strip them.
- The live site at documentation.basis.cloud is dynamically generated (not static files), meaning crawling requires following navigation links, not just directory listing.

**Build order rationale:** Implement first. This is the primary corpus and the most complex parser. Getting Flare parsing right validates the entire pipeline architecture.

**Complexity:** MEDIUM-HIGH (two paths, hierarchy reconstruction, dynamic site crawling)

### Source 2: Standalone PDFs

**Input:** PDF files linked from documentation.basis.cloud (e.g., `GuideToGuiProgrammingInBBj.pdf` already in repo root)

**Parser approach:**
- PyMuPDF (`fitz`) for text extraction
- Use `pymupdf4llm` variant for markdown-formatted output (preserves headings, lists, code blocks)
- Extract page-level metadata (page numbers for citation)
- Detect code blocks by indentation and font characteristics

**PDF-specific considerations:**
- PDFs vary widely in structure. The GUI programming guide is well-structured with clear headings. Other PDFs may be less structured.
- OCR is NOT needed -- BBj documentation PDFs are text-based, not scanned images.
- Tables in PDFs need special handling -- PyMuPDF's table detection is good but not perfect.

**Build order rationale:** Implement second. A PDF parser with PyMuPDF is straightforward and provides immediate value -- the `GuideToGuiProgrammingInBBj.pdf` is already in the repo and is an authoritative reference.

**Complexity:** LOW-MEDIUM (PyMuPDF handles most of the work; main challenge is structure detection)

### Source 3: WordPress HTML (Advantage Articles + Knowledge Base)

**Input:** HTML pages from two WordPress-based sites:
- `basis.cloud/advantage-index/` -- Advantage magazine articles (static article index)
- `basis.cloud/knowledge-base/` -- Knowledge Base articles (WordPress + LearnPress LMS)

**Parser approach:**
- httpx to fetch pages
- BeautifulSoup4 to extract article content from WordPress markup
- Strip WordPress chrome (navigation, sidebars, footers, comments)
- Extract article metadata from WordPress structured data (JSON-LD, Open Graph tags)

**WordPress-specific considerations:**
- The Knowledge Base uses LearnPress LMS (v4.3.1 confirmed via page metadata) with AJAX content loading. Direct HTML fetching may get incomplete content if articles load dynamically.
- Try the WordPress REST API first: `basis.cloud/wp-json/wp/v2/posts` for articles, and `basis.cloud/wp-json/lp/v1/` for LearnPress content. REST API returns structured JSON, avoiding HTML parsing entirely.
- Advantage articles are older (2014-2018 visible dates) and likely static HTML -- simpler to parse.
- Article categorization (Partnership, Language/Interpreter, Database Management, Development Tools, etc.) maps to metadata, not generation tags.

**Build order rationale:** Implement third. WordPress REST API (if available) makes this simpler than expected. If REST API is not available, falls back to HTML scraping which is well-understood territory.

**Complexity:** LOW (if REST API works) to MEDIUM (if HTML scraping needed)

### Source 4: Docusaurus MDX (DWC-Course)

**Input:** MDX files from `github.com/BasisHub/DWC-Course` repository

**Parser approach:**
- Clone or fetch raw MDX files from GitHub (use GitHub API or raw URLs)
- Parse MDX with markdown-it-py: extract frontmatter (YAML), heading structure, text content
- Strip JSX components (Tabs, TabItems, admonitions) down to their text content
- Extract BBj code blocks from fenced code sections
- Also parse accompanying BBj sample files from `samples/` directory

**Docusaurus-specific considerations:**
- MDX files contain JSX imports (`import Tabs from '@theme/Tabs'`) that are not valid Markdown. The parser must strip or handle these gracefully.
- Frontmatter contains metadata (`sidebar_position`, `title`, `description`) -- extract for document metadata.
- The DWC-Course is a Docusaurus site with the same stack as this project. Content is 75.2% TypeScript, 21.8% CSS, 3.0% MDX -- only the MDX and BBj sample files are relevant for RAG.

**Build order rationale:** Implement fourth. This source is well-structured (MDX is predictable), but the volume is small (3% MDX in a course-focused repo). Lower priority than the primary documentation sources.

**Complexity:** LOW (MDX is structured and predictable; GitHub raw file access is straightforward)

### Source 5: BBj Source Code

**Input:** BBj source files (`.bbj`, `.bbjt`, `.txt` sample programs)

**Parser approach:**
- Read BBj source files as plain text
- Extract comments (REM statements, `!` line comments) as natural language content
- Extract function/subroutine signatures for API-level documentation
- Use file path and naming conventions for metadata
- Code itself becomes content -- entire functions or classes as chunks

**BBj-code-specific considerations:**
- BBj code is the most domain-specific source. The parser needs BBj syntax awareness (unlike the others which parse standard formats).
- Generation tagging is critical here: code files often target a specific generation (character UI patterns vs. DWC patterns).
- Sample programs from the GUI programming guide PDF (cust-cui.txt, cust-gui.txt, cust-bbj.txt, cust-obj.txt) are particularly valuable as they demonstrate the same application across generations.

**Build order rationale:** Implement last. Requires the most domain-specific knowledge. Benefits most from having the other parsers working first (to validate the pipeline end-to-end with simpler sources).

**Complexity:** MEDIUM (requires BBj syntax awareness for meaningful parsing)

---

## 7. Configuration Architecture

### Source Configuration File

```toml
# config/sources.toml

[flare]
# Path A: Clean XHTML export directory (if you have Flare project access)
export_dir = "/path/to/flare/CleanXHTML/Output"

# Path B: Crawl from live site (fallback)
base_url = "https://documentation.basis.cloud/BASISHelp/WebHelp/"
crawl_delay_seconds = 1.0
max_pages = 5000

# Which path to use
mode = "export"  # "export" or "crawl"

[pdf]
# List of PDF files or URLs to ingest
files = [
    { path = "../GuideToGuiProgrammingInBBj.pdf", title = "Guide to GUI Programming in BBj" },
]
# URLs to PDF files that should be downloaded and parsed
urls = []

[wordpress]
# Advantage articles
[wordpress.advantage]
base_url = "https://basis.cloud"
index_path = "/advantage-index/"
api_endpoint = "/wp-json/wp/v2/posts"
use_api = true

# Knowledge Base
[wordpress.knowledge_base]
base_url = "https://basis.cloud"
index_path = "/knowledge-base/"
api_endpoint = "/wp-json/lp/v1/"
use_api = true

[docusaurus]
# DWC-Course repository
repo_url = "https://github.com/BasisHub/DWC-Course"
docs_path = "docs/"
samples_path = "samples/"
branch = "main"

[bbj_code]
# Directories containing BBj source files
paths = []
extensions = [".bbj", ".bbjt", ".txt"]

[pipeline]
# Embedding model (sentence-transformers compatible)
embedding_model = "BAAI/bge-base-en-v1.5"
embedding_dimension = 768

# Chunking defaults (overridden by doc_type)
default_chunk_size = 400
default_chunk_overlap = 50

[database]
host = "localhost"
port = 5432
database = "bbj_rag"
user = "postgres"
# password sourced from environment variable PGPASSWORD
```

### Environment Variables (Not in Config File)

```bash
# Database password -- never in source control
PGPASSWORD=your_password_here

# Optional: HuggingFace token for gated models
HF_TOKEN=hf_xxx
```

### Config Design Rationale

**TOML over YAML or JSON:** TOML is the Python ecosystem standard for configuration (pyproject.toml, Ruff, etc.). It is more readable than JSON and less error-prone than YAML (no ambiguous type coercion). Python 3.11+ includes `tomllib` in the standard library.

**Separate config from code:** Source URLs, file paths, and database credentials change between environments (developer laptop vs. CI vs. production). Keeping them in `config/sources.toml` with a `.example` template makes the project portable.

**`mode` field for Flare:** The dual ingestion path (export vs. crawl) is a first-class config option, not a code branch. Both paths produce the same `Document` objects.

---

## 8. Embedding Model Selection

**Recommendation: Start with `BAAI/bge-base-en-v1.5`**

| Criterion | BGE-base-en-v1.5 | BGE-M3 | all-MiniLM-L6-v2 |
|---|---|---|---|
| Dimension | 768 | 1024 | 384 |
| Parameters | 109M | 568M | 22M |
| Sequence length | 512 tokens | 8192 tokens | 256 tokens |
| MTEB rank (retrieval) | Strong | Top tier | Good |
| Speed (CPU) | Fast | Slower | Fastest |
| Memory | ~500MB | ~2.5GB | ~100MB |
| Multilingual | English only | 100+ languages | English-focused |
| Self-hostable | Yes | Yes | Yes |

**Why BGE-base-en-v1.5 as starting point:**
- 768 dimensions is the sweet spot: good quality without excessive storage
- 512-token sequence length covers all chunk sizes in the pipeline (200-600 tokens)
- Fast enough for batch processing on CPU (no GPU required for <50K chunks)
- English-only is fine -- BBj documentation is exclusively English
- Well-tested with sentence-transformers framework
- Can upgrade to BGE-M3 later if longer context or better retrieval quality is needed

**When to reconsider:**
- If chunk sizes exceed 512 tokens, upgrade to BGE-M3 (8192 token context)
- If retrieval quality is insufficient, consider Qwen3-Embedding-0.6B or fine-tuned embeddings
- If processing speed is critical, consider all-MiniLM-L6-v2 (4x faster, lower quality)

**Confidence:** MEDIUM -- Embedding model landscape evolves quickly. BGE-base-en-v1.5 is a well-validated choice as of January 2026, but newer models may surpass it. The pipeline is designed to be model-agnostic (embedding model name is in config, not hardcoded).

---

## 9. Doc Page Integration

### How `getting-started.md` References `rag-ingestion/`

Docusaurus markdown files cannot resolve relative links to files outside the `docs/` directory. This is a documented limitation. The solution is to use absolute GitHub URLs.

**Pattern for linking to code files:**

```markdown
The pipeline configuration lives in
[`sources.toml`](https://github.com/StephanWald/bbj-ai-strategy/blob/main/rag-ingestion/config/sources.example.toml).

To set up the database schema, run the
[setup script](https://github.com/StephanWald/bbj-ai-strategy/blob/main/rag-ingestion/scripts/setup_db.sh).
```

**Pattern for showing code inline (copy, don't link):**

For key code snippets that the reader needs to see in the doc page itself, copy the relevant section into the markdown rather than linking. This keeps the doc page self-contained and avoids broken links if the code moves.

```markdown
The database schema uses pgvector for vector storage:

\`\`\`sql
CREATE TABLE doc_chunks (
    id              BIGSERIAL PRIMARY KEY,
    content         TEXT NOT NULL,
    embedding       vector(768),
    generation      TEXT[] NOT NULL,
    ...
);
\`\`\`

See the [full schema](https://github.com/StephanWald/bbj-ai-strategy/blob/main/rag-ingestion/src/rag_ingestion/storage/schema.sql) for all columns and indexes.
```

**What NOT to do:**
- Do not use relative paths like `../../rag-ingestion/config/sources.toml` -- Docusaurus will warn about broken links
- Do not try to import MDX from outside docs/ -- causes React hooks errors in monorepo setups
- Do not use `@site/../rag-ingestion/` syntax -- fragile and causes dependency issues

**Confidence:** HIGH -- Verified against Docusaurus documentation and known issues (#4039, #3672, Discussion #6460).

---

## 10. Suggested Build Order

The pipeline should be built incrementally, with each step producing testable output before moving to the next.

### Step 1: Scaffold + Models + Schema

Create the directory structure, Pydantic data models, and database schema. This establishes the contract that all subsequent code must conform to.

**Deliverables:**
- `rag-ingestion/` directory with `pyproject.toml`
- `src/rag_ingestion/models.py` with Document, Chunk, EmbeddedChunk
- `src/rag_ingestion/storage/schema.sql`
- `src/rag_ingestion/storage/db.py` (connection management)
- `src/rag_ingestion/storage/migrate.py` (create tables)
- `scripts/setup_db.sh`

**Testable:** `uv run rag-ingest setup-db` creates the database schema.

### Step 2: Flare Parser (Primary Source)

Implement the Flare XHTML parser (export path first, crawl path second). This is the highest-value parser and validates the full Document model.

**Deliverables:**
- `src/rag_ingestion/parsers/base.py`
- `src/rag_ingestion/parsers/flare.py`
- `tests/test_parsers/test_flare.py` with fixture XHTML files

**Testable:** Parser produces Document objects from sample XHTML files.

### Step 3: Chunker + Tagger

Implement the generation tagger and document-type-aware chunker. These are the core enrichment components that make this pipeline BBj-specific.

**Deliverables:**
- `src/rag_ingestion/pipeline/tagger.py`
- `src/rag_ingestion/pipeline/chunker.py`
- `tests/test_pipeline/test_chunker.py`
- `tests/test_pipeline/test_tagger.py`

**Testable:** Documents from Step 2 are correctly tagged and chunked.

### Step 4: Embedder + Storage

Add embedding generation and database insertion. This completes the end-to-end pipeline for one source type.

**Deliverables:**
- `src/rag_ingestion/pipeline/embedder.py`
- `src/rag_ingestion/cli.py` (orchestration)
- `config/sources.example.toml`

**Testable:** Full pipeline runs: Flare XHTML -> parse -> tag -> chunk -> embed -> store in pgvector. Can query chunks by vector similarity.

### Step 5: Additional Parsers

Add remaining parsers in order of value and complexity:

1. `pdf.py` -- PDF parser (already have a test file in repo root)
2. `wordpress.py` -- WordPress/Advantage/KB parser
3. `docusaurus.py` -- DWC-Course MDX parser
4. `bbj_code.py` -- BBj source code parser

Each parser follows the same interface and plugs into the existing pipeline.

### Step 6: Documentation Page

Write `docs/06-rag-database/getting-started.md` linking to the completed sub-project. This is last because it documents what was built.

**Confidence:** HIGH -- This build order follows the principle of validating the full pipeline end-to-end with one source before adding breadth.

---

## 11. Anti-Patterns to Avoid

### Anti-Pattern: LangChain/LlamaIndex for Everything

**Trap:** Using LangChain or LlamaIndex as the framework for the ingestion pipeline.

**Why bad for this project:** These frameworks are designed for retrieval + generation workflows (query time), not batch ingestion. They add heavyweight abstractions (chains, agents, retrievers) that are irrelevant for a batch ETL pipeline. The ingestion pipeline is a simple: parse -> enrich -> embed -> store workflow. Direct library usage (BeautifulSoup, PyMuPDF, sentence-transformers, psycopg3) is simpler, faster, and has fewer dependencies.

**Exception:** LangChain's Docusaurus document loader could be useful as a reference for the DWC-Course parser, but should not be used as a runtime dependency.

### Anti-Pattern: Async-First Architecture

**Trap:** Making the pipeline async throughout because "async is modern."

**Why bad for this project:** Ingestion is a batch job, not a web server. The bottleneck is embedding computation (CPU/GPU bound), not I/O. Adding `async`/`await` throughout the codebase adds complexity (event loops, async context managers, async database drivers) with negligible performance benefit. The only place async may help is the HTTP fetcher for crawling (many pages in parallel) -- use `httpx.AsyncClient` there and keep everything else synchronous.

### Anti-Pattern: Over-Abstracting the Parser Interface

**Trap:** Building a generic plugin system with registry, auto-discovery, and dynamic loading for 5 parsers.

**Why bad for this project:** Five parsers. Known at development time. A simple base class with explicit imports in `cli.py` is sufficient. A plugin system is justified at 20+ parsers with third-party contributors. At 5, it is overengineering.

### Anti-Pattern: Streaming/Incremental Embedding

**Trap:** Processing documents one-at-a-time through the entire pipeline.

**Why bad for this project:** Embedding models are fastest when processing batches (sentence-transformers' `encode()` method is optimized for batch input). Parse all documents first, chunk all documents, then embed all chunks in batches. This maximizes GPU/CPU utilization.

### Anti-Pattern: Separate Metadata Store

**Trap:** Using a separate database or service for chunk metadata while pgvector stores only vectors.

**Why bad for this project:** pgvector is PostgreSQL. PostgreSQL stores structured data beautifully. Put everything in one table: vectors, text, metadata, generation labels, tsvector for BM25. One query does vector search + metadata filtering. No cross-service joins, no consistency issues.

---

## 12. Files Modified in Existing Repo

### New Files

| File | Description |
|---|---|
| `rag-ingestion/` (entire directory) | Python sub-project with all contents described above |
| `docs/06-rag-database/getting-started.md` | New Docusaurus doc page under Chapter 6 |

### Modified Files

| File | Change | Reason |
|---|---|---|
| `.gitignore` | Add Python patterns (`__pycache__/`, `*.pyc`, `.venv/`, `rag-ingestion/.venv/`, `*.egg-info/`) | Prevent Python build artifacts from being committed |

### Unchanged Files

| File | Why Unchanged |
|---|---|
| `docusaurus.config.ts` | New doc page auto-discovered by autogenerated sidebar |
| `sidebars.ts` | Autogenerated sidebar picks up new `.md` files automatically |
| `package.json` | No new Node.js dependencies |
| `deploy.yml` | GitHub Actions workflow only builds Docusaurus, ignores `rag-ingestion/` |
| `_category_.json` (06-rag-database) | Existing config supports additional pages in the category |

---

## Sources

### Verified (HIGH confidence)
- [MadCap Flare Clean XHTML Output docs](https://help.madcapsoftware.com/flare2021r2/Content/Flare/Step4-Developing-Targets/Output-Types/Clean-XHTML/Clean-XHTML-Output.htm) -- Clean XHTML strips mc tags, namespaces, JavaScript
- [Docusaurus Markdown Links](https://docusaurus.io/docs/markdown-features/links) -- Cannot resolve links outside docs/ directory
- [Docusaurus Issue #4039](https://github.com/facebook/docusaurus/issues/4039) -- Confirmed: no cross-directory markdown link resolution
- [uv Project Docs](https://docs.astral.sh/uv/guides/projects/) -- pyproject.toml setup, dependency management
- [pgvector GitHub](https://github.com/pgvector/pgvector) -- HNSW index, vector operations
- [sentence-transformers PyPI](https://pypi.org/project/sentence-transformers/) -- Model loading, batch encoding
- [BGE-M3 HuggingFace](https://huggingface.co/BAAI/bge-m3) -- Model capabilities, dimensions

### Verified (MEDIUM confidence)
- [BentoML -- Best Open-Source Embedding Models 2026](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models) -- Embedding model comparison
- [Unstract -- Python PDF Libraries 2026](https://unstract.com/blog/evaluating-python-pdf-to-text-libraries/) -- PyMuPDF vs pdfplumber benchmarks
- [Instaclustr -- pgvector 2026 Guide](https://www.instaclustr.com/education/vector-database/pgvector-key-features-tutorial-and-pros-and-cons-2026-guide/) -- HNSW vs IVFFlat guidance
- [Psycopg3 vs asyncpg comparison](https://fernandoarteaga.dev/blog/psycopg-vs-asyncpg/) -- Driver comparison

### Observed (from fetching live sites)
- `documentation.basis.cloud` redirects to `/BASISHelp/WebHelp/index.htm` -- dynamically generated, not static Flare output
- `basis.cloud/knowledge-base/` uses LearnPress LMS v4.3.1, WordPress with Astra theme, has REST API at `/wp-json/lp/v1/`
- `basis.cloud/advantage-index/` is a curated article index organized by category (Partnership, Language, Database, etc.)
- `github.com/BasisHub/DWC-Course` is a Docusaurus site with MDX docs and BBj sample files

---

*Research completed: 2026-01-31*
*Scope: RAG ingestion sub-project architecture for v1.2 milestone*
