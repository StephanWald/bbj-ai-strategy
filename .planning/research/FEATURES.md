# Features Research: Documentation Site

## Context

This research catalogs features for a public Docusaurus site communicating BASIS International's BBj AI strategy. The site has 7 topic chapters, 3 audiences (internal devs, leadership, customers/partners), and contains code examples, ASCII architecture diagrams, comparison tables, and training data schemas. It also serves as future implementation context.

Reference sites studied: Stripe docs, Vercel docs, Tailwind docs, Architecture Decision Records (ADR) sites, Kubernetes docs, Rust Book, Backstage docs, internal strategy communications from tech companies.

---

## Table Stakes

Features readers expect from a technical documentation site. Missing any of these causes users to leave or lose trust.

### Navigation & Structure

- **Sidebar navigation with hierarchy** — Persistent left sidebar showing chapter/section structure with expand/collapse. Docusaurus provides this out of the box. | Complexity: low
- **Breadcrumb trail** — Shows current location in hierarchy (Home > Chapter 2 > Section). Built into Docusaurus. | Complexity: low
- **Previous/Next page links** — Sequential navigation at the bottom of each page. Built into Docusaurus. | Complexity: low
- **Table of contents (in-page)** — Right sidebar showing H2/H3 headings on current page with scroll-spy highlighting. Built into Docusaurus. | Complexity: low
- **Mobile-responsive layout** — Content readable on tablets/phones. Docusaurus handles this by default. No custom mobile optimization needed. | Complexity: low

### Search

- **Full-text search** — Ability to search all content. Docusaurus offers local search plugins (lunr-based) or Algolia DocSearch (free for open-source). For a 7-chapter site, local search is sufficient. | Complexity: low (local) / medium (Algolia)

### Content Presentation

- **Syntax-highlighted code blocks** — Code examples rendered with proper highlighting. Docusaurus uses Prism.js. BBj won't have a built-in grammar, so a custom Prism language definition is needed or use a close-enough fallback (e.g., BASIC). | Complexity: low (fallback) / medium (custom BBj grammar)
- **Copy button on code blocks** — One-click copy for code examples. Available as Docusaurus plugin/theme option. | Complexity: low
- **Markdown tables** — Comparison tables, schema tables, etc. rendered cleanly. Native Docusaurus markdown. | Complexity: low
- **Clear typography and whitespace** — Readable fonts, adequate line height, reasonable max content width. Docusaurus defaults are good; minor CSS tweaks at most. | Complexity: low
- **Consistent heading hierarchy** — H1 for page title, H2 for sections, H3 for subsections. Editorial discipline, not a technical feature. | Complexity: low

### Landing & Orientation

- **Landing page with clear value proposition** — Homepage that answers "what is this, who is it for, how do I navigate it." Needs custom implementation in Docusaurus (custom page component or MDX). | Complexity: medium
- **Executive summary or overview page** — High-level summary of the entire strategy before diving into chapters. Can be a standard docs page. | Complexity: low

### Trust & Credibility

- **Last updated dates on pages** — Readers of strategy docs need to know if content is current. Docusaurus supports this via git timestamps or frontmatter. | Complexity: low
- **Version/date in header or footer** — Site-level indicator of document version (e.g., "Strategy v1.0 — January 2025"). Simple footer config. | Complexity: low
- **Clean, professional visual design** — No broken layouts, consistent styling, appropriate use of color. Docusaurus default theme with minor customization. | Complexity: low

### Performance & Accessibility

- **Fast page loads** — Static site generation makes this nearly automatic with Docusaurus. | Complexity: low
- **Accessible markup** — Semantic HTML, alt text for diagrams, keyboard navigable. Docusaurus provides good baseline; requires attention for custom components. | Complexity: low
- **Working links (no 404s)** — All internal and external links resolve. Docusaurus has broken-link detection at build time. | Complexity: low

---

## Differentiators

Features that make a strategy documentation site stand out from generic docs.

### Audience Awareness

