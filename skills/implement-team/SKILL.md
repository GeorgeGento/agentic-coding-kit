---
name: implement-team
description: Spawn a team of subagents to implement a spec, task list, or approved plan in parallel — decompose into independent tasks, build each in an isolated worktree, verify with lint/build/tests, and merge in dependency order. Use when the user has an agreed plan or a list of changes and wants it built by multiple agents ("implement these", "build the plan with agents"). Mutates code — requires explicit go.
---

# /implement-team

Multi-agent parallel implementation. **Follow `guidelines/subagent-orchestration.md`** for mechanics (worktree isolation, `depends_on` ordering, verify-after-each, single-writer state). This skill defines decomposition and the build loop.

## Usage

```
/implement-team <spec|tasklist|volN.md> [--agents N] [--model ...]
```

**Mutating.** Producing the task breakdown is safe; applying it requires explicit go (the invocation itself, or "implement it"). Confirm the plan before writing code unless the user already approved it.

## Input

A spec, a task list, or a `volN.md` from `review-team`/`security-team`. Each item must reduce to a concrete change with acceptance criteria; if the input is vague, resolve it to discrete tasks and confirm before building.

## Build loop

1. **Decompose** into independent tasks with a `depends_on` graph; record in `.team/findings.json` (each task an id).
2. **Build in parallel** — one builder agent per independent task, each in an isolated worktree (Workflow `isolation: 'worktree'`). Dependency chains run in order. Each builder gets a self-contained brief: the task, acceptance criteria, the files it may touch, and the conventions (point it at the relevant guideline — Angular/backend/etc.).
3. **Verify each** — run the project's lint/build/tests for the change; a builder isn't done until its slice is green and matches acceptance criteria.
4. **Merge** in `depends_on` order; re-run the full suite after merge; fix regressions the tests catch.
5. **Summarize** — what landed, test results, anything deferred. Never declare done with failing/missing tests (see [testing](../../guidelines/testing.md)).
