# Git & Versioning

Read for git, commits, versioning, `.env`, deployment, and remote servers.

## Commit & push policy

- **Never `git commit` or `git push` unless the user explicitly asks in that message.** Stage, branch, set/adjust remotes, and prepare freely — the commit is theirs to make.
- When the user does ask to commit: first offer the full test suite (recommended; the user may skip — see [testing](testing.md)), then inspect the staged diff and verify no secrets, PII, build artifacts, or uploads are staged.
- **Never `git add -A` or `git add .`** — stage specific files by name.
- Keep commits small, reviewable, and scoped to one feature/fix. Don't mix refactors, formatting, dependency bumps, and feature work.
- Don't add AI attribution / `Co-Authored-By` unless the user asks for it.

## New projects

- Before non-trivial work in a folder without git, initialize git, create/verify `.gitignore`, and get a buildable baseline ready for an initial commit. Don't leave significant code with no version history. (The commit itself still waits for the user unless they've said to commit.)

## `.env` & secrets

- Every project that uses `.env` ships a `.env.example` with placeholder values and a comment per variable. Mirror every `.env` change into it (structure, order, comments). Never put real secrets in the example.
- **Never commit a real `.env`.** If one is already tracked, remove it from tracking (and history) immediately.
- Add upload/storage/runtime-data directories and log files to `.gitignore` **before** the first commit. Never commit user-generated content.
- For any gitignored sensitive file, also commit a safe `.example`/template plus short setup notes (which file to copy, what to fill, where to get values).

## Versioning

- **Single source of truth for the version: the root `package.json`.** Other files read from it at build time — never hardcode a second version. Run `npm run version:sync` if such a script exists.
- Bump the app version on real fixes/features; documentation- or policy-only edits don't need a bump. Actually edit the version field — don't just mention a version in the commit message.
- Display the version in the app (e.g. footer), read from the central source.

## Deployment

- **Never deploy automatically.** Deploy only on an explicit instruction ("deploy", "deploy now", "proceed with deploy") in the same conversation. Don't infer deployment from commit / push / build / "next steps". Otherwise stop at "ready to deploy".
- Before pushing to a shared branch, run the test suite if tests exist; never push failing tests.

## Remote server safety

- Never delete or modify files, configs, services, or data on a remote server without an explicit command from the user.
- Always back up before modifying remote state — nginx configs, PM2 configs, SSL certs, app directories, database dumps, system configs — into a timestamped directory (e.g. `/opt/backups/YYYY-MM-DD_HH-MM-SS/`).

## Confidential files

- Never commit confidential documents (audit/pentest reports, internal or client-facing docs, anything marked Internal/Confidential/Private). Gitignore or exclude them and share via secure channels.
