#!/bin/bash
# Hook: Elicitation — intercept MCP structured input requests
# Decision control hook: can approve, modify, or decline (exit 2) MCP elicitations
# Currently: log and pass through (exit 0)

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
    "event": "Elicitation",
    "mcp_server_name": data.get("mcp_server_name", "unknown"),
    "action": data.get("action", ""),
    "mode": data.get("mode", ""),
    "elicitation_id": data.get("elicitation_id", ""),
}
with open(log_path, "a") as f:
    f.write(json.dumps(entry) + "\n")
PYEOF

# Exit 0 = allow the elicitation to proceed
# Exit 2 + JSON {"decision":"decline","reason":"..."} = block
exit 0
