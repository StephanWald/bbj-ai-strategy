# Pitfalls Research: BBj AI Strategy Documentation Site

Research dimension: What goes wrong when converting a long strategy paper into a Docusaurus documentation site deployed to GitHub Pages, serving three audiences (developers, leadership, customers)?

---

## Critical Pitfalls

### 1. GitHub Pages `baseUrl` Mismatch Breaks All Assets
**Risk:** Docusaurus defaults `baseUrl` to `/`. When deployed to GitHub Pages under a project repository (e.g., `username.github.io/bbj-ai-strategy/`), every CSS file, JS bundle, image, and internal link returns 404. The site appears as unstyled HTML or a blank white page. This is the single most common Docusaurus deployment failure.
**Warning Signs:**
- Site works perfectly on `localhost:3000` but shows blank page or unstyled content on GitHub Pages
- Browser console shows 404 errors for `/assets/js/main.*.js` (missing the repo name prefix)
- Links navigate to `username.github.io/docs/...` instead of `username.github.io/bbj-ai-strategy/docs/...`
**Prevention:**
- Set `baseUrl: '/bbj-ai-strategy/'` in `docusaurus.config.js` (must include both leading and trailing slashes)
- Set `url: 'https://username.github.io'` (the actual GitHub Pages domain, no trailing slash)
- Test the production build locally with `npm run build && npx serve build` before first deploy — but note this only partially validates since the path prefix is different locally
- Use `npm run build` and inspect `build/index.html` to verify asset paths include the baseUrl prefix
**Phase:** Must be correct at initial scaffolding. Fix immediately if deploying to a project repo (not a `username.github.io` repo).

### 2. Monolithic Content Dump Instead of Documentation Architecture
**Risk:** The most common failure when converting a long paper into a docs site: splitting the paper at its existing heading boundaries and pasting each section as a page, without rethinking structure for web consumption. The result reads like a paper split into tabs, not like documentation. Readers bounce because no single page answers their question completely — context is scattered across pages that assumed sequential reading.
**Warning Signs:**
- Pages that start with "As discussed in the previous section..." or assume the reader has read prior pages
- A chapter that is 2000+ words of dense prose with no scannable structure (headers, tables, callouts)
- Readers (or you, re-reading) cannot answer "what is this page about?" from the first two sentences
- The sidebar looks like a table of contents for a paper, not a navigation structure for a docs site
**Prevention:**
- Treat each page as a standalone entry point — someone may land on any page from search or a shared link
- Add a 2-3 sentence summary at the top of every page stating what this page covers and who it's for
- Break long narrative sections into scannable elements: tables for comparisons, code blocks for examples, admonitions for warnings/notes
- Use Docusaurus admonitions (`:::note`, `:::tip`, `:::warning`) to break up wall-of-text sections
- The original paper's 7-chapter structure is a starting point, not a final architecture — some chapters may need sub-pages
**Phase:** Content conversion phase. Review after initial content migration, before polishing.

### 3. `trailingSlash` Inconsistency Causes 404s on GitHub Pages
**Risk:** GitHub Pages serves static files and handles trailing slashes differently than Docusaurus dev server. If `trailingSlash` is not explicitly set in `docusaurus.config.js`, internal links may work in development but produce 404 errors in production. GitHub Pages expects `docs/chapter-1/index.html` when `trailingSlash: true` or `docs/chapter-1.html` when `false` — but Docusaurus default behavior differs between versions.
**Warning Signs:**
- Some pages load, others 404, despite identical link format
- Clicking sidebar links works, but pasting the same URL in a new tab 404s
- Inconsistent behavior between browsers (some auto-add trailing slashes)
**Prevention:**
- Explicitly set `trailingSlash: false` in `docusaurus.config.js` for GitHub Pages (this is the recommended setting for GH Pages)
- Test all navigation paths in production after first deploy, not just the landing page
- If using a custom domain later, re-test — trailing slash behavior can change
**Phase:** Initial scaffolding configuration.

### 4. Code Examples Lose Context When Split Across Pages
**Risk:** The strategy paper has BBj code examples that build on each other and reference multiple BBj generations. When split into separate pages, code examples lose the surrounding explanation of which generation they target, what they demonstrate, and how they relate to other examples. Readers see `window! = sysgui!.addWindow(...)` without understanding this is the modern approach vs. `WINDOW CREATE` on another page.
**Warning Signs:**
- Code blocks appear without a preceding sentence explaining what generation they target
- A reader on the "Fine-Tuning" chapter sees JSON training data but doesn't understand the generation labels without reading the "BBj Challenge" chapter first
- Copy-pasting a code example from a page doesn't work because a prerequisite (like `sysgui!` initialization) is on a different page
**Prevention:**
- Every code block should be self-contained or include the minimal setup context (even if repeated across pages)
- Add a generation badge/tag above code examples: "BBj DWC (Modern)" or "Visual PRO/5 (Legacy)"
- Use Docusaurus tabs component to show the same concept across generations side-by-side where relevant
- For JSON schema examples (training data format), include a complete example, not fragments
**Phase:** Content conversion and content refinement phases.

