# Production Patterns for Ionic + Capacitor Apps

Best practices for shipping reliable, performant, and secure Ionic + Capacitor apps. All examples use TypeScript.

---

## Error Handling for Native APIs

Capacitor plugin calls are async and can fail for many reasons. Always wrap in try/catch and distinguish user cancellation from real errors.

```typescript
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';

const takePhoto = async (): Promise<string | null> => {
  try {
    const image = await Camera.getPhoto({
      quality: 90,
      resultType: CameraResultType.Uri,
      source: CameraSource.Prompt,
    });
    return image.webPath ?? null;
  } catch (error: any) {
    if (error.message === 'User cancelled photos app') {
      return null; // Not an error — user just backed out
    }
    console.error('Camera error:', error);
    throw error;
  }
};
```

Geolocation has numeric error codes: `1` = PERMISSION_DENIED, `3` = TIMEOUT. Check `error.code` to distinguish and handle each case (prompt Settings vs retry).

Reusable pattern for any plugin:

```typescript
async function safePluginCall<T>(
  fn: () => Promise<T>,
  cancelMessages: string[] = []
): Promise<{ data: T | null; error: string | null }> {
  try {
    return { data: await fn(), error: null };
  } catch (error: any) {
    if (cancelMessages.includes(error.message)) return { data: null, error: null };
    return { data: null, error: error.message || 'Unknown error' };
  }
}
```

## Platform Detection

```typescript
import { Capacitor } from '@capacitor/core';

Capacitor.isNativePlatform();  // true on iOS/Android, false in browser
Capacitor.getPlatform();       // 'ios' | 'android' | 'web'
```

Use `isPlatform()` from `@ionic/react` (or `@ionic/angular`, `@ionic/vue`) for UI adjustments: `isPlatform('ios')`, `isPlatform('tablet')`, `isPlatform('desktop')`, `isPlatform('pwa')`.

Graceful fallback pattern:

```typescript
const shareContent = async (title: string, text: string, url: string) => {
  if (Capacitor.isNativePlatform()) {
    const { Share } = await import('@capacitor/share');
    await Share.share({ title, text, url });
  } else if (navigator.share) {
    await navigator.share({ title, text, url });
  } else {
    await navigator.clipboard.writeText(url); // Final fallback
  }
};

// Check plugin availability before calling
if (Capacitor.isPluginAvailable('Camera')) {
  await Camera.getPhoto({ /* ... */ });
} else {
  // Fall back to <input type="file" accept="image/*">
}
```

## Offline Handling

### Network Monitoring + Offline Banner

```typescript
import { Network } from '@capacitor/network';

Network.addListener('networkStatusChange', (status) => {
  if (!status.connected) {
    presentToast({
      message: 'You are offline. Some features may be unavailable.',
      duration: 0, position: 'top', color: 'warning',
      buttons: [{ text: 'Dismiss', role: 'cancel' }],
    });
  }
});
```

### Cache-First Data Fetching with Preferences

```typescript
import { Preferences } from '@capacitor/preferences';

async function getCachedOrFetch<T>(key: string, fetchFn: () => Promise<T>, ttl = 300000): Promise<T> {
  const { value } = await Preferences.get({ key: `cache_${key}` });
  if (value) {
    const cached = JSON.parse(value);
    if (Date.now() - cached.ts < ttl) return cached.data;
  }
  try {
    const data = await fetchFn();
    await Preferences.set({ key: `cache_${key}`, value: JSON.stringify({ data, ts: Date.now() }) });
    return data;
  } catch {
    if (value) return JSON.parse(value).data; // Return stale cache on failure
    throw new Error('No data available offline');
  }
}
```

### Offline Request Queue

Queue writes when offline, flush when connectivity returns:

```typescript
const QUEUE_KEY = 'offline_queue';

const enqueueRequest = async (url: string, method: string, body: any) => {
  const { value } = await Preferences.get({ key: QUEUE_KEY });
  const queue = value ? JSON.parse(value) : [];
  queue.push({ id: crypto.randomUUID(), url, method, body: JSON.stringify(body) });
  await Preferences.set({ key: QUEUE_KEY, value: JSON.stringify(queue) });
};

const flushQueue = async () => {
  const { value } = await Preferences.get({ key: QUEUE_KEY });
  if (!value) return;
  const remaining = [];
  for (const req of JSON.parse(value)) {
    try { await fetch(req.url, { method: req.method, headers: { 'Content-Type': 'application/json' }, body: req.body }); }
    catch { remaining.push(req); }
  }
  await Preferences.set({ key: QUEUE_KEY, value: JSON.stringify(remaining) });
};

Network.addListener('networkStatusChange', (s) => { if (s.connected) flushQueue(); });
```

## Security Best Practices

**XSS prevention**: Use framework binding (`{userInput}` in JSX, `{{ userInput }}` in Angular/Vue). Never use `dangerouslySetInnerHTML`, `[innerHTML]`, or `v-html` with user data.

