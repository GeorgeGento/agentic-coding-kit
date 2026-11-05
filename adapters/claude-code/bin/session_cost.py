#!/usr/bin/env python3
"""Where did the tokens go? Per-session and per-agent token use from Claude Code logs.

Reads the local session logs (~/.claude/projects/<project>/<session>.jsonl and
<session>/subagents/agent-*.jsonl + .meta.json). Nothing leaves the machine.
Python stdlib only.

Usage:
    python session_cost.py                       # last 10 sessions, all projects
    python session_cost.py --last 3 --project CLAUDE
    python session_cost.py --since 2026-11-01 --json
    python session_cost.py --session <id>        # one session in detail

Columns:
    turns        assistant messages (one API call each)
    first ctx    context size of the first call: the fixed cost every session pays
                 (system prompt, rules, tool definitions, memory)
    in/write/read/out   fresh input, cache writes, cache reads, output tokens
    in-equiv     one comparable number, weighting by API price ratios relative to
                 fresh input: cache read 0.1x, cache write 1.25x (5 min) or 2x (1 h),
                 output 5x. Subscription limits are not published, so treat it as a
                 relative measure, not a bill.
    top tools    tools whose results added the most characters to the context

The log format is Claude Code's own and not a public contract: if a field goes
missing, the row shows zeros instead of failing.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PROJECTS = Path.home() / ".claude" / "projects"
DEFAULT_LAST = 10
TOP_TOOLS = 3
CACHE_READ_WEIGHT = 0.1
CACHE_WRITE_5M_WEIGHT = 1.25
CACHE_WRITE_1H_WEIGHT = 2.0
OUTPUT_WEIGHT = 5.0


@dataclass
class Usage:
    turns: int = 0
    first_context: int = 0
    fresh: int = 0
    write_5m: int = 0
    write_1h: int = 0
    read: int = 0
    output: int = 0
    tool_chars: Counter = field(default_factory=Counter)

    @property
    def write(self) -> int:
        return self.write_5m + self.write_1h

    @property
    def input_equivalent(self) -> float:
        return (self.fresh + CACHE_WRITE_5M_WEIGHT * self.write_5m
                + CACHE_WRITE_1H_WEIGHT * self.write_1h
                + CACHE_READ_WEIGHT * self.read + OUTPUT_WEIGHT * self.output)

    def add(self, other: "Usage") -> None:
        self.turns += other.turns
        self.fresh += other.fresh
        self.write_5m += other.write_5m
        self.write_1h += other.write_1h
        self.read += other.read
        self.output += other.output
        self.tool_chars.update(other.tool_chars)


@dataclass
class Agent:
    agent_type: str
    description: str
    model: str
    usage: Usage


@dataclass
class Session:
    session_id: str
    project: str
    started: str
    usage: Usage
    agents: list[Agent]

    @property
    def total(self) -> Usage:
        total = Usage(first_context=self.usage.first_context)
        total.add(self.usage)
        for agent in self.agents:
            total.add(agent.usage)
        return total


def _content_chars(content: object) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(_content_chars(part.get("text") or part.get("content") or "")
                   for part in content if isinstance(part, dict))
    return 0


def parse_log(path: Path) -> tuple[Usage, str]:
    """Usage of one .jsonl log, de-duplicating streamed parts of the same message."""
    usage = Usage()
    seen: set[str] = set()
    tool_names: dict[str, str] = {}
    started = ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            started = started or entry.get("timestamp", "")
            message = entry.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if entry.get("type") == "assistant":
                for part in content if isinstance(content, list) else []:
                    if isinstance(part, dict) and part.get("type") == "tool_use":
                        tool_names[part.get("id", "")] = part.get("name", "?")
                msg_id = message.get("id") or entry.get("requestId") or entry.get("uuid", "")
                raw = message.get("usage")
                if not isinstance(raw, dict) or msg_id in seen:
                    continue
                seen.add(msg_id)
                cache = raw.get("cache_creation") or {}
                write_total = raw.get("cache_creation_input_tokens", 0) or 0
                write_1h = cache.get("ephemeral_1h_input_tokens", 0) or 0
                usage.turns += 1
                usage.fresh += raw.get("input_tokens", 0) or 0
                usage.write_1h += write_1h
                usage.write_5m += max(write_total - write_1h, 0)
                usage.read += raw.get("cache_read_input_tokens", 0) or 0
                usage.output += raw.get("output_tokens", 0) or 0
                if usage.turns == 1:
                    usage.first_context = ((raw.get("input_tokens", 0) or 0) + write_total
                                           + (raw.get("cache_read_input_tokens", 0) or 0))
            elif entry.get("type") == "user":
                for part in content if isinstance(content, list) else []:
                    if isinstance(part, dict) and part.get("type") == "tool_result":
                        name = tool_names.get(part.get("tool_use_id", ""), "?")
                        usage.tool_chars[name] += _content_chars(part.get("content"))
    return usage, started


def load_session(path: Path) -> Session:
    usage, started = parse_log(path)
    agents = []
    sub_dir = path.with_suffix("") / "subagents"
    for log in sorted(sub_dir.glob("agent-*.jsonl")) if sub_dir.is_dir() else []:
        meta_path = log.with_suffix(".meta.json")
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            meta = {}
        agent_usage, _ = parse_log(log)
        agents.append(Agent(meta.get("agentType", "?"), meta.get("description", ""),
                            meta.get("model", ""), agent_usage))
    return Session(path.stem, path.parent.name, started, usage, agents)


def find_sessions(projects: Path, project: str | None, since: str | None,
                  session: str | None) -> list[Path]:
    logs = [p for p in projects.glob("*/*.jsonl")
            if (project is None or project.lower() in p.parent.name.lower())
            and (session is None or p.stem.startswith(session))]
    if since:
        cutoff = datetime.fromisoformat(since).replace(tzinfo=timezone.utc).timestamp()
        logs = [p for p in logs if p.stat().st_mtime >= cutoff]
    return sorted(logs, key=lambda p: p.stat().st_mtime, reverse=True)


# --- output -------------------------------------------------------------------
def _k(n: float) -> str:
    return f"{n / 1000:.1f}k" if n >= 1000 else f"{n:.0f}"


def _row(label: str, usage: Usage, first: bool = True) -> str:
    tools = ", ".join(f"{name} {_k(chars / 4)}" for name, chars in usage.tool_chars.most_common(TOP_TOOLS))
    first_ctx = _k(usage.first_context) if first else "-"
    return (f"{label:44.44} {usage.turns:5} {first_ctx:>9} {_k(usage.fresh):>7} {_k(usage.write):>7} "
            f"{_k(usage.read):>8} {_k(usage.output):>7} {_k(usage.input_equivalent):>9}  {tools}")


def format_report(sessions: list[Session]) -> str:
    header = (f"{'session / agent':44} {'turns':>5} {'first ctx':>9} {'in':>7} {'write':>7} "
              f"{'read':>8} {'out':>7} {'in-equiv':>9}  top tools (result ~tokens)")
    lines = [header, "-" * len(header)]
    for s in sessions:
        lines.append(_row(f"{s.started[:16]} {s.project[-18:]} {s.session_id[:8]}", s.total))
        lines.append(_row("  main session", s.usage))
        for a in s.agents:
            lines.append(_row(f"  {a.agent_type} ({a.model}) {a.description}", a.usage))
    return "\n".join(lines)


def to_json(sessions: list[Session]) -> str:
    def u(x: Usage) -> dict:
        return {"turns": x.turns, "first_context": x.first_context, "fresh": x.fresh,
                "cache_write": x.write, "cache_read": x.read, "output": x.output,
                "input_equivalent": round(x.input_equivalent),
                "tool_result_chars": dict(x.tool_chars.most_common())}
    return json.dumps([{"session": s.session_id, "project": s.project, "started": s.started,
                        "total": u(s.total), "main": u(s.usage),
                        "agents": [{"type": a.agent_type, "model": a.model,
                                    "description": a.description, **u(a.usage)}
                                   for a in s.agents]} for s in sessions], indent=2)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Token use per session and agent.")
    parser.add_argument("--projects-dir", type=Path, default=DEFAULT_PROJECTS)
    parser.add_argument("--project", help="substring of the project folder name")
    parser.add_argument("--session", help="session id (prefix)")
    parser.add_argument("--since", help="YYYY-MM-DD: sessions modified on or after")
    parser.add_argument("--last", type=int, default=DEFAULT_LAST, help="newest N sessions")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.projects_dir.is_dir():
        print(f"No Claude Code logs at {args.projects_dir}", file=sys.stderr)
        return 1
    paths = find_sessions(args.projects_dir, args.project, args.since, args.session)[:args.last]
    sessions = [load_session(p) for p in paths]
    if not sessions:
        print("No matching sessions.")
        return 0
    print(to_json(sessions) if args.json else format_report(sessions))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
