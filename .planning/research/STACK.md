# Technology Stack: RAG Ingestion Pipeline

**Project:** BBj AI Strategy -- RAG Ingestion Sub-Project (`rag-ingestion/`)
**Researched:** 2026-01-31
**Scope:** Python stack for parsing 5 source types, chunking, embedding, and storing in pgvector
**Overall confidence:** HIGH (all recommendations verified via current web sources)

---

## Recommended Stack

### Runtime & Package Management

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.12+ | Runtime | Current stable. Required by pymupdf4llm (>=3.10). 3.12 has best performance of the 3.x line. |
| uv | latest | Package/project manager | Fastest Python package manager (10-100x pip). Handles venv, lockfile, and dependency resolution. Preferred over pip+venv for new projects in 2026. |

**Project structure recommendation:** Use `pyproject.toml` with uv for dependency management. No `setup.py` or `requirements.txt`.

```toml
[project]
name = "rag-ingestion"
version = "0.1.0"
requires-python = ">=3.12"
```

---

### Source Type 1: MadCap Flare Clean XHTML

**Primary path:** Parse Clean XHTML export from Flare project (engineers have access).
**Fallback path:** Crawl live site at documentation.basis.cloud.

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| lxml | 5.x (latest) | XHTML/XML parsing | 11x faster than BeautifulSoup for XML. Native XPath support is essential for navigating Flare's namespace-heavy XHTML (`xmlns:MadCap`). Flare Clean XHTML is valid XML, so lxml's strict parser works perfectly. |
| beautifulsoup4 | 4.x (latest) | Fallback/convenience parsing | Use only if lxml's strict XML mode rejects malformed pages from the live site crawl. NOT needed for Clean XHTML export path. |

**Why lxml over BeautifulSoup:** Flare Clean XHTML is well-formed XML by definition (MadCap strips all proprietary tags in Clean XHTML mode). lxml's `etree.parse()` handles this natively with XPath for structured extraction. BeautifulSoup adds overhead and is designed for forgiving HTML parsing, which is unnecessary here.

**What Clean XHTML gives you:** All `mc:` tags, `data-mc-` attributes, MadCap-specific styles, keywords, concepts, and conditions are stripped. You get pure semantic XHTML with standard HTML elements -- headings, paragraphs, lists, tables, code blocks. This is the ideal input for a chunking pipeline.

**Implementation approach:**
```python
from lxml import etree

def parse_flare_xhtml(filepath: str) -> list[dict]:
    tree = etree.parse(filepath)
    root = tree.getroot()
    # Extract title from <title> or first <h1>
    # Walk <body> children, extracting text with structure preservation
    # Tag each chunk with source metadata (file path, heading hierarchy)
```

**Confidence:** HIGH -- Flare Clean XHTML output is well-documented by MadCap. The FlareToSphinx project on GitHub confirms BeautifulSoup/lxml approach works. Clean XHTML specifically removes all the proprietary namespace detritus that makes raw Flare files difficult to parse.

---

### Source Type 2: PDF Extraction

**Target:** GuideToGuiProgrammingInBBj.pdf and any other standalone PDFs linked from documentation.

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| pymupdf4llm | latest (Jan 2026 release) | PDF to Markdown extraction | Purpose-built for RAG pipelines. Outputs GitHub-compatible Markdown with headers, tables, code blocks, and lists properly formatted. Handles reading order, font-size-based header detection, and table recognition. Outperforms pdfplumber and pypdf for RAG use cases. |
| PyMuPDF | 1.26.x | Underlying PDF engine | Installed automatically as pymupdf4llm dependency. Provides the actual PDF parsing via MuPDF C library. |

**Why pymupdf4llm over alternatives:**
- **vs. pdfplumber (MIT):** pdfplumber is slower (built on pdfminer.six) and outputs raw text without structural formatting. pymupdf4llm preserves document structure as Markdown, which is what the chunker needs.
- **vs. pypdf (BSD):** pypdf is pure Python and handles basic text extraction, but has no layout analysis or table detection. For a programming guide PDF with code samples and tables, this matters.
- **vs. marker-pdf:** Heavier dependency chain (requires PyTorch for ML-based layout detection). Overkill for well-structured technical PDFs.