**Content Security Policy** in `index.html`:
```html
<meta http-equiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';
    img-src 'self' data: https:; connect-src 'self' https://your-api.com;">
```

**HTTPS enforcement** in `capacitor.config.ts`: Set `server.androidScheme: 'https'` and `android.allowMixedContent: false`.

**Secure storage**: `@capacitor/preferences` is NOT encrypted. Use `capacitor-secure-storage-plugin` for tokens and secrets:
```typescript
import { SecureStoragePlugin } from 'capacitor-secure-storage-plugin';
await SecureStoragePlugin.set({ key: 'auth_token', value: token });
```

**Input validation**: Always validate server-side. Client-side validation is for UX only.

## Accessibility

```tsx
{/* ARIA labels on icon-only buttons */}
<IonButton aria-label="Delete item">
  <IonIcon icon={trashOutline} slot="icon-only" />
</IonButton>

{/* ion-label is required for screen reader support on form controls */}
<IonItem>
  <IonLabel position="stacked">Your Name</IonLabel>
  <IonInput placeholder="Enter your name" />
</IonItem>
```

**Screen reader announcements** with `@capacitor/screen-reader`:
```typescript
import { ScreenReader } from '@capacitor/screen-reader';
if (Capacitor.isNativePlatform()) {
  await ScreenReader.speak({ value: 'Item saved successfully' });
}
// Web fallback: update an ARIA live region element
```

**Keyboard navigation**: Use `tabIndex={0}` on custom interactive elements. Manage focus on modal open with `onDidPresent` to call `setFocus()` on the first input.

**Color contrast**: Ionic's built-in color system meets WCAG requirements. Use `--ion-color-primary-contrast` for guaranteed readable text on colored backgrounds.

## Debugging on Devices

- **iOS**: Safari > Develop menu > [Device Name] > [App WebView]. Requires Web Inspector enabled in Settings > Safari > Advanced
- **Android**: `chrome://inspect/#devices` while app runs on device/emulator with USB Debugging enabled
- `console.log` works in both Safari and Chrome remote debugging

```typescript
const DEBUG = !import.meta.env.PROD;
const debugLog = (...args: any[]) => { if (DEBUG) console.log('[DEBUG]', ...args); };

if (DEBUG) {
  console.log('Platform:', Capacitor.getPlatform());
  console.log('Is native:', Capacitor.isNativePlatform());
}
```

```bash
ionic cap run ios -l --external      # Live reload on iOS device
adb logcat | grep -i "capacitor"     # Filter Android logs
```

## Performance Patterns

**Lighthouse**: Run `ionic build --prod`, serve with `npx serve dist`, audit in Chrome DevTools. Target 90+ on Performance, Accessibility, Best Practices.

**Memory leak prevention** — every `addListener` needs cleanup:
```typescript
useEffect(() => {
  let watchId: string;
  const listeners: (() => void)[] = [];
  const setup = async () => {
    watchId = await Geolocation.watchPosition({ enableHighAccuracy: true }, (pos) => { /* ... */ });
    const h = await Network.addListener('networkStatusChange', (s) => { /* ... */ });
    listeners.push(() => h.remove());
  };
  setup();
  return () => {
    if (watchId) Geolocation.clearWatch({ id: watchId });
    listeners.forEach((r) => r());
  };
}, []);
```

**Common bottlenecks**: Large images (use `width` option in Camera, use `IonImg` for lazy loading), unoptimized lists (virtual scroll for 100+ items), excessive re-renders (memoize with `useMemo`/`useCallback`/`computed`), heavy initial load (lazy load routes — see SKILL.md).

**Lazy load plugins**: `const { Camera } = await import('@capacitor/camera');`

## Common Production Gotchas

**Keyboard pushing content**: Use `Keyboard.setResizeMode({ mode: KeyboardResize.Ionic })` (recommended). Options: `Body`, `Ionic`, `None`.

**Status bar overlap on Android**:
```typescript
if (Capacitor.getPlatform() === 'android') {
  await StatusBar.setOverlaysWebView({ overlay: false });
}
```

**Deep linking**: `App.addListener('appUrlOpen', (event) => { router.push(extractPath(event.url)); })`. Also check `App.getLaunchUrl()` on startup. Requires native config: Associated Domains (iOS) or intent-filter (Android).

**Android back button**:
```typescript
App.addListener('backButton', ({ canGoBack }) => {
  if (canGoBack) window.history.back();
  else App.minimizeApp(); // Background instead of exit
});
```

**Splash screen timing**: Set `launchAutoHide: false` in config, then:
```typescript
try {
  await Promise.all([loadUserProfile(), loadAppConfig(), checkAuthStatus()]);
} finally {
  await SplashScreen.hide({ fadeOutDuration: 300 }); // Always hide, even on error
}
```

**iOS swipe-back conflicts**: Horizontal swipe gestures (carousels) conflict with iOS back gesture. Use `scrollX={false}` on `IonContent` or disable swipe-back on affected pages.
