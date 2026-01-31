# Phase 7: Custom Branding - Context

**Gathered:** 2026-01-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Apply BASIS International brand identity to the Docusaurus documentation site. Replace default favicon, navbar logo, and color theme with BASIS brand assets. Typography updates only if BASIS specifies brand fonts. The reference implementation is the bbj-dwc-tutorial Docusaurus project at `/Users/beff/_workspace/bbj-dwc-tutorial`.

</domain>

<decisions>
## Implementation Decisions

### Logo & favicon source
- Copy `dwc-logo.png` (198x199px navbar logo) and `favicon.png` (32x32) from `/Users/beff/_workspace/bbj-dwc-tutorial/static/img/`
- Also copy `favicon.ico` if present in the reference project
- Do NOT copy other assets (social card, unused logo.svg, etc.)

### Navbar display
- Show logo image + site title text side by side (logo left, "BBj AI Strategy" title text next to it)
- Same pattern as the DWC tutorial navbar

### Color palette
- Copy the exact blue color palette from the DWC tutorial's `custom.css`
- Light mode primary: `#2563eb` (Tailwind blue-600 scale)
- Dark mode primary: `#60a5fa` (Tailwind blue-400 scale)
- Copy all 7 shade variants for both light and dark modes

### Dark mode colors
- Copy light/dark color variable pairs from DWC tutorial as-is
- No custom adjustments needed

### Default cleanup
- Remove any leftover Docusaurus default branding files (dinosaur logo.svg, default social card, etc.) from `static/img/`
- Clean references to removed files in config

### Claude's Discretion
- Whether the logo needs a separate dark mode variant (inspect the actual image and decide based on contrast)
- Typography — copy DWC tutorial approach if it has custom fonts, otherwise leave Infima defaults
- Exact Prism code highlighting theme (can match DWC tutorial's github/dracula setup)

</decisions>

<specifics>
## Specific Ideas

- Reference implementation: `/Users/beff/_workspace/bbj-dwc-tutorial` — match its branding approach for consistency across BASIS documentation sites
- The DWC tutorial uses `prismThemes.github` (light) and `prismThemes.dracula` (dark) for code blocks

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-custom-branding*
*Context gathered: 2026-01-31*
