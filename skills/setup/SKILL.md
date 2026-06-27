---
name: setup
description: install a curated set of Claude Code skills (Angular, UI/UX, TypeScript, Node/NestJS) into ~/.claude/skills, fetched fresh from source
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

Default set covers Angular + UI/UX + TypeScript + NestJS essentials.

| skill | source | trust | default |
| --- | --- | --- | --- |
| `angular-developer` | `angular/skills` | official · Angular team | ✅ |
| `angular-new-app` | `angular/skills` | official · Angular team | — |
| `frontend-design` | `anthropics/skills` | official · Anthropic | ✅ |
| `webapp-testing` | `anthropics/skills` | official · Anthropic | ✅ |
| `theme-factory` | `anthropics/skills` | official · Anthropic | — |
| `typescript-pro` | `Jeffallan/claude-skills` | community | ✅ |
| `nestjs-expert` | `Jeffallan/claude-skills` | community | ✅ |
| `code-reviewer` | `Jeffallan/claude-skills` | community | — |
| `secure-code-guardian` | `Jeffallan/claude-skills` | community | — |
| `graphify` | `pip: graphifyy` | MIT · self-updating | ✅ |

Most skills are git-fetched into `~/.claude/skills`; **`graphify`** is a Python package — `/setup` runs `pip install graphifyy` + `graphify install`, which installs it to its own tool-managed location. The registry lives in [`install_skills.py`](install_skills.py) — add/remove entries there.

## Not handled here

MCP servers (Context7, Playwright, Figma) and plugins (TypeScript LSP, Code Review) are **not** folder-skills — install those with the commands in the repo `README.md` ("MCP servers & plugins" section).
