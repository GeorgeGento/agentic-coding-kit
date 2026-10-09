#!/usr/bin/env python3
"""Deploy agent-workflows into an AI coding agent's config directory.

Renders core/ (rules, guidelines, roles, protocols, skills) for one harness:

  claude-code -> ~/.claude : CLAUDE.md (@imports), agents/<tier>.md, skills/,
                             a PreToolUse hook routing heavy commands to the queue
  codex       -> ~/.codex  : AGENTS.md (always-loaded files inlined),
                             agents/<tier>.toml, skills in ~/.agents/skills,
                             the queue's lock dir made writable in its sandbox (config.toml)
  opencode    -> ~/.config/opencode : AGENTS.md (inlined), agents/<tier>.md,
                             skills/, a plugin routing heavy bash commands to the queue

Tier models come from profiles/<name>.toml. The heavy-command queue
(core/bin/heavy.py) is shared by all harnesses at ~/.agent-workflows/bin/.
Anything overwritten is backed up to <target>/.deploy-backups/ first.

Usage:
    python deploy.py                          # claude-code, profile "claude"
    python deploy.py --tool codex             # codex, profile "openai"
    python deploy.py --tool opencode          # opencode, profile "opencode"
    python deploy.py --profile local          # pick another tier->model profile
    python deploy.py --dry-run                # show what would happen, change nothing
    python deploy.py --link                   # symlink copied dirs (edits stay live)
    python deploy.py --target PATH            # deploy somewhere other than the default
    python deploy.py --no-hook                # don't install the queue hook/plugin/sandbox root
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
CORE = REPO_ROOT / "core"
ADAPTERS = REPO_ROOT / "adapters"
PROFILES_DIR = REPO_ROOT / "profiles"
RULES_FILE = CORE / "rules.md"
HIERARCHY_PROTOCOL = CORE / "protocols" / "hierarchy.md"
HEAVY_SCRIPT = CORE / "bin" / "heavy.py"

# core/ dirs the repo fully owns -> replaced wholesale at <target>/<name>.
OWNED_DIRS = ("guidelines", "roles", "protocols")
# Files the instructions file loads every session (paths relative to <target>).
ALWAYS_LOADED = (
    "guidelines/coding-standards.md",
    "guidelines/workflow.md",
    "guidelines/testing.md",
    "guidelines/performance.md",
    "roles/lead.md",
)
ALWAYS_LOADED_MARKER = "{{ALWAYS_LOADED}}"
# The Lead is the main session, not a subagent; it is loaded via the instructions file.
MAIN_SESSION_ROLE = "lead"
# Skills folded into protocols/task-types.md; removed (backed up) from old deploys.
RETIRED_SKILLS = ("agent-orchestrator", "analyze-team", "feature-team", "implement-team",
                  "refactor-team", "review-team", "security-team", "test-team")
# Shared, harness-neutral home for the heavy queue (script + lock files).
SHARED_DIRNAME = ".agent-workflows"
HOOK_MATCHER = "Bash|PowerShell"
OPENCODE_PLUGIN = ADAPTERS / "opencode" / "plugins" / "heavy-queue.js"
HOOK_ID = "heavy.py\" hook"  # identifies our hook entry inside settings.json
CODEX_SANDBOX_TABLE = "sandbox_workspace_write"
CODEX_SANDBOX_HEADER = re.compile(rf"^\[{CODEX_SANDBOX_TABLE}\][ \t]*(#.*)?$", re.MULTILINE)
RELATIVE_LINK = re.compile(r"\]\((guidelines|protocols|roles)/")


@dataclass(frozen=True)
class Tool:
    """How one harness consumes the rendered config."""
    name: str
    default_target: Path
    default_profile: str
    instructions_file: str
    agent_format: str  # "claude" | "codex" | "opencode"
    inline_always_loaded: bool  # False -> @import lines (Claude Code)
    hook: str | None  # how the heavy queue is wired in: "settings" | "plugin" | "sandbox" | None
    home_depth: int = 1  # how many levels above the target the user's home is

    @property
    def agent_ext(self) -> str:
        return ".toml" if self.agent_format == "codex" else ".md"

    def home(self, target: Path) -> Path:
        """The home dir implied by target, so --target sandboxes everything (tests, dry runs)."""
        return target.parents[self.home_depth - 1]

    def skills_dir(self, target: Path) -> Path:
        # Codex reads user skills from ~/.agents/skills, not from inside ~/.codex.
        return self.home(target) / ".agents" / "skills" if self.name == "codex" else target / "skills"


TOOLS = {
    "claude-code": Tool("claude-code", Path.home() / ".claude", "claude", "CLAUDE.md",
                        "claude", inline_always_loaded=False, hook="settings"),
    "codex": Tool("codex", Path.home() / ".codex", "openai", "AGENTS.md",
                  "codex", inline_always_loaded=True, hook="sandbox"),
    "opencode": Tool("opencode", Path.home() / ".config" / "opencode", "opencode", "AGENTS.md",
                     "opencode", inline_always_loaded=True, hook="plugin", home_depth=2),
}


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def load_profile(name: str) -> dict[str, str]:
    """Return the tier -> model mapping from profiles/<name>.toml ("" = inherit)."""
    with open(PROFILES_DIR / f"{name}.toml", "rb") as fh:
        return tomllib.load(fh)["models"]


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a '---'-delimited frontmatter block (simple `key: value` lines) from the body."""
    _, front, body = text.split("---", 2)
    meta = dict(line.split(":", 1) for line in front.strip().splitlines())
    return {k.strip(): v.strip() for k, v in meta.items()}, body.strip()


