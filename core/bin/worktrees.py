#!/usr/bin/env python3
"""List and clean up agent worktrees (`agent/*` branches) so none pile up on disk.

Run from anywhere inside a git repo. Python stdlib only.

Usage:
    python worktrees.py list [--quiet]     # agent worktrees: size, age, dirty, applied
    python worktrees.py apply <path>       # its changes -> main checkout, uncommitted
    python worktrees.py clean              # remove applied ones + their branches
    python worktrees.py discard <path>     # remove one, applied or not (user-approved)
    python worktrees.py check-disk [path]  # exit 1 if free disk < min_free_disk_gb

"Applied" means the worktree's changes (commits since it branched plus uncommitted
and untracked files) are already present in the main checkout, checked with a
reverse `git apply --check`. Only applied worktrees are removed by `clean`, so no
work is lost; anything else is listed for the Lead to ask the user about.

`list --quiet` is the Claude Code SessionStart hook: silent when there's nothing
to report, one line otherwise. It never computes sizes, so session start stays fast.

Environment:
    AW_SETTINGS   settings file (default ~/.agent-memory/settings.toml)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path

AGENT_BRANCH_PREFIX = "refs/heads/agent/"
ENV_SETTINGS = "AW_SETTINGS"
DEFAULT_SETTINGS = Path.home() / ".agent-memory" / "settings.toml"
DEFAULT_MIN_FREE_DISK_GB = 10
GIT_TIMEOUT_SECONDS = 60
BYTES_PER_GB = 1024 ** 3
SECONDS_PER_DAY = 86_400
EXIT_USAGE = 2
EXIT_LOW_DISK = 1


@dataclass(frozen=True)
class Worktree:
    path: Path
    branch: str  # e.g. "agent/login-form"


def _git(cwd: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, input=stdin, capture_output=True,
                          text=True, encoding="utf-8", timeout=GIT_TIMEOUT_SECONDS)


def main_checkout(cwd: Path) -> Path | None:
    """The repo's main worktree (first `git worktree list` entry), or None outside git."""
    result = _git(cwd, "worktree", "list", "--porcelain")
    if result.returncode != 0:
        return None
    first = result.stdout.splitlines()[0]
    return Path(first.removeprefix("worktree "))


def parse_worktrees(porcelain: str) -> list[Worktree]:
    """Agent worktrees from `git worktree list --porcelain` output.

    Example:
        parse_worktrees("worktree /r\\nbranch refs/heads/main\\n\\n"
                        "worktree /r-a\\nbranch refs/heads/agent/x\\n")
        # -> [Worktree(path=Path('/r-a'), branch='agent/x')]
    """
    found = []
    for block in porcelain.strip().split("\n\n"):
        fields = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        branch = fields.get("branch", "")
        if branch.startswith(AGENT_BRANCH_PREFIX):
            found.append(Worktree(Path(fields["worktree"]), branch.removeprefix("refs/heads/")))
    return found


def agent_worktrees(main: Path) -> list[Worktree]:
    _git(main, "worktree", "prune")  # drop entries whose folder is already gone
    return parse_worktrees(_git(main, "worktree", "list", "--porcelain").stdout)


def is_dirty(wt: Worktree) -> bool:
    return bool(_git(wt.path, "status", "--porcelain").stdout.strip())


def worktree_patch(main: Path, wt: Worktree) -> str:
    """Everything the worktree changed since it branched off the main checkout's HEAD."""
    base = _git(main, "merge-base", "HEAD", wt.branch).stdout.strip()
    # Intent-to-add makes untracked files show up in the diff; it only touches the
    # agent worktree's own index.
    _git(wt.path, "add", "--intent-to-add", "--all")
    return _git(wt.path, "diff", "--binary", base).stdout


def is_applied(main: Path, wt: Worktree) -> bool:
    """True if the worktree's changes are already in the main checkout (or there are none)."""
    patch = worktree_patch(main, wt)
    if not patch.strip():
        return True
    return _git(main, "apply", "--reverse", "--check", "-", stdin=patch).returncode == 0


def dir_size(path: Path) -> int:
    """Bytes on disk under path, not following symlinks."""
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.lstat(os.path.join(root, name)).st_size
            except OSError:
                pass
    return total


def format_size(size: int) -> str:
    return f"{size / BYTES_PER_GB:.1f} GB" if size >= BYTES_PER_GB / 10 else f"{size // 1024 ** 2} MB"


def remove(main: Path, wt: Worktree) -> bool:
    # --force is needed because agent work is uncommitted; callers only get here
    # once the changes are verified applied, or the user approved the discard.
    removed = _git(main, "worktree", "remove", "--force", str(wt.path)).returncode == 0
    if removed:
        _git(main, "branch", "-D", wt.branch)
    return removed


