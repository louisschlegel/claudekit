#!/bin/bash
# Hook: PostToolUseFailure — log and inject recovery context on tool failures
INPUT=$(cat)
python3 - "$INPUT" << 'PYEOF'
import json, sys, os
from datetime import datetime, timezone
from pathlib import Path

raw = sys.argv[1] if len(sys.argv) > 1 else ""
if not raw.strip(): sys.exit(0)
try:
    event = json.loads(raw)
except json.JSONDecodeError: sys.exit(0)

tool = event.get("tool_name", "")
error = event.get("error", "")
is_interrupt = event.get("is_interrupt", False)

if not error and not is_interrupt: sys.exit(0)

# Log failure event
root = os.environ.get("PROJECT_ROOT", os.getcwd())
events = Path(root) / ".template" / "agent-events.jsonl"
events.parent.mkdir(parents=True, exist_ok=True)
entry = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "event": "PostToolUseFailure",
    "tool": tool,
    "error": str(error)[:200],
    "is_interrupt": is_interrupt
}
with events.open("a") as f:
    f.write(json.dumps(entry) + "\n")

# Inject recovery context for rate limits
if "rate_limit" in str(error).lower():
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUseFailure",
        "additionalContext": "⚠️ Rate limit hit. Wait 30s before retrying. Consider using a cheaper model for this operation."}}))

sys.exit(0)
PYEOF
exit 0
