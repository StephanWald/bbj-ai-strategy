# Phase 21: Data Configuration + Ingestion - Research

**Researched:** 2026-02-01
**Domain:** CLI orchestration, config-driven ingestion, pgvector upsert, batch resume
**Confidence:** HIGH

## Summary

Phase 21 wires all 6 BBj documentation sources into a config-driven ingestion pipeline that runs against the pgvector database from Phase 20. The existing codebase already has all 6 parsers implemented (Flare, PDF, MDX, BBj source, WordPress Advantage/KB, web crawl), a working pipeline module (`pipeline.py`) that does parse -> intelligence -> chunk -> embed -> store, and a Click-based CLI (`cli.py`) with per-source `ingest` and `parse` commands.

The work in this phase is: (1) create an external source config file defining all 6 sources with paths, parser types, generation tags, and enabled flags; (2) extend the MdxParser to handle multiple directories (3 separate tutorial repos); (3) build a standalone orchestration CLI script that reads the config, validates all paths, and runs ingestion across all enabled sources with progress reporting, resume capability, and a --clean flag.

**Primary recommendation:** Use TOML for the sources config file (consistent with existing config.toml pattern and Python ecosystem standard). Keep the orchestration script as a standalone Click CLI separate from the existing `bbj-rag` CLI entry point. Use database-side content_hash for upsert/idempotency (already implemented) and a lightweight JSON state file for source-level resume tracking.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | >=8.1,<9 | CLI framework | Already used in project (`cli.py`). All 6 parser commands already wired through Click. |
| tomllib | stdlib (3.12) | TOML parsing | Built into Python 3.12 (project minimum). No extra dependency needed. |
| pydantic | >=2.12,<3 | Config validation | Already used for Document/Chunk models. Validates source config entries. |
| psycopg | >=3.3,<4 | Database operations | Already used. ON CONFLICT content_hash dedup already implemented in `db.py`. |
| pgvector | >=0.4,<0.5 | Vector type registration | Already used. `register_vector(conn)` in `db.py`. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| concurrent.futures | stdlib | Parallel execution | Only if `--parallel` flag is used. ThreadPoolExecutor for I/O-bound parsers. |
| json | stdlib | Resume state file | Track completed sources for resume capability. |
| time | stdlib | Duration tracking | Per-source and total duration for summary table. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TOML config | YAML config | YAML is already a dependency (pyyaml in pyproject.toml). But TOML is Python ecosystem standard (pyproject.toml), matches existing config.toml pattern, and has stdlib support via tomllib. TOML wins. |
| Standalone CLI script | FastAPI management command | User decision: standalone CLI, not FastAPI command. Correct choice -- ingestion is a batch operation, not a web request. |
| JSON state file for resume | Database marker table | JSON file is simpler, no schema migration needed, works outside Docker. Database marker adds coupling. |
| ThreadPoolExecutor | asyncio | Parsers are synchronous (file I/O, httpx sync client). Threading is simpler and sufficient. asyncio would require rewriting parsers. |

**Installation:**
```bash
# No new dependencies needed -- all libraries already in pyproject.toml or stdlib
```

## Architecture Patterns

### Recommended Project Structure

```
rag-ingestion/
├── sources.toml               # NEW: Source definitions (6 sources)
├── config.toml                # EXISTING: DB/embedding settings
├── .env                       # EXISTING: Docker env vars
├── src/bbj_rag/
│   ├── cli.py                 # EXISTING: bbj-rag CLI (per-source)
│   ├── ingest_all.py          # NEW: Orchestration CLI (all sources)
│   ├── source_config.py       # NEW: Source config loader + validation
│   ├── pipeline.py            # EXISTING: parse->chunk->embed->store
│   └── parsers/
│       ├── mdx.py             # MODIFIED: Accept list[Path] for multi-dir
│       └── ...                # EXISTING: All 6 parsers unchanged
└── .ingestion-state.json      # NEW: Resume tracking (gitignored)
```

### Pattern 1: TOML Array-of-Tables for Source Config

