# Stack Research: BBj AI Strategy Docs

**Researched:** 2026-01-31
**Scope:** Docusaurus documentation site for BASIS International's BBj AI strategy
**Method:** npm registry, GitHub releases, official Docusaurus docs (all verified live)

---

## Recommended Stack

### Core Framework

- **Docusaurus 3.9.2** (latest stable, released 2025-10-17) -- The current and correct version. Docusaurus 3.x is the only actively maintained line. There is no Docusaurus 4.x yet; the maintainer (Sebastien Lorber) is incrementally introducing v4 features via `future` flags in v3. React 19 support was added in 3.7.0. Node.js 22 is the default runtime as of 3.8.1.

- **@docusaurus/preset-classic 3.9.2** -- Bundles the standard plugins (docs, blog, pages, sitemap, gtag) and the classic theme. Use this as the foundation; do not assemble plugins individually unless you have a specific reason to deviate.

- **@docusaurus/faster 3.9.2** -- Enables the Rspack-based build pipeline (Rust toolchain: Rspack bundler, SWC transpiler/minifier, Lightning CSS). Introduced in 3.6.0, stable and used in production on the Docusaurus site itself. Provides 2-4x faster builds. Enable with a single config flag:
  ```js
  future: {
    experimental_faster: true,
  }
  ```
  WHY: Build speed matters for iterative content authoring. The "experimental" label refers to the config key name, not stability. The Docusaurus team plans to make this the default in v4.

- **Node.js 22 LTS** -- Docusaurus requires Node >=20.0. Use 22 LTS (current LTS line in 2026) for best compatibility. The Docusaurus team upgraded their own CI to Node 22 in 3.8.1.

- **npm** (package manager) -- The Docusaurus docs and GitHub Actions examples use npm by default. For a documentation site with no complex monorepo needs, npm keeps things simple and avoids the additional layer of Yarn/pnpm configuration. Lock with `package-lock.json`.

### Themes

- **@docusaurus/theme-classic** (included in preset-classic) -- Provides the standard documentation layout with sidebar navigation, dark mode, code blocks with syntax highlighting (Prism), table of contents, and responsive design. No reason to use a custom theme for this project.

- **@docusaurus/theme-mermaid** (latest: 3.9.2) -- Enables Mermaid diagram rendering in Markdown code blocks. Supports Mermaid 10 and 11, including architecture diagrams. Essential for this project because the strategy paper contains architecture diagrams. Mermaid diagrams are more maintainable than static images and can be version-controlled as text.
  ```js
  themes: ['@docusaurus/theme-mermaid'],
  markdown: { mermaid: true },
  ```
  WHY: The BBj strategy paper has multiple architecture diagrams (infrastructure overview, VSCode extension architecture, chat system architecture). Converting ASCII art to Mermaid diagrams makes them interactive, dark-mode-aware, and maintainable.

### Plugins & Extensions

- **@docusaurus/plugin-content-docs** (included in preset-classic) -- Core docs plugin. Handles sidebar generation, versioning, MDX processing. Configure with `sidebarPath` pointing to `sidebars.js` for explicit chapter ordering.

- **@docusaurus/plugin-sitemap** (included in preset-classic) -- Auto-generates sitemap.xml. No configuration needed beyond what preset-classic provides. Important for SEO of a public site.

- **@easyops-cn/docusaurus-search-local 0.52.3** (last published 2026-01-29) -- Client-side local search using lunr.js. Actively maintained; compatible with Docusaurus 3.x. WHY over Algolia: Algolia DocSearch requires an application/approval process and external service dependency. For a 7-chapter documentation site, local search is simpler, has zero external dependencies, works offline, and requires no API keys. The search index will be small enough to download to the browser.
  ```js
  themes: [
    ['@easyops-cn/docusaurus-search-local', { hashed: true }],
  ],
  ```

- **@docusaurus/plugin-ideal-image** (included in Docusaurus ecosystem, 3.9.2) -- OPTIONAL. Only add if the site needs responsive image optimization for architecture diagrams exported as PNGs. For a text-heavy docs site with Mermaid diagrams, this is likely unnecessary at launch. Revisit if image-heavy pages appear later.

