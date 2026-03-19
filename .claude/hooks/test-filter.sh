#!/bin/bash
# Hook: PreToolUse(Bash) — filter test output to show only failures
# Saves 60-90% of context tokens on test runs
INPUT=$(cat)
python3 - "$INPUT" << 'PYEOF'
import json, sys, re

raw = sys.argv[1] if len(sys.argv) > 1 else ""
if not raw.strip(): sys.exit(0)
try:
    event = json.loads(raw)
except json.JSONDecodeError: sys.exit(0)

tool = event.get("tool_name", "")
if tool != "Bash": sys.exit(0)

cmd = event.get("tool_input", {}).get("command", "")

# Only filter known verbose test commands
VERBOSE_TESTS = ["pytest", "npm test", "npm run test", "jest", "vitest", "go test", "cargo test"]
is_test = any(t in cmd for t in VERBOSE_TESTS)
if not is_test: sys.exit(0)

# Don't filter if already has -q or --quiet or output filtering
if any(f in cmd for f in ["-q", "--quiet", "| tail", "| head", "| grep", "--tb=short", "--tb=line"]):
    sys.exit(0)

# Suggest filtered version via updatedInput
filtered = cmd
if "pytest" in cmd and "-v" in cmd:
    filtered = cmd.replace("-v", "-q --tb=short")
elif "pytest" in cmd and "-v" not in cmd and "-q" not in cmd:
    filtered = cmd.rstrip() + " -q --tb=short"

if filtered != cmd:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": {"command": filtered}
        }
    }))

sys.exit(0)
PYEOF
exit 0
