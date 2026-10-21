# Personal memory

What you (the user) want every AI coding agent to know about you, on every tool, project and machine. Deploys from `agent-workflows` only create this folder when it's missing; after that it is **yours**, and no deploy edits it.

## Layout

| File | What |
| --- | --- |
| `MEMORY.md` | The index. Loaded every session. One line per entry: `- [Title](file.md) — hook`. |
| `README.md` | This file. |
| `<slug>.md` | One fact per file (below). |

## Entry format

```md
---
name: no-fresh-packages
description: one line, used to decide relevance when recalling
type: user | feedback | reference
---

The fact. For feedback, add:
**Why:** the reason or incident behind it.
**How to apply:** when and how it changes behavior.
```

- **user**: who you are (role, expertise, preferences).
- **feedback**: how agents should work, both corrections and approaches you confirmed.
- **reference**: pointers to external resources (dashboards, docs, tickets).

## Global vs project

- **Here (global):** facts about you and how you work that apply everywhere.
- **Not here (project):** facts about one codebase. Those go in the tool's project memory or the repo's own docs.

Agents ask you which one each time they save, and recommend one. If a project memory turns up in a second project, they propose moving it here.

## How each tool loads it

- **Claude Code:** `@import` of `MEMORY.md` in `~/.claude/CLAUDE.md`. It is live, so edits apply without a redeploy.
- **Codex / opencode:** an instruction to read `MEMORY.md` at session start. Codex's sandbox can write here.

Entries are read on demand from the index, so keep each index line short and specific.

## Rules

- Never store secrets, tokens, passwords, or other people's personal data.
- Update an existing entry instead of adding a duplicate. Delete entries that turn out wrong.
- Shared workflow rules belong in the `agent-workflows` repo (`core/`), not here. This folder is personal.

## Sync across machines

Make this folder a private git repo (`git init`, then add a private remote) and pull it on each machine. Deploy never runs git here.
