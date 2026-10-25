# UI / UX & SEO

Read for building UI, components, accessibility, and public-page SEO.

## Design direction

Generic output ("AI slop": purple gradients, default Inter, centered card grids, fade-in on everything) comes from building without a direction and without looking at the result. Fix both.

- **Brief before UI code.** For any new screen or visual redesign, write a short design brief and get it approved with the plan:
  - **Direction:** one sentence on the aesthetic (e.g. "editorial, high-contrast, generous whitespace"), plus 2–3 concrete references (sites or apps) and what to take from each.
  - **Type:** typeface pairing and scale (sizes, weights, line heights). Pick on purpose; don't default to the system or Inter.
  - **Color:** palette as tokens, with an accent used sparingly; light and dark.
  - **Layout:** grid, spacing scale, density, and the one element that breaks the grid on purpose.
  - **Motion:** what moves, why, durations and easings (see [motion-3d](motion-3d.md)).
  - **Signature moment:** the one thing that makes this screen memorable.

  In an existing product, the brief is mostly "follow the design system". Only list what's new.
- **Respect the existing brand and kit.** A brief extends the design system; it never forks it. If the brief needs a new primitive, add it to the kit.
- **Look, compare, iterate.** After building, screenshot the screen at 390px, ~768px, and desktop (dark mode, where it exists, in its own round), look at the images, and compare them against the brief: hierarchy, spacing rhythm, alignment, type, contrast, and the signature moment. Fix what's off, then re-shoot. Cap it at about 3 screenshots per round and 3 rounds; each image costs tokens. Write screenshots to `.output/screenshots/` (e.g. `npx playwright screenshot --viewport-size=390,844 <url> .output/screenshots/x-390.png`). Desktop and mobile apps: see [ui-testing-platforms](ui-testing-platforms.md).

## UX standards

- Clean, modern, business-grade UI — not a generic template look. Intentional spacing, hierarchy, contrast, and typography, per the design brief above.
- Responsive, **mobile-first**. Verify narrow mobile, tablet, and desktop widths.
- Handle every state: loading, empty, error, success, and offline/slow-network.
- **Right-align all numeric values** in tables, lists, and number fields (financial readability).
- Minimize input and clicks: auto-calculate derivable fields (e.g. fill `total` when `quantity` and `price` are set). Don't make users compute what the system can.
- Accessibility: semantic HTML first, then ARIA. Visible focus states, explicit labels, keyboard navigation for every interactive element, WCAG-friendly contrast.

## Styling

- Prefer utility-first CSS (Tailwind) with design tokens and small reusable primitives over large custom CSS files. (Angular Tailwind 4 setup: see [`angular-frontend.md`](angular-frontend.md).)
- Define and reuse primitives (buttons, inputs, cards, tables, badges, alerts, nav, modals, loading) once UI repeats. Avoid long repeated class strings — extract components.
- **Build UI from the project's component kit.** If a kit component doesn't fit, extend the kit — don't hand-roll markup or CSS in the feature. Fix alignment in the kit, not per page, and verify it by measurement (e.g. a Playwright check of icon centring and row heights), not by eye.
- Use CSS variables / theme tokens for brand colors, surfaces, radii, shadows, and spacing. No scattered one-off colors.
- Don't add a UI component library unless it materially improves delivery and passes dependency review. Native + utility CSS first.

## Modals / dialogs (every modal)

- **Full-viewport overlay** with no gaps and no horizontal scroll: `fixed inset-0` + a `z-index` above any sticky/fixed header, plus `overflow-y-auto` when taller than the screen. The modal must live at the component-tree root or be portalled to `body`.
- **Click outside to close:** backdrop click closes; `stopPropagation` on the inner panel.
- **ESC closes** (only the topmost when stacked).
- **Body scroll lock** while open (restore on close).
- Prefer a shared modal component / utility so every modal gets this behaviour for free.

## Admin tables — row click

- Clicking anywhere on a row opens **Edit** (or **View** if read-only). The whole row is clickable with `cursor-pointer` + hover feedback; keep action buttons for discoverability but `stopPropagation` on inline controls.

