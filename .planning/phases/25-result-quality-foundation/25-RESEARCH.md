# Phase 25: Result Quality Foundation - Research

**Researched:** 2026-02-03
**Domain:** URL mapping, source-balanced ranking, API response enrichment
**Confidence:** HIGH

## Summary

Phase 25 adds two capabilities to the existing RAG pipeline: (1) every search result includes a `display_url` field with a clickable public URL (or bracketed fallback), and (2) minority source types get a ranking boost so Flare's 88% corpus dominance doesn't bury relevant PDF, BBj Source, and MDX results. Both capabilities touch the same code paths -- the search layer, API schemas, and MCP formatting -- so they belong together.

The codebase is well-structured for these additions. The `source_url` field already encodes the source type via its prefix scheme (`flare://`, `pdf://`, `file://`, `mdx-*://`, `https://`). URL mapping is a pure function from `source_url` to `display_url` -- it can be computed at query time or stored at ingestion time. Source-balanced ranking is an application-level post-processing step on top of the existing RRF hybrid search, requiring no SQL changes.

**Primary recommendation:** Add `display_url` and `source_type` fields to the `SearchResult` dataclass and API schemas, implement URL mapping as a utility module, add a post-RRF reranking step for source diversity, and update the MCP server formatting. No database schema migration is needed if mapping is computed at query time; a schema migration is needed if stored at ingestion time (the user chose ingestion-time storage in CONTEXT.md).

## Current Architecture Snapshot

### Source URL Patterns in the Corpus

Each parser produces `source_url` values with distinct prefix schemes. These are the exact patterns found in the codebase:

| Source Type | Parser | source_url Pattern | Example | Chunk Count (from VALIDATION.md) |
|-------------|--------|-------------------|---------|----------------------------------|
| Flare | `FlareParser` | `flare://Content/{relative_path}` | `flare://Content/bbjobjects/Window/bbjbutton/BBjButton.htm` | 44,587 (doc_type: flare) |
| PDF | `PdfParser` | `pdf://{filename}#{slug}` | `pdf://GuideToGuiProgrammingInBBj.pdf#blowing-the-doors-wide-open` | ~140 (doc_type: example/concept) |
| MDX (DWC) | `MdxParser` | `mdx-dwc://{relative_path}` | `mdx-dwc://02-browser-developer-tools/03-css-custom-properties.md` | Part of 954 (doc_type: tutorial) |
| MDX (Beginner) | `MdxParser` | `mdx-beginner://{relative_path}` | `mdx-beginner://10-event-handling/02-events.md` | Part of 954 (doc_type: tutorial) |
| MDX (DB Mod) | `MdxParser` | `mdx-db-modernization://{relative_path}` | `mdx-db-modernization://docs/01-intro.md` | Part of 954 (doc_type: tutorial) |
| BBj Source | `BbjSourceParser` | `file://{relative_path}` | `file://samples/DWCNavigator.bbj` | ~140 (doc_type: example) |
| WordPress Advantage | `AdvantageParser` | `https://basis.cloud/advantage/{slug}` | `https://basis.cloud/advantage/some-article/` | Part of 1,798 (doc_type: article) |
| WordPress KB | `KnowledgeBaseParser` | `https://basis.cloud/knowledge-base/{slug}` | `https://basis.cloud/knowledge-base/kb01220/` | Part of 2,960 (doc_type: concept) |
| Web Crawl | `WebCrawlParser` | `https://documentation.basis.cloud/BASISHelp/WebHelp/{path}` | `https://documentation.basis.cloud/BASISHelp/WebHelp/bbjobjects/Window/bbjwindow/bbjwindow_addbutton.htm` | Part of 44,587 (doc_type: web_crawl) |

**Key observation:** Web Crawl and WordPress sources already have clickable HTTPS URLs as their `source_url`. Flare, PDF, BBj Source, and MDX use custom schemes that need mapping.

### Source Type Derivation

There is no explicit `source_type` column in the database. Currently, `doc_type` serves a different purpose (content classification: "flare", "concept", "article", "tutorial", "example", "web_crawl"). The `source_type` must be derived from the `source_url` prefix or stored as a new field.

The mapping from `source_url` prefix to `source_type` label:

