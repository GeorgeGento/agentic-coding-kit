# Capacitor Native Plugins — Complete Reference

Guide to all 24 official Capacitor plugins with TypeScript examples and production patterns.

## Universal Installation Pattern

```bash
npm install @capacitor/<plugin-name>
ionic cap sync    # Required — copies plugin code to native projects
```

For plugins requiring permissions, configure platform-specific entries:
- **iOS**: Add usage description keys to `ios/App/App/Info.plist`
- **Android**: Add `<uses-permission>` to `android/app/src/main/AndroidManifest.xml`

## Plugins Documented in SKILL.md

These plugins have full examples in `SKILL.md` — refer there for details:

- **@capacitor/camera** — `Camera.getPhoto()` with quality, source, resultType
- **@capacitor/geolocation** — `getCurrentPosition()`, `watchPosition()`, `clearWatch()`
- **@capacitor/push-notifications** — `register()`, token listeners, notification handlers
- **@capacitor/filesystem** — `writeFile()`, `readFile()` with Directory/Encoding enums

SKILL.md also has a quick-reference table for: `@capacitor/app`, `@capacitor/browser`, `@capacitor/clipboard`, `@capacitor/device`, `@capacitor/haptics`, `@capacitor/keyboard`, `@capacitor/network`, `@capacitor/preferences`, `@capacitor/share`, `@capacitor/splash-screen`, `@capacitor/status-bar`.

## Action Sheet

```bash
npm install @capacitor/action-sheet && ionic cap sync
```

```typescript
import { ActionSheet, ActionSheetButtonStyle } from '@capacitor/action-sheet';

const showPhotoOptions = async (): Promise<string | null> => {
  const result = await ActionSheet.showActions({
    title: 'Select Photo Source',
    message: 'Choose where to get your photo',
    options: [
      { title: 'Camera', style: ActionSheetButtonStyle.Default },
      { title: 'Photo Library', style: ActionSheetButtonStyle.Default },
      { title: 'Remove Photo', style: ActionSheetButtonStyle.Destructive },
      { title: 'Cancel', style: ActionSheetButtonStyle.Cancel },
    ],
  });

  switch (result.index) {
    case 0: return 'camera';
    case 1: return 'library';
    case 2: return 'remove';
    default: return null;
  }
};
```

**Native vs Ionic**: Use `@capacitor/action-sheet` for OS-native look with zero customization. Use `IonActionSheet` or `useIonActionSheet()` when you need icons, colors, or cross-platform consistency. Ionic's version is the better default choice.

## App Launcher

```bash
npm install @capacitor/app-launcher && ionic cap sync
```

```typescript
import { AppLauncher } from '@capacitor/app-launcher';

const openInMaps = async (lat: number, lng: number): Promise<void> => {
  const { value: canOpen } = await AppLauncher.canOpenUrl({ url: 'comgooglemaps://' });

  if (canOpen) {
    await AppLauncher.openUrl({ url: `comgooglemaps://?center=${lat},${lng}&zoom=14` });
  } else {
    await AppLauncher.openUrl({ url: `https://www.google.com/maps/@${lat},${lng},14z` });
  }
};
```

**iOS requirement**: Declare queried URL schemes in `Info.plist` or `canOpenUrl()` always returns `false`:

```xml
<key>LSApplicationQueriesSchemes</key>
<array>
  <string>comgooglemaps</string>
  <string>whatsapp</string>
</array>
```

## Dialog

```bash
npm install @capacitor/dialog && ionic cap sync
```

```typescript
import { Dialog } from '@capacitor/dialog';

// Alert — informational, single OK button
await Dialog.alert({ title: 'Error', message: 'Something went wrong', buttonTitle: 'OK' });

// Confirm — returns { value: boolean }
const confirmDelete = async (itemName: string): Promise<boolean> => {
  const { value } = await Dialog.confirm({
    title: 'Delete Item',
    message: `Delete "${itemName}"? This cannot be undone.`,
    okButtonTitle: 'Delete',
    cancelButtonTitle: 'Cancel',
  });
  return value;
};

