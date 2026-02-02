# Phase 24: End-to-End Validation - Context

**Gathered:** 2026-02-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove the full RAG pipeline works end-to-end: user query enters through REST API or MCP, hits real ingested BBj documentation across all 6 sources, and returns relevant results. This is validation of the existing system, not building new features.

</domain>

<decisions>
## Implementation Decisions

### Test queries & coverage
- Two query categories: source-targeted (one per source, 6 queries) AND topic-based (representative BBj topics, 5-10 queries)
- Full query set runs through REST API
- Subset of 3-4 representative queries through MCP (thin wrapper — full coverage unnecessary)
- Claude selects representative topics from the ingested corpus based on source diversity
- Generation filter testing: Claude's discretion on whether to include based on value vs. already-covered ground

### Result quality bar
- Top 1 result for each query must be relevant — a human reading it should be able to answer the original question
- Cross-source criterion: across the full query set, demonstrate results come from multiple different parsers — not every individual query needs multi-source hits
- Record RRF ranking scores alongside results as a baseline for future retrieval tuning

### Validation output format
- Markdown report (VALIDATION.md) in project root — visible proof the system works
- Include content snippets (~100 chars) from top results so a reader can judge relevance without running queries
- Include corpus stats section (total chunks, chunks per source from /stats endpoint) as context
- Per-query structure: query text, pass/fail, top result source/title/score/snippet

### Failure handling
- Poor or irrelevant results: document in report as known issues, move on — quality tuning is a future concern
- Check prerequisites before running queries: Docker, DB, Ollama must be running — clear error if not
- Missing sources (zero chunks for any of the 6 sources) = validation failure — all 6 must be present
- MCP validation done programmatically (invoke search_bbj_knowledge directly), not manual Claude Desktop demo

### Claude's Discretion
- Exact query text for both source-targeted and topic-based queries
- Number of topic-based queries (5-10 range)
- Whether to include generation filter in test queries
- Report formatting and section structure details
- Which 3-4 queries to run through MCP

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 24-end-to-end-validation*
*Context gathered: 2026-02-02*