**License note:** pymupdf4llm inherits PyMuPDF's AGPL-3.0 license. This is acceptable here because:
1. The ingestion pipeline is an internal developer tool, not a distributed product or SaaS.
2. The pipeline code itself can be open-sourced alongside the docs repo.
3. If licensing becomes a concern later, drop to `pdfplumber` (MIT) with a custom Markdown formatter -- a moderate effort refactor, not a rewrite.

**Implementation approach:**
```python
import pymupdf4llm

def extract_pdf(filepath: str) -> list[dict]:
    pages = pymupdf4llm.to_markdown(filepath, page_chunks=True)
    # Each page is a dict with 'text' (markdown) and metadata
    # Post-process: strip page headers/footers, merge split paragraphs
    return pages
```

**Confidence:** HIGH -- pymupdf4llm is actively maintained (last release Jan 10, 2026), widely used in RAG pipelines, and the Artifex team (MuPDF maintainers) develops it directly.

---

### Source Type 3: WordPress Sites (Knowledge Base + Advantage Magazine)

**Targets:**
- `basis.cloud/knowledge-base/` -- WordPress + LearnPress LMS
- `basis.cloud/advantage-index/` -- Magazine article archive

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| crawl4ai | 0.8.x (latest) | Site crawling + Markdown extraction | Purpose-built for LLM/RAG pipelines. Outputs clean Markdown from HTML pages automatically. Deep crawl with link-following, URL filtering, and content pruning (strips nav, footer, sidebar). Handles JavaScript-rendered content via Playwright. |
| httpx | 0.28.x | HTTP client (fallback) | If crawl4ai is too heavy for simple WordPress pages, httpx + lxml is a lighter alternative. Only use as fallback. |

**Why crawl4ai over alternatives:**
- **vs. Scrapy:** Scrapy is a full crawl framework designed for large-scale scraping. Overkill for two small WordPress sites. Crawl4ai is simpler to set up and outputs clean Markdown directly -- exactly what the chunking pipeline needs.
- **vs. BeautifulSoup + requests:** Would work for static pages, but requires manual boilerplate stripping (nav, sidebar, footer, cookie banners). Crawl4ai's `PruningContentFilter` handles this automatically.
- **vs. WordPress REST API:** The WordPress REST API (`/wp-json/wp/v2/posts`) could provide structured content without crawling. Worth trying first for the Knowledge Base -- if the API is enabled and returns full content, it is cleaner than scraping. Fall back to crawl4ai if the API is disabled or returns excerpts only.

**Implementation approach:**
```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def crawl_wordpress_site(base_url: str, url_pattern: str) -> list[dict]:
    config = CrawlerRunConfig(
        # Use fit_markdown for cleaned content (strips boilerplate)
        # Filter URLs to stay within the target section
    )
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(urls, config=config)
    return [{"url": r.url, "markdown": r.markdown.fit_markdown} for r in results]
```

**WordPress REST API alternative (try first):**
```python
import httpx

async def fetch_wp_posts(base_url: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        # Paginate through /wp-json/wp/v2/posts?per_page=100&page=N
        # Extract title, content (HTML), date, categories
        # Convert HTML content to markdown with a simple converter
        pass
```

**Confidence:** MEDIUM-HIGH -- crawl4ai is actively maintained and well-suited for this use case. The WordPress REST API approach is cleaner if available but needs to be tested against the live sites. Neither site has been verified for API availability.

---

### Source Type 4: Docusaurus MDX + BBj Code Samples