- **Audience signal badges** — Visual indicators on sections showing relevance: "Technical Deep Dive," "Leadership Summary," "Customer-Facing." Implemented as custom Docusaurus admonitions or MDX components. Helps the three audiences self-select without needing separate navigation paths. | Complexity: medium
- **TL;DR / Executive Summary blocks** — Collapsible or highlighted summary at the top of each chapter for leadership readers who won't read full technical detail. Custom MDX component. | Complexity: low
- **Progressive disclosure of technical depth** — Main content is accessible to all; expandable sections reveal implementation details for developers. Docusaurus `<details>` tags or custom components. | Complexity: low

### Strategy-Specific Content Patterns

- **Decision records inline** — Architecture Decision Record (ADR) style callouts explaining why specific technical choices were made ("Why Ollama over API-based hosting," "Why custom extension over Copilot"). Custom admonition type. This is what separates strategy docs from reference docs. | Complexity: low
- **Current status indicators** — Visual badges showing implementation status per chapter/initiative: "Research," "In Progress," "Shipped," "Future." Custom MDX component or frontmatter-driven. | Complexity: medium
- **Risk/tradeoff callouts** — Styled callouts that surface risks, tradeoffs, and mitigations directly in context rather than buried in a table at the end. Custom admonition type. | Complexity: low
- **Comparison tables with clear recommendations** — Tables that don't just compare but call out the recommended option (e.g., highlighted row, checkmark). CSS styling on standard tables. | Complexity: low

### Code & Technical Content

- **Custom BBj syntax highlighting** — Prism.js language grammar for BBj so code examples render with proper coloring. Significant differentiator since BBj readers will immediately notice if code looks wrong. | Complexity: medium
- **Generation-labeled code examples** — Visual tabs or badges showing which BBj generation a code example applies to ("All Generations," "DWC Only," "Visual PRO/5"). Docusaurus tabs component or custom MDX. | Complexity: medium
- **ASCII diagram rendering** — Ensure the ASCII architecture diagrams from the strategy paper render correctly in a monospace block with no wrapping issues. May need custom CSS for wide diagrams. | Complexity: low
- **Side-by-side code comparison** — Show legacy vs. modern code patterns next to each other (e.g., Visual PRO/5 vs. DWC). Docusaurus tabs or custom two-column layout. | Complexity: medium

### Navigation & Discovery

- **Chapter progress/roadmap visualization** — Visual indicator showing the 7 chapters and where the reader is in the overall narrative arc. Custom component, possibly in the sidebar or as a banner. | Complexity: medium
- **Cross-references between chapters** — Contextual links like "This relates to the RAG Database design discussed in Chapter 6." Editorial practice plus anchor links. | Complexity: low
- **Glossary with hover definitions** — Key terms (DWC, Langium, RAG, LoRA) get tooltip definitions on hover. Custom MDX component or plugin. Especially valuable given the niche terminology. | Complexity: medium

### Visual Communication

- **Mermaid or diagram support** — Render architecture diagrams as Mermaid charts instead of (or in addition to) ASCII art. Docusaurus has Mermaid plugin. More professional than ASCII for public audiences. | Complexity: medium
- **Key metrics/numbers callout blocks** — Styled blocks for important numbers ("95% syntactic validity target," "$200K-300K Year 1 investment"). Custom MDX component. Catches leadership eyes. | Complexity: low

### Engagement & Feedback

- **"Edit this page" link** — Links to the source markdown on GitHub. Built into Docusaurus. Signals openness and enables contributions. | Complexity: low
- **Feedback mechanism** — Simple "Was this helpful? Yes/No" or link to file an issue. Can be a GitHub Issues link per page. Lightweight but signals the doc is maintained. | Complexity: low (link) / medium (widget)

### SEO & Shareability

- **Open Graph / social meta tags** — Custom og:title, og:description, og:image per page so links shared in Slack/email look professional. Docusaurus supports via frontmatter and config. | Complexity: low
- **Descriptive URLs** — Clean slugs like `/strategy/fine-tuning` not `/docs/chapter-3`. Docusaurus slug configuration. | Complexity: low
- **Sitemap generation** — Automatic sitemap for search engines. Docusaurus plugin. | Complexity: low

