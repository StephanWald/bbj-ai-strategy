# Feature Landscape: RAG Ingestion Pipeline

**Domain:** Python RAG ingestion pipeline for BBj technical documentation
**Researched:** 2026-01-31
**Scope:** Features for a starter kit (v1.2), not production CI/CD infrastructure

---

## Table Stakes

Features that any competent RAG ingestion pipeline must have. Without these, the pipeline produces unusable or unreliable output.

### Parsing & Extraction

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **XHTML/HTML parser for MadCap Flare output** | Primary corpus is Clean XHTML export; must extract text from semantic HTML elements (`h1`-`h6`, `p`, `li`, `table`, `code`) while stripping markup | Low | Use BeautifulSoup or lxml. Chapter 6 already specifies Clean XHTML as ingestion format. Do NOT use regex for XML/HTML parsing -- this is universally warned against. |
| **Heading hierarchy extraction** | Section headings (`h1` > `h2` > `h3`) form the contextual header for each chunk. Without this, chunks lose their position in the document structure and embeddings are degraded. | Low | Walk the DOM tree, track heading stack. Required for contextual chunk headers (see below). |
| **PDF text extraction** | Standalone PDFs (e.g., GUI programming guide) are a defined source type. Must extract readable text from PDF pages. | Low | pymupdf4llm is the recommended tool -- 0.12s extraction, outputs Markdown with headers. Released Jan 2026. Alternative: `unstructured` for semantic chunking. |
| **HTML scraping for web-hosted sources** | Advantage articles and Knowledge Base are web-hosted HTML. Must fetch and parse article content from live pages. | Medium | requests + BeautifulSoup. Knowledge Base is WordPress/LearnPress -- check for REST API at `/wp-json/wp/v2/posts` first (structured JSON), fall back to HTML scraping. Advantage articles are standard WordPress pages. |
| **MDX content extraction for DWC-Course** | DWC-Course is a Docusaurus site with MDX files. Must strip JSX/import statements and extract clean Markdown text + code blocks. | Medium | Two paths: (1) clone repo and parse .mdx files directly (preferred -- access to raw source), or (2) use `docusaurus-plugin-llms` output if available. MDX imports/React components must be stripped. |
| **Code block preservation** | BBj code samples within documentation must be extracted intact, not split or corrupted. Code blocks are high-value for retrieval queries like "how do I create a window." | Low | Detect `<pre>`, `<code>`, fenced code blocks in Markdown. Preserve as atomic units during chunking. |

### Chunking

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Document-type-aware chunk sizing** | Chapter 6 defines variable chunk sizes: API refs 200-400 tokens, concepts 400-600 tokens, code examples kept intact. Uniform chunking degrades retrieval quality by up to 9% vs. best approach per Firecrawl benchmarks. | Medium | Requires document type classification (see differentiators). At minimum, distinguish between short API entries and long conceptual pages. |
| **Contextual chunk headers (CCH)** | Prepend section hierarchy path to each chunk before embedding. This is one of the highest-impact RAG techniques -- FinanceBench showed 83% vs. 19% baseline when combined with relevant segment extraction. Chapter 6 explicitly requires this. | Low | Format: `"Section > Subsection > Sub-subsection: [chunk text]"`. Built from heading hierarchy extracted during parsing. |
| **Chunk overlap** | Chapter 6 specifies 10-15% overlap between adjacent chunks. Standard practice; prevents information loss at chunk boundaries. Industry recommendation is 50-100 tokens for 500-token chunks. | Low | Sliding window with configurable overlap percentage. |
| **Token-aware splitting** | Chunks must respect token limits, not just character counts. Embedding models have fixed context windows (typically 512 tokens). Splitting mid-sentence degrades embedding quality. | Low | Use tiktoken or model-specific tokenizer. Split at sentence boundaries within token budget. |
| **Code block integrity** | Never split a code block across chunks. A function split in half is useless for retrieval. Chapter 6: "Code examples should never be split mid-function." | Medium | Detect code blocks before splitting. If a code block exceeds chunk size, it becomes its own chunk (possibly oversized, but intact). |

### Embedding

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Embedding generation via local model** | Chapter 6 requires self-hostable embeddings (enterprise data policy). Generate dense vector embeddings for every chunk using an open-source model. | Medium | Recommended: sentence-transformers library. Model selection is a separate research question (see STACK.md). Chapter 6 suggests BGE-M3 or similar; as of Jan 2026, Qwen3-Embedding (Apache 2.0) is the top open-source option on MTEB. |
| **Batch embedding with progress tracking** | Thousands of chunks need embedding. Must show progress (not a silent black box). A corpus of ~50K chunks at ~100ms per batch could take 15-30 minutes. | Low | tqdm progress bar or logging. Process in batches of 32-64 for GPU efficiency. |

