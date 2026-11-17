---
packages: [core]
type: feat
---

# Subagents get an auto-compact window

- `deploy.py`: a new `auto_compact_window` setting (profile, overridden by `~/.agent-memory/settings.toml`) is written into every Claude Code agent's frontmatter as `autoCompactWindow` (a plain integer; Claude Code reads `700k` in frontmatter as 700). Other tools are unchanged.
- `profiles/claude.toml`: `auto_compact_window = 700000`, matching the main session's `/autocompact 700k`.
- `core/memory-seed/settings.toml`: commented example of the override.
- Tests: frontmatter line rendered, absent when unset, user value wins over the profile.

## Changes to existing behaviour

Claude Code subagents compact at 700k tokens instead of the models' ~967k default.
