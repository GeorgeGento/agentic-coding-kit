"""Tests for core/bin/heavy_parsers.py. Run: python -m unittest tests.test_heavy_parsers -v

Fixtures are synthetic samples in each tool's normal output format.
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core" / "bin"))
import heavy_parsers as hp  # noqa: E402

LOG = Path("/logs/proj/1.log")

JEST_FAIL = """\
 FAIL  src/user.service.spec.ts
  UserService
    ✓ returns user (3 ms)
    ✕ returns 401 when token missing (5 ms)

  ● UserService › returns 401 when token missing

    expect(received).toBe(expected) // Object.is equality

    Expected: 401
    Received: 200

      46 |     const res = await service.check(undefined);
    > 48 |     expect(res.status).toBe(401);
         |                        ^
      49 |   });

      at Object.<anonymous> (src/user.service.spec.ts:48:24)
      at processTicksAndRejections (node:internal/process/task_queues:95:5)
      at node_modules/jest-circus/build/utils.js:298:28

Test Suites: 1 failed, 4 passed, 5 total
Tests:       1 failed, 211 passed, 212 total
Snapshots:   0 total
Time:        4.2 s
"""

JEST_PASS = """\
 PASS  src/a.spec.ts
Test Suites: 5 passed, 5 total
Tests:       212 passed, 212 total
"""

VITEST_FAIL = """\
 ❯ src/calc.test.ts (2 tests | 1 failed) 4ms
   × calc > adds 3ms

⎯⎯⎯⎯⎯⎯⎯ Failed Tests 1 ⎯⎯⎯⎯⎯⎯⎯

 FAIL  src/calc.test.ts > calc > adds
AssertionError: expected 4 to be 3 // Object.is equality

- Expected
+ Received

- 3
+ 4

 ❯ src/calc.test.ts:5:17
      3|   it('adds', () => {
      4|     expect(add(2, 2))
      5|       .toBe(3)
       |        ^

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/1]⎯

 Test Files  1 failed | 3 passed (4)
      Tests  1 failed | 20 passed (21)
"""

PYTEST_FAIL = """\
============================= test session starts =============================
collected 4 items

tests/test_calc.py .F..                                                  [100%]

================================== FAILURES ===================================
__________________________________ test_add ___________________________________

    def test_add():
>       assert add(2, 2) == 3
E       assert 4 == 3
E        +  where 4 = add(2, 2)

tests/test_calc.py:7: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_calc.py::test_add - assert 4 == 3
========================= 1 failed, 3 passed in 0.05s =========================
"""

CARGO_COMPILE = """\
   Compiling demo v0.1.0 (/work/demo)
error[E0308]: mismatched types
 --> src/main.rs:4:18
  |
4 |     let x: u32 = "a";
  |            ---   ^^^ expected `u32`, found `&str`
  |
warning: unused variable: `y`
 --> src/main.rs:5:9

For more information about this error, try `rustc --explain E0308`.
error: could not compile `demo` (bin "demo") due to 1 previous error; 1 warning emitted
"""

CARGO_TEST = """\
running 2 tests
test tests::ok ... ok
test tests::adds ... FAILED

failures:

---- tests::adds stdout ----

thread 'tests::adds' panicked at src/lib.rs:10:9:
assertion `left == right` failed
  left: 4
 right: 3
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace


failures:
    tests::adds

test result: FAILED. 1 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
"""

TSC_FAIL = """\
src/app/user.ts(12,5): error TS2322: Type 'string' is not assignable to type 'number'.
src/app/api.ts:3:10 - error TS2305: Module '"./x"' has no exported member 'Y'.

Found 2 errors in 2 files.
"""

NG_FAIL = """\
✘ [ERROR] TS2339: Property 'nme' does not exist on type 'User'. [plugin angular-compiler]

    src/app/user/user.component.html:3:12:
      3 │   <p>{{ user.nme }}</p>
        ╵             ~~~
"""

ESLINT_FAIL = """\

/work/app/src/user.ts
   3:7   error    'unused' is assigned a value but never used  @typescript-eslint/no-unused-vars
  10:1   warning  Unexpected console statement                 no-console

✖ 2 problems (1 error, 1 warning)
"""

PLAYWRIGHT_FAIL = """\
Running 6 tests using 2 workers

  1) [chromium] › tests/login.spec.ts:12:5 › login › shows error on bad password ───

    Error: expect(locator).toBeVisible() failed

    Locator: getByRole('alert')
    Expected: visible
    Received: <element(s) not found>

      14 |   await page.click('text=Sign in');
    > 15 |   await expect(page.getByRole('alert')).toBeVisible();
         |                                         ^
      16 | });

        at /work/tests/login.spec.ts:15:41

    attachment #1: trace (application/zip) ────────

  1 failed
    [chromium] › tests/login.spec.ts:12:5 › login › shows error on bad password
  5 passed (8.1s)
