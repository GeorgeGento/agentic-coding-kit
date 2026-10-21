# Coding Standards

General, language-agnostic standards for writing and editing code. Read this before any code change. Language-specific rules live in [`languages/`](languages/README.md) (index per language); framework-specific rules in [`angular-frontend.md`](angular-frontend.md) and [`backend-nodejs.md`](backend-nodejs.md).

## Core principles

- **No code duplication** unless genuinely required — i.e. two things that *look* alike but are semantically independent and will evolve separately. Extract shared logic into utilities, base classes, or reusable components.
- **Modularity and reusability first.** Design every new piece so it can be reused, not welded to its first consumer.
- **Long-term maintainability** outweighs short-term convenience. Prefer the design that will still make sense in a year.
- **Single Responsibility.** Each function, class, and component has one reason to change. Split large units into smaller composable ones.
- **Immutability by default.** Don't mutate inputs, props, or shared state in place — create new objects/arrays and assign. (Framework specifics, e.g. Angular signals, in the frontend guide.)
- **Errors at boundaries only.** Validate and handle errors where untrusted data enters (API edges, I/O, user input). Don't wrap internal calls in defensive `try/catch` "just in case".
- **Shared packages hold only what is shared.** A symbol goes in a shared/common package only when 2+ consumers use it; single-consumer types and constants stay local to that package.

## Naming & clarity

- **Meaningful, self-documenting names.** A good identifier beats a comment.
- **Field/property names camelCase; string constant values kebab-case** (statuses, types, modes — e.g. `completionMode: 'required-only'`). The project's existing convention wins.
- **No magic numbers or strings.** Hoist them to named constants (in JS/TS: `as const` objects, see [javascript-typescript](languages/javascript-typescript.md)).
- Prefer clear code over clever code. Optimise for the next reader.

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
- **Half-finished migrations** — a renamed folder with one straggler import, a feature split across old and new locations, mappers/types that disagree. After moving or splitting directories, grep tooling config (lint overrides, package scripts, CI paths, tsconfig `paths`, test globs) for the old path: a glob that matches nothing fails silently.

When grouping imports, **use the highest available barrel** (`from './enums'`, not `from './enums/foo/bar.enum'`) and **merge consecutive imports from the same module** into one statement.

Surface findings explicitly: list what you found, classify by severity, fix the high-priority ones or get a steer before bulk-changing.

## Porting & migrations

- **Port, don't reinvent.** When moving a feature to a new stack/codebase, start from the existing implementation: keep its UI and behavior, and change only the wiring (imports, providers, types). Write something new only when the user agrees the old one shouldn't carry over.
- **The target contract is the source of truth.** Before mapping a field, verify the target backend actually emits it (schema/DTO/mapper). A field the API never sends is dead code — don't add types for it. If something needed is missing from the contract, stop and ask.

## Throwaway & helper scripts

- Write codemods, one-off migration scripts, and mass-edit helpers to the **active project root** (so they show up in git status and the user can review them) — not `/tmp` or `$HOME`.
- **Delete the script once the task is done**, before reporting complete. Never leave stray scripts scattered around.
- **Scripted rewrites of data/config files** (JSON/YAML form definitions, settings, schema setups, seeds) need the user's approval per case: prompt first, offering individual reviewable edits as the alternative. Read-only scripts that scan or verify such files are always fine.
- **All generated output in one git-ignored folder.** Test results, Playwright reports/traces, screenshots, coverage, logs → `.output/<tool>/` at the repo root (or the project's existing convention). Never create ad-hoc output dirs. Ensure `.output/` and `.team/` are in `.gitignore` before the first run that writes there; never commit generated output.
- Pure scratch files that the user never needs to see may use the session scratchpad instead.

## Before you call it done

- Run the project's **format / lint / build / test** commands that exist in the repo.
- Re-read your own diff: did you leave debug logging, commented-out code, or orphaned imports/variables your change created? (Remove only what *your* change orphaned — never pre-existing dead code without asking.)
