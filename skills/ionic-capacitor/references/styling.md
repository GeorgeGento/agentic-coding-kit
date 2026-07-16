# Ionic CSS Styling Reference

Complete guide to styling Ionic applications: utility classes, the color system, shadow parts, CSS custom properties, responsive breakpoints, and practical component customization recipes.

## Table of Contents
1. [CSS Utility Classes](#css-utility-classes)
2. [Ionic Color System](#ionic-color-system)
3. [CSS Shadow Parts](#css-shadow-parts)
4. [CSS Custom Properties](#css-custom-properties)
5. [Responsive Breakpoints](#responsive-breakpoints)
6. [Component Customization Recipes](#component-customization-recipes)

---

## CSS Utility Classes

Ionic provides utility classes for padding, margin, text alignment, flex layout, and visibility. These classes require CSS imports to work.

### Importing Utility CSS

You can import each utility stylesheet individually or use the bundle:

```tsx
/* Individual imports (granular control) */
import '@ionic/react/css/padding.css';
import '@ionic/react/css/margin.css';
import '@ionic/react/css/float-elements.css';
import '@ionic/react/css/text-alignment.css';
import '@ionic/react/css/text-transformation.css';
import '@ionic/react/css/flex-utils.css';
import '@ionic/react/css/display.css';

/* OR use the bundle (includes all of the above + core CSS) */
import '@ionic/react/css/ionic.bundle.css';
```

For Angular, import in `global.scss`:
```scss
@import '@ionic/angular/css/padding.css';
@import '@ionic/angular/css/ionic.bundle.css'; // or bundle
```

For Vue, import in `main.ts`:
```ts
import '@ionic/vue/css/padding.css';
import '@ionic/vue/css/ionic.bundle.css'; // or bundle
```

### Padding

Requires: `@ionic/react/css/padding.css`

| Class | Effect |
|-------|--------|
| `ion-padding` | Padding on all sides (16px default) |
| `ion-padding-top` | Padding on top only |
| `ion-padding-bottom` | Padding on bottom only |
| `ion-padding-start` | Padding on the start side (left in LTR, right in RTL) |
| `ion-padding-end` | Padding on the end side (right in LTR, left in RTL) |
| `ion-padding-horizontal` | Padding on start and end |
| `ion-padding-vertical` | Padding on top and bottom |
| `ion-no-padding` | Remove all padding |

```tsx
<IonContent className="ion-padding">
  <p className="ion-no-padding">Flush paragraph inside padded content.</p>
</IonContent>
```

### Margin

Requires: `@ionic/react/css/margin.css`

| Class | Effect |
|-------|--------|
| `ion-margin` | Margin on all sides (16px default) |
| `ion-margin-top` | Margin on top only |
| `ion-margin-bottom` | Margin on bottom only |
| `ion-margin-start` | Margin on start side |
| `ion-margin-end` | Margin on end side |
| `ion-margin-horizontal` | Margin on start and end |
| `ion-margin-vertical` | Margin on top and bottom |
| `ion-no-margin` | Remove all margin |

### Text Alignment and Wrapping

Requires: `@ionic/react/css/text-alignment.css` and `@ionic/react/css/text-transformation.css`

| Class | Effect |
|-------|--------|
| `ion-text-center` | Center-align text |
| `ion-text-start` | Align text to start (LTR-aware) |
| `ion-text-end` | Align text to end (LTR-aware) |
| `ion-text-justify` | Justify text |
| `ion-text-wrap` | Allow text to wrap |
| `ion-text-nowrap` | Prevent text wrapping |
| `ion-text-uppercase` | Transform text to uppercase |
| `ion-text-lowercase` | Transform text to lowercase |
| `ion-text-capitalize` | Capitalize first letter of each word |

```tsx
<IonLabel className="ion-text-center ion-text-uppercase">Centered Title</IonLabel>
<IonNote className="ion-text-wrap">This long note text will wrap to the next line.</IonNote>
```

### Float

Requires: `@ionic/react/css/float-elements.css`

| Class | Effect |
|-------|--------|
| `ion-float-left` | Float element to the left |
| `ion-float-right` | Float element to the right |

### Display and Responsive Visibility

Requires: `@ionic/react/css/display.css`

| Class | Effect |
|-------|--------|
| `ion-hide` | Hide element at all breakpoints |
| `ion-hide-sm-up` | Hide at >= 576px |
| `ion-hide-sm-down` | Hide at < 576px |
| `ion-hide-md-up` | Hide at >= 768px |
| `ion-hide-md-down` | Hide at < 768px |
| `ion-hide-lg-up` | Hide at >= 992px |
| `ion-hide-lg-down` | Hide at < 992px |
| `ion-hide-xl-up` | Hide at >= 1200px |
| `ion-hide-xl-down` | Hide at < 1200px |

```tsx
{/* Show mobile-only header, hide on tablet and up */}
<h2 className="ion-hide-md-up">Mobile View</h2>

{/* Show desktop sidebar, hide on mobile */}
<aside className="ion-hide-md-down">Desktop Sidebar</aside>
```

### Flex Utilities

Requires: `@ionic/react/css/flex-utils.css`

| Class | Effect |
|-------|--------|
| `ion-justify-content-start` | Justify content to start |
| `ion-justify-content-center` | Center content along main axis |
| `ion-justify-content-end` | Justify content to end |
| `ion-justify-content-between` | Space between items |
| `ion-justify-content-around` | Space around items |
| `ion-justify-content-evenly` | Space evenly between items |
| `ion-align-items-start` | Align items to start of cross axis |
| `ion-align-items-center` | Center items on cross axis |
| `ion-align-items-end` | Align items to end of cross axis |
| `ion-align-items-stretch` | Stretch items to fill cross axis |
| `ion-align-items-baseline` | Align items to text baseline |
| `ion-align-self-start` | Override alignment for single item |
| `ion-align-self-center` | Center a single item on cross axis |
| `ion-align-self-end` | Align a single item to end |
| `ion-wrap` | Allow flex items to wrap |
| `ion-nowrap` | Prevent flex items from wrapping |

```tsx
<IonRow className="ion-justify-content-center ion-align-items-center">
  <IonCol size="auto">
    <IonButton>Centered Button</IonButton>
  </IonCol>
</IonRow>
```

---

## Ionic Color System

### Built-in Colors

Ionic ships with 9 named colors. Every component that accepts a `color` prop uses this system.

| Name | Default Value | Purpose |
|------|---------------|---------|
| `primary` | `#3880ff` | Main brand color, CTAs, active states |
| `secondary` | `#3dc2ff` | Secondary actions, accents |
| `tertiary` | `#5260ff` | Tertiary accents, less prominent actions |
| `success` | `#2dd36f` | Positive outcomes, confirmations |
| `warning` | `#ffc409` | Warnings, caution states |
| `danger` | `#eb445a` | Errors, destructive actions, alerts |
| `light` | `#f4f5f8` | Light backgrounds, subtle borders |
| `medium` | `#92949c` | Secondary text, disabled states |
| `dark` | `#222428` | Dark backgrounds, strong text |

```tsx
<IonButton color="primary">Submit</IonButton>
<IonButton color="danger">Delete</IonButton>
<IonBadge color="success">Active</IonBadge>
<IonText color="medium"><p>Secondary info</p></IonText>
<IonItem color="light">Light background row</IonItem>
```

### Customizing Built-in Colors

Override any built-in color in `theme/variables.css`. You must set all 6 CSS variables for each color:

```css
:root {
  --ion-color-primary: #1a73e8;
  --ion-color-primary-rgb: 26, 115, 232;
  --ion-color-primary-contrast: #ffffff;
  --ion-color-primary-contrast-rgb: 255, 255, 255;
  --ion-color-primary-shade: #1765cc;
  --ion-color-primary-tint: #3181ea;
}
```

### Creating Custom Colors

Define entirely new named colors that work with the `color` prop on any Ionic component:

```css
/* Step 1: Define the color variables */
:root {
  --ion-color-brand: #8a2be2;
  --ion-color-brand-rgb: 138, 43, 226;
  --ion-color-brand-contrast: #ffffff;
  --ion-color-brand-contrast-rgb: 255, 255, 255;
  --ion-color-brand-shade: #7926c7;
  --ion-color-brand-tint: #9640e5;
}

/* Step 2: Register the color class (required for the color prop to work) */
.ion-color-brand {
  --ion-color-base: var(--ion-color-brand);
  --ion-color-base-rgb: var(--ion-color-brand-rgb);
  --ion-color-contrast: var(--ion-color-brand-contrast);
  --ion-color-contrast-rgb: var(--ion-color-brand-contrast-rgb);
  --ion-color-shade: var(--ion-color-brand-shade);
  --ion-color-tint: var(--ion-color-brand-tint);
}
```

Both steps are required. The `:root` variables define the values, and the `.ion-color-brand` class maps them to Ionic's internal color system. Then use it like any built-in color:

```tsx
<IonButton color="brand">Brand Button</IonButton>
<IonChip color="brand">Brand Chip</IonChip>
```

Use the [Ionic Color Generator](https://ionicframework.com/docs/theming/color-generator) to calculate correct `-shade`, `-tint`, `-rgb`, and `-contrast` values from any hex color.

---

## CSS Shadow Parts

Ionic components use Shadow DOM to encapsulate their internal markup. You cannot style internal elements with normal CSS selectors. Instead, use the `::part()` pseudo-element to target exposed shadow parts.

### Syntax

```css
/* Target a shadow part */
ion-component::part(part-name) {
  /* your styles */
}

/* With a class scope */
.my-custom-class ion-button::part(native) {
  border-radius: 20px;
}
```

### Common Shadow Parts by Component

**ion-button**
```css
ion-button::part(native) {
  /* The actual <button> element inside the shadow DOM */
  border-radius: 20px;
  font-weight: 700;
  text-transform: none;
  letter-spacing: 0;
}
```

**ion-input**
```css
ion-input::part(native) {
  /* The underlying <input> element */
  font-size: 16px;
  caret-color: var(--ion-color-primary);
}
```

**ion-item**
```css
ion-item::part(native) {
  /* The item wrapper (background, padding) */
  background: transparent;
  border-bottom: 1px solid #e0e0e0;
}
ion-item::part(detail-icon) {
  /* The chevron icon on items with detail=true */
  color: var(--ion-color-primary);
}
```

**ion-modal**
```css
ion-modal::part(backdrop) {
  /* The semi-transparent overlay behind the modal */
  background: rgba(0, 0, 0, 0.6);
}
ion-modal::part(content) {
  /* The modal content container */
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}
ion-modal::part(handle) {
  /* The drag handle on sheet modals */
  background: var(--ion-color-medium);
  width: 40px;
}
```

**ion-select**
```css
ion-select::part(text) {
  /* The displayed selected value text */
  font-weight: 600;
  color: var(--ion-color-dark);
}
ion-select::part(placeholder) {
  /* The placeholder text when nothing is selected */
  color: var(--ion-color-medium);
  font-style: italic;
}
ion-select::part(icon) {
  /* The dropdown arrow icon */
  color: var(--ion-color-primary);
  opacity: 1;
}
```

**ion-searchbar**
```css
ion-searchbar::part(icon) {
  /* The search icon */
  color: var(--ion-color-primary);
}
ion-searchbar::part(clear-icon) {
  /* The clear/X icon */
  color: var(--ion-color-medium);
}
```

**ion-toggle**
```css
ion-toggle::part(track) {
  /* The toggle track/groove */
  background: #ccc;
}
ion-toggle::part(handle) {
  /* The toggle handle/knob */
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
```

### How to Find Shadow Parts

1. **Browser DevTools**: Inspect the component, expand the `#shadow-root`, and look for `part="..."` attributes on internal elements.
2. **Ionic docs**: Each component's documentation page lists its CSS Shadow Parts in a table at the bottom.
3. **Source code**: Search the Ionic GitHub repository for `part=` in the component's `.tsx` file.

---

## CSS Custom Properties

Most Ionic components expose CSS custom properties (CSS variables) that let you override internal styles without using `::part()`. Set these on the component selector or via a class.

### ion-content

```css
ion-content {
  --background: #f5f5f5;
  --color: #333333;
  --padding-top: 16px;
  --padding-bottom: 16px;
  --padding-start: 16px;
  --padding-end: 16px;
  --keyboard-offset: 0px;
  --offset-top: 0px;
  --offset-bottom: 0px;
}
```

### ion-item

```css
ion-item {
  --background: #ffffff;
  --background-activated: rgba(0, 0, 0, 0.05);
  --background-focused: rgba(0, 0, 0, 0.08);
  --background-hover: rgba(0, 0, 0, 0.03);
  --border-color: #e0e0e0;
  --border-width: 0 0 1px 0;
  --border-style: solid;
  --border-radius: 0;
  --color: #333333;
  --padding-start: 16px;
  --padding-end: 16px;
  --inner-padding-end: 8px;
  --inner-border-width: 0;
  --min-height: 48px;
  --transition: background-color 0.15s;
  --ripple-color: var(--ion-color-primary);
}
```

### ion-button

```css
ion-button {
  --background: var(--ion-color-primary);
  --background-activated: var(--ion-color-primary-shade);
  --background-hover: var(--ion-color-primary-tint);
  --background-focused: var(--ion-color-primary-shade);
  --color: var(--ion-color-primary-contrast);
  --border-radius: 8px;
  --border-width: 0;
  --border-color: transparent;
  --box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  --padding-start: 24px;
  --padding-end: 24px;
  --padding-top: 12px;
  --padding-bottom: 12px;
  --ripple-color: rgba(255, 255, 255, 0.3);
}
```

### ion-toolbar

```css
ion-toolbar {
  --background: #ffffff;
  --color: #000000;
  --border-color: #e0e0e0;
  --border-width: 0 0 1px 0;
  --min-height: 56px;
  --padding-start: 8px;
  --padding-end: 8px;
  --padding-top: 4px;
  --padding-bottom: 4px;
}
```

### ion-card

```css
ion-card {
  --background: #ffffff;
  --color: #333333;
  border-radius: 12px;        /* Not a CSS variable — use regular property */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

### ion-modal

```css
ion-modal {
  --width: 90%;
  --max-width: 500px;
  --height: auto;
  --max-height: 80vh;
  --border-radius: 16px;
  --backdrop-opacity: 0.5;
  --background: #ffffff;
  --box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}

/* Sheet modal specific */
ion-modal.sheet-modal {
  --border-radius: 16px 16px 0 0;
  --height: auto;
}
```

### ion-list

```css
ion-list {
  --ion-item-background: #ffffff;
  background: transparent;
}
```

### ion-input

```css
ion-input {
  --background: #f5f5f5;
  --color: #333333;
  --placeholder-color: #999999;
  --placeholder-opacity: 1;
  --padding-start: 12px;
  --padding-end: 12px;
  --highlight-color-focused: var(--ion-color-primary);
  --highlight-color-valid: var(--ion-color-success);
  --highlight-color-invalid: var(--ion-color-danger);
  --border-radius: 8px;
}
```

### Global Theming Variables

Set these at `:root` level to affect the entire application:

```css
:root {
  --ion-background-color: #ffffff;
  --ion-background-color-rgb: 255, 255, 255;
  --ion-text-color: #000000;
  --ion-text-color-rgb: 0, 0, 0;
  --ion-font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --ion-toolbar-background: #ffffff;
  --ion-toolbar-color: #000000;
  --ion-tab-bar-background: #ffffff;
  --ion-tab-bar-color: var(--ion-color-medium);
  --ion-tab-bar-color-selected: var(--ion-color-primary);
  --ion-card-background: #ffffff;
  --ion-item-background: #ffffff;
}
```

---

## Responsive Breakpoints

### Breakpoint Values

| Name | Min Width | Typical Devices |
|------|-----------|-----------------|
| `xs` | `0px` | Small phones (portrait) |
| `sm` | `576px` | Large phones (landscape) |
| `md` | `768px` | Tablets (portrait) |
| `lg` | `992px` | Tablets (landscape), small laptops |
| `xl` | `1200px` | Desktops, large screens |

### IonGrid Fixed Container

Use the `fixed` prop on `IonGrid` to set a max-width that matches the current breakpoint, centering the grid on large screens:

```tsx
{/* Content stays centered, won't stretch across ultra-wide screens */}
<IonGrid fixed>
  <IonRow>
    <IonCol>Centered content with max-width</IonCol>
  </IonRow>
</IonGrid>
```

Fixed grid max-widths per breakpoint: `sm: 540px`, `md: 720px`, `lg: 960px`, `xl: 1140px`.

### Responsive Column Sizing

`IonCol` accepts responsive `size` props. The grid uses a 12-column system:

| Prop | Breakpoint | Example |
|------|------------|---------|
| `size` | All (default/xs) | `size="12"` = full width |
| `sizeSm` | >= 576px | `sizeSm="6"` = half width on sm+ |
| `sizeMd` | >= 768px | `sizeMd="4"` = third width on md+ |
| `sizeLg` | >= 992px | `sizeLg="3"` = quarter width on lg+ |
| `sizeXl` | >= 1200px | `sizeXl="2"` = sixth width on xl+ |

```tsx
{/* Responsive card grid: 1 col mobile, 2 tablet, 3 desktop, 4 large desktop */}
<IonGrid>
  <IonRow>
    {items.map((item) => (
      <IonCol size="12" sizeSm="6" sizeMd="4" sizeXl="3" key={item.id}>
        <IonCard>
          <IonCardHeader>
            <IonCardTitle>{item.title}</IonCardTitle>
          </IonCardHeader>
        </IonCard>
      </IonCol>
    ))}
  </IonRow>
</IonGrid>
```

### Column Offset, Push, and Pull

Use `offset` to add empty space before a column. Use `push` and `pull` to visually reorder columns without changing DOM order:

```tsx
{/* Centered column (3 cols offset + 6 cols content + 3 cols remaining) */}
<IonRow>
  <IonCol size="6" offset="3">Centered content</IonCol>
</IonRow>

{/* Responsive offset */}
<IonRow>
  <IonCol size="12" sizeMd="8" offsetMd="2">
    Centered on desktop, full width on mobile
  </IonCol>
</IonRow>

{/* Reorder columns visually: image right on desktop, top on mobile */}
<IonRow>
  <IonCol size="12" sizeMd="6" pushMd="6">Image content</IonCol>
  <IonCol size="12" sizeMd="6" pullMd="6">Text content</IonCol>
</IonRow>
```

### Using Breakpoints in Custom CSS

Ionic does not export its breakpoints as CSS variables, but the values are standard. Use them in your own media queries:

```css
/* Match Ionic's breakpoint system */
@media (min-width: 576px)  { /* sm */ }
@media (min-width: 768px)  { /* md */ }
@media (min-width: 992px)  { /* lg */ }
@media (min-width: 1200px) { /* xl */ }

/* Example: larger font on tablets and up */
@media (min-width: 768px) {
  .page-title {
    font-size: 2rem;
  }
}
```

---

## Component Customization Recipes

### Recipe 1: Custom-Styled Card with Shadow Parts

A card with custom border radius, hover effects, and styled sub-components:

```css
/* styles/CustomCard.css */
.custom-card {
  --background: #ffffff;
  --color: #1a1a1a;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  overflow: hidden;
  margin: 8px;
}

.custom-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.custom-card ion-card-header {
  padding: 16px 20px 8px;
}

.custom-card ion-card-title {
  font-size: 1.125rem;
  font-weight: 700;
}

.custom-card ion-card-subtitle {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--ion-color-medium);
}

.custom-card ion-card-content {
  padding: 0 20px 20px;
  font-size: 0.95rem;
  line-height: 1.5;
}

.custom-card ion-button::part(native) {
  text-transform: none;
  font-weight: 600;
  letter-spacing: 0;
}
```

```tsx
<IonCard className="custom-card">
  <IonImg src="/assets/cover.jpg" alt="Cover image" />
  <IonCardHeader>
    <IonCardSubtitle>Tutorial</IonCardSubtitle>
    <IonCardTitle>Getting Started with Ionic</IonCardTitle>
  </IonCardHeader>
  <IonCardContent>
    Learn how to build beautiful cross-platform apps.
  </IonCardContent>
  <div className="ion-padding-horizontal ion-padding-bottom">
    <IonButton fill="clear" size="small">Read More</IonButton>
  </div>
</IonCard>
```

### Recipe 2: Themed Form Inputs

Consistent input styling across your app:

```css
/* styles/FormTheme.css */
.themed-input {
  --background: #f8f9fa;
  --border-radius: 12px;
  --padding-start: 16px;
  --padding-end: 16px;
  --highlight-color-focused: var(--ion-color-primary);
  --highlight-color-valid: var(--ion-color-success);
  --highlight-color-invalid: var(--ion-color-danger);
  --placeholder-color: #adb5bd;
  --placeholder-opacity: 1;
  margin-bottom: 12px;
}

.themed-input::part(native) {
  font-size: 16px; /* Prevents iOS zoom on focus */
}

.themed-select {
  --border-radius: 12px;
  --padding-start: 16px;
}

.themed-select::part(text) {
  font-weight: 500;
}

.themed-select::part(icon) {
  color: var(--ion-color-primary);
  opacity: 1;
}

/* Error state */
.themed-input.ion-invalid.ion-touched {
  --background: #fff5f5;
}

.form-submit-btn {
  --border-radius: 12px;
  --box-shadow: 0 4px 14px rgba(var(--ion-color-primary-rgb), 0.3);
  --padding-top: 14px;
  --padding-bottom: 14px;
  font-weight: 600;
  margin-top: 24px;
}
```

```tsx
<IonList lines="none">
  <IonItem>
    <IonInput
      className="themed-input"
      label="Full Name"
      labelPlacement="stacked"
      fill="outline"
      placeholder="John Doe"
    />
  </IonItem>
  <IonItem>
    <IonInput
      className="themed-input"
      label="Email"
      labelPlacement="stacked"
      fill="outline"
      type="email"
      placeholder="john@example.com"
      helperText="We'll never share your email"
      errorText="Please enter a valid email"
    />
  </IonItem>
  <IonItem>
    <IonSelect
      className="themed-select"
      label="Role"
      labelPlacement="stacked"
      fill="outline"
      interface="action-sheet"
    >
      <IonSelectOption value="dev">Developer</IonSelectOption>
      <IonSelectOption value="design">Designer</IonSelectOption>
    </IonSelect>
  </IonItem>
</IonList>
<IonButton expand="block" className="form-submit-btn">
  Create Account
</IonButton>
```

### Recipe 3: Custom Modal Appearance

A polished modal with rounded corners and custom backdrop:

```css
/* styles/CustomModal.css */
.custom-modal {
  --width: 92%;
  --max-width: 480px;
  --height: auto;
  --max-height: 85vh;
  --border-radius: 20px;
  --backdrop-opacity: 0.6;
  --box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.custom-modal::part(backdrop) {
  background: #1a1a2e;
}

.custom-modal::part(content) {
  border-radius: 20px;
}

.custom-modal::part(handle) {
  background: #dee2e6;
  width: 36px;
  height: 4px;
  margin-top: 12px;
}

.custom-modal ion-toolbar {
  --background: transparent;
  --border-width: 0;
}

.custom-modal ion-content {
  --padding-start: 24px;
  --padding-end: 24px;
  --padding-bottom: 24px;
}
```

```tsx
<IonModal
  isOpen={isOpen}
  onDidDismiss={() => setIsOpen(false)}
  className="custom-modal"
  breakpoints={[0, 0.5, 0.85]}
  initialBreakpoint={0.85}
  handle={true}
>
  <IonHeader>
    <IonToolbar>
      <IonTitle>Details</IonTitle>
      <IonButtons slot="end">
        <IonButton onClick={() => setIsOpen(false)}>
          <IonIcon icon={closeOutline} slot="icon-only" />
        </IonButton>
      </IonButtons>
    </IonToolbar>
  </IonHeader>
  <IonContent>
    {/* Modal body content */}
  </IonContent>
</IonModal>
```

### Recipe 4: Platform-Specific Styling

Ionic adds `.ios` or `.md` (Material Design) to the root `ion-app` element. Use these to write platform-targeted styles:

```css
/* iOS-specific styles */
.ios ion-toolbar {
  --min-height: 44px;
}

.ios .hero-title {
  font-weight: 700;
  font-size: 2rem;
  letter-spacing: -0.5px;
}

.ios ion-button::part(native) {
  border-radius: 10px;
}

/* Material Design / Android-specific styles */
.md ion-toolbar {
  --min-height: 56px;
}

.md .hero-title {
  font-weight: 500;
  font-size: 1.75rem;
  letter-spacing: 0;
}

.md ion-button::part(native) {
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Platform-specific card styling */
.ios ion-card {
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
}

.md ion-card {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08);
}

/* Different list styles per platform */
.ios ion-list {
  margin: 16px;
  border-radius: 12px;
  overflow: hidden;
}

.md ion-list {
  margin: 8px 0;
  border-radius: 0;
}
```

You can also check the platform at runtime when you need conditional logic rather than just CSS:

```tsx
import { isPlatform } from '@ionic/react';

if (isPlatform('ios')) {
  // iOS-specific logic
}
if (isPlatform('android')) {
  // Android-specific logic
}
```
