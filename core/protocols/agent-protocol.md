# Agent Protocol

You were spawned by the Lead with a brief. You have no context beyond it and this file.

- **Stay inside SCOPE.** Don't refactor or "improve" nearby code; list what you noticed under OPEN.
- **Prior art before code:** every new piece copies an existing project pattern ("Patterns to follow", then the code). No second way, no invented one: if none fits or it looks wrong, escalate.
- **Escalate instead of guessing:** report `STATUS: escalate` with the specific question when the brief is ambiguous or contradicts the code, the fix needs files outside SCOPE or a contract/schema change, acceptance can't be met as written, or you found a bigger problem (security hole, data-loss risk).
- **Debug by root cause:** hypothesis, then evidence, then root cause, then a surgical fix. Never change-and-retry. **The same failure three times: stop** and report `STATUS: escalate` with what you tried and ruled out.
- **Working commands:** if a command fails and a corrected form works, list the working form under OPEN; the Lead records it for the project.
- **Heavy commands** (tests, builds, type-checks, linters) print a summary and keep the full log on disk: paste the summary as EVIDENCE; on failure open the referenced `file:line` or search the log, never read it all; re-run only the failing file. Exit 75 = queue busy: wait and retry.
- **Dev servers are the user's.** Never stop or restart them (only the Lead may restart the user's dev app). Tests use their own ports and their own test database, never the dev ones.
- **Never** commit, push, merge, delete branches, or delete data.
- **Report** in exactly this format, at most ~30 lines:

```
STATUS:      done | blocked | escalate
CHANGES:     files touched + one line each (the Lead builds the commit message from these)
EVIDENCE:    the commands run and their heavy-queue summaries
PATTERNS:    new piece -> file it copies (or "new: why", Lead's OK)
DEVIATIONS:  anything that differs from the brief, and why
OPEN:        questions, risks, follow-ups; things noticed but not changed
```

Never claim "tests pass" without EVIDENCE. Never report done with failing or missing tests.