**Target:** github.com/BasisHub/DWC-Course (Docusaurus site with MDX content and BBj sample files)

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| python-frontmatter | 1.1.0 | YAML frontmatter extraction | Parses `---` delimited YAML metadata from MDX files. Separates metadata (title, sidebar_position, description) from body content. Small, stable, widely used. |
| markdown-it-py | 3.x | Markdown parsing | Parses Markdown body into tokens/AST. Extracts headings, paragraphs, code blocks as structured elements. Handles standard Markdown; JSX components get treated as raw HTML blocks (which is fine -- we want the text content, not the React components). |
| lxml | 5.x | JSX tag stripping | Reuse from Source Type 1. Strip `<Tabs>`, `<TabItem>`, and other JSX/MDX components to extract inner text content. Simple regex or lxml HTML parser handles this. |

**Why NOT a full MDX parser:** MDX is a JavaScript ecosystem format. The only complete MDX parsers (remark + remark-mdx) are in Node.js. For a Python pipeline processing a small set of known MDX files, a pragmatic approach works:
1. Extract frontmatter with `python-frontmatter`
2. Strip JSX component tags with regex (they are well-formed: `<ComponentName>...</ComponentName>`)
3. Parse remaining Markdown with `markdown-it-py`
4. For BBj code blocks (` ```bbj ` or ` ```basic `), extract as separate code chunks with language metadata

**BBj sample files (.bbj/.txt):** These are plain text files. Read directly, tag with source file metadata. The CodeChunker from chonkie (or a simple custom splitter) can chunk by function/subroutine boundaries if the files are large.

**Implementation approach:**
```python
import frontmatter
import re

def parse_mdx(filepath: str) -> dict:
    post = frontmatter.load(filepath)
    metadata = post.metadata  # title, sidebar_position, etc.
    body = post.content
    # Strip JSX components, keeping inner text
    body = re.sub(r'<[A-Z][a-zA-Z]*[^>]*>', '', body)  # opening tags
    body = re.sub(r'</[A-Z][a-zA-Z]*>', '', body)       # closing tags
    return {"metadata": metadata, "markdown": body}
```

**Confidence:** HIGH -- This is a well-understood pattern. The DWC-Course repo uses standard Docusaurus MDX with minimal custom components. python-frontmatter is stable at 1.1.0 and handles the YAML extraction reliably.

---

### Source Type 5: BBj Code Samples (standalone)

**Target:** `.bbj`, `.txt`, and inline code blocks from all other sources.

No additional libraries needed. BBj code files are plain text.

**Approach:**
- Read files directly with Python's built-in `pathlib` / file I/O
- Tag with `generation` metadata based on file naming or content analysis:
  - `character` -- files with `PRINT`, `INPUT`, `READ` without GUI mnemonics
  - `vpro5` -- files with Visual PRO/5 mnemonic syntax (`PRINT(sysgui)'WINDOW'(...)`)
  - `bbj-gui` -- files with BBj Swing API (`BBjWindow`, `BBjButton`)
  - `dwc` -- files with DWC API (`BBjHtmlView`, web components)
  - `all` -- general BBj syntax applicable across generations
- Chunk by function/subroutine boundaries or by logical sections (comment-delimited blocks)

**Confidence:** HIGH -- BBj files are simple text. The generation tagging logic is domain-specific but straightforward based on keyword detection.

---

### Chunking

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| chonkie | 1.5.x | Text chunking | Lightweight, modular, purpose-built for RAG. 9 chunking strategies including RecursiveChunker (best for docs), SemanticChunker (for dense prose), and CodeChunker (AST-aware for code). Has native pgvector integration via `chonkie[pgvector]` extra. 10x lighter than LangChain's text splitters. |

**Why chonkie over alternatives:**
- **vs. LangChain text splitters:** LangChain's `RecursiveCharacterTextSplitter` and `MarkdownTextSplitter` work but pull in the entire LangChain dependency tree (hundreds of packages). Chonkie does one thing well with minimal dependencies.
- **vs. LlamaIndex node parsers:** Same problem -- massive framework dependency for a single function.
- **vs. custom splitting:** For Markdown content, custom splitting on `##` headers works initially but fails on edge cases (nested headers, code blocks containing `#`, tables). Chonkie's RecursiveChunker handles these correctly.
- **vs. semantic chunking:** Semantic chunking (embedding every sentence, clustering by similarity) is computationally expensive and unnecessary for well-structured documentation. Use RecursiveChunker with Markdown-aware rules as the default. Reserve SemanticChunker for prose-heavy Advantage magazine articles where structure is less predictable.

