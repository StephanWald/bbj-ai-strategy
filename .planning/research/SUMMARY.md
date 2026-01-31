# Project Research Summary

**Project:** BBj AI Strategy Documentation Site
**Domain:** Technical documentation site (Docusaurus)
**Researched:** 2026-01-31
**Confidence:** HIGH

## Executive Summary

This project converts a comprehensive AI strategy paper (~1100 lines) into a professional Docusaurus documentation site serving three distinct audiences: internal developers, leadership, and customers/partners. The research confirms that Docusaurus 3.9.2 with modern tooling (Rspack builds, Mermaid diagrams, local search) is the optimal stack for this use case. The site will present 7 chapters of strategic content plus appendices, deployed to GitHub Pages with zero runtime dependencies.

The recommended approach prioritizes content architecture over technical features. Docusaurus provides 70% of required functionality out of the box; the differentiating work is creating audience-aware content patterns (decision record callouts, TL;DR blocks, generation-specific code examples) and ensuring the narrative flow works for web consumption rather than sequential reading. The biggest technical differentiator is custom BBj syntax highlighting, which is essential for credibility with the developer audience but can be deferred to the polish phase.

Key risks center on deployment configuration (GitHub Pages baseUrl mismatches cause complete site failure), content structure (monolithic paper dumps fail as documentation), and audience clarity (mixing strategic rationale with implementation details alienates all three audiences). All three are preventable with upfront configuration discipline and content architecture planning before migration begins.

## Key Findings

### Recommended Stack

The research identifies Docusaurus 3.9.2 as the clear choice, with the modern Rspack build pipeline (2-4x faster builds), Mermaid diagram support (essential for architecture diagrams), and local search for zero external dependencies. The stack is production-ready and actively maintained by Meta.

**Core technologies:**
- **Docusaurus 3.9.2 with @docusaurus/preset-classic** — Industry-standard documentation framework providing sidebar navigation, dark mode, code highlighting, and static site generation. No viable alternative for this use case.
- **@docusaurus/faster 3.9.2 (Rspack builds)** — Rust-based build pipeline (Rspack bundler, SWC transpiler). Provides 2-4x faster builds, critical for iterative content authoring. Already used in production by Docusaurus team.
- **@docusaurus/theme-mermaid 3.9.2** — Enables Mermaid diagram rendering in markdown. Essential for converting the strategy paper's ASCII architecture diagrams to maintainable, theme-aware diagrams.
- **@easyops-cn/docusaurus-search-local 0.52.3** — Client-side search using lunr.js. Zero external dependencies, no API keys, works offline. Simpler than Algolia DocSearch for a 7-chapter site.
- **Node.js 22 LTS** — Current LTS, well within Docusaurus >=20.0 requirement. Default for Docusaurus team's own CI.
- **GitHub Actions + GitHub Pages** — Modern deployment using actions/deploy-pages@v4 with OIDC authentication. Standard approach replacing older gh-pages branch method.

**What NOT to use:**
- Docusaurus 2.x (end-of-life)
- Algolia DocSearch (overkill for 7 chapters, can add later)
- Webpack builds (Rspack is production-ready and faster)
- Alternative frameworks (MkDocs/VitePress/GitBook) all have significant drawbacks versus Docusaurus for this use case

### Expected Features

Most features are built into Docusaurus by default. The differentiation comes from content patterns, not technical implementation.

**Must have (table stakes):**
- Sidebar navigation with hierarchy — Docusaurus default
- Full-text search — Local search plugin
- Syntax-highlighted code blocks — Prism.js (BBj grammar needed)
- Copy buttons on code blocks — Theme config toggle
- Mobile-responsive layout — Docusaurus default
- Table of contents (in-page) — Docusaurus default
- Landing page with value proposition — Custom React page (medium effort)
- Last updated dates on pages — Git timestamps config
- Fast page loads — Static generation automatic
- Working links with broken-link detection — Docusaurus build-time validation

