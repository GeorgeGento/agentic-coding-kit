---
name: agent-orchestrator
description: Iterative multi-agent code review and fix pipeline. Fans out review agents (default 5, latest Sonnet) over a target codebase with a shared context file, dedupes their findings, adversarially verifies each one with refute-mode skeptics, consolidates survivors into versioned volume files (vol1.md, vol2.md, ...), and stops at zero blockers, a dry round, or the volume cap. Implements the final plan only when the user explicitly opts in. Use when the user asks for a multi-agent review, "N agents to propose fixes", iterative fix volumes, or an overnight unattended fix run.
---

# Agent Orchestrator

Multi-agent review pipeline: **find → dedup → adversarially verify → consolidate → repeat on open items → (optionally) implement.** Produces an auditable trail of `volN.md` files so every fix can be traced to the round that proposed it, the skeptics that confirmed it, and the round that closed it.

## Usage

```
/agent-orchestrator <path>                      # review + volumes, then STOP and present the plan
/agent-orchestrator <path> --agents 8           # finder agents per round (default 5)
/agent-orchestrator <path> --max-volumes 10     # volume cap (default 10)
/agent-orchestrator <path> --focus "auth, db"   # steer agents at known problem areas
/agent-orchestrator <path> --model opus         # subagent model (default: sonnet)
/agent-orchestrator <path> --verify blockers    # verify blockers only (all | blockers | none; default: all)
/agent-orchestrator <path> --auto               # implement the final plan without asking (explicit opt-in)
```

## Defaults

- **5 finder agents per round**, spawned with the **latest Sonnet model** (`model: sonnet`). Raise `--agents` for big codebases.
- **Subagent model is configurable** via `--model sonnet|opus|haiku` (or "use opus agents" in the request). Sonnet default; Opus for the hardest verification, Haiku for mechanical sweeps. Pass the choice as `model:` on every spawn; don't mix models within a stage unless asked.
- Stop at **0 open blockers**, a **dry round** (no new confirmed findings 2 rounds in a row), or the **volume cap** — whichever first.
- **Verify scope** `--verify all|blockers|none` (default `all`). The skeptic pass is the cost driver — on a huge repo each finding spawns 2–3 verifiers, so `--verify blockers` (skip verification for major/minor, keep it for blockers) roughly halves spend on large runs. `none` = no adversarial pass (fast, unverified — say so in the report).
- **Never auto-implements** unless the user explicitly opted in (`--auto`, "don't ask me", "ready by morning").

## Shared memory (on disk — deterministic, no result-blob parsing)

Subagents have isolated contexts, so shared state lives in files. **Every finding has a stable `id`** (e.g. `f-001`), and all bookkeeping is keyed by it — never reconstructed by matching prose. Three files under `<path>/.orchestrator/`:

- `context.md` — the shared brief: project summary, architecture notes, known symptoms/error logs, focus areas, conventions all agents must respect, and a running "decisions so far" list. Written before round 1, updated between rounds.
- `findings.json` — the canonical store: an array of finding objects (schema below), each with its `id`, `status` (`open` → `confirmed` | `disputed` | `refuted`), and an appended `verdicts` list. **The orchestrator is the single writer.** Finders return new findings (orchestrator assigns ids + appends); verifiers return `{id, refuted, ...}` and the orchestrator updates that finding's `verdicts`/`status` by id. Because merges are keyed by `id`, there is no text-matching guesswork and results never cross-contaminate — the failure mode a prose-merge hits.
- `volN.md` — the human-readable snapshot of `findings.json` each round (rendered from the data, structure below).

Assign `id` when a finding first enters `findings.json` and pass it into every verifier's brief so the verdict comes back tagged. Do not rely on the agent's return blob being intact end-to-end — write to `findings.json` as each stage completes.

## The orchestrator's job (main agent)

You (the main agent) coordinate — you do not review files yourself. Every subagent gets a **complete, self-contained brief**:

1. **Scope** — the exact files/modules it owns (distinct per agent, never the whole repo; weight by `--focus`).
2. **Context** — `orchestrator-context.md` contents (or instruct it to read the file first) + symptom context for its scope.
3. **Task** — find (round 1+), or refute (verify pass) — never both in one agent.
4. **Output contract** — the findings schema below. Nothing else.

A subagent that asks "which files?" or returns prose without the schema means the brief was too thin — fix the brief, not the agent.

## Findings schema (all agents return this)

Require every agent to return JSON, one object per finding:

