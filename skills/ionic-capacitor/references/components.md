# Complete Ionic UI Component Reference

All 94 Ionic UI components organized by category. Use this as a lookup when building interfaces. Every component name maps directly to both its HTML tag (`ion-button`) and framework wrapper (`IonButton`).

## Table of Contents
1. [Layout & Content](#layout--content)
2. [Navigation](#navigation)
3. [Tabs](#tabs)
4. [Menu](#menu)
5. [Toolbar](#toolbar)
6. [Buttons & Actions](#buttons--actions)
7. [Cards](#cards)
8. [Lists & Items](#lists--items)
9. [Forms & Inputs](#forms--inputs)
10. [Data Display](#data-display)
11. [Overlays](#overlays)
12. [Progress & Loading](#progress--loading)
13. [Grid](#grid)
14. [Content Organization](#content-organization)
15. [Scroll & Refresh](#scroll--refresh)
16. [Date & Time](#date--time)
17. [Media](#media)
18. [Typography](#typography)

---

## Layout & Content

| Component | Purpose |
|-----------|---------|
| `ion-app` | Root app container — wraps the entire application |
| `ion-content` | Main scrollable content area. Use `fullscreen` for safe area support |

## Navigation

| Component | Purpose |
|-----------|---------|
| `ion-nav` | Stack-based navigation container |
| `ion-nav-link` | Link that pushes/pops pages on a nav stack |
| `ion-router` | Client-side route management (vanilla JS) |
| `ion-router-outlet` | Renders matched route components with transitions |
| `ion-route` | Individual route definition |
| `ion-route-redirect` | Redirects one route to another |
| `ion-router-link` | Anchor-style link for router navigation |

## Tabs

| Component | Purpose |
|-----------|---------|
| `ion-tabs` | Container for tabbed navigation layout |
| `ion-tab` | Individual tab content container |
| `ion-tab-bar` | Bar containing tab buttons (slot="bottom" or "top") |
| `ion-tab-button` | Individual tab button with icon and label |

## Menu

| Component | Purpose |
|-----------|---------|
| `ion-menu` | Side drawer menu. Set `contentId` to target main content |
| `ion-menu-button` | Hamburger button that toggles the menu |
| `ion-menu-toggle` | Wraps items to auto-close menu on click |
| `ion-split-pane` | Shows menu permanently on wide screens, toggleable on mobile |

## Toolbar

| Component | Purpose |
|-----------|---------|
| `ion-header` | Container for top toolbar. Use `collapse="condense"` for iOS large titles |
| `ion-footer` | Container for bottom toolbar |
| `ion-toolbar` | Horizontal bar for titles, buttons, and search |
| `ion-title` | Page title. Use `size="large"` inside collapse headers |
| `ion-buttons` | Container for toolbar buttons. Use `slot="start"/"end"/"primary"/"secondary"` |
| `ion-back-button` | Native back button. Always set `defaultHref` |

## Buttons & Actions

| Component | Purpose |
|-----------|---------|
| `ion-button` | Primary interactive button. Props: `fill` (solid/outline/clear), `expand` (block/full), `size`, `color` |
| `ion-fab` | Floating action button container. Position with `vertical` and `horizontal` |
| `ion-fab-button` | Circular floating button |
| `ion-fab-list` | List of actions that expand from a FAB |
| `ion-ripple-effect` | Material Design touch ripple effect |

## Cards

| Component | Purpose |
|-----------|---------|
| `ion-card` | Content container card with elevation |
| `ion-card-header` | Top section of card (contains title/subtitle) |
| `ion-card-title` | Card heading text |
| `ion-card-subtitle` | Card subheading text |
| `ion-card-content` | Main card content area |

## Lists & Items

| Component | Purpose |
|-----------|---------|
| `ion-list` | Container for items. Use `inset` for rounded card-style list |
| `ion-list-header` | Section header within a list |
| `ion-item` | Row container for text, icons, inputs, avatars. Props: `button`, `detail`, `lines` |
| `ion-item-divider` | Visual separator between list sections |
| `ion-item-group` | Groups items under a divider |
| `ion-item-sliding` | Wraps item to enable swipe actions |
| `ion-item-options` | Container for slide-out options. Use `side="start"` or `side="end"` |
| `ion-item-option` | Individual swipe action button |
| `ion-label` | Text label inside items. Supports `<h2>`, `<h3>`, `<p>` for multi-line |
| `ion-note` | Secondary/meta text (timestamps, counts) |

## Forms & Inputs

| Component | Purpose |
|-----------|---------|
| `ion-input` | Text input. Props: `type`, `label`, `labelPlacement`, `fill`, `helperText`, `errorText` |
| `ion-input-password-toggle` | Show/hide toggle for password inputs |
| `ion-input-otp` | One-time password input with individual character boxes |
| `ion-textarea` | Multi-line text input. Use `autoGrow` for dynamic height |
| `ion-checkbox` | Binary checkbox control |
| `ion-radio` | Single radio option (use inside `ion-radio-group`) |
| `ion-radio-group` | Groups radio buttons for single selection |
| `ion-toggle` | On/off switch toggle |
| `ion-select` | Dropdown/picker selection. Props: `interface` (action-sheet/alert/popover) |
| `ion-select-option` | Individual option within a select |
| `ion-range` | Slider for value selection. Props: `min`, `max`, `step`, `pin` |
| `ion-searchbar` | Search input with clear button and cancel |

## Data Display

| Component | Purpose |
|-----------|---------|
| `ion-badge` | Small count/status indicator. Use `color` for styling |
| `ion-chip` | Compact tag/filter display with optional close button |
| `ion-breadcrumb` | Individual breadcrumb link |
| `ion-breadcrumbs` | Breadcrumb navigation trail |

## Overlays

| Component | Purpose |
|-----------|---------|
| `ion-modal` | Full or partial overlay. Use `breakpoints` for sheet-style modals |
| `ion-backdrop` | Semi-transparent background behind overlays |
| `ion-popover` | Small contextual overlay anchored to trigger element |
| `ion-alert` | Dialog for confirmations and simple inputs |
| `ion-action-sheet` | Bottom sheet with list of actions |
| `ion-toast` | Non-blocking notification message |
| `ion-loading` | Full-screen loading overlay with spinner |

## Progress & Loading

| Component | Purpose |
|-----------|---------|
| `ion-progress-bar` | Horizontal progress indicator. Props: `value` (0-1), `type` (determinate/indeterminate) |
| `ion-skeleton-text` | Placeholder animation while content loads. Use `animated` prop |
| `ion-spinner` | Animated loading indicator. Styles: bubbles, circles, crescent, dots, lines |

## Grid

| Component | Purpose |
|-----------|---------|
| `ion-grid` | 12-column responsive grid container. Use `fixed` for max-width centering |
| `ion-row` | Horizontal row of columns |
| `ion-col` | Column within a row. Size props: `size`, `sizeSm`, `sizeMd`, `sizeLg`, `sizeXl` (1-12) |

**When to use Grid vs List:**
- **IonGrid**: Photo galleries, card grids, dashboards, multi-column layouts, stat displays
- **IonList**: Single-column scrollable lists of items, settings pages, data rows with actions

## Content Organization

| Component | Purpose |
|-----------|---------|
| `ion-accordion` | Collapsible content section |
| `ion-accordion-group` | Container for accordions. Use `multiple` to allow multiple open |
| `ion-segment` | Horizontal button group for filtering/switching views |
| `ion-segment-button` | Individual segment option |
| `ion-segment-content` | Content area tied to a segment button |
| `ion-segment-view` | Manages segment content display |

## Scroll & Refresh

| Component | Purpose |
|-----------|---------|
| `ion-refresher` | Pull-to-refresh container. Use `slot="fixed"` |
| `ion-refresher-content` | Visual indicator during refresh |
| `ion-infinite-scroll` | Triggers loading when scrolled near bottom |
| `ion-infinite-scroll-content` | Loading indicator for infinite scroll |
| `ion-reorder` | Drag handle for reorderable items |
| `ion-reorder-group` | Container enabling drag-to-reorder |

## Date & Time

| Component | Purpose |
|-----------|---------|
| `ion-datetime` | Full date/time picker with calendar view |
| `ion-datetime-button` | Compact button that opens a datetime picker |
| `ion-picker` | Custom column-based picker (like iOS picker wheel) |
| `ion-picker-column` | Column in a picker |
| `ion-picker-column-option` | Individual option in a picker column |

## Media

| Component | Purpose |
|-----------|---------|
| `ion-avatar` | Small circular image container (profile pics) |
| `ion-icon` | Ionicons icon. Import individually: `import { heart } from 'ionicons/icons'` |
| `ion-img` | Lazy-loading image component (better than `<img>` for performance) |
| `ion-thumbnail` | Small rectangular image container for list items |

## Typography

| Component | Purpose |
|-----------|---------|
| `ion-text` | Wrapper for applying Ionic color to text |
