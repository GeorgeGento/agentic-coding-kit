# UI Testing by Platform

Read when you need to open an app, look at its UI, and drive a flow on web, Electron, Tauri, Android, or Compose Desktop. The look-compare-iterate loop and the screenshot cap are in [ux-ui-seo](ux-ui-seo.md#design-direction); this file covers **how** to launch, screenshot, and drive each platform. Screenshots go to `.output/screenshots/`, traces and reports to `.output/<tool>/`.

Before launching anything: if the app needs a dev server, emulator, or running backend, **ask the user** whether you start it or they do. Never start a second instance of something they already run, and stop everything you started.

## Pick the cheapest level that proves it

1. **Component/UI tests** (fast, headless): logic, states, rendering.
2. **The frontend alone with the backend mocked** (browser + Playwright): most flows and visual checks.
3. **The real app end to end**: only the critical journeys, and the checks that need the real shell (native menus, file dialogs, IPC, permissions).

## Web

- Playwright (`@playwright/test`) for flows; `npx playwright screenshot --viewport-size=390,844 <url> .output/screenshots/x-390.png` for quick looks. The `webapp-testing` skill wraps this for local apps.
- Prefer the CLI and test files over a browser MCP server: an MCP server's tool definitions cost tokens every session.

## Electron

- Playwright drives Electron directly: `const app = await _electron.launch({ args: ['.'] })` (from `playwright`), then `const win = await app.firstWindow()`. Same locators, `toHaveScreenshot`, and traces as web.
- `app.evaluate(({ app }) => ...)` runs code in the main process (e.g. read app paths, trigger menu actions). Close with `app.close()` in teardown.
- Point the app at a **throwaway user-data dir** for tests (`args: ['.', '--user-data-dir=<tmp>']` or an env override): never the real profile.

## Tauri

Playwright can't launch a Tauri webview directly. In order of preference:

1. **Frontend + mocked backend (default):** run the frontend dev server in a normal browser, mock the Rust commands with `mockIPC` from `@tauri-apps/api/mocks` (clear with `clearMocks()` after each test), and use Playwright as on the web. Covers most UI and flows.
2. **Real app on Windows via WebView2 debugging (verify on first use):** launch the built app with `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9222` (a free port per instance), wait until the window is up, then `chromium.connectOverCDP('http://127.0.0.1:9222')` and take `browser.contexts()[0].pages()[0]`. Documented by Playwright for WebView2; Tauri uses WebView2 on Windows, but confirm it works for the project before relying on it.
3. **Official WebDriver route:** `tauri-driver` + WebdriverIO. Windows and Linux only (no macOS driver), and on Windows `msedgedriver` must match the installed WebView2 version.

## Android (Kotlin, Compose or XML)

- **Component level:** Compose UI tests (`createComposeRule()`, `onNodeWithText(...).performClick()`, `assertIsDisplayed()`), or Espresso for XML views. Instrumented: `./gradlew connectedDebugAndroidTest`; JVM-only with Robolectric where the project uses it.
- **Open the app and look:**
  ```sh
  emulator -avd <name> -no-snapshot-save &        # or a device the user connected
  adb wait-for-device
  ./gradlew installDebug
  adb shell am start -n <applicationId>/<.MainActivity>
  adb exec-out screencap -p > .output/screenshots/home.png
  adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml .output/ui.xml   # element tree
  adb shell input tap <x> <y>      # or: input text "...", keyevent KEYCODE_BACK
  ```
  Read the element tree for text and bounds instead of guessing coordinates from the image.
- **Flows:** Maestro, with YAML flows committed in the repo (e.g. `.maestro/login.yaml`: `launchApp`, `tapOn: "Log in"`, `inputText`, `assertVisible`). Run `maestro test .maestro/`; `maestro hierarchy` shows the current screen's elements. Use `clearState: true` or a fresh install, never the user's real app data.
- **Restrictions and costs:** the emulator needs hardware acceleration (Windows Hypervisor Platform), roughly 10 GB+ for the SDK and a system image, and several GB of RAM. Maestro needs Java 17+ (`JAVA_HOME` set); on Windows install it from the release zip on PATH. Check these before suggesting an emulator run.

## Compose Desktop / Multiplatform

- **UI tests** run headless: `runComposeUiTest { setContent { App() }; onNodeWithText("Save").performClick() }`. Dependencies: `compose.uiTest` in the common test source set, `compose.desktop.currentOs` in the desktop one. The API is still marked experimental, so check the project's Compose version.
- **Screenshots without a window:** render offscreen with `ImageComposeScene(width, height) { App() }.render()` and save the image to `.output/screenshots/`. Use fixed sizes, fonts, and data so images are stable.
- **The real window:** `./gradlew run`, then screenshot only through computer use or the user, which is slower and costs more. Use it only for checks the offscreen render can't show (native menus, tray, window chrome).

## Every platform

- Fix the inputs that make screenshots unstable: time, random seeds, animations (disable them or emulate reduced motion), network data (mock it), fonts.
- One re-run to tell a flake from a real failure; report flakes.
- Never use real accounts or real user data; use seeded test data and throwaway profiles.
