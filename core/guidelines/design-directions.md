# Design Directions

Read when writing a design brief ([ux-ui-seo](ux-ui-seo.md#design-direction)) or choosing how a screen should look and move. Pick **one direction**, adapt it to the brand, and name its references and signature moment in the brief. These are starting points, not templates: never copy a site. Engineering rules for motion and 3D (performance, disposal, reduced motion, testing) are in [motion-3d](motion-3d.md).

## 1. The context sets the motion budget

Decide this first; it limits everything below.

| Context | Allowed | Never |
| --- | --- | --- |
| **App work screens** (admin, dashboards, forms, settings, chat transcripts) | Motion for feedback and continuity: state changes, enter/leave, shared-element transitions, skeletons, 120–240 ms | Ambient 3D, scroll-jacking, decorative loops, anything that delays input |
| **App moments** (login, onboarding, empty states, the assistant's idle/listening/thinking state, a "done" moment) | One ambient 3D or shader element, or one signature animation; pauses when hidden | More than one per screen, blocking the content |
| **Marketing / portfolio pages** | Scroll stories, shader images, 3D heroes: 1–2 strong moments per page, calm everywhere else | Effects on every section |

Platforms:
- **Tauri / Electron desktop:** web rules apply. WebView2 on Windows supports WebGPU.
- **Android (native Kotlin/Compose):** three.js doesn't apply. Use Compose animation APIs (`animate*AsState`, `AnimatedContent`, `updateTransition`, shared-element transitions), Lottie only for authored illustrations, and AGSL `RuntimeShader` (Android 13+) for ambient shader effects, with a static fallback below API 33. Battery and thermal budget come first.

## 2. Directions

Each one: when it fits · type (free fonts) · color · motion character · 3D/shader · study.

### Calm product: the default for app work screens
- **Fits:** admin, framework apps, settings, data-heavy screens.
- **Type:** one strong sans with tabular numbers (Inter Tight, Geist, IBM Plex Sans), tight scale, weight for hierarchy rather than size.
- **Color:** neutral surfaces with a quiet tint, one accent used only for primary actions and focus, semantic colors for status, real dark mode (not inverted).
- **Motion:** 120–240 ms, standard easing, enter/leave and layout continuity only; numbers count up only on first load.
- **3D:** none on work screens. Empty states and login may borrow a small *Gradient-noise background* (recipe C).
- **Study:** Linear, Vercel dashboard, Raycast, Stripe dashboard: density, alignment, and restraint.

### Living assistant: the default for the AI assistant
- **Fits:** the assistant's home, idle, listening, thinking, and speaking states.
- **Type:** a humanist sans for conversation (Inter, Manrope), a mono for tool output and code.
- **Color:** deep neutral base, one luminous accent per state (listening, thinking, error), soft glows rather than hard borders.
- **Motion:** the presence breathes: slow idle loop (4–8 s), faster reactive response to audio level and state changes; transcript and controls stay calm (calm-product rules).
- **3D / shader:** *Particle presence* (recipe D) driven by state and audio amplitude; on Android an AGSL shader orb with the same states.
- **Study:** voice-assistant idle states, Codrops particle tutorials, audio-reactive shader demos.

### Editorial
- **Fits:** docs landing pages, blog, portfolio, about pages.
- **Type:** an expressive serif display (Fraunces, Instrument Serif) with a clean sans for text; very large headings, generous line length control.
- **Color:** paper and ink, one accent.
- **Motion:** line-by-line text reveals, images unmasking on scroll.
- **3D / shader:** *Shader image hover* (recipe A), *Text reveal* (recipe B).
- **Study:** Codrops shader gallery tutorials, editorial magazine sites.

### Dark luxe
- **Fits:** premium product pages, launch pages.
- **Type:** a refined display serif or high-contrast sans, letter-spaced small caps for labels.
- **Color:** near-black base, warm metallic accent (gold or copper) used sparingly, subtle grain.
- **Motion:** slow and weighty (600–1200 ms), long easings, camera drifts rather than jumps.
- **3D / shader:** a single hero object with physical material and soft studio light, subtle bloom; *Scroll camera* (recipe E) for the product story.
- **Study:** Awwwards Site of the Day product launches.

### Soft glass
- **Fits:** consumer apps, onboarding, settings for a polished desktop app.
- **Type:** rounded geometric sans (Manrope, Plus Jakarta Sans).
- **Color:** light, airy gradients; translucent panels with backdrop blur; sufficient contrast on every panel (check it).
- **Motion:** springy, short; panels lift and settle.
- **3D / shader:** *Gradient-noise background* (recipe C) behind frosted panels; *Glass object* (recipe F) for a hero.
- **Study:** current OS design languages' material and translucency guidance.

### Scroll story
- **Fits:** a product or feature explainer page.
- **Type and color:** follow the brand; chapters get their own accent.
- **Motion:** the page is a camera path; each chapter pins, plays, and releases. Text stays readable and selectable.
- **3D / shader:** *Scroll camera* (recipe E), chapter transitions with *Page transition* (recipe H).
- **Study:** Codrops scroll-driven 3D world tutorials, Awwwards scroll narratives.

### Retro / dither
- **Fits:** developer tools, technical brand pages, playful internal tools.
- **Type:** a monospace or grotesk (JetBrains Mono, Space Grotesk).
- **Color:** limited palette (2–4 colors), high contrast.
- **Motion:** stepped, snappy timing; no smooth easing.
- **3D / shader:** *Dither pass* (recipe G) over a simple 3D scene.
- **Study:** Codrops dithering explainer, demoscene-inspired sites.

## 3. Recipes

Each recipe follows [motion-3d](motion-3d.md): lazy-loaded, rendered on demand or paused when hidden, all GPU resources disposed on destroy, a `prefers-reduced-motion` and no-WebGL fallback.

**Renderer default for new 3D work:** three.js `WebGPURenderer` from `three/webgpu`, shaders in TSL from `three/tsl`. It falls back to WebGL 2 automatically. Call `await renderer.init()` before the first render. Test the WebGL 2 path with `forceWebGL: true`. Classic `ShaderMaterial` / `onBeforeCompile` / `EffectComposer` don't work with it: write node materials and TSL post-processing instead. Keep `WebGLRenderer` only where a project already depends on those.

- **A. Shader image hover/distortion:** a plane per image with a texture; a noise- or displacement-driven UV offset tied to pointer velocity and a 0→1 hover uniform tweened with GSAP. Keep the real `<img>` in the DOM for accessibility and SEO; the canvas is decoration. Fallback: CSS scale/opacity.
- **B. Text reveal:** GSAP `SplitText` into lines/words with masked line wrappers, staggered `yPercent` reveal. Optional shader letters for one headline only. The text stays real DOM text; reduced motion means appearing instantly.
- **C. Gradient-noise background:** a full-screen quad with animated simplex/curl noise mixing 2–3 brand colors, very slow time scale, low resolution render target upscaled (it's soft anyway). Cheapest ambient effect; pause off-screen.
- **D. Particle presence / sculpture:** instanced points (or `Points` with a TSL position node) morphing between target shapes stored as buffers; state (idle, listening, thinking) changes the target and noise amplitude, audio level drives scale or turbulence. Use compute shaders on WebGPU for large counts, with a lower-count WebGL fallback. Cap counts by device (e.g. 20k desktop, 5k low-end).
- **E. Scroll camera:** a `CatmullRomCurve3` camera path sampled by GSAP `ScrollTrigger` progress (scrub with smoothing); chapters pin with `ScrollTrigger`. Keep content sections real DOM over or between the canvas.
- **F. Glass object:** `MeshPhysicalMaterial` (or its node-material equivalent) with `transmission`, `thickness`, `roughness`, and an environment map; costly, so one object, a low-res transmission buffer, and a static image fallback on low-end devices.
- **G. Dither pass:** a post-processing pass (TSL) that quantizes luminance with an ordered (Bayer) matrix to a limited palette; render at reduced resolution and upscale with nearest filtering for crisp pixels.
- **H. Page transition:** the View Transitions API for DOM state (Angular router `withViewTransitions()`), with an optional WebGL handoff: capture the outgoing element's rect, animate a textured plane from it to the incoming layout, then swap. Without support, a plain cross-fade.

## 4. In the brief

Name the context row, the direction (adapted), 2–3 references with what to take from each, the recipe(s) used and where, the signature moment, and the fallback. Then build, run the look-compare-iterate loop, and have `ui-ux` review screenshots against the brief.