### Storage

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **pgvector schema creation** | Chapter 6 selected pgvector. Pipeline must create the `doc_chunks` table with vector column, metadata columns, and tsvector column for BM25. | Low | SQL migration script. Depends on Chapter 6 schema design. Use `CREATE EXTENSION IF NOT EXISTS vector;` |
| **Chunk insertion with all metadata** | Each chunk row must include: embedding vector, content text, source URL, document type, generation tags, contextual header, source type, and tsvector for full-text search. | Low | Standard INSERT via psycopg2/psycopg3 with pgvector-python for vector type registration. |
| **Full-text search vector column** | Chapter 6 specifies hybrid retrieval (dense + BM25). The `search_vector` tsvector column must be populated at ingestion time, not deferred. | Low | `to_tsvector('english', content)` in the INSERT statement or as a generated column. |
| **HNSW index creation** | Chapter 6 discusses HNSW indexing for approximate nearest neighbor search. Index must be created after bulk insertion for efficiency. | Low | `CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)`. Build after data load, not before. |

### Pipeline Orchestration

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Source-by-source CLI invocation** | Engineer must be able to run ingestion per source type: `python ingest.py --source flare`, `--source pdf`, etc. Not a monolithic "ingest everything" with no control. | Low | argparse or click CLI. Each source type is a separate command or flag. |
| **Configuration file for paths and connection** | Database connection string, source paths, model name, chunk sizes -- all configurable. No hardcoded paths. | Low | YAML or .env file. `config.yaml` with source paths, `DATABASE_URL`, `EMBEDDING_MODEL`, chunk size params. |
| **Logging with structured output** | Every step must log what it's doing: files parsed, chunks created, embeddings generated, rows inserted. Essential for debugging when something goes wrong. | Low | Python `logging` module. INFO for progress, DEBUG for details, WARNING for skipped files, ERROR for failures. |
| **Error handling with continue-on-failure** | If one file fails to parse, the pipeline must log the error and continue with the next file. A single malformed XHTML file should not abort the entire batch. | Low | try/except per file with error logging. Report summary at end: "Processed 1,847 files. 3 failures. See errors.log." |

### Data Integrity

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Content hashing for idempotent ingestion** | Re-running the pipeline must not create duplicate chunks. Hash each chunk's content (SHA-256) and use upsert or skip-if-exists logic. | Low | `hashlib.sha256(content.encode()).hexdigest()` as a column. ON CONFLICT DO UPDATE or skip. |
| **Deterministic chunk IDs** | Each chunk needs a stable, reproducible ID derived from source path + chunk position. This enables upsert behavior and change detection across re-runs. | Low | Format: `{source_type}/{file_path}#{chunk_index}` or hash of source path + chunk index. |
| **Source URL tracking** | Every chunk must link back to its source document URL for citation. Consumers (IDE, chat) need to show "Source: documentation.basis.cloud/BASISHelp/WebHelp/..." | Low | Store the original URL or file path as metadata on every chunk row. |

---

## Differentiators

Features that make this pipeline specifically suited for the BBj documentation corpus. These are not generic RAG features -- they address BBj's unique multi-generational problem.

### Generation Tagging (The Core Differentiator)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Automatic generation classification** | Every chunk must be tagged with which BBj generation it applies to: `all`, `character`, `vpro5`, `bbj-gui`, `dwc`. This is the defining feature of the entire RAG strategy per Chapter 6. Without it, retrieval cannot be generation-aware. | High | This is the hardest feature. Requires heuristic rules based on API names, syntax patterns, and file paths. See classification signals below. |
| **Multi-generation tag support** | A single chunk can apply to multiple generations (e.g., `BBjSysGui.addWindow()` applies to both `bbj-gui` and `dwc`). Schema must support array-valued generation tags. | Low | PostgreSQL array column: `generation TEXT[]`. Chapter 6 already defines this. |
| **Generation classification signals** | The pipeline must use multiple signals to infer generation: (1) API class names (`BBjSysGui` = bbj-gui/dwc, `BBjControl` = bbj-gui/dwc), (2) syntax patterns (`PRINT (sysgui)'WINDOW'(...)` = vpro5, `PRINT @(x,y)` = character), (3) file path patterns (Flare topics often organized by product version), (4) explicit version annotations (since_version metadata). | High | Start with keyword/regex rules. A lookup table of known API classes mapped to generations is the most reliable approach. Deferred: LLM-assisted classification for ambiguous cases. |
| **Default generation fallback** | When generation cannot be determined, default to `all` rather than guessing. Wrong generation tags are worse than broad tags -- they cause retrieval to miss relevant content. | Low | Conservative default. Log every fallback for manual review. |

