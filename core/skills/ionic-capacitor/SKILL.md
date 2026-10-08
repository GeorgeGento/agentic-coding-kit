---
name: ionic-capacitor
description: >
  MUST USE for any task involving Ionic Framework or Capacitor. REQUIRED whenever the user's code or
  project involves: ion-* components (ion-button, ion-content, ion-tabs, ion-modal, ion-grid, ion-page),
  @ionic/react, @ionic/angular, @ionic/vue, @capacitor/core, Capacitor plugins (Camera, Preferences,
  Geolocation, Push Notifications, Filesystem, Haptics, StatusBar, SplashScreen), capacitor.config.ts,
  the Ionic CLI, IonPage wrappers, Ionic lifecycle hooks (useIonViewWillEnter, onIonViewWillEnter),
  Ionic theming (ion-palette-dark, CSS custom properties), IonRouterOutlet, sheet modals with breakpoints,
  or cross-platform mobile apps deployed to iOS/Android via Capacitor. Trigger even if the user doesn't
  say "Ionic" but references ion-* components, Capacitor APIs, or hybrid mobile patterns. Contains
  critical patterns Claude does not know from training: correct dark mode classes, lifecycle hooks
  vs useEffect/onMounted, IonGrid vs IonList for galleries, standalone Angular imports, and more.
---

# Ionic Capacitor Development Skill

Build performant, native-feeling mobile apps using Ionic UI components and Capacitor's native runtime. This skill covers the full stack: project setup, component patterns, state management, native APIs, theming, and deployment across React, Angular, and Vue.

## Quick Decision: Which Framework?

| Factor | React | Angular | Vue |
|--------|-------|---------|-----|
| Learning curve | Moderate | Steeper | Gentle |
| Ecosystem | Largest | Enterprise-strong | Growing fast |
| State management | Zustand/TanStack Query | Signals + Services | Pinia |
| Best for | Startups, flexibility | Enterprise, structure | Simplicity, speed |
| Ionic integration | `@ionic/react` | `@ionic/angular` | `@ionic/vue` |

All three are first-class citizens in Ionic. Pick based on team familiarity. Read `references/react.md`, `references/angular.md`, or `references/vue.md` for framework-specific deep dives.

## Project Setup

### Create a New Project

```bash
# Install Ionic CLI
npm install -g @ionic/cli

# Create project (pick your framework)
ionic start myApp tabs --type=react      # React
ionic start myApp tabs --type=angular    # Angular
ionic start myApp tabs --type=vue        # Vue

# Templates: blank, tabs, sidemenu, list, conference
```

### Project Structure (Universal)

```
myApp/
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/            # Route-level page components
│   ├── services/         # API calls, business logic
│   ├── hooks/            # Custom hooks (React/Vue)
│   ├── store/            # State management
│   ├── theme/
│   │   └── variables.css # Ionic CSS custom properties
│   ├── assets/           # Static files (images, fonts)
│   └── App.tsx           # Root component
├── public/
├── capacitor.config.ts   # Capacitor configuration
├── ionic.config.json     # Ionic CLI configuration
└── package.json
```

### Capacitor Configuration

```typescript
// capacitor.config.ts
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.yourcompany.appname',    // Reverse domain notation
  appName: 'Your App Name',
  webDir: 'dist',                       // Build output directory
  server: {
    // For development live reload (remove in production):
    // url: 'http://192.168.1.x:8100',
    // cleartext: true,
    androidScheme: 'https',             // Always use https
  },
  ios: {
    contentInset: 'automatic',          // Safe area handling
    preferredContentMode: 'mobile',
  },
  android: {
    allowMixedContent: false,           // Security: keep false in prod
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: true,
      androidScaleType: 'CENTER_CROP',
      splashFullScreen: true,
      splashImmersive: true,
    },
    StatusBar: {
      style: 'dark',                    // 'dark' or 'light'
    },
  },
};

export default config;
```

### Add Native Platforms

```bash
# Build web assets first
ionic build

# Add platforms
ionic cap add ios
ionic cap add android

# Sync web assets to native projects
ionic cap sync

# Open native IDEs
ionic cap open ios      # Opens Xcode
ionic cap open android  # Opens Android Studio
```

## Core Component Patterns

### Page Structure — The Foundation

Every page follows this pattern. Never skip it — Ionic's scroll behavior, safe areas, and transitions depend on this structure.

