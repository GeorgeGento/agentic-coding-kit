#!/usr/bin/env python3
"""Install curated Claude Code skills and subagents.

Three install methods (`via` in the catalog):
  - "git" (default): shallow git sparse-checkout of `path` from `repo`,
    copied into <target>/<name>. Stays current on re-run.
  - "pip": `pip install --upgrade <package>` then run the package's own
    installer (`python -m <module> <cli_args>`). The package manages its own
    skill location (e.g. graphify).
  - "git" + kind="agent": fetches a single subagent .md file from `repo` and
    places it in ~/.claude/agents/<name>.md (Claude Code subagent, not a skill).

Backups of anything overwritten go to ~/.claude/.skill-backups/ — never next
to the skill itself (a sibling `<name>.bak-*` inside skills/ shows up as a
phantom skill in Claude Code).

Cross-platform: Windows, macOS, Linux. Driven by the /setup skill.

Usage:
    python install_skills.py                 # install the default set
    python install_skills.py --list          # show catalog, install nothing
    python install_skills.py --only a,b      # install only these
    python install_skills.py --all           # install everything
    python install_skills.py --dry-run
    python install_skills.py --target PATH   # default: ~/.claude/skills (git skills only)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Don't crash on legacy Windows consoles (cp1252). Output is ASCII anyway.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

JEFFALLAN = "https://github.com/Jeffallan/claude-skills"
VOLTAGENT = "https://github.com/VoltAgent/awesome-claude-code-subagents"

# Skill/agent registry. See module docstring for the `via` methods.
# default=True entries form the lean default set; everything else is opt-in
# (--only / --all) so public users pick what matches their stack.
CATALOG: dict[str, dict] = {
    # --- Angular ---
    "angular-developer": dict(repo="https://github.com/angular/skills",
        path="angular-developer", trust="official - Angular team", group="Angular", default=True),
    "angular-new-app": dict(repo="https://github.com/angular/skills",
        path="angular-new-app", trust="official - Angular team", group="Angular", default=False),
    # --- UI/UX ---
    "frontend-design": dict(repo="https://github.com/anthropics/skills",
        path="skills/frontend-design", trust="official - Anthropic", group="UI/UX", default=True),
    "webapp-testing": dict(repo="https://github.com/anthropics/skills",
        path="skills/webapp-testing", trust="official - Anthropic", group="UI/UX", default=True),
    "theme-factory": dict(repo="https://github.com/anthropics/skills",
        path="skills/theme-factory", trust="official - Anthropic", group="UI/UX", default=False),
    # --- TypeScript / JavaScript ---
    "typescript-pro": dict(repo=JEFFALLAN,
        path="skills/typescript-pro", trust="community - review first", group="TypeScript/JS", default=True),
    "javascript-pro": dict(repo=JEFFALLAN,
        path="skills/javascript-pro", trust="community - review first", group="TypeScript/JS", default=False),
    # --- Node / NestJS ---
    "nestjs-expert": dict(repo=JEFFALLAN,
        path="skills/nestjs-expert", trust="community - review first", group="Node/NestJS", default=True),
    # --- React ecosystem ---
    "react-expert": dict(repo=JEFFALLAN,
        path="skills/react-expert", trust="community - review first", group="React", default=False),
    "nextjs-developer": dict(repo=JEFFALLAN,
        path="skills/nextjs-developer", trust="community - review first", group="React", default=False),
    "react-native-expert": dict(repo=JEFFALLAN,
        path="skills/react-native-expert", trust="community - review first", group="React", default=False),
    # --- Vue ---
    "vue-expert": dict(repo=JEFFALLAN,
        path="skills/vue-expert", trust="community - review first", group="Vue", default=False),
    # --- Desktop / Mobile ---
    "electron-pro": dict(repo=VOLTAGENT, kind="agent",
        path="categories/01-core-development/electron-pro.md",
        trust="community - VoltAgent (subagent)", group="Desktop/Mobile", default=False),
    "flutter-expert": dict(repo=JEFFALLAN,
        path="skills/flutter-expert", trust="community - review first", group="Desktop/Mobile", default=False),
    # ionic-capacitor is bundled in this repo's skills/ (vendored, MIT) — not in the catalog.
    # --- Quality / review ---
    "code-reviewer": dict(repo=JEFFALLAN,
        path="skills/code-reviewer", trust="community - review first", group="Quality", default=False),
    "secure-code-guardian": dict(repo=JEFFALLAN,
        path="skills/secure-code-guardian", trust="community - review first", group="Quality", default=False),
    "playwright-expert": dict(repo=JEFFALLAN,
        path="skills/playwright-expert", trust="community - review first", group="Quality", default=False),
    "code-reviewer-agent": dict(repo=VOLTAGENT, kind="agent",
        path="categories/04-quality-security/code-reviewer.md",
        trust="community - VoltAgent (subagent)", group="Quality", default=False),
    "security-auditor-agent": dict(repo=VOLTAGENT, kind="agent",
        path="categories/04-quality-security/security-auditor.md",
        trust="community - VoltAgent (subagent)", group="Quality", default=False),
    # --- Tone ---
    "caveman": dict(repo="https://github.com/JuliusBrussee/caveman",
        path="skills/caveman", trust="community - JuliusBrussee (MIT)", group="Tone", default=True),
    # --- Knowledge graph ---
    "graphify": dict(via="pip", package="graphifyy", module="graphify", cli_args=["install"],
        trust="MIT - safishamsi (self-updating)", group="Knowledge graph", default=True),
}
LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt")
BACKUP_DIR = Path.home() / ".claude" / ".skill-backups"
AGENTS_DIR = Path.home() / ".claude" / "agents"


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _run(cmd: list[str], cwd: str | None = None, quiet: bool = True) -> None:
    subprocess.run(cmd, cwd=cwd, check=True,
                   stdout=subprocess.DEVNULL if quiet else None,
                   stderr=subprocess.PIPE if quiet else None, text=True)


def _git(args: list[str], cwd: str | None = None) -> None:
    _run(["git", *args], cwd=cwd)


def _backup(dest: Path) -> None:
    if dest.exists() or dest.is_symlink():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        bak = BACKUP_DIR / f"{dest.name}.bak-{_stamp()}"
        shutil.move(os.fspath(dest), os.fspath(bak))
        print(f"    backed up existing -> .skill-backups/{bak.name}")


def _source(meta: dict) -> str:
    if meta.get("via") == "pip":
        return f"pip:{meta['package']}"
    return meta["repo"].replace("https://github.com/", "")


def print_catalog() -> None:
    print("Curated catalog (* = installed by default; 'agent' = subagent, not skill):\n")
    for group in dict.fromkeys(m["group"] for m in CATALOG.values()):
        print(f"  {group}")
        for name, meta in CATALOG.items():
            if meta["group"] == group:
                mark = "*" if meta["default"] else " "
                kind = "agent" if meta.get("kind") == "agent" else ("pip" if meta.get("via") == "pip" else "skill")
                print(f"    {mark} {name:24} {kind:5}  {_source(meta):36} {meta['trust']}")
        print()
    print("Bundled in the config repo (installed by deploy.py, not listed above):")
    print("      setup, ionic-capacitor, and the senior/mid/junior tier agents")


def install_git_item(name: str, meta: dict, target_dir: Path, dry: bool) -> bool:
    repo, sub = meta["repo"], meta["path"]
    is_agent = meta.get("kind") == "agent"
    dest_root = AGENTS_DIR if is_agent else target_dir
    label = "agent" if is_agent else "skill"
    print(f"  {name:24} <- {repo} :{sub}  [{meta['trust']}] ({label})")
    if dry:
        return True
    tmp = Path(tempfile.mkdtemp(prefix=f"skill-{name}-"))
    try:
        _git(["clone", "--depth", "1", "--filter=blob:none", "--sparse", repo, str(tmp)])
        # Sparse-checkout the parent dir when the target is a single file.
        sparse = str(Path(sub).parent) if is_agent else sub
        _git(["-C", str(tmp), "sparse-checkout", "set", sparse])
        src = tmp / sub
        if not src.exists():
            print(f"    ! source path not found in repo: {sub}")
            return False

        dest_root.mkdir(parents=True, exist_ok=True)
        dest = dest_root / (f"{name}.md" if is_agent else name)
        _backup(dest)
        if src.is_dir():
            shutil.copytree(src, dest)
            # Preserve upstream license/attribution if present at the repo root.
            for lic in LICENSE_NAMES:
                lp = tmp / lic
                if lp.exists():
                    shutil.copy2(lp, dest / f"UPSTREAM-{lic}")
                    break
        else:
            shutil.copy2(src, dest)
        return True
    except subprocess.CalledProcessError as exc:
        msg = (exc.stderr or "").strip() or str(exc)
        print(f"    ! git failed: {msg}")
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def install_pip_item(name: str, meta: dict, dry: bool) -> bool:
    pkg = meta["package"]
    print(f"  {name:24} <- pip:{pkg}  [{meta['trust']}]  (installs to its own location)")
    if dry:
        return True
    try:
        _run([sys.executable, "-m", "pip", "install", "--upgrade", pkg], quiet=False)
        if meta.get("module"):
            _run([sys.executable, "-m", meta["module"], *meta.get("cli_args", [])], quiet=False)
        return True
    except subprocess.CalledProcessError as exc:
        msg = (getattr(exc, "stderr", None) or "").strip() or str(exc)
        print(f"    ! install failed: {msg}")
        return False


def install_item(name: str, meta: dict, target_dir: Path, dry: bool) -> bool:
    if meta.get("via") == "pip":
        return install_pip_item(name, meta, dry)
    return install_git_item(name, meta, target_dir, dry)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install curated Claude Code skills and subagents.")
    parser.add_argument("--list", action="store_true", help="show catalog, install nothing")
    parser.add_argument("--all", action="store_true", help="install every catalog entry")
    parser.add_argument("--only", default="", help="comma-separated names")
    parser.add_argument("--dry-run", action="store_true", help="show actions only")
    parser.add_argument("--target", type=Path, default=Path.home() / ".claude" / "skills",
                        help="destination dir for git skills (default: ~/.claude/skills); "
                             "agents always go to ~/.claude/agents")
    args = parser.parse_args()

    if args.list:
        print_catalog()
        return 0

    if args.only:
        names = [n.strip() for n in args.only.split(",") if n.strip()]
        unknown = [n for n in names if n not in CATALOG]
        if unknown:
            print(f"Unknown name(s): {', '.join(unknown)}. Use --list to see options.")
            return 1
    elif args.all:
        names = list(CATALOG)
    else:
        names = [n for n, m in CATALOG.items() if m["default"]]

    needs_git = any(CATALOG[n].get("via", "git") == "git" for n in names)
    if needs_git and shutil.which("git") is None:
        print("git is required for some selected entries but was not found on PATH.")
        return 1

    target = args.target.expanduser().resolve()
    if not args.dry_run and needs_git:
        target.mkdir(parents=True, exist_ok=True)

    suffix = " (dry-run)" if args.dry_run else ""
    print(f"Installing {len(names)} item(s){suffix}:")
    installed = sum(install_item(n, CATALOG[n], target, args.dry_run) for n in names)

    print(f"\nDone: {installed}/{len(names)} item(s).")
    if any("community" in CATALOG[n]["trust"] for n in names):
        print("Note: community skills/agents are third-party code - review before relying on them.")
    return 0 if installed == len(names) else 1


if __name__ == "__main__":
    raise SystemExit(main())