**What:** Define each source as a `[[sources]]` entry in TOML with parser type, paths, generation tag, and enabled flag.
**When to use:** When you need a list of heterogeneous structured entries with clear field names.

```toml
# sources.toml -- All 6 BBj documentation sources

# Base directory for relative path resolution.
# Override with DATA_DIR env var or CLI flag.
data_dir = "/Users/beff/_workspace"

[[sources]]
name = "flare"
parser = "flare"
paths = ["bbjdocs"]              # relative to data_dir
generation_tag = "bbj"
enabled = true

[[sources]]
name = "pdf"
parser = "pdf"
paths = ["bbj-ai-strategy/GuideToGuiProgrammingInBBj.pdf"]
generation_tag = "bbj_gui"
enabled = true

[[sources]]
name = "mdx-dwc"
parser = "mdx"
paths = ["bbj-dwc-tutorial/docs"]
generation_tag = "dwc"
enabled = true

[[sources]]
name = "mdx-beginner"
parser = "mdx"
paths = ["bbj-beginner-tutorial/docs"]
generation_tag = "bbj"
enabled = true

[[sources]]
name = "mdx-db-modernization"
parser = "mdx"
paths = ["bbj-db-modernization-tutorial/docs"]
generation_tag = "bbj"
enabled = true

[[sources]]
name = "bbj-source"
parser = "bbj-source"
paths = [
    "bbj-dwc-tutorial/samples",
    "bbj-beginner-tutorial"
]
generation_tag = "auto"           # parser does its own classification
enabled = true

[[sources]]
name = "wordpress-advantage"
parser = "wordpress-advantage"
paths = []                         # URL-based, no local paths
generation_tag = "bbj"
enabled = true

[[sources]]
name = "wordpress-kb"
parser = "wordpress-kb"
paths = []
generation_tag = "bbj"
enabled = true

[[sources]]
name = "web-crawl"
parser = "web-crawl"
paths = []
generation_tag = "bbj"
enabled = true
```

**Key design choice for MDX:** Use **separate entries** per MDX tutorial directory (not one entry with multiple paths). Rationale:
- Each tutorial is a separate repo with its own generation tag (dwc vs bbj)
- Separate entries allow independent enable/disable
- Resume tracking works at source level, so each MDX dir can resume independently
- The MdxParser already takes a single `docs_dir: Path` -- no refactor needed
- The orchestration script instantiates one MdxParser per entry

### Pattern 2: Fail-Fast Pre-Validation

**What:** Before starting any ingestion, validate all enabled sources: check that paths exist, config is well-formed, database is reachable, and embedder is available.
**When to use:** Always. Catches misconfigurations before any slow work begins.

```python
def validate_sources(sources: list[SourceConfig], data_dir: Path) -> list[str]:
    """Return list of error messages. Empty list means all valid."""
    errors = []
    for src in sources:
        if not src.enabled:
            continue
        for rel_path in src.paths:
            full_path = data_dir / rel_path
            if src.parser in ("flare", "mdx", "bbj-source"):
                if not full_path.is_dir():
                    errors.append(f"{src.name}: directory not found: {full_path}")
            elif src.parser == "pdf":
                if not full_path.is_file():
                    errors.append(f"{src.name}: file not found: {full_path}")
            # URL-based parsers (wordpress-*, web-crawl) skip path validation
    return errors
```

### Pattern 3: Source-Level Orchestration with Continue-on-Failure

**What:** Run each source sequentially through the existing `run_pipeline()`. If a source fails, log the error and continue to the next source. Report all failures at the end.
**When to use:** Production ingestion runs where partial progress is better than total failure.

```python
results = {}
failures = {}

for source in enabled_sources:
    try:
        parser = create_parser_for_source(source, data_dir, settings)
        stats = run_pipeline(parser, embedder, conn, ...)
        results[source.name] = stats
        save_resume_state(source.name, "completed")
    except Exception as exc:
        failures[source.name] = str(exc)
        logger.error("Source %s failed: %s", source.name, exc)
        # Partial data kept in DB (not rolled back) per user decision

print_summary_table(results, failures, durations)
```