| source_url prefix | source_type value |
|-------------------|-------------------|
| `flare://` | `flare` |
| `pdf://` | `pdf` |
| `file://` | `bbj_source` |
| `mdx-dwc://` | `mdx` |
| `mdx-beginner://` | `mdx` |
| `mdx-db-modernization://` | `mdx` |
| `https://basis.cloud/advantage` | `wordpress` |
| `https://basis.cloud/knowledge-base` | `wordpress` |
| `https://documentation.basis.cloud/` | `web_crawl` |

### Corpus Composition (Dominance Problem)

From VALIDATION.md corpus stats:

- **Total chunks:** 50,439
- **Flare + Web Crawl (same content, different source):** ~44,587 doc_type: flare + unknown web_crawl count = ~88%+ of corpus
- **Non-Flare minority sources:** concept (2,960), article (1,798), tutorial (954), example (140) = ~12% of corpus

The VALIDATION.md cross-source summary confirms the ranking problem:
- PDF (`pdf://`): **never appeared** in any query results
- BBj Source (`file://`): **never appeared** in any query results
- Source-targeted queries for PDF and BBj Source returned Advantage PDF articles (from web crawl) or Flare content instead

This is the exact problem source-balanced ranking must solve.

### Current Search Architecture

The search pipeline is:
1. Query text arrives at `/search` endpoint (`api/routes.py`)
2. Query is embedded via Ollama (`qwen3-embedding:0.6b`, 1024 dimensions)
3. `async_hybrid_search()` runs RRF fusion of dense vector + BM25 keyword search (`search.py`)
4. Each sub-query fetches top-20 candidates, RRF combines them, returns top-N by fused score
5. Results converted to `SearchResultItem` Pydantic models and returned as JSON

**The RRF SQL query is a single SQL statement.** Adding source-balanced reranking must happen in Python after the SQL returns, not inside the SQL itself. This is the cleanest approach because:
- The SQL already does the hard work (vector search + BM25 + rank fusion)
- Source diversity is an application-level concern
- Python post-processing is testable without a database

### Current API Response Shape

```json
{
  "query": "BBjWindow addButton method",
  "results": [
    {
      "content": "...",
      "title": "BBjButton Methods",
      "source_url": "flare://Content/bbjobjects/Window/bbjbutton/BBjButton.htm",
      "doc_type": "flare",
      "generations": ["bbj"],
      "context_header": "bbjobjects > Window > bbjbutton > BBjButton Methods > Creation",
      "deprecated": false,
      "score": 0.0381
    }
  ],
  "count": 5
}
```

New fields (`display_url`, `source_type`) will be added to `SearchResultItem`. Source type breakdown will be added to `SearchResponse` metadata.

### MCP Server Output Format

The MCP server (`mcp_server.py`) is a thin proxy that calls the REST API and formats results as text blocks. The `_format_results()` function currently renders:

```
## Result 1: {title}
*{context_header}*

{content}

Source: {source_url}
Generations: {generations}
```

This will need to render `display_url` instead of (or alongside) `source_url`.

## URL Mapping Rules (Per Source Type)

### 1. Flare -> documentation.basis.cloud (CONFIRMED)

**Pattern:** `flare://Content/{relative_path}` -> `https://documentation.basis.cloud/BASISHelp/WebHelp/{relative_path}`

**Derivation from the confirmed reference example:**
- Input: `flare://Content/bbjobjects/bbjapi/bbjapi.htm`
- Output: `https://documentation.basis.cloud/BASISHelp/WebHelp/bbjobjects/bbjapi/bbjapi.htm`

**Rule:**
```
strip "flare://Content/" prefix
prepend "https://documentation.basis.cloud/BASISHelp/WebHelp/"
```

**Regex pattern:**
```python
re.sub(r'^flare://Content/', 'https://documentation.basis.cloud/BASISHelp/WebHelp/', source_url)
```

**Confidence:** HIGH -- the web crawl parser already uses `https://documentation.basis.cloud/BASISHelp/WebHelp/` as its base URL, confirming this is the correct public URL structure.

### 2. PDF -> Bracketed Fallback (NO PUBLIC URL)

**Pattern:** `pdf://{filename}#{slug}` -> `[pdf://{filename}#{slug}]`

**Analysis:** The PDF source is a local file (`GuideToGuiProgrammingInBBj.pdf`). The `source_url` format is `pdf://GuideToGuiProgrammingInBBj.pdf#section-slug`. There is no public-facing URL where this PDF is hosted.

