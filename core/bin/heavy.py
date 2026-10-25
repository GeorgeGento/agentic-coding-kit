#!/usr/bin/env python3
"""Machine-wide queue for heavy commands (test runners, builds, type-checks).

Limits how many heavy commands run at once across all AI-agent sessions so the
PC does not freeze. Cheap commands are never queued. Python stdlib only.

Usage:
    python heavy.py run --shell bash|powershell|sh -- "<command string>"
    python heavy.py run --raw --shell bash -- "<command>"   # raw output, no summary
    python heavy.py run --shell powershell --from-env   # command in $env:AW_HEAVY_CMD
    python heavy.py status
    python heavy.py hook            # Claude Code PreToolUse hook (JSON on stdin)
    python heavy.py wrap bash|powershell   # command on stdin -> wrapped (or nothing)

Environment:
    AW_HEAVY_SLOTS     concurrent heavy commands (default 2)
    AW_HEAVY_MAX_WAIT  seconds to wait for a slot before exit 75 (default 480,
                       must stay under the Claude Code 10-minute tool timeout)
    AW_HEAVY_DIR       lock directory (default ~/.agent-workflows/heavy)
    AW_HEAVY_HELD      set to 1 in the child; nested `run` skips the queue
    AW_HEAVY_CMD       command for `--from-env` (avoids PowerShell 5.1 mangling
                       embedded double quotes when passing args to native exes)
    HEAVY_RAW          set to 1 to print raw output instead of a summary
    AW_HEAVY_LOG_DIR   full-output logs (default ~/.agent-workflows/logs/<project>/)
    AW_SETTINGS        user settings (default ~/.agent-memory/settings.toml);
                       `heavy_log_keep` = logs kept per project (default 20)

Output: the command's full output goes to a log file and a structured summary
(heavy_parsers.py) is printed instead: one line on success, the failures with
file:line otherwise. The exit code is always the command's own. Nested calls
(AW_HEAVY_HELD=1) stay raw so the outer call summarizes once.

A slot is `<dir>/slot-<i>.lock`. On POSIX it is held by a workload supervisor:
if the calling wrapper is killed, the supervisor stops its descendants before
freeing the slot. The supervisor is POSIX-only; on Windows the wrapper holds the
slot itself and the OS file lock frees it when the wrapper exits.
"""

from __future__ import annotations

import base64
import ctypes
import json
import os
import random
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import threading
import hashlib
import tomllib
from pathlib import Path
from typing import BinaryIO

IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    import msvcrt
else:
    import fcntl

# --- configuration -----------------------------------------------------------
ENV_SLOTS = "AW_HEAVY_SLOTS"
ENV_MAX_WAIT = "AW_HEAVY_MAX_WAIT"
ENV_DIR = "AW_HEAVY_DIR"
ENV_HELD = "AW_HEAVY_HELD"
ENV_CMD = "AW_HEAVY_CMD"
ENV_RAW = "HEAVY_RAW"
ENV_LOG_DIR = "AW_HEAVY_LOG_DIR"
ENV_SETTINGS = "AW_SETTINGS"
DEFAULT_SLOTS = 2
DEFAULT_MAX_WAIT_SECONDS = 480
DEFAULT_DIR = Path.home() / ".agent-workflows" / "heavy"
DEFAULT_LOG_DIR = Path.home() / ".agent-workflows" / "logs"
DEFAULT_SETTINGS = Path.home() / ".agent-memory" / "settings.toml"
DEFAULT_LOG_KEEP = 20
LOG_SLUG_CHARS = 40
PROJECT_HASH_CHARS = 8
POLL_INTERVAL_SECONDS = 1.0
POLL_JITTER_SECONDS = 0.25
NICE_INCREMENT = 10
CHILD_POLL_SECONDS = 0.05
TERMINATE_GRACE_SECONDS = 1.0
EXIT_CANCELLED = 130
PR_SET_CHILD_SUBREAPER = 36
EXIT_QUEUE_BUSY = 75
EXIT_USAGE = 2
EXIT_SHELL_MISSING = 127
HOOK_TIMEOUT_MS = 600_000
WRAPPER_MARKER = "heavy.py"
# Exit codes produced by the queue itself: its own messages are shown raw.
QUEUE_EXIT_CODES = (EXIT_QUEUE_BUSY, EXIT_SHELL_MISSING, EXIT_CANCELLED)
HOOK_TOOLS = ("Bash", "PowerShell")