```tsx
<IonPage>
  <IonHeader>
    <IonToolbar>
      <IonTitle>Page Title</IonTitle>
    </IonToolbar>
  </IonHeader>

  <IonContent fullscreen>
    {/* iOS large title support */}
    <IonHeader collapse="condense">
      <IonToolbar>
        <IonTitle size="large">Page Title</IonTitle>
      </IonToolbar>
    </IonHeader>

    {/* Your page content */}
  </IonContent>
</IonPage>
```

The `collapse="condense"` header creates the native iOS large-title-to-small-title scroll effect. Always include it for iOS native feel.

### Navigation Patterns

**Tabs** — Best for apps with 3-5 top-level sections:
```tsx
<IonTabs>
  <IonRouterOutlet>
    <Route exact path="/tab1" component={Tab1} />
    <Route exact path="/tab2" component={Tab2} />
    <Route exact path="/tab3" component={Tab3} />
  </IonRouterOutlet>
  <IonTabBar slot="bottom">
    <IonTabButton tab="tab1" href="/tab1">
      <IonIcon icon={homeOutline} />
      <IonLabel>Home</IonLabel>
    </IonTabButton>
    {/* ... */}
  </IonTabBar>
</IonTabs>
```

**Side Menu** — Best for apps with many sections:
```tsx
<IonSplitPane contentId="main">
  <IonMenu contentId="main">
    <IonHeader>
      <IonToolbar>
        <IonTitle>Menu</IonTitle>
      </IonToolbar>
    </IonHeader>
    <IonContent>
      <IonList>
        <IonMenuToggle autoHide={false}>
          <IonItem routerLink="/page1">Page 1</IonItem>
        </IonMenuToggle>
      </IonList>
    </IonContent>
  </IonMenu>
  <IonRouterOutlet id="main" />
</IonSplitPane>
```

**Stack Navigation** — For drill-down flows:
```tsx
<IonBackButton defaultHref="/home" />
```
Always set `defaultHref` so back navigation works even when the user deep-links into a page.

### Lists — The Workhorse Component

Lists appear everywhere in mobile apps. Use the right pattern:

```tsx
{/* Basic list */}
<IonList>
  <IonItem>
    <IonLabel>
      <h2>Primary Text</h2>
      <p>Secondary text</p>
    </IonLabel>
  </IonItem>
</IonList>

{/* Sliding items with actions */}
<IonList>
  <IonItemSliding>
    <IonItemOptions side="start">
      <IonItemOption color="success">Archive</IonItemOption>
    </IonItemOptions>
    <IonItem>
      <IonLabel>Swipe me</IonLabel>
    </IonItem>
    <IonItemOptions side="end">
      <IonItemOption color="danger">Delete</IonItemOption>
    </IonItemOptions>
  </IonItemSliding>
</IonList>

{/* Virtual scroll for large lists (performance critical) */}
{/* Use framework-specific virtual scroll or @ionic/react's IonContent */}
```

### Grid Layout — Responsive Image/Card Galleries

Use `IonGrid` with `IonRow` and `IonCol` for responsive grid layouts like photo galleries, dashboards, or card grids. This is the correct approach for multi-column layouts (not IonList):

```tsx
{/* Photo/Image Gallery — use IonGrid, NOT IonList */}
<IonGrid>
  <IonRow>
    {photos.map((photo) => (
      <IonCol size="6" sizeMd="4" sizeLg="3" key={photo.id}>
        <IonCard>
          <IonImg src={photo.webPath} alt={photo.description} />
          <IonCardHeader>
            <IonCardSubtitle>{photo.date}</IonCardSubtitle>
          </IonCardHeader>
        </IonCard>
      </IonCol>
    ))}
  </IonRow>
</IonGrid>

{/* Dashboard stats grid */}
<IonGrid>
  <IonRow>
    <IonCol size="6"><StatCard label="Steps" value={steps} /></IonCol>
    <IonCol size="6"><StatCard label="Calories" value={calories} /></IonCol>
    <IonCol size="6"><StatCard label="Distance" value={distance} /></IonCol>
    <IonCol size="6"><StatCard label="Time" value={activeTime} /></IonCol>
  </IonRow>
</IonGrid>
```

Column sizing: `size` sets the default (out of 12 columns). Use `sizeSm`, `sizeMd`, `sizeLg`, `sizeXl` for responsive breakpoints. For example, `size="6" sizeMd="4" sizeLg="3"` gives 2 columns on mobile, 3 on tablet, 4 on desktop.

### Forms — Getting Input Right

