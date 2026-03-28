---
name: User runs tools themselves
description: Do not run bash/shell commands — the user executes all terminal commands themselves
type: feedback
---

Never run Bash tool commands (uv, pytest, git, etc.). The user runs all terminal commands themselves.

**Why:** Claude doesn't pick up the nix environment, so shell commands won't work correctly anyway.

**How to apply:** Make code changes only. When a shell command is needed, tell the user what to run rather than running it.