# --- heavy command classification --------------------------------------------
PACKAGE_MANAGERS = frozenset({"npm", "pnpm", "yarn", "bun"})
HEAVY_SCRIPTS = ("test", "t", "build", "lint", "e2e", "typecheck", "check")
DEV_SCRIPTS = ("dev", "start", "serve", "storybook", "watch")
HEAVY_TOOLS = frozenset(
    {"jest", "vitest", "tsc", "eslint", "pytest", "mvn", "gradle", "gradlew", "make"}
)
HEAVY_SUBCOMMANDS = {
    "ng": frozenset({"build", "test", "e2e", "lint"}),
    "nx": frozenset({"build", "test", "lint", "run-many", "affected"}),
    "playwright": frozenset({"test"}),
    "maestro": frozenset({"test"}),
    "docker": frozenset({"build"}),  # `docker compose build` handled in _is_heavy_tokens
    "cargo": frozenset({"build", "test", "clippy"}),
    "go": frozenset({"build", "test"}),
    "dotnet": frozenset({"build", "test"}),
}
DEV_SERVER_COMMANDS = {
    "ng": frozenset({"serve"}),
    "next": frozenset({"dev"}),
    "nodemon": None,  # any use
    "vite": frozenset({"dev"}),
}
PYTHON_NAMES = frozenset({"python", "python3", "py"})
WATCH_FLAGS = frozenset({"--watch", "-w", "--watchAll"})
EXEC_PREFIXES = frozenset({"npx", "bunx"})
EXEC_SUBCOMMAND_PREFIXES = {"pnpm": ("exec", "dlx"), "yarn": ("exec", "dlx")}
SEGMENT_SEPARATORS = ("&&", "||", ";", "|", "\n")
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
EXECUTABLE_SUFFIXES = (".exe", ".cmd", ".bat", ".ps1")


def _split_segments(command: str) -> list[str]:
    """Split on &&, ||, ;, | and newlines, ignoring separators inside quotes."""
    segments: list[str] = []
    current: list[str] = []
    quote = ""
    i = 0
    while i < len(command):
        char = command[i]
        if quote:
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        else:
            sep = next((s for s in SEGMENT_SEPARATORS if command.startswith(s, i)), None)
            if sep:
                segments.append("".join(current))
                current = []
                i += len(sep)
                continue
        current.append(char)
        i += 1
    segments.append("".join(current))
    return [s.strip() for s in segments if s.strip()]


