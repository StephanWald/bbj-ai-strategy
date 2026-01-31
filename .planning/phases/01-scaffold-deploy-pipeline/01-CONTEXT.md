# Phase 1: Scaffold & Deploy Pipeline - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Initialize a Docusaurus project with 7-chapter folder structure and automated GitHub Pages deployment. The site must build, deploy, and show all chapters in the sidebar with placeholder content. No real content authoring, no custom components, no search — just the working skeleton and pipeline.

</domain>

<decisions>
## Implementation Decisions

### Repo & URL structure
- Repo name: `bbj-ai-strategy` (matches current directory)
- Hosted under personal GitHub account (`beff`)
- Project site: initial URL at `beff.github.io/bbj-ai-strategy`
- `baseUrl` set to `/bbj-ai-strategy/`
- Plan to add custom domain later — configure so migration is straightforward
- `trailingSlash`: Claude's discretion (pick what works correctly with GitHub Pages)

### Chapter placeholder content
- Each chapter gets a teaser paragraph (2-3 sentences summarizing what the chapter will cover)
- All 7 chapters visible in sidebar from day one — no hidden/draft pages
- Single page vs sub-pages per chapter: Claude decides based on content length judgment
  - Short chapters → single page
  - Long/complex chapters → sub-pages in a folder

### Site identity & naming
- Site title: "BBj AI Strategy"
- Tagline: "Intelligent Code Assistance Across Four Generations of Business BASIC"
- Color scheme: Docusaurus defaults (customize in v2)
- Logo/favicon: skip for now (Docusaurus default)

### Branch & deploy strategy
- Deploy from `main` branch — push triggers GitHub Actions → GitHub Pages
- Docusaurus file structure placement: Claude's discretion (root vs subfolder — pick cleanest approach)
- Original strategy paper (`bbj-llm-strategy.md`) stays in repo as reference until all content is migrated, then removed

### Claude's Discretion
- `trailingSlash` setting (pick what avoids GitHub Pages 404s)
- Docusaurus at root vs in subfolder (pick cleanest coexistence with .planning/ and strategy paper)
- Per-chapter decision on single page vs sub-pages
- Exact sidebar ordering approach (numbered prefixes, `_category_.json`, etc.)

</decisions>

<specifics>
## Specific Ideas

- URL will eventually move to a custom domain, so avoid hardcoding the GitHub Pages URL in content
- Site should feel professional even with placeholder content — visitors seeing teasers is fine, but it shouldn't look broken or abandoned

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-scaffold-deploy-pipeline*
*Context gathered: 2026-01-31*