"""


def summary(text, code=1, command="npm test"):
    return hp.summarize(command, text, code, 12.3, LOG)


class HeaderTests(unittest.TestCase):
    def test_success_is_one_line_with_counts_and_log(self):
        out = summary(JEST_PASS, code=0)
        self.assertEqual(out, "heavy: npm test | exit 0 | 12s | 212 passed | log /logs/proj/1.log")

    def test_success_without_known_tool_is_still_one_line(self):
        self.assertEqual(len(summary("built in 3s\n", code=0).splitlines()), 1)

    def test_exit_code_decides_failure_even_if_counts_look_green(self):
        out = summary(JEST_PASS, code=2)
        self.assertIn("exit 2", out)
        self.assertGreater(len(out.splitlines()), 1)  # fallback body, never a bare header

    def test_long_command_is_truncated(self):
        out = summary("", code=0, command="x" * 200)
        self.assertIn("x" * 77 + "...", out)
        self.assertNotIn("x" * 81, out)

    def test_ansi_and_carriage_returns_are_stripped(self):
        lines = hp.clean_lines("\x1b[31mred\x1b[0m\nprogress 10%\rprogress 100%\n")
        self.assertEqual(lines[:2], ["red", "progress 100%"])


class ParserTests(unittest.TestCase):
    def test_jest_failure_keeps_message_and_location_drops_noise(self):
        out = summary(JEST_FAIL)
        self.assertIn("1 failed, 211 passed", out)
        self.assertIn("1. UserService › returns 401 when token missing", out)
        self.assertIn("Received: 200", out)
        self.assertIn("src/user.service.spec.ts:48:24", out)
        self.assertNotIn("node_modules", out)
        self.assertNotIn("node:internal", out)
        self.assertNotIn("> 48 |", out)

    def test_vitest_failure(self):
        out = summary(VITEST_FAIL)
        self.assertIn("1 failed, 20 passed", out)
        self.assertIn("1. src/calc.test.ts > calc > adds", out)
        self.assertIn("AssertionError: expected 4 to be 3", out)
        self.assertIn("src/calc.test.ts:5:17", out)

    def test_pytest_failure_uses_sections(self):
        out = summary(PYTEST_FAIL)
        self.assertIn("1 failed, 3 passed", out)
        self.assertIn("1. test_add", out)
        self.assertIn("assert 4 == 3", out)
        self.assertIn("tests/test_calc.py:7: AssertionError", out)

    def test_pytest_short_summary_only(self):
        out = summary("FAILED tests/t.py::test_x - KeyError: 'a'\n=== 1 failed in 0.01s ===\n")
        self.assertIn("1. tests/t.py::test_x - KeyError: 'a'", out)

    def test_cargo_compile_error_has_location_and_skips_summary_errors(self):
        out = summary(CARGO_COMPILE, command="cargo build")
        self.assertIn("1 compile error(s)", out)
        self.assertIn("1. src/main.rs:4:18 error[E0308]: mismatched types", out)
        self.assertNotIn("2. ", out)  # warnings and "could not compile" aren't items

    def test_cargo_test_panic(self):
        out = summary(CARGO_TEST, command="cargo test")
        self.assertIn("1 passed; 1 failed", out)
        self.assertIn("1. tests::adds", out)
        self.assertIn("panicked at src/lib.rs:10:9", out)
        self.assertNotIn("RUST_BACKTRACE", out)

    def test_tsc_both_formats(self):
        out = summary(TSC_FAIL, command="tsc --noEmit")
        self.assertIn("2 errors", out)
        self.assertIn("1. src/app/user.ts:12:5 TS2322: Type 'string'", out)
        self.assertIn("2. src/app/api.ts:3:10 TS2305:", out)

    def test_angular_esbuild_error_gets_location(self):
        out = summary(NG_FAIL, command="ng build")
        self.assertIn("1. src/app/user/user.component.html:3:12 TS2339: Property 'nme'", out)
        self.assertNotIn("plugin angular-compiler", out)

    def test_eslint_errors_only_as_items(self):
        out = summary(ESLINT_FAIL, command="npm run lint")
        self.assertIn("2 problems (1 error, 1 warning)", out)
        self.assertIn("1. /work/app/src/user.ts:3:7 @typescript-eslint/no-unused-vars:", out)
        self.assertNotIn("no-console", out)

    def test_playwright_failure(self):
        out = summary(PLAYWRIGHT_FAIL, command="npx playwright test")
        self.assertIn("1 failed, 5 passed", out)
        self.assertIn("1. [chromium] › tests/login.spec.ts:12:5 › login", out)
        self.assertIn("Error: expect(locator).toBeVisible() failed", out)
        self.assertIn("/work/tests/login.spec.ts:15:41", out)
        self.assertNotIn("attachment", out)


class FallbackTests(unittest.TestCase):
    def test_unknown_tool_shows_error_lines_and_tail(self):
        text = "".join(f"line {i}\n" for i in range(100)) + "Fatal Error: disk full\n"
        out = summary(text)
        self.assertIn("error-like lines:", out)
        self.assertIn("Fatal Error: disk full", out)
        self.assertIn("line 99", out)
        self.assertNotIn("line 5\n", out)

    def test_crash_with_no_output_is_not_empty(self):
        out = summary("", code=139)
        self.assertIn("exit 139", out)
        self.assertGreater(len(out.splitlines()), 1)

    def test_parser_exception_falls_back_with_note(self):
        with mock.patch.object(hp, "parse", side_effect=ValueError("boom")):
            out = summary(JEST_FAIL)
        self.assertIn("[heavy] parser error (ValueError)", out)
        self.assertIn("Received: 200", out)

    def test_many_failures_are_capped(self):
        text = "".join(f"FAILED tests/t.py::test_{i} - boom {i}\n" for i in range(30))
        out = summary(text + "=== 30 failed in 1s ===\n")
        self.assertIn(f"(showing {hp.MAX_ITEMS} of 30 failures; see log)", out)
        self.assertLessEqual(len(out.splitlines()), hp.MAX_LINES)

    def test_identical_failures_are_collapsed(self):
        text = "FAILED tests/t.py::test_x - boom\n" * 3 + "=== 3 failed in 1s ===\n"
        out = summary(text)
        self.assertIn("1. tests/t.py::test_x - boom  (x3)", out)
        self.assertNotIn("2. ", out)

    def test_total_lines_are_capped(self):
        text = "".join(f"  ● suite › t{i}\n\n" + "    detail\n" * 10 for i in range(10))
        out = summary(text + "Tests:       10 failed, 10 total\n")
        self.assertLessEqual(len(out.splitlines()), hp.MAX_LINES)


if __name__ == "__main__":
    unittest.main()
