"""Tests for deploy.py. Run: python -m unittest tests.test_deploy -v

Every deploy goes into a throwaway fake home, never the real ~/.claude etc.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import deploy  # noqa: E402

RUN_TIMEOUT = 60
HOOK_MARKER = 'heavy.py" hook'


class DeployCase(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="aw-deploy-test-"))
        self.addCleanup(shutil.rmtree, self.home, True)

    def deploy(self, tool, target, *extra):
        return subprocess.run(
            [sys.executable, str(REPO / "deploy.py"), "--tool", tool, "--target", str(target), *extra],
            capture_output=True, text=True, timeout=RUN_TIMEOUT,
        )

    def assertOk(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ClaudeCodeDeployTests(DeployCase):
    def setUp(self):
        super().setUp()
        self.target = self.home / ".claude"

    def test_renders_instructions_with_imports_and_absolute_links(self):
        self.assertOk(self.deploy("claude-code", self.target))
        text = (self.target / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("@guidelines/performance.md", text)
        self.assertIn("@roles/lead.md", text)
        self.assertNotIn("{{ALWAYS_LOADED}}", text)
        self.assertIn(f"]({self.target.as_posix()}/guidelines/git-and-versioning.md)", text)
        self.assertNotIn("](guidelines/", text)

    def test_renders_tier_agents_but_not_lead(self):
        self.assertOk(self.deploy("claude-code", self.target))
        senior = (self.target / "agents" / "senior.md").read_text(encoding="utf-8")
        self.assertIn("model: claude-opus-5-5", senior)
        self.assertIn("# Hierarchy Protocol", senior)
        self.assertTrue(senior.startswith("---\nname: senior\n"))
        self.assertFalse((self.target / "agents" / "lead.md").exists())

    def test_copies_core_dirs_skills_and_shared_queue(self):
        self.assertOk(self.deploy("claude-code", self.target))
        for rel in ("guidelines/performance.md", "protocols/task-types.md", "roles/lead.md",
                    "skills/ionic-capacitor/SKILL.md", "skills/setup/SKILL.md", "README.md"):
            self.assertTrue((self.target / rel).exists(), rel)
        self.assertTrue((self.home / ".agent-workflows" / "bin" / "heavy.py").exists())

    def test_hook_merges_into_existing_settings_idempotently(self):
        self.target.mkdir(parents=True)
        other = {"matcher": "Edit", "hooks": [{"type": "command", "command": "lint.sh"}]}
        (self.target / "settings.json").write_text(
            json.dumps({"model": "keep-me", "hooks": {"PreToolUse": [other]}}), encoding="utf-8")
        self.assertOk(self.deploy("claude-code", self.target))
        self.assertOk(self.deploy("claude-code", self.target))
        settings = json.loads((self.target / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["model"], "keep-me")
        pre = settings["hooks"]["PreToolUse"]
        self.assertIn(other, pre)
        ours = [e for e in pre if any(HOOK_MARKER in h["command"] for h in e["hooks"])]
        self.assertEqual(len(ours), 1)
        self.assertEqual(ours[0]["matcher"], "Bash|PowerShell")
        self.assertTrue(list((self.target / ".deploy-backups").glob("settings.json.bak-*")))

    def test_invalid_settings_json_is_left_untouched(self):
        self.target.mkdir(parents=True)
        (self.target / "settings.json").write_text("{ not json", encoding="utf-8")
        result = self.deploy("claude-code", self.target)
        self.assertOk(result)
        self.assertIn("queue hook NOT installed", result.stdout)
        self.assertEqual((self.target / "settings.json").read_text(encoding="utf-8"), "{ not json")

    def test_no_hook_flag_skips_settings(self):
        self.assertOk(self.deploy("claude-code", self.target, "--no-hook"))
        self.assertFalse((self.target / "settings.json").exists())

    def test_retired_team_skills_are_backed_up_and_removed(self):
        old = self.target / "skills" / "review-team"
        old.mkdir(parents=True)
        (old / "SKILL.md").write_text("old", encoding="utf-8")
        self.assertOk(self.deploy("claude-code", self.target))
        self.assertFalse(old.exists())
        self.assertTrue(list((self.target / ".deploy-backups").glob("review-team.bak-*")))

    def test_user_installed_skills_survive(self):
        mine = self.target / "skills" / "my-skill"
        mine.mkdir(parents=True)
        self.assertOk(self.deploy("claude-code", self.target))
        self.assertTrue(mine.exists())

    def test_dry_run_changes_nothing(self):
        self.assertOk(self.deploy("claude-code", self.target, "--dry-run"))
        self.assertFalse(self.target.exists())
        self.assertFalse((self.home / ".agent-workflows").exists())


class CodexDeployTests(DeployCase):
    def setUp(self):
        super().setUp()
        self.target = self.home / ".codex"

    def test_agents_md_inlines_always_loaded_files(self):
        self.assertOk(self.deploy("codex", self.target))
        text = (self.target / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("# Performance", text)
        self.assertIn("# Role: Lead", text)
        self.assertNotIn("@guidelines/", text)
        self.assertNotIn("name: lead", text)  # frontmatter stripped when inlining

    def test_agents_are_valid_toml_and_inherit_model_when_profile_empty(self):
        self.assertOk(self.deploy("codex", self.target))
        agent = tomllib.loads((self.target / "agents" / "mid.toml").read_text(encoding="utf-8"))
        self.assertEqual(agent["name"], "mid")
        self.assertTrue(agent["description"])
        self.assertIn("# Hierarchy Protocol", agent["developer_instructions"])
        self.assertNotIn("model", agent)

    def test_skills_go_to_shared_agents_dir_and_no_hook(self):
        self.assertOk(self.deploy("codex", self.target))
        self.assertTrue((self.home / ".agents" / "skills" / "ionic-capacitor" / "SKILL.md").exists())
        self.assertFalse((self.target / "skills" / "setup").exists())  # Claude-only skill
        self.assertFalse((self.target / "settings.json").exists())
        self.assertTrue((self.home / ".agent-workflows" / "bin" / "heavy.py").exists())


class OpencodeDeployTests(DeployCase):
    def setUp(self):
        super().setUp()
        self.target = self.home / ".config" / "opencode"

    def test_subagents_use_opencode_frontmatter(self):
        self.assertOk(self.deploy("opencode", self.target))
        mid = (self.target / "agents" / "mid.md").read_text(encoding="utf-8")
        front = mid.split("---")[1]
        self.assertIn("mode: subagent", front)
        self.assertIn("model: anthropic/claude-sonnet-5-5", front)
        self.assertNotIn("name:", front)
        self.assertTrue((self.target / "AGENTS.md").exists())
        self.assertTrue((self.target / "skills" / "ionic-capacitor" / "SKILL.md").exists())

    def test_plugin_points_at_shared_queue_in_real_home(self):
        self.assertOk(self.deploy("opencode", self.target))
        plugin = (self.target / "plugins" / "heavy-queue.js").read_text(encoding="utf-8")
        self.assertNotIn("__PYTHON__", plugin)
        self.assertNotIn("__HEAVY__", plugin)
        heavy = self.home / ".agent-workflows" / "bin" / "heavy.py"
        self.assertIn(json.dumps(heavy.as_posix()), plugin)
        self.assertTrue(heavy.exists())

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_plugin_is_valid_javascript(self):
        self.assertOk(self.deploy("opencode", self.target))
        mjs = self.home / "plugin.mjs"
        shutil.copy(self.target / "plugins" / "heavy-queue.js", mjs)
        result = subprocess.run(["node", "--check", str(mjs)], capture_output=True, text=True,
                                timeout=RUN_TIMEOUT)
        self.assertOk(result)


class ArgumentTests(DeployCase):
    def test_unknown_profile_is_rejected(self):
        result = self.deploy("claude-code", self.home / ".claude", "--profile", "nope")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown profile", result.stdout)

    def test_refuses_to_deploy_into_repo(self):
        result = self.deploy("claude-code", REPO / "sub")
        self.assertEqual(result.returncode, 1)


class MergeHookTests(unittest.TestCase):
    def test_does_not_mutate_input_and_refreshes_existing_command(self):
        original = {"hooks": {"PreToolUse": [
            {"matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": '"old" "x/heavy.py" hook'}]}]}}
        snapshot = json.dumps(original)
        merged = deploy.merge_hook(original, '"new" "x/heavy.py" hook')
        self.assertEqual(json.dumps(original), snapshot)
        self.assertEqual(merged["hooks"]["PreToolUse"][0]["hooks"][0]["command"], '"new" "x/heavy.py" hook')
        self.assertEqual(len(merged["hooks"]["PreToolUse"]), 1)


if __name__ == "__main__":
    unittest.main()