**Chunking strategy by source type:**

| Source | Chunker | Rationale |
|--------|---------|-----------|
| Flare XHTML | RecursiveChunker | Structured documentation with clear heading hierarchy |
| PDFs | RecursiveChunker | pymupdf4llm outputs structured Markdown |
| WordPress articles | RecursiveChunker or SemanticChunker | Knowledge Base is structured; magazine articles may benefit from semantic chunking |
| Docusaurus MDX | RecursiveChunker | Structured docs with heading hierarchy |
| BBj code | CodeChunker | AST-aware chunking preserves function/class boundaries |

**Chunk size recommendation:** 512-1024 tokens with 64-128 token overlap. For a small corpus (<50K chunks), larger chunks preserve more context. Start at 768 tokens / 96 overlap and tune based on retrieval quality.

**Generation tagging:** Each chunk must carry a `generation` tag (`all`, `character`, `vpro5`, `bbj-gui`, `dwc`) in its metadata. This enables generation-filtered retrieval at query time -- the core differentiator of the BBj RAG system.

**Installation:**
```bash
uv add "chonkie[semantic,code,pgvector]"
```

**Confidence:** HIGH -- chonkie 1.5.2 released Jan 5, 2026. Actively maintained, purpose-built for RAG, supports pgvector natively.

---

### Embedding Model

**Recommendation: Qwen3-Embedding-0.6B** (Apache 2.0, self-hostable)

| Model | Parameters | Dimensions | MTEB Multi. | Context | Languages | VRAM (FP16) | License |
|-------|-----------|------------|-------------|---------|-----------|-------------|---------|
| **Qwen3-Embedding-0.6B** | 600M | 1024 (flexible 32-1024) | Competitive with 7B models | 32K tokens | 100+ natural + programming | ~4 GB | Apache 2.0 |
| Qwen3-Embedding-4B | 4B | 2560 | Near SOTA | 32K tokens | 100+ | ~10 GB | Apache 2.0 |
| Qwen3-Embedding-8B | 8B | 4096 | #1 MTEB Multilingual (70.58) | 32K tokens | 100+ | ~18 GB | Apache 2.0 |
| Nomic Embed Text v2 (MoE) | ~300M active | 768 (flexible 256-768) | Competitive at size class | 8K tokens | 100+ | ~2 GB | Apache 2.0 |
| EmbeddingGemma-300M | 308M | 768 (flexible 128-768) | #1 under 500M params | 8K tokens | 100+ | <1 GB | Gemma license |
| BGE-M3 | 567M | 1024 | 63.0 | 8K tokens | 100+ | ~3 GB | MIT |

**Why Qwen3-Embedding-0.6B:**

1. **Code + text:** The Qwen3 embedding series explicitly supports 100+ programming languages. The 8B model scores 80.68 on MTEB-Code. Even the 0.6B model inherits the code-aware training. This matters for a corpus with BBj code samples alongside documentation prose.

2. **Size/quality sweet spot:** At 600M parameters and ~4GB VRAM (FP16), it runs on any modern GPU including consumer cards. It performs competitively with models 10x its size on real-world retrieval tasks and sits just behind Gemini-Embedding (proprietary) on MTEB among models in its size range.

3. **Instruction-aware:** Supports custom task instructions that improve retrieval by 1-5%. For a domain-specific corpus like BBj documentation, instruction prefixes like "Retrieve documentation about BBj programming" can meaningfully improve results.

4. **Flexible dimensions:** Matryoshka Representation Learning (MRL) allows truncating output from 1024 down to 32 dimensions. Start at 768 dimensions for quality, compress to 512 or 384 later if storage or speed becomes a concern. This flexibility avoids lock-in.

5. **32K context:** Handles entire documentation pages without truncation. Nomic v2 and BGE-M3 max at 8K tokens, which may truncate long pages.

