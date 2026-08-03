---
name: review-team
description: Spawn a team of subagents to review a codebase for correctness bugs plus reuse/simplification/efficiency issues, adversarially verify each finding, and produce a ranked report. Use for a multi-agent or scaled code review ("review this thoroughly", "N agents to review"), especially on a large diff or repo where a single pass under-covers. Optionally applies confirmed fixes with --fix.
---

# /review-team

Multi-agent code review. **All orchestration mechanics live in `guidelines/subagent-orchestration.md` — follow it** (shared `findings.json`, model settings, adversarial verify, dedup, stop conditions, Workflow tool, opt-in mutation). This skill only defines the review-specific lenses and output.

## Usage

```
/review-team <path|diff> [--agents N] [--model ...] [--verify all|blockers|none] [--focus "..."] [--fix]
```

`--fix` = opt-in apply of confirmed fixes (mutation — see the guideline). Default: review only, present the report, stop.

## Finder lenses (one scope + one lens per agent)

- **correctness** — real bugs: logic errors, null/edge cases, async/races, unhandled error paths.
- **reuse/duplication** — duplicated logic, a shared utility that should have been used, copy-paste drift.
- **simplification/altitude** — over-abstraction, dead code, a simpler equivalent, needless indirection.
- **efficiency** — needless work, N+1 queries, avoidable re-renders/allocations, quadratic loops.
- **contracts/types** — wrong types, `any`, unsafe assertions, public-API-contract traps.

Assign each agent a distinct module/directory slice; weight scopes by `--focus`. Add finders for big repos, drop lenses that don't apply.

## Verify → output

Adversarial refute-mode per finding (guideline). Render `volN.md` + a report ranked confirmed-first, blocker→minor. Complements the built-in single-pass `/code-review` — reach for `review-team` when the surface is large enough to need parallel coverage.