def _tokenize(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:  # unbalanced quote: best effort
        return segment.split()


def _command_name(token: str) -> str:
    name = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    for suffix in EXECUTABLE_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _strip_prefixes(tokens: list[str]) -> list[str]:
    """Drop leading env assignments and npx/pnpm exec style launchers."""
    while tokens and ENV_ASSIGNMENT.match(tokens[0]):
        tokens = tokens[1:]
    if not tokens:
        return tokens
    name = _command_name(tokens[0])
    if name in EXEC_PREFIXES:
        tokens = tokens[1:]
        while tokens and tokens[0].startswith("-"):
            tokens = tokens[1:]
    elif len(tokens) > 1 and tokens[1] in EXEC_SUBCOMMAND_PREFIXES.get(name, ()):
        tokens = tokens[2:]
    return tokens


def _script_matches(script: str, names: tuple[str, ...]) -> bool:
    return any(script == n or script.startswith(n + ":") for n in names)


def _is_dev_server(name: str, args: list[str]) -> bool:
    if name in PACKAGE_MANAGERS:
        rest = args[1:] if args[:1] == ["run"] else args
        return bool(rest) and _script_matches(rest[0], DEV_SCRIPTS)
    if name == "docker":
        return args[:2] == ["compose", "up"]
    if name == "vite":
        return not args or args[0] == "dev"
    if name in DEV_SERVER_COMMANDS:
        subs = DEV_SERVER_COMMANDS[name]
        return subs is None or args[:1] != [] and args[0] in subs
    return False


def _is_heavy_tokens(tokens: list[str]) -> bool:
    if not tokens:
        return False
    name, args = _command_name(tokens[0]), tokens[1:]
    if any(a in WATCH_FLAGS for a in args) or _is_dev_server(name, args):
        return False
    if name in PACKAGE_MANAGERS:
        rest = args[1:] if args[:1] == ["run"] else args
        return bool(rest) and _script_matches(rest[0], HEAVY_SCRIPTS)
    if name in HEAVY_TOOLS:
        return True
    if name in PYTHON_NAMES:
        return args[:2] == ["-m", "pytest"]
    if name == "docker" and args[:1] == ["compose"]:
        args = args[1:]
    if name in HEAVY_SUBCOMMANDS:
        return bool(args) and args[0] in HEAVY_SUBCOMMANDS[name]
    return False


def is_heavy(command: str) -> bool:
    """Return True if any segment of `command` starts a heavy process.

    Matches only on command position, so `git commit -m "npm test"` is cheap.
    Watch-mode flags and dev servers are never heavy (they never finish).

    Example:
        >>> is_heavy("cd app && npm run lint")
        True
        >>> is_heavy("grep -r jest src")
        False
    """
    for segment in _split_segments(command):
        tokens = _strip_prefixes(_tokenize(segment))
        if _is_heavy_tokens(tokens):
            return True
        # `yarn jest` style: bare yarn forwards to a local binary
        if tokens and _command_name(tokens[0]) == "yarn" and _is_heavy_tokens(tokens[1:]):
            return True
    return False


# --- slots --------------------------------------------------------------------
def _slot_count() -> int:
    return max(1, int(os.environ.get(ENV_SLOTS, DEFAULT_SLOTS)))


def _heavy_dir() -> Path:
    path = Path(os.environ.get(ENV_DIR) or DEFAULT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _try_lock(handle: BinaryIO) -> bool:
    """Take an exclusive non-blocking OS lock on the file's first byte."""
    try:
        if IS_WINDOWS:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _unlock(handle: BinaryIO) -> None:
    if IS_WINDOWS:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _try_acquire(directory: Path, index: int) -> BinaryIO | None:
    handle = open(directory / f"slot-{index}.lock", "a+b")
    if _try_lock(handle):
        return handle
    handle.close()
    return None


def acquire_slot(directory: Path, slots: int, max_wait: float,
                 cancelled: threading.Event | None = None) -> tuple[BinaryIO, int] | None:
    """Poll for a free slot; return (lock handle, slot index) or None on timeout."""
    deadline = time.monotonic() + max_wait
    announced = False
    while True:
        if cancelled is not None and cancelled.is_set():
            return None
        for index in range(slots):
            handle = _try_acquire(directory, index)
            if handle:
                return handle, index
        if time.monotonic() >= deadline:
            return None
        if not announced:
            print(f"[heavy] waiting for a slot (all {slots} busy)...", file=sys.stderr, flush=True)
            announced = True
        delay = POLL_INTERVAL_SECONDS + random.uniform(0, POLL_JITTER_SECONDS)
        if cancelled is None:
            time.sleep(delay)
        else:
            cancelled.wait(delay)


# --- run ----------------------------------------------------------------------
def _windows_bash() -> str:
    """Prefer Git Bash: a bare `bash` on Windows is often WSL's System32 launcher."""
    found = shutil.which("bash")
    if found and "system32" not in found.lower():
        return found
    git_bash = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
    return str(git_bash) if git_bash.exists() else found or "bash"


def _shell_argv(shell: str, command: str) -> list[str]:
    if shell == "bash" and IS_WINDOWS:
        return [_windows_bash(), "-c", command]
    if shell == "powershell":
        exe = shutil.which("powershell") or shutil.which("pwsh") or "powershell"
        # -EncodedCommand sidesteps Windows command-line quoting entirely.
        encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
        return [exe, "-NoProfile", "-EncodedCommand", encoded]
    return [shell, "-c", command]


def _spawn_controlled(action: str, shell: str, command: str,
                      out: BinaryIO | None = None) -> tuple[subprocess.Popen, int]:
    """Start a helper with a private pipe, leaving command stdin untouched. POSIX only."""
    read_fd, write_fd = os.pipe()
    env = dict(os.environ, **{ENV_CMD: command})
    try:
        child = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), action, shell, str(read_fd)],
            env=env, pass_fds=(read_fd,), start_new_session=True,
            **_output_kwargs(out))
        return child, write_fd
    except BaseException:
        os.close(write_fd)
        raise
    finally:
        os.close(read_fd)