---

## Anti-Features

Things to deliberately NOT build. Each would add complexity without matching the project's goals.

- **Authentication / gated content** — The site is explicitly public. Adding login adds friction and contradicts the goal of accessible strategy communication. (Confirmed in PROJECT.md: out of scope.)
- **Interactive chat widget or AI demo** — This site documents the AI strategy; it is not the AI system. Building a chat demo conflates the documentation project with the implementation project and adds massive scope. (Confirmed in PROJECT.md: out of scope.)
- **Multi-language / i18n** — English only. The audience is English-speaking developers and leadership. Translation adds ongoing maintenance burden with no clear ROI for this niche. (Confirmed in PROJECT.md: out of scope.)
- **User accounts or personalization** — No need for saved preferences, bookmarks, or personalized views. This is a read-through strategy document, not a reference portal visited daily.
- **Comments / discussion per page** — Invites low-signal noise on a strategy document. Feedback should flow through structured channels (GitHub Issues, internal meetings), not inline comments.
- **PDF export / print stylesheet** — Adds complexity for an edge case. The source markdown can be shared directly. If leadership needs a PDF, a simple browser print works.
- **Analytics dashboards or complex tracking** — Basic page-view analytics (e.g., Plausible, simple GA) is fine. Do not build custom dashboards tracking engagement per section, scroll depth, etc. This is documentation, not a marketing funnel.
- **Blog / changelog section** — The strategy is versioned as a document, not as a stream of updates. A "What's New" section on the landing page is sufficient; a full blog adds editorial overhead.
- **Notification system** — No need to alert readers about updates. The site is consumed on-demand, not subscribed to.
- **Dark mode toggle** — Docusaurus includes this by default (no effort to include), but do NOT invest time in custom dark-mode theming for diagrams, custom components, etc. Accept Docusaurus defaults.
- **Heavyweight search (Algolia, ElasticSearch)** — Overkill for a 7-chapter site. Local search (lunr/flexsearch) is sufficient. Algolia DocSearch is free for OSS but adds external dependency and setup overhead.
- **Custom video player / embedded videos** — Video content adds production overhead and maintenance burden. Diagrams, code blocks, and text communicate the strategy effectively. If a video is ever needed, a simple YouTube embed suffices.

---

## Feature Dependencies

| Feature | Depends On |
|---------|-----------|
| Sidebar navigation | Docusaurus scaffolding complete |
| Full-text search | All content written (search index needs content) |
| Syntax-highlighted code blocks | Custom BBj Prism grammar (for proper highlighting) |
| Copy button on code blocks | Docusaurus theme config |
| Landing page | Chapter structure finalized (to build navigation/overview) |
| Audience signal badges | Custom MDX component created |
| TL;DR blocks | Custom MDX component or admonition type |
| Decision record callouts | Custom admonition type defined in Docusaurus config |
| Current status indicators | Custom MDX component; chapter content written |
| Generation-labeled code examples | Docusaurus tabs component; BBj syntax highlighting |
| Side-by-side code comparison | Docusaurus tabs or custom CSS grid layout |
| Mermaid diagram support | Docusaurus Mermaid plugin installed |
| Glossary hover definitions | Custom MDX component; glossary terms defined |
| Chapter progress visualization | Sidebar config; all 7 chapters scaffolded |
| Cross-references | Content written for target chapters (need anchor targets) |
| Open Graph meta tags | Landing page content; site metadata configured |
| Descriptive URLs | Docusaurus slug configuration in frontmatter |
| Edit this page links | GitHub repo configured in docusaurus.config.js |
| Key metrics callout blocks | Custom MDX component created |
| Risk/tradeoff callouts | Custom admonition type defined |
| Comparison tables with recommendations | CSS for highlighted rows; editorial convention |
| Feedback mechanism | GitHub Issues enabled on repo |
| Last updated dates | Git history or frontmatter convention established |

