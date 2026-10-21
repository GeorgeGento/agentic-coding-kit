# Angular & Frontend

Read for Angular, frontend architecture, and Tailwind. Targets **Angular 22** (latest stable; v21/v20 in LTS) and **Tailwind CSS 4**. General code rules live in [`coding-standards.md`](coding-standards.md); UX rules in [`ux-ui-seo.md`](ux-ui-seo.md).

## Components & architecture

- **Standalone** components / directives / pipes. No `NgModule` for new code.
- Keep components lean: components coordinate UI state; services handle API access + domain logic; pure helpers do formatting/calculation.
- **One component per folder** with separate `.ts`, `.html`, and `.scss`. Folder name = selector root (kebab-case). No inline `template`/`styles` for reusable or non-trivial components (throwaway single-file demos excepted).
- `ChangeDetectionStrategy.OnPush` on every component (zoneless-ready).

## Signals-first state

- Use `signal()` / `computed()` / `effect()` / `input()` / `output()` / `model()`. Prefer signals over `BehaviorSubject` for local state; use RxJS where streams are the natural fit (HTTP, user events).
- **Angular 22 runs zoneless by default** — plain (non-signal) properties don't trigger template re-render. Anything bound in a template must be a signal.
- Immutability: never mutate a signal's value in place — set/update with a new reference.
- Never `.set()` a signal inside `computed()` (NG0600), and never read and write the same signal in one `effect()` — build the value in a local variable, then set once.
- Drop `ngOnInit` / `ngAfterViewInit` when a signal, `computed`, or `effect` does the job; use lifecycle hooks only when genuinely right (e.g. DOM measurement after view init).

## Dependency injection & extensibility

- **Use DI for dynamic injection and extensibility — don't hardcode dependencies.** Prefer `inject()` over constructor injection (cleaner, tree-shakes better, works in base classes and functions).
- **Program to an abstraction:** define an `InjectionToken` (or abstract class) for a capability, inject the token, and provide the concrete implementation. This lets implementations be swapped or extended **without editing consumers**.
- Provide dynamically with `useClass` / `useFactory` / `useValue` / `useExisting`. Use `providedIn: 'root'` for singletons; route- or component-level `providers` for scoped instances.
- Centralize cross-cutting config as injected tokens rather than imported constants, so apps and libraries can override them.

## Control flow & bindings

- New control flow `@if` / `@for` / `@switch` — never `*ngIf` / `*ngFor` / `*ngSwitch`. Always include `track` in `@for`.
- Native `[class]` / `[style]` bindings — not `NgClass` / `NgStyle`.

## Forms & HTTP

- Typed reactive forms for non-trivial forms. (Angular 22 **Signal Forms** are now stable — use them where they fit.) Frontend validators must match backend constraints; add `maxlength`, clear inline errors, and disabled/loading state during submit.
- `HttpClient` with typed request/response models, interceptors for auth/error concerns, and centralized API services. No scattered `fetch` calls across components.

## Routing

- Lazy-load routes via `loadComponent` / `loadChildren` by default.

## Tailwind CSS 4 setup (Angular)

Tailwind 4 needs a PostCSS config, or all directives pass through unprocessed and the page renders unstyled:

1. `npm install -D tailwindcss@4 @tailwindcss/postcss@4`
2. Create `.postcssrc.json` next to `angular.json`:
   ```json
   { "plugins": { "@tailwindcss/postcss": {} } }
   ```
3. In `src/styles.css`: `@import "tailwindcss";`

No `tailwind.config.js` — Tailwind 4 uses CSS `@theme` blocks.

## Accessibility

- Semantic HTML, ARIA where needed, and keyboard navigation for every interactive element. (More UX detail in [`ux-ui-seo.md`](ux-ui-seo.md).)