- **@docusaurus/plugin-google-gtag** (included in preset-classic) -- OPTIONAL. Add Google Analytics tracking if BASIS wants to measure which chapters get the most traffic and which audiences are engaging. Configure only when a GA measurement ID is available.

### Content Format

- **MDX 3** (bundled with Docusaurus 3.x) -- Write content in `.md` or `.mdx` files. MDX allows embedding React components in Markdown when needed (tabs, admonitions, custom callouts). For this project, standard Markdown with front matter will cover 95% of needs. Use MDX features only for:
  - Tabbed code examples (showing different BBj generations side by side)
  - Custom admonition blocks for audience-specific callouts
  - Embedding Mermaid diagrams

- **Front matter pattern** -- Each doc should specify:
  ```yaml
  ---
  title: "Chapter Title"
  sidebar_position: 1
  description: "SEO description for the chapter"
  ---
  ```

- **Code blocks with language hints** -- Docusaurus supports syntax highlighting via Prism. BBj is not a built-in Prism language, but `basic` or a custom language definition can be used. Register a custom Prism language for `bbj` in `docusaurus.config.js`:
  ```js
  prism: {
    additionalLanguages: ['java', 'json', 'typescript', 'bash'],
    // Custom BBj language can be added via prism-include-languages
  },
  ```

### Deployment

- **GitHub Actions + GitHub Pages** -- Use the official Docusaurus-recommended workflow with `actions/deploy-pages@v4`. This is the standard 2026 approach (replaces the older `docusaurus deploy` CLI method and the gh-pages branch approach).

  Two workflow files:
  1. `.github/workflows/deploy.yml` -- Triggers on push to `main`, builds the site, uploads artifact, deploys to GitHub Pages using the modern `actions/upload-pages-artifact@v3` + `actions/deploy-pages@v4` pipeline.
  2. `.github/workflows/test-deploy.yml` -- Triggers on PRs to `main`, runs `npm run build` to verify the site builds without errors.

  Key configuration in `docusaurus.config.js`:
  ```js
  url: 'https://<org>.github.io',
  baseUrl: '/bbj-ai-strategy/',
  organizationName: '<github-org>',
  projectName: 'bbj-ai-strategy',
  trailingSlash: false,
  ```

  WHY this approach over `docusaurus deploy` CLI:
  - No need for GIT_USER tokens or SSH keys
  - Uses GitHub's native Pages deployment with OIDC authentication
  - PR preview builds catch broken content before merge
  - Standard approach recommended by Docusaurus docs as of 2025

- **GitHub Pages settings**: Set source to "GitHub Actions" (not "Deploy from a branch"). This is the modern configuration.

- **`.nojekyll` file in `static/`** -- Prevents GitHub Pages from running Jekyll on the output. Required because Docusaurus outputs files that start with `_`.

### Content Authoring

- **Direct Markdown editing** -- For a research-driven content process, write Markdown files directly in the `docs/` directory. No CMS layer needed. Each chapter is a `.md` file (or folder with `index.md` for chapters with sub-pages).

- **`docusaurus start` for live preview** -- The dev server provides hot-reloading on file save. With `@docusaurus/faster` enabled, rebuilds are near-instant.

- **Sidebar configuration via `sidebars.js`** -- Explicit ordering of the 7 chapters. Use a manual sidebar definition rather than auto-generated, because chapter order matters for the narrative flow:
  ```js
  module.exports = {
    strategy: [
      'intro',
      'the-bbj-challenge',
      'strategic-architecture',
      'fine-tuning',
      'ide-integration',
      'documentation-chat',
      'rag-database-design',
      'implementation-roadmap',
    ],
  };
  ```

- **Admonitions** -- Built into Docusaurus. Use for audience-targeted callouts:
  - `:::tip` for practical guidance (developers)
  - `:::info` for strategic context (leadership)
  - `:::note` for additional detail

### Project Structure