// Prompt — returns { value: string, cancelled: boolean }
const askForName = async (): Promise<string | null> => {
  const { value, cancelled } = await Dialog.prompt({
    title: 'Your Name',
    message: 'Enter your display name:',
    inputPlaceholder: 'John Doe',
    okButtonTitle: 'Save',
    cancelButtonTitle: 'Skip',
  });
  return cancelled ? null : value;
};
```

**Native vs Ionic**: Use native `Dialog` for critical OS-styled confirmations (delete, logout). Use `IonAlert` when you need multiple inputs, styled buttons, or custom layouts.

## Local Notifications

```bash
npm install @capacitor/local-notifications && ionic cap sync
```

```typescript
import { LocalNotifications } from '@capacitor/local-notifications';

// Request permission (required on iOS; auto-granted on Android 12 and below)
const permStatus = await LocalNotifications.requestPermissions();
const granted = permStatus.display === 'granted';

// Schedule a one-time notification
await LocalNotifications.schedule({
  notifications: [{
    id: Date.now(),
    title: 'Reminder',
    body: 'Time to check in!',
    schedule: { at: new Date(Date.now() + 30 * 60 * 1000) },
    sound: 'default',
    smallIcon: 'ic_notification',
    extra: { type: 'reminder' },
  }],
});

// Schedule a recurring daily notification
await LocalNotifications.schedule({
  notifications: [{
    id: 1001,
    title: 'Daily Check-in',
    body: 'Log your progress!',
    schedule: { on: { hour: 9, minute: 0 }, repeats: true, allowWhileIdle: true },
    channelId: 'reminders',
  }],
});

// Android 8+ channels (create once at app startup)
await LocalNotifications.createChannel({
  id: 'reminders',
  name: 'Reminders',
  description: 'Daily reminder notifications',
  importance: 4,
  vibration: true,
});

// Manage pending and delivered notifications
const { notifications: pending } = await LocalNotifications.getPending();
await LocalNotifications.cancel({ notifications: [{ id: 1001 }] });
const { notifications: delivered } = await LocalNotifications.getDeliveredNotifications();
await LocalNotifications.removeAllDeliveredNotifications();

// Event listeners
LocalNotifications.addListener('localNotificationReceived', (notification) => {
  console.log('Received:', notification);
});

LocalNotifications.addListener('localNotificationActionPerformed', (action) => {
  // Navigate based on action.notification.extra
  console.log('Action:', action.actionId, action.notification.extra);
});
```

## Motion

```bash
npm install @capacitor/motion && ionic cap sync
```

```typescript
import { Motion } from '@capacitor/motion';
import type { AccelListenerEvent } from '@capacitor/motion';

// Accelerometer data
await Motion.addListener('accel', (event: AccelListenerEvent) => {
  const { x, y, z } = event.acceleration;
  const { x: gx, y: gy, z: gz } = event.accelerationIncludingGravity;
});

// Device orientation (gyroscope)
await Motion.addListener('orientation', (event) => {
  // alpha: z-axis rotation (0-360), beta: front-back tilt (-180 to 180), gamma: left-right (-90 to 90)
  const { alpha, beta, gamma } = event;
});

// Shake detection
const detectShake = async (onShake: () => void): Promise<void> => {
  const THRESHOLD = 30;
  let lastX = 0, lastY = 0, lastZ = 0;

  await Motion.addListener('accel', (event: AccelListenerEvent) => {
    const { x, y, z } = event.accelerationIncludingGravity;
    if (Math.abs(x - lastX) + Math.abs(y - lastY) + Math.abs(z - lastZ) > THRESHOLD) {
      onShake();
    }
    lastX = x; lastY = y; lastZ = z;
  });
};

// Always clean up — continuous sensor use drains battery
await Motion.removeAllListeners();
```

Call `removeAllListeners()` when leaving a page. In native Capacitor apps no extra permission is needed; on iOS web, the user must grant motion permission in Safari settings.

## Screen Reader

```bash
npm install @capacitor/screen-reader && ionic cap sync
```

```typescript
import { ScreenReader } from '@capacitor/screen-reader';