### Document Type Classification

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Document type classification** | Chapter 6 defines 7 types: `api-reference`, `concept`, `example`, `migration`, `language-reference`, `best-practice`, `version-note`. Type determines chunk size and retrieval boosting. | Medium | Heuristic classification: API refs have method signatures and parameter lists. Concepts have prose paragraphs. Examples have code blocks. Migration docs reference "from X to Y" patterns. File path and heading patterns are strong signals. |
| **Chunk size variation by type** | API refs get 200-400 tokens, concepts get 400-600 tokens, code examples stay intact. Per Chapter 6 design. | Low | Once doc type is classified, select chunk size from config map. |

### Source-Specific Parsers

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **MadCap Flare TOC-aware parsing** | Use Flare's Table of Contents structure to maintain hierarchical relationships between topics. The Flare TOC provides the "Section > Subsection" hierarchy that becomes the contextual chunk header. | Medium | Parse the TOC XML file from the Flare export. Map each topic file to its position in the hierarchy. Without TOC, must infer hierarchy from heading levels within each file (less accurate but workable). |
| **Advantage article category extraction** | Advantage articles are organized by category (Partnership, Language/Interpreter, Database Management, Development Tools, System Administration, Building Blocks). Extract category as metadata for filtering. | Low | Parse from WordPress category markup or REST API response. |
| **DWC-Course chapter-aware chunking** | DWC-Course has 12 chapters with progressive structure (GUI-to-DWC migration through deployment). Chapter number and topic provide rich contextual headers. All content is DWC-generation. | Low | Parse MDX frontmatter for chapter metadata. All chunks from this source get `generation: ["dwc"]`. |
| **Knowledge Base Q&A structure detection** | Knowledge Base articles likely follow Q&A/troubleshooting patterns. Detect question-answer pairs and keep them together as chunks rather than splitting Q from A. | Medium | Look for heading patterns like "Problem:", "Solution:", "Steps:", FAQ formatting. Keep Q+A as atomic chunks. |

### Cross-Reference Metadata

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Supersedes/superseded_by links** | Chapter 6 defines modernization path links: `vpro5-window-create` is superseded by `bbj-addwindow`. These enable retrieval to surface modern equivalents alongside legacy answers. | High | Requires manual mapping or heuristic matching of legacy and modern APIs. Start with a manual lookup table for the most important API pairs. |
| **Related topic links** | Extract cross-references from Flare output (internal links between topics) as `related` metadata. Enables "see also" suggestions. | Medium | Parse `<a href>` within topic content. Resolve relative paths to topic IDs. |

### Ingestion Quality Reporting

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Post-ingestion summary report** | After ingestion completes, report: total chunks by source type, by generation tag, by document type. Shows coverage gaps at a glance. | Low | SQL aggregate queries + formatted console output. |
| **Generation tag distribution report** | Show how many chunks are tagged per generation. Uneven distribution (e.g., 80% `all`, 2% `vpro5`) may indicate classification issues. | Low | `SELECT generation, count(*) FROM doc_chunks GROUP BY generation` |
| **Orphan detection** | Flag chunks that have no generation tag or no document type. These need manual review. | Low | `SELECT * FROM doc_chunks WHERE generation IS NULL OR doc_type IS NULL` |

---

## Anti-Features

Things to deliberately NOT build in v1.2. Each is either premature optimization, scope creep, or contradicts the "starter kit" goal.

### Production Infrastructure (Explicitly Out of Scope per PROJECT.md)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **CI/CD automated re-ingestion** | v1.2 is a starter kit, not a production pipeline. Automated triggers add deployment complexity with no immediate value. | Manual CLI invocation: `python ingest.py --source flare`. An engineer runs it when needed. |
| **Scheduled/incremental ingestion** | Incremental change detection (only re-ingest modified files) requires content versioning infrastructure. Over-engineering for a corpus that changes infrequently. | Full re-ingestion with idempotent upserts. At ~50K chunks, a full re-run takes minutes, not hours. |
| **Docker/container packaging** | Containerizing adds Dockerfile maintenance and assumes a deployment target. The starter kit runs on an engineer's machine. | Virtual environment with `requirements.txt` or `pyproject.toml`. `pip install -e .` |
| **Multi-environment config (staging/prod)** | No staging/prod distinction needed for a starter kit. One database, one config. | Single `.env` file with `DATABASE_URL`. |

