# agent-workflows

A portable setup for AI coding agents (**Claude Code, Codex, opencode**, and local models through any of them). It provides:

- a lean set of global rules;
- topic guidelines that load **on demand**;
- a flat **agent setup**: the Lead plans and builds, executors take parallel work, specialists check it, and the Lead audits once;
- a machine-wide **queue for heavy commands**, so parallel agents don't freeze the PC, which also turns raw test/build output into short summaries;
- **agent worktree cleanup**, so isolated agent work never piles up on disk.

One source in `core/` is rendered for each tool by `deploy.py`. Works on Windows, macOS and Linux.

## Layout

| Path | What |
| --- | --- |
| `core/rules.md` | Global always-on rules + the "when to read what" router. Rendered as `CLAUDE.md` / `AGENTS.md` |
| `core/guidelines/` | Topic rules: coding-standards (loads every session), plus workflow, testing, performance, debugging, motion-3d, ui-testing-platforms, git-and-versioning, security-privacy-logging, dependencies-supply-chain, angular-frontend, backend-nodejs, library-design, ux-ui-seo (on demand; their must-dos are a checklist in `rules.md`) |
| `core/guidelines/languages/` | Language-specific rules (on demand): `README.md` index → one file per language (`javascript-typescript.md`, …) |
| `core/roles/` | `lead` (your main session, loads every session); `executor`, `escalation` and the specialists `reviewer` / `security` / `tester` / `e2e` / `ui-ux` (rendered as subagents) |
| `core/protocols/` | `hierarchy.md` (roles, briefs, the two-stage audit, worktree lifecycle; read by the Lead) · `agent-protocol.md` (the short part inlined into every agent) · `task-types.md` (feature, analyze, review, security, implement, test, refactor) · `teams.md` (multi-agent mechanics: `.team/` state, adversarial verify, dedup, stop conditions) |
| `core/skills/` | Harness-neutral skills (`ionic-capacitor`, vendored) |
| `core/bin/` | `heavy.py` (heavy-command queue) + `heavy_parsers.py` (output summaries) · `worktrees.py` (agent worktree list/apply/clean). Python stdlib only |
| `adapters/claude-code/` | Claude-only extras: the `/setup` skill |
| `adapters/opencode/` | opencode plugin that routes heavy commands to the queue |
| `profiles/*.toml` | Role → model defaults and `max_parallel`: `claude`, `openai` (Codex), `opencode`, `local` |
| `deploy.py` | Renders and installs everything for one tool |
| `core/memory-seed/` | Seeded into `~/.agent-memory/` if missing: `MEMORY.md`, `README.md`, `settings.toml` |
| `tests/` | `python -m unittest discover tests` |

## Deploy

Requires Python ≥ 3.11. Anything overwritten is backed up to `<target>/.deploy-backups/`.

```sh
python deploy.py                       # Claude Code -> ~/.claude (profile: claude)
python deploy.py --tool codex          # Codex       -> ~/.codex, skills in ~/.agents/skills (profile: openai)
python deploy.py --tool opencode       # opencode    -> ~/.config/opencode (profile: opencode)
python deploy.py --profile local       # any tool, different role->model mapping
python deploy.py --max-parallel 3      # default parallel code-changing agents
python deploy.py --dry-run             # preview, change nothing
python deploy.py --link                # symlink guidelines/roles/protocols/skills (live edits)
python deploy.py --no-hook             # skip the queue hook (Claude Code) / plugin (opencode) / sandbox root (Codex)
python deploy.py --target /custom/path
```

What each tool gets:

| | Claude Code | Codex | opencode |
| --- | --- | --- | --- |
| Instructions | `CLAUDE.md` with `@imports` | `AGENTS.md`, always-loaded files inlined | `AGENTS.md`, inlined |
| Role agents | `agents/<role>.md` (`model:`) | `agents/<role>.toml` (`model`, `developer_instructions`) | `agents/<role>.md` (`mode: subagent`, `model: provider/id`) |
| Skills | `~/.claude/skills/` (+ `/setup`) | `~/.agents/skills/` | `~/.config/opencode/skills/` |
| Heavy queue | PreToolUse hook merged into `settings.json` (+ a SessionStart hook reporting leftover agent worktrees) | instruction (agents call `heavy.py`); lock dir added to `[sandbox_workspace_write] writable_roots` in `config.toml` | `plugins/heavy-queue.js` |
| Personal memory | `@~/.agent-memory/MEMORY.md` import (live) | "read `~/.agent-memory/MEMORY.md` at session start" line; memory dir added to `writable_roots` | same instruction line as Codex |

