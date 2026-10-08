"""Tests for core/bin/heavy.py. Run: python -m unittest tests.test_heavy -v"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HEAVY = Path(__file__).resolve().parent.parent / "core" / "bin" / "heavy.py"
sys.path.insert(0, str(HEAVY.parent))
import heavy  # noqa: E402

GIT_BASH_CANDIDATES = (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\bin\sh.exe")
START_TIMEOUT = 10
RUN_TIMEOUT = 30
SLEEP_SECONDS = 0.5
LOCKED_SLOT_COMMAND_SECONDS = 60

HEAVY_COMMANDS = [
    "npm test", "pnpm run build", "npx jest --ci", "FOO=1 vitest run",
    "cd app && npm run lint", "ng build --configuration production", "tsc --noEmit",
    "docker build .", "pytest -q", "npm run test:unit", "python -m pytest",
    "yarn jest", "cargo test", "docker compose build",
]
CHEAP_COMMANDS = [
    "grep -r jest src", 'git commit -m "npm test"', "ls", "cat package.json", "ng serve",
    "npm run dev", "npm start", "vitest --watch", "jest --watch", "docker compose up",
    "echo build", "rg tsc", "cat tsconfig.json", "echo 'a && npm test'",
]


def _find_shell():
    for candidate in GIT_BASH_CANDIDATES:
        if os.path.exists(candidate):
            return "bash" if "bash" in candidate else "sh", str(Path(candidate).parent)
    for name in ("bash", "sh"):
        found = shutil.which(name)
        if found:
            return name, str(Path(found).parent)
    return None, None


SHELL, SHELL_DIR = _find_shell()


class IsHeavyTests(unittest.TestCase):
    def test_heavy_commands(self):
        for command in HEAVY_COMMANDS:
            with self.subTest(command=command):
                self.assertTrue(heavy.is_heavy(command))

    def test_cheap_commands(self):
        for command in CHEAP_COMMANDS:
            with self.subTest(command=command):
                self.assertFalse(heavy.is_heavy(command))


@unittest.skipUnless(SHELL, "no POSIX shell available")
class RunTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="heavy-test-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.procs = []
        self.addCleanup(self._kill_all)
        self.logger = Path(self.dir, "interval.py")
        self.logger.write_text(
            # One log file per process: concurrent appends to a shared file can
            # lose lines on Windows, which would make the overlap check flaky.
            "import os, sys, time\n"
            "log, secs = f'{sys.argv[1]}.{os.getpid()}', float(sys.argv[2])\n"
            "open(log, 'a').write(f'start {time.time()}\\n')\n"
            "time.sleep(secs)\n"
            "open(log, 'a').write(f'end {time.time()}\\n')\n"
        )

    def _kill_all(self):
        for proc in self.procs:
            if proc.poll() is None:
                proc.kill()
            proc.wait()

    def _env(self, slots=1, **extra):
        env = {k: v for k, v in os.environ.items() if k != heavy.ENV_HELD}
        env.update({
            "AW_HEAVY_DIR": self.dir, "AW_HEAVY_SLOTS": str(slots),
            "PATH": SHELL_DIR + os.pathsep + env.get("PATH", ""),
        })
        env.update(extra)
        return env

    def _spawn(self, command, slots=1, **extra):
        proc = subprocess.Popen(
            [sys.executable, str(HEAVY), "run", "--shell", SHELL, "--", command],
            env=self._env(slots, **extra), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.procs.append(proc)
        return proc

    def _hold_slot(self):
        sleeper = f'"{sys.executable.replace(chr(92), "/")}" -c "import time; time.sleep({LOCKED_SLOT_COMMAND_SECONDS})"'
        holder = self._spawn(sleeper)
        deadline = time.time() + START_TIMEOUT
        while not Path(self.dir, "slot-0.json").exists():
            self.assertLess(time.time(), deadline, "holder never acquired slot")
            time.sleep(0.05)
        return holder

    def _intervals(self, log):
        starts, ends = [], []
        per_process = Path(log).parent.glob(Path(log).name + ".*")
        for line in (line for p in per_process for line in p.read_text().splitlines()):
            kind, stamp = line.split()
            (starts if kind == "start" else ends).append(float(stamp))
        return sorted(zip(sorted(starts), sorted(ends)))

    def _max_overlap(self, intervals):
        events = sorted([(s, 1) for s, _ in intervals] + [(e, -1) for _, e in intervals],
                        key=lambda ev: (ev[0], ev[1]))
        current = peak = 0
        for _, delta in events:
            current += delta
            peak = max(peak, current)
        return peak

    def _concurrency_peak(self, slots):
        log = Path(self.dir, "log.txt")
        py = sys.executable.replace("\\", "/")
        command = f'"{py}" "{self.logger.as_posix()}" "{log.as_posix()}" {SLEEP_SECONDS}'
        procs = [self._spawn(command, slots=slots) for _ in range(3)]
        for proc in procs:
            proc.communicate(timeout=RUN_TIMEOUT)
            self.assertEqual(proc.returncode, 0)
        intervals = self._intervals(log)
        self.assertEqual(len(intervals), 3)
        return self._max_overlap(intervals)

    def test_single_slot_serializes(self):
        self.assertEqual(self._concurrency_peak(1), 1)

    def test_two_slots_allow_at_most_two(self):
        self.assertLessEqual(self._concurrency_peak(2), 2)

    def test_killed_holder_frees_slot(self):
        holder = self._hold_slot()
        holder.kill()
        holder.wait()
        start = time.time()
        proc = self._spawn("exit 0")
        proc.communicate(timeout=RUN_TIMEOUT)
        self.assertEqual(proc.returncode, 0)
        self.assertLess(time.time() - start, 5)

    def test_max_wait_exits_75(self):
        self._hold_slot()
        proc = self._spawn("exit 0", AW_HEAVY_MAX_WAIT="1")
        _, err = proc.communicate(timeout=RUN_TIMEOUT)
        self.assertEqual(proc.returncode, 75)
        self.assertIn("waiting for a slot", err)
        self.assertIn("run_in_background", err)

    def test_nested_call_skips_queue(self):
        self._hold_slot()
        proc = self._spawn("exit 0", **{heavy.ENV_HELD: "1"})
        proc.communicate(timeout=RUN_TIMEOUT)
        self.assertEqual(proc.returncode, 0)

    def test_exit_code_propagates(self):
        proc = self._spawn("exit 3")
        proc.communicate(timeout=RUN_TIMEOUT)
        self.assertEqual(proc.returncode, 3)

    def test_child_sees_held_flag(self):
        proc = self._spawn('echo "held=$AW_HEAVY_HELD"')
        out, _ = proc.communicate(timeout=RUN_TIMEOUT)
        self.assertIn("held=1", out)

    def test_bash_wrapped_command_keeps_double_quotes(self):
        """End to end: the hook's wrapped command, executed by bash, sees the exact args."""
        wrapped = heavy.wrap_command("Bash", "echo \"a  b\" 'c\"d'")
        bash = shutil.which("bash", path=SHELL_DIR) or SHELL
        proc = subprocess.run([bash, "-c", wrapped], env=self._env(),
                              capture_output=True, text=True, timeout=RUN_TIMEOUT)
        self.assertEqual(proc.stdout.strip(), 'a  b c"d')

    @unittest.skipUnless(shutil.which("powershell") or shutil.which("pwsh"), "no PowerShell")
    def test_powershell_wrapped_command_keeps_double_quotes(self):
        """End to end through PowerShell 5.1/pwsh: embedded double quotes survive."""
        wrapped = heavy.wrap_command("PowerShell", "Write-Output \"a  b\" 'c\"d'")
        exe = shutil.which("powershell") or shutil.which("pwsh")
        proc = subprocess.run([exe, "-NoProfile", "-Command", wrapped], env=self._env(),
                              capture_output=True, text=True, timeout=RUN_TIMEOUT)
        self.assertEqual(proc.stdout.splitlines(), ["a  b", 'c"d'])
        self.assertEqual(proc.returncode, 0)

    def test_status_shows_busy_and_free(self):
        proc = subprocess.run([sys.executable, str(HEAVY), "status"], env=self._env(),
                              capture_output=True, text=True, timeout=RUN_TIMEOUT)
        self.assertIn("slot-0: free", proc.stdout)
        self._hold_slot()
        proc = subprocess.run([sys.executable, str(HEAVY), "status"], env=self._env(),
                              capture_output=True, text=True, timeout=RUN_TIMEOUT)
        self.assertIn("slot-0: busy", proc.stdout)
        self.assertIn("pid=", proc.stdout)


