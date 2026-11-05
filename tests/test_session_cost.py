"""Tests for adapters/claude-code/bin/session_cost.py. Run: python -m unittest tests.test_session_cost -v

Uses synthetic logs in a temp dir shaped like ~/.claude/projects; never the real one.
"""

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "adapters" / "claude-code" / "bin"))
import session_cost as sc  # noqa: E402


def assistant(msg_id, usage, content=None):
    return {"type": "assistant", "timestamp": "2026-11-02T10:00:00Z",
            "message": {"id": msg_id, "usage": usage, "content": content or []}}


def tool_result(tool_id, text):
    return {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": tool_id, "content": text}]}}


USAGE = {"input_tokens": 10, "cache_creation_input_tokens": 1000,
         "cache_creation": {"ephemeral_1h_input_tokens": 600},
         "cache_read_input_tokens": 5000, "output_tokens": 100}


class SessionCostTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="aw-session-cost-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.project = self.root / "c--work-myapp"
        self.project.mkdir()

    def write_log(self, path, entries, junk=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(e) for e in entries] + (["{not json"] if junk else [])
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def make_session(self, sid="s1"):
        log = self.project / f"{sid}.jsonl"
        use = {"type": "tool_use", "id": "t1", "name": "Bash"}
        self.write_log(log, [
            assistant("m1", USAGE, [use]),
            assistant("m1", USAGE),  # second streamed part of the same message: not counted twice
            tool_result("t1", "x" * 400),
            assistant("m2", {"input_tokens": 5, "cache_read_input_tokens": 6000, "output_tokens": 50}),
        ], junk=True)
        sub = self.project / sid / "subagents"
        self.write_log(sub / "agent-a1.jsonl", [assistant("a1", USAGE)])
        (sub / "agent-a1.meta.json").write_text(
            json.dumps({"agentType": "executor", "description": "Build X", "model": "sonnet"}),
            encoding="utf-8")
        return log

    def test_dedupes_streamed_parts_and_splits_cache_writes(self):
        usage, started = sc.parse_log(self.make_session())
        self.assertEqual(usage.turns, 2)
        self.assertEqual((usage.fresh, usage.read, usage.output), (15, 11000, 150))
        self.assertEqual((usage.write_1h, usage.write_5m), (600, 400))
        self.assertEqual(usage.first_context, 10 + 1000 + 5000)
        self.assertEqual(started, "2026-11-02T10:00:00Z")

    def test_tool_result_chars_are_attributed_to_the_tool(self):
        usage, _ = sc.parse_log(self.make_session())
        self.assertEqual(usage.tool_chars["Bash"], 400)

    def test_session_includes_subagents_with_meta(self):
        session = sc.load_session(self.make_session())
        self.assertEqual(len(session.agents), 1)
        agent = session.agents[0]
        self.assertEqual((agent.agent_type, agent.model, agent.description), ("executor", "sonnet", "Build X"))
        self.assertEqual(session.total.turns, 3)
        self.assertEqual(session.total.first_context, session.usage.first_context)

    def test_input_equivalent_uses_price_ratios(self):
        usage = sc.Usage(fresh=100, write_5m=100, write_1h=100, read=1000, output=10)
        self.assertAlmostEqual(usage.input_equivalent, 100 + 125 + 200 + 100 + 50)

    def test_missing_fields_and_meta_give_zeros_not_errors(self):
        log = self.project / "s2.jsonl"
        self.write_log(log, [assistant("m1", {}), {"type": "assistant", "message": "odd"}])
        sub = self.project / "s2" / "subagents"
        self.write_log(sub / "agent-b.jsonl", [])
        session = sc.load_session(log)
        self.assertEqual(session.usage.turns, 1)
        self.assertEqual(session.usage.input_equivalent, 0)
        self.assertEqual(session.agents[0].agent_type, "?")

    def test_project_and_session_filters(self):
        self.make_session("abc123")
        other = self.root / "c--work-other"
        self.write_log(other / "zzz.jsonl", [assistant("m", USAGE)])
        found = sc.find_sessions(self.root, "myapp", None, None)
        self.assertEqual([p.stem for p in found], ["abc123"])
        self.assertEqual([p.stem for p in sc.find_sessions(self.root, None, None, "zz")], ["zzz"])

    def test_cli_text_and_json(self):
        self.make_session()
        for flags in ([], ["--json"]):
            out = io.StringIO()
            with redirect_stdout(out):
                code = sc.main(["--projects-dir", str(self.root), *flags])
            self.assertEqual(code, 0)
            if flags:
                data = json.loads(out.getvalue())
                self.assertEqual(data[0]["agents"][0]["type"], "executor")
                self.assertEqual(data[0]["total"]["turns"], 3)
            else:
                self.assertIn("main session", out.getvalue())
                self.assertIn("executor (sonnet) Build X", out.getvalue())

    def test_missing_projects_dir(self):
        self.assertEqual(sc.main(["--projects-dir", str(self.root / "nope")]), 1)


if __name__ == "__main__":
    unittest.main()
