# Motion & 3D

Read before adding animation, scroll effects, transitions, canvas/WebGL, or three.js. Motion and 3D must look deliberate and stay fast. Generic fade-ins on everything and a spinning cube are the "AI slop" version: avoid them.

## Direction first

- Motion follows the **design brief** ([ux-ui-seo](ux-ui-seo.md#design-direction)): what moves, why, how fast, which easing. Every animation has a job: guide attention, show cause and effect, keep context across a change, or add one signature moment. No job, no animation.
- **One signature moment per screen** (a hero reveal, a 3D scene, a shared-element transition), with everything else calm. Uniform motion on every element reads as template.
- Define motion tokens once: durations (e.g. 120 / 240 / 400 ms), 2–3 named easings, and the stagger step. Reuse them; no one-off `0.37s ease-in-out`.

## Choosing the tool

| Need | Use |
| --- | --- |
| Enter/leave, hover, state changes | Native CSS transitions/keyframes. Angular: `animate.enter` / `animate.leave` (v20.2+). `@angular/animations` is deprecated since v20.2, so don't add it to new code |
| Route or layout changes keeping context | View Transitions API (Angular router `withViewTransitions()`), with a fallback where unsupported |
| Timelines, sequencing, scroll-driven scenes, SVG morphing | GSAP (free, including all plugins; not open source: its licence forbids building Webflow competitors). Use `gsap.context()` / `matchMedia()` and revert on destroy |
| Simple scroll-linked effects | CSS scroll-driven animations (`animation-timeline: view()`) where supported, else GSAP ScrollTrigger |
| 3D scenes | three.js directly, or `angular-three` for a declarative Angular API. React projects: React Three Fiber + Drei |

Check the project's framework version before picking an API, and check what the project already uses before adding a library (dependency review applies). For API depth, the `gsap-skills` (official) and `threejs-skills` bundles from `/setup` can be installed into the project that uses them.

## Performance (part of correctness)

- **Animate only `transform` and `opacity`** (and `filter` sparingly). Never animate `width`, `height`, `top`, `left`, or `box-shadow` on large areas. `will-change` only during the animation, then remove it.
- **Frame budget: 16 ms.** No layout reads inside animation frames (batch reads before writes). Run animation loops **outside Angular change detection** (`NgZone.runOutsideAngular`, or zoneless with no signal writes per frame).
- **three.js:**
  - **Lazy-load the 3D chunk:** a dynamic `import()` behind the route or after first paint. three.js adds roughly 150 KB+ gzipped.
  - **Render on demand** (when something changed) instead of a constant `requestAnimationFrame` loop, unless the scene is genuinely continuous. Pause when the tab is hidden or the canvas is off-screen (`IntersectionObserver`).
  - **Cap the pixel ratio:** `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))`.
  - **Reuse resources:** `InstancedMesh` for repeated objects; share geometries and materials. Compress assets (Draco/Meshopt for geometry, KTX2 for textures).
  - **Dispose everything on destroy:** geometries, materials, textures, render targets, controls, the renderer, and event listeners. Leaks here are the #1 three.js bug.
  - **Resize** with a `ResizeObserver` on the container, not `window.onresize`.
- Measure: Chrome Performance panel or `stats.js` during development. No dropped frames on a mid-range laptop is the bar; check a throttled CPU (4x) for anything on a public page.

## Accessibility

- **Always honour `prefers-reduced-motion`.** Reduce to opacity or instant changes; stop autoplaying, parallax, and camera motion. In GSAP use `gsap.matchMedia()`.
- Nothing essential lives only in motion or only in the 3D canvas: provide text, labels, or a static fallback. The canvas gets `role="img"` with an `aria-label`, or a described alternative.
- No flashing more than 3 times per second. Motion must not block input; interactive elements stay focusable and keyboard-operable.
- Provide a fallback when WebGL is unavailable (a static image or simplified view).

## Testing

- Unit-test the logic (state machines, timelines' start/end states), not the frames.
- **Visual regression** with Playwright `toHaveScreenshot` for key states. Disable or finish animations first (`animations: 'disabled'`, or `emulateMedia({ reducedMotion: 'reduce' })`), and wait on a "scene ready" signal, not on timeouts.
- **WebGL in headless browsers** needs software rendering (e.g. Chromium `--use-angle=swiftshader` / `--enable-unsafe-swiftshader`). Fix random seeds, camera, and time so screenshots are stable, and allow a small `maxDiffPixelRatio` for GPU differences. Expect flakes here first: re-run once before calling it a real failure.
- Check memory: mount and unmount the 3D view a few times and confirm the heap and `renderer.info.memory` return to baseline.
