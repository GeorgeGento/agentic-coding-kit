---
packages: [core, profiles]
type: feat
---

# Review standards, codebase-graph guide, rules promoted from memory

General rules that lived in personal memory now ship with the rules, so every project and tool gets them:

- **Lean code rules** in coding-standards: extract on the third repeat, search before writing a parser/table/allow-list, no single-implementation abstractions, derived key lists, doc tags only when informative.
- **Risk-scaled review** in the feature playbook (one reviewer for ordinary code; reviewer + tester + security for auth, session, crypto, permission, or tenancy code) and **triage**: medium and above is fixed before a commit, low goes to the backlog.
- **New task types:** coherence audit (once per release, against the real app) and pen test (before any publish).
- **Review standards** (new guideline): one critical/high/medium/low severity scale; reviewer checklist (Google engineering practices), security baseline (OWASP ASVS 5.0, Top 10:2025, API Top 10:2023, MASVS, Electron/Tauri), tester test-design techniques, ui-ux WCAG 2.2 AA.
- **Codebase graph** (new guideline): when and how to use graphify (free incremental update, query, `affected` blast radius) and paste impact lists into reviewer/tester briefs.
- **Agents:** reports capped at about 30 lines; dev servers are never stopped or restarted, and tests never share their ports or databases; plans prefer small phases.
- **Changelog fragments:** one dated file per change instead of a hand-edited CHANGELOG; executors write them and releases generate the changelogs.
- **Profiles:** the security specialist runs on the strong model.
- **Loop guard and working commands** (ideas from microsoft/TokenEconomizer, as rules, not a dependency): the same failure three times means stop and ask or escalate; a corrected command form that works is recorded once in the project's `CLAUDE.md`.
- **`session_cost.py`** (Claude Code adapter): token use per session and per agent from the local logs: turns, fixed context, cache reads/writes, output, and the tools that filled the context. First run: about 44k tokens of fixed context per agent (rules are about 6k of it), and turn count dominates cost.
- **Context budget test:** a deploy test fails when the always-loaded instructions exceed 26 KB or an agent file exceeds 4 KB.
- **Finishing a task:** the Lead's report ends with a change description, a ready-to-paste commit message, and the fragment path. It still never commits on its own.

## Changes to existing behaviour

- **Feature checks:** they no longer spawn security for every diff, only for security-relevant code. Watch that auth-adjacent changes are classified as security-relevant.
- **Severity names:** blocker/major/minor are replaced by critical/high/medium/low in roles, the findings schema, and triage. Older `.team/findings.json` files use the old names.
- **Security model:** the security agent now runs on Opus (Claude Code, opencode) or `gpt-6.1-sol` (Codex), so security audits cost more per run but run less often.
- **Changelogs:** executors now write a `changes/` fragment as part of a task, so expect one new file per change in each project, and no CHANGELOG.md edits.