def absolutize_links(text: str, root: Path) -> str:
    """Point relative guideline/protocol/role links at the deployed copies.

    The model reads these paths from the project's working directory, where a
    relative `guidelines/x.md` would not resolve.
    """
    text = RELATIVE_LINK.sub(lambda m: f"]({root.as_posix()}/{m.group(1)}/", text)
    return text.replace("](README.md)", f"]({root.as_posix()}/README.md)")


def render_instructions(tool: Tool, rules: str, target: Path) -> str:
    """Render core/rules.md as the harness's global instructions file.

    Example:
        render_instructions(TOOLS["codex"], RULES_FILE.read_text(), Path("~/.codex"))
    """
    if tool.inline_always_loaded:
        parts = []
        for rel in ALWAYS_LOADED:
            text = (CORE / rel).read_text(encoding="utf-8")
            if text.startswith("---"):
                text = split_frontmatter(text)[1]
            parts.append(f"<!-- {rel} -->\n\n{text.strip()}")
        loaded = "\n\n".join(parts)
    else:
        loaded = "\n".join(f"@{rel}" for rel in ALWAYS_LOADED)
    return absolutize_links(rules.replace(ALWAYS_LOADED_MARKER, loaded), target)


def render_agent(tool: Tool, role_text: str, model: str, protocol_text: str,
                 target: Path) -> str:
    """Render a role file as a subagent definition for the given harness.

    The protocol is inlined so each agent is self-contained: a subagent starts
    with no context beyond its definition and the brief it is handed.

    Example:
        render_agent(TOOLS["claude-code"], Path("core/roles/mid.md").read_text(),
                     "claude-sonnet-5-5", HIERARCHY_PROTOCOL.read_text(), Path("~/.claude"))
    """
    meta, body = split_frontmatter(role_text)
    instructions = absolutize_links(
        f"{body}\n\n"
        f"Coding, testing, performance and other guidelines live in `{target.as_posix()}/guidelines/` "
        "— read the ones the brief or the task touches (performance.md always).\n\n"
        f"{protocol_text.strip()}\n",
        target,
    )
    if tool.agent_format == "codex":
        # Literal multi-line string: no escaping needed as long as ''' never appears.
        if "'''" in instructions:
            raise ValueError(f"role {meta['name']} contains ''' and can't be rendered to TOML")
        model_line = f"model = {json.dumps(model)}\n" if model else ""
        return (f"name = {json.dumps(meta['name'])}\n"
                f"description = {json.dumps(meta['description'])}\n"
                f"{model_line}developer_instructions = '''\n{instructions}'''\n")
    if tool.agent_format == "opencode":
        # opencode names the agent after the file; `mode: subagent` keeps it out of the main picker.
        model_line = f"model: {model}\n" if model else ""
        return (f"---\ndescription: {meta['description']}\nmode: subagent\n{model_line}---\n\n"
                f"{instructions}")
    front = "\n".join(f"{k}: {v}" for k, v in meta.items())
    return f"---\n{front}\nmodel: {model or 'inherit'}\n---\n\n{instructions}"