### Pattern 4: Upsert with --clean Flag

**What:** Default to upsert (ON CONFLICT content_hash DO NOTHING, already implemented). With `--clean`, delete existing chunks for a source before re-ingesting.
**When to use:** `--clean` when parser logic or chunking strategy changes and old data must be replaced.

```python
def clean_source(conn, source_name: str, source_url_prefix: str) -> int:
    """Delete all chunks matching a source's URL prefix."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM chunks WHERE source_url LIKE %s",
            (f"{source_url_prefix}%",)
        )
        count = cur.rowcount
    conn.commit()
    return count
```

Source URL prefix mapping (from existing parsers):
| Source | source_url prefix |
|--------|------------------|
| flare | `flare://` |
| pdf | `pdf://` |
| mdx-dwc | `dwc-course://` |
| mdx-beginner | `dwc-course://` (needs update -- see pitfalls) |
| mdx-db-modernization | `dwc-course://` (needs update -- see pitfalls) |
| bbj-source | `file://` |
| wordpress-advantage | `https://basis.cloud/advantage` |
| wordpress-kb | `https://basis.cloud/knowledge-base` |
| web-crawl | `https://documentation.basis.cloud` |

### Pattern 5: Resume via JSON State File

**What:** Track which sources completed successfully in a `.ingestion-state.json` file. On resume, skip completed sources.
**When to use:** When a long ingestion run is interrupted (network failure during web crawl, Ollama crash, etc.).

```python
# .ingestion-state.json
{
    "run_id": "2026-02-01T12:00:00",
    "completed_sources": ["flare", "pdf", "mdx-dwc"],
    "failed_sources": {"web-crawl": "httpx.ConnectError: ..."}
}
```

```python
def load_resume_state(state_file: Path) -> dict:
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {"completed_sources": [], "failed_sources": {}}

def save_resume_state(state_file: Path, state: dict) -> None:
    state_file.write_text(json.dumps(state, indent=2))
```

The `--resume` flag checks this file and skips sources listed in `completed_sources`. A new `--fresh` or default run clears the state file first.

### Anti-Patterns to Avoid

- **Hardcoding source paths in Python:** All 6 sources must come from the TOML config file, not from Python constants. The existing `config.py` Settings fields (`flare_source_path`, `mdx_source_path`, etc.) are superseded by `sources.toml`.
- **One MdxParser with multiple dirs:** Don't modify MdxParser to accept `list[Path]`. Instead, instantiate one MdxParser per MDX config entry. Simpler, no refactor needed, and each MDX source gets its own generation tag and resume tracking.
- **Rolling back on source failure:** User decision is to keep partial data. Don't wrap ingestion in a transaction that rolls back on failure.
- **Global parallel by default:** Web-crawl and WordPress parsers use rate-limited HTTP. Parallel execution of these with CPU-bound parsers is fine, but two HTTP-based parsers in parallel could cause rate-limiting issues or IP blocks. Default to sequential.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Content deduplication | Custom hash tracking | Existing `ON CONFLICT (content_hash) DO NOTHING` in `db.py` | Already implemented, battle-tested, handles concurrent inserts |
| TOML parsing | Custom parser | `tomllib` (stdlib Python 3.12) | Zero dependencies, correct spec compliance |
| Config validation | Manual if/else checks | Pydantic model for source config | Type safety, clear error messages, serialization |
| Embedding batching | Custom batch logic | Existing `run_pipeline()` with `batch_size` parameter | Already handles batching, resume, and progress logging |
| Progress reporting | Custom progress bars | Simple print statements with per-source summary | CLI decision: stdout only, no log file. Keep it simple. |
| Parallel execution | Custom threading | `concurrent.futures.ThreadPoolExecutor` | stdlib, well-tested, simple API |

**Key insight:** The existing `pipeline.py` `run_pipeline()` function already handles the hard parts (batching, embedding, dedup insert, progress logging). The orchestration script's job is just config loading, path validation, parser instantiation, and source-level looping. Don't duplicate pipeline logic.

