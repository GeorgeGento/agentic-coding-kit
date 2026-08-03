---
name: analyze-team
description: Spawn a team of subagents to understand and map a codebase — module responsibilities, architecture, data/control flows, key abstractions, god nodes, and risk areas — then synthesize a structured architecture report. Use for "explain this codebase", "map the architecture", onboarding to an unfamiliar repo, or scoping before a big change. Understanding only — never modifies code.
---

# /analyze-team

Multi-agent codebase analysis. **Follow `guidelines/subagent-orchestration.md`** for mechanics — with one swap: there is nothing to refute here, so the skeptic pass is replaced by a **completeness critic** (guideline). This skill defines the reader scopes, synthesis, and output.

## Usage

```
/analyze-team <path> [--agents N] [--model ...] [--focus "..."]
```

Read-only. Produces a report, changes no code.

## If graphify is present

If `<path>/graphify-out/` exists, read `graphify-out/GRAPH_REPORT.md` first and treat architecture questions as graphify queries before fanning out — it already has god nodes + community structure.

## Reader agents (one subsystem per agent)

Split the repo by subsystem/package/layer — one reader each. Every reader returns, for its slice: **responsibility** (what it owns), **public surface** (entry points/exports), **key abstractions**, **dependencies** (in/out), **data/control flows** it participates in, and **risks/smells** (god objects, tight coupling, dead areas).

## Synthesize → critique → output

Merge the readers into one map: system overview, module responsibilities, cross-cutting flows, dependency graph, and a ranked risk list. Then run the **completeness critic** — "what subsystem, flow, or entry point did we miss?" — and do a second reader pass on the gaps. Output a single architecture report (`.team/analysis.md`).
