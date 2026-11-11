---
packages: [core]
type: feat
---

# Design directions: a catalog of looks and 3D/shader recipes

New on-demand guideline `design-directions.md` that the design brief picks from, so UI work starts from a deliberate direction instead of generic defaults.

- **Motion budget by context:** app work screens get feedback and continuity motion only; app moments (login, empty states, the assistant's idle/listening/thinking state) get one ambient 3D or shader element; marketing pages get 1–2 strong moments. Android native uses Compose animations and AGSL shaders, not three.js.
- **Seven directions:** calm product (default for admin/framework apps), living assistant (default for the AI assistant), editorial, dark luxe, soft glass, scroll story, retro/dither. Each has type, color, motion character, 3D/shader choice, and what to study.
- **Eight recipes:** shader image hover, text reveal, gradient-noise background, particle presence, scroll camera, glass object, dither pass, page transition. All with fallbacks and resource disposal.
- **Renderer default for new 3D:** three.js `WebGPURenderer` with TSL, automatic WebGL 2 fallback.

## Changes to existing behaviour

- **Design briefs** now start from a direction and the context's motion budget. Watch that work screens don't get ambient 3D.
- **New three.js work** defaults to `WebGPURenderer` + TSL; existing `WebGLRenderer` code with custom `ShaderMaterial` or `EffectComposer` stays as is until deliberately ported.