def _finish_posix_group(child: subprocess.Popen) -> None:
    """Stop remaining descendants, then keep the slot until their group exits."""
    deadline = time.monotonic() + TERMINATE_GRACE_SECONDS
    group_alive = True
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        group_alive = False
    while True:
        # On Linux the supervisor adopts orphaned descendants. Reap only after
        # Popen collected its own child, preserving the command's exit code.
        if child.poll() is not None:
            try:
                while os.waitpid(-1, os.WNOHANG)[0]:
                    pass
            except ChildProcessError:
                pass
        adopted = []
        if sys.platform.startswith("linux") and child.poll() is not None:
            # Orphans that called setsid() escape the original process group,
            # but still become our children after their ancestor is stopped.
            children_file = Path(f"/proc/{os.getpid()}/task/{os.getpid()}/children")
            adopted = [int(pid) for pid in children_file.read_text().split()]
            for pid in adopted:
                try:
                    os.kill(pid, signal.SIGKILL if time.monotonic() >= deadline else signal.SIGTERM)
                except ProcessLookupError:
                    pass
        if group_alive:
            try:
                os.killpg(child.pid, signal.SIGKILL if time.monotonic() >= deadline else 0)
            except ProcessLookupError:
                group_alive = False
        if not group_alive and not adopted:
            child.wait()
            return
        time.sleep(CHILD_POLL_SECONDS)


def _output_kwargs(out: BinaryIO | None) -> dict:
    """Popen kwargs sending stdout+stderr to `out`, or inheriting them when None."""
    return {"stdout": out, "stderr": subprocess.STDOUT} if out is not None else {}


def _run_child(shell: str, command: str, cancelled: threading.Event | None = None,
               lock: BinaryIO | None = None, out: BinaryIO | None = None) -> int:
    env = {k: v for k, v in os.environ.items() if k != ENV_CMD}
    env[ENV_HELD] = "1"
    kwargs: dict = {"env": env, **_output_kwargs(out)}
    if IS_WINDOWS:
        kwargs["creationflags"] = subprocess.BELOW_NORMAL_PRIORITY_CLASS
    else:
        if cancelled is None:
            kwargs["preexec_fn"] = lambda: os.nice(NICE_INCREMENT)
        if cancelled is not None:
            kwargs["start_new_session"] = True
            # The foreground shell also holds the lock if the supervisor is
            # killed outright. Normal cleanup unlocks only after the tree exits.
            kwargs["pass_fds"] = (lock.fileno(),) if lock is not None else ()
    try:
        if cancelled is not None and cancelled.is_set():
            return EXIT_CANCELLED
        child = subprocess.Popen(_shell_argv(shell, command), **kwargs)
    except FileNotFoundError:
        print(f"[heavy] shell not found: {shell}", file=sys.stderr)
        return EXIT_SHELL_MISSING
    if cancelled is not None:
        try:
            while child.poll() is None and not cancelled.wait(CHILD_POLL_SECONDS):
                pass
            return EXIT_CANCELLED if cancelled.is_set() else child.returncode
        finally:
            _finish_posix_group(child)
    try:
        return child.wait()
    except KeyboardInterrupt:
        child.terminate()
        return child.wait()


def _run_owned(shell: str, command: str, cancelled: threading.Event | None = None,
               out: BinaryIO | None = None) -> int:
    """Acquire and retain the slot: inside the supervisor on POSIX, in-process on Windows."""
    slots = _slot_count()
    max_wait = float(os.environ.get(ENV_MAX_WAIT, DEFAULT_MAX_WAIT_SECONDS))
    try:
        directory = _heavy_dir()
        acquired = acquire_slot(directory, slots, max_wait, cancelled)
    except OSError as exc:
        # E.g. a sandbox (Codex workspace-write) that can't write the lock dir:
        # running unqueued beats failing every heavy command.
        print(f"[heavy] queue unavailable ({exc}); running without a slot.", file=sys.stderr)
        return _run_child(shell, command, cancelled, out=out)
    if acquired is None:
        if cancelled is not None and cancelled.is_set():
            return EXIT_CANCELLED
        print(
            f"[heavy] queue busy: no slot free after {max_wait:g}s ({slots} slots). "
            "Retry later or use run_in_background.",
            file=sys.stderr,
        )
        return EXIT_QUEUE_BUSY
    handle, index = acquired
    info_path = directory / f"slot-{index}.json"
    try:
        info = {"pid": os.getpid(), "command": command, "cwd": os.getcwd(), "started": time.time()}
        info_path.write_text(json.dumps(info), encoding="utf-8")
        return _run_child(shell, command, cancelled, handle, out)
    finally:
        try:
            info_path.unlink(missing_ok=True)
        finally:
            try:
                _unlock(handle)
            finally:
                handle.close()