**Deep-linking feasibility:** The PDF parser stores a `#slug` fragment in the `source_url` (e.g., `pdf://GuideToGuiProgrammingInBBj.pdf#blowing-the-doors-wide-open`). This slug is derived from the heading text via `_slugify()`. If the PDF were ever hosted publicly (e.g., at `https://documentation.basis.cloud/guides/GuideToGuiProgrammingInBBj.pdf`), the fragment would work for navigation in some PDF viewers, but PDF fragment identifiers use `#page=N` or `#nameddest=N` syntax, not slugs. **The current slug-based fragments would NOT work for PDF deep-linking.** Page numbers are not preserved in the chunk metadata (pymupdf4llm converts to a single markdown string with `page_chunks=False`).

**Recommendation:** Use bracketed fallback: `[pdf://GuideToGuiProgrammingInBBj.pdf#section-slug]`. If the PDF is ever hosted publicly, a follow-up phase could add page-number tracking to the PDF parser metadata and map to `{base_url}#page=N`.

### 3. BBj Source -> Bracketed Fallback (NO CONFIRMED PUBLIC URL)

**Pattern:** `file://{relative_path}` -> `[file://{relative_path}]`

**Analysis:** BBj source files come from two local directories:
- `bbj-dwc-tutorial/samples/` (DWC tutorial code samples)
- `bbj-beginner-tutorial/` (beginner tutorial source files)

These are part of local tutorial repos. There is no evidence in the codebase that these files are hosted on a public web server or Git repository viewer. The `source_url` is `file://samples/DWCNavigator.bbj` -- relative to the source directory, not a full path.

**Potential investigation:** If these tutorial repos are GitHub repositories, the source files could be mapped to `https://github.com/{org}/{repo}/blob/main/{path}`. However, no GitHub organization or repo URL is confirmed in the codebase. The `docusaurus.config.ts` references `https://github.com/StephanWald/bbj-ai-strategy` for THIS project, but the tutorial repos are separate data directories.

**Recommendation:** Use bracketed fallback: `[file://samples/DWCNavigator.bbj]`. The bracketed format clearly signals "not clickable" to consumers.

### 4. MDX -> Bracketed Fallback (DEPLOYMENT STATUS UNCLEAR)

**Pattern:** `mdx-{name}://{relative_path}` -> `[mdx-{name}://{relative_path}]`

**Analysis:** The three MDX sources are Docusaurus tutorial sites:
- `mdx-dwc` -> `bbj-dwc-tutorial/docs/`
- `mdx-beginner` -> `bbj-beginner-tutorial/docs/`
- `mdx-db-modernization` -> `bbj-db-modernization-tutorial/docs/`

The current project itself (`bbj-ai-strategy`) deploys to `https://StephanWald.github.io/bbj-ai-strategy/`. However, there is no evidence in the codebase that the three tutorial projects are deployed to public URLs. They are data sources referenced by relative paths in `sources.toml`.

**If deployed:** The MDX path mapping would be:
- Strip the `mdx-{name}://` prefix
- Remove the `.md`/`.mdx` extension
- Map to the deployed site URL structure (e.g., `https://{org}.github.io/{repo}/docs/{path}`)
- Docusaurus uses `sidebar_position` frontmatter to determine URL slugs, which may differ from file paths

**Recommendation:** Use bracketed fallback. If deployment URLs are later confirmed, the mapping rules can be added without schema changes.

### 5. WordPress -> Already HTTPS (NO MAPPING NEEDED)

**Pattern:** `https://basis.cloud/...` -> `https://basis.cloud/...` (pass-through)

WordPress Advantage and Knowledge Base sources already have clickable HTTPS URLs as their `source_url`. No mapping needed.

### 6. Web Crawl -> Already HTTPS (NO MAPPING NEEDED)

**Pattern:** `https://documentation.basis.cloud/...` -> `https://documentation.basis.cloud/...` (pass-through)

Web Crawl sources already have clickable HTTPS URLs. No mapping needed.

### URL Mapping Summary Table

| source_type | Mapping Strategy | display_url Example | Clickable? |
|-------------|-----------------|---------------------|------------|
| `flare` | Regex transform | `https://documentation.basis.cloud/BASISHelp/WebHelp/bbjobjects/bbjapi/bbjapi.htm` | YES |
| `pdf` | Bracketed fallback | `[pdf://GuideToGuiProgrammingInBBj.pdf#section-slug]` | NO |
| `bbj_source` | Bracketed fallback | `[file://samples/DWCNavigator.bbj]` | NO |
| `mdx` | Bracketed fallback | `[mdx-dwc://02-browser-developer-tools/03-css-custom-properties.md]` | NO |
| `wordpress` | Pass-through | `https://basis.cloud/advantage/some-article/` | YES |
| `web_crawl` | Pass-through | `https://documentation.basis.cloud/BASISHelp/WebHelp/...` | YES |