## Common Pitfalls

### Pitfall 1: MDX source_url Collision Across Tutorial Directories

**What goes wrong:** The current MdxParser uses `dwc-course://{relative_path}` as source_url for all documents. If three different MDX tutorial dirs are ingested, documents from different tutorials could collide on `relative_path` (e.g., all three might have an `index.md`).
**Why it happens:** MdxParser was originally built for a single DWC-Course directory.
**How to avoid:** Each MDX source entry must produce a distinct source_url prefix. Options:
  - Pass a `source_prefix` parameter to MdxParser: `MdxParser(docs_dir=path, source_prefix="mdx-beginner")` producing `mdx-beginner://index.md`
  - Or derive prefix from the config entry name: `{source_name}://{relative_path}`
  This also fixes the `--clean` flag: each MDX source can be cleaned independently by its prefix.
**Warning signs:** Chunks from different tutorials appearing with identical source_urls; `--clean` for one MDX source deleting chunks from all MDX sources.

### Pitfall 2: Report Module source_url Pattern Mismatch

**What goes wrong:** The existing `intelligence/report.py` uses `WHEN source_url LIKE 'mdx://%%' THEN 'mdx'` but the actual MdxParser produces `dwc-course://` URLs. The report will miscategorize MDX chunks.
**Why it happens:** The report was written before the MDX parser was finalized, or was written with a different convention in mind.
**How to avoid:** When updating source_url prefixes for multi-MDX support, also update the report SQL CASE expressions to match the new prefixes. If using per-source prefixes like `mdx-dwc://`, `mdx-beginner://`, consider a pattern like `WHEN source_url LIKE 'mdx-%%' THEN 'mdx'` or adding more granular entries.
**Warning signs:** The quality report showing 0 MDX chunks after successful MDX ingestion.

### Pitfall 3: DATA_DIR Path Resolution in Docker vs Host

**What goes wrong:** `sources.toml` is authored on the host with paths like `bbjdocs/` relative to `/Users/beff/_workspace`. Inside Docker, the data mount is at `/data`. If `data_dir` in sources.toml points to a host path, it won't work in Docker.
**Why it happens:** The TOML file is shared between host and Docker environments.
**How to avoid:** Allow `data_dir` to be overridden by environment variable (e.g., `DATA_DIR=/data`). The orchestration script checks: env var first, then TOML `data_dir` key. Docker sets `DATA_DIR=/data`, host uses the TOML value.
**Warning signs:** "directory not found" errors when running inside Docker despite all sources existing on host.

### Pitfall 4: Embedding Model Must Be Pulled Before Ingestion

**What goes wrong:** Running ingestion without `ollama pull qwen3-embedding:0.6b` first causes a cryptic Ollama error partway through (after parsing succeeds but before embedding).
**Why it happens:** Fail-fast validation checks paths and database but not the embedding model availability.
**How to avoid:** Add an embedding model check to fail-fast validation: attempt a single test embedding during validation. If Ollama returns an error, fail immediately with a helpful message including `ollama pull {model}`.
**Warning signs:** Parser succeeds, then pipeline crashes at embedding step with "model not found" error.

### Pitfall 5: Web Crawl Parser is Very Slow

**What goes wrong:** The web crawl parser fetches hundreds of pages from documentation.basis.cloud with a 0.5s rate limit per request. At 500+ pages, this takes 4+ minutes minimum. If it fails partway, resume is critical.
**Why it happens:** Rate-limiting is necessary to avoid being blocked.
**How to avoid:** Put web-crawl last in the source order. The resume mechanism saves progress at the source level (not per-document), so a failed web crawl doesn't lose work from other sources. Consider making web-crawl optional (enabled=false by default) since Flare is the primary source for the same content.
**Warning signs:** Ingestion appearing to hang during web crawl phase; total ingestion time exceeding 30 minutes.

### Pitfall 6: PostgreSQL Connection Timeout During Long Ingestion

