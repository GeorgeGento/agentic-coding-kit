#!/usr/bin/env python3
"""Install curated Claude Code skills.

Two install methods:
  - via="git" (default): shallow git sparse-checkout of `path` from `repo`,
    copied into <target>/<name>. Stays current on re-run.
  - via="pip": `pip install --upgrade <package>` then run its own installer
    (`python -m <module> <cli_args>`). The package manages its own skill
    location (e.g. graphify installs to ~/.claude/skills itself).

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

# Skill registry. See module docstring for the two `via` methods.
CATALOG: dict[str, dict] = {
    "angular-developer": dict(repo="https://github.com/angular/skills",
        path="angular-developer", trust="official - Angular team", group="Angular", default=True),
    "angular-new-app": dict(repo="https://github.com/angular/skills",
        path="angular-new-app", trust="official - Angular team", group="Angular", default=False),
    "frontend-design": dict(repo="https://github.com/anthropics/skills",
        path="skills/frontend-design", trust="official - Anthropic", group="UI/UX", default=True),
    "webapp-testing": dict(repo="https://github.com/anthropics/skills",
        path="skills/webapp-testing", trust="official - Anthropic", group="UI/UX", default=True),
    "theme-factory": dict(repo="https://github.com/anthropics/skills",
        path="skills/theme-factory", trust="official - Anthropic", group="UI/UX", default=False),
    "typescript-pro": dict(repo="https://github.com/Jeffallan/claude-skills",
        path="skills/typescript-pro", trust="community - review first", group="TypeScript", default=True),
    "nestjs-expert": dict(repo="https://github.com/Jeffallan/claude-skills",
        path="skills/nestjs-expert", trust="community - review first", group="Node/NestJS", default=True),
    "code-reviewer": dict(repo="https://github.com/Jeffallan/claude-skills",
        path="skills/code-reviewer", trust="community - review first", group="Quality", default=False),
    "secure-code-guardian": dict(repo="https://github.com/Jeffallan/claude-skills",
        path="skills/secure-code-guardian", trust="community - review first", group="Quality", default=False),
    "graphify": dict(via="pip", package="graphifyy", module="graphify", cli_args=["install"],
        trust="MIT - safishamsi (self-updating)", group="Knowledge graph", default=True),
}
LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt")


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _run(cmd: list[str], cwd: str | None = None, quiet: bool = True) -> None:
    subprocess.run(cmd, cwd=cwd, check=True,
                   stdout=subprocess.DEVNULL if quiet else None,
                   stderr=subprocess.PIPE if quiet else None, text=True)


def _git(args: list[str], cwd: str | None = None) -> None:
    _run(["git", *args], cwd=cwd)


def _source(meta: dict) -> str:
    if meta.get("via") == "pip":
        return f"pip:{meta['package']}"
    return meta["repo"].replace("https://github.com/", "")


def print_catalog() -> None:
    print("Curated skill catalog (* = installed by default):\n")
    for group in dict.fromkeys(m["group"] for m in CATALOG.values()):
        print(f"  {group}")
        for name, meta in CATALOG.items():
            if meta["group"] == group:
                mark = "*" if meta["default"] else " "
                print(f"    {mark} {name:22} {_source(meta):26} {meta['trust']}")
        print()


def install_git_skill(name: str, meta: dict, target_dir: Path, dry: bool) -> bool:
    repo, sub = meta["repo"], meta["path"]
    print(f"  {name:22} <- {repo} :{sub}  [{meta['trust']}]")
    if dry:
        return True
    tmp = Path(tempfile.mkdtemp(prefix=f"skill-{name}-"))
    try:
        _git(["clone", "--depth", "1", "--filter=blob:none", "--sparse", repo, str(tmp)])
        _git(["-C", str(tmp), "sparse-checkout", "set", sub])
        src = tmp / sub
        if not src.is_dir():
            print(f"    ! source path not found in repo: {sub}")
            return False

        dest = target_dir / name
        if dest.exists() or dest.is_symlink():
            bak = dest.with_name(f"{dest.name}.bak-{_stamp()}")
            shutil.move(os.fspath(dest), os.fspath(bak))
            print(f"    backed up existing -> {bak.name}")
        shutil.copytree(src, dest)

        # Preserve upstream license/attribution if present at the repo root.
        for lic in LICENSE_NAMES:
            lp = tmp / lic
            if lp.exists():
                shutil.copy2(lp, dest / f"UPSTREAM-{lic}")
                break
        return True
    except subprocess.CalledProcessError as exc:
        msg = (exc.stderr or "").strip() or str(exc)
        print(f"    ! git failed: {msg}")
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def install_pip_skill(name: str, meta: dict, dry: bool) -> bool:
    pkg = meta["package"]
    print(f"  {name:22} <- pip:{pkg}  [{meta['trust']}]  (installs to its own location)")
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


def install_skill(name: str, meta: dict, target_dir: Path, dry: bool) -> bool:
    if meta.get("via") == "pip":
        return install_pip_skill(name, meta, dry)
    return install_git_skill(name, meta, target_dir, dry)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install curated Claude Code skills.")
    parser.add_argument("--list", action="store_true", help="show catalog, install nothing")
    parser.add_argument("--all", action="store_true", help="install every skill")
    parser.add_argument("--only", default="", help="comma-separated skill names")
    parser.add_argument("--dry-run", action="store_true", help="show actions only")
    parser.add_argument("--target", type=Path, default=Path.home() / ".claude" / "skills",
                        help="destination dir for git skills (default: ~/.claude/skills)")
    args = parser.parse_args()

    if args.list:
        print_catalog()
        return 0

    if args.only:
        names = [n.strip() for n in args.only.split(",") if n.strip()]
        unknown = [n for n in names if n not in CATALOG]
        if unknown:
            print(f"Unknown skill(s): {', '.join(unknown)}. Use --list to see options.")
            return 1
    elif args.all:
        names = list(CATALOG)
    else:
        names = [n for n, m in CATALOG.items() if m["default"]]

    needs_git = any(CATALOG[n].get("via", "git") == "git" for n in names)
    if needs_git and shutil.which("git") is None:
        print("git is required for some selected skills but was not found on PATH.")
        return 1

    target = args.target.expanduser().resolve()
    if not args.dry_run and needs_git:
        target.mkdir(parents=True, exist_ok=True)

    suffix = " (dry-run)" if args.dry_run else ""
    print(f"Installing {len(names)} skill(s){suffix}:")
    installed = sum(install_skill(n, CATALOG[n], target, args.dry_run) for n in names)

    print(f"\nDone: {installed}/{len(names)} skill(s).")
    if any("community" in CATALOG[n]["trust"] for n in names):
        print("Note: community skills are third-party code - review before relying on them.")
    return 0 if installed == len(names) else 1


if __name__ == "__main__":
    raise SystemExit(main())
