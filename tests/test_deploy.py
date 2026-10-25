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
        self.assertIn("@guidelines/coding-standards.md", text)
        self.assertIn("@roles/lead.md", text)
        self.assertNotIn("@guidelines/performance.md", text)  # on demand now
        self.assertNotIn("{{ALWAYS_LOADED}}", text)
        self.assertNotIn("{{MAX_PARALLEL}}", text)
        self.assertIn("Default `max_parallel` for this install: 1**", text)
        self.assertIn(f"]({self.target.as_posix()}/guidelines/debugging.md)", text)
        self.assertIn(f"]({self.target.as_posix()}/guidelines/motion-3d.md)", text)
        self.assertIn(f"]({self.target.as_posix()}/guidelines/ui-testing-platforms.md)", text)
        self.assertIn(f"]({self.target.as_posix()}/guidelines/git-and-versioning.md)", text)
        self.assertNotIn("](guidelines/", text)

    def test_renders_role_agents_with_short_protocol_but_not_lead(self):
        self.assertOk(self.deploy("claude-code", self.target))
        executor = (self.target / "agents" / "executor.md").read_text(encoding="utf-8")
        self.assertTrue(executor.startswith("---\nname: executor\n"))
        self.assertIn("model: claude-sonnet-5-5", executor)
        self.assertIn("# Agent Protocol", executor)
        self.assertNotIn("# Hierarchy Protocol", executor)
        escalation = (self.target / "agents" / "escalation.md").read_text(encoding="utf-8")
        self.assertIn("model: claude-opus-5-5", escalation)
        for role in deploy.SPECIALIST_ROLES:  # specialists fall back to the `specialist` model
            text = (self.target / "agents" / f"{role}.md").read_text(encoding="utf-8")
            self.assertIn("model: claude-sonnet-5-5", text, role)
        self.assertFalse((self.target / "agents" / "lead.md").exists())

    def test_retired_tier_agents_are_backed_up_and_removed(self):
        agents = self.target / "agents"
        agents.mkdir(parents=True)
        for name in ("senior", "mid", "junior"):
            (agents / f"{name}.md").write_text("old", encoding="utf-8")
        (agents / "electron-pro.md").write_text("user agent", encoding="utf-8")
        self.assertOk(self.deploy("claude-code", self.target))
        for name in ("senior", "mid", "junior"):
            self.assertFalse((agents / f"{name}.md").exists(), name)
            self.assertTrue(list((self.target / ".deploy-backups").glob(f"{name}.md.bak-*")), name)
        self.assertTrue((agents / "electron-pro.md").exists())

    def test_copies_core_dirs_skills_and_shared_scripts(self):
        self.assertOk(self.deploy("claude-code", self.target))
        for rel in ("guidelines/performance.md", "guidelines/debugging.md",
                    "protocols/task-types.md", "protocols/agent-protocol.md", "roles/lead.md",
                    "skills/ionic-capacitor/SKILL.md", "skills/setup/SKILL.md", "README.md"):
            self.assertTrue((self.target / rel).exists(), rel)
        for name in deploy.BIN_SCRIPTS:
            self.assertTrue((self.home / ".agent-workflows" / "bin" / name).exists(), name)

    def test_session_start_hook_reports_leftover_worktrees(self):
        self.assertOk(self.deploy("claude-code", self.target))
        self.assertOk(self.deploy("claude-code", self.target))
        settings = json.loads((self.target / "settings.json").read_text(encoding="utf-8"))
        entries = settings["hooks"]["SessionStart"]
        self.assertEqual(len(entries), 1)
        command = entries[0]["hooks"][0]["command"]
        self.assertIn('worktrees.py" list --quiet', command)
        self.assertNotIn("model", settings)  # no Lead model chosen in settings.toml

    def write_settings(self, text):
        memory = self.home / ".agent-memory"
        memory.mkdir(exist_ok=True)
        (memory / "settings.toml").write_text(text, encoding="utf-8")

    def test_user_settings_override_profile_and_flag_overrides_settings(self):
        self.write_settings('max_parallel = 3\n[models.claude-code]\n'
                            'executor = "my-exec"\nsecurity = "my-sec"\n')
        self.assertOk(self.deploy("claude-code", self.target))
        agents = self.target / "agents"
        self.assertIn("model: my-exec", (agents / "executor.md").read_text(encoding="utf-8"))
        self.assertIn("model: my-sec", (agents / "security.md").read_text(encoding="utf-8"))
        self.assertIn("model: claude-sonnet-5-5", (agents / "reviewer.md").read_text(encoding="utf-8"))
        claude_md = (self.target / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("for this install: 3**", claude_md)
        self.assertOk(self.deploy("claude-code", self.target, "--max-parallel", "2"))
        self.assertIn("for this install: 2**",
                      (self.target / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_chosen_lead_model_is_written_next_to_other_settings(self):
        self.target.mkdir(parents=True)
        (self.target / "settings.json").write_text(
            json.dumps({"model": "old", "theme": "dark"}), encoding="utf-8")
        self.write_settings('[models.claude-code]\nlead = "claude-opus-5-5"\n')
        result = self.deploy("claude-code", self.target)
        self.assertOk(result)
        settings = json.loads((self.target / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["model"], "claude-opus-5-5")
        self.assertEqual(settings["theme"], "dark")
        self.assertIn("PreToolUse", settings["hooks"])
        self.assertNotIn("Reminder: set the Lead", result.stdout)

    def test_missing_or_invalid_settings_fall_back_to_profile(self):
        result = self.deploy("claude-code", self.target)
        self.assertOk(result)
        self.assertIn("run /setup to choose", result.stdout)
        self.write_settings("not = [valid")
        result = self.deploy("claude-code", self.target)
        self.assertOk(result)
        self.assertIn("is not valid TOML", result.stdout)
        self.assertIn("model: claude-sonnet-5-5",
                      (self.target / "agents" / "executor.md").read_text(encoding="utf-8"))

    def test_existing_settings_toml_is_never_overwritten(self):
        self.write_settings("max_parallel = 2\n")
        self.assertOk(self.deploy("claude-code", self.target))
        self.assertEqual((self.home / ".agent-memory" / "settings.toml").read_text(encoding="utf-8"),
                         "max_parallel = 2\n")

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

    def test_retired_agent_orchestrator_is_backed_up_and_removed(self):
        old = self.target / "skills" / "agent-orchestrator"
        old.mkdir(parents=True)
        (old / "SKILL.md").write_text("old", encoding="utf-8")
        self.assertOk(self.deploy("claude-code", self.target))
        self.assertFalse(old.exists())
        self.assertTrue(list((self.target / ".deploy-backups").glob("agent-orchestrator.bak-*")))

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
        self.assertIn("# Coding Standards", text)
        self.assertIn("# Role: Lead", text)
        self.assertNotIn("# Performance", text)  # on demand now
        self.assertNotIn("@guidelines/", text)
        self.assertNotIn("name: lead", text)  # frontmatter stripped when inlining

    def test_agents_are_valid_toml_and_inherit_model_when_profile_empty(self):
        self.assertOk(self.deploy("codex", self.target, "--profile", "local"))
        agent = tomllib.loads((self.target / "agents" / "executor.toml").read_text(encoding="utf-8"))
        self.assertEqual(agent["name"], "executor")
        self.assertTrue(agent["description"])
        self.assertIn("# Agent Protocol", agent["developer_instructions"])
        self.assertNotIn("model", agent)

    def test_default_profile_renders_models_and_reminds_about_lead(self):
        result = self.deploy("codex", self.target)
        self.assertOk(result)
        models = deploy.load_profile("openai")
        expected = {"executor": models["executor"], "escalation": models["escalation"],
                    **{role: models["specialist"] for role in deploy.SPECIALIST_ROLES}}
        for role, model in expected.items():
            agent = tomllib.loads(
                (self.target / "agents" / f"{role}.toml").read_text(encoding="utf-8"))
            self.assertEqual(agent["model"], model, role)
        self.assertFalse((self.target / "agents" / "lead.toml").exists())
        self.assertIn(f"set the Lead (main session) model to {models['lead']}", result.stdout)

    def test_skills_go_to_shared_agents_dir_and_no_hook(self):
        self.assertOk(self.deploy("codex", self.target))
        self.assertTrue((self.home / ".agents" / "skills" / "ionic-capacitor" / "SKILL.md").exists())
        self.assertFalse((self.target / "skills" / "setup").exists())  # Claude-only skill
        self.assertFalse((self.target / "settings.json").exists())
        self.assertTrue((self.home / ".agent-workflows" / "bin" / "heavy.py").exists())


    def _lock_dir(self):
        return (self.home / ".agent-workflows" / "heavy").as_posix()

    def _memory_dir(self):
        return (self.home / ".agent-memory").as_posix()

    def _sandbox_roots(self):
        config = tomllib.loads((self.target / "config.toml").read_text(encoding="utf-8"))
        return config["sandbox_workspace_write"]["writable_roots"]

    def test_lock_dir_made_writable_in_new_config(self):
        self.assertOk(self.deploy("codex", self.target))
        self.assertEqual(self._sandbox_roots(), [self._lock_dir(), self._memory_dir()])
        self.assertTrue(Path(self._lock_dir()).is_dir())  # sandbox can't create it itself
        self.assertTrue(Path(self._memory_dir()).is_dir())

    def test_existing_config_is_preserved_backed_up_and_idempotent(self):
        self.target.mkdir()
        original = 'model = "m"\n\n[sandbox_workspace_write]\nnetwork_access = true\n'
        (self.target / "config.toml").write_text(original, encoding="utf-8")
        self.assertOk(self.deploy("codex", self.target))
        config = tomllib.loads((self.target / "config.toml").read_text(encoding="utf-8"))
        self.assertEqual(config["model"], "m")
        self.assertTrue(config["sandbox_workspace_write"]["network_access"])
        self.assertEqual(self._sandbox_roots(), [self._lock_dir(), self._memory_dir()])
        backups = list((self.target / ".deploy-backups").glob("config.toml.bak-*"))
        self.assertEqual([b.read_text(encoding="utf-8") for b in backups], [original])
        once = (self.target / "config.toml").read_text(encoding="utf-8")
        result = self.deploy("codex", self.target)
        self.assertOk(result)
        self.assertIn("already writable", result.stdout)
        self.assertEqual((self.target / "config.toml").read_text(encoding="utf-8"), once)

    def test_existing_simple_writable_roots_get_new_roots_appended(self):
        self.target.mkdir()
        original = f'[sandbox_workspace_write]\nwritable_roots = ["{self._lock_dir()}"]\n'
        (self.target / "config.toml").write_text(original, encoding="utf-8")
        self.assertOk(self.deploy("codex", self.target))
        self.assertEqual(self._sandbox_roots(), [self._lock_dir(), self._memory_dir()])
        once = (self.target / "config.toml").read_text(encoding="utf-8")
        result = self.deploy("codex", self.target)
        self.assertIn("already writable", result.stdout)
        self.assertEqual((self.target / "config.toml").read_text(encoding="utf-8"), once)

    def test_unsafe_writable_roots_layout_is_left_to_the_user(self):
        self.target.mkdir()
        original = '[sandbox_workspace_write]\nwritable_roots = [\n  "/elsewhere",\n]\n'
        (self.target / "config.toml").write_text(original, encoding="utf-8")
        result = self.deploy("codex", self.target)
        self.assertOk(result)
        self.assertIn("yourself", result.stdout)
        self.assertEqual((self.target / "config.toml").read_text(encoding="utf-8"), original)

    def test_invalid_config_toml_is_left_untouched(self):
        self.target.mkdir()
        (self.target / "config.toml").write_text("not = [valid", encoding="utf-8")
        result = self.deploy("codex", self.target)
        self.assertOk(result)
        self.assertIn("not valid TOML", result.stdout)
        self.assertEqual((self.target / "config.toml").read_text(encoding="utf-8"), "not = [valid")

    def test_no_hook_and_dry_run_skip_config(self):
        self.assertOk(self.deploy("codex", self.target, "--no-hook"))
        self.assertFalse((self.target / "config.toml").exists())
        dry = self.home / "dry" / ".codex"
        self.assertOk(self.deploy("codex", dry, "--dry-run"))
        self.assertFalse((dry / "config.toml").exists())


class CodexWritableRootTests(unittest.TestCase):
    def roots(self, text):
        return tomllib.loads(text)["sandbox_workspace_write"]["writable_roots"]

    def test_empty_config_gets_root(self):
        self.assertEqual(self.roots(deploy.add_codex_writable_root("", "/h/a")), ["/h/a"])

    def test_simple_list_gets_root_appended_keeping_others(self):
        text = '[sandbox_workspace_write]\nwritable_roots = ["/x"]  # mine\n'
        updated = deploy.add_codex_writable_root(text, "/h/a")
        self.assertEqual(self.roots(updated), ["/x", "/h/a"])
        self.assertIn("# mine", updated)
        self.assertEqual(text, '[sandbox_workspace_write]\nwritable_roots = ["/x"]  # mine\n')

    def test_empty_list_and_trailing_comma(self):
        for inner in ("", '"/x",'):
            text = f"[sandbox_workspace_write]\nwritable_roots = [{inner}]\n"
            updated = deploy.add_codex_writable_root(text, "/h/a")
            self.assertEqual(self.roots(updated)[-1], "/h/a")

    def test_already_listed_is_unchanged_and_idempotent(self):
        text = '[sandbox_workspace_write]\nwritable_roots = ["/x", "/h/a"]\n'
        self.assertEqual(deploy.add_codex_writable_root(text, "/h/a"), text)

    def test_multiline_list_is_not_edited(self):
        text = '[sandbox_workspace_write]\nwritable_roots = [\n "/x",\n]\n'
        self.assertIsNone(deploy.add_codex_writable_root(text, "/h/a"))

    def test_dotted_key_table_is_not_edited(self):
        text = "sandbox_workspace_write.network_access = true\n"
        self.assertIsNone(deploy.add_codex_writable_root(text, "/h/heavy"))

    def test_header_with_comment_gets_key_inserted(self):
        text = "[sandbox_workspace_write] # mine\nnetwork_access = true\n"
        updated = deploy.add_codex_writable_root(text, "/h/heavy")
        self.assertEqual(tomllib.loads(updated)["sandbox_workspace_write"],
                         {"network_access": True, "writable_roots": ["/h/heavy"]})


class OpencodeDeployTests(DeployCase):
    def setUp(self):
        super().setUp()
        self.target = self.home / ".config" / "opencode"

    def test_subagents_use_opencode_frontmatter(self):
        self.assertOk(self.deploy("opencode", self.target))
        executor = (self.target / "agents" / "executor.md").read_text(encoding="utf-8")
        front = executor.split("---")[1]
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


class MemoryTests(DeployCase):
    TOOL_TARGETS = {"claude-code": ".claude", "codex": ".codex",
                    "opencode": ".config/opencode"}

    def target(self, tool):
        return self.home / self.TOOL_TARGETS[tool]

    def memory(self):
        return self.home / ".agent-memory"

    def test_rendered_instructions_reference_memory_dir(self):
        mem = self.memory().as_posix()
        for tool, rel in self.TOOL_TARGETS.items():
            self.assertOk(self.deploy(tool, self.target(tool)))
            name = "CLAUDE.md" if tool == "claude-code" else "AGENTS.md"
            text = (self.target(tool) / name).read_text(encoding="utf-8")
            self.assertNotIn("{{MEMORY_", text, tool)
            self.assertIn(mem, text)
            if tool == "claude-code":
                self.assertIn(f"\n@{mem}/MEMORY.md\n", text)
            else:
                self.assertIn(f"**At session start, read `{mem}/MEMORY.md`**", text)

    def test_fresh_home_gets_seed_files(self):
        result = self.deploy("claude-code", self.target("claude-code"))
        self.assertOk(result)
        for name in ("MEMORY.md", "README.md", "settings.toml"):
            self.assertEqual((self.memory() / name).read_bytes(),
                             (deploy.MEMORY_SEED_DIR / name).read_bytes())
        self.assertEqual(result.stdout.count("seed    "), 3)

    def test_only_missing_seed_file_is_created(self):
        self.memory().mkdir()
        index = self.memory() / "MEMORY.md"
        index.write_bytes(b"mine\n")
        result = self.deploy("claude-code", self.target("claude-code"))
        self.assertOk(result)
        self.assertEqual(index.read_bytes(), b"mine\n")
        self.assertEqual((self.memory() / "README.md").read_bytes(),
                         (deploy.MEMORY_SEED_DIR / "README.md").read_bytes())
        self.assertEqual(result.stdout.count("seed    "), 2)

    def test_link_mode_seeds_real_files(self):
        self.assertOk(self.deploy("claude-code", self.target("claude-code"), "--link"))
        for name in ("MEMORY.md", "README.md"):
            path = self.memory() / name
            self.assertTrue(path.is_file() and not path.is_symlink(), name)

    def test_existing_memory_is_untouched_even_with_link(self):
        self.memory().mkdir()
        index = self.memory() / "MEMORY.md"
        entry = self.memory() / "likes-tabs.md"
        index.write_bytes(b"custom index\r\n- [T](likes-tabs.md) \xe2\x80\x94 h\n")
        entry.write_bytes(b"---\nname: x\n---\nbody\n")
        readme = self.memory() / "README.md"
        readme.write_bytes(b"my readme\n")
        (self.memory() / "settings.toml").write_bytes(b"max_parallel = 2\n")
        before = (index.read_bytes(), entry.read_bytes(), readme.read_bytes())
        for extra in ((), ("--link",)):
            for tool in self.TOOL_TARGETS:
                result = self.deploy(tool, self.target(tool), *extra)
                self.assertOk(result)
                self.assertIn("user-owned, untouched", result.stdout)
                self.assertFalse(index.is_symlink())
        self.assertEqual((index.read_bytes(), entry.read_bytes(), readme.read_bytes()), before)
        self.assertEqual(sorted(p.name for p in self.memory().iterdir()),
                         ["MEMORY.md", "README.md", "likes-tabs.md", "settings.toml"])
        for tool in self.TOOL_TARGETS:
            baks = self.target(tool) / ".deploy-backups"
            if baks.exists():
                self.assertFalse([p for p in baks.iterdir() if "MEMORY" in p.name or "likes" in p.name])

    def test_dry_run_creates_nothing(self):
        for tool in self.TOOL_TARGETS:
            self.assertOk(self.deploy(tool, self.target(tool), "--dry-run"))
        self.assertFalse(self.memory().exists())

    def test_git_hint_only_without_git_repo(self):
        result = self.deploy("claude-code", self.target("claude-code"))
        self.assertIn("private git repo", result.stdout)
        (self.memory() / ".git").mkdir()
        result = self.deploy("claude-code", self.target("claude-code"))
        self.assertNotIn("private git repo", result.stdout)
        self.assertEqual(sorted(p.name for p in self.memory().iterdir()),
                         [".git", "MEMORY.md", "README.md", "settings.toml"])

    def test_no_hook_still_seeds_memory(self):
        self.assertOk(self.deploy("codex", self.target("codex"), "--no-hook"))
        self.assertTrue((self.memory() / "MEMORY.md").exists())


class ArgumentTests(DeployCase):
    def test_unknown_profile_is_rejected(self):
        result = self.deploy("claude-code", self.home / ".claude", "--profile", "nope")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown profile", result.stdout)

    def test_refuses_to_deploy_into_repo(self):
        result = self.deploy("claude-code", REPO / "sub")
        self.assertEqual(result.returncode, 1)

    def test_max_parallel_below_one_is_rejected(self):
        result = self.deploy("claude-code", self.home / ".claude", "--max-parallel", "0")
        self.assertEqual(result.returncode, 1)
        self.assertIn("--max-parallel must be at least 1", result.stdout)


class ResolveSettingsTests(unittest.TestCase):
    PROFILE = {"max_parallel": 1, "models": {"lead": "p-lead", "executor": "p-exec",
                                             "specialist": "p-spec"}}

    def test_profile_only(self):
        settings = deploy.resolve_settings("claude-code", self.PROFILE, {}, None)
        self.assertEqual(settings.max_parallel, 1)
        self.assertEqual(settings.models["reviewer"], "p-spec")
        self.assertFalse(settings.lead_chosen)

    def test_user_settings_per_tool_and_flag_precedence(self):
        user = {"max_parallel": 3, "models": {"claude-code": {"lead": "u-lead", "e2e": "u-e2e"},
                                              "codex": {"executor": "codex-only"}}}
        settings = deploy.resolve_settings("claude-code", self.PROFILE, user, 2)
        self.assertEqual(settings.max_parallel, 2)
        self.assertEqual(settings.models["lead"], "u-lead")
        self.assertEqual(settings.models["executor"], "p-exec")  # codex entry ignored
        self.assertEqual(settings.models["e2e"], "u-e2e")
        self.assertEqual(settings.models["tester"], "p-spec")
        self.assertTrue(settings.lead_chosen)

    def test_inputs_are_not_mutated(self):
        profile = json.loads(json.dumps(self.PROFILE))
        deploy.resolve_settings("claude-code", profile, {}, None)
        self.assertEqual(profile, self.PROFILE)

    def test_default_when_nothing_sets_max_parallel(self):
        settings = deploy.resolve_settings("claude-code", {"models": {}}, {}, None)
        self.assertEqual(settings.max_parallel, deploy.DEFAULT_MAX_PARALLEL)


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