```json
{
  "id": "f-001",
  "file": "src/auth/token.service.ts",
  "line": 42,
  "title": "expiry check off-by-one",
  "severity": "blocker | major | minor",
  "analysis": "2-4 sentence root cause",
  "fix_before": "<current code>",
  "fix_after": "<ready-to-apply code>",
  "depends_on": ["<other finding id or - >"],
  "new_risks": ["<anything surfaced beyond scope>"]
}
```

Finders may leave `id` blank — the orchestrator assigns it on write. Verifiers return `{ "id": "f-001", "refuted": bool, "confidence": "...", "verdict_reason": "...", "corrected_severity": "..." }` so the verdict merges into `findings.json` by id with zero ambiguity.

When the Workflow tool is available, **use it** and pass this as the `schema` option — validation then happens at the tool-call layer (agents retry on mismatch, no parse errors), and the run gains resume-after-crash and token budgets. Otherwise batch parallel Agent calls and validate the JSON yourself.

## Procedure

### Round 0 — shared brief

Create `<path>/.orchestrator/`, write `context.md`, and init `findings.json` as `[]`. Build the per-agent file assignment list.

### Find (parallel)

Dispatch N finder agents in parallel with the chosen model. As each returns, assign `id`s and append its findings to `findings.json`.

### Dedup (orchestrator, no agents)

Merge findings that share file + root cause (agents on adjacent files report the same bug in different words). Keep the best snippet, union the `depends_on`. Dedup against **all previously seen** findings — not just confirmed ones — or refuted findings resurface every round and the loop never converges.

### Verify (parallel, per finding — the skeptic pass)

Honor `--verify` (default `all`): `blockers` verifies only blocker-severity findings and auto-confirms the rest (note that in the report); `none` skips this stage entirely (mark all findings unverified). Otherwise, for each **new** deduped finding in scope, spawn 2–3 verifiers whose job is to **refute it**: "Prove this is a false positive or the fix is wrong. Default to refuted if uncertain." Pass each verifier the finding's `id` and require it back in the verdict. Give each a distinct lens — correctness, security, does-it-actually-reproduce. Majority refute → finding dies (`status: refuted`; don't re-litigate). 0 refutes → `confirmed`; a split → `disputed` (needs a human call). Write each verdict into `findings.json` under its `id` as it returns.

Verification is per-finding, so findings verify as soon as they're deduped — don't wait for all finders to finish (no barrier unless dedup requires the full set).

### Consolidate — write `volN.md`

Render deterministically from `findings.json` (single source of truth) — one section per finding, keyed and ordered by status then severity:

```
## [file path] — [title]                       (status: confirmed | open | refuted)
**Severity:** blocker | major | minor
**Order/dependency:** ...
**Analysis:** ...
**Fix:**
```<language>
<snippet>
```
```

End with `## Open Blockers` (unresolved blockers only). Update `context.md` with decisions made. `findings.json` already carries every item with its status — `volN.md` is just its readable snapshot; never delete history.

### Rounds 2..N — only the open items

Fresh finder agents get: the shared brief + **only open/new findings** and untouched high-risk areas. Confirmed items are settled — re-reviewing them burns tokens for nothing. Then dedup → verify → consolidate as above.

### Stop condition

Stop when any of:
- `Open Blockers` empty (0 blockers),
- dry round ×2 (no new confirmed findings two rounds running),
- volume cap reached.

### Final step

- **Without `--auto`:** present the final volume as the proposed plan and STOP. Implement only after the user approves (per the global workflow guideline).
- **With `--auto`:** apply confirmed fixes in `depends_on` order. Independent fixes may be applied by parallel agents in **isolated worktrees** (Workflow `isolation: 'worktree'`) and merged; dependency chains stay sequential. Run the project's lint/build/tests after each logical group, fix regressions the tests catch, and finish with a summary of everything changed plus test results. No per-fix confirmation — the user opted in.

## Notes

- The `.orchestrator/` dir (`context.md`, `findings.json`) and the `volN.md` volumes are working artifacts: write them under the target path (visible in git status) and ask the user whether to keep or delete them at the end.
- `findings.json` is the recovery point: if a run is interrupted, resume from it rather than re-running finders. Never depend on an agent's return blob surviving intact end-to-end — persist to `findings.json` as each stage completes.
- If installed review subagents exist (e.g. `code-reviewer`, `security-auditor` in `~/.claude/agents/`), use them for finder/verifier role diversity — a mix of correctness, security, and performance lenses catches more than N identical generalists.
- Severity discipline: only true ship-stoppers are `blocker`. Inflated severities stall the stop condition.