```tsx
<IonList>
  <IonItem>
    <IonInput
      label="Email"
      labelPlacement="stacked"
      type="email"
      placeholder="you@example.com"
      fill="outline"
      helperText="We'll never share your email"
      errorText="Invalid email"
      className={isValid ? '' : 'ion-invalid ion-touched'}
    />
  </IonItem>

  <IonItem>
    <IonTextarea
      label="Message"
      labelPlacement="stacked"
      fill="outline"
      autoGrow={true}
      rows={4}
    />
  </IonItem>

  <IonItem>
    <IonSelect label="Category" labelPlacement="stacked" fill="outline">
      <IonSelectOption value="bug">Bug Report</IonSelectOption>
      <IonSelectOption value="feature">Feature Request</IonSelectOption>
    </IonSelect>
  </IonItem>

  <IonItem>
    <IonToggle>Enable notifications</IonToggle>
  </IonItem>

  <IonItem>
    <IonRange labelPlacement="stacked" label="Volume" min={0} max={100}>
      <IonLabel slot="start">0</IonLabel>
      <IonLabel slot="end">100</IonLabel>
    </IonRange>
  </IonItem>
</IonList>
```

Use `labelPlacement="stacked"` and `fill="outline"` for modern form styling. Use `fill="solid"` for a softer look.

### Overlays — Modals, Alerts, Action Sheets

```tsx
{/* Modal — Present complex UI */}
<IonModal
  isOpen={showModal}
  onDidDismiss={() => setShowModal(false)}
  breakpoints={[0, 0.5, 1]}       // Sheet modal with stops
  initialBreakpoint={0.5}          // Start half-open
  handle={true}                     // Show drag handle
>
  <IonContent>
    {/* Modal content */}
  </IonContent>
</IonModal>

{/* Alert — Simple decisions */}
const [presentAlert] = useIonAlert();
presentAlert({
  header: 'Confirm',
  message: 'Are you sure?',
  buttons: ['Cancel', { text: 'OK', role: 'confirm' }],
});

{/* Action Sheet — List of actions */}
const [presentActionSheet] = useIonActionSheet();
presentActionSheet({
  header: 'Actions',
  buttons: [
    { text: 'Share', icon: shareOutline },
    { text: 'Delete', role: 'destructive', icon: trashOutline },
    { text: 'Cancel', role: 'cancel' },
  ],
});

{/* Toast — Non-intrusive feedback */}
const [presentToast] = useIonToast();
presentToast({
  message: 'Item saved!',
  duration: 2000,
  position: 'bottom',
  color: 'success',
});

{/* Loading — Block UI during operations */}
const [presentLoading, dismissLoading] = useIonLoading();
await presentLoading({ message: 'Saving...' });
await saveData();
await dismissLoading();
```

### Cards — Content Containers

```tsx
<IonCard>
  <IonImg src="/assets/photo.jpg" alt="Description" />
  <IonCardHeader>
    <IonCardSubtitle>Category</IonCardSubtitle>
    <IonCardTitle>Card Title</IonCardTitle>
  </IonCardHeader>
  <IonCardContent>
    Card description text goes here.
  </IonCardContent>
  <IonToolbar>
    <IonButtons slot="start">
      <IonButton fill="clear">
        <IonIcon icon={heartOutline} slot="icon-only" />
      </IonButton>
    </IonButtons>
  </IonToolbar>
</IonCard>
```

### Pull-to-Refresh and Infinite Scroll

```tsx
<IonContent>
  <IonRefresher slot="fixed" onIonRefresh={handleRefresh}>
    <IonRefresherContent />
  </IonRefresher>

  {/* Your list content */}

  <IonInfiniteScroll
    onIonInfinite={loadMore}
    threshold="100px"
    disabled={hasNoMoreData}
  >
    <IonInfiniteScrollContent loadingSpinner="bubbles" />
  </IonInfiniteScroll>
</IonContent>
```

### Skeleton Loading — Perceived Performance

```tsx
{isLoading ? (
  <IonList>
    {[...Array(5)].map((_, i) => (
      <IonItem key={i}>
        <IonThumbnail slot="start">
          <IonSkeletonText animated />
        </IonThumbnail>
        <IonLabel>
          <h2><IonSkeletonText animated style={{ width: '60%' }} /></h2>
          <p><IonSkeletonText animated style={{ width: '80%' }} /></p>
        </IonLabel>
      </IonItem>
    ))}
  </IonList>
) : (
  <ActualContent data={data} />
)}
```

