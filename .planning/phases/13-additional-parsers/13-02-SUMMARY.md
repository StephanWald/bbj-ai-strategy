---
phase: 13-additional-parsers
plan: 02
subsystem: parsers
tags: [wordpress, httpx, beautifulsoup, web-crawl, advantage, knowledge-base, eckb]

# Dependency graph
requires:
  - phase: 10-flare-parser
    provides: "DocumentParser protocol, Document model, web_crawl._html_to_markdown"
provides:
  - "AdvantageParser for basis.cloud/advantage-index/ magazine articles"
  - "KnowledgeBaseParser for basis.cloud/knowledge-base/ ECKB plugin content"
  - "WordPress-specific chrome stripping (_strip_wp_chrome)"
affects: [13-04-pipeline-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Index-then-article crawl pattern with sitemap XML fallback"
    - "WordPress chrome selector list with media tag stripping"
    - "ECKB plugin content selector priority (#eckb-article-body)"

key-files:
  created:
    - "rag-ingestion/src/bbj_rag/parsers/wordpress.py"
    - "rag-ingestion/tests/test_wordpress_parser.py"
  modified: []

key-decisions:
  - "Reuse _html_to_markdown from web_crawl (no reimplementation)"
  - "Separate WordPress chrome selectors from Flare chrome selectors"
  - "Strip all media tags (img, video, audio, iframe, figure, svg) for text-only"
  - "Advantage doc_type='article', KB doc_type='concept'"
  - "Sitemap fallback: /post-sitemap.xml for Advantage, /kb-sitemap.xml then /sitemap.xml for KB"

patterns-established:
  - "WordPress parser pattern: index URL discovery -> per-article fetch -> chrome strip -> markdown convert"
  - "Sitemap XML fallback when HTML index parsing yields zero URLs"

# Metrics
duration: 5min
completed: 2026-02-01
---

# Phase 13 Plan 02: WordPress Parsers Summary

**AdvantageParser and KnowledgeBaseParser crawling basis.cloud via httpx+BeautifulSoup with WordPress chrome stripping and ECKB plugin support**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-01T08:19:07Z
- **Completed:** 2026-02-01T08:24:07Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments
- AdvantageParser discovers article URLs from index page with sitemap XML fallback
- KnowledgeBaseParser handles ECKB plugin layout (#eckb-article-body selector)
- WordPress-specific chrome stripping removes nav, header, footer, sidebar, comments, media
- Both parsers reuse _html_to_markdown from web_crawl module (no duplication)
- 16 unit tests with mocked HTTP covering both parsers end-to-end

## Task Commits

Each task was committed atomically:

1. **Task 1: WordPress parser module** - `db76937` (feat)
2. **Task 2: Unit tests for WordPress parsers** - `384e537` (test)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified
- `rag-ingestion/src/bbj_rag/parsers/wordpress.py` - AdvantageParser and KnowledgeBaseParser classes with shared WordPress helpers
- `rag-ingestion/tests/test_wordpress_parser.py` - 16 unit tests covering protocol compliance, URL discovery, chrome stripping, Document fields, sitemap fallback, empty/media handling

## Decisions Made
- Reused `_html_to_markdown` from web_crawl module rather than reimplementing HTML-to-Markdown conversion
- WordPress chrome selectors kept separate from Flare chrome selectors (different boilerplate patterns)
- All media tags stripped (img, video, audio, iframe, figure, svg) per text-only requirement
- Advantage articles typed as `doc_type="article"`, KB content typed as `doc_type="concept"`
- Sitemap fallback using standard sitemap.org XML schema when index page HTML parsing finds no links
- Title extraction strips " - BASIS International" and similar suffixes

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- WordPress parsers ready for pipeline integration (Plan 13-04)
- Both parsers implement DocumentParser protocol (isinstance checks verified)
- No blocking issues for downstream phases

---
*Phase: 13-additional-parsers*
*Completed: 2026-02-01*
