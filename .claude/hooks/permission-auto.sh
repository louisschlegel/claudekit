#!/bin/bash
# Hook: PermissionRequest — auto-approve safe patterns
# Approves read-only operations and common dev commands without prompting.

INPUT=$(cat)

python3 - "$INPUT" << 'PYEOF'
import json, sys

raw = sys.argv[1] if len(sys.argv) > 1 else ""
if not raw.strip():
    sys.exit(0)

try:
    event = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(0)

tool_name = event.get("tool_name", "")
tool_input = event.get("tool_input", {})

# Safe patterns to auto-approve
SAFE_BASH = [
    "git status", "git diff", "git log", "git branch",
    "ls ", "cat ", "head ", "tail ", "wc ",
    "python3 -m pytest", "pytest ", "npm test", "npm run test",
    "python3 -m py_compile", "python3 -c ",
    "make validate", "make check", "make test",
    "ruff check", "ruff format", "eslint", "prettier",
    "grep ", "find ", "which ", "echo ",
]

if tool_name == "Bash":
    cmd = tool_input.get("command", "")
    for safe in SAFE_BASH:
        if cmd.strip().startswith(safe):
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "permissionDecision": "allow"
                }
            }))
            sys.exit(0)

# Read operations are always safe
if tool_name in ("Read", "Glob", "Grep"):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "permissionDecision": "allow"
        }
    }))
    sys.exit(0)

# Everything else: let the user decide
sys.exit(0)
PYEOF
exit 0