6. **Apache 2.0:** No licensing restrictions. Fully self-hostable. No API calls needed.

**Why NOT the alternatives:**

| Model | Why Not |
|-------|---------|
| Qwen3-Embedding-8B | ~18GB VRAM is too heavy for a small corpus. The 0.6B model provides sufficient quality. Scale up only if retrieval quality testing shows gaps. |
| Qwen3-Embedding-4B | Good middle ground, but 0.6B is likely sufficient for <50K chunks of structured documentation. Start small, scale up if needed. |
| Nomic Embed Text v2 | Strong general model but 8K context limit may truncate long Flare pages. No explicit code training emphasis. |
| Nomic Embed Code (7B) | Code-specific but 7B parameters is heavy, and this corpus is majority prose with code samples, not a code-only corpus. |
| EmbeddingGemma-300M | Excellent efficiency but the Gemma license is more restrictive than Apache 2.0. Also newer (Sep 2025) with less community production experience. |
| BGE-M3 | Solid and battle-tested but older generation (2024). Lower MTEB scores than Qwen3 at comparable size. 8K context limit. |
| all-MiniLM-L6-v2 | Too small (384 dims, 56.3 MTEB). Fine for prototyping, not for production embedding quality. |

**Inference library:**

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| sentence-transformers | >=2.7.0 | Embedding inference | Standard library for running embedding models. Direct support for Qwen3 models. Simple API: `model.encode(texts)`. |
| transformers | >=4.51.0 | Model loading backend | Required by sentence-transformers for Qwen3 model compatibility. |
| torch | 2.x (latest) | ML runtime | Required by sentence-transformers/transformers. Install with CUDA support if GPU available. |

**Usage:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

# With instruction for better retrieval (optional but recommended)
texts = ["search_document: How to create a BBj window using DWC API"]
embeddings = model.encode(texts)
# embeddings.shape: (1, 1024)
```

**Confidence:** HIGH -- Qwen3-Embedding-0.6B is verified on HuggingFace with MTEB benchmarks. sentence-transformers compatibility confirmed (requires >=2.7.0). Apache 2.0 license confirmed. VRAM requirements verified.

---

### Vector Storage (pgvector Integration)

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| pgvector (Python) | 0.4.2 | pgvector type support | Official Python library for pgvector. Registers vector types with psycopg/asyncpg/SQLAlchemy. MIT license. Last updated Jan 22, 2026. |
| psycopg | 3.x (latest) | PostgreSQL driver | Modern async-capable PostgreSQL driver. psycopg3 (package name: `psycopg`) is the actively developed version. Supports binary COPY protocol for fast bulk inserts -- critical for loading embeddings. |
| SQLAlchemy | 2.x (latest) | ORM (optional) | Use only if the schema needs migrations or if other parts of the system use SQLAlchemy. For a simple ingestion pipeline, raw psycopg3 is simpler and faster. |

**Why psycopg3 over psycopg2:**
- psycopg3 is the actively maintained version (psycopg2 is legacy)
- Native async support (`psycopg.AsyncConnection`)
- Binary COPY protocol for fast bulk vector inserts
- Better type system integration with pgvector

**Why NOT SQLAlchemy (for now):** The ingestion pipeline does one thing: bulk-insert chunks with embeddings. Raw psycopg3 with parameterized queries and COPY is simpler and 2-5x faster for bulk operations than ORM-mediated inserts. If the project later needs a query API or migrations, SQLAlchemy can be added without changing the schema.

**Schema approach:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    source_type TEXT NOT NULL,       -- 'flare', 'pdf', 'wordpress', 'mdx', 'code'
    source_path TEXT NOT NULL,       -- file path or URL
    generation TEXT NOT NULL,        -- 'all', 'character', 'vpro5', 'bbj-gui', 'dwc'
    title TEXT,                      -- section/page title
    heading_path TEXT[],             -- breadcrumb of headings
    chunk_index INTEGER NOT NULL,    -- position within source document
    content TEXT NOT NULL,           -- raw text content
    token_count INTEGER NOT NULL,
    embedding vector(1024) NOT NULL, -- Qwen3-Embedding-0.6B default dimension
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index for cosine similarity search
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Filter indexes for generation-scoped retrieval
CREATE INDEX ON chunks (generation);
CREATE INDEX ON chunks (source_type);
```