**Should have (competitive):**
- **Audience signal badges** — Visual indicators showing relevance per audience (Technical Deep Dive, Leadership Summary, Customer-Facing). Custom MDX component. This is the most important differentiator for the multi-audience requirement.
- **Decision record callouts** — Architecture Decision Record style explanations for technical choices. Custom admonition type. Separates strategy docs from reference docs.
- **TL;DR/Executive Summary blocks** — Collapsible summaries for leadership readers. Custom MDX component. Low complexity, high value.
- **Custom BBj syntax highlighting** — Proper Prism.js language grammar. Critical for developer audience credibility; BBj readers will immediately notice broken highlighting.
- **Generation-labeled code examples** — Visual tags showing which BBj generation applies (All, DWC Only, Visual PRO/5). Docusaurus tabs component.
- **Mermaid diagram support** — Replaces ASCII art with professional, theme-aware diagrams. Official Docusaurus plugin.
- **Progressive disclosure of technical depth** — Expandable sections for implementation details. HTML details tags or custom components.
- **Current status indicators** — Badges showing implementation status (Research, In Progress, Shipped, Future). Custom MDX component.

**Defer (v2+):**
- Glossary hover definitions — Nice but not essential for launch
- Chapter progress visualization — Custom sidebar component, polish phase
- Interactive code playgrounds — Client-side complexity, no clear ROI for launch
- PDF export — Browser print suffices; adds complexity
- Analytics dashboards — Simple page-view tracking is enough

**Anti-features (do NOT build):**
- Authentication/gated content — Site is explicitly public
- Interactive chat widget — Documents the AI strategy, does not demonstrate it
- Multi-language/i18n — English only, confirmed out of scope
- Comments per page — Low-signal noise on strategy docs
- Blog/changelog section — Not a stream of updates; single versioned strategy
- Dark mode customization beyond Docusaurus defaults — Accept defaults, don't invest time

### Architecture Approach

Docusaurus follows a conventional static site architecture with three navigation layers (navbar, sidebar, landing page) that work together. The folder structure uses numbered prefixes (01-, 02-) to ensure correct chapter ordering with autogenerated sidebars.

**Major components:**
1. **Content layer (docs/)** — 7 chapter folders with markdown files. Each chapter has an index.md landing page plus 2-5 topic pages. Autogenerated sidebar from folder structure with _category_.json per chapter for labels/position.
2. **Landing page (src/pages/index.tsx)** — Custom React component outside docs tree. Serves as executive summary and provides three audience entry paths. Not part of sidebar navigation.
3. **Build pipeline (GitHub Actions + Docusaurus SSG)** — Static site generation to /build directory, deployed via actions/deploy-pages@v4. Modern OIDC-based GitHub Pages deployment, not the older gh-pages branch approach.
4. **Theme layer (src/css/custom.css + Docusaurus theme)** — Classic theme with minimal customization. Custom BBj Prism grammar registered in docusaurus.config.ts.
5. **Search (client-side local search)** — Lunr.js-based index built at build time, downloaded to browser. Zero runtime dependencies.

**Key architectural decisions:**
- Autogenerated sidebar with _category_.json overrides (minimal configuration maintenance)
- Numbered folder prefixes (01-, 02-) for explicit ordering
- Index.md per chapter for clickable category landings
- Flat page structure within chapters (no deep nesting)
- Landing page as React component, not markdown
- GitHub Actions deploy-pages (not gh-pages branch)
- trailingSlash: false for GitHub Pages compatibility

**File structure:**
```
bbj-ai-strategy/
├── docs/
│   ├── 01-bbj-challenge/          # Chapter folders with numeric prefixes
│   │   ├── _category_.json        # Sidebar label + position
│   │   ├── index.md               # Chapter landing
│   │   └── *.md                   # Topic pages (2-5 per chapter)
│   ├── 02-strategic-architecture/
│   ├── 03-fine-tuning/
│   ├── 04-ide-integration/
│   ├── 05-documentation-chat/
│   ├── 06-rag-database/
│   ├── 07-implementation-roadmap/
│   └── appendices/
├── src/
│   ├── pages/index.tsx            # Custom landing page
│   └── css/custom.css             # Theme overrides
├── .github/workflows/deploy.yml   # GitHub Pages deployment
├── docusaurus.config.ts           # Site configuration
└── sidebars.ts                    # Autogenerated config
```

### Critical Pitfalls

The research identified 12 critical/medium pitfalls. The top 5 by impact:

