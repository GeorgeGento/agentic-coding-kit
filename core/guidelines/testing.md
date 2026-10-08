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
- Match the project's existing test framework — don't introduce a second one.

## Stack tooling

- **Node / NestJS:** Jest or Vitest + the NestJS testing module; `supertest` for HTTP/controller tests; `mongodb-memory-server` or a disposable test DB for repository/integration tests.
- **Angular:** the project's configured runner (Jest/Vitest or Karma/Jasmine); component tests via Testing Library / component harnesses; assert signals/`computed` through their public effects; mock HTTP with `HttpTestingController`.