**Usage:**
```python
import psycopg
from pgvector.psycopg import register_vector

conn = psycopg.connect("postgresql://...")
register_vector(conn)

# Bulk insert with COPY
with conn.cursor() as cur:
    with cur.copy("COPY chunks (source_type, source_path, generation, title, "
                  "heading_path, chunk_index, content, token_count, embedding) "
                  "FROM STDIN WITH (FORMAT BINARY)") as copy:
        copy.set_types(["text", "text", "text", "text",
                       "text[]", "int4", "text", "int4", "vector"])
        for chunk in chunks:
            copy.write_row(chunk.as_tuple())
```

**Confidence:** HIGH -- pgvector-python 0.4.2 verified on PyPI (Jan 22, 2026). psycopg3 binary COPY with vector types is documented in the official repo examples.

---

### Configuration & CLI

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| pydantic | 2.x | Configuration validation | Type-safe config with environment variable support. Define source paths, DB connection, model name, chunk sizes as a validated config object. |
| pydantic-settings | 2.x | Environment variable loading | Loads config from `.env` files and environment variables. Standard pattern for DB credentials and model paths. |
| typer | 0.x (latest) | CLI interface | Simple CLI framework built on Click. Define commands like `ingest flare`, `ingest pdf`, `ingest all`. Minimal boilerplate. |
| rich | 13.x | Terminal output | Progress bars, tables, colored output for the ingestion CLI. Shows progress during long embedding runs. |

**Why NOT LangChain or LlamaIndex:**
These are framework-level dependencies that would dominate the project. They provide document loaders, text splitters, vector store integrations, and embedding wrappers -- but each of those is a thin wrapper around the libraries we are already using directly. Adding LangChain means:
- 100+ transitive dependencies
- Framework lock-in for simple operations
- Abstraction layers that obscure what is happening
- Version compatibility issues across the framework

For a focused ingestion pipeline with 5 known source types and a single vector store, direct library usage is simpler, faster, and more maintainable.

---

## Complete Dependency List

### Core dependencies (pyproject.toml)

```toml
[project]
dependencies = [
    # Parsing
    "lxml>=5.0",
    "pymupdf4llm>=0.2",
    "crawl4ai>=0.8",
    "python-frontmatter>=1.1",
    "markdown-it-py>=3.0",

    # Chunking
    "chonkie[semantic,code,pgvector]>=1.5",

    # Embedding
    "sentence-transformers>=2.7",
    "transformers>=4.51",
    "torch>=2.0",

    # Database
    "pgvector>=0.4",
    "psycopg[binary]>=3.0",

    # Config & CLI
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "typer>=0.9",
    "rich>=13.0",

    # HTTP (for WordPress REST API fallback)
    "httpx>=0.28",
]
```

### Development dependencies

```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.9",
    "mypy>=1.14",
]
```

### Installation

```bash
# Create project and install all dependencies
uv init rag-ingestion
cd rag-ingestion
uv add lxml pymupdf4llm "crawl4ai" python-frontmatter markdown-it-py
uv add "chonkie[semantic,code,pgvector]"
uv add sentence-transformers transformers torch
uv add pgvector "psycopg[binary]"
uv add pydantic pydantic-settings typer rich httpx
uv add --group dev pytest pytest-asyncio ruff mypy

# Post-install for crawl4ai (sets up Playwright browser)
uv run crawl4ai-setup
```

---

## What NOT To Use (And Why)

### Do NOT use: LangChain or LlamaIndex

These are RAG application frameworks, not ingestion libraries. They add 100+ transitive dependencies to wrap the same libraries recommended above. For a batch ingestion pipeline that runs offline, the abstraction layers add complexity without value. The pipeline does not need chains, agents, memory, or runtime orchestration -- it needs parsers, a chunker, an embedder, and a database writer.

