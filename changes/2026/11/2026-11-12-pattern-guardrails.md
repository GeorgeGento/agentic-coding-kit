---
packages: [core]
type: feat
---

# Pattern guardrails for building agents

Sub-agent work kept drifting from the projects' patterns (an i18n convention nobody wrote down, hard-coded template text,
new mechanisms next to existing ones): agents copied the nearest code or invented, and the Lead's audit checked tests and
screenshots, not the shape of the code. Now:

- **Executor, step 2 "Prior art before code":** read the project's "Patterns to follow" and the brief's PATTERNS; every new
  piece copies an existing pattern; never a second way, never an invented one; escalate when nothing fits.
- **Agent protocol:** the same rule in the inlined part, and a `PATTERNS:` line in every report (`piece -> path`, or
  "new: why" only with the Lead's OK).
- **Brief:** a `PATTERNS:` field (the project's lines for the area + canonical files).
- **Audit: three stages** (spec, pattern conformance, quality); a wrong shape bounces even when the tests pass; a fresh-eyes
  reviewer may do the pattern pass on large diffs. Lead role, hierarchy, task types and README updated.

## Changes to existing behaviour

- Executors may now stop with `escalate` when no existing pattern fits, instead of inventing one.
- Reports carry a new `PATTERNS:` line; the Lead's audit gains a stage.