```
bbj-ai-strategy/
  docs/
    intro.md                    # Landing / executive summary
    the-bbj-challenge.md        # Chapter 1
    strategic-architecture.md   # Chapter 2
    fine-tuning.md             # Chapter 3
    ide-integration.md         # Chapter 4
    documentation-chat.md      # Chapter 5
    rag-database-design.md     # Chapter 6
    implementation-roadmap.md  # Chapter 7
  src/
    css/
      custom.css               # Theme overrides, BBj syntax colors
    pages/
      index.js                 # Landing page (optional custom)
  static/
    img/                       # Static images if needed
    .nojekyll                  # Required for GitHub Pages
  .github/
    workflows/
      deploy.yml               # Production deploy
      test-deploy.yml          # PR build check
  docusaurus.config.js         # Site configuration
  sidebars.js                  # Chapter ordering
  package.json
```

---

## What NOT To Use (And Why)

### Do Not Use: Docusaurus 2.x
Docusaurus 2 is end-of-life. Version 3.x has been stable since late 2023 and is the only maintained line. Starting a new project on 2.x would immediately create upgrade debt.

### Do Not Use: Algolia DocSearch (for now)
Algolia DocSearch is the "official" search recommendation, but it requires applying for the free program (approval can take weeks), depends on an external crawler, and is overkill for a 7-chapter site. Local search (`@easyops-cn/docusaurus-search-local`) provides instant, zero-dependency search. If the site grows significantly or needs AI-powered "Ask AI" search later, Algolia can be added as a drop-in replacement.

### Do Not Use: `docusaurus deploy` CLI
The older deployment method that clones, builds, and force-pushes to a `gh-pages` branch. The GitHub Actions approach with `actions/deploy-pages` is cleaner, more secure (uses OIDC tokens instead of PATs), and is now the recommended approach in the Docusaurus docs.

### Do Not Use: Webpack (default bundler)
Docusaurus still defaults to Webpack, but the `@docusaurus/faster` package with Rspack is production-ready and 2-4x faster. There is no reason to start a new project in 2026 without enabling it. The Docusaurus site itself runs on it.

### Do Not Use: Yarn or pnpm
For a standalone documentation site (not a monorepo), npm is the simplest choice with the best compatibility with GitHub Actions caching. Yarn and pnpm add configuration complexity with no meaningful benefit for this use case.

### Do Not Use: MkDocs, GitBook, or VitePress
- **MkDocs** (Python): Good tool, but Python ecosystem is disconnected from the JS/React ecosystem that Docusaurus uses. No component extensibility.
- **GitBook**: Proprietary platform with vendor lock-in. Free tier has limitations. No custom component support.
- **VitePress** (Vue): Strong competitor, but Docusaurus has a larger ecosystem, better plugin selection, and the project requirements don't need Vue-specific features.
- **Starlight** (Astro): Newer entrant with good DX, but smaller plugin ecosystem and less battle-tested for large documentation sites.

### Do Not Use: Custom Prism BBj Syntax (at launch)
Adding a custom Prism language grammar for BBj would be nice, but it's a yak-shave for launch. Use `basic` or `vb` as approximate syntax highlighting for BBj code blocks initially. Build a proper BBj grammar as a later enhancement.

### Do Not Use: Blog Plugin
The preset-classic includes a blog plugin. Disable it -- this is a strategy documentation site, not a blog. Remove the blog directory and set `blog: false` in the preset config to keep the build clean.

### Do Not Use: Versioning
Docusaurus supports doc versioning, but this site presents a single strategy document, not API docs that need version tracking. Versioning would add unnecessary complexity. Track changes through git history instead.

### Do Not Use: i18n
The site is English-only per project constraints. Do not configure i18n -- it adds build complexity and doubles build time.

---

## Alternatives Considered

| Option | Why Not |
|--------|---------|
| MkDocs (Material) | Python ecosystem; no React component extensibility; weaker plugin ecosystem for JS-heavy content |
| VitePress | Vue-based; smaller ecosystem; Docusaurus has better sidebar/docs-specific features out of the box |
| GitBook | Proprietary; vendor lock-in; limited customization; free tier restrictions |
| Starlight (Astro) | Newer, smaller community; fewer battle-tested plugins; less documentation about edge cases |
| Nextra (Next.js) | Heavier runtime; designed for apps, not static docs; overkill for a content-only site |
| Plain GitHub Pages + Jekyll | No search, no sidebar nav, no dark mode, no code block features; would require building everything from scratch |
| Algolia DocSearch | Requires external service + approval; overkill for 7 chapters; can be added later if needed |
| Netlify/Vercel deployment | Adds vendor dependency when GitHub Pages is free, simpler, and sufficient for a static docs site |
| Docusaurus 2.x | End of life; missing React 19 support, Rspack/faster builds, Mermaid 11, MDX 3 |
| Yarn Berry / pnpm | Added complexity with no benefit for a standalone docs project |