def hook_command(heavy_path: Path) -> str:
    return f'"{Path(sys.executable).as_posix()}" "{heavy_path.as_posix()}" hook'


def render_opencode_plugin(template: str, heavy_path: Path) -> str:
    """Fill the opencode queue plugin with this machine's python and heavy.py paths."""
    return (template.replace("__PYTHON__", json.dumps(Path(sys.executable).as_posix()))
                    .replace("__HEAVY__", json.dumps(heavy_path.as_posix())))


def merge_hook(settings: dict, command: str) -> dict:
    """Return settings with our PreToolUse queue hook added or refreshed (idempotent).

    Other hooks and keys are preserved; the input is not mutated.

    Example:
        merge_hook({}, '"python" "/h/.agent-workflows/bin/heavy.py" hook')
    """
    merged = json.loads(json.dumps(settings))
    pre = merged.setdefault("hooks", {}).setdefault("PreToolUse", [])
    for entry in pre:
        for hook in entry.get("hooks", []):
            if HOOK_ID in hook.get("command", ""):
                hook["command"] = command
                return merged
    pre.append({"matcher": HOOK_MATCHER, "hooks": [{"type": "command", "command": command}]})
    return merged


def add_codex_writable_root(text: str, root: str) -> str | None:
    """Return config.toml text with `root` in [sandbox_workspace_write].writable_roots.

    Returns the text unchanged if `root` is already listed, or None if the
    existing writable_roots can't be edited safely as text (left to the user).
    Raises tomllib.TOMLDecodeError on invalid TOML.

    Example:
        add_codex_writable_root("", "/h/.agent-workflows/heavy")
        # -> '[sandbox_workspace_write]\nwritable_roots = ["/h/.agent-workflows/heavy"]\n'
    """
    table = tomllib.loads(text).get(CODEX_SANDBOX_TABLE, {})
    roots = table.get("writable_roots")
    if isinstance(roots, list) and root in roots:
        return text
    if roots is not None:
        return None
    entry = f"writable_roots = [{json.dumps(root)}]"
    header = CODEX_SANDBOX_HEADER.search(text)
    if header:
        updated = f"{text[:header.end()]}\n{entry}{text[header.end():]}"
    else:
        section = (f"# agent-workflows heavy-command queue: lock files must be writable from the sandbox\n"
                   f"[{CODEX_SANDBOX_TABLE}]\n{entry}\n")
        updated = f"{text.rstrip()}\n\n{section}" if text.strip() else section
    # Text edits can't handle every layout (e.g. the table set via dotted keys).
    try:
        ok = root in tomllib.loads(updated)[CODEX_SANDBOX_TABLE]["writable_roots"]
    except (tomllib.TOMLDecodeError, KeyError, TypeError):
        ok = False
    return updated if ok else None


