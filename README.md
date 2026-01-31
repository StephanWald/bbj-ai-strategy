# BBj AI Strategy

This repo contains the AI strategy documentation for BBj (a Business BASIC language by BASIS International) and a RAG ingestion pipeline for processing BBj documentation into a vector database. The documentation site covers LLM fine-tuning, IDE integration, documentation chat, and RAG database design across 7 chapters.

**Live site:** https://stephanwald.github.io/bbj-ai-strategy/

## What's Here

- **`/docs`** and root Docusaurus config -- the strategy documentation site (Docusaurus 3, TypeScript, deployed to GitHub Pages)
- **`/rag-ingestion`** -- Python ingestion pipeline for processing BBj documentation sources into pgvector (Python 3.12+, uv)

## Tech Stack

| Component           | Stack                                          |
| ------------------- | ---------------------------------------------- |
| Documentation site  | Docusaurus 3.9, Rspack, TypeScript, GitHub Pages |
| Ingestion pipeline  | Python 3.12+, uv, pgvector/PostgreSQL          |

## Getting Started

**Documentation site** -- visit the [live site](https://stephanwald.github.io/bbj-ai-strategy/) to read the strategy docs.

**Ingestion pipeline** -- set up the Python development environment:

```bash
cd rag-ingestion
uv sync
make check
```

Full setup details will be in `rag-ingestion/README.md`.