class HookTests(unittest.TestCase):
    def _hook(self, stdin):
        return subprocess.run([sys.executable, str(HEAVY), "hook"], input=stdin,
                              capture_output=True, text=True, timeout=RUN_TIMEOUT)

    def _payload(self, command, tool="Bash", **tool_input):
        return json.dumps({"tool_name": tool, "tool_input": {"command": command, **tool_input}})

    def test_heavy_bash_is_wrapped(self):
        result = self._hook(self._payload("npm test", timeout=5000))
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertNotIn("permissionDecision", out)
        self.assertEqual(out["updatedInput"]["timeout"], 600000)
        wrapped = out["updatedInput"]["command"]
        self.assertIn("heavy.py", wrapped)
        self.assertIn("--shell bash -- 'npm test'", wrapped)
        self.assertNotIn("\\", wrapped)

    def test_bash_quotes_are_escaped(self):
        wrapped = json.loads(self._hook(self._payload("npm test -- -t 'a b'")).stdout)[
            "hookSpecificOutput"]["updatedInput"]["command"]
        self.assertIn("--shell bash -- 'npm test -- -t '\"'\"'a b'\"'\"''", wrapped)

    def test_powershell_form(self):
        result = self._hook(self._payload("npm run build -- --name 'x'", tool="PowerShell"))
        wrapped = json.loads(result.stdout)["hookSpecificOutput"]["updatedInput"]["command"]
        self.assertTrue(wrapped.startswith("$env:AW_HEAVY_CMD = 'npm run build -- --name ''x'''; & \""))
        self.assertTrue(wrapped.endswith("--shell powershell --from-env"))

    def test_wrap_cli_for_plugins(self):
        def wrap(command):
            return subprocess.run([sys.executable, str(HEAVY), "wrap", "bash"], input=command,
                                  capture_output=True, text=True, timeout=RUN_TIMEOUT).stdout
        self.assertIn("--shell bash -- 'npm test'", wrap("npm test"))
        self.assertEqual(wrap("git status"), "")
        self.assertEqual(wrap(wrap("npm test")), "")

    def test_non_heavy_is_silent(self):
        result = self._hook(self._payload("ls -la"))
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_already_wrapped_is_silent(self):
        result = self._hook(self._payload('python "/x/heavy.py" run --shell bash -- \'npm test\''))
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_background_has_no_timeout(self):
        result = self._hook(self._payload("npm test", run_in_background=True))
        updated = json.loads(result.stdout)["hookSpecificOutput"]["updatedInput"]
        self.assertNotIn("timeout", updated)

    def test_garbage_stdin_is_silent(self):
        for stdin in ("not json", "", "[]", '{"tool_name": "Bash"}', '{"tool_name":"Bash","tool_input":{"command":5}}'):
            with self.subTest(stdin=stdin):
                result = self._hook(stdin)
                self.assertEqual((result.returncode, result.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