def _supervise(shell: str, control: int) -> int:
    cancelled = threading.Event()

    def watch_parent() -> None:
        try:
            while os.read(control, 1):
                pass
        finally:
            os.close(control)
            cancelled.set()

    threading.Thread(target=watch_parent, daemon=True).start()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda _signum, _frame: cancelled.set())
    if sys.platform.startswith("linux"):
        # PR_SET_CHILD_SUBREAPER makes abandoned grandchildren reapable here,
        # including on machines whose PID 1 does not reap orphaned processes.
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "cannot supervise orphaned children")
    os.nice(NICE_INCREMENT)
    return _run_owned(shell, os.environ[ENV_CMD], cancelled)


def run_heavy(shell: str, command: str, raw: bool = False) -> int:
    """Run `command` in `shell` once a slot is free; return its exit code.

    Returns 75 if no slot frees up within AW_HEAVY_MAX_WAIT seconds. If
    AW_HEAVY_HELD=1 (nested call) the command runs immediately, with raw output.
    If the lock dir can't be created or written, it warns and runs the command
    unqueued. Output is summarized unless `raw` or HEAVY_RAW=1.

    Example:
        >>> run_heavy("sh", "exit 3")  # doctest: +SKIP
        3
    """
    if os.environ.get(ENV_HELD) == "1":
        return _run_child(shell, command)
    if raw or os.environ.get(ENV_RAW) == "1":
        return _run_queued(shell, command)
    return _run_summarized(shell, command)


def _run_summarized(shell: str, command: str) -> int:
    """Run with output captured to a log, then print the structured summary."""
    try:
        log_path = _new_log_path(command)
        handle = open(log_path, "wb")
    except OSError as exc:
        print(f"[heavy] log dir unavailable ({exc}); showing raw output.", file=sys.stderr)
        return _run_queued(shell, command)
    started = time.monotonic()
    with handle:
        code = _run_queued(shell, command, handle)
    seconds = time.monotonic() - started
    text = log_path.read_text(encoding="utf-8", errors="replace")
    if code in QUEUE_EXIT_CODES:
        _write_utf8(sys.stderr, text)  # the queue's own messages, short and already actionable
    else:
        _write_utf8(sys.stdout, _summary(command, text, code, seconds, log_path) + "\n")
    _prune_logs(log_path.parent, _log_keep())
    return code


def _write_utf8(stream, text: str) -> None:
    """Write UTF-8 bytes, as the tools themselves do; a cp1252 console would mangle `●`, `›`."""
    stream.flush()
    buffer = getattr(stream, "buffer", None)
    if buffer is None:  # e.g. an in-memory stream in tests
        stream.write(text)
        return
    buffer.write(text.encode("utf-8"))
    buffer.flush()


def _summary(command: str, text: str, code: int, seconds: float, log_path: Path) -> str:
    try:
        import heavy_parsers
    except ImportError:  # an older deploy without the parser module: degrade to the tail
        tail = "\n".join(text.splitlines()[-40:])
        return f"heavy: exit {code} | log {log_path.as_posix()}\n{tail}"
    return heavy_parsers.summarize(command, text, code, seconds, log_path)


def _project_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def _new_log_path(command: str) -> Path:
    """<log dir>/<project>-<hash>/<timestamp>-<command slug>.log (dir created)."""
    root = _project_root(Path.cwd().resolve())
    digest = hashlib.sha1(root.as_posix().encode("utf-8")).hexdigest()[:PROJECT_HASH_CHARS]
    folder = Path(os.environ.get(ENV_LOG_DIR) or DEFAULT_LOG_DIR) / f"{root.name or 'root'}-{digest}"
    folder.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", command).strip("-")[:LOG_SLUG_CHARS] or "command"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return folder / f"{stamp}-{os.getpid()}-{slug}.log"


def _log_keep() -> int:
    path = Path(os.environ.get(ENV_SETTINGS) or DEFAULT_SETTINGS)
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8")).get("heavy_log_keep")
    except (OSError, tomllib.TOMLDecodeError):
        value = None
    return max(1, int(value)) if isinstance(value, int) else DEFAULT_LOG_KEEP


