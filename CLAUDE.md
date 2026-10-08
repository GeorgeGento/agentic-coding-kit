# Working on agent-workflows

This repo is the **source** for global agent config. It is not itself a global config. Your global rules come from the deployed `~/.claude/CLAUDE.md`. This file only covers how to change the repo. Layout and deploy: [README.md](README.md).

- **Source of truth is `core/`.** Never hand-edit deployed copies (`~/.claude`, `~/.codex`, `~/.config/opencode`). Edit here, then redeploy.
- **Keep `core/` harness-neutral.** No tool-specific syntax (`@imports`, tool names, `~/.claude` paths) in `core/`. Put it in `deploy.py` rendering or `adapters/<tool>/`. Refer to agents by tier (`senior|mid|junior`), never by model name. Models live only in `profiles/`.
- **`core/rules.md` is the always-loaded file for every session on every tool.** Keep it lean. Anything situational goes in `core/guidelines/` or `core/protocols/`, with a router row.
- **Role and protocol files are inlined into every rendered agent.** Keep them short and self-contained. Don't use `'''` (it breaks Codex TOML rendering; a test catches it).
- **Tests:** `python -m unittest discover tests` (stdlib only). `deploy.py` and `core/bin/heavy.py` must work on Windows, macOS and Linux. Deploy tests use a throwaway fake home; never point tests at a real config dir.
- **Preview a deploy** with `python deploy.py --tool <tool> --dry-run` or `--target <temp dir>` before running it for real.
