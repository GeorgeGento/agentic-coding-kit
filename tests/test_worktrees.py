"""Tests for core/bin/worktrees.py. Run: python -m unittest tests.test_worktrees -v

Every test uses a throwaway git repo in a temp dir, never a real one.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "core" / "bin" / "worktrees.py"
RUN_TIMEOUT = 60
GIT_IDENTITY = ("-c", "user.name=Test", "-c", "user.email=test@example.com")


@unittest.skipUnless(shutil.which("git"), "git not installed")
class WorktreesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aw-worktrees-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self.git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "app.txt").write_text("one\n", encoding="utf-8")
        self.git(self.repo, "add", "-A")
        self.git(self.repo, *GIT_IDENTITY, "commit", "-q", "-m", "init")

    def git(self, cwd, *args):
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                                timeout=RUN_TIMEOUT)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def run_script(self, *args, cwd=None, **env):
        full_env = {**os.environ, "AW_SETTINGS": str(self.tmp / "settings.toml"), **env}
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd or self.repo,
                              capture_output=True, text=True, timeout=RUN_TIMEOUT, env=full_env)

    def add_worktree(self, name, branch_prefix="agent/"):
        path = self.tmp / name
        self.git(self.repo, "worktree", "add", "-q", "-b", f"{branch_prefix}{name}", str(path))
        return path

    def do_work(self, wt):
        (wt / "app.txt").write_text("one\ntwo\n", encoding="utf-8")
        (wt / "new.txt").write_text("brand new\n", encoding="utf-8")  # untracked

    def branches(self):
        return self.git(self.repo, "branch", "--list", "--format=%(refname:short)").split()

    def test_quiet_list_is_silent_without_leftovers(self):
        result = self.run_script("list", "--quiet")
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_quiet_list_reports_leftovers_in_one_line(self):
        self.add_worktree("login")
        result = self.run_script("list", "--quiet")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(result.stdout.strip().splitlines()), 1)
        self.assertIn("1 leftover agent worktree(s)", result.stdout)
        self.assertIn("agent/login", result.stdout)

    def test_list_shows_size_state_and_applied(self):
        wt = self.add_worktree("login")
        self.do_work(wt)
        out = self.run_script("list").stdout
        self.assertIn("agent/login", out)
        self.assertIn("dirty", out)
        self.assertIn("NOT applied", out)
        self.assertIn("1 agent worktree(s)", out)

    def test_non_agent_worktrees_are_ignored(self):
        self.add_worktree("feature", branch_prefix="user/")
        self.assertIn("No agent worktrees.", self.run_script("list").stdout)
        self.run_script("clean")
        self.assertTrue((self.tmp / "feature").exists())
        self.assertIn("user/feature", self.branches())

    def test_apply_copies_changes_uncommitted_including_untracked(self):
        wt = self.add_worktree("login")
        self.do_work(wt)
        result = self.run_script("apply", str(wt))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / "app.txt").read_text(encoding="utf-8"), "one\ntwo\n")
        self.assertEqual((self.repo / "new.txt").read_text(encoding="utf-8"), "brand new\n")
        self.assertEqual(self.git(self.repo, "rev-list", "--count", "HEAD").strip(), "1")
        self.assertIn("applied", self.run_script("list").stdout.replace("NOT applied", ""))
        self.assertIn("already applied", self.run_script("apply", str(wt)).stdout)

    def test_clean_removes_applied_worktree_and_branch(self):
        wt = self.add_worktree("login")
        self.do_work(wt)
        self.run_script("apply", str(wt))
        result = self.run_script("clean")
        self.assertIn("removed  agent/login", result.stdout)
        self.assertFalse(wt.exists())
        self.assertNotIn("agent/login", self.branches())
        self.assertEqual((self.repo / "new.txt").read_text(encoding="utf-8"), "brand new\n")

    def test_clean_keeps_unapplied_work(self):
        wt = self.add_worktree("login")
        self.do_work(wt)
        result = self.run_script("clean")
        self.assertIn("kept     agent/login", result.stdout)
        self.assertTrue((wt / "new.txt").exists())
        self.assertIn("agent/login", self.branches())

    def test_clean_removes_worktree_without_changes(self):
        wt = self.add_worktree("empty")
        self.run_script("clean")
        self.assertFalse(wt.exists())

    def test_committed_agent_work_counts_as_applied_only_once_present(self):
        wt = self.add_worktree("login")
        self.do_work(wt)
        self.git(wt, "add", "-A")
        self.git(wt, *GIT_IDENTITY, "commit", "-q", "-m", "agent work")
        self.assertIn("NOT applied", self.run_script("list").stdout)
        self.assertEqual(self.run_script("apply", str(wt)).returncode, 0)
        self.run_script("clean")
        self.assertFalse(wt.exists())

    def test_discard_removes_unapplied_worktree(self):
        wt = self.add_worktree("login")
        self.do_work(wt)
        result = self.run_script("discard", str(wt))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(wt.exists())
        self.assertNotIn("agent/login", self.branches())
        self.assertFalse((self.repo / "new.txt").exists())

    def test_discard_rejects_non_agent_path(self):
        wt = self.add_worktree("feature", branch_prefix="user/")
        result = self.run_script("discard", str(wt))
        self.assertEqual(result.returncode, 1)
        self.assertTrue(wt.exists())

    def test_deleted_folder_is_pruned(self):
        wt = self.add_worktree("gone")
        shutil.rmtree(wt)
        self.assertIn("No agent worktrees.", self.run_script("list").stdout)

    def test_works_from_inside_a_worktree(self):
        wt = self.add_worktree("login")
        self.do_work(wt)
        self.assertEqual(self.run_script("apply", str(wt), cwd=wt).returncode, 0)
        self.assertTrue((self.repo / "new.txt").exists())

    def test_outside_a_repo(self):
        outside = self.tmp / "plain"
        outside.mkdir()
        quiet = self.run_script("list", "--quiet", cwd=outside)
        self.assertEqual((quiet.returncode, quiet.stdout), (0, ""))
        self.assertEqual(self.run_script("list", cwd=outside).returncode, 1)

    def test_check_disk_uses_settings_threshold(self):
        (self.tmp / "settings.toml").write_text("min_free_disk_gb = 1000000\n", encoding="utf-8")
        low = self.run_script("check-disk")
        self.assertEqual(low.returncode, 1)
        self.assertIn("Low disk", low.stdout)
        (self.tmp / "settings.toml").write_text("min_free_disk_gb = 0\n", encoding="utf-8")
        self.assertEqual(self.run_script("check-disk").returncode, 0)

    def test_usage_errors(self):
        self.assertEqual(self.run_script().returncode, 2)
        self.assertEqual(self.run_script("bogus").returncode, 2)


if __name__ == "__main__":
    unittest.main()
