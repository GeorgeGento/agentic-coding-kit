# Hierarchy Protocol

How work flows through the agent hierarchy: **Lead → Senior → Mid → Junior**. It works like a small engineering org. Work flows down as briefs, results flow up as reports, and **every level audits what comes up before passing it on**. Whoever delegates a piece of work is accountable for it.

Tiers are roles, not models. Which model fills each tier is set in a profile (`profiles/*.toml`), so this protocol works for any LLM set.

## Tiers

| Tier | Owns | Decides | Never |
| --- | --- | --- | --- |
| **Lead** | The conversation with the user, routing, final acceptance | What gets built, by whom, when to stop for the user | Writes or edits code itself |
| **Senior** | A workstream (feature, subsystem, cross-cutting change) | Architecture, task breakdown, acceptance criteria | Hands down a task without acceptance criteria |
| **Mid** | One task (component, endpoint, module change) incl. its tests | Implementation details within the brief | Changes architecture or public contracts without escalating |
| **Junior** | One fully specified unit (a test file, a small component, a mechanical edit) | Nothing beyond the brief | Guesses on ambiguity: it escalates |

## Routing: pick the lowest tier that can own it

Score the work. The **highest** signal decides the tier.

- **Senior**: ambiguous goal, touches several modules, changes a public API/schema/data model, security-sensitive, or hard to reverse.
- **Mid**: clear goal and one module, but real design choices inside it (state shape, query design, error handling).
- **Junior**: fully specified, local, mechanical, easy to verify (write these tests, add this field end-to-end per the pattern in X, rename Y).

**Skip levels for small work.** A one-file fix goes straight to a Mid or Junior. Don't route a typo through four tiers. **Don't delegate work smaller than the brief you'd write for it.** Do read-only lookups yourself.

**User-assigned tier wins.** If the user names who does a task ("lead, do it", "senior should handle this"), that tier does the work **itself** — no further delegation down. Lead → works solo for that request; Senior → implements directly instead of briefing Mid/Junior. It still audits its own diff and reports with evidence. The assignment covers that task only, not the session.

## Brief (down)

Every delegation is a self-contained brief. The receiver has no other context.

```
GOAL:        one sentence: the outcome, not the steps
SCOPE:       files/dirs you may touch; anything outside requires escalation
CONTEXT:     relevant decisions, patterns to follow (file:line), guidelines that apply
ACCEPTANCE:  verifiable checks, e.g. "tests X pass", "endpoint returns 404 on missing id", "query uses index {a:1,b:1}"
CONSTRAINTS: performance expectations (data size), no new deps, style/conventions
DONE MEANS:  lint + build + tests green for the slice; report in the format below
```

A brief without ACCEPTANCE is not a brief. If the receiver asks "which files?" or returns prose instead of a report, the brief was too thin. Fix the brief.

## Report (up)

```
STATUS:      done | blocked | escalate
CHANGES:     files touched + one line each
EVIDENCE:    commands run and their actual output (tests, lint, build, explain plans)
DEVIATIONS:  anything that differs from the brief, and why
OPEN:        questions, risks, follow-ups; things you noticed but didn't change
```

Never claim "tests pass" without EVIDENCE. Never report done with failing or missing tests.

## Audit (the core rule)

Before you accept a child's report and pass it up, **verify it yourself, with evidence, not by trusting the report**:

1. Read the diff. Does it meet every ACCEPTANCE item and stay inside SCOPE?
2. Re-run the relevant tests/lint/build yourself.
3. Check against the guidelines, **performance included**: merged loops, no lookups inside loops, an index for every new query, no N+1, bounded reads.
4. Check that it fits the architecture you (or your parent) decided.

**Reject** with a numbered defect list (what, where, why, expected), sent back to the same agent so it keeps its context. **Max 2 bounces.** After that, either do it yourself (if within your tier's role) or escalate up with what was tried. Once you accept, the work is yours. Your parent will audit it as your output.

## Escalation (up)

Stop and report `STATUS: escalate` instead of guessing when you hit any of these:
- the brief is ambiguous or contradicts the code;
- the fix needs files outside SCOPE or a contract/schema change;
- acceptance can't be met as written;
- you found a bigger problem than the task (security hole, data-loss risk).

Escalating early is cheap. Guessing wrong and having it audited out two levels up is expensive.

## Mechanics

- **Spawning:** if your harness lets you spawn subagents, delegate directly to the tier's agent (Claude Code: `subagent_type: senior | mid | junior`). If it can't nest, add a `DELEGATE:` list of briefs (with the target tier) to your report. Your parent dispatches them and sends the results back to **you** for audit, so accountability stays with you.
- **Continuity:** send rework to the *same* agent (Claude Code: `SendMessage` to its id), not a fresh one.
- **No subagents at all** (single-agent harness or a local model without tools for it): run the tiers sequentially yourself. Plan as Senior, implement as Mid, then audit as Senior against the written acceptance criteria before reporting.
- **Parallelism:** run independent briefs in parallel, **at most 4 code-changing agents at once** (each agent is itself a heavy process). Parallel agents that mutate code must have disjoint SCOPE or isolated worktrees.
- **Heavy commands** (tests, builds, type-checks, linters) go through the machine-wide queue: `python3 "$HOME/.agent-workflows/bin/heavy.py" run --shell bash -- "<command>"` (`python` on Windows; `--shell powershell` from PowerShell). In Claude Code a hook wraps them automatically. Exit 75 means the queue is busy: wait and retry, or run in the background. Never queue cheap commands (`grep`, `git`, reading files) or dev servers/watchers.
- **Shared state:** for multi-agent runs, keep the plan and decisions in `.team/` (`context.md`, `plan.md`), per [team mechanics](teams.md). Multi-agent task types (feature, review, security, …) are in [task-types](task-types.md). The delegator is the single writer.
- **Safety:** no agent at any tier commits, pushes, or deletes data without explicit user instruction relayed by the Lead.
