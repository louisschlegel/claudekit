#!/bin/bash
# Hook: SessionEnd — cleanup, telemetry, learning.md final update
# Fires on: clear, logout, prompt_input_exit
# Distinct from Stop (which fires when Claude finishes a task)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Clean up session tracking files
rm -f "$PROJECT_ROOT/.template/session-files.txt" 2>/dev/null

# Log session end event
python3 - "$PROJECT_ROOT" << 'PYEOF'
import json, sys, os
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
events_file = root / ".template" / "agent-events.jsonl"
events_file.parent.mkdir(parents=True, exist_ok=True)

event = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "event": "SessionEnd",
    "type": "lifecycle"
}

with events_file.open("a") as f:
    f.write(json.dumps(event) + "\n")
PYEOF

exit 0