## Source-Balanced Ranking

### The Problem (Quantified)

The VALIDATION.md confirms:
- PDF (`pdf://`): **0 results** across all test queries
- BBj Source (`file://`): **0 results** across all test queries
- Even source-targeted queries explicitly looking for PDF/BBj Source content returned Flare or Advantage PDFs instead

With 44,587 Flare chunks vs ~140 PDF chunks and ~140 BBj Source chunks, the vector space is dominated by Flare content. RRF scoring naturally favors Flare results because:
1. Dense vector search: Flare embeddings dominate the HNSW index neighborhood
2. BM25 search: Flare content has the broadest keyword coverage
3. RRF fusion amplifies this by summing ranks from both sub-queries

### Recommended Approach: Post-RRF Diversity Reranking

**Strategy:** After the existing `async_hybrid_search()` returns its top-N results, apply a diversity-aware reranking step that promotes minority source types.

**Algorithm (Maximal Marginal Relevance variant for source diversity):**

1. Run hybrid search with an **over-fetch** (e.g., request top-20 instead of top-5)
2. Classify each result by `source_type` (derived from `source_url` prefix)
3. Check if the result set is "dominated" -- if the top-N results are all from the same source type
4. If dominated, boost minority source results by adjusting their score or position
5. Return the final top-N with adjusted ordering

**Boost mechanics (recommendation):**

```python
# Multiplicative boost for underrepresented source types
MINORITY_BOOST = 1.3  # 30% score boost

# Only trigger when a single source type holds >= 80% of results
DOMINATION_THRESHOLD = 0.8
```

The boost should be **multiplicative on the RRF score**, not additive. This preserves the relative quality signal -- a terrible minority result with score 0.001 still won't beat a good majority result with score 0.03, but a decent minority result with score 0.015 * 1.3 = 0.0195 would leapfrog marginal majority results.

**Trigger logic recommendation:** Apply balancing only when a single source type constitutes >= 80% of the over-fetched results. This avoids penalizing naturally diverse result sets. On "dominated-only" queries (which is most queries given the 88% Flare dominance), minority results get a boost.

**Over-fetch factor:** Request 2x the desired limit from the SQL query (e.g., limit=10 when user wants 5), apply diversity reranking, then truncate to the requested limit. The existing SQL sub-queries already fetch top-20 each, so over-fetching to 20 for a limit=10 request is essentially free.

### Score Transparency Recommendation

**Recommendation: Expose only the adjusted score.** Returning both raw and adjusted scores adds API complexity for marginal benefit. The consumer (MCP server, chat UI) only needs the final ranked order. If debugging is needed, add a `?debug=true` query parameter that includes raw scores in a separate field -- but don't implement this in Phase 25 unless needed.

### Boost Factor Configuration Recommendation

**Recommendation: Hardcoded constants in a module-level dict.** The boost factor and domination threshold are tuning parameters that will rarely change. Putting them in config.toml or environment variables adds complexity without clear benefit. If tuning is needed later, promoting constants to config is a trivial change.

```python
# search.py or a new diversity.py module
SOURCE_BOOST = {
    "pdf": 1.3,
    "bbj_source": 1.3,
    "mdx": 1.2,
    "wordpress": 1.0,  # Already well-represented
    "web_crawl": 1.0,  # Same content as Flare
    "flare": 1.0,       # Majority source, no boost
}
DOMINATION_THRESHOLD = 0.8  # Trigger diversity reranking
```

### Test Queries for Validation

Based on the VALIDATION.md failures, these queries should validate that balanced ranking works:

| Query | Expected Behavior | Current Behavior (from VALIDATION.md) |
|-------|-------------------|--------------------------------------|
| `customer information program BBj GUI example` | At least one `pdf://` result in top 10 | Top result was Advantage PDF from web crawl |
| `BBj sample source code PROCESS_EVENTS` | At least one `file://` result in top 10 | Top result was Advantage PDF from web crawl |
| `DWC web component tutorial getting started` | At least one `mdx-*://` result in top 5 (currently passes) | Already passes -- MDX result at position 1 |
| `GUI programming BBj window button` | At least one `pdf://` result in top 10 | Not tested but expected to be all Flare |
| `BBj Navigator sample code` | At least one `file://` result in top 10 | Not tested but expected to be all Flare |

