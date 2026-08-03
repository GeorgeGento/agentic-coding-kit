---
name: test-team
description: Spawn a team of subagents to find test gaps and write the missing tests — map public API/behavior against existing coverage, then generate happy-path, edge, error, and security cases per the testing guideline, running them until green. Use for "add tests", "cover this with tests", "improve coverage" across a module or repo. Mutates the repo (adds test files) — requires explicit go.
---

# /test-team

Multi-agent test authoring. **Follow `guidelines/subagent-orchestration.md`** for mechanics, and treat **`guidelines/testing.md`** as the standard for what to cover and how. This skill defines gap-finding and the write loop.

## Usage

```
/test-team <path> [--agents N] [--model ...] [--focus "..."]
```

**Mutating** (adds/edits test files). Finding gaps is safe; writing tests requires explicit go.

## Gap finding (one scope per agent)

Each agent maps its module's public API / observable behavior against existing tests and records under-tested units in `.team/findings.json`: what's untested, the realistic scenarios missing (happy / edge / error / security / concurrency per the testing guideline), and the risk if it breaks. Prioritize by risk, not line count.

## Write loop

1. Match the project's existing test framework and conventions — never introduce a second runner.
2. One author agent per module/unit: write behavior-named tests covering the identified scenarios; deterministic only (fake clock/random/network, isolate state).
3. **Run them** — tests must pass and actually exercise the behavior (not trivial pass-throughs). A bug uncovered while testing is a finding to surface, not to paper over.
4. Summarize new tests + what's now covered. Don't weaken assertions to make a suite pass.
