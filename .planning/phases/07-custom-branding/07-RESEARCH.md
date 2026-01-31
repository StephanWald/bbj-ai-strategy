# Phase 7: Custom Branding - Research

**Researched:** 2026-01-31
**Domain:** Docusaurus 3.x theming (favicon, navbar logo, CSS variables, typography)
**Confidence:** HIGH

## Summary

This phase replaces Docusaurus defaults with BASIS International branding on the BBj AI Strategy documentation site. The reference implementation (`/Users/beff/_workspace/bbj-dwc-tutorial`) provides exact assets and CSS values to copy, making this a well-defined copy-and-adapt operation rather than a design exercise.

Key findings: (1) The favicon.ico already matches the reference project (identical MD5 hash), but `favicon.png` is missing and the config points to `.ico` instead of `.png`. (2) The navbar has no logo configured -- it needs `dwc-logo.png` added plus a `logo` object in `docusaurus.config.ts`. (3) The custom.css color variables use Docusaurus default green (#2e8555) and must be replaced with the blue palette (#2563eb). (4) The reference project uses no custom fonts, so typography stays as Infima defaults. (5) The existing `logo.svg` is the Docusaurus default dinosaur and should be removed.

**Primary recommendation:** Copy `dwc-logo.png` and `favicon.png` from the reference project's `static/img/`, update `docusaurus.config.ts` (favicon path + navbar logo), replace the color palette in `custom.css`, update hardcoded admonition colors, and delete the default `logo.svg`.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Docusaurus | 3.9.2 | Site generator | Already installed; theming is built-in |
| Infima | (bundled) | CSS framework | Docusaurus bundles Infima; color theming uses its CSS variables |
| prism-react-renderer | ^2.3.0 | Code syntax highlighting | Already configured with github/dracula themes |

### Supporting
No additional libraries needed. All branding changes are pure configuration and CSS.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Infima CSS variables | Swizzled theme components | Overkill for color changes; CSS variables are the standard approach |
| Static PNG favicon | SVG favicon | PNG/ICO has better browser compatibility; reference project uses PNG |

**Installation:**
```bash
# No packages to install -- all changes are config and CSS
```

## Architecture Patterns

### Relevant File Structure
```
static/
├── img/
│   ├── dwc-logo.png         # NEW - Navbar logo (198x199px, from reference)
│   ├── favicon.png           # NEW - PNG favicon (32x32, from reference)
│   └── favicon.ico           # KEEP - Already matches reference (identical)
│   └── logo.svg              # DELETE - Docusaurus default dinosaur
src/
└── css/
    └── custom.css            # MODIFY - Replace green palette with blue
docusaurus.config.ts          # MODIFY - favicon path + navbar logo config
```

### Pattern 1: Infima CSS Variable Override
**What:** Override `--ifm-color-primary` and its 6 shade variants in `:root` and `[data-theme='dark']` selectors
**When to use:** Any time you want to change the site's primary color scheme
**Example:**
```css
/* Source: Reference project /Users/beff/_workspace/bbj-dwc-tutorial/src/css/custom.css */
:root {
  --ifm-color-primary: #2563eb;
  --ifm-color-primary-dark: #1d4ed8;
  --ifm-color-primary-darker: #1e40af;
  --ifm-color-primary-darkest: #1e3a8a;
  --ifm-color-primary-light: #3b82f6;
  --ifm-color-primary-lighter: #60a5fa;
  --ifm-color-primary-lightest: #93c5fd;
}

[data-theme='dark'] {
  --ifm-color-primary: #60a5fa;
  --ifm-color-primary-dark: #3b82f6;
  --ifm-color-primary-darker: #2563eb;
  --ifm-color-primary-darkest: #1d4ed8;
  --ifm-color-primary-light: #93c5fd;
  --ifm-color-primary-lighter: #bfdbfe;
  --ifm-color-primary-lightest: #dbeafe;
}
```

### Pattern 2: Navbar Logo Configuration
**What:** Add a `logo` object to `themeConfig.navbar` in `docusaurus.config.ts`
**When to use:** Display a brand image in the navbar alongside the site title
**Example:**
```typescript
// Source: Reference project /Users/beff/_workspace/bbj-dwc-tutorial/docusaurus.config.ts
navbar: {
  title: 'BBj AI Strategy',
  logo: {
    alt: 'BASIS Logo',
    src: 'img/dwc-logo.png',
  },
  items: [ /* ... */ ],
},
```

### Pattern 3: Favicon Configuration
**What:** Set `favicon` in the top-level Docusaurus config to point to the brand favicon
**When to use:** Replace the browser tab icon
**Example:**
```typescript
// Source: Docusaurus docs (https://docusaurus.io/docs/api/docusaurus-config)
const config: Config = {
  favicon: 'img/favicon.png',  // Reference uses .png not .ico
  // ...
};
```

### Anti-Patterns to Avoid
- **Swizzling for simple color changes:** Don't swizzle theme components just to change colors. CSS variable overrides are the correct approach for palette changes.
- **Hardcoding colors that should reference variables:** The admonition `border-color` correctly uses `var(--ifm-color-primary)`, but the background uses hardcoded RGB. When changing the primary color, update both.
- **Forgetting dark mode:** Every `:root` color variable needs a corresponding `[data-theme='dark']` variant.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Color palette shades | Manual shade calculation | Copy exact values from reference project | The reference uses Tailwind blue-600 scale with tested shade progressions |
| Dark mode toggle | Custom toggle component | Docusaurus built-in `colorMode` config | Already configured with `respectPrefersColorScheme: true` |
| Favicon generation | Multi-format favicon pipeline | Copy existing `.png` and `.ico` from reference | Reference already has properly sized 32x32 assets |

**Key insight:** The reference project (`bbj-dwc-tutorial`) has already solved every branding problem. Copy its assets and CSS values rather than deriving them independently.

## Common Pitfalls

### Pitfall 1: Admonition Color Mismatch After Primary Color Change
**What goes wrong:** The current `custom.css` has admonition styles (`.alert--success`, `.alert--info`) with hardcoded green RGB values (e.g., `rgba(46, 133, 85, 0.08)`). The `.alert--success` border uses `var(--ifm-color-primary)` which will auto-update to blue, creating a green-background/blue-border mismatch.
**Why it happens:** The admonition colors were written when the primary was green (#2e8555 = rgb(46, 133, 85)). Changing primary to blue (#2563eb) only updates CSS variable references, not hardcoded values.
**How to avoid:** Update the `.alert--success` background colors to use the new blue primary values (e.g., `rgba(37, 99, 235, 0.08)` for light mode). Keep `.alert--info` unchanged since it already uses a blue tone (#3678c2). Also update the dark mode `.alert--success` colors from the old green (`rgba(37, 194, 160, ...)`) to the new blue (`rgba(96, 165, 250, ...)`).
**Warning signs:** Green-tinted admonition backgrounds with blue borders after the color change.

### Pitfall 2: Missing favicon.png
**What goes wrong:** The current config uses `'img/favicon.ico'` but the reference project uses `'img/favicon.png'`. The `.ico` file exists and is identical between projects, but the `.png` file is missing from the current project.
**Why it happens:** Phase 5 cleanup kept `favicon.ico` and `logo.svg` but didn't add `favicon.png` since it wasn't needed at the time.
**How to avoid:** Copy `favicon.png` from the reference project and update the config to use `'img/favicon.png'` (matching the reference pattern). Keep `favicon.ico` as a fallback for older browsers.
**Warning signs:** Config says `favicon.png` but the file doesn't exist, causing a broken favicon.

### Pitfall 3: Forgetting to Remove Default Docusaurus Assets
**What goes wrong:** The `static/img/logo.svg` is the Docusaurus default octopus/dinosaur. If left in place, it could be accidentally referenced or confuse future maintainers.
**Why it happens:** Phase 5 cleanup kept it because the branding phase was supposed to handle it.
**How to avoid:** Delete `logo.svg` after adding `dwc-logo.png` as the replacement. Verify no config or source files reference `logo.svg` after deletion.
**Warning signs:** `logo.svg` still present in `static/img/` after branding is applied.

### Pitfall 4: Logo Not Working in Dark Mode
**What goes wrong:** A logo image with no background or a light-colored logo becomes invisible on dark backgrounds.
**Why it happens:** Not providing a `srcDark` alternative when the logo has poor contrast in dark mode.
**How to avoid:** The `dwc-logo.png` from the reference project has a dark rounded-square background with a white icon. This renders well on both light and dark backgrounds. No `srcDark` variant is needed. The reference project does not use `srcDark`.
**Warning signs:** Logo invisible or hard to see when toggling dark mode.

### Pitfall 5: Build Cache Showing Old Branding
**What goes wrong:** After changing favicon or logo, the old icons still appear in the browser.
**Why it happens:** Docusaurus build cache and browser cache retain old assets.
**How to avoid:** Run `npm run clear` before `npm run build` to purge the Docusaurus cache. Hard-refresh the browser (Cmd+Shift+R) during development.
**Warning signs:** Old dinosaur favicon still showing after deploying new branding.

## Code Examples

### Complete custom.css Color Replacement
```css
/* Source: /Users/beff/_workspace/bbj-dwc-tutorial/src/css/custom.css */
/* Replace the :root color variables (lines 8-17 of current custom.css) */
:root {
  --ifm-color-primary: #2563eb;
  --ifm-color-primary-dark: #1d4ed8;
  --ifm-color-primary-darker: #1e40af;
  --ifm-color-primary-darkest: #1e3a8a;
  --ifm-color-primary-light: #3b82f6;
  --ifm-color-primary-lighter: #60a5fa;
  --ifm-color-primary-lightest: #93c5fd;
  --ifm-code-font-size: 95%;
  --docusaurus-highlighted-code-line-bg: rgba(0, 0, 0, 0.1);
}

/* Replace the [data-theme='dark'] color variables (lines 21-30) */
[data-theme='dark'] {
  --ifm-color-primary: #60a5fa;
  --ifm-color-primary-dark: #3b82f6;
  --ifm-color-primary-darker: #2563eb;
  --ifm-color-primary-darkest: #1d4ed8;
  --ifm-color-primary-light: #93c5fd;
  --ifm-color-primary-lighter: #bfdbfe;
  --ifm-color-primary-lightest: #dbeafe;
  --docusaurus-highlighted-code-line-bg: rgba(0, 0, 0, 0.3);
}
```

### Updated Admonition Colors (align with new blue primary)
```css
/* alert--success border uses var(--ifm-color-primary) -> auto-updates to blue */
/* But background RGB values must be manually updated from green to blue */
.alert--success {
  --ifm-alert-background-color: rgba(37, 99, 235, 0.08);          /* was rgba(46, 133, 85, 0.08) */
  --ifm-alert-background-color-highlight: rgba(37, 99, 235, 0.15); /* was rgba(46, 133, 85, 0.15) */
  --ifm-alert-border-color: var(--ifm-color-primary);              /* no change needed */
  border-left-width: 5px;
  font-size: 1.05rem;
}

[data-theme='dark'] .alert--success {
  --ifm-alert-background-color: rgba(96, 165, 250, 0.08);          /* was rgba(37, 194, 160, 0.08) */
  --ifm-alert-background-color-highlight: rgba(96, 165, 250, 0.15); /* was rgba(37, 194, 160, 0.15) */
}
```

### Navbar Logo Addition in docusaurus.config.ts
```typescript
// Add logo object to themeConfig.navbar
navbar: {
  title: 'BBj AI Strategy',
  logo: {
    alt: 'BASIS Logo',
    src: 'img/dwc-logo.png',
  },
  items: [
    // existing items unchanged
  ],
},
```

### Favicon Path Update in docusaurus.config.ts
```typescript
// Change from 'img/favicon.ico' to 'img/favicon.png'
const config: Config = {
  title: 'BBj AI Strategy',
  tagline: 'Intelligent Code Assistance Across Four Generations of Business BASIC',
  favicon: 'img/favicon.png',
  // ...
};
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Docusaurus 2 CSS module approach | Infima CSS variable overrides | Docusaurus 2.x+ (stable) | Use `:root` and `[data-theme='dark']` selectors for all color customization |
| ICO-only favicons | Multi-format (PNG + ICO) | Ongoing best practice | PNG is standard for modern browsers; ICO kept as fallback |

**Deprecated/outdated:**
- None relevant. The CSS variable approach has been stable since Docusaurus 2.0 and continues in 3.x.

## Open Questions

1. **Admonition background color strategy**
   - What we know: The `.alert--success` backgrounds use hardcoded green RGB values that will clash with the new blue primary. The `.alert--info` backgrounds already use blue tones (#3678c2) that happen to align with the new palette.
   - What's unclear: Whether the admonition backgrounds should match the primary color (blue) or keep semantic colors (green for success/tip). The `.alert--success` border already uses `var(--ifm-color-primary)` which will become blue.
   - Recommendation: Update `.alert--success` backgrounds to blue to match the border (which uses `var(--ifm-color-primary)`). This creates a cohesive blue appearance. The "success" semantic was repurposed for TL;DR blocks in this project, so the green color has no semantic meaning here. This is a Claude's Discretion area per the CONTEXT.md.

2. **Whether to keep both favicon.ico and favicon.png**
   - What we know: The current project has `favicon.ico` (already identical to reference). The reference project has both `.ico` and `.png`.
   - What's unclear: Whether `.ico` should be kept alongside `.png` or removed.
   - Recommendation: Keep both. The config will point to `.png` (matching reference), but `.ico` serves as automatic fallback for older browsers that look for `favicon.ico` at the root.

## Sources

### Primary (HIGH confidence)
- Reference project `/Users/beff/_workspace/bbj-dwc-tutorial/` - Examined `docusaurus.config.ts`, `src/css/custom.css`, `static/img/` assets directly
- Current project `/Users/beff/_workspace/bbj-ai-strategy/` - Examined all corresponding files; verified MD5 hash match on favicon.ico
- Docusaurus official docs `https://docusaurus.io/docs/styling-layout` - CSS variable override patterns
- Docusaurus official docs `https://docusaurus.io/docs/api/themes/configuration` - Navbar logo configuration (src, srcDark, alt, width, height)
- Docusaurus official docs `https://docusaurus.io/docs/api/docusaurus-config` - Favicon and site config options

### Secondary (MEDIUM confidence)
- None needed. All findings verified against reference project files and official docs.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new libraries; all changes are config and CSS within Docusaurus 3.9.2
- Architecture: HIGH - Exact patterns copied from working reference implementation with identical Docusaurus setup
- Pitfalls: HIGH - Identified through direct file comparison between reference and current project; admonition color conflict confirmed via RGB value analysis

**Research date:** 2026-01-31
**Valid until:** 2026-03-01 (stable domain; Docusaurus CSS variable approach unchanged since 2.0)
