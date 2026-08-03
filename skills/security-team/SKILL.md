---
name: security-team
description: Spawn a team of subagents to run a security audit of a codebase — authorization, injection, secrets/logging, auth/session, supply-chain, crypto/data-at-rest — adversarially verify each issue by whether it actually exploits, and produce a threat-ranked report. Use for "security review", "audit for vulnerabilities", or a scaled security pass on a large or published codebase.
---

# /security-team

Multi-agent security audit. **Follow `guidelines/subagent-orchestration.md`** for all mechanics, and treat **`guidelines/security-privacy-logging.md`** as the standard the finders check against. This skill defines the security lenses, verification angle, and output.

## Usage

```
/security-team <path> [--agents N] [--model ...] [--verify all|blockers|none] [--focus "..."]
```

Read-only by default (audits don't auto-patch). Apply fixes only on explicit opt-in per the guideline.

## Finder lenses (one scope + one lens per agent)

- **authorization** — object-level/ownership/tenant checks on every protected read+write; fail-open guards; missing role checks.
- **injection** — XSS, SQL/NoSQL, command, path, template, unsafe deserialization; unsanitized sinks.
- **secrets & logging** — secrets in code/logs/output, PII logged, tokens/keys mishandled.
- **auth & session** — password/reset/MFA flows, session fixation, CSRF, cookie flags, enumeration/brute-force.
- **supply-chain** — risky deps, lifecycle scripts, unpinned/unaudited packages, remote/CDN runtime loads.
- **crypto & data-at-rest** — weak hashing, plaintext sensitive data, missing field-level encryption, insecure randomness.

Scope by module; weight by `--focus`. Prefer the installed `security-auditor` subagent (`~/.claude/agents/`) for finder/verifier role diversity when present.

## Verify → output

Verifiers refute by **exploitability**: "show the concrete attack path, or refute." Rank confirmed issues by severity × exploitability. Note any finding that's real but not reachable as `disputed`, not `blocker`.