// Check if VoiceOver (iOS) or TalkBack (Android) is active
const { value: isEnabled } = await ScreenReader.isEnabled();

// Announce dynamic content changes to screen reader users
await ScreenReader.speak({ value: `List updated. ${count} items loaded.` });

// React to screen reader being toggled on/off
ScreenReader.addListener('stateChange', ({ value: enabled }) => {
  console.log('Screen reader enabled:', enabled);
});
```

Use `speak()` for state changes that visual users see but screen readers might miss: toast messages, loading completions, error states.

## Text Zoom

```bash
npm install @capacitor/text-zoom && ionic cap sync
```

```typescript
import { TextZoom } from '@capacitor/text-zoom';

const { value: current } = await TextZoom.get();         // 1.0 = default
const { value: preferred } = await TextZoom.getPreferred(); // System setting
await TextZoom.set({ value: 1.2 });                      // Set to 120%

// Accessibility settings helper
const increaseZoom = async (): Promise<void> => {
  const { value } = await TextZoom.get();
  await TextZoom.set({ value: Math.min(value + 0.1, 2.0) });
};

const decreaseZoom = async (): Promise<void> => {
  const { value } = await TextZoom.get();
  await TextZoom.set({ value: Math.max(value - 0.1, 0.5) });
};

const matchSystem = async (): Promise<void> => {
  const { value } = await TextZoom.getPreferred();
  await TextZoom.set({ value });
};
```

Only works in native Capacitor context (not via `ionic serve`). Maps to `WebSettings.setTextZoom()` on Android and WebView text scaling on iOS.

## Toast

```bash
npm install @capacitor/toast && ionic cap sync
```

```typescript
import { Toast } from '@capacitor/toast';

await Toast.show({
  text: 'Changes saved',
  duration: 'short',    // 'short' (~2s) or 'long' (~3.5s)
  position: 'bottom',   // 'top', 'center', or 'bottom'
});
```

**Native Toast vs `IonToast`**: Native `@capacitor/toast` offers no customization — no colors, icons, action buttons, or dismiss callbacks. Use Ionic's `IonToast` (via `useIonToast()`) when you need custom colors, action buttons (e.g., "Undo"), icons, `onDidDismiss`, or consistent cross-platform styling. `IonToast` is the better default for Ionic apps.

## Google Maps

```bash
npm install @capacitor/google-maps && ionic cap sync
```

**Setup**: Get API keys from Google Cloud Console (enable Maps SDK for iOS and Android).

```typescript
// capacitor.config.ts
const config: CapacitorConfig = {
  plugins: { GoogleMaps: { androidApiKey: 'YOUR_ANDROID_KEY' } },
};
```

```xml
<!-- ios/App/App/Info.plist -->
<key>GMS_SERVICES_API_KEY</key>
<string>YOUR_IOS_KEY</string>
```

**Usage** (add `<capacitor-google-map id="map" style="display:inline-block;width:100%;height:400px">` to your template):

```typescript
import { GoogleMap, Marker, MapType } from '@capacitor/google-maps';

// Create map
const map = await GoogleMap.create({
  id: 'main-map',
  element: document.getElementById('map')!,
  apiKey: 'YOUR_API_KEY',
  config: { center: { lat: 37.7749, lng: -122.4194 }, zoom: 12 },
  forceCreate: true,
});

// Add markers (returns array of marker IDs)
const markerIds = await map.addMarkers([
  { coordinate: { lat: 37.7749, lng: -122.4194 }, title: 'San Francisco', snippet: 'CA' },
]);

// Camera control
await map.setCamera({ coordinate: { lat: 37.7749, lng: -122.4194 }, zoom: 15, animate: true });
await map.setMapType(MapType.Satellite); // Normal, Satellite, Terrain, Hybrid

// Features
await map.enableCurrentLocation(true);  // Blue dot (requires location permission)
await map.enableClustering();

// Event listeners
await map.setOnMarkerClickListener((marker) => console.log('Tapped:', marker.title));
await map.setOnMapClickListener((e) => console.log('Map tap:', e.latitude, e.longitude));
await map.setOnCameraIdleListener(() => { /* load data for visible region */ });