**What goes wrong:** A single psycopg connection held open for 30+ minutes of ingestion may hit server-side idle timeout or be killed by connection pooler.
**Why it happens:** The pipeline uses a single connection for the entire run.
**How to avoid:** Use `conn.execute("SELECT 1")` keepalive between sources, or open a fresh connection per source. The existing `get_connection()` / `get_connection_from_settings()` makes this easy.
**Warning signs:** "connection closed" or "server closed the connection unexpectedly" errors mid-ingestion.

### Pitfall 7: shm_size Exhaustion During Large HNSW Index Builds

**What goes wrong:** After inserting thousands of chunks with embeddings, PostgreSQL may need to rebuild/update the HNSW index. With `shm_size: 256mb` (current setting), very large corpora could exhaust shared memory.
**Why it happens:** HNSW index maintenance uses shared memory proportional to the index size.
**How to avoid:** Monitor with `docker stats`. If the corpus exceeds ~50K chunks, consider increasing `shm_size` to `512mb` or `1gb` in docker-compose.yml. The current 6-source corpus is likely 5K-15K chunks, well within 256mb.
**Warning signs:** PostgreSQL crashes or `ERROR: could not resize shared memory segment` during ingestion.

## Code Examples

### Source Config Pydantic Model

```python
# source_config.py
from __future__ import annotations

import tomllib
from pathlib import Path
from pydantic import BaseModel, field_validator


class SourceEntry(BaseModel):
    """A single documentation source from sources.toml."""
    name: str
    parser: str  # "flare", "pdf", "mdx", "bbj-source", "wordpress-advantage", "wordpress-kb", "web-crawl"
    paths: list[str] = []
    generation_tag: str = "bbj"
    enabled: bool = True

    @field_validator("parser")
    @classmethod
    def parser_must_be_known(cls, v: str) -> str:
        known = {"flare", "pdf", "mdx", "bbj-source", "wordpress-advantage", "wordpress-kb", "web-crawl"}
        if v not in known:
            raise ValueError(f"Unknown parser: {v}. Must be one of: {sorted(known)}")
        return v


class SourcesConfig(BaseModel):
    """Top-level sources.toml structure."""
    data_dir: str = ""
    sources: list[SourceEntry]


def load_sources_config(config_path: Path) -> SourcesConfig:
    """Load and validate sources.toml."""
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)
    return SourcesConfig.model_validate(raw)
```

### Orchestration CLI Entry Point

```python
# ingest_all.py
import click
import json
import time
from pathlib import Path

@click.command()
@click.option("--config", default="sources.toml", type=click.Path(exists=True))
@click.option("--clean", is_flag=True, help="Wipe and re-ingest all enabled sources")
@click.option("--resume", is_flag=True, help="Skip completed sources from previous run")
@click.option("--parallel", is_flag=True, help="Run file-based sources in parallel")
@click.option("--verbose", "-v", is_flag=True, help="Per-file progress output")
@click.option("--source", multiple=True, help="Run only named sources (repeatable)")
def ingest_all(config, clean, resume, parallel, verbose, source):
    """Ingest all configured documentation sources."""
    ...
```

### Parser Factory from Source Config

```python
def create_parser_for_source(
    source: SourceEntry,
    data_dir: Path,
    settings: Settings,
) -> DocumentParser:
    """Create the appropriate parser based on source config entry."""
    if source.parser == "flare":
        from bbj_rag.parsers.flare import FlareParser
        project_dir = data_dir / source.paths[0]
        return FlareParser(content_dir=project_dir / "Content", project_dir=project_dir)

    if source.parser == "pdf":
        from bbj_rag.parsers.pdf import PdfParser
        return PdfParser(pdf_path=data_dir / source.paths[0])

    if source.parser == "mdx":
        from bbj_rag.parsers.mdx import MdxParser
        return MdxParser(docs_dir=data_dir / source.paths[0])

    if source.parser == "bbj-source":
        from bbj_rag.parsers.bbj_source import BbjSourceParser
        dirs = [data_dir / p for p in source.paths]
        return BbjSourceParser(source_dirs=dirs)

    if source.parser == "wordpress-advantage":
        from bbj_rag.parsers.wordpress import AdvantageParser
        return AdvantageParser(index_url=settings.advantage_index_url)

    if source.parser == "wordpress-kb":
        from bbj_rag.parsers.wordpress import KnowledgeBaseParser
        return KnowledgeBaseParser(index_url=settings.kb_index_url)

    if source.parser == "web-crawl":
        from bbj_rag.parsers.web_crawl import WebCrawlParser
        return WebCrawlParser()

    raise ValueError(f"Unknown parser: {source.parser}")
```