---

## Implementation Priority Tiers

Based on complexity, dependencies, and value to the three audiences.

### Tier 1: Build First (scaffold + content prerequisites)
These are either free with Docusaurus or required before content work begins.

| Feature | Complexity | Rationale |
|---------|-----------|-----------|
| Sidebar navigation | Low | Docusaurus default; defines chapter structure |
| Breadcrumbs | Low | Docusaurus default |
| Previous/Next links | Low | Docusaurus default |
| Table of contents | Low | Docusaurus default |
| Mobile responsive | Low | Docusaurus default |
| Clean typography | Low | Minor CSS tweaks |
| Copy button on code blocks | Low | Theme config toggle |
| Edit this page links | Low | Config change |
| Descriptive URLs | Low | Frontmatter slugs |
| Last updated dates | Low | Config toggle |
| Version in footer | Low | Config change |

### Tier 2: Build During Content Phase (enhance content as it's written)
These improve how content is consumed. Build the components, then use them as chapters are written.

| Feature | Complexity | Rationale |
|---------|-----------|-----------|
| Landing page | Medium | Needed once chapter structure is stable |
| Decision record callouts | Low | Custom admonition; used across all chapters |
| TL;DR / Executive Summary blocks | Low | Simple component; high value for leadership |
| Risk/tradeoff callouts | Low | Custom admonition; used in most chapters |
| Audience signal badges | Medium | Helps multi-audience navigation |
| Progressive disclosure (details tags) | Low | Native HTML; use where technical depth varies |
| Comparison tables with recommendations | Low | CSS styling convention |
| Key metrics callout blocks | Low | Simple styled component |
| Cross-references | Low | Editorial practice; no tooling needed |
| Local full-text search | Low | Plugin install once content exists |

### Tier 3: Polish Phase (after all content is written)
Nice-to-haves that improve the professional feel but aren't needed for content creation.

| Feature | Complexity | Rationale |
|---------|-----------|-----------|
| Custom BBj syntax highlighting | Medium | Enhances code readability; not blocking |
| Generation-labeled code examples | Medium | Requires tabs; best added during code review |
| Side-by-side code comparison | Medium | Layout work; used in specific chapters only |
| Mermaid diagram support | Medium | Alternative to ASCII; nice but ASCII works |
| Glossary hover definitions | Medium | Custom component; best after terminology stabilizes |
| Chapter progress visualization | Medium | Custom component; best after all 7 chapters exist |
| Current status indicators | Medium | Needs content and implementation status tracking |
| Open Graph meta tags | Low | Config + per-page frontmatter |
| Sitemap | Low | Plugin install |
| Feedback mechanism | Low | GitHub Issues link |

---

## Key Observations

1. **Docusaurus gives you 70% of table stakes for free.** The real work is content, not features. Most Tier 1 items are configuration, not development.

2. **The biggest differentiators are content patterns, not technology.** Decision record callouts, audience badges, TL;DR blocks, and status indicators are what separate a strategy doc from generic API reference. These are low-complexity custom MDX components.

3. **BBj syntax highlighting is the most impactful technical feature.** Because the audience knows BBj intimately, broken or missing syntax highlighting will undermine credibility faster than any other missing feature. This should be prioritized above other Tier 3 items.

4. **Multi-audience support is better handled with content conventions than navigation.** Separate audience paths (e.g., /developer vs. /leadership) would fragment the narrative. Instead, use inline badges and progressive disclosure so all audiences follow the same structure but self-select depth.

5. **The site's dual purpose (communication + implementation context) means machine-readability matters.** Clean markdown, structured frontmatter, consistent heading hierarchy, and well-labeled code blocks make the content useful as future LLM context for actually building the system.

6. **Anti-features are load-bearing decisions.** The "Out of Scope" section in PROJECT.md already captures the biggest ones. The anti-features listed above extend that with rationale for features that might seem tempting but would add complexity without proportional value.
