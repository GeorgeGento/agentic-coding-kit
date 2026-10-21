# Workflow & Process

How to approach tasks. Read for planning, multi-step work, and reviews.

## Think before coding

- State assumptions explicitly; if uncertain, ask. Don't hide confusion.
- If multiple interpretations exist, present them — don't silently pick one.
- If a simpler approach exists, say so. Push back when warranted.
- When asked "what do you suggest?" or for a proposal, **present the plan and wait for discussion**. Do NOT start building until confirmed.

## Simplicity first

- Minimum code that solves the problem. Nothing speculative, no features beyond what was asked.
- No abstractions for single-use code, and none built for imagined future callers. Reach for an abstraction only when the work is genuinely complex, repeated across many places, or fixing a bug that needs containment. For small direct edits (one label, one string, one key), inline it.
- No error handling for scenarios that cannot occur.

## Surgical changes in existing code

- Touch only what the request requires. Don't "improve" adjacent code, formatting, or style.
- Don't refactor working code unless explicitly asked (code/security review excepted — and even then apply basic principles, don't rewrite for taste).
- Match existing style even if you'd do it differently.
- List unrelated issues or dead code under **"Observed, not changed:"** at the end — don't fix them.
- Remove imports/variables/functions only if YOUR change orphaned them. Never remove pre-existing dead code without asking.

## Goal-driven execution

Define what "done" looks like in concrete terms before coding. Weak criteria ("make it work") force constant clarification; strong criteria ("returns 401 on missing token, 200 with a valid one, covered by a test") let you execute independently.

For multi-step tasks, state a brief plan:

1. [Step] → verify: [check]
2. [Step] → verify: [check]

Make success criteria verifiable and cover them with tests — treat tests as part of "done", not optional (see [testing](testing.md)).

## Review mode

- While editing, keep observations brief and at the end of the response.
- When explicitly asked to "review", produce findings only — what you'd change, why, and the tradeoff. Don't modify files until confirmed.

## TODO tracking

- Keep a `TODO.md` at the project root for non-trivial projects. Check it at session start; mark tasks done (`[x]`) or add new ones (`[ ]`). It gives continuity across sessions.

## Documentation operations

- Before non-trivial work, read existing docs (`README*`, `CLAUDE.md`/`AGENTS.md`, other agents' rule files such as `.cursor/rules/`, `.github/copilot-instructions.md`, `.windsurfrules`, `docs/`, `.env.example`, `CHANGELOG*`) and reconcile your plan with them. This is non-destructive discovery — never ask first. If docs conflict with code, note the discrepancy rather than trusting one silently.
- Update README / About / changelog when behavior, setup, commands, env vars, or security controls change.
- Every changelog entry has a **Changes to existing behaviour** section: each change, and what to watch after deploy (what could break, what to check). "None" is stated explicitly.
- **Plans live in the project**: `docs/plans/<topic>-plan.md` (or the project's own convention) — never only in a home-dir or harness-internal location. Open decisions the user must answer go in a separate `<topic>-decisions.md` linked from the plan. Finished reference docs stay at the top level of `docs/`.
- **Keep progress docs current**: when a planned item lands and passes its checks, update its plan/progress doc in the same turn (status, date, evidence).
- **Repo markdown by default**: write specs, plans, and write-ups as markdown in the repo. Don't publish them to external page/doc services unless the user asks in that message.
- Keep global instructions concise and high-signal. Move topic-specific rules into guideline files (as this repo does) and repeatable multi-step procedures into skills, rather than bloating `CLAUDE.md`.
- Never put real secrets, tokens, private URLs, or production data in docs — use placeholders and synthetic examples.
