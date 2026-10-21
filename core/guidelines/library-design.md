# Library & Framework Design

Read when authoring a reusable package (framework, UI kit, shared library) that other apps consume. App code rules stay in [coding-standards](coding-standards.md).

## Configuration

- **No hidden defaults.** Behavioural, security and data options (seeds, hooks, auth strategies, secrets, permission sets, captcha) are required. Validate them at bootstrap and throw an error that names the missing option. Cover each throw with a test. A consumer must never debug behaviour they didn't configure.
- Safe ergonomic defaults (route path, page size) are allowed only when documented with `@default` in JSDoc. JSDoc every config option and mark the required ones.
- Seed engines ship zero built-in data; the consumer passes every seed set explicitly.

## Scope

- **Project-agnostic.** Ship utilities, ports, registries and hooks. Never persist app data: return normalized results and fire hooks (`onRequest`, `onResponse`, …) so the consumer stores what it wants. Message contracts and app events belong to the consumer.
- **Pages are consumer-side.** The library ships components and logic; apps compose the pages. Promote an assembled part into the library only when a second consumer needs it.
- **Authorize on permissions, not roles.** No built-in super-admin bypass and no behaviour keyed on a role name. The library may declare which permission key its own endpoints require. Roles and grants are consumer data, so never seed them.

## UI kits

- Components are self-contained: styles live in compiled component styles off CSS variables, with no reliance on the consumer's utility-CSS setup or resets. Any utility-CSS bridge is a separate, optional entry.

## Packaging

General rules, any ecosystem:

- **A consumer installs only what it uses.** Heavy or optional dependencies (DB drivers, auth stacks, editors) sit behind their own artifact or opt-in switch, never forced on small consumers.
- No "install everything" bundle when consumers include small services; consumers list the parts they need.
- Dependencies only point down: base packages never depend on feature packages.
- Derive build/publish order from the dependency graph; never hardcode it.
- Version the parts in lockstep unless they genuinely release independently.

### npm

- npm can't declare dependencies per subpath, so a **required peer means a separate package**. Optional peers (`peerDependenciesMeta`) keep heavy features opt-in.
- Framework-level deps (`@angular/*`, `@nestjs/*`, `rxjs`) are peers, never direct dependencies, so the consumer has exactly one copy.

### Gradle (Kotlin / Java)

- The unit is the module (one published artifact): split heavy integrations into their own module.
- Declare dependencies with `implementation`; use `api` only for types consumers must see, so internals don't leak onto their classpath.
- Share versions through a version catalog (`libs.versions.toml`) or a BOM, not repeated literals.

### Cargo (Rust)

- Gate heavy or optional dependencies behind **features** (`optional = true` + `[features]`); keep `default` features minimal. Split into a separate crate only when it must version or publish independently.
- Depending on another crate, set `default-features = false` and enable only what you use.
- Keep related crates in one workspace with shared `[workspace.dependencies]` versions.

## Local development against consumers

- Test a library against a real consumer before publishing, without hand-editing the consumer's manifests in ways that can be committed by accident.
- **npm:** `npm link` and Windows junctions can load a **second copy of the framework** in a dev server's dependency optimizer (Angular: `NG0203`) even though the production build is fine. Hard-copy the built `dist` into the consumer's `node_modules` (no nested `node_modules`) instead of linking.
- **Gradle:** use a composite build (`includeBuild`) instead of publishing to `mavenLocal`.
- **Cargo:** use a `path` dependency or a `[patch]` section, kept out of commits.