## Admin screens

- Generic CRUD / model-driven screens for plain data (articles, categories, lookup tables).
- Purpose-built screens for rare, high-stakes configuration (auth, roles/permissions, tenancy setup, editors). Never force these into a generic CRUD shape.
- Wizards for infrequent create/setup flows, not for editing.

## 2FA / OTP inputs

- Autofocus the code field the moment the step appears (`ViewChild` + `effect`/short timeout — not the HTML `autofocus` attribute alone).
- Auto-submit when the user types the Nth character for fixed-length codes (6 for TOTP, 8 for backup). Do **not** auto-submit variable-length recovery codes.
- Set `inputmode="numeric"` and `autocomplete="one-time-code"` for the mobile numeric pad + autofill.

## Mobile bottom sheets

- Every bottom sheet has a centered drag handle (a short rounded "grabber") at the very top, above the title, from a single shared handle component.

## Text correctness

- HTML entities must never reach users (`It&#039;s`, `&amp;`, `&nbsp;` are bugs). Decode at ingest/parse time so storage holds clean glyphs; add a defensive decode at display time for legacy data. Applies wherever a CMS or third-party API returns HTML-encoded strings.

## Verifying in the running app

- **Dev server: ask, don't assume.** If a check needs the dev server, prompt the user (structured question if the harness has one): you start it (in the background), or they run it and tell you when it's up. Never start a second one if the user already runs one.
- **Every UI-touching change is verified in a real browser before it's done, scoped to what you touched.** Run the API on the throwaway test DB (via an env override, never the dev DB) and the frontend, following the dev-server rule above. In headless Chromium/Playwright, drive only the changed component/feature and the flows that directly use it. For a shared kit component, that means one or two representative screens, not every consumer. No full-app sweeps per change: the full visual/UI suite runs once at the gate. Check console errors, failed requests, and layout at 390px and desktop, in light and dark. Unit tests, HTTP e2e and curl'ing SSR HTML don't count. Prefer committed visual-flow specs that screenshot each step into `.output/`, and look at the screenshots before reporting. Never print credentials, and stop every server you started.
- **Stale state before code bugs.** When the running app doesn't match your edit, first rule out stale state: dev-server hot reload, browser cache, SSR/translation caches, or an external cache (e.g. Redis) that survives restarts and deploys. Confirm via a build, the actually-served bundle, or a cold (uncached) run; ask the user for a hard refresh or restart. Never flush a shared cache (`FLUSHALL`/`FLUSHDB`) — delete only the specific keys, with approval.

## Internationalization

- **No hardcoded single-language UI strings** — not in templates, tooltips, placeholders, defaults (`'No data'`), or aria labels. Every user-visible string goes through the project's translation layer with a catalog key. Applies even when the app ships one language today.
- **Shared UI kits don't own i18n**: they take already-translated strings as inputs (`emptyMessage`, `placeholder`) instead of depending on one app's translation setup.
- **Scope catalogs by consumer**: strings used by one app/tenant stay in that app; only genuinely shared strings go in a shared catalog.
- Data-driven labels from the API stay as multilingual fields and are resolved per the current language.

## Favicon & branding

- **Never ship the framework default favicon.** Add a custom favicon (`favicon.ico` + apple-touch + android PNGs) from day one. Respect the project's existing brand; ask before imposing colors.

## SEO (public pages only)

- First classify the page: public vs private / internal / admin / staging / authenticated. Apply SEO only to **public** pages.
- Internal / admin / staging / authenticated pages default to `noindex,nofollow` and are excluded from sitemaps.
- Public pages: unique, descriptive `<title>` + meta description (no generic "Home"/"app"); one `h1`, logical heading order, alt text; Open Graph + Twitter/X cards where sharing matters; canonical URLs; clean human-readable URLs.
- Keep public content crawlable (SSR/static where practical). Optimize Core Web Vitals: small bundles, compressed images with explicit dimensions, lazy-load non-critical media, avoid layout shift.
- Use `schema.org` JSON-LD only when it matches visible content. Ensure `sitemap.xml` + `robots.txt` exist for public sites; exclude private routes.
