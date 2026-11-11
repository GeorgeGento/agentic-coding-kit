---
packages: [core]
type: feat
---

# Rules promoted from memory: commits, dev-app restarts, worktrees, session hygiene, test cleanup, Rust

Rules that lived in personal memory and partly contradicted the deployed rules now ship with them:

- **Commits:** the Lead's finish step no longer offers "commit" as an option; it hands over the message and stops. An option the agent wrote is never permission.
- **Dev app restarts:** the Lead may stop and relaunch the user's running dev app to load changes without asking (only that app's dev processes, never app data). Subagents still never touch dev servers.
- **Worktrees:** created by hand at `<workspace>/.worktrees/<repo>-<task>`, outside every repo; never the harness's built-in isolation. `node_modules` is linked to the main checkout unless the task changes dependencies.
- **Session hygiene:** fresh session per milestone, fewer and bigger turns, and a fresh small builder for follow-ups instead of resuming a large one.
- **Tests leave no trace:** temp files removed on failure too, per-package prefixes, leftovers counted before and after a run.
- **Rust:** one shared `CARGO_TARGET_DIR` (+ one for worktrees), never per task; temp-dir fixture pitfalls (field order, `impl Drop`, open files on Windows, background tasks, `Arc` cycles).

## Changes to existing behaviour

- **Finishing a task** no longer presents commit/PR/keep/discard as options; expect a commit message and a stop.
- **Dev app:** the Lead now restarts your running dev app on its own when changes need loading. It still asks before touching app data.
- **Worktrees** move from wherever the tool put them to `<workspace>/.worktrees/`; add `.claude/worktrees/` to each repo's `.gitignore`.
- **Rework:** a builder with a long history is replaced by a fresh one for follow-ups, so the rework agent may differ from the original.
