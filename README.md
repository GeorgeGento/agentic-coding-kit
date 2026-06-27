# Claude Code — Global Config

A portable, general-purpose Claude Code setup: a lean router `CLAUDE.md` plus topic guidelines that load **on demand**, bundled skills, and a cross-platform deploy script. Everything deploys into `~/.claude`.

## Layout

| Path | What | Loaded |
| --- | --- | --- |
| `CLAUDE.md` | Router — always-on rules + a "when to read what" table | every session |
| `guidelines/` | Topic rules: coding-standards, workflow, testing, git-and-versioning, security-privacy-logging, dependencies-supply-chain, angular-frontend, backend-nodejs, ux-ui-seo | on demand |
| `skills/` | Bundled skill: `setup` (`/setup`) — installs the rest | when triggered |
| `deploy.py` | Copy/symlink everything into `~/.claude` | — |
| `README.md` | This file — orientation + machine setup | — |

## Deploy

```sh
python deploy.py            # copy into ~/.claude (backs up anything it overwrites)
python deploy.py --dry-run  # preview, change nothing
python deploy.py --link     # symlink instead of copy (edits here stay live)
python deploy.py --target /custom/path
```

Works on Windows, macOS, and Linux. After deploying, `CLAUDE.md` sits at `~/.claude/CLAUDE.md` and its relative links to `guidelines/` and `README.md` resolve correctly.

## Skills

A skill is a folder under `~/.claude/skills/<name>/` with a `SKILL.md` (frontmatter: `name`, `description`, `trigger`), invoked by typing `/<trigger>`. Install by placing the folder; remove by deleting it. **Treat every third-party skill, hook, MCP server, and plugin as executable code — review the source before enabling** (see [guidelines/dependencies-supply-chain.md](guidelines/dependencies-supply-chain.md)).

### Bundled (deployed by `deploy.py`)

- **`setup`** — `/setup`: installs the curated stack skills (see below).
- **caveman** (`/caveman`, terse tone) is *not* bundled — add the folder yourself if you want it.

### Stack skills — `/setup`

Run **`/setup`** to install the curated skills (re-run to update). Default set:

- `angular-developer`, `frontend-design`, `webapp-testing`, `typescript-pro`, `nestjs-expert` — fetched fresh from source into `~/.claude/skills`.
- **`graphify`** (`/graphify`) — installed via `pip install graphifyy` + its own installer (MIT, self-updating). Turns any folder into a knowledge graph (HTML + JSON + `GRAPH_REPORT.md`); for a project with a `graphify-out/` dir, read `graphify-out/GRAPH_REPORT.md` before architecture questions.

`/setup --list` shows the full catalog (also `angular-new-app`, `theme-factory`, `code-reviewer`, `secure-code-guardian`); `/setup --all` installs everything.

### MCP servers & plugins (not folder-skills — install manually)

- **MCP:** **Context7** *(Upstash)* — version-specific library docs on demand · **Playwright** *(Microsoft)* — `claude mcp add playwright npx @playwright/mcp@latest` · **Figma** — design-to-code.
- **Plugins:** **TypeScript LSP** *(Anthropic)* — `claude.com/plugins/typescript-lsp` · **Code Review** *(Anthropic)* — `claude.com/plugins/code-review` (a built-in `/code-review` also ships).
- **Browse for more:** `github.com/anthropics/skills` · `github.com/hesreallyhim/awesome-claude-code` · `github.com/VoltAgent/awesome-agent-skills`.

## settings.json (`~/.claude/settings.json`)

- **Permissions allowlist** for trusted read-only commands to cut prompt noise (the `/fewer-permission-prompts` skill can generate one).
- **Hooks** for behavior that must run automatically every time (the harness runs hooks, not the model). Use `/update-config` to edit safely.
- Set **model** and **theme** via `/config`.

## New-machine checklist

- [ ] `python deploy.py` — installs `CLAUDE.md` + `README.md` + `guidelines/` + bundled `skills/setup` into `~/.claude/`
- [ ] `/setup` — installs the stack skills (angular-developer, frontend-design, webapp-testing, typescript-pro, nestjs-expert, graphify)
- [ ] Add MCP + plugins manually: Context7, Playwright, TypeScript LSP
- [ ] Set model/theme via `/config`; add a permissions allowlist
- [ ] Confirm git identity (`git config --global user.name/.email`) and SSH keys exist

## Editing

Edit files here, then re-run `python deploy.py` (or use `--link` once so edits are live). Keep `CLAUDE.md` lean; put deep, situational rules in `guidelines/` and let the router point to them.