def load_settings() -> dict:
    path = Path(os.environ.get(ENV_SETTINGS, DEFAULT_SETTINGS))
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


# --- commands -----------------------------------------------------------------
def cmd_list(main: Path, quiet: bool) -> int:
    trees = agent_worktrees(main)
    if quiet:
        if trees:
            names = ", ".join(wt.branch for wt in trees)
            print(f"[worktrees] {len(trees)} leftover agent worktree(s) in {main}: {names}. "
                  "Run `worktrees.py list`, then apply, `clean`, or ask the user to discard.")
        return 0
    if not trees:
        print("No agent worktrees.")
        return 0
    total = 0
    for wt in trees:
        size = dir_size(wt.path)
        total += size
        age_days = (time.time() - wt.path.stat().st_mtime) / SECONDS_PER_DAY
        state = "dirty" if is_dirty(wt) else "clean"
        applied = "applied" if is_applied(main, wt) else "NOT applied"
        print(f"{wt.branch}  {wt.path}  {format_size(size)}  {age_days:.1f}d  {state}  {applied}")
    print(f"{len(trees)} agent worktree(s), {format_size(total)} total.")
    return 0


def cmd_apply(main: Path, target: Path) -> int:
    """Apply one worktree's changes to the main checkout as uncommitted changes."""
    wt = _find(main, target)
    if wt is None:
        return 1
    if is_applied(main, wt):
        print(f"already applied  {wt.branch}")
        return 0
    result = _git(main, "apply", "--binary", "-", stdin=worktree_patch(main, wt))
    if result.returncode != 0:
        print(f"apply failed for {wt.branch} (main checkout changed under it?):\n"
              f"{result.stderr.strip()}", file=sys.stderr)
        return 1
    print(f"applied  {wt.branch}  ->  {main} (uncommitted)")
    return 0


def _find(main: Path, target: Path) -> Worktree | None:
    for wt in agent_worktrees(main):
        if wt.path.resolve() == target.resolve():
            return wt
    print(f"{target} is not an agent worktree of this repo.", file=sys.stderr)
    return None


def cmd_clean(main: Path) -> int:
    kept = 0
    for wt in agent_worktrees(main):
        if is_applied(main, wt) and remove(main, wt):
            print(f"removed  {wt.branch}  {wt.path}")
        else:
            kept += 1
            print(f"kept     {wt.branch}  {wt.path}  (not applied: ask the user to apply or discard)")
    if kept == 0:
        print("No agent worktrees left.")
    return 0


def cmd_discard(main: Path, target: Path) -> int:
    wt = _find(main, target)
    if wt is None:
        return 1
    if remove(main, wt):
        print(f"discarded  {wt.branch}  {wt.path}")
        return 0
    print(f"could not remove {wt.path}", file=sys.stderr)
    return 1


def cmd_check_disk(path: Path) -> int:
    minimum = float(load_settings().get("min_free_disk_gb", DEFAULT_MIN_FREE_DISK_GB))
    free = shutil.disk_usage(path).free / BYTES_PER_GB
    if free < minimum:
        print(f"Low disk: {free:.1f} GB free < {minimum:g} GB. "
              "Run in the main checkout instead, or ask the user.")
        return EXIT_LOW_DISK
    print(f"OK: {free:.1f} GB free (minimum {minimum:g} GB).")
    return 0


# --- CLI ----------------------------------------------------------------------
def main(argv: list[str]) -> int:
    """CLI entry point; see module docstring."""
    usage = ("usage: worktrees.py list [--quiet] | apply <path> | clean | discard <path>"
             " | check-disk [path]")
    if not argv:
        print(usage, file=sys.stderr)
        return EXIT_USAGE
    action, rest = argv[0], argv[1:]
    cwd = Path.cwd()
    if action == "check-disk" and len(rest) <= 1:
        return cmd_check_disk(Path(rest[0]) if rest else cwd)
    quiet = rest == ["--quiet"]
    main_path = main_checkout(cwd)
    if main_path is None:
        if quiet:
            return 0  # hook outside a repo: nothing to say
        print("Not inside a git repository.", file=sys.stderr)
        return 1
    if action == "list" and rest in ([], ["--quiet"]):
        return cmd_list(main_path, quiet)
    if action == "clean" and not rest:
        return cmd_clean(main_path)
    if action == "apply" and len(rest) == 1:
        return cmd_apply(main_path, Path(rest[0]))
    if action == "discard" and len(rest) == 1:
        return cmd_discard(main_path, Path(rest[0]))
    print(usage, file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, subprocess.SubprocessError) as exc:
        quiet_hook = sys.argv[1:] == ["list", "--quiet"]
        if not quiet_hook:  # a hook must never break session start
            print(f"[worktrees] {exc}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
