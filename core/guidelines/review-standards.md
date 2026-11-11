# Review Standards

Read when you review, audit, or test someone else's change: the `reviewer`, `security`, `tester`, and `ui-ux` roles, and the Lead verifying their findings. Each section is a compact checklist that cites the public standard behind it, so a finding can be checked against the source instead of argued. The project's own guidelines (coding-standards, performance, security-privacy-logging, testing, ux-ui-seo) still apply on top.

## Severity (one scale for every role)

| Severity | Meaning | Examples |
| --- | --- | --- |
| **critical** | Exploitable now, or data loss/corruption, or the main flow is broken | auth bypass, cross-tenant read, injection reachable from input, migration that drops data |
| **high** | Wrong behaviour users will hit, or a security weakness with a plausible path | missing ownership check behind another guard, unhandled error on a common path, N+1 on a list endpoint, missing index on a production query |
| **medium** | Correct today but fragile, slow at expected scale, or a gap in required coverage | untested error path, race under concurrent use, unbounded read, duplicated logic that will drift, a11y failure on a secondary control |
| **low** | Style, naming, minor clarity, nice-to-have | a clearer name, a comment that restates code, small simplification |

**Blocker** in the protocols means critical or high. **Triage:** critical, high, and medium are fixed before the commit. Low goes to the project's `TODO.md` backlog. A finding without evidence (location plus a concrete failing input, scenario, or attack path) is not a finding: drop it or mark it `disputed`.

**Finding format:** `severity | file:line | what goes wrong | evidence | fix | standard id` (e.g. `ASVS V8.2.1`, `CWE-639`, `WCAG 2.4.7`). Use the findings schema in `protocols/teams.md` when the brief asks for JSON.

## Reviewer: correctness and design

Based on Google's engineering practices, "What to look for in a code review".

- **Design:** does the change belong here, fit the architecture, and avoid adding a second way to do something that already exists?
- **Functionality:** does it do what the brief says for every input class? Check edge cases, concurrency, error paths, and what users actually see.
- **Complexity:** could it be simpler? Look for single-implementation abstractions, a repeat that should be extracted (third occurrence), or a parser or table that already exists elsewhere (coding-standards, lean rules).
- **Tests:** do they exist, test behaviour rather than implementation, and fail if the code were wrong?
- **Performance** (performance guideline): passes that could merge, lookups inside loops, queries without an index, N+1, unbounded reads, sequential independent awaits.
- **Contracts:** types, public API, DB fields, migrations, env/config, and every change to existing behaviour (release readiness).
- **Naming and comments:** names explain intent; comments say why. Formatting belongs to the linter, never to review.

## Security: verification baseline

Baseline is **OWASP ASVS 5.0**, level 2 for anything with user accounts or user data, and level 1 for internal tools. Map risks to the **OWASP Top 10:2025** (and the **OWASP API Security Top 10:2023** for APIs). Cite ASVS requirement or CWE ids.

- **Access control** (A01; API1 BOLA, API5 function level; CWE-639, CWE-862): ownership, tenant, and role checks on every protected read **and** write, enforced server-side, failing closed. Is each concept (identity, tenant, scope, permission) decided in one place? Covers SSRF too (CWE-918).
- **Misconfiguration** (A02): debug off, secure headers (CSP, HSTS, frame options), CORS allow-list rather than `*` with credentials, no default credentials, and security features actually enabled rather than left optional.
- **Supply chain** (A03): pinned versions and a lockfile, no install scripts from unknown packages, no runtime remote code, and new dependencies justified (dependencies guideline).
- **Crypto** (A04): standard libraries only, current algorithms (argon2id/bcrypt for passwords, AES-GCM, TLS 1.2+), CSPRNG for tokens, and no secrets in code or logs.
- **Injection** (A05; CWE-79/89/78/22): parameterised queries, output encoding, no shell strings built from input, path normalisation, and schema validation at every boundary with unknown fields rejected.
- **Insecure design** (A06): rate limits on auth and expensive endpoints, abuse cases, and limits on sizes and counts.
- **Authentication and session** (A07): MFA where offered, reset and verification tokens single-use and short-lived, session rotation on login, cookie flags (`HttpOnly`, `Secure`, `SameSite`), CSRF on cookie auth, and no user enumeration.
- **Integrity** (A08): signed or verified updates and webhooks, and no unsafe deserialisation.
- **Logging and alerting** (A09): security events are logged without secrets or PII, and failures are visible.
- **Exceptional conditions** (A10): errors fail closed, no stack traces or internals leak to clients, and timeouts and partial failures leave consistent state.
- **Platform extras:**
  - **Android:** OWASP MASVS (storage, network/TLS, platform IPC, exported components, WebView settings).
  - **Electron:** the Electron security checklist (`contextIsolation`, `sandbox`, no `nodeIntegration`, validated IPC, a CSP).
  - **Tauri:** the capabilities and permissions model (least privilege, scoped filesystem and shell access, validated command inputs).

Every finding shows the attack path: who sends what, where, and what they gain. Real but unreachable is `disputed`. Rank by severity, adjusted for exploitability.

## Tester: test design

Use standard test design techniques (ISTQB) instead of ad-hoc cases:

- **Equivalence classes:** one test per class of input that should behave the same (valid, each kind of invalid, empty).
- **Boundary values:** at, just below, and just above each limit (0, 1, max, max+1, empty string, max length, unicode).
- **Decision tables:** every combination of conditions that changes the outcome (role × state × flag).
- **State transitions:** every allowed transition plus the forbidden ones (e.g. cancel after shipped).
- **Error and security cases:** invalid input, unauthorised and cross-tenant access, timeouts, retries, idempotency.
- **Mutation mindset:** for each assertion, ask whether a small change to the code (flip a condition, drop a line) would still pass. If it would, the test is too weak.
- **Property-based tests** for parsers, validators, serialisers, and pure transforms (round-trip, invariants), using the project's existing library if it has one.
- **UI:** automated accessibility checks (axe) in e2e where the project has Playwright.
- **No trace:** tests that touch the file system clean up on failure too; count temp leftovers before and after a run (testing guideline).

Unsure what the code should do? Ask; never encode a guessed expectation.

## UI/UX: interface quality

- **Accessibility:** **WCAG 2.2 level AA**. Cite criteria: 1.4.3 contrast, 2.1.1 keyboard, 2.4.7 focus visible, 2.4.11 focus not obscured, 2.5.8 target size, 3.3.x input assistance, 4.1.2 name/role/value.
- **Design:** the design brief and the anti-slop rules in ux-ui-seo; motion per motion-3d.
- If installed, use the `accessibility` skill (WCAG audit) and the `web-design-guidelines` skill (interface guidelines) as the checklist engines.