1. **GitHub Pages baseUrl mismatch breaks all assets** — Docusaurus defaults baseUrl to /. When deployed to GitHub Pages project repo (username.github.io/bbj-ai-strategy/), every CSS/JS/image returns 404. Site appears as blank page or unstyled HTML. **Prevention:** Set baseUrl: '/bbj-ai-strategy/' and trailingSlash: false in docusaurus.config.ts before first deploy. Verify with local production build.

2. **Monolithic content dump instead of documentation architecture** — Splitting the paper at existing heading boundaries without rethinking structure for web consumption. Pages assume sequential reading; readers landing via search/link find scattered context. **Prevention:** Treat each page as standalone entry point. Add 2-3 sentence summary at top. Break prose into scannable elements (tables, code blocks, admonitions). Review structure after initial migration.

3. **Three audiences, zero audience clarity per page** — No visual/structural differentiation between content for developers, leadership, and customers. Everyone reads everything, 60% is irrelevant. **Prevention:** Add audience indicators to sections (admonitions: "For Leadership", "For Developers"). Landing page provides three entry paths. Review internal-only content (budgets, costs) for public site appropriateness.

4. **Code examples lose context when split across pages** — BBj examples reference multiple generations and build on each other. When split, code appears without generation context or prerequisite setup. **Prevention:** Every code block self-contained or includes minimal setup. Add generation badges/tags above examples. Use Docusaurus tabs to show same concept across generations side-by-side.

5. **trailingSlash inconsistency causes 404s on GitHub Pages** — GitHub Pages handles trailing slashes differently than Docusaurus dev server. Some pages load, others 404 despite identical link format. **Prevention:** Explicitly set trailingSlash: false for GitHub Pages (recommended setting). Test all navigation paths in production after first deploy.

**Other notable pitfalls:**
- ASCII art diagrams render poorly (convert to Mermaid)
- MDX parsing errors with angle brackets/curly braces in code (use fenced code blocks)
- Sensitive content on public site (review budgets, costs for appropriateness)
- Landing page using default Docusaurus template (customize immediately)
- GitHub Actions workflow misconfiguration (use recommended Docusaurus workflow)

## Implications for Roadmap

Based on research, this project has clear phase dependencies driven by Docusaurus architecture. Content cannot be written until scaffolding exists, and polish features depend on content structure being finalized.