### Clean Source Before Re-Ingestion

```python
# Source URL prefix mapping for --clean
_SOURCE_URL_PREFIXES: dict[str, str] = {
    "flare": "flare://",
    "pdf": "pdf://",
    "bbj-source": "file://",
    "wordpress-advantage": "https://basis.cloud/advantage",
    "wordpress-kb": "https://basis.cloud/knowledge-base",
    "web-crawl": "https://documentation.basis.cloud",
    # MDX sources use their config name as prefix: "mdx-dwc://", "mdx-beginner://", etc.
}

def get_source_url_prefix(source: SourceEntry) -> str:
    """Get the source_url prefix for a source, used for --clean deletion."""
    if source.parser == "mdx":
        return f"{source.name}://"
    return _SOURCE_URL_PREFIXES[source.parser]

def clean_source_chunks(conn, prefix: str) -> int:
    """Delete all chunks matching the given source_url prefix."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM chunks WHERE source_url LIKE %s", (f"{prefix}%",))
        count = cur.rowcount
    conn.commit()
    return count
```

### Summary Table Output

```python
def print_summary_table(
    results: dict[str, dict[str, int]],
    failures: dict[str, str],
    durations: dict[str, float],
) -> None:
    """Print a formatted summary table to stdout."""
    click.echo("\n" + "=" * 72)
    click.echo(f"  {'Source':<25} {'Files':>7} {'Chunks':>8} {'Duration':>10} {'Status':>8}")
    click.echo("-" * 72)

    for name, stats in results.items():
        dur = f"{durations.get(name, 0):.1f}s"
        click.echo(
            f"  {name:<25} {stats['docs_parsed']:>7} "
            f"{stats['chunks_stored']:>8} {dur:>10} {'OK':>8}"
        )

    for name, error in failures.items():
        dur = f"{durations.get(name, 0):.1f}s"
        click.echo(f"  {name:<25} {'--':>7} {'--':>8} {dur:>10} {'FAILED':>8}")

    click.echo("=" * 72)
    total_docs = sum(s["docs_parsed"] for s in results.values())
    total_chunks = sum(s["chunks_stored"] for s in results.values())
    total_dur = sum(durations.values())
    click.echo(f"  Total: {total_docs} docs, {total_chunks} chunks, {total_dur:.1f}s")
    if failures:
        click.echo(f"  Failures: {', '.join(failures.keys())}")
```

## Claude's Discretion Recommendations

### 1. Config File Format: TOML (recommended)

**Decision:** Use TOML for `sources.toml`.

**Rationale:**
- The project already uses `config.toml` for database/embedding settings
- Python 3.12 includes `tomllib` in stdlib -- zero new dependencies
- TOML `[[sources]]` array-of-tables syntax maps cleanly to `list[SourceEntry]`
- pydantic-settings already has `TomlConfigSettingsSource` if integration is desired later
- TOML's explicit typing avoids YAML's notorious type-coercion gotchas (e.g., `NO` becoming `False`)
- YAML is also in `pyproject.toml` dependencies (pyyaml), so either would work, but TOML is more consistent with the project's existing patterns

### 2. Multi-MDX Structure: Separate Entries (recommended)

**Decision:** Define each MDX tutorial directory as its own `[[sources]]` entry.

**Rationale:**
- Three tutorials have different generation tags: DWC tutorial = "dwc", beginner = "bbj", DB modernization = "bbj"
- Separate entries allow independent enable/disable per tutorial
- Resume tracking works at source level -- each tutorial can resume independently
- The MdxParser constructor takes a single `docs_dir: Path` -- no refactor needed
- Each entry gets its own source_url prefix for clean `--clean` support (e.g., `mdx-dwc://`, `mdx-beginner://`, `mdx-db-modernization://`)
- Tradeoff: 3 entries instead of 1, but the config is clearer and more flexible