---

## Confidence Levels

| Recommendation | Confidence | Notes |
|----------------|------------|-------|
| Docusaurus 3.9.2 | **Very High** | Verified on npm (published 2025-10-17). Latest stable. Actively maintained by Sebastien Lorber at Meta. |
| @docusaurus/preset-classic | **Very High** | Standard starting point for all Docusaurus docs sites. No reason to deviate. |
| @docusaurus/faster (Rspack) | **High** | Production-ready since 3.6.0 (Nov 2024). Used on docusaurus.io itself. "Experimental" label is about the config key name, not stability. One edge case: custom webpack plugins may need minor adaptation, but this project has none. |
| Node.js 22 LTS | **Very High** | Docusaurus team uses Node 22 in their CI. Well within the >=20.0 requirement. |
| npm as package manager | **High** | Simplest option. GitHub Actions examples in Docusaurus docs default to npm. Only reconsider if this becomes part of a monorepo. |
| @docusaurus/theme-mermaid | **High** | Official Docusaurus theme. Supports Mermaid 10/11. Architecture diagrams in the strategy paper are a clear use case. |
| @easyops-cn/docusaurus-search-local | **High** | Actively maintained (last publish: 2026-01-29). v0.52.3 is compatible with Docusaurus 3.x. Well-established community plugin with 1400+ GitHub stars. Small site = small search index = ideal for local search. |
| GitHub Actions + deploy-pages | **Very High** | Exact workflow YAML is provided in official Docusaurus docs. Uses GitHub's native OIDC-based Pages deployment. Battle-tested across thousands of Docusaurus sites. |
| MDX 3 / Markdown content | **Very High** | Built into Docusaurus 3.x. No alternative needed. |
| Disable blog, versioning, i18n | **Very High** | Project scope is explicitly single-language, single-version strategy docs. These features add build time and complexity with zero benefit. |
| Skip Algolia for now | **Medium-High** | Correct for launch. If the site grows beyond 7 chapters or BASIS wants AI-powered search, Algolia can be swapped in later -- the theme is a drop-in replacement. |
| Skip custom BBj Prism grammar | **Medium** | Pragmatic for launch. Code blocks will look reasonable with `basic` highlighting. A proper BBj grammar would be a nice enhancement but is not blocking. |

---

## Version Matrix (All Verified 2026-01-31)

| Package | Version | Published | Source |
|---------|---------|-----------|--------|
| @docusaurus/core | 3.9.2 | 2025-10-17 | npm registry |
| @docusaurus/preset-classic | 3.9.2 | 2025-10-17 | npm registry |
| @docusaurus/faster | 3.9.2 | 2025-10-17 | npm registry |
| @docusaurus/theme-mermaid | 3.9.2 | 2025-10-17 | npm registry |
| @easyops-cn/docusaurus-search-local | 0.52.3 | 2026-01-29 | npm registry |
| Node.js | 22 LTS | -- | nodejs.org |

---

## Key Docusaurus 3.x Timeline (for context)

- **3.6.0** (2024-11-04): Docusaurus Faster introduced (Rspack, SWC, Lightning CSS). 2-4x build speed improvement.
- **3.7.0** (2025-01-03): React 19 support. SVGR plugin. Bluesky/Mastodon social icons.
- **3.8.0** (2025-05-26): CSS cascade layers. Rspack persistent cache. Worker thread SSG.
- **3.8.1** (2025-06-06): Default Node.js upgraded to 22.
- **3.9.0** (2025-09-25): DocSearch v4.1 integration. Rspack upgraded to 1.5. Mermaid ELK layout support.
- **3.9.2** (2025-10-17): Current latest. Bug fixes only.

No Docusaurus 4.0 has been announced. The v4 transition will happen via the `future` flag mechanism already in v3.

---

*Research conducted by examining npm registry, GitHub releases (facebook/docusaurus), and official Docusaurus documentation site at docusaurus.io.*