class Deployer:
    def __init__(self, tool: Tool, target: Path, *, profile: str, link: bool,
                 dry_run: bool, hook: bool, stamp: str) -> None:
        self.tool = tool
        self.target = target
        self.profile = profile
        self.link = link
        self.dry = dry_run
        self.hook = hook
        self.stamp = stamp
        self.shared = tool.home(target) / SHARED_DIRNAME
        self.steps = 0

    def log(self, msg: str) -> None:
        print(("[dry-run] " if self.dry else "") + msg)
        self.steps += 1

    def _backup(self, dest: Path) -> None:
        """Move an existing dest out of the way before we write over it.

        Backups live in <target>/.deploy-backups/, NOT next to dest: a sibling
        `<skill>.bak-*` inside skills/ shows up as a phantom skill in Claude Code.
        """
        if dest.is_symlink() or dest.exists():
            bak_dir = self.target / ".deploy-backups"
            bak = bak_dir / f"{dest.name}.bak-{self.stamp}"
            self.log(f"backup  {dest}  ->  .deploy-backups/{bak.name}")
            if not self.dry:
                bak_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(os.fspath(dest), os.fspath(bak))  # handles file/dir/symlink

    def _place(self, src: Path, dest: Path) -> None:
        """Symlink or copy src -> dest. Caller has already cleared dest."""
        if not self.dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
        if self.link:
            try:
                if not self.dry:
                    os.symlink(os.fspath(src), os.fspath(dest),
                               target_is_directory=src.is_dir())
                self.log(f"link    {dest}  ->  {src}")
                return
            except OSError as exc:  # Windows without privilege, etc.
                self.log(f"! symlink failed ({exc}); copying instead")
        if src.is_dir():
            if not self.dry:
                shutil.copytree(src, dest)
        elif not self.dry:
            shutil.copy2(src, dest)
        self.log(f"copy    {src}  ->  {dest}")

    def _write(self, dest: Path, content: str) -> None:
        """Back up dest, then write generated content (never symlinked)."""
        self._backup(dest)
        if not self.dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
        self.log(f"render  {dest}")

    def deploy_owned(self) -> None:
        for name in OWNED_DIRS:
            dest = self.target / name
            self._backup(dest)
            self._place(CORE / name, dest)
        self._backup(self.target / "README.md")
        self._place(REPO_ROOT / "README.md", self.target / "README.md")

    def deploy_instructions(self) -> None:
        rules = RULES_FILE.read_text(encoding="utf-8")
        self._write(self.target / self.tool.instructions_file,
                    render_instructions(self.tool, rules, self.target))

    def deploy_agents(self, models: dict[str, str]) -> None:
        protocol = HIERARCHY_PROTOCOL.read_text(encoding="utf-8")
        for role_path in sorted((CORE / "roles").glob("*.md")):
            tier = role_path.stem
            if tier == MAIN_SESSION_ROLE:
                continue
            content = render_agent(self.tool, role_path.read_text(encoding="utf-8"),
                                   models.get(tier, ""), protocol, self.target)
            self._write(self.target / "agents" / f"{tier}{self.tool.agent_ext}", content)

    def deploy_skills(self) -> None:
        """Merge skills child-by-child so sibling (user-installed) skills survive."""
        skills_dir = self.tool.skills_dir(self.target)
        sources = [CORE / "skills", ADAPTERS / self.tool.name / "skills"]
        for src_dir in (s for s in sources if s.is_dir()):
            for child in sorted(src_dir.iterdir()):
                dest = skills_dir / child.name
                self._backup(dest)
                self._place(child, dest)
        for name in RETIRED_SKILLS:
            if (skills_dir / name).exists():
                self.log(f"retire  {name} (folded into protocols/task-types.md)")
                self._backup(skills_dir / name)

    def deploy_heavy(self) -> None:
        dest = self.shared / "bin" / "heavy.py"
        self._backup(dest)
        self._place(HEAVY_SCRIPT, dest)

    def deploy_plugin(self) -> None:
        content = render_opencode_plugin(OPENCODE_PLUGIN.read_text(encoding="utf-8"),
                                         self.shared / "bin" / "heavy.py")
        self._write(self.target / "plugins" / OPENCODE_PLUGIN.name, content)

    def deploy_hook(self) -> None:
        settings_path = self.target / "settings.json"
        settings = {}
        if settings_path.exists():
            try:
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                self.log(f"! {settings_path} is not valid JSON ({exc}); queue hook NOT installed")
                return
        merged = merge_hook(settings, hook_command(self.shared / "bin" / "heavy.py"))
        if merged == settings:
            self.log(f"ok      {settings_path} (queue hook already present)")
            return
        if settings_path.exists() and not self.dry:
            bak_dir = self.target / ".deploy-backups"
            bak_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(settings_path, bak_dir / f"settings.json.bak-{self.stamp}")
        self._write_settings(settings_path, merged)

    def deploy_sandbox_root(self) -> None:
        """Let Codex's workspace-write sandbox write the queue's lock files."""
        lock_dir = self.shared / "heavy"
        config_path = self.target / "config.toml"
        text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
        try:
            updated = add_codex_writable_root(text, lock_dir.as_posix())
        except tomllib.TOMLDecodeError as exc:
            self.log(f"! {config_path} is not valid TOML ({exc}); sandbox root NOT added")
            return
        if not self.dry:
            # The sandbox can't create it later: its parent isn't writable there.
            lock_dir.mkdir(parents=True, exist_ok=True)
        if updated is None:
            self.log(f"! {config_path}: add {lock_dir.as_posix()!r} to "
                     f"[{CODEX_SANDBOX_TABLE}] writable_roots yourself")
        elif updated == text:
            self.log(f"ok      {config_path} (queue lock dir already writable)")
        else:
            if config_path.exists() and not self.dry:
                bak_dir = self.target / ".deploy-backups"
                bak_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(config_path, bak_dir / f"config.toml.bak-{self.stamp}")
            if not self.dry:
                config_path.parent.mkdir(parents=True, exist_ok=True)
                config_path.write_text(updated, encoding="utf-8")
            self.log(f"sandbox {config_path} (writable_roots += {lock_dir.as_posix()})")

    def _write_settings(self, path: Path, settings: dict) -> None:
        if not self.dry:
            path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        self.log(f"hook    {path} (PreToolUse {HOOK_MATCHER} -> heavy queue)")

    def run(self) -> None:
        models = load_profile(self.profile)
        self.log(f"tool:    {self.tool.name}")
        self.log(f"target:  {self.target}")
        self.log(f"profile: {self.profile}")
        self.log(f"mode:    {'symlink' if self.link else 'copy'}")
        self.deploy_owned()
        self.deploy_instructions()
        self.deploy_agents(models)
        self.deploy_skills()
        self.deploy_heavy()
        if self.hook and self.tool.hook == "settings":
            self.deploy_hook()
        elif self.hook and self.tool.hook == "plugin":
            self.deploy_plugin()
        elif self.hook and self.tool.hook == "sandbox":
            self.deploy_sandbox_root()
        print()
        print(f"Done ({self.steps} step(s)).")
        lead = models.get(MAIN_SESSION_ROLE) or "(your choice)"
        where = {"claude-code": "/config or settings.json \"model\"",
                 "codex": "\"model\" in ~/.codex/config.toml",
                 "opencode": "\"model\" in ~/.config/opencode/opencode.json"}[self.tool.name]
        print(f"Reminder: set the Lead (main session) model to {lead} via {where}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy agent-workflows into a harness config dir.")
    parser.add_argument("--tool", choices=sorted(TOOLS), default="claude-code",
                        help="target harness (default: claude-code)")
    parser.add_argument("--profile", help="tier->model profile in profiles/<name>.toml "
                                          "(default: claude / openai / opencode per tool)")
    parser.add_argument("--target", type=Path,
                        help="destination dir (default: ~/.claude, ~/.codex or ~/.config/opencode)")
    parser.add_argument("--link", action="store_true", help="symlink copied dirs (live edits)")
    parser.add_argument("--dry-run", action="store_true", help="show actions without changing anything")
    parser.add_argument("--no-hook", action="store_true",
                        help="don't install the heavy-queue hook (claude-code) / plugin (opencode)"
                             " / sandbox writable root (codex)")
    args = parser.parse_args()

    tool = TOOLS[args.tool]
    profile = args.profile or tool.default_profile
    target = (args.target or tool.default_target).expanduser().resolve()
    if target == REPO_ROOT or REPO_ROOT in target.parents:
        print("Refusing to deploy into the repo itself.")
        return 1
    if not (PROFILES_DIR / f"{profile}.toml").is_file():
        print(f"Unknown profile '{profile}' (no profiles/{profile}.toml).")
        return 1

    Deployer(tool, target, profile=profile, link=args.link, dry_run=args.dry_run,
             hook=not args.no_hook, stamp=_stamp()).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
