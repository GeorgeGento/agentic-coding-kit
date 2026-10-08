# agent-workflows

A portable setup for AI coding agents (**Claude Code, Codex, opencode**, and local models through any of them). It provides:

- a lean set of global rules;
- topic guidelines that load **on demand**;
- an **agent hierarchy** (Lead → Senior → Mid → Junior) in which every level audits the level below;
- a machine-wide **queue for heavy commands**, so parallel agents don't freeze the PC.

One source in `core/` is rendered for each tool by `deploy.py`. Works on Windows, macOS and Linux.

## Layout

| Path | What |
| --- | --- |
| `core/rules.md` | Global always-on rules + the "when to read what" router. Rendered as `CLAUDE.md` / `AGENTS.md` |
| `core/guidelines/` | Topic rules: coding-standards, workflow, testing, **performance** (these 4 load every session), plus git-and-versioning, security-privacy-logging, dependencies-supply-chain, angular-frontend, backend-nodejs, ux-ui-seo (on demand) |
| `core/roles/` | `lead` (your main session, loads every session) and `senior` / `mid` / `junior` (rendered as subagents) |
| `core/protocols/` | `hierarchy.md` (brief → report → audit → escalate; inlined into every agent) · `task-types.md` (feature, analyze, review, security, implement, test, refactor) · `teams.md` (multi-agent mechanics: `.team/` state, adversarial verify, dedup, stop conditions) |
| `core/skills/` | Harness-neutral skills (`ionic-capacitor`, vendored) |
| `core/bin/heavy.py` | The heavy-command queue (Python stdlib only) |
| `adapters/claude-code/` | Claude-only extras: the `/setup` skill |
| `adapters/opencode/` | opencode plugin that routes heavy commands to the queue |
| `profiles/*.toml` | Tier → model mapping: `claude`, `openai` (Codex), `opencode`, `local` |
| `deploy.py` | Renders and installs everything for one tool |
| `tests/` | `python -m unittest discover tests` |

## Deploy

Requires Python ≥ 3.11. Anything overwritten is backed up to `<target>/.deploy-backups/`.

```sh
python deploy.py                       # Claude Code -> ~/.claude (profile: claude)
python deploy.py --tool codex          # Codex       -> ~/.codex, skills in ~/.agents/skills (profile: openai)
python deploy.py --tool opencode       # opencode    -> ~/.config/opencode (profile: opencode)
python deploy.py --profile local       # any tool, different tier->model mapping
python deploy.py --dry-run             # preview, change nothing
python deploy.py --link                # symlink guidelines/roles/protocols/skills (live edits)
python deploy.py --no-hook             # skip the queue hook (Claude Code) / plugin (opencode)
python deploy.py --target /custom/path
```

What each tool gets:

| | Claude Code | Codex | opencode |
| --- | --- | --- | --- |
| Instructions | `CLAUDE.md` with `@imports` | `AGENTS.md`, always-loaded files inlined | `AGENTS.md`, inlined |
| Tier agents | `agents/<tier>.md` (`model:`) | `agents/<tier>.toml` (`model`, `developer_instructions`) | `agents/<tier>.md` (`mode: subagent`, `model: provider/id`) |
| Skills | `~/.claude/skills/` (+ `/setup`) | `~/.agents/skills/` | `~/.config/opencode/skills/` |
| Heavy queue | PreToolUse hook merged into `settings.json` | instruction only (agents call `heavy.py`) | `plugins/heavy-queue.js` |

The instructions file is always **rendered** (never symlinked). After editing `core/rules.md`, re-run the deploy. **Set the Lead's model yourself** (the main session); deploy prints where.

**Profiles:** in `profiles/<name>.toml`, an empty string means the agent inherits the session model. Fill in `openai.toml` (Codex) and `local.toml` with the model ids you use.

## Agent hierarchy

Work flows like a small engineering org:

- **Lead**: the session you talk to. It plans, routes and audits, and never edits code.
- **Senior**: architects a workstream and writes the plan. New features stop at the plan for your approval.
- **Mid**: implements a task, including its tests.
- **Junior**: mechanical, fully specified units. It escalates instead of guessing.

How the levels work together:

- Each level hands down a full **brief** (goal, scope, acceptance criteria, constraints) and receives a **report** with evidence (actual test output).
- Each level **audits the work before passing it up**: it reads the diff, re-runs the tests and checks the guidelines, performance included. Rejected work goes back to the same agent at most twice, then gets escalated.
- Routing picks the lowest tier that can own the work, and **skips levels for small jobs**.
- At most 4 agents change code at the same time.

Say **"solo"** to make the Lead do a request itself.

Tiers are roles, not models, so the same protocol runs on any LLM set. Where subagents can't nest or don't exist (some local setups), the protocol falls back to the parent dispatching on the child's behalf, or to running the tiers sequentially. Full rules: [`core/protocols/hierarchy.md`](core/protocols/hierarchy.md). Multi-agent task types (review, security, test, …) used to be `/…-team` skills; they now live in [`core/protocols/task-types.md`](core/protocols/task-types.md), and the Lead picks one from what you ask for.

## Heavy-command queue

Test runners, builds, type-checks and linters (`npm test`, `ng build`, `tsc`, `jest`, `vitest`, `pytest`, `docker build`, `cargo test`, …) wait for one of **2 slots**, shared across every session, project and tool on the machine. They run at **below-normal CPU priority**.

- Cheap commands (`grep`, `git`, `ls`, reading files) are never queued. Neither are dev servers or watch mode (`ng serve`, `npm run dev`, `--watch`), because they never finish.
- A crashed agent can't leave a slot stuck: slots are OS file locks.
- A heavy command that calls another heavy command doesn't wait in the queue twice.

```sh
python3 ~/.agent-workflows/bin/heavy.py status                                # what's running
python3 ~/.agent-workflows/bin/heavy.py run --shell bash -- "npm test"        # manual use
```

| Env var | Default | Meaning |
| --- | --- | --- |
| `AW_HEAVY_SLOTS` | `2` | concurrent heavy commands |
| `AW_HEAVY_MAX_WAIT` | `480` | seconds to wait for a slot before giving up (exit 75). Keep it under Claude Code's 10-minute tool timeout |
| `AW_HEAVY_DIR` | `~/.agent-workflows/heavy` | lock directory |

Claude Code: the hook rewrites matching `Bash`/`PowerShell` commands. Normal permission prompts still apply to the rewritten command.

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
- [ ] Set the Lead model (Claude Code: `/config`; Codex: `~/.codex/config.toml`; opencode: `opencode.json`)
- [ ] Claude Code: `/setup` for stack skills; add MCP + plugins; add a permissions allowlist (`/fewer-permission-prompts`)
- [ ] Confirm git identity (`git config --global user.name/.email`) and SSH keys

## Editing

Edit files in `core/` (or `adapters/`, `profiles/`), run `python -m unittest discover tests`, then re-deploy. Keep `core/rules.md` lean: put deep, situational rules in `core/guidelines/` or `core/protocols/` and let the router point to them. Rules for working *on* this repo are in [`CLAUDE.md`](CLAUDE.md).