### 5. Three Audiences, Zero Audience Clarity Per Page
**Risk:** The strategy paper implicitly serves all three audiences (developers, leadership, customers) in every section. When converted to a docs site, no page clearly signals which audience it serves. Developers wade through ROI justifications. Leadership encounters implementation-level JSON schemas. Customers see internal resource estimates. Everyone reads everything and finds 60% irrelevant.
**Warning Signs:**
- Pages mix strategic rationale ("why this matters for the business") with implementation detail ("here's the TypeScript interface") in alternating paragraphs
- The "Resource Requirements" and "Estimated Costs" section is visible to customers/partners on a public site
- No visual or structural differentiation between audience-targeted content
- Sidebar has no grouping or signaling that helps a reader find "their" content
**Prevention:**
- Add audience indicators to pages or sections: "This section is most relevant for [developers/leadership/customers]"
- Use Docusaurus admonitions for audience-specific callouts: `:::tip For Leadership` with a summary, `:::info For Developers` with technical detail
- Consider whether resource estimates and internal costs belong on a public site at all — this may need redaction, not just reorganization
- The landing page should provide three clear entry paths: "I'm a developer", "I'm evaluating this strategy", "I'm a customer/partner"
**Phase:** Content architecture (before writing), revisited during content refinement.

---

## Medium-Risk Pitfalls

### 6. GitHub Pages Deployment Action Misconfiguration
**Risk:** Using the wrong GitHub Actions workflow configuration for Docusaurus. Common issues: using the old `gh-pages` branch approach instead of the newer GitHub Pages Actions workflow, not setting the correct Node.js version, or having the build output directory wrong.
**Prevention:**
- Use Docusaurus's recommended GitHub Actions workflow from their deployment docs (deploy to `gh-pages` branch or use the newer Pages artifact approach)
- Pin Node.js version in the workflow (Node 18+ for Docusaurus 3.x)
- Verify `build` output directory matches what the action deploys
- Set the Pages source in repo Settings > Pages to "GitHub Actions" (not "Deploy from a branch") if using the artifact approach
**Phase:** Initial scaffolding.

### 7. Sidebar Configuration Doesn't Match File Structure
**Risk:** Docusaurus auto-generates sidebar from file system structure, but the default ordering is alphabetical by filename, not logical reading order. With 7 chapters plus sub-pages, the sidebar becomes unintuitive. Alternatively, a manually configured `sidebars.js` drifts out of sync with actual files when content is added or renamed.
**Prevention:**
- Use numeric filename prefixes for ordering: `01-bbj-challenge.md`, `02-strategic-architecture.md`, etc. — OR use `sidebar_position` frontmatter in each doc
- Prefer `sidebar_position` frontmatter over `sidebars.js` manual configuration for this project size — it keeps ordering co-located with content
- Set meaningful `sidebar_label` in frontmatter (short names for navigation, full titles in the page `title`)
- Review sidebar after every content addition

### 8. ASCII Art Diagrams Render Poorly in Docusaurus
**Risk:** The strategy paper has ASCII art architecture diagrams (the infrastructure diagram, VSCode extension architecture, chat system architecture). These render in monospaced font in a raw markdown viewer but may break in Docusaurus depending on the theme, font settings, and container width. Lines misalign, boxes break, and the diagrams become unreadable.
**Warning Signs:**
- Diagram boxes don't align — vertical and horizontal lines are offset
- Diagrams overflow the content area on narrower screens
- Characters like `│`, `┌`, `└` render with inconsistent spacing
**Prevention:**
- Convert ASCII diagrams to Mermaid diagrams (Docusaurus has built-in Mermaid support via `@docusaurus/theme-mermaid`) or to SVG/PNG images
- If keeping ASCII art, wrap in a `<pre>` tag with explicit monospace font and disable line wrapping
- Test all diagrams at the default content width after deploying — not just in a wide IDE window
- Mermaid is the better long-term choice: it's maintainable, responsive, and theme-aware

### 9. Landing Page Is Just Another Doc Page
**Risk:** The Docusaurus landing page (`src/pages/index.js` or `index.tsx`) is a React component, not a markdown doc. If this isn't customized, the site either shows the default Docusaurus template (confusing) or redirects to `/docs` (losing the opportunity for an executive summary entry point). For a strategy documentation site, the landing page is the most important page.
**Prevention:**
- Customize the landing page with: project title, one-paragraph executive summary, three audience entry paths (developer/leadership/customer), and a "start reading" CTA
- Keep it concise — the landing page is a routing page, not a content page
- Use Docusaurus `hero` pattern or custom React components — the default template with "dinosaur" branding must be replaced
**Phase:** Initial scaffolding (replace template), then refine during content phase.