### 3. Sequential Default with --parallel Flag (recommended)

**Decision:** Default to sequential execution. Expose `--parallel` flag for advanced users.

**Rationale:**
- Web crawl and WordPress parsers use rate-limited HTTP -- running them in parallel with each other risks IP blocking
- Sequential is easier to debug and produces cleaner logs
- The total corpus is ~5K-15K chunks across 6 sources -- sequential completes in ~10-20 minutes
- Parallel mode can use `ThreadPoolExecutor` to run file-based parsers (Flare, PDF, MDX, BBj source) concurrently while HTTP-based parsers (WordPress, web crawl) run sequentially
- The `--parallel` flag exists but most users won't need it

### 4. Verbosity Levels (recommended)

**Decision:** Two levels: default (per-source summary) and `--verbose` (per-file detail).

**Default output:**
```
Validating sources... OK (6 sources, 3 with local paths)
[1/6] flare ........... 1,247 docs -> 4,521 chunks (45.2s)
[2/6] pdf ............. 89 docs -> 312 chunks (8.1s)
[3/6] mdx-dwc ........ 27 docs -> 156 chunks (3.2s)
[4/6] mdx-beginner ... 45 docs -> 234 chunks (4.1s)
[5/6] mdx-db-mod ..... 26 docs -> 189 chunks (3.5s)
[6/6] bbj-source ...... 72 docs -> 72 chunks (12.3s)
```

**Verbose output (with --verbose or -v):**
Adds per-file lines within each source:
```
[1/6] flare
  Content/bbjobjects/Window/bbjwindow.htm -> 5 chunks
  Content/bbjobjects/Window/bbjwindow_addbutton.htm -> 3 chunks
  ...
  1,247 docs -> 4,521 chunks (45.2s)
```

Generation tags are shown in verbose mode only, appended to each file line.

### 5. Resume Tracking: JSON State File (recommended)

**Decision:** Use `.ingestion-state.json` in the working directory.

**Rationale:**
- Simpler than a database marker table -- no schema migration needed
- Works when running outside Docker (no database required to check state)
- Human-readable for debugging: just `cat .ingestion-state.json`
- `.ingestion-state.json` added to `.gitignore`
- State is per-source (not per-document) -- matches the source-level orchestration pattern
- A new run without `--resume` clears the state file first
- Tradeoff: doesn't survive `docker compose down` (container filesystem is ephemeral), but the data volume mount makes this irrelevant -- the state file lives on the host

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single `mdx_source_path` setting | Multi-source TOML config | This phase | Supports 3 MDX tutorial dirs |
| Per-source CLI commands (`bbj-rag ingest --source flare`) | Orchestration script ingesting all sources | This phase | Single command for full corpus |
| No resume capability | JSON state file + `--resume` flag | This phase | Interrupted runs can continue |
| ON CONFLICT DO NOTHING only | + `--clean` flag for wipe-and-rewrite | This phase | Supports re-ingestion after model changes |

**Deprecated/outdated:**
- The individual `*_source_path` fields in `config.py` (e.g., `flare_source_path`, `mdx_source_path`) are superseded by `sources.toml` but should be kept for backward compatibility with the existing `bbj-rag ingest --source <name>` CLI commands.

## Real Data Paths (Verified on Host)

The following paths have been verified to exist on the host machine:

