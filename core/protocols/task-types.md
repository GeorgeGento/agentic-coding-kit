# Task Types

The kinds of multi-agent work the Lead routes. Each one runs through the [hierarchy](hierarchy.md) (briefs down, reports up, one Lead audit) and the [team mechanics](teams.md) (shared `.team/` state, id-keyed findings, adversarial verify, dedup, stop conditions). This file adds only what is specific to each type: who owns it, how the work is split, and what comes out.

Trigger phrases are hints, not commands. The Lead picks the type from intent: "review this thoroughly" → review, "is this secure?" → security, "build X" → feature, "ready to release?" → coherence, then pentest.

**Mutating types** (feature, implement, test, refactor) produce a plan freely but **change code only after the user's go**: the invocation itself, "implement it", or an approved plan. Read-only types (analyze, review, security) never change code unless the user opts into fixes.

## feature: idea → tested implementation (the default playbook for "build X")

Owner: **Lead**. Phases, with state carried in `.team/`:
1. **Architect**: run *analyze* scoped to the areas the feature touches: patterns, extension points, constraints.
2. **Plan + GATE**: the Lead writes `.team/plan.md` (design, precise tasks with `depends_on`, who builds each (Lead or executor), acceptance criteria, data sizes and indexes, risks), presents it, and **stops for approval**. A feature with new screens or a visual redesign also gets a **design brief** in the plan ([ux-ui-seo](../guidelines/ux-ui-seo.md#design-direction)); executors building UI get it pasted into their brief. Only an explicit "go end-to-end unattended" skips the gate.
3. **Build**: run *implement* from the plan. UI work ends with the look-compare-iterate loop against the design brief before it counts as built.
4. **Check (opt-in, recommended)**: prompt the user (structured question if the harness has one) to run independent auditors over the diff, recommending yes. **Scale to risk:** one `reviewer` (correctness, regressions in existing behaviour, release readiness: migrations, env/config changes, deploy order) for ordinary code; `reviewer` + `tester` + `security` in parallel only when the diff touches auth, sessions, crypto, permissions, tenancy, or other security-relevant code. Add `ui-ux` (reviews screenshots against the design brief) / `e2e` when the diff touches UI. **Triage** (severity scale in [review-standards](../guidelines/review-standards.md)): before a commit, fix findings of medium severity and above; low ones go to a backlog (the project's `TODO.md`) and get done once, in a cheap batch. A medium-or-above finding loops back to build and then re-check; don't call it ready until every check is clean. If skipped, say so in the report.
5. **Cover**: run *test* for the new behavior (`tester` specialist, or the executor's own tests when they already cover it).
6. **Report**: what was built, the decisions, findings and their resolutions, test evidence, changes to existing behaviour and what to watch after deploy, deferred items. Never commit.

## analyze: map a codebase (read-only)

Owner: **Lead** (synthesis); readers are executors (read-only brief). If `graphify-out/` exists, read `graphify-out/GRAPH_REPORT.md` first.
- **Split** by subsystem/package/layer, one reader each. Each returns: responsibility, public surface, key abstractions, dependencies in/out, the data/control flows it takes part in, and risks/smells (god objects, tight coupling, dead areas).
- **Synthesize** one map: overview, module responsibilities, cross-cutting flows, dependency graph, ranked risks. Then run the **completeness critic** ("which subsystem, flow, or entry point did we miss?") and a second pass on the gaps.
- **Output:** `.team/analysis.md`.

## review: correctness + quality (read-only; `--fix` to apply)

Owner: **Lead**; finders and verifiers are `reviewer` specialists (escalation for disputed blockers). One module slice and one lens per finder:
- **correctness**: logic errors, null/edge cases, async/races, unhandled error paths.
- **performance**: per [performance](../guidelines/performance.md): mergeable passes, lookups inside loops, queries without a serving index, N+1, unbounded reads/caches, sequential independent awaits.
- **reuse/duplication**: duplicated logic, a shared utility that should have been used, copy-paste drift.
- **simplification**: over-abstraction, dead code, needless indirection.
- **contracts/types**: wrong types, `any`, unsafe assertions, public-API traps.

Verify in refute mode. **Output:** `volN.md`, ranked confirmed-first, critical → low. For a small diff, the built-in single-pass `/code-review` is enough. Use this type when the surface needs parallel coverage.

## security: audit (read-only; fixes on opt-in)

Owner: **Lead**; finders and verifiers are `security` specialists. The standard is [security-privacy-logging](../guidelines/security-privacy-logging.md). Lenses:
- **authorization**: object/ownership/tenant checks on every protected read+write; fail-open guards; missing role checks.
- **injection**: XSS, SQL/NoSQL, command, path, template, unsafe deserialization.
- **secrets & logging**: secrets in code/logs/output, PII logged, keys mishandled.
- **auth & session**: password/reset/MFA flows, fixation, CSRF, cookie flags, enumeration/brute-force.
- **supply-chain**: risky deps, lifecycle scripts, unpinned packages, remote runtime loads.
- **crypto & data-at-rest**: weak hashing, plaintext sensitive data, insecure randomness.

Verifiers refute by **exploitability**: "show the concrete attack path, or refute." A finding that is real but unreachable is `disputed`, not `blocker`. Rank by severity × exploitability.

## coherence: whole-change audit, once per release (read-only)

Owner: **Lead**; `reviewer`, `tester`, and `security` in parallel, against the **real running app**, not only unit tests. Per-plan checks can't see the holes between plans or between a framework and the app that uses it.
- **One concept, one place:** each concept (identity, tenant, platform, scope, permission, origin, device) is decided in exactly one place with one rule. Flag anything resolved in one place and taken raw in another, and caches or gates that can disagree.
- **Wired, not optional:** the app actually turns on the framework's security features (device binding, CSRF, rate limits, …) instead of leaving them optional.
- Run it once per release, before the pen test. Clean per-plan checks are no reason to skip it. Findings follow the normal triage (verify, bounce, medium and above block).

## pentest: live attack before any publish (read-only)

Owner: **Lead**; two `security` agents on the strong model, split by attack surface (e.g. API and auth flows vs. UI, client, and supply chain), against the live app, last thing before a release. Each shows concrete attack paths; the Lead verifies them and does the **chain pass**: combining low findings into a real exploit path. Test accounts and a throwaway environment only; never production data.

## implement: build an approved plan or task list (mutating)

Owner: **Lead**.
1. **Decompose** into precise tasks with `depends_on`, who builds each (Lead or executor), and acceptance criteria. Record them in `.team/findings.json`. Vague input gets resolved into tasks and confirmed before building.
2. **Build**: the Lead does small tasks itself; independent tasks go to executors in parallel (within `max_parallel`), with disjoint SCOPE or a worktree. Dependency chains run in order.
3. **Audit each** (hierarchy, three stages): spec first, then pattern conformance, then quality, slice green.
4. **Integrate** in `depends_on` order (worktree diffs applied uncommitted), re-run the full suite, fix regressions, clean up worktrees.

## test: find gaps, write tests (mutating)

Owner: **Lead**; gap finding and test writing go to `tester` specialists, e2e journeys to `e2e`. The standard is [testing](../guidelines/testing.md).
- **Gap finding**, one module per agent: map the public API and observable behavior against existing tests. Record missing realistic scenarios (happy/edge/error/security/concurrency) by risk.
- **Write**: use the project's existing runner (never a second one), behavior-named tests, deterministic only. Run them to green. A bug found while testing is a finding to surface, not to paper over. Never weaken assertions.

## refactor: behavior-preserving cleanup (mutating)

Owner: **Lead** (decides targets); the Lead or executors apply.
- **Guardrails:** behavior-preserving only; no API/route/export/DB-field renames without a separate ask. The suite passes before and after each refactor. If the behavior has no test coverage, add characterization tests first or skip it.
- **Targets:** duplication to extract, over-long units to split, poor seams, dead code, unclear names, magic values, and performance smells per the guideline. Record each with its blast radius.
- **Apply** independent refactors in isolation: apply → lint/build/tests → merge in order. A real bug found along the way gets surfaced, not silently fixed.

## Common knobs

`agents N` · `role <name>` (override the default role) · `verify all|blockers|none` · `focus "..."` · `fix`/`auto` (mutating opt-in). Defaults: read-only fan-outs 5 agents; code-changing agents capped by `max_parallel`; verify all; no auto.