### 10. Forgetting Docusaurus Build Is Static — No Dynamic Content
**Risk:** Planning for content that requires runtime behavior (dynamic audience filtering, interactive code playgrounds, conditional content based on user role) without realizing Docusaurus produces a fully static site. GitHub Pages serves only static files.
**Prevention:**
- All audience targeting must be structural (different pages, different sections) not dynamic (no server-side filtering)
- If code playgrounds are desired for BBj examples, they would require custom client-side components — not a Phase 1 concern
- Search is client-side (Docusaurus built-in search or Algolia) — plan for this, don't assume server-side search
- Any future interactive features need to be client-side React components embedded in MDX

### 11. Sensitive Content on a Public Site
**Risk:** The strategy paper contains resource estimates ($200K-$300K budget), personnel allocation percentages, internal infrastructure specifications, and competitive positioning statements. Publishing these verbatim on a public GitHub Pages site may not be appropriate.
**Warning Signs:**
- Dollar amounts for development costs visible on public pages
- Personnel effort estimates (50% ML Engineer for 6 months) visible to customers
- Competitive comparisons that could age poorly or create friction with partners (e.g., "Copilot won't work")
**Prevention:**
- Review every page before deployment for content appropriateness on a public site
- Move internal-only content (budgets, personnel, internal infrastructure specs) to a separate internal document or remove from the public site
- Reframe competitive comparisons as capability statements ("BBj requires a specialized approach") rather than product criticism
**Phase:** Content conversion — must happen during initial content migration, not as afterthought.

### 12. MDX vs. Standard Markdown Confusion
**Risk:** Docusaurus uses MDX (Markdown + JSX) by default. Standard markdown features like angle brackets (`<`, `>`), curly braces (`{`, `}`), and certain HTML patterns can break MDX parsing. The BBj strategy paper likely contains angle brackets in code explanations and JSON examples with curly braces that could trigger MDX parsing errors.
**Warning Signs:**
- Build errors like "Unexpected token" or "Expected corresponding JSX closing tag"
- Code blocks that render partially or show React error boundaries
- Text with `<something>` being interpreted as JSX components
**Prevention:**
- Wrap all inline code containing `<`, `>`, or `{` in backtick code spans
- Use fenced code blocks (triple backticks) with language identifiers for all code examples
- Test the build (`npm run build`) after adding each chapter — MDX errors are build-time errors, not runtime
- If MDX is unnecessary for this project, consider using `.md` extension (Docusaurus still renders it, with fewer parsing surprises)

---

## Low-Risk Pitfalls

- **Not setting up a custom 404 page**: GitHub Pages shows a generic 404. Add a `src/pages/404.js` with helpful navigation back to the site. Scaffolding phase.
- **Missing `title` and `description` frontmatter**: Without frontmatter metadata, the sidebar shows filenames and SEO/sharing previews are empty. Add to every doc during content conversion.
- **Docusaurus version pinning**: Not pinning the Docusaurus version in `package.json` can cause build breaks when a new version introduces breaking changes. Use exact versions (`3.x.y` not `^3.x.y`). Scaffolding phase.
- **Ignoring the `build` directory in git**: Not adding `build/` and `node_modules/` to `.gitignore` bloats the repository. Scaffolding phase.
- **Broken internal links**: Docusaurus validates internal links at build time (with `onBrokenLinks: 'throw'` config). If this is set to `warn` or `ignore`, broken links silently accumulate. Set to `throw` from day one.
- **Not enabling Docusaurus built-in search**: For a 7-chapter site, search is necessary. Enable the built-in search (`@docusaurus/theme-search-algolia` or the local search plugin) during scaffolding, not as an afterthought.
- **Overriding the Docusaurus theme too early**: Spending time on custom CSS/theming before content is in place. Content structure should drive design decisions, not the reverse. Theme after content is stable.
- **Missing `editUrl` configuration**: For a docs site that will be incrementally improved, configure `editUrl` in `docusaurus.config.js` to point to the GitHub repo's edit page. Enables "Edit this page" links that make future content improvements frictionless.
- **Large images committed to the repo**: Architecture diagrams as high-resolution PNGs bloat git history. Use SVG where possible, compress PNGs, or use Mermaid for diagrams. Content phase.

---

*Research completed: 2026-01-31*
*Source context: PROJECT.md, bbj-llm-strategy.md (~1100 lines), Docusaurus 3.x deployment documentation, GitHub Pages static hosting constraints*