## Theming — Native Look and Feel

### Platform-Adaptive Styling

Ionic automatically adapts to iOS and Material Design. The mode is set per-platform but can be overridden:

```typescript
// Force a specific mode globally
// In app setup:
setupIonicReact({ mode: 'ios' });  // or 'md'
```

### CSS Custom Properties

Ionic's design system is built on CSS variables. Override them in `theme/variables.css`:

```css
:root {
  /* Primary brand color — generates shade/tint automatically */
  --ion-color-primary: #3880ff;
  --ion-color-primary-rgb: 56, 128, 255;
  --ion-color-primary-contrast: #ffffff;
  --ion-color-primary-shade: #3171e0;
  --ion-color-primary-tint: #4c8dff;

  /* Application-level variables */
  --ion-background-color: #ffffff;
  --ion-text-color: #000000;
  --ion-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

  /* Stepped colors (for subtle backgrounds) */
  --ion-color-step-50: #f2f2f2;
  --ion-color-step-100: #e6e6e6;
  /* ... up to step-950 */
}
```

Use the [Ionic Color Generator](https://ionicframework.com/docs/theming/color-generator) to produce correct shade/tint/contrast values.

### Dark Mode

Three approaches (pick one):

```css
/* 1. Always dark */
@import '@ionic/react/css/palettes/dark.always.css';

/* 2. Follow system preference (recommended) */
@import '@ionic/react/css/palettes/dark.system.css';

/* 3. Toggle via CSS class */
@import '@ionic/react/css/palettes/dark.class.css';
/* Then add/remove .ion-palette-dark class on <html> */
```

Add this meta tag for native UI elements:
```html
<meta name="color-scheme" content="light dark" />
```

### Per-Component Styling

Use CSS Shadow Parts and CSS variables:
```css
/* Target shadow DOM parts */
ion-button::part(native) {
  border-radius: 20px;
}

/* Component-level CSS variables */
ion-item {
  --background: transparent;
  --border-color: var(--ion-color-light);
  --padding-start: 16px;
}
```

### CSS Utility Classes

Ionic provides utility classes for common styling. Import them in your global CSS:

```css
/* Import all utilities at once */
@import '@ionic/react/css/ionic.bundle.css';  /* React */
@import '@ionic/angular/css/ionic.bundle.css'; /* Angular */
@import '@ionic/vue/css/ionic.bundle.css';     /* Vue */
```

```html
<!-- Padding & Margin -->
<div class="ion-padding">Padded content</div>
<div class="ion-margin-top ion-no-padding">Top margin, no padding</div>

<!-- Text alignment -->
<p class="ion-text-center">Centered text</p>

<!-- Responsive visibility -->
<div class="ion-hide-md-up">Mobile only</div>
<div class="ion-hide-md-down">Tablet & desktop only</div>
```

> For complete utility class reference, Shadow Parts, and customization recipes, read `references/styling.md`.

## Capacitor Native APIs

### Installation Pattern

```bash
npm install @capacitor/camera    # Install the plugin
ionic cap sync                   # Sync to native projects
```

### Camera

```typescript
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';

const takePhoto = async () => {
  const image = await Camera.getPhoto({
    quality: 90,
    allowEditing: false,
    resultType: CameraResultType.Uri,      // or Base64, DataUrl
    source: CameraSource.Camera,           // or Photos, Prompt
    width: 1024,                           // Max width
    saveToGallery: true,
  });
  return image.webPath;  // Use this for <img src>
};
```

### Geolocation

```typescript
import { Geolocation } from '@capacitor/geolocation';

const getCurrentPosition = async () => {
  const coordinates = await Geolocation.getCurrentPosition({
    enableHighAccuracy: true,
    timeout: 10000,
  });
  return {
    lat: coordinates.coords.latitude,
    lng: coordinates.coords.longitude,
  };
};

// Watch position changes
const watchId = await Geolocation.watchPosition(
  { enableHighAccuracy: true },
  (position, err) => { /* handle updates */ }
);
// Later: Geolocation.clearWatch({ id: watchId });
```

### Push Notifications

```typescript
import { PushNotifications } from '@capacitor/push-notifications';

const initPush = async () => {
  const permStatus = await PushNotifications.requestPermissions();
  if (permStatus.receive === 'granted') {
    await PushNotifications.register();
  }

  PushNotifications.addListener('registration', (token) => {
    console.log('FCM token:', token.value);
    // Send token to your server
  });

  PushNotifications.addListener('pushNotificationReceived', (notification) => {
    console.log('Push received:', notification);
  });

  PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
    console.log('Push action:', action);
    // Navigate based on action.notification.data
  });
};
```

### Filesystem

```typescript
import { Filesystem, Directory, Encoding } from '@capacitor/filesystem';

// Write a file
await Filesystem.writeFile({
  path: 'data/config.json',
  data: JSON.stringify(config),
  directory: Directory.Data,
  encoding: Encoding.UTF8,
  recursive: true,  // Create directories as needed
});

// Read a file
const result = await Filesystem.readFile({
  path: 'data/config.json',
  directory: Directory.Data,
  encoding: Encoding.UTF8,
});
```

### Other Core Plugins

| Plugin | Install | Key Methods |
|--------|---------|-------------|
| `@capacitor/app` | `npm i @capacitor/app` | `App.addListener('appStateChange')`, `App.getLaunchUrl()` |
| `@capacitor/browser` | `npm i @capacitor/browser` | `Browser.open({ url })` |
| `@capacitor/clipboard` | `npm i @capacitor/clipboard` | `Clipboard.write()`, `Clipboard.read()` |
| `@capacitor/device` | `npm i @capacitor/device` | `Device.getInfo()`, `Device.getId()` |
| `@capacitor/haptics` | `npm i @capacitor/haptics` | `Haptics.impact()`, `Haptics.vibrate()` |
| `@capacitor/keyboard` | `npm i @capacitor/keyboard` | `Keyboard.show()`, `Keyboard.hide()` |
| `@capacitor/network` | `npm i @capacitor/network` | `Network.getStatus()`, `Network.addListener()` |
| `@capacitor/preferences` | `npm i @capacitor/preferences` | `Preferences.set()`, `Preferences.get()` |
| `@capacitor/share` | `npm i @capacitor/share` | `Share.share({ title, text, url })` |
| `@capacitor/splash-screen` | `npm i @capacitor/splash-screen` | `SplashScreen.hide()`, `SplashScreen.show()` |
| `@capacitor/status-bar` | `npm i @capacitor/status-bar` | `StatusBar.setStyle()`, `StatusBar.hide()` |
| `@capacitor/action-sheet` | `npm i @capacitor/action-sheet` | `ActionSheet.showActions({ options })` |
| `@capacitor/app-launcher` | `npm i @capacitor/app-launcher` | `AppLauncher.canOpenUrl()`, `openUrl()` |
| `@capacitor/dialog` | `npm i @capacitor/dialog` | `Dialog.alert()`, `confirm()`, `prompt()` |
| `@capacitor/google-maps` | `npm i @capacitor/google-maps` | `GoogleMap.create()`, `addMarker()`, `setCamera()` |
| `@capacitor/local-notifications` | `npm i @capacitor/local-notifications` | `LocalNotifications.schedule()`, `requestPermissions()` |
| `@capacitor/motion` | `npm i @capacitor/motion` | `Motion.addListener('accel')`, `'orientation'` |
| `@capacitor/screen-reader` | `npm i @capacitor/screen-reader` | `ScreenReader.isEnabled()`, `speak()` |
| `@capacitor/text-zoom` | `npm i @capacitor/text-zoom` | `TextZoom.get()`, `set()`, `getPreferred()` |
| `@capacitor/toast` | `npm i @capacitor/toast` | `Toast.show({ text, position, duration })` |

> For full plugin documentation with code examples, read `references/native-plugins.md`.

## Performance Optimization

### Lazy Loading Routes

Split your app into chunks. Load pages only when navigated to:

```tsx
// React
const Tab1 = React.lazy(() => import('./pages/Tab1'));
const Tab2 = React.lazy(() => import('./pages/Tab2'));

// Wrap in Suspense with skeleton fallback
<Suspense fallback={<IonSpinner />}>
  <Route exact path="/tab1" component={Tab1} />
</Suspense>
```

### Image & Render Optimization

- Use `<IonImg>` instead of `<img>` for lazy loading; `<IonThumbnail>` in lists
- Memoize with `useMemo`/`useCallback` (React), `computed` (Vue), `trackBy` (Angular)
- Avoid inline object creation in JSX props

### Bundle Size

Import only what you use: `import { IonButton } from '@ionic/react'` — never `import * as Ionic`. Analyze with `npx source-map-explorer dist/assets/*.js`.

### Virtual Scrolling for Large Lists

For lists with 100+ items, use virtual scrolling to render only visible items. Each framework has its approach — see the framework-specific reference files.

## Development Workflow

```bash
ionic serve                           # Browser preview
ionic cap run ios -l --external       # Live reload on iOS device
ionic cap run android -l --external   # Live reload on Android
ionic build && ionic cap sync         # Build + sync to native projects
ionic cap open ios                    # Open Xcode
ionic cap open android                # Open Android Studio
```

**Debugging:** Browser via `ionic serve` DevTools • iOS via Safari > Develop > [Device] • Android via `chrome://inspect`

## Deployment

**iOS:** Apple Developer account ($99/yr) → configure signing in Xcode → set Bundle ID matching `appId` → Product > Archive → upload via Xcode Organizer.

**Android:** Google Play Developer account ($25) → Build > Generate Signed Bundle (AAB) → upload to Google Play Console.

### App Icons, Splash Screens & Assets Generation

Use `@capacitor/assets` to generate all platform icons and splash screens from source images.

```bash
# Install
npm install @capacitor/assets --save-dev
```

Place your logo at `assets/logo.png` (1024x1024px min), optionally `assets/logo-dark.png` for dark mode:

```bash
npx @capacitor/assets generate \
  --iconBackgroundColor '#ffffff' \
  --iconBackgroundColorDark '#111111' \
  --splashBackgroundColor '#ffffff' \
  --splashBackgroundColorDark '#111111'
```

For custom mode, provide separate `icon-only.png`, `icon-foreground.png`, `icon-background.png`, and `splash.png` (2732x2732px) in the `assets/` directory. Use `--ios`, `--android`, or `--pwa` flags to target specific platforms.

## Production Essentials

### Error Handling for Native APIs

Always wrap Capacitor plugin calls in try/catch and distinguish user cancellation from real errors:

```typescript
import { Camera, CameraResultType } from '@capacitor/camera';

const takePhoto = async () => {
  try {
    const image = await Camera.getPhoto({
      quality: 90,
      resultType: CameraResultType.Uri,
    });
    return image.webPath;
  } catch (error: any) {
    if (error.message === 'User cancelled photos app') {
      return null; // Not an error — user just cancelled
    }
    console.error('Camera error:', error);
    throw error;
  }
};
```

### Platform-Aware Code

```typescript
import { Capacitor } from '@capacitor/core';

// Check if running on native device (iOS/Android) vs browser
if (Capacitor.isNativePlatform()) {
  // Use native plugin
  const { Camera } = await import('@capacitor/camera');
  await Camera.getPhoto({ /* ... */ });
} else {
  // Web fallback
  fileInput.click();
}

// Get specific platform: 'ios' | 'android' | 'web'
const platform = Capacitor.getPlatform();
```

> For complete production patterns (offline handling, security, accessibility, debugging), read `references/production.md`.

## Common Pitfalls

1. **Missing IonPage wrapper** — Every routed page component must be wrapped in `<IonPage>`. Without it, page transitions break and content may not scroll properly.

2. **Not using ionic cap sync** — After installing Capacitor plugins, always run `ionic cap sync`. Just `npm install` isn't enough.

3. **Hardcoding platform checks** — Use Ionic's `isPlatform()` utility instead of user-agent sniffing.

4. **Ignoring safe areas** — Use `<IonContent fullscreen>` and Ionic's built-in safe area handling. Don't manually add padding for notches.

5. **Using browser APIs directly** — Use Capacitor plugins instead. `navigator.camera` doesn't exist in native context — use `@capacitor/camera`.

6. **Not testing on real devices** — Emulators miss touch behavior, performance issues, and native plugin quirks. Test on physical devices regularly.

7. **Importing entire icon libraries** — Import individual icons: `import { heart } from 'ionicons/icons'` not the entire library.

## Reference Files

For deep dives, read the appropriate reference:

- **Components**: `references/components.md` — Complete list of all 94 Ionic UI components with usage guidance
- **Native Plugins**: `references/native-plugins.md` — All 24 Capacitor plugins with code examples
- **Styling**: `references/styling.md` — CSS utilities, Shadow Parts, custom properties, responsive design
- **Production**: `references/production.md` — Error handling, security, accessibility, debugging, performance
- **React**: `references/react.md` — Hooks, routing with React Router, state with Zustand/TanStack Query
- **Angular**: `references/angular.md` — Standalone components, signals, guards, services
- **Vue**: `references/vue.md` — Composition API, Pinia, Vue Router integration
