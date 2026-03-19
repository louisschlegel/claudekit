#!/bin/bash
# Hook: SubagentStop — log subagent completion for observability

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)

python3 - <<PYEOF 2>/dev/null
import json, time
from pathlib import Path

data = json.loads("""$INPUT""") if """$INPUT""".strip() else {}
log_path = Path("$PROJECT_ROOT/.template/agent-events.jsonl")
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
