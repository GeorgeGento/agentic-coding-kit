---
name: feature-team
description: End-to-end feature delivery by chaining subagent teams — architect (analyze-team) → plan (human gate) → build (implement-team) → check (review-team + security-team) → cover (test-team). Use in a design session when the user wants a feature taken from idea to tested implementation with multi-agent help at each stage. Stops for approval after the architecture/plan before writing any code.
---

# /feature-team

Conductor that chains the `*-team` skills to take a feature from idea → architected → built → checked → tested. **Follow `guidelines/subagent-orchestration.md`** for all shared mechanics; each phase delegates to the matching team skill rather than reimplementing it. Shared state lives in `<path>/.team/` so context flows between phases.

## Usage

```
/feature-team "<feature description>" [path] [--model ...] [--auto-after-plan]
```

Best driven from an Opus session (the architecture reasoning benefits from it). `--auto-after-plan` skips the approval gate — use only when the user explicitly wants unattended end-to-end.

## Phases

### 1. Architect — `analyze-team`
Run `analyze-team` scoped to the areas the feature touches: existing patterns, extension points, constraints, affected modules. Its map feeds the plan. (If `graphify-out/` exists, query it first.)

### 2. Plan — synthesize + **GATE**
From the architecture, write a concrete plan to `.team/plan.md`: the design, a task breakdown with `depends_on`, files to touch, acceptance criteria, and risks. **STOP and present the plan for approval. Do not write feature code until the user approves** (per the [workflow](../../guidelines/workflow.md) guideline — architecture is cheap to revise on paper, expensive after code). `--auto-after-plan` is the only bypass.

### 3. Build — `implement-team`
On approval, hand `.team/plan.md` to `implement-team`: parallel worktree build, verify each task, merge in dependency order.

### 4. Check — `review-team` + `security-team` (parallel)
Run both over the new/changed code. Consolidate confirmed findings. If a blocker surfaces, loop back — fix via `implement-team`, then re-check. Minor/disputed items go to the report for a human call.

### 5. Cover — `test-team`
Write the missing tests for the new behavior (happy/edge/error/security per the [testing](../../guidelines/testing.md) guideline); run to green.

### Final
Summarize: what was built, the architecture decisions, check findings + resolutions, test results, anything deferred. Leave the feature branch for the user to review and commit — **never auto-commit**.

## Notes

- Each phase is a real team run (schema-validated findings, adversarial verify where it applies) — not one agent pretending to be a team.
- Model: give architecture and plan synthesis opus; delegate mechanical build/test phases to sonnet. Configurable per the guideline.
- The plan gate is the entire point of the flow. Honor it unless explicitly told otherwise.