The instructions file is always **rendered** (never symlinked). After editing `core/rules.md`, re-run the deploy.

**Settings:** which model each role uses and `max_parallel` come from, highest first: the `--max-parallel` flag → your `~/.agent-memory/settings.toml` (per tool: `[models.claude-code]`, `[models.codex]`, …) → `profiles/<name>.toml`. A specialist without its own model uses `specialist`. An empty string means the agent inherits the session model. In Claude Code, a `lead` model set in `settings.toml` is written into `settings.json`; otherwise deploy prints where to set it. `/setup` asks for these defaults and writes `settings.toml`.

### Personal memory

`~/.agent-memory/` is one tool-neutral memory folder shared by every harness and project. `MEMORY.md` is the index (`- [Title](file.md) — hook`, one line per entry); each entry is its own file. Every deploy renders the path into the tool's instructions, and **seeds `MEMORY.md`, an explainer `README.md` and a commented-out `settings.toml` (from `core/memory-seed/`), each only if missing**. After that the folder is yours: deploy never overwrites, backs up, links or edits it, even with `--link`. `--dry-run` creates nothing. To sync across machines, make it a private git repo yourself (deploy prints a hint and never runs git).

## Agents

Flat on purpose, to keep token use low without dropping checks:

- **Lead**: the session you talk to. It plans (and waits for your approval), writes small and medium changes itself, and audits everything once.
- **Executor**: one task with a tight file list, including its tests. Spawned only for parallel work or work that would flood the main session.
- **Specialists**: `reviewer`, `security`, `tester`, `e2e` (Playwright), `ui-ux`. Spawned per task type, read-only unless you opt into fixes.
- **Escalation**: strong model, only when an executor fails twice or hits a real design problem.

How they work together:

- The Lead hands down a full **brief** (goal, exact files, acceptance criteria) and gets back a **report** with evidence (the heavy-queue summaries).
- **One audit, two stages:** spec compliance first (bounced at once on a miss), then quality, performance included. Rework goes back to the same agent, at most twice.
- **`max_parallel`** caps code-changing agents (default from settings; Pro 1, Max 3). The Lead asks once per session, at the first task that would spawn agents: the default, its recommendation for the task, or your own number.
- **Worktrees** only when file lists overlap or a task is experimental. They share one `.git`. Their changes are applied to your checkout **uncommitted**, tested there, then the worktree and its `agent/*` branch are removed. A task isn't done while one of its worktrees exists.

Roles are not models, so the same protocol runs on any LLM set; without subagents the Lead runs the roles in sequence. Full rules: [`core/protocols/hierarchy.md`](core/protocols/hierarchy.md). Multi-agent task types (feature, review, security, test, …) are in [`core/protocols/task-types.md`](core/protocols/task-types.md).

## Heavy-command queue

Test runners, builds, type-checks and linters (`npm test`, `ng build`, `tsc`, `jest`, `vitest`, `pytest`, `docker build`, `cargo test`, …) wait for one of **2 slots**, shared across every session, project and tool on the machine. They run at **below-normal CPU priority**.

- Cheap commands (`grep`, `git`, `ls`, reading files) are never queued. Neither are dev servers or watch mode (`ng serve`, `npm run dev`, `--watch`), because they never finish.
- On POSIX, a crashed caller's supervisor stops its workload before releasing the OS file lock. Cancellation and normal shell exit also clean up remaining background workers. Windows has no supervisor: the wrapper holds the slot and the OS frees the lock when it exits.
- POSIX workers use a process group. Linux also cleans up adopted descendants that create a separate session. On macOS, descendants that deliberately detach from the process group are outside this cleanup guarantee.
- A heavy command that calls another heavy command doesn't wait in the queue twice.
- If the lock dir can't be written (e.g. a sandbox without it in its writable roots), the command still runs, unqueued, with a warning.

**Output summaries.** The full output goes to `~/.agent-workflows/logs/<project>-<hash>/` (newest `heavy_log_keep` kept, default 20) and the agent sees a summary instead: one line on success, otherwise the failures with `file:line`, capped at ~60 lines. Parsers cover jest, vitest, Playwright, pytest, cargo, tsc / `ng build` and eslint; anything else gets error-like lines plus the tail. The exit code is always the command's own, and a failure is never summarized to nothing. Use `run --raw` or `HEAVY_RAW=1` for raw output.