### Phase 1: Scaffold & Configure
**Rationale:** Docusaurus configuration must be correct before any content work. GitHub Pages baseUrl mismatch (critical pitfall #1) cannot be fixed retroactively without breaking all deployed links. Sidebar structure defines content organization.

**Delivers:**
- Working Docusaurus 3.9.2 installation with faster builds enabled
- docusaurus.config.ts configured for GitHub Pages (baseUrl, trailingSlash, url, organizationName)
- Sidebar structure defined (autogenerated config with numbered chapter folders)
- All 7 chapter folders created with _category_.json files
- Placeholder index.md in each chapter folder
- GitHub Actions deployment workflow configured
- Verified local build (npm run build succeeds)

**Addresses features:**
- Sidebar navigation (table stakes)
- Breadcrumbs, pagination, ToC (all Docusaurus defaults)
- Mobile responsive (Docusaurus default)
- Broken link detection (onBrokenLinks: 'throw')

**Avoids pitfalls:**
- #1: GitHub Pages baseUrl mismatch (config set correctly upfront)
- #3: trailingSlash inconsistency (explicit setting)
- #6: GitHub Actions misconfiguration (use recommended workflow)
- #7: Sidebar doesn't match file structure (numbered prefixes + autogenerated)

**Research flag:** Standard patterns, no additional research needed.

### Phase 2: Content Architecture & Landing Page
**Rationale:** Content structure must be planned before migration begins to avoid monolithic dump pitfall (#2). Landing page provides the three-audience entry point and must exist before docs content links to it. Custom MDX components for audience signaling must be built before content uses them.

**Delivers:**
- Landing page (src/pages/index.tsx) with executive summary and three audience paths
- Content migration plan: which paper sections map to which pages
- Custom admonition types defined (decision records, TL;DR, audience badges)
- Each chapter index.md written as standalone overview
- First draft of all 7 chapters migrated from strategy paper
- Frontmatter standard established (title, description, sidebar_position, sidebar_label)
- Content reviewed for public site appropriateness (budgets, costs redacted if needed)

**Addresses features:**
- Landing page with value proposition (table stakes)
- Decision record callouts (competitive differentiator)
- TL;DR/Executive Summary blocks (competitive differentiator)
- Audience signal badges (competitive differentiator)

**Avoids pitfalls:**
- #2: Monolithic content dump (each page standalone with summary)
- #5: Three audiences without clarity (audience indicators added)
- #9: Landing page is default template (customized in this phase)
- #11: Sensitive content on public site (reviewed during migration)

**Research flag:** Standard patterns, no additional research needed.

### Phase 3: Code Examples & Technical Content
**Rationale:** Code examples depend on content structure being finalized (Phase 2). BBj syntax highlighting is critical for developer credibility but can follow initial content migration. Mermaid diagrams replace ASCII art from strategy paper.

**Delivers:**
- Custom BBj Prism.js language grammar registered
- All code examples labeled with generation (DWC, Visual PRO/5, Character, All)
- Docusaurus tabs component used for cross-generation comparisons
- Mermaid diagrams converted from ASCII art (infrastructure, VSCode architecture, chat system)
- Training data JSON examples formatted with proper highlighting
- All code blocks self-contained or include minimal setup context
- Comparison tables styled with recommendations highlighted

**Addresses features:**
- Custom BBj syntax highlighting (competitive differentiator, HIGH priority)
- Generation-labeled code examples (competitive differentiator)
- Mermaid diagram support (competitive differentiator)
- Copy button on code blocks (table stakes, theme config)
- Comparison tables with recommendations (competitive differentiator)

**Avoids pitfalls:**
- #4: Code examples lose context (generation labels, self-contained)
- #8: ASCII diagrams render poorly (converted to Mermaid)
- #12: MDX parsing errors (proper fenced code blocks)

**Research flag:** May need BBj Prism grammar research if no existing grammar found. Otherwise standard patterns.

### Phase 4: Search, Polish & Deploy
**Rationale:** Search requires content to exist (needs corpus to index). Polish features (status indicators, chapter progress) depend on finalized content. Deployment is final step after all content verified.

**Delivers:**
- Local search plugin installed and configured (@easyops-cn/docusaurus-search-local)
- Current status indicators added to roadmap chapter (Research, In Progress, Shipped)
- Open Graph meta tags configured (per-page frontmatter + site config)
- Static assets added (logo, favicon, social card image)
- Edit this page links configured (editUrl in docusaurus.config.ts)
- Last updated dates enabled (git timestamps)
- Full site tested in local production build
- Deployed to GitHub Pages
- All navigation paths verified in production

**Addresses features:**
- Full-text search (table stakes)
- Current status indicators (competitive differentiator)
- Open Graph meta tags (competitive differentiator)
- Last updated dates (table stakes)
- Edit this page links (table stakes)

**Avoids pitfalls:**
- All critical pitfalls prevented in earlier phases
- Production testing catches any deployment issues before launch

**Research flag:** Standard patterns, no additional research needed.

### Phase Ordering Rationale

1. **Configuration before content:** GitHub Pages baseUrl and trailingSlash must be correct from day one. Fixing deployment configuration after content is live breaks all existing links.

2. **Content architecture before migration:** Prevents monolithic dump pitfall. Landing page and custom MDX components must exist before content references them.

3. **BBj syntax highlighting after content structure:** Critical for credibility but not blocking initial migration. Developers can review content with fallback highlighting (basic/text), then see proper syntax in Phase 3.

4. **Search and polish last:** Requires content corpus. These are enhancement features that don't block content creation.

This ordering minimizes rework: configuration changes after content deployment are expensive (broken links), but polish features added after content is stable are straightforward enhancements.

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 3:** Custom BBj Prism grammar — May need to research existing BASIC Prism grammars or write custom tokenizer. If no suitable grammar exists, this becomes a mini-project within Phase 3.

**Phases with standard patterns (skip research-phase):**
- **Phase 1:** Docusaurus scaffolding and GitHub Pages deployment are well-documented with official workflows
- **Phase 2:** Content migration and custom MDX components follow standard Docusaurus patterns
- **Phase 4:** Search plugin installation and Open Graph configuration are standard features

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **Very High** | All versions verified on npm (published 2025-10-17 to 2026-01-29). Docusaurus 3.9.2 is current stable. GitHub Actions workflow is from official docs. No untested tools. |
| Features | **High** | 70% are Docusaurus defaults (verified). Custom features (audience badges, decision callouts, BBj syntax) are straightforward MDX components or Prism config, following documented patterns. |
| Architecture | **Very High** | Docusaurus architecture is well-established. Numbered folder prefixes + autogenerated sidebars is a common pattern. GitHub Pages deployment with actions/deploy-pages is the modern recommended approach. |
| Pitfalls | **High** | Critical pitfalls (baseUrl, monolithic dump, audience clarity) are well-documented Docusaurus failure modes. Prevention strategies are proven. Some pitfalls (MDX parsing, ASCII diagrams) are based on common issues but specific to this content. |

**Overall confidence:** **HIGH**

The research is grounded in verified sources (npm registry, official Docusaurus docs, GitHub releases). The recommended stack is production-ready and actively maintained. The architecture follows established Docusaurus patterns. The primary unknowns are content-specific (how well the strategy paper maps to web documentation) rather than technical.

### Gaps to Address

**BBj Prism syntax grammar:** No built-in Prism language for BBj. Research identified this need but did not produce a grammar. During Phase 3, either:
- Search for existing BASIC/Visual Basic Prism grammars that approximate BBj syntax
- Write a custom Prism language definition (50-100 lines of tokenizer rules)
- Use fallback highlighting (basic/text) if timeline is tight, with proper grammar as v2 enhancement

**Recommendation:** Attempt custom grammar in Phase 3; fallback to `basic` highlighting if it exceeds 4 hours of effort. The site is usable with fallback highlighting; proper BBj syntax is a polish feature, not a blocker.

**Internal vs. public content:** The strategy paper contains budget estimates ($200K-$300K), personnel allocations, and competitive positioning that may not be appropriate for a public site. Research flagged this (pitfall #11) but did not make content decisions. During Phase 2 content migration, explicitly review:
- Chapter 7 (Implementation Roadmap): Resources section has dollar amounts and personnel percentages
- Chapter 1 (BBj Challenge): Competitive comparisons mention GitHub Copilot by name

**Recommendation:** Redact specific dollar amounts, replace with ranges or "to be determined." Reframe competitive comparisons as capability requirements rather than product criticism.

**Audience path effectiveness:** Research identified the three-audience requirement and proposed solutions (audience badges, progressive disclosure, landing page entry paths), but these are untested patterns. The effectiveness depends on editorial discipline during content migration.

**Recommendation:** After Phase 2 initial content migration, conduct a review pass with the question: "If I land on this page from search as a [developer/leader/customer], can I tell if this page is relevant to me within 10 seconds?" Add or adjust audience indicators as needed.

## Sources

### Primary (HIGH confidence)
- npm registry: Versions verified for @docusaurus/core, @docusaurus/preset-classic, @docusaurus/faster, @docusaurus/theme-mermaid, @easyops-cn/docusaurus-search-local (all checked 2026-01-31)
- Docusaurus official documentation (docusaurus.io): Deployment guides, GitHub Pages configuration, theme configuration, MDX usage
- GitHub releases (facebook/docusaurus): Version timeline, feature history (3.6.0 introduced Faster, 3.7.0 added React 19 support, etc.)
- GitHub Actions documentation: actions/deploy-pages@v4, actions/upload-pages-artifact@v3
- PROJECT.md: Project scope, out-of-scope items, audience definition
- bbj-llm-strategy.md: Source content structure, chapter breakdown, code examples

### Secondary (MEDIUM confidence)
- Docusaurus community plugins: @easyops-cn/docusaurus-search-local GitHub repo (1400+ stars, actively maintained)
- Reference documentation sites: Stripe docs, Vercel docs, Tailwind docs (studied for feature patterns)
- Architecture Decision Records (ADR) pattern: General best practice for strategy documentation

### Tertiary (LOW confidence, needs validation)
- Custom BBj Prism grammar: No existing grammar found. Assumption that BASIC/Visual Basic grammars may provide approximation. Needs testing in Phase 3.

---
*Research completed: 2026-01-31*
*Ready for roadmap: yes*
