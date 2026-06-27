# UI / UX & SEO

Read for building UI, components, accessibility, and public-page SEO.

## UX standards

- Clean, modern, business-grade UI — not a generic template look. Intentional spacing, hierarchy, contrast, and typography.
- Responsive, **mobile-first**. Verify narrow mobile, tablet, and desktop widths.
- Handle every state: loading, empty, error, success, and offline/slow-network.
- **Right-align all numeric values** in tables, lists, and number fields (financial readability).
- Minimize input and clicks: auto-calculate derivable fields (e.g. fill `total` when `quantity` and `price` are set). Don't make users compute what the system can.
- Accessibility: semantic HTML first, then ARIA. Visible focus states, explicit labels, keyboard navigation for every interactive element, WCAG-friendly contrast.

## Styling

- Prefer utility-first CSS (Tailwind) with design tokens and small reusable primitives over large custom CSS files. (Angular Tailwind 4 setup: see [`angular-frontend.md`](angular-frontend.md).)
- Define and reuse primitives (buttons, inputs, cards, tables, badges, alerts, nav, modals, loading) once UI repeats. Avoid long repeated class strings — extract components.
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

## 2FA / OTP inputs

- Autofocus the code field the moment the step appears (`ViewChild` + `effect`/short timeout — not the HTML `autofocus` attribute alone).
- Auto-submit when the user types the Nth character for fixed-length codes (6 for TOTP, 8 for backup). Do **not** auto-submit variable-length recovery codes.
- Set `inputmode="numeric"` and `autocomplete="one-time-code"` for the mobile numeric pad + autofill.

## Mobile bottom sheets

- Every bottom sheet has a centered drag handle (a short rounded "grabber") at the very top, above the title, from a single shared handle component.

## Text correctness

- HTML entities must never reach users (`It&#039;s`, `&amp;`, `&nbsp;` are bugs). Decode at ingest/parse time so storage holds clean glyphs; add a defensive decode at display time for legacy data. Applies wherever a CMS or third-party API returns HTML-encoded strings.

## Favicon & branding

- **Never ship the framework default favicon.** Add a custom favicon (`favicon.ico` + apple-touch + android PNGs) from day one. Respect the project's existing brand; ask before imposing colors.

## SEO (public pages only)

- First classify the page: public vs private / internal / admin / staging / authenticated. Apply SEO only to **public** pages.
- Internal / admin / staging / authenticated pages default to `noindex,nofollow` and are excluded from sitemaps.
- Public pages: unique, descriptive `<title>` + meta description (no generic "Home"/"app"); one `h1`, logical heading order, alt text; Open Graph + Twitter/X cards where sharing matters; canonical URLs; clean human-readable URLs.
- Keep public content crawlable (SSR/static where practical). Optimize Core Web Vitals: small bundles, compressed images with explicit dimensions, lazy-load non-critical media, avoid layout shift.
- Use `schema.org` JSON-LD only when it matches visible content. Ensure `sitemap.xml` + `robots.txt` exist for public sites; exclude private routes.