### Do NOT use: OpenAI / Cohere / Voyage embedding APIs

Project requirement is self-hostable with no external API calls. Even if API-based models score higher on benchmarks, they add latency, cost, and a hard dependency on external services. Qwen3-Embedding-0.6B runs locally and matches or exceeds older API models.

### Do NOT use: ChromaDB, Qdrant, Pinecone, Weaviate

pgvector is already selected as the vector store (Chapter 6 decision). For <50K chunks, pgvector provides identical performance to dedicated vector databases with simpler infrastructure (just PostgreSQL). Adding a second vector database is unnecessary complexity.

### Do NOT use: Unstructured.io

Unstructured is a popular document parsing library, but it is a heavy dependency (~1GB+ with all extras) that wraps the same underlying libraries (pymupdf, pdfminer, lxml). For 5 known source types with known structures, direct parsing is more predictable and debuggable.

### Do NOT use: Hugging Face TEI (Text Embeddings Inference) for initial development

TEI is a production inference server. For the initial ingestion pipeline (batch processing <50K chunks), sentence-transformers running locally is simpler. TEI adds Docker/container complexity. Consider TEI only when moving to production with concurrent embedding requests.

### Do NOT use: ONNX / llama.cpp for embedding inference (initially)

ONNX Runtime and llama.cpp (via llama-cpp-python) can provide faster inference for embedding models. But sentence-transformers with PyTorch is the simplest starting point and is what the model cards document. Optimize inference runtime only if embedding speed becomes a bottleneck (unlikely for <50K chunks).

### Do NOT use: asyncpg (initially)

