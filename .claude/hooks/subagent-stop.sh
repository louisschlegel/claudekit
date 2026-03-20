#!/bin/bash
# Hook: SubagentStop — log subagent completion for observability

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)

python3 - "$INPUT" "$PROJECT_ROOT" << 'PYEOF' 2>/dev/null
import json, sys, time
from pathlib import Path

raw = sys.argv[1] if len(sys.argv) > 1 else ""
root = sys.argv[2] if len(sys.argv) > 2 else "."

try:
    data = json.loads(raw) if raw.strip() else {}
except json.JSONDecodeError:
    data = {}

log_path = Path(root) / ".template" / "agent-events.jsonl"
log_path.parent.mkdir(exist_ok=True)

entry = {
    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    "event": "SubagentStop",
    "agent_id": data.get("agent_id", "unknown"),
    "duration_ms": data.get("duration_ms"),
}
with open(log_path, "a") as f:
    f.write(json.dumps(entry) + "\n")
PYEOF

exit 0