| Source | Parser | Real Path | File Count |
|--------|--------|-----------|------------|
| Flare | `flare` | `/Users/beff/bbjdocs/` (Content/ and Project/ dirs) | ~1,200+ .htm files |
| PDF | `pdf` | `/Users/beff/_workspace/bbj-ai-strategy/GuideToGuiProgrammingInBBj.pdf` | 1 file |
| MDX DWC | `mdx` | `/Users/beff/_workspace/bbj-dwc-tutorial/docs/` | 27 .md/.mdx files |
| MDX Beginner | `mdx` | `/Users/beff/_workspace/bbj-beginner-tutorial/docs/` | 45 .md/.mdx files |
| MDX DB Modernization | `mdx` | `/Users/beff/_workspace/bbj-db-modernization-tutorial/docs/` | 26 .md/.mdx files |
| BBj Source (DWC samples) | `bbj-source` | `/Users/beff/_workspace/bbj-dwc-tutorial/samples/` | 44 .bbj files |
| BBj Source (Beginner) | `bbj-source` | `/Users/beff/_workspace/bbj-beginner-tutorial/` | 28 .bbj files |
| WordPress Advantage | `wordpress-advantage` | URL-based: `https://basis.cloud/advantage-index/` | ~50-100 articles |
| WordPress KB | `wordpress-kb` | URL-based: `https://basis.cloud/knowledge-base/` | ~30-50 articles |
| Web Crawl | `web-crawl` | URL-based: `https://documentation.basis.cloud/BASISHelp/WebHelp/` | ~500+ pages |

**data_dir for host:** `/Users/beff/_workspace` (all local sources are relative to this)
**data_dir for Docker:** `/data` (sources mounted via INGESTION_DATA_PATH volume)

## Open Questions

1. **MdxParser source_url prefix update**
   - What we know: MdxParser currently hardcodes `dwc-course://` as prefix. Multi-MDX support requires unique prefixes per MDX source.
   - What's unclear: Should the prefix come from the source config `name` field, or should a separate `source_url_prefix` field be added to the config?
   - Recommendation: Pass a `source_prefix` parameter to MdxParser constructor. Default to `"dwc-course"` for backward compat. Config-driven entries pass `source.name` as prefix.

2. **Whether to keep existing `bbj-rag ingest --source <name>` commands**
   - What we know: The new `ingest_all.py` orchestration script is the primary interface. The old per-source CLI still works.
   - What's unclear: Should the old CLI be updated to read from `sources.toml` too, or remain independent?
   - Recommendation: Keep old CLI as-is. It reads from `config.toml` / env vars. The new orchestration script reads from `sources.toml`. They coexist. The old CLI is useful for debugging individual sources.

3. **Web crawl enable/disable default**
   - What we know: Web crawl is very slow (4+ minutes) and largely redundant with Flare parser output. Flare is the canonical source for documentation.basis.cloud content.
   - What's unclear: Should web crawl be `enabled: false` by default in `sources.toml`?
   - Recommendation: Set `enabled: true` for completeness in the initial config, but document that it can be disabled when Flare is the primary source.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: All 6 parsers, pipeline.py, cli.py, config.py, db.py, schema.sql read and analyzed
- File system verification: All 6 source paths verified on host machine
- Python 3.12 `tomllib` docs: stdlib TOML support confirmed
- TOML v1.0.0 specification: `[[array]]` syntax verified for array-of-tables

### Secondary (MEDIUM confidence)
- [Pydantic Settings docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - TomlConfigSettingsSource nested tables support
- [PostgreSQL ON CONFLICT docs](https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT) - Upsert pattern verified
- [concurrent.futures docs](https://docs.python.org/3/library/concurrent.futures.html) - ThreadPoolExecutor for parallel option
- [Start Data Engineering - Idempotent Pipelines](https://www.startdataengineering.com/post/why-how-idempotent-data-pipeline/) - Delete-write pattern for --clean
- [Prefect - Checkpointing](https://www.prefect.io/blog/the-importance-of-idempotent-data-pipelines-for-resilience) - Resume/checkpoint patterns

### Tertiary (LOW confidence)
- None -- all findings verified with official documentation or codebase analysis

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- patterns derived directly from existing codebase analysis
- Pitfalls: HIGH -- identified from real codebase analysis (source_url collisions, report mismatches are verifiable bugs)
- Data paths: HIGH -- all paths verified on actual filesystem

**Research date:** 2026-02-01
**Valid until:** 2026-03-01 (stable -- no fast-moving dependencies)