Additional queries to identify from corpus analysis (requires running against the live DB):
- Any query about "AppBuilder" or "Barista" should surface PDF content (the PDF has tutorial sections on these topics)
- Any query about "DWCNavigator" should surface BBj Source content (file exists in DWC tutorial samples)

## Implementation Architecture

### Approach A: Query-Time Mapping (Simpler, No Migration)

Compute `display_url` and `source_type` when building the API response, not at ingestion time.

**Pros:**
- No database schema change or migration needed
- No re-ingestion required
- Mapping rules can be updated without touching the DB
- Simpler to implement and test

**Cons:**
- Mapping computed on every query (trivial cost -- regex on 5-10 results)
- Can't query/filter by source_type or display_url in SQL

### Approach B: Ingestion-Time Storage (User's Choice from CONTEXT.md)

Add `display_url` and `source_type` columns to the chunks table. Compute mapping during ingestion and store alongside `source_url`.

**Pros:**
- Data is pre-computed, no per-query overhead
- Can index and query by source_type (useful for diversity analysis)
- Enables future SQL-level source-type filtering

**Cons:**
- Requires schema migration (ALTER TABLE ADD COLUMN)
- Requires re-ingestion or backfill UPDATE for existing 50,439 chunks
- Mapping rules are "frozen" at ingestion time -- changing rules requires re-ingestion

**User decision from CONTEXT.md: Ingestion-time storage.** The implementation should:
1. Add `display_url TEXT` and `source_type TEXT` columns to the `chunks` table
2. Add a `url_mapping.py` module with the mapping functions
3. Call mapping during the pipeline (in `chunk_document()` or `run_pipeline()`)
4. Backfill existing chunks via a one-time SQL UPDATE using the same mapping logic
5. Update the INSERT SQL in `db.py` to include the new columns

### Schema Migration Plan

```sql
-- Add new columns with defaults so existing rows get values
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS source_type TEXT NOT NULL DEFAULT '';
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS display_url TEXT NOT NULL DEFAULT '';

-- Index on source_type for diversity queries and balanced ranking
CREATE INDEX IF NOT EXISTS idx_chunks_source_type ON chunks (source_type);
```

**Backfill strategy:** A Python script that reads all distinct `source_url` prefixes, applies the mapping rules, and runs batch UPDATE statements. This avoids re-ingesting all 50,439 chunks.

### API Field Structure Recommendation

**Recommendation: Top-level fields on SearchResultItem (not nested).**

The existing API response has flat fields (`source_url`, `doc_type`, `title`, etc.). Adding `display_url` and `source_type` at the same level is consistent with the established pattern. A nested structure (e.g., `source: { url, display_url, type }`) would break backward compatibility.

Updated `SearchResultItem`:
```python
class SearchResultItem(BaseModel):
    content: str
    title: str
    source_url: str
    display_url: str          # NEW
    source_type: str           # NEW
    doc_type: str
    generations: list[str]
    context_header: str
    deprecated: bool
    score: float
```

Updated `SearchResponse`:
```python
class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    count: int
    source_type_counts: dict[str, int]  # NEW: e.g., {"flare": 4, "pdf": 1}
```

### MCP Server Update

The `_format_results()` function should render `display_url` as the primary source link:

```
## Result 1: {title}
*{context_header}*

{content}

Source: {display_url}
Type: {source_type}
Generations: {generations}
```

When `display_url` is bracketed (unmappable), it should still be shown -- the brackets signal to the LLM that it's not a clickable link.

### New Module: `url_mapping.py`

Recommended location: `rag-ingestion/src/bbj_rag/url_mapping.py`

```python
"""URL mapping: internal source_url -> public display_url and source_type."""

import re

# source_type classification from source_url prefix
_SOURCE_TYPE_RULES: list[tuple[str, str]] = [
    ("flare://", "flare"),
    ("pdf://", "pdf"),
    ("file://", "bbj_source"),
    ("mdx-", "mdx"),
    ("https://basis.cloud/advantage", "wordpress"),
    ("https://basis.cloud/knowledge-base", "wordpress"),
    ("https://documentation.basis.cloud/", "web_crawl"),
]

# display_url mapping rules
_FLARE_BASE = "https://documentation.basis.cloud/BASISHelp/WebHelp/"

def classify_source_type(source_url: str) -> str: ...
def map_display_url(source_url: str) -> str: ...
```