// Clean up when leaving page
await map.destroy();
```

**Key considerations**:
- The map renders as a native view behind the web view. Ionic components over the map need `--background: transparent`.
- Always call `map.destroy()` on page leave to free resources.
- Set `Privacy - Location When In Use Usage Description` in `Info.plist` if using `enableCurrentLocation`.

## All 24 Capacitor Plugins — Quick Reference

| # | Plugin | Package | Key Methods | Permissions |
|---|--------|---------|-------------|-------------|
| 1 | Action Sheet | `@capacitor/action-sheet` | `showActions()` | None |
| 2 | App | `@capacitor/app` | `getInfo()`, `getState()`, `addListener('appStateChange')`, `getLaunchUrl()`, `exitApp()` | None |
| 3 | App Launcher | `@capacitor/app-launcher` | `canOpenUrl()`, `openUrl()` | iOS: `LSApplicationQueriesSchemes` |
| 4 | Browser | `@capacitor/browser` | `open()`, `close()`, `addListener('browserFinished')` | None |
| 5 | Camera | `@capacitor/camera` | `getPhoto()`, `pickImages()`, `checkPermissions()`, `requestPermissions()` | Camera + Photo Library |
| 6 | Clipboard | `@capacitor/clipboard` | `write()`, `read()` | None |
| 7 | Device | `@capacitor/device` | `getInfo()`, `getId()`, `getBatteryInfo()`, `getLanguageCode()` | None |
| 8 | Dialog | `@capacitor/dialog` | `alert()`, `confirm()`, `prompt()` | None |
| 9 | Filesystem | `@capacitor/filesystem` | `writeFile()`, `readFile()`, `deleteFile()`, `mkdir()`, `readdir()`, `stat()` | Android: Storage (API < 30) |
| 10 | Geolocation | `@capacitor/geolocation` | `getCurrentPosition()`, `watchPosition()`, `clearWatch()` | Location |
| 11 | Google Maps | `@capacitor/google-maps` | `GoogleMap.create()`, `addMarker()`, `setCamera()`, `setMapType()`, `destroy()` | Location (blue dot) |
| 12 | Haptics | `@capacitor/haptics` | `impact()`, `notification()`, `vibrate()`, `selectionStart/Changed/End()` | None |
| 13 | Keyboard | `@capacitor/keyboard` | `show()`, `hide()`, `setAccessoryBarVisible()`, `addListener('keyboardWillShow')` | None |
| 14 | Local Notifications | `@capacitor/local-notifications` | `schedule()`, `cancel()`, `getPending()`, `createChannel()`, `requestPermissions()` | Notifications |
| 15 | Motion | `@capacitor/motion` | `addListener('accel'/'orientation')`, `removeAllListeners()` | iOS Web: Motion |
| 16 | Network | `@capacitor/network` | `getStatus()`, `addListener('networkStatusChange')` | None |
| 17 | Preferences | `@capacitor/preferences` | `set()`, `get()`, `remove()`, `clear()`, `keys()` | None |
| 18 | Push Notifications | `@capacitor/push-notifications` | `register()`, `requestPermissions()`, `addListener('registration'/'received')` | Push |
| 19 | Screen Reader | `@capacitor/screen-reader` | `isEnabled()`, `speak()`, `addListener('stateChange')` | None |
| 20 | Screen Orientation | `@capacitor/screen-orientation` | `lock()`, `unlock()`, `addListener('screenOrientationChange')` | None |
| 21 | Share | `@capacitor/share` | `share({ title, text, url })`, `canShare()` | None |
| 22 | Splash Screen | `@capacitor/splash-screen` | `show()`, `hide()` | None |
| 23 | Status Bar | `@capacitor/status-bar` | `setStyle()`, `setBackgroundColor()`, `show()`, `hide()`, `setOverlaysWebView()` | None |
| 24 | Text Zoom | `@capacitor/text-zoom` | `get()`, `set()`, `getPreferred()` | None |
