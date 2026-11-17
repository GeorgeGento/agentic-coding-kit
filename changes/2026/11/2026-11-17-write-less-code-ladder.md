---
packages: [core]
type: feat
---

# Ladder before writing code

- `core/guidelines/coding-standards.md`: new first core principle. Before writing code, check in order: is it needed at all, does the codebase already do it, does the standard library/platform/framework provide it, does an installed dependency cover it; only then write the minimum that works. Safety, validation, accessibility and the `testing.md` coverage are never cut. The former "Grep before writing a parser, table, or allow-list" principle is folded into the codebase rung (same rule, same deliberate-copies exception) to stay within the always-loaded size budget.
- Idea borrowed from the `ponytail` skill; the package itself is not installed (no third-party hook packs).

## Changes to existing behaviour

Agents should prefer reuse, removal, and built-ins over new code more explicitly. Watch for agents skipping required tests in the name of "less code"; `testing.md` still wins.
