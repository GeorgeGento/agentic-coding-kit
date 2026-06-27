# Claude Code — Global Guidelines

My global configuration for Claude Code. It stays **lean on purpose**: the universal rules live in this file and apply to every task; the deep, situational rules live in `guidelines/` and are read **on demand** so they only cost context when they are relevant.

## How to use this file

1. **Always-on rules** (bottom of this file) apply to **every** task. Follow them without being asked.
2. Before doing substantive work in a domain, **read the matching guideline file first** (table below) and treat it as binding for that work.
3. For setting up this machine (skills, tools, deploy), see [`README.md`](README.md).
4. A project's own `CLAUDE.md` always **wins over these global rules** for that project.

## When to read which guideline

| If the task involves… | Read first |
| --- | --- |
| Writing or editing **any** code | [`guidelines/coding-standards.md`](guidelines/coding-standards.md) |
| Planning, scoping, reviewing, multi-step work | [`guidelines/workflow.md`](guidelines/workflow.md) |
| git, commits, versioning, `.env`, deploys, remote servers | [`guidelines/git-and-versioning.md`](guidelines/git-and-versioning.md) |
| Anything security / auth / secrets / privacy / logging | [`guidelines/security-privacy-logging.md`](guidelines/security-privacy-logging.md) |
| Installing or upgrading packages | [`guidelines/dependencies-supply-chain.md`](guidelines/dependencies-supply-chain.md) |
| Angular / frontend / Tailwind | [`guidelines/angular-frontend.md`](guidelines/angular-frontend.md) |
| Node / NestJS / API / MongoDB | [`guidelines/backend-nodejs.md`](guidelines/backend-nodejs.md) |
| UI/UX, components, accessibility, SEO | [`guidelines/ux-ui-seo.md`](guidelines/ux-ui-seo.md) |
| Writing tests, or verifying behavior | [`guidelines/testing.md`](guidelines/testing.md) |

> The table is the **router**. If a task spans several rows, read each relevant file before editing. Reading guideline files is non-destructive discovery — never ask permission to read them.

## Always-on rules (apply everywhere — no file needed)

These are the non-negotiables. The guideline files expand on them; this is the part that must always be in context.

- **Think before coding.** State assumptions; surface tradeoffs; if something is unclear, ask instead of guessing. When asked for a proposal or "what do you suggest?", **present the plan and wait** — do not start building until confirmed.
- **Simplicity first.** Write the minimum code that solves the problem. No speculative abstractions, no features beyond what was asked. If 200 lines could be 50, rewrite it.
- **Surgical changes.** Touch only what the request requires. Match the existing style even if you'd do it differently. Don't refactor or reformat unrelated code; list anything you noticed but didn't change under **"Observed, not changed:"** at the end.
- **Preserve comments.** Never delete or rewrite existing comments except to correct them. Add comments for non-obvious "why", never to restate the code.
- **Destructive actions need explicit confirmation.** Never delete files, data, or code, and never rename public APIs / exported symbols / routes / DB fields, without the user asking. Reading, searching, and exploring are always free.
- **Never `git commit` or `git push`** unless the user explicitly asks in that message. Stage, branch, and prepare freely; the commit is theirs to make. (See [git-and-versioning](guidelines/git-and-versioning.md).)
- **No secrets in code, logs, or output.** Never print, commit, or log credentials, tokens, or PII. (See [security](guidelines/security-privacy-logging.md).)
- **The linter is the source of truth for style.** Run ESLint/Prettier (or the project's formatter); never argue formatting.
- **Make it testable, and test it.** Design code so it can be tested; cover happy-path, edge, error, and security scenarios; new behavior isn't done until its tests pass. See [testing](guidelines/testing.md).
- **Read the project's docs before non-trivial work.** `README*`, `CLAUDE.md`/`AGENTS.md`, `docs/`, `.env.example`, `CHANGELOG*`. Reconcile your plan with them before editing.
- **Truth over agreement.** Be concise and direct. Don't reflexively validate the user as "right"; cross-check and base answers on first principles. Don't apologise reflexively.