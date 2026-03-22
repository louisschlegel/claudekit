#!/bin/bash
# Hook: WorktreeCreate — log worktree creation event
# Fires when Claude creates a new git worktree (--worktree flag)

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
    "event": "WorktreeCreate",
    "worktree_path": data.get("worktree_path", "unknown"),
    "branch": data.get("branch", "unknown"),
}
with open(log_path, "a") as f:
    f.write(json.dumps(entry) + "\n")
PYEOF

exit 0
