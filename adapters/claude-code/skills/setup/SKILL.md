---
name: setup
description: install curated Claude Code skills and subagents for your stack (Angular, React, Vue, Node/NestJS, TypeScript, Electron, Flutter, UI/UX, quality/review), fetched fresh from source into ~/.claude/skills and ~/.claude/agents
trigger: /setup
---

# /setup

Install a curated set of high-quality skills for this stack into `~/.claude/skills`, fetched fresh from their official/community source repos. Re-run anytime to update.

## Usage

```
/setup                 # install the default recommended set
/setup --list          # show the catalog; install nothing
/setup --only a,b      # install only these (comma-separated)
/setup --all           # install every skill in the catalog
/setup --dry-run       # show what would happen, change nothing
/setup --target PATH   # install somewhere other than ~/.claude/skills
```

## What to do when invoked

1. Run the bundled helper (it does the git fetch + copy deterministically):
   ```
   python "<directory of this SKILL.md>/install_skills.py" [args]
   ```
   On Windows use `py` if `python` is missing. Requires `git` + network access.
2. Pass through whatever flags the user gave (`--list`, `--only`, `--all`, `--dry-run`, `--target`).
3. Report exactly what was installed and from where.
4. **Trust note:** community skills are third-party code fetched from the repos below. Remind the user to review them before relying on them (see the `dependencies-supply-chain` guideline).

## Catalog

Lean defaults (✅) cover the Angular + NestJS + TypeScript stack; everything else is opt-in so each user installs only what matches their stack (`--only`, or `--all`).

| name | kind | source | default |
| --- | --- | --- | --- |
| `angular-developer` | skill | `angular/skills` (official) | ✅ |
| `angular-new-app` | skill | `angular/skills` (official) | — |
| `frontend-design` | skill | `anthropics/skills` (official) | ✅ |
| `webapp-testing` | skill | `anthropics/skills` (official) | ✅ |
| `theme-factory` | skill | `anthropics/skills` (official) | — |
| `typescript-pro` | skill | `Jeffallan/claude-skills` | ✅ |
| `javascript-pro` | skill | `Jeffallan/claude-skills` | — |
| `nestjs-expert` | skill | `Jeffallan/claude-skills` | ✅ |
| `react-expert` | skill | `Jeffallan/claude-skills` | — |
| `nextjs-developer` | skill | `Jeffallan/claude-skills` | — |
| `react-native-expert` | skill | `Jeffallan/claude-skills` | — |
| `vue-expert` | skill | `Jeffallan/claude-skills` | — |
| `electron-pro` | **agent** | `VoltAgent/awesome-claude-code-subagents` | — |
| `flutter-expert` | skill | `Jeffallan/claude-skills` | — |
| `code-reviewer` | skill | `Jeffallan/claude-skills` | — |
| `secure-code-guardian` | skill | `Jeffallan/claude-skills` | — |
| `playwright-expert` | skill | `Jeffallan/claude-skills` | — |
| `code-reviewer-agent` | **agent** | `VoltAgent/awesome-claude-code-subagents` | — |
| `security-auditor-agent` | **agent** | `VoltAgent/awesome-claude-code-subagents` | — |
| `caveman` | skill | `JuliusBrussee/caveman` (MIT) | ✅ |
| `graphify` | pip | `pip: graphifyy` (MIT, self-updating) | ✅ |

- **skills** are git-fetched into `~/.claude/skills/<name>/`.
- **agents** are Claude Code *subagents* — a single `.md` placed in `~/.claude/agents/<name>.md`, spawned as role-specialized reviewers/builders (e.g. as extra reviewers in multi-agent review/security tasks; the hierarchy's own `senior`/`mid`/`junior` agents come from `deploy.py`).
- **graphify** is a Python package — `/setup` runs `pip install --upgrade graphifyy` + `graphify install`.
- **Bundled in the config repo** (deployed by `deploy.py`, no catalog entry): `setup`, the `senior`/`mid`/`junior` tier agents, and `ionic-capacitor` (vendored, MIT — upstream is dormant so the repo copy is the source of truth).

The registry lives in [`install_skills.py`](install_skills.py) — add/remove entries there. All non-official entries are third-party code: review before relying on them.

## Not handled here

MCP servers (Context7, Playwright, Figma) and plugins (TypeScript LSP, Code Review) are **not** folder-skills — install those with the commands in the repo `README.md` ("MCP servers & plugins" section).
