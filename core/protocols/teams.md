# Team Mechanics

How we spawn and coordinate subagent **teams**. Every [task type](task-types.md) (feature, analyze, review, security, implement, test, refactor) follows these mechanics; each type only adds its scenario-specific lenses and output. Who owns and audits what is defined by the [hierarchy](hierarchy.md). Read this before running a multi-agent task.

## When to spawn a team

Fan out when the task needs breadth one context can't hold, independent perspectives, or adversarial checking before committing. Stay solo for a single-file lookup or a trivial edit. **Scale to the ask:** a quick check = a few agents + single verify; a "thorough audit" = larger pool + multi-vote verify + a synthesis stage.

## The team lifecycle

`brief → fan-out → dedup → verify (or critique) → consolidate → (loop) → present / implement`

Not every skill uses every stage — `analyze` swaps verify for a completeness critic; `implement`/`test`/`refactor` add a build-and-merge stage. The primitives below compose.

## Shared memory (deterministic, on disk)

Subagents have isolated contexts, so shared state lives in files under `<path>/.team/` (add `.team/` to `.gitignore` when you create it; it is never committed):

- `context.md` — the shared brief: project summary, architecture notes, symptoms, focus areas, conventions all agents must respect, and a running "decisions so far" list. Written before round 1, updated between rounds.
- `findings.json` — the canonical **id-keyed** store. Every finding has a stable `id`; the **orchestrator is the single writer**. Finders return findings (orchestrator assigns ids + appends); verifiers return `{id, ...}` and the orchestrator merges by id. Keyed merges mean no prose-matching and no cross-contamination. It is also the **recovery point** — resume from it, never re-run finders.
- `volN.md` / report — the human-readable snapshot rendered from `findings.json`.

Persist to `findings.json` as each stage completes; never depend on an agent's return blob surviving intact end-to-end.

## Model

Pick agents by **tier**, not model name: spawn `senior | mid | junior` (see [hierarchy](hierarchy.md)); the profile maps each tier to a model. Default finders/verifiers to `mid`; `senior` for the hardest verification/synthesis, `junior` for mechanical sweeps. `--model` overrides with a tier or a harness model id.

## Scoped briefs (the orchestrator's job)

You coordinate — you do **not** do the work yourself. Every subagent gets a self-contained brief:

1. **Scope** — the exact files/modules it owns (distinct per agent, never the whole repo; weight by `--focus`).
2. **Context** — read `context.md` first, plus the scenario context for its scope.
3. **Task** — one job only: find | refute | read | implement.
4. **Output contract** — the schema, nothing else.

An agent that asks "which files?" or returns freeform prose means the brief was too thin — fix the brief, not the agent.

## Findings schema (id-keyed)

```json
{ "id": "f-001", "file": "...", "line": 42, "title": "...",
  "severity": "blocker | major | minor", "analysis": "...",
  "fix_before": "...", "fix_after": "...",
  "depends_on": ["<id>"], "new_risks": ["..."] }
```

Finders may leave `id` blank (orchestrator assigns on write). Verifiers return `{ "id", "refuted": bool, "confidence", "verdict_reason", "corrected_severity" }` so verdicts merge by id with zero ambiguity.

## Adversarial verify (the skeptic pass)

For each new finding, spawn 2–3 verifiers whose job is to **refute it**: "Prove this is a false positive or the fix is wrong. Default to refuted if uncertain." Give each a distinct lens (correctness / security / does-it-actually-reproduce). Verdict: **0 refutes → confirmed, 1 → disputed (human call), ≥2 → refuted (dropped)**. This is what catches plausible-but-wrong findings and bad fixes a single pass would commit. `--verify all|blockers|none` scopes it — `blockers` verifies only blocker-severity findings and roughly halves cost on a big repo.

## Completeness critic (for read/understand tasks)

When there is nothing to refute (analysis, mapping), replace the skeptic with a critic: "what's missing — a subsystem not read, a data flow not traced, a claim unsourced?" Its gaps become the next round's scope.

## Dedup

Merge findings that share file + root cause. Dedup against **all seen** findings, not just confirmed ones — otherwise refuted items resurface every round and the loop never converges.

## Stop conditions

Stop at 0 open blockers, a **dry round** (no new confirmed findings two rounds running), the round/volume cap, or the token budget. **Log anything a cap dropped** — silent truncation reads as "covered everything" when it didn't.

## Workflow tool

**Opt-in only.** Default to batched parallel subagent calls and validate their JSON yourself. Use a workflow/orchestration tool only in the **Hierarchy + workflows** session mode (see the Lead role) or when the user explicitly asks for one — fan-out runs are slow and token-expensive, and runs that die mid-way leave half-written edits. When opted in: pass the findings schema as its `schema` option (validation at the tool-call layer, agents retry on mismatch), gain resume-after-crash and token budgets, and use `isolation: 'worktree'` when agents mutate files in parallel. Default to `pipeline()` (per-item, no barrier); use a barrier only when a stage genuinely needs all prior results (dedup, early-exit on zero).

## Implementing (mutation) — opt-in only

Producing a plan is always safe. **Applying** changes mutates code — never do it without explicit opt-in (`--auto`, "implement it", "don't ask me"). When applying: order by `depends_on`, isolate independent changes in worktrees and merge, run the project's lint/build/tests after each logical group, fix regressions the tests catch, and summarize. (Per the [workflow](../guidelines/workflow.md) guideline: plan → confirm → implement.)

## Composing teams

Teams chain. The canonical composition is feature delivery (the *feature* task type): **architect** (*analyze*) → **plan + human gate** → **build** (*implement*) → **check** (*review* + *security*, in parallel) → **cover** (*test*). Shared `.team/` state carries context across phases — the architecture map feeds the plan, the plan feeds the build, the diff feeds review/security/test. The owner of a composed task *delegates* each phase rather than doing it inline. Always keep the **plan gate**: stop for approval before the build phase unless the user explicitly opted into unattended end-to-end.

## Common flags

`--agents N` · `--model senior|mid|junior` · `--verify all|blockers|none` · `--focus "..."` · `--auto` (mutating skills only). Defaults: **5 agents, mid, verify all, no auto**.