```sh
python3 ~/.agent-workflows/bin/heavy.py status                                # what's running
python3 ~/.agent-workflows/bin/heavy.py run --shell bash -- "npm test"        # manual use
```

| Env var | Default | Meaning |
| --- | --- | --- |
| `AW_HEAVY_SLOTS` | `2` | concurrent heavy commands |
| `AW_HEAVY_MAX_WAIT` | `480` | seconds to wait for a slot before giving up (exit 75). Keep it under Claude Code's 10-minute tool timeout |
| `AW_HEAVY_DIR` | `~/.agent-workflows/heavy` | lock directory |
| `AW_HEAVY_LOG_DIR` | `~/.agent-workflows/logs` | full-output logs |
| `HEAVY_RAW` | unset | `1` = raw output, no summary |

Claude Code: the hook rewrites matching `Bash`/`PowerShell` commands. Normal permission prompts still apply to the rewritten command.

## Agent worktrees

```sh
python3 ~/.agent-workflows/bin/worktrees.py list          # agent/* worktrees: size, age, dirty, applied
python3 ~/.agent-workflows/bin/worktrees.py apply <path>  # its changes -> your checkout, uncommitted
python3 ~/.agent-workflows/bin/worktrees.py clean         # remove the applied ones + their branches
python3 ~/.agent-workflows/bin/worktrees.py discard <path>
python3 ~/.agent-workflows/bin/worktrees.py check-disk    # exit 1 below min_free_disk_gb (default 10)
```

`clean` only removes worktrees whose changes it verified are already in your checkout; everything else is listed for you to decide. In Claude Code, a session-start hook prints one line when leftovers exist (e.g. after a crash).

## Skills

A skill is a folder with a `SKILL.md` (frontmatter: `name`, `description`). Claude Code, Codex and opencode all read this format. **Treat every third-party skill, hook, MCP server and plugin as executable code, and review the source before enabling it** (see [dependencies-supply-chain](core/guidelines/dependencies-supply-chain.md)).

- **`ionic-capacitor`** (bundled, vendored, MIT): Ionic + Capacitor patterns, dormant until an Ionic project triggers it.
- **`/setup`** (Claude Code only): installs the curated stack skills and subagents, fetched fresh from source.
  - Defaults: `angular-developer`, `frontend-design`, `webapp-testing`, `typescript-pro`, `nestjs-expert`, `caveman`, `graphify`. `caveman` is the terse-tone skill, on by default via `core/rules.md` when installed; turn it off with "stop caveman". `graphify` builds a queryable knowledge graph of a folder.
  - Opt-in catalog (`/setup --list`): React, Vue, JS, Electron, Flutter, quality reviewers, and more.

```sh
/setup                                   # defaults
/setup --only react-expert,vue-expert    # pick your stack
/setup --all                             # everything
```

### MCP servers & plugins (install manually)

- **MCP:** **Context7** (version-specific library docs) · **Playwright** (`claude mcp add playwright npx @playwright/mcp@latest`) · **Figma**.
- **Claude Code plugins:** TypeScript LSP · Code Review (a built-in `/code-review` also ships).
- **Browse:** `github.com/anthropics/skills` · `github.com/hesreallyhim/awesome-claude-code` · `github.com/VoltAgent/awesome-agent-skills`.

## New-machine checklist

- [ ] `python deploy.py` (plus `--tool codex` / `--tool opencode` for the tools you use)
- [ ] Claude Code: `/setup` asks for your defaults (models, `max_parallel`, disk threshold) and writes `~/.agent-memory/settings.toml`; otherwise set the Lead model yourself (Codex: `~/.codex/config.toml`; opencode: `opencode.json`)
- [ ] Claude Code: `/setup` for stack skills; add MCP + plugins; add a permissions allowlist (`/fewer-permission-prompts`)
- [ ] Confirm git identity (`git config --global user.name/.email`) and SSH keys

## Editing

Edit files in `core/` (or `adapters/`, `profiles/`), run `python -m unittest discover tests`, then re-deploy. Keep `core/rules.md` lean: put deep, situational rules in `core/guidelines/` or `core/protocols/` and let the router point to them. Rules for working *on* this repo are in [`CLAUDE.md`](CLAUDE.md).
