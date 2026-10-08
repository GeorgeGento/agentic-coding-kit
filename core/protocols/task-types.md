# Task Types

The kinds of multi-agent work the Lead routes. Each one runs through the [hierarchy](hierarchy.md) (briefs down, reports up, audit at every level) and the [team mechanics](teams.md) (shared `.team/` state, id-keyed findings, adversarial verify, dedup, stop conditions). This file adds only what is specific to each type: who owns it, how the work is split, and what comes out.

Trigger phrases are hints, not commands. The Lead picks the type from intent: "review this thoroughly" → review, "is this secure?" → security, "build X" → feature.

**Mutating types** (feature, implement, test, refactor) produce a plan freely but **change code only after the user's go**: the invocation itself, "implement it", or an approved plan. Read-only types (analyze, review, security) never change code unless the user opts into fixes.

## feature: idea → tested implementation (the default playbook for "build X")

Owner: **Senior**. Phases, with state carried in `.team/`:
1. **Architect**: run *analyze* scoped to the areas the feature touches: patterns, extension points, constraints.
2. **Plan + GATE**: Senior writes `.team/plan.md` (design, tasks with `depends_on` and a tier each, acceptance criteria, data sizes and indexes, risks). The Lead presents it and **stops for approval**. Only an explicit "go end-to-end unattended" skips the gate.
3. **Build**: run *implement* from the plan.
4. **Check**: run *review* and *security* over the diff, in parallel. A blocker loops back to build and then re-check.
5. **Cover**: run *test* for the new behavior.
6. **Report**: what was built, the decisions, findings and their resolutions, test evidence, deferred items. Never commit.

## analyze: map a codebase (read-only)

Owner: **Senior** (synthesis); readers are **Mid**. If `graphify-out/` exists, read `graphify-out/GRAPH_REPORT.md` first.
- **Split** by subsystem/package/layer, one reader each. Each returns: responsibility, public surface, key abstractions, dependencies in/out, the data/control flows it takes part in, and risks/smells (god objects, tight coupling, dead areas).
- **Synthesize** one map: overview, module responsibilities, cross-cutting flows, dependency graph, ranked risks. Then run the **completeness critic** ("which subsystem, flow, or entry point did we miss?") and a second pass on the gaps.
- **Output:** `.team/analysis.md`.

## review: correctness + quality (read-only; `--fix` to apply)

Owner: **Senior**; finders **Mid**, verifiers **Mid** (Senior for disputed blockers). One module slice and one lens per finder:
- **correctness**: logic errors, null/edge cases, async/races, unhandled error paths.
- **performance**: per [performance](../guidelines/performance.md): mergeable passes, lookups inside loops, queries without a serving index, N+1, unbounded reads/caches, sequential independent awaits.
- **reuse/duplication**: duplicated logic, a shared utility that should have been used, copy-paste drift.
- **simplification**: over-abstraction, dead code, needless indirection.
- **contracts/types**: wrong types, `any`, unsafe assertions, public-API traps.

Verify in refute mode. **Output:** `volN.md`, ranked confirmed-first, blocker → minor. For a small diff, the built-in single-pass `/code-review` is enough. Use this type when the surface needs parallel coverage.

## security: audit (read-only; fixes on opt-in)

Owner: **Senior**. The standard is [security-privacy-logging](../guidelines/security-privacy-logging.md). Lenses:
- **authorization**: object/ownership/tenant checks on every protected read+write; fail-open guards; missing role checks.
- **injection**: XSS, SQL/NoSQL, command, path, template, unsafe deserialization.
- **secrets & logging**: secrets in code/logs/output, PII logged, keys mishandled.
- **auth & session**: password/reset/MFA flows, fixation, CSRF, cookie flags, enumeration/brute-force.
- **supply-chain**: risky deps, lifecycle scripts, unpinned packages, remote runtime loads.
- **crypto & data-at-rest**: weak hashing, plaintext sensitive data, insecure randomness.

Verifiers refute by **exploitability**: "show the concrete attack path, or refute." A finding that is real but unreachable is `disputed`, not `blocker`. Rank by severity × exploitability.

## implement: build an approved plan or task list (mutating)

Owner: **Senior** (or **Mid** for a small single-module list).
1. **Decompose** into tasks with `depends_on`, a tier each, and acceptance criteria. Record them in `.team/findings.json`. Vague input gets resolved into tasks and confirmed before building.
2. **Build in parallel**: one agent per independent task, with disjoint SCOPE or an isolated worktree. Dependency chains run in order.
3. **Audit each** (hierarchy): diff and evidence against acceptance, slice green.
4. **Merge** in `depends_on` order, re-run the full suite, fix regressions.

## test: find gaps, write tests (mutating)

Owner: **Mid**; mechanical test files go to **Junior**. The standard is [testing](../guidelines/testing.md).
- **Gap finding**, one module per agent: map the public API and observable behavior against existing tests. Record missing realistic scenarios (happy/edge/error/security/concurrency) by risk.
- **Write**: use the project's existing runner (never a second one), behavior-named tests, deterministic only. Run them to green. A bug found while testing is a finding to surface, not to paper over. Never weaken assertions.

## refactor: behavior-preserving cleanup (mutating)

Owner: **Senior** (decides targets); **Mid** applies.
- **Guardrails:** behavior-preserving only; no API/route/export/DB-field renames without a separate ask. The suite passes before and after each refactor. If the behavior has no test coverage, add characterization tests first or skip it.
- **Targets:** duplication to extract, over-long units to split, poor seams, dead code, unclear names, magic values, and performance smells per the guideline. Record each with its blast radius.
- **Apply** independent refactors in isolation: apply → lint/build/tests → merge in order. A real bug found along the way gets surfaced, not silently fixed.

## Common knobs

`agents N` · `tier senior|mid|junior` (override the default tier) · `verify all|blockers|none` · `focus "..."` · `fix`/`auto` (mutating opt-in). Defaults: 5 agents, Mid finders, verify all, no auto.
