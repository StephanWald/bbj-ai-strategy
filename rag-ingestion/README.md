# BBj RAG Ingestion Pipeline

A Python pipeline that parses BBj documentation from multiple sources, tags content by BBj generation and document type, chunks it with contextual headers, generates embeddings, and stores everything in PostgreSQL with pgvector for hybrid retrieval.

## Overview

The pipeline ingests documentation from six source types (MadCap Flare XHTML, PDFs, WordPress articles, Docusaurus MDX, BBj source code, and web crawl fallback), enriches each document with generation tags (character, vpro5, bbj\_gui, dwc) and document type classification (api-reference, concept, tutorial, etc.), splits content into heading-aware chunks, generates embeddings via Ollama or OpenAI, and bulk-inserts everything into a PostgreSQL database with pgvector for hybrid dense + BM25 retrieval.

The result is a searchable vector database powering the BBj AI documentation chat. For design rationale (generation tagging strategy, chunking approach, hybrid search design), see the [Getting Started guide](https://stephanwald.github.io/bbj-ai-strategy/docs/rag-database/getting-started).

## Prerequisites

### 1. Python 3.12+

```bash
python3 --version
# Python 3.12.x or higher
```

### 2. uv (Python package manager)

```bash
uv --version
# uv 0.7.x or higher
```

Install: <https://docs.astral.sh/uv/getting-started/installation/>

### 3. PostgreSQL 16+ with pgvector

```bash
psql --version
# psql (PostgreSQL) 16.x or higher
```

Create the database and install the pgvector extension:

```bash
createdb bbj_rag
psql bbj_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Apply the schema:

```bash
psql bbj_rag < sql/schema.sql
```

This creates the `chunks` table with vector embeddings, full-text search (tsvector), content-hash deduplication, and all required indexes (HNSW for dense search, GIN for keyword search and generation filtering).

### 4. Ollama (for embedding model)

```bash
ollama --version
# ollama version 0.x.x
```

Install: <https://ollama.com>

Pull the embedding model:

```bash
ollama pull qwen3-embedding:0.6b
```

## Installation

```bash
git clone https://github.com/StephanWald/bbj-ai-strategy.git
cd bbj-ai-strategy/rag-ingestion
uv sync
```

## Configuration

### Config File

The pipeline reads `config.toml` in the working directory. Example:

```toml
database_url = "postgresql://localhost:5432/bbj_rag"
embedding_model = "qwen3-embedding:0.6b"
embedding_dimensions = 1024
embedding_provider = "ollama"
embedding_batch_size = 64
chunk_size = 400
chunk_overlap = 50

flare_source_path = "/path/to/flare/project"
pdf_source_path = "/path/to/GuideToGuiProgramming.pdf"
mdx_source_path = "/path/to/dwc-course/docs"
bbj_source_dirs = ["/path/to/bbj/source1", "/path/to/bbj/source2"]

advantage_index_url = "https://basis.cloud/advantage-index/"
kb_index_url = "https://basis.cloud/knowledge-base/"
```

### Configuration Reference

| Setting | Type | Default | Env Override | Description |
|---------|------|---------|-------------|-------------|
| `database_url` | `str` | `postgresql://localhost:5432/bbj_rag` | `BBJ_RAG_DATABASE_URL` | PostgreSQL connection URL with pgvector |
| `embedding_model` | `str` | `qwen3-embedding:0.6b` | `BBJ_RAG_EMBEDDING_MODEL` | Embedding model name (Ollama or OpenAI) |
| `embedding_dimensions` | `int` | `1024` | `BBJ_RAG_EMBEDDING_DIMENSIONS` | Output vector dimensions (must match model) |
| `embedding_provider` | `str` | `ollama` | `BBJ_RAG_EMBEDDING_PROVIDER` | Embedding provider: `ollama` or `openai` |
| `embedding_batch_size` | `int` | `64` | `BBJ_RAG_EMBEDDING_BATCH_SIZE` | Number of texts per embedding API call |
| `chunk_size` | `int` | `400` | `BBJ_RAG_CHUNK_SIZE` | Target chunk size in approximate tokens |
| `chunk_overlap` | `int` | `50` | `BBJ_RAG_CHUNK_OVERLAP` | Overlap between consecutive chunks in tokens |
| `flare_source_path` | `str` | `""` | `BBJ_RAG_FLARE_SOURCE_PATH` | Path to MadCap Flare project root directory |
| `crawl_source_urls` | `list[str]` | `[]` | `BBJ_RAG_CRAWL_SOURCE_URLS` | URLs for web crawl fallback parser |
| `pdf_source_path` | `str` | `""` | `BBJ_RAG_PDF_SOURCE_PATH` | Path to PDF file for ingestion |
| `mdx_source_path` | `str` | `""` | `BBJ_RAG_MDX_SOURCE_PATH` | Path to Docusaurus MDX docs directory |
| `bbj_source_dirs` | `list[str]` | `[]` | `BBJ_RAG_BBJ_SOURCE_DIRS` | Directories containing BBj source code files |
| `advantage_index_url` | `str` | `https://basis.cloud/advantage-index/` | `BBJ_RAG_ADVANTAGE_INDEX_URL` | WordPress Advantage article index URL |
| `kb_index_url` | `str` | `https://basis.cloud/knowledge-base/` | `BBJ_RAG_KB_INDEX_URL` | WordPress Knowledge Base article index URL |

### Environment Variables

Environment variables override TOML file values. All variables use the `BBJ_RAG_` prefix.

**Priority order** (highest to lowest): constructor arguments > environment variables > TOML file > field defaults.

```bash
export BBJ_RAG_DATABASE_URL="postgresql://user:pass@host:5432/bbj_rag"
export BBJ_RAG_FLARE_SOURCE_PATH="/path/to/flare/project"
```

## Usage

### Full Ingestion

Run the complete pipeline (parse, tag, chunk, embed, store) for a source:

```bash
bbj-rag ingest --source flare
```

**Options:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--source` | Yes | -- | Source type: `flare`, `pdf`, `advantage`, `kb`, `mdx`, `bbj-source` |
| `--resume` | No | off | Skip chunks whose content hash already exists in the database |
| `--batch-size` | No | `64` | Number of chunks per embedding batch |
| `-v, --verbose` | No | off | Enable debug logging (set on the group, before `ingest`) |

**Example with all options:**

```bash
bbj-rag -v ingest --source flare --resume --batch-size 32
```

After successful ingestion, the quality report is auto-printed showing chunk distributions and any anomaly warnings.

### Parse Only

Parse source documents without embedding or storing (useful for debugging parsers):

```bash
bbj-rag parse --source pdf
```

**Options:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--source` | Yes | -- | Source type: `flare`, `pdf`, `advantage`, `kb`, `mdx`, `bbj-source` |

Prints the total document count and first 5 sample titles.

### Quality Report

Show post-ingestion quality metrics from the database:

```bash
bbj-rag report
```

**Output includes:**

- Chunk counts by source (flare, advantage, kb, pdf, mdx, bbj-source)
- Chunk counts by BBj generation (all, character, vpro5, bbj\_gui, dwc, untagged)
- Chunk counts by document type (api-reference, concept, tutorial, etc.)
- Automated anomaly warnings (empty sources, low counts, high untagged percentage, unknown doc types, dominant source)

**Example output:**

```
=== BBj RAG Quality Report ===

Chunks by Source:
  flare      2,847  (68.2%)
  advantage    412  (9.9%)
  kb           389  (9.3%)
  pdf          287  (6.9%)
  mdx          156  (3.7%)
  bbj-source    82  (2.0%)
  ──────────────────────────
  Total      4,173

Chunks by Generation:
  all        1,823  (43.7%)
  bbj_gui    1,412  (33.8%)
  dwc          634  (15.2%)

Chunks by Document Type:
  api-reference    1,956  (46.9%)
  concept            892  (21.4%)
  tutorial           312  (7.5%)

Warnings:
  [!] 42 chunks (1.0%) have generation "untagged"
```

### Search Validation

Run search validation assertions against embedded data:

```bash
bbj-rag validate
```

**Options:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `-v, --verbose` | No | off | Show detailed test results |

Requires a populated database with embedded chunks. Delegates to pytest with the `search_validation` marker.

### All-Source Ingestion

Ingest every enabled source from `sources.toml` in a single command:

```bash
bbj-ingest-all --config sources.toml --data-dir /path/to/data
```

**Options:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--config` | No | `sources.toml` | Path to sources config file |
| `--data-dir` | No | from config/env | Override base data directory |
| `--clean` | No | off | Wipe existing chunks before re-ingesting each source |
| `--resume` | No | off | Skip sources completed in a previous interrupted run |
| `--source` | No | all | Run only named sources (repeatable) |
| `-v, --verbose` | No | off | Per-file progress output |

```bash
# Ingest only specific sources
bbj-ingest-all --config sources.toml --source flare --source pdf

# Clean re-ingest with verbose output
bbj-ingest-all --config sources.toml --clean -v
```

## Docker Usage

Docker Compose is the primary deployment path. It runs pgvector and the FastAPI app together, with Ollama running on the host for GPU acceleration.

### Quick Start

```bash
cd rag-ingestion
cp .env.example .env   # edit credentials (at minimum, change BBJ_RAG_DB_PASSWORD)
```

Ensure Ollama is running on the host and listening on all interfaces:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

Start the services:

```bash
docker compose up -d      # start pgvector + app
docker compose logs -f     # watch startup (Ctrl-C to detach)
```

The app waits for the database health check to pass before starting. On first launch, the schema is applied automatically via the init script mounted into pgvector.

### Environment Variables (.env)

Copy `.env.example` to `.env` and edit as needed. Key variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BBJ_RAG_DB_PASSWORD` | Yes | -- | Database password (fail-fast if unset) |
| `BBJ_RAG_DB_USER` | No | `bbj` | Database user |
| `BBJ_RAG_DB_NAME` | No | `bbj_rag` | Database name |
| `DB_PORT_EXTERNAL` | No | `10432` | Host port mapped to PostgreSQL |
| `APP_PORT_EXTERNAL` | No | `10800` | Host port mapped to the REST API |
| `BBJDOCS_PATH` | No | `/Users/beff/bbjdocs` | Host path to Flare docs |
| `BBJ_AI_STRATEGY_PATH` | No | `/Users/beff/_workspace/bbj-ai-strategy` | Host path to this repo |
| `BBJ_DWC_TUTORIAL_PATH` | No | `/Users/beff/_workspace/bbj-dwc-tutorial` | Host path to DWC tutorial |
| `BBJ_BEGINNER_TUTORIAL_PATH` | No | `/Users/beff/_workspace/bbj-beginner-tutorial` | Host path to beginner tutorial |
| `BBJ_DB_MODERNIZATION_PATH` | No | `/Users/beff/_workspace/bbj-db-modernization-tutorial` | Host path to DB modernization tutorial |

Source data directories are mounted as read-only volumes into the container at `/data`. The compose environment sets `DATA_DIR=/data` so `sources.toml` paths resolve automatically.

### Ingestion via Docker

All CLI commands work inside the running container via `docker compose exec`:

**All sources:**

```bash
# Local
bbj-ingest-all --config sources.toml --data-dir /path/to/data

# Docker
docker compose exec app bbj-ingest-all --config sources.toml
```

**Single source:**

```bash
# Local
bbj-rag ingest --source flare

# Docker
docker compose exec app bbj-rag ingest --source flare
```

**Full clean re-ingest:**

```bash
# Local
bbj-ingest-all --config sources.toml --data-dir /path/to/data --clean

# Docker
docker compose exec app bbj-ingest-all --config sources.toml --clean
```

**Parse only (no embedding):**

```bash
# Local
bbj-rag parse --source pdf

# Docker
docker compose exec app bbj-rag parse --source pdf
```

Inside Docker, `DATA_DIR=/data` is set by the compose environment, so `--data-dir` is not needed. Source data is mounted read-only from the host paths configured in `.env`.

## Project Structure

```
src/bbj_rag/
    __init__.py
    cli.py                  # Click CLI entry point (ingest, parse, report, validate)
    config.py               # Settings (TOML + env var loading via pydantic-settings)
    models.py               # Document and Chunk Pydantic models
    pipeline.py             # Pipeline orchestrator (parse -> tag -> chunk -> embed -> store)
    chunker.py              # Heading-aware text chunking with code block preservation
    embedder.py             # Embedding via Ollama (default) or OpenAI (fallback)
    db.py                   # PostgreSQL connection and bulk insert with COPY protocol
    schema.py               # Schema creation helper (applies sql/schema.sql)
    search.py               # Dense, BM25, and hybrid RRF search
    intelligence/
        __init__.py         # Package re-exports for intelligence API
        generations.py      # BBj generation tagger (all/character/vpro5/bbj_gui/dwc)
        doc_types.py        # Document type classifier (api-reference, concept, etc.)
        context_headers.py  # Hierarchical context header builder
        report.py           # Quality report (DB metrics, anomaly warnings)
    parsers/
        __init__.py         # DocumentParser protocol + shared constants
        flare.py            # MadCap Flare XHTML parser (with snippet resolution)
        flare_toc.py        # Flare TOC index builder (section path extraction)
        flare_cond.py       # Flare condition tag extractor (generation signals)
        web_crawl.py        # Web crawl fallback parser (rendered HTML)
        wordpress.py        # WordPress parsers (Advantage articles + Knowledge Base)
        pdf.py              # PDF parser (pymupdf4llm with per-section tagging)
        mdx.py              # Docusaurus MDX parser (frontmatter + markdown)
        bbj_source.py       # BBj source code parser (DWC/GUI classification)
```

## Development

Run development commands from the `rag-ingestion/` directory:

```bash
make check      # Run all checks (lint, typecheck, test)
make test       # Run tests (excludes search_validation by default)
make lint       # Run ruff linter
make format     # Format code with ruff
make typecheck  # Run mypy in strict mode
make clean      # Remove build artifacts and caches
```

Individual tool commands:

```bash
uv run pytest                       # Run unit tests
uv run ruff check src/ tests/       # Lint check
uv run ruff format src/ tests/      # Auto-format
uv run mypy src/                    # Type check
```

## Further Reading

- [Getting Started with RAG Ingestion](https://stephanwald.github.io/bbj-ai-strategy/docs/rag-database/getting-started) -- Pipeline design, code tour, and setup walkthrough
- [Chapter 6: RAG Database Design](https://stephanwald.github.io/bbj-ai-strategy/docs/rag-database) -- Full design rationale: generation tagging, chunking strategy, hybrid search
