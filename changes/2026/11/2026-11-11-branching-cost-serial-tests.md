---
packages: [core]
type: feat
---

# Rules promoted from memory: branching, cost/legal actions, serial test runners, no commit attribution

Three rules that lived only in personal memory now ship with the core rules (the branching one contradicted them), plus a fix to how commit messages are handed over.

- **Branching:** agents no longer create or switch branches on their own. They work on the checked-out branch and ask first when a new branch looks useful or the current one looks unexpected. The Lead's `agent/*` worktree branches are exempt. (`core/rules.md`, `core/guidelines/git-and-versioning.md`)
- **Cost and legal actions:** billable calls, real accounts in place of test ones, accepting terms and data-handling choices need the user's yes. A missing test option is reported, never swapped for a real one. (`core/rules.md`)
- **Serial test runners:** one heavy command at a time, jest `--runInBand` (`--forceExit` when needed), nx `--parallel=1`, and executor briefs say so. (`core/guidelines/testing.md`)
- **Commit messages:** the message the Lead hands over has no `Co-Authored-By` or AI attribution line, even when the harness asks for one. This removes a contradiction between `core/roles/lead.md` and `core/guidelines/git-and-versioning.md`.

## Changes to existing behaviour

- **Branches:** "creating branches is always fine" is gone. Expect a question before any new branch or branch switch.
- **External services:** agents stop and ask before billable or real-account actions instead of proceeding, including when a sandbox option is missing.
- **Tests:** suites run serially, so runs may take longer but no longer freeze the machine.
- **Commit messages:** no more `Co-Authored-By` trailer in handed-over commit messages or PR descriptions.