### Diversity Reranking Module

Recommended location: Either extend `search.py` with a `rerank_for_diversity()` function, or create a new `diversity.py` module.

The function signature:

```python
def rerank_for_diversity(
    results: list[SearchResult],
    limit: int,
    domination_threshold: float = 0.8,
) -> list[SearchResult]:
    """Re-score and re-order results to promote source diversity."""
```

This function is called in `api/routes.py` between the hybrid search call and the response construction:

```python
# In search() route handler:
results = await async_hybrid_search(conn, embedding, query, limit=limit*2)  # over-fetch
results = rerank_for_diversity(results, limit=body.limit)  # diversity rerank
# Build response...
```

## Files That Need Changes

### Must Modify

| File | Change |
|------|--------|
| `sql/schema.sql` | Add `source_type` and `display_url` columns to CREATE TABLE |
| `src/bbj_rag/models.py` | Add `source_type` and `display_url` fields to `Document` and `Chunk` |
| `src/bbj_rag/search.py` | Add `source_type` and `display_url` to SELECT columns and `SearchResult` dataclass |
| `src/bbj_rag/api/schemas.py` | Add `display_url`, `source_type` to `SearchResultItem`; add `source_type_counts` to `SearchResponse` |
| `src/bbj_rag/api/routes.py` | Compute `source_type_counts`, pass through `display_url` and `source_type`, add diversity reranking |
| `src/bbj_rag/mcp_server.py` | Update `_format_results()` to show `display_url` and `source_type` |
| `src/bbj_rag/db.py` | Add `source_type` and `display_url` to INSERT SQL and `_chunk_to_params()` |

### Must Create

| File | Purpose |
|------|---------|
| `src/bbj_rag/url_mapping.py` | `classify_source_type()` and `map_display_url()` functions |

### Should Modify

| File | Change |
|------|--------|
| `src/bbj_rag/pipeline.py` | Call `url_mapping` functions when creating chunks |
| `src/bbj_rag/chunker.py` | Pass through `source_type` and `display_url` from Document to Chunk |
| `src/bbj_rag/parsers/flare.py` | No change needed (mapping derived from source_url) |
| `src/bbj_rag/parsers/pdf.py` | No change needed |
| `src/bbj_rag/parsers/bbj_source.py` | No change needed |
| `src/bbj_rag/parsers/mdx.py` | No change needed |
| `scripts/validate_e2e.py` | Add display_url and source_type_counts assertions |

### Should Create

| File | Purpose |
|------|---------|
| `tests/test_url_mapping.py` | Unit tests for classify_source_type and map_display_url |
| `tests/test_diversity.py` | Unit tests for rerank_for_diversity |
| `scripts/backfill_urls.py` | One-time script to populate source_type and display_url for existing chunks |

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema migration on production DB | Downtime during ALTER TABLE on 50K rows | ALTER TABLE ADD COLUMN with DEFAULT is near-instant in PostgreSQL (no table rewrite) |
| Backfill script fails midway | Partial data | Run in a single transaction; batch UPDATE with WHERE source_type = '' |
| Diversity boost makes irrelevant results surface | Lower quality results | Multiplicative boost (1.3x) is conservative; only triggers on dominated result sets; bad results with very low scores still won't outrank good results |
| URL mapping rules become stale | Broken links | Only Flare mapping is a computed URL; the rest are pass-through or bracketed. If the Flare site URL changes, one constant needs updating |
| Over-fetching doubles SQL work | Performance regression | The SQL already fetches top-20 in each sub-query; over-fetching to 20 for a limit=10 is essentially the same cost |

## Recommendation Summary

1. **URL mapping module** (`url_mapping.py`): Pure functions, easily testable, no external dependencies
2. **Schema migration**: Two new columns (`source_type TEXT`, `display_url TEXT`) with defaults, plus one index
3. **Backfill script**: One-time Python script to populate existing rows
4. **Diversity reranking**: Post-RRF Python function with hardcoded boost factors, triggered on dominated result sets
5. **API enrichment**: Flat top-level fields on `SearchResultItem`, `source_type_counts` dict on `SearchResponse`
6. **MCP update**: Render `display_url` as primary source link, add `source_type` label
7. **Score handling**: Expose only adjusted scores; no raw/adjusted split

---

*Phase: 25-result-quality-foundation*
*Research completed: 2026-02-03*
