# Coding Standards

General, language-agnostic standards for writing and editing code. Read this before any code change. Framework-specific rules live in [`angular-frontend.md`](angular-frontend.md) and [`backend-nodejs.md`](backend-nodejs.md).

## Core principles

- **No code duplication** unless genuinely required — i.e. two things that *look* alike but are semantically independent and will evolve separately. Extract shared logic into utilities, base classes, or reusable components.
- **Modularity and reusability first.** Design every new piece so it can be reused, not welded to its first consumer.
- **Long-term maintainability** outweighs short-term convenience. Prefer the design that will still make sense in a year.
- **Single Responsibility.** Each function, class, and component has one reason to change. Split large units into smaller composable ones.
- **Immutability by default.** Don't mutate inputs, props, or shared state in place — create new objects/arrays and assign. (Framework specifics, e.g. Angular signals, in the frontend guide.)

## Naming & clarity

- **Meaningful, self-documenting names.** A good identifier beats a comment.
- **No magic numbers or strings.** Hoist them to named constants or enums.
- Prefer clear code over clever code. Optimise for the next reader.

## TypeScript standards

- **`strict: true`.** No `any` — use `unknown` + narrowing, or a proper union/generic. If `any` is truly unavoidable, isolate and comment why.
- **Explicit return types** on every exported function, method, and `computed()`.
- **No `as any` / `as unknown as X`** to silence the compiler — fix the underlying type.
- **Errors at boundaries only.** Validate and handle errors where untrusted data enters (API edges, I/O, user input). Don't wrap internal calls in defensive `try/catch` "just in case".

## Documentation (JSDoc)

- **JSDoc every exported JS/TS function** with an `@example` block — **unless** the name is self-explanatory from its signature (e.g. `isEmpty(arr)`, `toKebabCase(str)`). When in doubt, add it.
- JSDoc explains **why / how to use**, not what the code literally does.

## Comments

- **Never delete or rewrite existing comments** except to correct one that is wrong or unclear; preserve the original intent.
- Add comments for non-obvious logic, side effects, and "why" decisions. Never add comments that just restate the code.

## Proactive hidden-issue detection

Don't stop at "it compiles." During substantive changes, hunt for and surface these — fix the high-confidence ones, ask before bulk changes:

- **Name collisions** (same symbol as interface vs enum vs class; same export from multiple files). **Resolve by renaming** the non-canonical side to something clearer — not by import-path workarounds.
- **Duplicate exports / duplicated implementations** across modules (two `deepMerge`s, two DTOs with the same name). Dedupe to one canonical and re-export if needed.
- **Bypasses** — `@ts-ignore`, `@ts-expect-error`, `eslint-disable`, `as any`, suspicious assertions. Each is a flag: investigate and remove if the real issue can be fixed.
- **Stale shims / "moved to X" re-exports** — artifacts of an unfinished migration. Either finish the migration or document why the shim must stay.
- **`TODO` / `FIXME` / `HACK` / `XXX`** — surface them; ask whether to resolve now or leave with a real ticket reference.
- **Half-finished migrations** — a renamed folder with one straggler import, a feature split across old and new locations, mappers/types that disagree.

When grouping imports, **use the highest available barrel** (`from './enums'`, not `from './enums/foo/bar.enum'`) and **merge consecutive imports from the same module** into one statement.

Surface findings explicitly: list what you found, classify by severity, fix the high-priority ones or get a steer before bulk-changing.

## Throwaway & helper scripts

- Write codemods, one-off migration scripts, and mass-edit helpers to the **active project root** (so they show up in git status and the user can review them) — not `/tmp` or `$HOME`.
- **Delete the script once the task is done**, before reporting complete. Never leave stray scripts scattered around.
- Pure scratch files that the user never needs to see may use the session scratchpad instead.

## Before you call it done

- Run the project's **format / lint / build / test** commands that exist in the repo.
- Re-read your own diff: did you leave debug logging, commented-out code, or orphaned imports/variables your change created? (Remove only what *your* change orphaned — never pre-existing dead code without asking.)
