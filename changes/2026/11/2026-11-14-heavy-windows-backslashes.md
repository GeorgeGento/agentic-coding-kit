---
packages: [core]
type: fix
---

# Heavy queue: Windows bash commands keep their backslashes

- `bin/heavy.py`: on Windows, the queued command reaches Git Bash through an environment variable (`AW_HEAVY_BASH_CMD`, evaluated and unset by the shell) instead of the `bash -c` argument. Python's `list2cmdline` quoting and MSYS argv parsing disagree on backslashes, so `C:\\Users` arrived as `C:\Users` and Python one-liners, regexes and Windows paths broke.
- Tests: regression test for backslashes and quotes reaching the shell unchanged; the killed-waiter test stops the orphaned worker on Windows (no supervisor there) before draining the holder's pipes.

## Changes to existing behaviour

None intended: commands run as before, now byte-for-byte as written.