def _prune_logs(folder: Path, keep: int) -> None:
    """Delete all but the newest `keep` logs in this project's log folder."""
    try:
        logs = sorted(folder.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in logs[keep:]:
            old.unlink(missing_ok=True)
    except OSError:
        pass  # pruning is best effort; a busy file is retried next run


def _run_queued(shell: str, command: str, out: BinaryIO | None = None) -> int:
    if IS_WINDOWS:
        return _run_owned(shell, command, out=out)
    child, control = _spawn_controlled("_supervise", shell, command, out)
    try:
        try:
            return child.wait()
        except KeyboardInterrupt:
            os.close(control)
            control = None
            return child.wait()
    finally:
        if control is not None:
            os.close(control)


# --- status -------------------------------------------------------------------
def format_status(directory: Path, slots: int) -> list[str]:
    """One line per slot: free, or busy with holder info."""
    lines = []
    for index in range(slots):
        handle = _try_acquire(directory, index)
        if handle:
            _unlock(handle)
            handle.close()
            lines.append(f"slot-{index}: free")
            continue
        try:
            info = json.loads((directory / f"slot-{index}.json").read_text(encoding="utf-8"))
            since = time.strftime("%H:%M:%S", time.localtime(info["started"]))
            lines.append(
                f"slot-{index}: busy pid={info['pid']} since={since} "
                f"cwd={info['cwd']} cmd={info['command']}"
            )
        except (OSError, ValueError, KeyError):
            lines.append(f"slot-{index}: busy (holder info unavailable)")
    return lines


# --- hook ---------------------------------------------------------------------
def wrap_command(tool_name: str, command: str) -> str:
    """Build the human-readable wrapped command for Bash or PowerShell."""
    python = sys.executable.replace("\\", "/")
    script = Path(__file__).resolve().as_posix()
    if tool_name.lower() == "powershell":
        # Single-quoted PowerShell literal is exact; passing it via env (not argv)
        # avoids PowerShell 5.1 stripping embedded double quotes for native exes.
        quoted = "'" + command.replace("'", "''") + "'"
        return f'$env:{ENV_CMD} = {quoted}; & "{python}" "{script}" run --shell powershell --from-env'
    return f'"{python}" "{script}" run --shell bash -- {shlex.quote(command)}'


def hook_output(payload: object) -> dict | None:
    """Return the PreToolUse output for a hook payload, or None to stay silent."""
    if not isinstance(payload, dict) or payload.get("tool_name") not in HOOK_TOOLS:
        return None
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    wrapped = wrapped_or_none(payload["tool_name"], command) if isinstance(command, str) else None
    if wrapped is None:
        return None
    updated: dict = {"command": wrapped}
    if not tool_input.get("run_in_background"):
        updated["timeout"] = HOOK_TIMEOUT_MS
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": updated}}


def wrapped_or_none(tool_name: str, command: str) -> str | None:
    """Wrapped command if `command` is heavy and not already wrapped, else None.

    Example:
        >>> wrapped_or_none("bash", "ls") is None
        True
    """
    if WRAPPER_MARKER in command or not is_heavy(command):
        return None
    return wrap_command(tool_name, command)


def _wrap(tool_name: str) -> int:
    """`wrap` CLI for non-Claude harness plugins (e.g. opencode): stdin -> stdout."""
    wrapped = wrapped_or_none(tool_name, sys.stdin.read())
    if wrapped:
        sys.stdout.write(wrapped)
    return 0


def _hook() -> int:
    try:
        output = hook_output(json.loads(sys.stdin.read()))
        if output:
            sys.stdout.write(json.dumps(output))
    except Exception:  # a hook must never break the tool call
        pass
    return 0


# --- CLI ----------------------------------------------------------------------
def main(argv: list[str]) -> int:
    """CLI entry point; see module docstring."""
    usage = ("usage: heavy.py run [--raw] --shell bash|powershell|sh (-- <command> | --from-env)"
             " | status | hook | wrap bash|powershell")
    if not argv:
        print(usage, file=sys.stderr)
        return EXIT_USAGE
    action, rest = argv[0], argv[1:]
    if action == "_supervise" and len(rest) == 2:
        return _supervise(rest[0], int(rest[1]))
    if action == "hook":
        return _hook()
    if action == "wrap" and len(rest) == 1:
        return _wrap(rest[0])
    if action == "status":
        print("\n".join(format_status(_heavy_dir(), _slot_count())))
        return 0
    raw = action == "run" and rest[:1] == ["--raw"]
    if raw:
        rest = rest[1:]
    if action == "run" and len(rest) >= 3 and rest[0] == "--shell":
        shell, command_parts = rest[1], rest[2:]
        if command_parts == ["--from-env"] and os.environ.get(ENV_CMD):
            return run_heavy(shell, os.environ[ENV_CMD], raw)
        if command_parts[:1] == ["--"]:
            command_parts = command_parts[1:]
        if command_parts:
            return run_heavy(shell, " ".join(command_parts), raw)
    print(usage, file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
