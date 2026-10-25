"""Turn raw test/build/lint output into a short, structured summary for agents.

Pure functions only (text in, text out) so they are easy to test with fixtures.
heavy.py captures the full output to a log and prints `summarize(...)` instead.

Parsers read each tool's normal text output; none of them change the command.
Rules that keep the summary honest:
  - the exit code is always in the header, and decides pass/fail, never a parser;
  - non-zero exit with nothing parsed -> fallback (error-like lines + tail), never empty;
  - a parser crash -> fallback plus a one-line note.

Example:
    summarize("npm test", raw_text, 1, 41.2, Path("~/.agent-workflows/logs/x/1.log"))
    # heavy: npm test | exit 1 | 41s | 3 failed, 209 passed | log ...
    # 1. UserService › returns 401 when token missing
    #    Expected: 401  Received: 200
    #    at Object.<anonymous> (src/user.service.spec.ts:48:15)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

MAX_ITEMS = 10
ITEM_LINES = 6
MAX_LINES = 60
MAX_LINE_CHARS = 200
MAX_COMMAND_CHARS = 80
FALLBACK_ERROR_LINES = 20
FALLBACK_TAIL_LINES = 40
LOCATION_SCAN_LINES = 8

ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07")
NOISE_FRAME = re.compile(r"(node_modules|node:internal|\(internal/|<anonymous>\)$)")
CODE_FRAME = re.compile(r"^\s*(>\s*)?\d+\s*\|")
CARET_LINE = re.compile(r"^\s*\|\s*[\^~\s]*$")
SEPARATOR = re.compile(r"^\s*[─⎯\-=_]{6,}\s*$")
LOCATION = re.compile(r"[\w./\\-]+\.\w+:\d+(:\d+)?")
ERROR_LIKE = re.compile(r"\b(error|Error|ERROR|FAIL|FAILED|Exception|Traceback|panicked)\b")


@dataclass
class Parsed:
    tool: str
    counts: str = ""
    items: list[list[str]] = field(default_factory=list)


# --- helpers -----------------------------------------------------------------
def clean_lines(text: str) -> list[str]:
    """Strip ANSI codes and carriage-return redraws; keep the final text of each line."""
    lines = []
    for raw in ANSI.sub("", text).split("\n"):
        lines.append(raw.rsplit("\r", 1)[-1].rstrip())
    return lines


def _keep(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not (NOISE_FRAME.search(stripped) or CODE_FRAME.match(line)
                                   or CARET_LINE.match(line) or SEPARATOR.match(line))


def _block(lines: list[str], start: int, is_end: Callable[[str], bool]) -> list[str]:
    """Meaningful lines after `start` up to the next line where is_end() is true."""
    body = []
    for line in lines[start + 1:]:
        if is_end(line):
            break
        if _keep(line):
            body.append(line.strip())
    return body


def _first_match(lines: list[str], pattern: re.Pattern) -> re.Match | None:
    for line in lines:
        match = pattern.match(line)
        if match:
            return match
    return None


# --- parsers -----------------------------------------------------------------
PW_HEADER = re.compile(r"^\s+\d+\) (\[[^\]]+\] › .+?)\s*─*$")
PW_COUNT = re.compile(r"^\s+(\d+ (?:passed|failed|flaky|skipped|did not run))\b")


def parse_playwright(lines: list[str]) -> Parsed | None:
    starts = [i for i, line in enumerate(lines) if PW_HEADER.match(line)]
    # Bare "  5 passed" lines are too generic on their own; Playwright also prints `›` paths.
    if not starts and not any(" › " in line for line in lines):
        return None
    counts = [m.group(1) for m in map(PW_COUNT.match, lines) if m]
    if not starts and not counts:
        return None
    items = []
    for i in starts:
        body = _block(lines, i, lambda l: bool(PW_HEADER.match(l) or PW_COUNT.match(l)))
        body = [b for b in body if not b.startswith(("attachment #", "Error Context:", "Usage:"))]
        items.append([PW_HEADER.match(lines[i]).group(1), *body])
    return Parsed("playwright", ", ".join(counts), items)


JEST_COUNT = re.compile(r"^Tests:\s+(.+?)(?:,\s*\d+ total)?$")
JEST_HEADER = re.compile(r"^\s*● (?!Console\b)(.+)$")


def parse_jest(lines: list[str]) -> Parsed | None:
    count = _first_match(lines, JEST_COUNT)
    starts = [i for i, line in enumerate(lines) if JEST_HEADER.match(line)]
    if not count and not starts:
        return None
    items, seen = [], set()
    for i in starts:
        title = JEST_HEADER.match(lines[i]).group(1).strip()
        if title in seen:
            continue
        seen.add(title)
        body = _block(lines, i, lambda l: bool(JEST_HEADER.match(l) or JEST_COUNT.match(l)
                                               or l.startswith("Test Suites:")))
        items.append([title, *body])
    return Parsed("jest", count.group(1) if count else "", items)


VITEST_COUNT = re.compile(r"^\s*Tests\s{2,}(.+?)(?:\s+\(\d+\))?$")
VITEST_HEADER = re.compile(r"^\s*FAIL\s+(\S.*>.*)$")


def parse_vitest(lines: list[str]) -> Parsed | None:
    count = _first_match(lines, VITEST_COUNT)
    starts = [i for i, line in enumerate(lines) if VITEST_HEADER.match(line)]
    if not count and not starts:
        return None
    items, seen = [], set()
    for i in starts:
        title = VITEST_HEADER.match(lines[i]).group(1).strip()
        if title in seen:
            continue
        seen.add(title)
        body = _block(lines, i, lambda l: bool(VITEST_HEADER.match(l) or VITEST_COUNT.match(l)
                                               or re.match(r"^\s*Test Files\s", l)
                                               or re.match(r"^\s*⎯+\[\d+/\d+\]⎯+", l)))
        items.append([title, *body])
    counts = count.group(1).replace(" | ", ", ") if count else ""
    return Parsed("vitest", counts, items)


PYTEST_COUNT = re.compile(r"^=+ (.+?) in [\d.]+s.*=+$")
PYTEST_SECTION = re.compile(r"^_{3,} (.+?) _{3,}$")
PYTEST_SHORT = re.compile(r"^(FAILED|ERROR) (\S+)(?: - (.*))?$")
PYTEST_LOCATION = re.compile(r"^(\S+\.py):(\d+): (\w+)")


def parse_pytest(lines: list[str]) -> Parsed | None:
    count = _first_match(lines, PYTEST_COUNT)
    short = [m for m in map(PYTEST_SHORT.match, lines) if m]
    if not count and not short:
        return None
    items = []
    for i, line in enumerate(lines):
        section = PYTEST_SECTION.match(line)
        if not section:
            continue
        body = []
        for follow in lines[i + 1:]:
            if PYTEST_SECTION.match(follow) or follow.startswith("="):
                break
            if follow.startswith("E   ") and len(body) < ITEM_LINES - 2:
                body.append(follow[4:].strip())
            elif PYTEST_LOCATION.match(follow):
                body.append(follow.strip())
        items.append([section.group(1), *body])
    if not items:
        items = [[f"{m.group(2)}" + (f" - {m.group(3)}" if m.group(3) else "")] for m in short]
    return Parsed("pytest", count.group(1) if count else "", items)


CARGO_DIAG = re.compile(r"^error(\[E\d+\])?: (.+)$")
CARGO_ARROW = re.compile(r"^\s*--> (\S+)$")
CARGO_SUMMARY_ERROR = re.compile(r"^(could not compile|aborting due to)")
CARGO_RESULT = re.compile(r"^test result: (\w+)\. (.+?); finished")
CARGO_PANIC_BLOCK = re.compile(r"^---- (\S+) stdout ----$")
CARGO_COMPILE_FAIL = re.compile(r"^error: could not compile .+ due to (\d+) previous errors?")


def parse_cargo(lines: list[str]) -> Parsed | None:
    items = []
    for i, line in enumerate(lines):
        diag = CARGO_DIAG.match(line)
        if diag and not CARGO_SUMMARY_ERROR.match(diag.group(2)):
            where = next((m.group(1) for m in map(CARGO_ARROW.match,
                                                   lines[i + 1:i + LOCATION_SCAN_LINES]) if m), "")
            code = diag.group(1) or ""
            items.append([f"{where} error{code}: {diag.group(2)}".strip()])
        panic = CARGO_PANIC_BLOCK.match(line)
        if panic:
            body = _block(lines, i, lambda l: bool(CARGO_PANIC_BLOCK.match(l)
                                                   or l.strip() == "failures:"))
            body = [b for b in body if not b.startswith("note: run with")]
            items.append([panic.group(1), *body])
    result = _first_match(lines, CARGO_RESULT)
    compile_fail = _first_match(lines, CARGO_COMPILE_FAIL)
    if not items and not result and not compile_fail:
        return None
    counts = result.group(2) if result else (
        f"{compile_fail.group(1)} compile error(s)" if compile_fail else "")
    return Parsed("cargo", counts, items)


TSC_PAREN = re.compile(r"^(.+?)\((\d+),(\d+)\): error (TS\d+): (.+)$")
TSC_PRETTY = re.compile(r"^(.+?):(\d+):(\d+) - error (TS\d+): (.+)$")
NG_ERROR = re.compile(r"^\s*(?:✘|X) \[ERROR\] (.+?)(?: \[plugin .+\])?$")
NG_LOCATION = re.compile(r"^\s+(\S+?):(\d+):(\d+):$")
TSC_FOUND = re.compile(r"^Found (\d+ errors?)")


def parse_tsc(lines: list[str]) -> Parsed | None:
    items = []
    for i, line in enumerate(lines):
        match = TSC_PAREN.match(line) or TSC_PRETTY.match(line)
        if match:
            path, row, col, code, msg = match.groups()
            items.append([f"{path}:{row}:{col} {code}: {msg}"])
            continue
        ng = NG_ERROR.match(line)
        if ng:
            where = next((f"{m.group(1)}:{m.group(2)}:{m.group(3)} " for m in
                          map(NG_LOCATION.match, lines[i + 1:i + LOCATION_SCAN_LINES]) if m), "")
            items.append([f"{where}{ng.group(1)}"])
    found = _first_match(lines, TSC_FOUND)
    if not items and not found:
        return None
    return Parsed("tsc", found.group(1) if found else f"{len(items)} error(s)", items)


ESLINT_FILE = re.compile(r"^(?:[A-Za-z]:[\\/]|/|\.{0,2}[\w@.-]+[\\/])\S*\.\w+$")
ESLINT_PROBLEM = re.compile(r"^\s+(\d+):(\d+)\s+(error|warning)\s+(.+?)\s{2,}(\S+)$")
ESLINT_TOTAL = re.compile(r"^✖ (\d+ problems? \(.+\))")


def parse_eslint(lines: list[str]) -> Parsed | None:
    items, current, problems = [], "", 0
    for line in lines:
        if ESLINT_FILE.match(line):
            current = line.strip()
            continue
        problem = ESLINT_PROBLEM.match(line)
        if problem:
            problems += 1
            row, col, level, msg, rule = problem.groups()
            if level == "error":
                items.append([f"{current}:{row}:{col} {rule}: {msg}"])
    total = _first_match(lines, ESLINT_TOTAL)
    if not problems and not total:
        return None
    return Parsed("eslint", total.group(1) if total else f"{problems} problem(s)", items)


PARSERS = (parse_playwright, parse_jest, parse_vitest, parse_pytest, parse_cargo,
           parse_tsc, parse_eslint)


# --- summary -----------------------------------------------------------------
def parse(lines: list[str], failed: bool) -> Parsed | None:
    """First parser that explains the run: with items when it failed, with counts otherwise."""
    fallback = None
    for parser in PARSERS:
        result = parser(lines)
        if result is None:
            continue
        if (result.items if failed else result.counts):
            return result
        fallback = fallback or result
    return fallback


def _cap_item(item: list[str]) -> list[str]:
    """First ITEM_LINES lines, but never drop the first file:line:col location."""
    if len(item) <= ITEM_LINES:
        return item
    head = item[:ITEM_LINES - 1]
    if any(LOCATION.search(line) for line in head):
        return item[:ITEM_LINES]
    where = next((line for line in item[ITEM_LINES - 1:] if LOCATION.search(line)), None)
    return [*head, where] if where else item[:ITEM_LINES]


def _fmt_items(items: list[list[str]]) -> list[str]:
    grouped: dict[tuple[str, ...], int] = {}
    for item in items:
        key = tuple(line[:MAX_LINE_CHARS] for line in _cap_item(item))
        grouped[key] = grouped.get(key, 0) + 1
    out = []
    for n, (item, times) in enumerate(list(grouped.items())[:MAX_ITEMS], 1):
        repeat = f"  (x{times})" if times > 1 else ""
        out.append(f"{n}. {item[0]}{repeat}")
        out.extend(f"   {line}" for line in item[1:])
    if len(grouped) > MAX_ITEMS:
        out.append(f"(showing {MAX_ITEMS} of {len(grouped)} failures; see log)")
    return out


def _fallback(lines: list[str]) -> list[str]:
    errors, seen = [], set()
    for line in lines:
        text = line.strip()
        if ERROR_LIKE.search(text) and _keep(line) and text not in seen:
            seen.add(text)
            errors.append(text[:MAX_LINE_CHARS])
    tail = [line[:MAX_LINE_CHARS] for line in lines if line.strip()][-FALLBACK_TAIL_LINES:]
    out = []
    if errors:
        out += ["error-like lines:", *errors[:FALLBACK_ERROR_LINES]]
    return out + [f"last {len(tail)} lines:", *tail]


def summarize(command: str, text: str, exit_code: int, seconds: float, log_path: Path) -> str:
    """The structured summary heavy.py prints instead of the raw output."""
    lines = clean_lines(text)
    failed = exit_code != 0
    note = ""
    try:
        parsed = parse(lines, failed)
    except Exception as exc:  # a parser bug must never hide a failure
        parsed, note = None, f"[heavy] parser error ({type(exc).__name__}); raw excerpt below"
    short = command if len(command) <= MAX_COMMAND_CHARS else command[:MAX_COMMAND_CHARS - 3] + "..."
    header = f"heavy: {short} | exit {exit_code} | {seconds:.0f}s"
    if parsed and parsed.counts:
        header += f" | {parsed.counts}"
    header += f" | log {log_path.as_posix()}"
    if not failed:
        return header
    body = _fmt_items(parsed.items) if parsed and parsed.items else _fallback(lines)
    out = [header, *([note] if note else []), *body]
    if len(out) > MAX_LINES:
        out = out[:MAX_LINES - 1] + ["(summary truncated; full output in the log)"]
    return "\n".join(out)
