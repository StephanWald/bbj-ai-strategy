# Phase 12: Embedding Pipeline - Context

**Gathered:** 2026-02-01
**Status:** Ready for planning

<domain>
## Phase Boundary

End-to-end batch pipeline that parses Flare documentation, applies BBj intelligence (generation tagging, doc type classification, context headers), chunks content, embeds via a configurable model, and stores in pgvector with hybrid search validation. Covers only the Flare source -- additional parsers plug in during Phase 13.

</domain>

<decisions>
## Implementation Decisions

### Chunking strategy
- Claude's discretion on splitting approach (heading-aware vs fixed-size vs hybrid)
- Claude's discretion on chunk size range
- Claude's discretion on code block handling (keep with text vs separate)
- Claude's discretion on whether context headers are prepended to chunk text before embedding or stored as metadata only

### Embedding model & inference
- Local-first using Ollama, with API fallback as a configurable option
- User has Ollama installed locally with strong GPU hardware
- Researcher should investigate current best embedding models available in Ollama for technical documentation
- Claude's discretion on API fallback provider (OpenAI, Voyage, etc.)
- Claude's discretion on embedding dimensions based on corpus size (~2-5K docs) and pgvector performance

### CLI & pipeline orchestration
- Both a full pipeline command (`bbj-rag ingest --source flare`) AND individual stage commands for debugging/re-runs
- Simple logging for progress (stage-by-stage log lines, not rich progress bars) -- must work in CI logs
- `--resume` flag for development (skip already-stored chunks); default is clean re-run for CI
- Claude's discretion on CLI framework (click, typer, or argparse)

### Search validation approach
- Automated assertions, not just eyeball-check scripts
- Validation cases defined in a data file (not hardcoded in test code) -- engineers add cases without writing code
- Claude's discretion on cases file format (YAML, TOML, etc.)
- Claude's discretion on initial case count (enough to validate success criteria)
- Include generation-filtered search validation (e.g., query filtered to bbj_gui generation)
- Start with a small set of cases; more can be added later without code changes

### Claude's Discretion
- Chunking approach (splitting strategy, size, overlap, code block handling, context header embedding)
- Embedding dimensions and model recommendation (via research)
- API fallback provider
- CLI framework choice
- Validation cases format and initial count
- Batch size and concurrency for embedding inference

</decisions>

<specifics>
## Specific Ideas

- User runs Ollama locally with strong GPU -- optimize for local inference path
- CI pipeline should always restart clean (no resume by default)
- Validation cases file is a key deliverable -- engineers will extend it as they add sources in Phase 13+
- Generation-filtered search is important to validate (not just unfiltered search)

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 12-embedding-pipeline*
*Context gathered: 2026-02-01*
