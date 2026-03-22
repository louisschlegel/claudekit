#!/bin/bash
# Hook: PostToolUse — Context Monitor
# Tracks effective context usage and warns when approaching limits.
# Non-blocking (informational only).

INPUT=$(cat)

python3 - "$INPUT" << 'PYEOF' 2>/dev/null
import json, sys, os

raw = sys.argv[1] if len(sys.argv) > 1 else ""
if not raw.strip():
    sys.exit(0)

try:
    event = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(0)

# Check if we have context usage info in the event
# Claude Code provides tool_response with usage metadata
tool_name = event.get("tool_name", "")
session_tokens = event.get("session_tokens", 0)
max_tokens = event.get("max_context_tokens", 0)

# If no token info available, try reading from usage file
if not session_tokens:
    try:
        root = os.environ.get("PROJECT_ROOT", os.getcwd())
        usage_file = os.path.join(root, ".template", "usage.jsonl")
        if os.path.exists(usage_file):
            with open(usage_file) as f:
                lines = f.readlines()
            if lines:
                last = json.loads(lines[-1])
                session_tokens = last.get("session_tokens", 0)
                max_tokens = last.get("max_context_tokens", 200000)
    except:
        pass

if not session_tokens or not max_tokens:
    sys.exit(0)

pct = (session_tokens / max_tokens) * 100

# Rescale to effective range (compaction happens at ~83.5% raw)
# Map 0-83.5% raw to 0-100% effective
effective_pct = min(100, (pct / 83.5) * 100)

if effective_pct >= 90:
    msg = f"⚠️  Contexte à {effective_pct:.0f}% — compaction imminente. Utilisez /compact [focus] maintenant."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))
elif effective_pct >= 75:
    msg = f"📊 Contexte à {effective_pct:.0f}% — pensez à /compact ou /clear entre les tâches."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))

sys.exit(0)
PYEOF
exit 0
