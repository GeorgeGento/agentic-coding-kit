# Debugging

Read when a test fails, a bug is reported, or behavior surprises you. **Find the root cause before changing code.** Guess-and-retry burns tokens and hides the real problem.

## The loop

1. **Reproduce.** Get a failing test or a deterministic repro first. If you can't reproduce it, say so and gather evidence (logs, inputs, environment) instead of guessing.
2. **Baseline.** Check whether the failure already exists on HEAD (a clean `git worktree`, never `git stash`). A failure that predates the change says nothing about it.
3. **Hypothesis.** State one specific cause: "X is null because Y runs before Z".
4. **Evidence.** Confirm or kill the hypothesis by reading code, adding a targeted assertion or log, or narrowing the input. One variable at a time.
5. **Root cause.** Trace back to where the wrong value or state *originates*, not where it surfaces.
6. **Fix surgically** at the origin, with a regression test that fails before the fix and passes after.

## Rules

- Never change code "to see if it helps". Each edit tests a stated hypothesis.
- Two failed hypotheses in a row: stop, list what you know and what you ruled out, and widen the search (or escalate) instead of a third guess.
- Never weaken an assertion, add a retry, or catch-and-ignore to make a test pass.
- Flaky? Re-run the single test once to confirm the flake, then find the nondeterminism (time, order, shared state, network, waiting on timers instead of conditions).
- Remove temporary logs and assertions before reporting.