### Premature Optimization

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Distributed/parallel ingestion (Ray)** | The corpus is ~50K chunks. Sequential processing on a single machine completes in reasonable time. Ray adds massive dependency complexity. | Simple Python `for` loop with progress bar. Profile first; optimize only if ingestion exceeds 1 hour. |
| **Embedding fine-tuning** | Chapter 6 explicitly defers this: "optimization should be deferred until the baseline pipeline is operational and retrieval quality can be measured." | Use a pre-trained embedding model. Measure retrieval quality first. Fine-tune later with query-document pairs from real usage. |
| **Cross-encoder reranking at ingestion time** | Reranking is a retrieval-time concern (Stage 4 of Chapter 6's retrieval function). It has nothing to do with ingestion. | Implement reranking in the retrieval API, not the ingestion pipeline. |
| **GraphRAG / knowledge graph construction** | Emerging pattern (TreeRAG, GraphRAG) adds LLM-powered semantic enrichment during ingestion. Massive complexity for uncertain benefit at this corpus size. | Flat vector store with metadata filtering. If graph relationships are needed later, they can be added as a layer on top. |
| **LLM-assisted chunk summarization** | Some approaches generate per-chunk summaries using an LLM during ingestion. Adds LLM cost and latency for each of ~50K chunks with uncertain retrieval benefit. | Contextual chunk headers (deterministic, free) provide most of the same benefit. Per Snowflake FinanceBench results, CCH is more robust than per-chunk LLM summaries. |
| **Semantic deduplication (embedding clustering)** | MinHash/LSH or embedding-based near-duplicate detection is designed for corpora with heavy redundancy. BBj docs are authored content, not web-scraped duplicates. | Hash-based exact deduplication only. If semantic duplicates emerge, address manually. |
| **Agentic ingestion (multi-step reasoning)** | Agentic RAG patterns (query expansion, HyDE, critic loops) are retrieval-time features. They do not belong in ingestion. | Build a simple, deterministic pipeline. Agent-based retrieval is a future enhancement. |

### Scope Creep

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Retrieval API server** | The ingestion pipeline writes to pgvector. Building a FastAPI retrieval server is a separate project (the consumers -- IDE extension and chat). | Document the SQL queries for retrieval (Chapter 6 already provides them). Provide a `query_example.py` script for testing, not a server. |
| **Web UI for ingestion management** | A dashboard for monitoring ingestion is production infrastructure. The starter kit is a CLI tool. | Console logging + summary report printed to stdout. |
| **Automated web crawling with link discovery** | Recursively crawling documentation.basis.cloud could pull in thousands of pages including navigation chrome, duplicate content, and irrelevant pages. | Curated URL lists per source type. For MadCap Flare, use the Clean XHTML export (file system, not crawl). For Advantage/KB, maintain a list of known article URLs. |
| **Multi-language embedding support** | BBj docs are English only. No need for multilingual embedding models. | Choose an English-optimized model. If multilingual is free (e.g., BGE-M3 handles English well), fine, but don't select a model specifically for multilingual capability. |
| **OCR for scanned content** | The BBj corpus is authored digital text (XHTML, HTML, MDX, PDF). No scanned documents. | Skip OCR entirely. If a specific PDF turns out to be image-based, flag it for manual review. |
| **BBj source code ingestion** | Chapter 6's source corpus table lists "BBj source code" as a supporting corpus, but PROJECT.md's active requirements list only 5 sources. Source code parsing (AST extraction, function boundary detection) is a distinct problem. | Defer to a future milestone. The 5 defined sources are sufficient for the initial RAG database. |

---

## Feature Dependencies

### Dependencies on Chapter 6 Design

| Feature | Chapter 6 Dependency | Status |
|---------|---------------------|--------|
| pgvector schema creation | Schema conceptually defined (doc structure examples in Chapter 6) but not formalized as DDL | Needs: concrete CREATE TABLE DDL |
| Generation labels | 5-label taxonomy defined: `all`, `character`, `vpro5`, `bbj-gui`, `dwc` | Ready |
| Document types | 7 types defined: `api-reference`, `concept`, `example`, `migration`, `language-reference`, `best-practice`, `version-note` | Ready |
| Chunk sizes by type | Defined in Chapter 6 table (API: 200-400, concept: 400-600, code: variable, migration: 400-600, language: 300-500) | Ready |
| Contextual chunk headers | Described in Chapter 6, format established | Ready |
| Chunk overlap | 10-15% specified | Ready |
| Hybrid search columns | Need both vector column (embedding) and tsvector column (search_vector) | Ready (design), needs DDL |
| Supersedes/superseded_by | Described in Chapter 6 document examples | Needs: lookup table of known API pairs |
| Generation scoring logic | TypeScript pseudocode in Chapter 6 | Needs: Python translation for validation |

### Internal Feature Dependencies

```
Parsing (per source type)
  --> Heading hierarchy extraction
    --> Contextual chunk headers (CCH)
      --> Embedding generation
        --> pgvector storage

Document type classification
  --> Chunk size selection
    --> Token-aware splitting
      --> Embedding generation

Generation classification signals
  --> Generation tagging
    --> Multi-generation tag support
      --> pgvector storage (generation TEXT[] column)

Configuration file
  --> All other features (paths, DB connection, model name)

Content hashing
  --> Idempotent ingestion (upsert logic)
```

### External Dependencies

| Dependency | What It Blocks | Status |
|-----------|---------------|--------|
| PostgreSQL with pgvector extension | All storage features | Engineer must provision locally (Docker or native install) |
| MadCap Flare Clean XHTML export | Flare source parsing | Requires access to Flare project OR fallback to crawl |
| Embedding model download | Embedding generation | First run downloads model (~1-4 GB depending on model) |
| Python 3.10+ | pymupdf4llm requirement | Standard for 2026 |
| GPU (optional) | Embedding speed | CPU works but slower. GPU recommended for full corpus (50K chunks). |

---

## Implementation Priority for v1.2

### Phase 1: Schema + Core Parsing (Build First)

These must work before anything else can be validated.

| Feature | Complexity | Rationale |
|---------|-----------|-----------|
| Configuration file | Low | Everything else reads from config |
| pgvector schema creation (DDL) | Low | Must exist before any data can be stored |
| XHTML parser for Flare docs | Low | Primary corpus; validates the entire pipeline |
| Heading hierarchy extraction | Low | Required for CCH |
| Contextual chunk headers | Low | Highest-impact retrieval quality feature |
| Token-aware splitting with overlap | Low | Core chunking logic |
| Code block integrity | Medium | BBj code samples are high-value content |
| Logging + error handling | Low | Must be present from day one |

### Phase 2: Generation + Type Classification

The BBj-specific intelligence layer.

| Feature | Complexity | Rationale |
|---------|-----------|-----------|
| Generation classification signals | High | The defining differentiator; determines pipeline's value |
| Document type classification | Medium | Drives chunk sizing |
| Chunk size variation by type | Low | Depends on doc type classification |
| Default generation fallback | Low | Safety net for ambiguous content |

### Phase 3: Embedding + Storage

Actually producing the vector database.

| Feature | Complexity | Rationale |
|---------|-----------|-----------|
| Embedding generation (batch) | Medium | Requires model selection and GPU/CPU decision |
| Chunk insertion with metadata | Low | Standard SQL |
| Full-text search vector column | Low | Populated at insertion time |
| Content hashing + idempotent upsert | Low | Data integrity |
| HNSW index creation | Low | Post-bulk-insert optimization |
| Deterministic chunk IDs | Low | Enables re-runs |
| Source URL tracking | Low | Required for citations |

### Phase 4: Additional Sources

Extend beyond Flare to the other 4 source types.

| Feature | Complexity | Rationale |
|---------|-----------|-----------|
| PDF text extraction | Low | pymupdf4llm handles this cleanly |
| HTML scraping for Advantage articles | Medium | WordPress HTML parsing |
| Knowledge Base scraping | Medium | WordPress/LearnPress; try REST API first |
| MDX extraction for DWC-Course | Medium | Clone repo, strip JSX, extract content |
| Source-by-source CLI invocation | Low | Ties it all together |

### Phase 5: Quality + Reporting

Validate and verify the output.

| Feature | Complexity | Rationale |
|---------|-----------|-----------|
| Post-ingestion summary report | Low | Essential feedback loop |
| Generation tag distribution report | Low | Validates classification quality |
| Orphan detection | Low | Catches gaps |
| Query example script | Low | Proves the pipeline produces usable data |

---

## Key Observations

1. **Generation tagging is the make-or-break feature.** Without it, this is a generic RAG pipeline. With it, it solves BBj's core problem: generation-aware retrieval. Budget the most research and iteration time for the classification heuristics.

2. **Contextual chunk headers are the highest-ROI generic feature.** They are simple to implement (string concatenation of heading hierarchy) but have outsized impact on retrieval quality. FinanceBench benchmark: 83% vs. 19% baseline. Do this before any other optimization.

3. **The Flare parser is the critical path.** MadCap Flare docs are the primary corpus. If the Flare parser works well, the pipeline delivers value even before the other 4 sources are connected. Prioritize Flare over the others.

4. **Document type classification drives everything downstream.** Chunk size, retrieval boosting, and generation inference all depend on knowing whether a chunk is an API reference, concept, or example. Get this right and the rest follows.

5. **Idempotent ingestion is non-negotiable for a starter kit.** Engineers will run the pipeline multiple times during development. If re-runs create duplicates, the database becomes unusable fast. Content hashing + upsert must be there from day one.

6. **The five source types have very different parsing needs but identical output format.** Each source requires a custom parser, but all parsers produce the same intermediate representation (chunks with metadata). The architecture should enforce a common `ChunkDocument` interface that all parsers output.

7. **Anti-features are load-bearing.** The strongest temptation will be to build a retrieval API server, add agentic features, or set up CI/CD. These are all valuable but belong in future milestones. The v1.2 deliverable is a script that fills a database, not an application.

---

## Sources

### HIGH Confidence (Context7/Official Documentation)
- Chapter 6: RAG Database Design (project source, `/docs/06-rag-database/index.md`) -- schema, chunking strategy, generation taxonomy, retrieval architecture
- MadCap Flare Clean XHTML documentation: [MadCap Software Blog](https://www.madcapsoftware.com/blog/new-feature-highlight-clean-xhtml-output-madcap-flare-2017/)
- pgvector-python official: [github.com/pgvector/pgvector-python](https://github.com/pgvector/pgvector-python)
- pymupdf4llm: [PyPI](https://pypi.org/project/pymupdf4llm/), [PyMuPDF RAG docs](https://pymupdf.readthedocs.io/en/latest/rag.html)
- LlamaIndex ingestion pipeline: [docs.llamaindex.ai](https://docs.llamaindex.ai/en/stable/module_guides/loading/ingestion_pipeline/)

### MEDIUM Confidence (WebSearch verified with multiple sources)
- Contextual chunk headers technique: [NirDiamant/RAG_Techniques](https://github.com/NirDiamant/RAG_Techniques/blob/main/all_rag_techniques/contextual_chunk_headers.ipynb), [Snowflake FinanceBench](https://www.snowflake.com/en/engineering-blog/impact-retrieval-chunking-finance-rag/)
- Chunking best practices (300-500 tokens, 10-20% overlap): [Firecrawl](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025), [Weaviate](https://weaviate.io/blog/chunking-strategies-for-rag), [Databricks](https://docs.databricks.com/aws/en/generative-ai/tutorials/ai-cookbook/quality-data-pipeline-rag)
- Embedding model landscape (Qwen3-Embedding, BGE-M3): [BentoML guide](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models), [VentureBeat MTEB](https://venturebeat.com/ai/new-embedding-model-leaderboard-shakeup-google-takes-1-while-alibabas-open-source-alternative-closes-gap/), [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
- Metadata filtering in RAG: [Unstructured](https://unstructured.io/insights/how-to-use-metadata-in-rag-for-better-contextual-results), [Haystack](https://haystack.deepset.ai/blog/extracting-metadata-filter)
- Deduplication / idempotent ingestion: [Databricks](https://docs.databricks.com/aws/en/generative-ai/tutorials/ai-cookbook/quality-data-pipeline-rag), [IBM RAG Cookbook](https://www.ibm.com/architectures/papers/rag-cookbook/data-ingestion)
- LangChain vs. LlamaIndex 2026: [rahulkolekar.com](https://rahulkolekar.com/langchain-vs-llamaindex-2026-which-is-best-for-production-rag/)

### LOW Confidence (Single sources, needs validation)
- WordPress REST API availability for basis.cloud/knowledge-base/ -- assumed based on WordPress standard, not verified
- Advantage article count (~6 visible on index page, may have more behind pagination)
- MadCap Flare TOC file format -- described conceptually, not verified against actual export
