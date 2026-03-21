#!/bin/bash
# Hook: TeammateIdle — log idle agent and redistribute pending tasks if any

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)

python3 - <<PYEOF 2>/dev/null
import json, time
from pathlib import Path

data = json.loads("""$INPUT""") if """$INPUT""".strip() else {}
log_path = Path("$PROJECT_ROOT/.template/agent-events.jsonl")
log_path.parent.mkdir(exist_ok=True)

agent_id = data.get("agent_id", "unknown")
reason = data.get("reason", "")

entry = {
    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    "event": "TeammateIdle",
    "agent_id": agent_id,
    "reason": reason,
}
with open(log_path, "a") as f:
    f.write(json.dumps(entry) + "\n")

# Check if there are pending tasks to redistribute
queue_path = Path("$PROJECT_ROOT/.template/teammate-queue.json")
if queue_path.exists():
    try:
        queue = json.loads(queue_path.read_text())
        pending = [t for t in queue if t.get("status") == "pending"]
        if pending:
            # Mark first pending task as assigned to this now-idle agent
            for task in queue:
                if task.get("status") == "pending":
                    task["status"] = "assigned"
                    task["assigned_to"] = agent_id
                    task["assigned_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    break
            queue_path.write_text(json.dumps(queue, indent=2))
    except Exception:
        pass
PYEOF

exit 0
