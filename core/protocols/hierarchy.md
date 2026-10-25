# Hierarchy Protocol

How work flows between the **Lead** and the agents it spawns. Flat on purpose: the Lead plans and audits; an **executor** builds; **specialists** check; an **escalation** agent takes what the others can't crack. Work goes down as briefs and comes up as reports. The Lead audits everything before it reaches the user, and whoever delegates a piece of work stays accountable for it.

Roles are not models. A profile (`profiles/*.toml`) or the user's settings map each role to a model, so this protocol works for any LLM set.

## Roles

| Role | Owns | Never |
| --- | --- | --- |
| **Lead** (main session) | The conversation, the plan, small and medium code changes, the one audit, final acceptance | Delegates work smaller than the brief it would write |
| **Executor** | One task with a tight file list, including its tests | Changes architecture or public contracts without escalating |
| **Specialists**: `reviewer`, `security`, `tester`, `e2e`, `ui-ux` | One lens over a diff or an area; read-only unless the user opted into fixes | Builds features |
| **Escalation** | A task an executor failed twice, or a real design/root-cause problem | Routine work |

## Solo by default

The Lead does the work itself. It spawns an agent only when that pays:

- **Parallel:** independent tasks with disjoint files that can run at the same time.
- **Context-heavy:** large reads or long investigations that would flood the main session.
- **Independent eyes:** specialists for review, security, test gaps, e2e flows, or UI/UX, per the [task types](task-types.md).

Don't delegate work smaller than the brief you'd write for it. Do read-only lookups yourself. If the user names who does a task, that role does it itself, for that task only.

## Parallel cap

`max_parallel` (in the user's `settings.toml`, else the profile) is the default number of code-changing agents at once. Read-only specialists don't count. At the first task in a session that would spawn agents, ask the user once (structured question if the harness has one): **default (N)**, **recommended for this task (M, with the reason)**, or **custom**. Keep the answer for the session. Pure Q&A sessions never see the prompt.

## Plans

A plan task for an executor names exact file paths (and `file:line` anchors where known), the steps, and how to verify each step, so the executor doesn't explore. Don't write the complete code into the plan; that writes it twice.

## Brief (down)

Every delegation is a self-contained brief. The receiver has no other context.

```
GOAL:        one sentence: the outcome, not the steps
SCOPE:       files/dirs you may touch; anything outside requires escalation
CONTEXT:     decisions, patterns to follow (file:line), pasted excerpts, guidelines that apply
ACCEPTANCE:  verifiable checks, e.g. "tests X pass", "endpoint returns 404 on missing id"
CONSTRAINTS: data sizes / performance expectations, no new deps, conventions
WORKTREE:    none (shared checkout) | agent/<task-slug>
```

A brief without ACCEPTANCE is not a brief. If the receiver asks "which files?" or returns prose instead of a report, the brief was too thin: fix the brief. Paste the plan excerpt or bug list the agent needs instead of "read these docs". One agent per feature, screen, or component.

## Report (up)

```
STATUS:      done | blocked | escalate
CHANGES:     files touched + one line each
EVIDENCE:    the commands run and their heavy-queue summaries
DEVIATIONS:  anything that differs from the brief, and why
OPEN:        questions, risks, follow-ups; things noticed but not changed
```

Never claim "tests pass" without EVIDENCE. Never report done with failing or missing tests.

## Audit: once, in two stages

The executor self-checks with targeted tests. The Lead then audits once:

1. **Spec first.** Every ACCEPTANCE item met, nothing outside SCOPE. On a miss, bounce at once, without a quality pass.
2. **Quality second.** Read the diff against the guidelines, performance included (merged loops, no lookups inside loops, an index for every new query, no N+1, bounded reads). Re-run only the targeted tests.

**Reject** with a numbered defect list (what, where, why, expected), sent to the **same** agent so it keeps its context. **Max 2 bounces**, each fixing the root cause. After that, do it yourself or hand it to the escalation agent with what was tried.

**Specialist findings:** check each against the code before acting. Confirm or refute it, drop duplicates, and push back on wrong ones. Never apply findings blindly.

## Escalation (up)

An agent stops with `STATUS: escalate` instead of guessing when:
- the brief is ambiguous or contradicts the code;
- the fix needs files outside SCOPE or a contract/schema change;
- acceptance can't be met as written;
- it found a bigger problem than the task (security hole, data-loss risk).

## Worktrees

Parallel agents share one checkout with disjoint SCOPE by default. Use a git worktree (it shares one `.git`, so there's no repo copy) only when file lists overlap, the task is experimental, or agents would fight over build output or ports.

The script is `python "$HOME/.agent-workflows/bin/worktrees.py"` (`python` on Windows), run from inside the repo.

1. **Before creating:** at most `max_parallel` worktrees; run `worktrees.py check-disk` (exit 1 = below `min_free_disk_gb`, default 10). If disk is low, run in the main checkout or ask. Branch: `agent/<task-slug>`. Dependencies get a fresh install inside the worktree.
2. **Baseline:** the executor runs the targeted tests once before editing and records any failures that already exist.
3. **Apply, don't merge:** after the audit, `worktrees.py apply <path>` copies the worktree's changes (untracked files included) into the main checkout as uncommitted changes. History stays untouched; commits remain the user's.
4. **Test in the main checkout.** On failure the worktree stays, and the rework goes to the same agent.
5. **Clean up once green:** `worktrees.py clean` removes every worktree whose changes are verified present in the main checkout, plus its `agent/*` branch. **Standing rule:** this needs no confirmation. Never remove anything else, or any other branch, without the user's imperative.
6. **Rejected or abandoned work:** ask the user: discard (recommended) or keep. On discard: `worktrees.py discard <path>`.
7. **No leftovers:** a task isn't done while one of its worktrees exists. Before reporting, run `worktrees.py list` and resolve each one. A worktree is kept only by the user's explicit choice. In Claude Code a session-start hook reports leftovers from crashed sessions.

## Mechanics

- **Spawning:** Claude Code: `subagent_type: executor | escalation | reviewer | security | tester | e2e | ui-ux`. If the harness can't spawn, run the roles sequentially yourself: plan, build, then audit against the written acceptance.
- **Continuity:** rework, including auditors' findings, goes to the *same* agent (Claude Code: `SendMessage` to its id). Specialists are always separate agents from the builder.
- **One gate.** Agents verify their slice with targeted suites. The Lead runs the full gate once at the end. When suites share a test DB, two DB-backed e2e/UI suites never run at once.
- **Heavy commands** (tests, builds, type-checks, linters) go through the machine-wide queue, which prints a structured summary and keeps the full log on disk. Paste the summary as EVIDENCE. On failure, open the referenced `file:line` or search the log; never read the whole log back. Re-run only the failing test file. In Claude Code a hook wraps the commands automatically; elsewhere: `python3 "$HOME/.agent-workflows/bin/heavy.py" run --shell bash -- "<command>"`. Exit 75 means the queue is busy: wait and retry.
- **Shared state** for multi-agent runs lives in `.team/` (`context.md`, `plan.md`), per [team mechanics](teams.md). The delegator is the single writer.
- **Safety:** no agent commits, pushes, or deletes data without an explicit user instruction relayed by the Lead (the `agent/*` cleanup rule above is the only standing exception).
