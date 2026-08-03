---
name: refactor-team
description: Spawn a team of subagents to find refactor targets (duplication, over-long units, poor seams, dead code, weak names) and apply behavior-preserving refactors verified by the test suite. Use for "clean this up", "refactor this module", "reduce duplication" at scale. Mutates code — behavior-preserving only, tests must stay green — and requires explicit go.
---

# /refactor-team

Multi-agent refactoring. **Follow `guidelines/subagent-orchestration.md`** for mechanics, and **`guidelines/coding-standards.md`** for what "better" means here. This skill defines target-finding and the safe-apply loop.

## Usage

```
/refactor-team <path> [--agents N] [--model ...] [--focus "..."]
```

**Mutating.** Finding targets is safe; applying requires explicit go.

## Guardrails (non-negotiable)

- **Behavior-preserving only.** No feature changes, no API/route/export/DB-field renames without a separate explicit ask.
- **Tests are the safety net.** The suite must pass before and after each refactor. If a module has no tests covering the behavior being moved, add characterization tests first (or flag it and skip) — never refactor blind.

## Find (one scope + one lens per agent)

Targets: duplicated logic to extract, over-long functions/classes to split (single responsibility), poor seams (hard-to-test → inject/return-value), dead code, unclear names, magic values. Record each in `.team/findings.json` with the proposed change and its blast radius.

## Apply loop

Independent refactors run in isolated worktrees (guideline). Each: apply → run lint/build/tests → confirm behavior unchanged → merge in `depends_on` order. Surface anything that turns out to be a real bug (not a smell) as a finding rather than silently "fixing" it. Summarize what changed and why.
