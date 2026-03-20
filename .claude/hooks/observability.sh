#!/bin/bash
# Hook: PostToolUse — append tool events to .template/agent-events.jsonl
# Lightweight observability: tracks tool usage without blocking

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")

# Only log Edit, Write, Bash — skip Read to avoid noise
if [[ "$TOOL_NAME" != "Edit" && "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "Bash" && "$TOOL_NAME" != "MultiEdit" ]]; then
  exit 0
fi

python3 - "$TOOL_NAME" "$PROJECT_ROOT" << 'PYEOF' 2>/dev/null
import json, time, sys
from pathlib import Path

tool = sys.argv[1] if len(sys.argv) > 1 else "unknown"
root = sys.argv[2] if len(sys.argv) > 2 else "."

try:
    log_path = Path(root) / ".template" / "agent-events.jsonl"
    log_path.parent.mkdir(exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": "PostToolUse",
        "tool": tool,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
except Exception:
    pass
PYEOF

exit 0
