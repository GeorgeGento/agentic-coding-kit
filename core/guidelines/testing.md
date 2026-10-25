# Testing & Testability

Read when writing code or tests, or verifying behavior. **Testing is part of "done", not an afterthought.**

## Design for testability

- **Everything should be testable.** Structure code so it can be tested without heroics: pure functions for logic, DI for swapping collaborators (see [angular-frontend](angular-frontend.md) / [backend-nodejs](backend-nodejs.md)), thin controllers with logic in services, formatting in pure helpers, no hidden global state, side effects pushed to the edges.
- If something is hard to test, treat it as a **design smell** — add seams (inject dependencies, return values instead of mutating, isolate I/O) rather than reaching for elaborate mocking.

## What to cover

Write as many tests as needed to cover **every realistic scenario** — driven by behavior, not by a line-coverage number. For each unit/feature, cover:

- **Happy path(s)** — the expected use.
- **Edge cases** — empty, null/undefined, zero, negative, boundary values, max length, large inputs, unicode.
- **Error/failure paths** — invalid input, thrown errors, rejected promises, timeouts, missing resources.
- **Security cases** — authorization denied, injection/unknown-field rejection, validation failures (see [security](security-privacy-logging.md)).
- **Concurrency/ordering** where relevant — races, retries, idempotency.
- **Regressions** — every bug fix gets a test that fails before the fix and passes after.

Test **observable behavior and contracts**, not implementation details, so tests survive refactors. Don't test trivial pass-throughs or the framework itself.

**Unsure what the logic should do? Ask before writing its test.** Never encode a guessed expectation — a wrong test locks in a bug. Batch these questions (structured prompt if the harness has one) rather than stopping per test.

## Test levels (testing pyramid)

- **Unit** — pure logic, services, utilities, pipes. Fast, isolated, the bulk of the suite.
- **Integration** — modules with real collaborators (DB, repositories), API/controller endpoints.
- **E2E** — only the critical user journeys through the running app.

Many unit, fewer integration, fewest E2E.

## Practices

- **Tests are part of "done":** implement → test → verify → then commit on request. Never declare new behavior complete with missing or failing tests.
- **Deterministic only:** no reliance on real wall-clock time, randomness, network, or test order. Fake the clock, seed randomness, mock external services, isolate state between tests (fresh fixtures, no shared mutable state).
- **Name by behavior** ("returns 401 when token missing"); arrange–act–assert; keep each test focused.
- **Realistic fake data only** — never real PII or production data in fixtures (see [security](security-privacy-logging.md)).
- Run the suite before pushing; never push failing tests (see [git-and-versioning](git-and-versioning.md)).
- **Run narrow while iterating.** Only the specs/package you touched, with a path filter and low worker count (e.g. jest `--maxWorkers=1`). In a monorepo, build/typecheck only the affected project(s) — never `run-many --all` or every package's suite in one command. Run the full suite **once**, at the end of the task.
- **Two gate levels, both scripted.** A *partial gate* checks one task's slice: lint, type-check and tests for the touched package/files (plus touched e2e/UI specs). Agents and the Lead run it. The *full gate* (build + lint + every suite over the whole tree) runs once, when all work is marked ready. Both are committed scripts in the project (e.g. a scope argument for the partial gate) that write to `.output/`, not ad-hoc commands. Dedupe steps (if `npm test` already runs e2e, don't add a separate e2e step), skip browser/UI suites when the diff touches no UI paths, and abort if required ports are busy instead of killing a server. When a browser test fails, re-run just that test once to tell a flake from a real failure, and report flakes.
- **Full suite before commit (user may skip).** When the user asks to commit, first prompt them (structured question if the harness has one): run the full suite now (recommended) or skip. If skipped, say so in the commit report.
- **Baseline before blaming.** When a suite fails, check whether the failure already exists on HEAD (clean checkout via `git worktree add <tmp> HEAD`, never `git stash`) and report which failures pre-exist. Pre-existing failures say nothing about your change.
- Match the project's existing test framework — don't introduce a second one.

## Stack tooling

- **Node / NestJS:** Jest or Vitest + the NestJS testing module; `supertest` for HTTP/controller tests; `mongodb-memory-server` or a disposable test DB for repository/integration tests.
- **Angular:** the project's configured runner (Jest/Vitest or Karma/Jasmine); component tests via Testing Library / component harnesses; assert signals/`computed` through their public effects; mock HTTP with `HttpTestingController`.