asyncpg is a fast async PostgreSQL driver, but psycopg3 already supports async and has better pgvector type integration (via the pgvector-python library's `register_vector`). Use psycopg3 for both sync and async operations. Add asyncpg only if you need the absolute maximum async throughput, which is unlikely for batch ingestion.

### Do NOT use: markdown-analyzer-lib for MDX

This package exists on PyPI and claims MDX support, but it has limited documentation and community adoption. The python-frontmatter + markdown-it-py + regex combination is more transparent, well-documented, and handles the known DWC-Course MDX patterns reliably.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| XHTML parsing | lxml | BeautifulSoup + lxml backend | Extra abstraction layer. Flare XHTML is well-formed XML; lxml handles it natively. |
| PDF extraction | pymupdf4llm | pdfplumber (MIT) | Slower, no structure-preserving Markdown output. Consider only if AGPL is a blocker. |
| PDF extraction | pymupdf4llm | marker-pdf | Requires PyTorch for layout detection. Heavy for well-structured technical PDFs. |
| Web crawling | crawl4ai | Scrapy | Overkill framework for 2 small WordPress sites. |
| Web crawling | crawl4ai | requests + BeautifulSoup | Works but requires manual boilerplate stripping. |
| MDX parsing | frontmatter + regex | remark/remark-mdx (Node.js) | Would require subprocess calls to Node.js. Overkill for known simple MDX. |
| Chunking | chonkie | LangChain text splitters | Massive dependency for a single function. |
| Chunking | chonkie | Custom splitting | Fragile on edge cases (code blocks, tables). |
| Embedding | Qwen3-Embedding-0.6B | Nomic Embed Text v2 | 8K context limit; less explicit code training. |
| Embedding | Qwen3-Embedding-0.6B | BGE-M3 | Older generation; lower MTEB scores; 8K context. |
| Embedding | Qwen3-Embedding-0.6B | EmbeddingGemma-300M | More restrictive Gemma license; newer with less production validation. |
| Embedding runtime | sentence-transformers | HF TEI server | Production inference server; overkill for batch pipeline. |
| DB driver | psycopg3 | psycopg2 | Legacy; no async; slower COPY protocol. |
| DB driver | psycopg3 | asyncpg | Less integrated pgvector type support. |
| Package manager | uv | pip + venv | Slower resolution; no lockfile by default; uv is the 2026 standard. |
| Framework | Direct libraries | LangChain | 100+ deps; framework lock-in; abstractions hide behavior. |
| Framework | Direct libraries | LlamaIndex | Same problems as LangChain at smaller scale. |

---

## Version Matrix (All Verified 2026-01-31)

| Package | Version | Last Updated | Source |
|---------|---------|-------------|--------|
| lxml | 5.x | Active | PyPI |
| pymupdf4llm | latest | 2026-01-10 | PyPI |
| PyMuPDF | 1.26.7 | Active | PyPI |
| crawl4ai | 0.8.x | Active | PyPI / GitHub |
| python-frontmatter | 1.1.0 | Stable | PyPI |
| markdown-it-py | 3.x | Active | PyPI |
| chonkie | 1.5.2 | 2026-01-05 | PyPI |
| sentence-transformers | >=2.7.0 | Active | PyPI |
| transformers | >=4.51.0 | Active | PyPI |
| pgvector (Python) | 0.4.2 | 2026-01-22 | PyPI |
| psycopg | 3.x | Active | PyPI |
| pydantic | 2.x | Active | PyPI |
| typer | 0.x | Active | PyPI |
| Qwen3-Embedding-0.6B | -- | 2025-06 | HuggingFace |

---

## Embedding Model Scaling Path

Start with Qwen3-Embedding-0.6B. If retrieval quality testing shows gaps:

1. **First:** Try instruction tuning. Add task-specific instructions to the encoding call. This is free and can improve results 1-5%.
2. **Second:** Increase dimensions. Start at 768, go to 1024. Re-embed the corpus (batch job, hours not days for <50K chunks).
3. **Third:** Scale to Qwen3-Embedding-4B (~10GB VRAM). Same API, same code, just swap the model name. Re-embed required.
4. **Last resort:** Qwen3-Embedding-8B (~18GB VRAM). Requires a production GPU (A100/L40S/4090).

The key insight: re-embedding <50K chunks takes hours, not days. The schema supports any dimension via pgvector's vector type. Model upgrades are a config change + batch re-run, not an architecture change.

---

## Sources

- [Qwen3 Embedding Blog Post](https://qwenlm.github.io/blog/qwen3-embedding/) -- Official benchmarks and architecture details
- [Qwen3-Embedding-0.6B on HuggingFace](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) -- Model card, usage examples, version requirements
- [pgvector-python GitHub](https://github.com/pgvector/pgvector-python) -- Version 0.4.2, driver support, usage examples
- [chonkie GitHub](https://github.com/chonkie-inc/chonkie) -- Chunking strategies, pgvector integration, version 1.5.2
- [pymupdf4llm PyPI](https://pypi.org/project/pymupdf4llm/) -- Latest release, RAG-focused PDF extraction
- [crawl4ai Documentation](https://docs.crawl4ai.com/) -- Deep crawling, markdown generation, content filtering
- [MadCap Flare Clean XHTML](https://www.madcapsoftware.com/blog/new-feature-highlight-clean-xhtml-output-madcap-flare-2017/) -- Clean XHTML output format specification
- [FlareToSphinx GitHub](https://github.com/boltzmann-brain/FlareToSphinx) -- Prior art for Python-based Flare parsing
- [BentoML Open Source Embedding Models Guide](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models) -- 2026 embedding model landscape
- [Nomic Embed Text v2 Blog](https://www.nomic.ai/blog/posts/nomic-embed-text-v2) -- MoE architecture, benchmarks
- [EmbeddingGemma on Google Developers Blog](https://developers.googleblog.com/introducing-embeddinggemma/) -- 300M model benchmarks
- [Nomic Embed Code Blog](https://www.nomic.ai/blog/posts/introducing-state-of-the-art-nomic-embed-code) -- Code-specific embedding model
- [PyMuPDF AGPL Discussion](https://github.com/pymupdf/PyMuPDF/discussions/971) -- License implications

---

*Research conducted 2026-01-31 via WebSearch for current versions, benchmarks, and ecosystem state. All version numbers and dates verified against PyPI, HuggingFace, and GitHub.*
