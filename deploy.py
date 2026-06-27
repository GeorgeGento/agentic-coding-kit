#!/usr/bin/env python3
"""Deploy this Claude Code config repo into ~/.claude.

Copies (or symlinks) CLAUDE.md, README.md, guidelines/, and skills/ from
this repo into the user's Claude config directory. Anything it would overwrite
is backed up to a timestamped sibling first. Cross-platform: Windows, macOS, Linux.

Usage:
    python deploy.py                 # copy into ~/.claude (backs up overwrites)
    python deploy.py --dry-run       # show what would happen, change nothing
    python deploy.py --link          # symlink instead of copy (edits stay live)
    python deploy.py --target PATH   # deploy somewhere other than ~/.claude
"""
from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# Single files copied to <target>/<name>.
FILES = ("CLAUDE.md", "README.md")
# Directories the repo fully owns -> replaced wholesale at <target>/<name>.
OWNED_DIRS = ("guidelines",)
# Directories merged child-by-child so sibling content survives (e.g. other skills).
MERGE_DIRS = ("skills",)


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


class Deployer:
    def __init__(self, target: Path, *, link: bool, dry_run: bool, stamp: str) -> None:
        self.target = target
        self.link = link
        self.dry = dry_run
        self.stamp = stamp
        self.steps = 0

    def log(self, msg: str) -> None:
        print(("[dry-run] " if self.dry else "") + msg)
        self.steps += 1

    def _backup(self, dest: Path) -> None:
        """Move an existing dest out of the way before we write over it."""
        if dest.is_symlink() or dest.exists():
            bak = dest.with_name(f"{dest.name}.bak-{self.stamp}")
            self.log(f"backup  {dest}  ->  {bak.name}")
            if not self.dry:
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

    def deploy_item(self, name: str, *, merge: bool = False) -> None:
        src = REPO_ROOT / name
        if not src.exists():
            self.log(f"! skip {name} (not found in repo)")
            return
        if merge and src.is_dir():
            if not self.dry:
                (self.target / name).mkdir(parents=True, exist_ok=True)
            for child in sorted(src.iterdir()):
                dest = self.target / name / child.name
                self._backup(dest)
                self._place(child, dest)
        else:
            dest = self.target / name
            self._backup(dest)
            self._place(src, dest)

    def run(self) -> None:
        self.log(f"target: {self.target}")
        self.log(f"mode:   {'symlink' if self.link else 'copy'}")
        for name in FILES:
            self.deploy_item(name)
        for name in OWNED_DIRS:
            self.deploy_item(name)
        for name in MERGE_DIRS:
            self.deploy_item(name, merge=True)
        print()
        print(f"Done ({self.steps} step(s)).")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deploy this Claude Code config into ~/.claude.")
    parser.add_argument("--target", type=Path, default=Path.home() / ".claude",
                        help="destination dir (default: ~/.claude)")
    parser.add_argument("--link", action="store_true",
                        help="symlink instead of copy (live edits)")
    parser.add_argument("--dry-run", action="store_true",
                        help="show actions without changing anything")
    args = parser.parse_args()

    target = args.target.expanduser().resolve()
    if target == REPO_ROOT:
        print("Refusing to deploy into the repo itself.")
        return 1

    Deployer(target, link=args.link, dry_run=args.dry_run, stamp=_stamp()).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
