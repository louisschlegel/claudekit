#!/bin/bash
# Hook: ElicitationResult — log the result of a completed MCP elicitation

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
    "event": "ElicitationResult",
    "mcp_server_name": data.get("mcp_server_name", "unknown"),
    "action": data.get("action", ""),
    "elicitation_id": data.get("elicitation_id", ""),
    "has_content": bool(data.get("content")),
}
with open(log_path, "a") as f:
    f.write(json.dumps(entry) + "\n")
PYEOF

exit 0
