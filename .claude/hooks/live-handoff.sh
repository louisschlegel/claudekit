#!/bin/bash
# Hook: PostToolUse — Live Handoff
# Tracks file modifications for automatic session state preservation.
# Appends modified file paths to .template/session-files.txt

INPUT=$(cat)

python3 - "$INPUT" << 'PYEOF'
import json, sys, os
from pathlib import Path
from datetime import datetime

raw = sys.argv[1] if len(sys.argv) > 1 else ""
if not raw.strip():
    sys.exit(0)

try:
    event = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(0)

tool_name = event.get("tool_name", "")
if tool_name not in ("Edit", "Write", "MultiEdit"):
    sys.exit(0)

tool_input = event.get("tool_input", {})
file_path = tool_input.get("file_path", "")
if not file_path:
    sys.exit(0)

# Track modified files for handoff
root = os.environ.get("PROJECT_ROOT", os.getcwd())
tracker = Path(root) / ".template" / "session-files.txt"
tracker.parent.mkdir(parents=True, exist_ok=True)

# Append if not already tracked
existing = set()
if tracker.exists():
    existing = set(tracker.read_text().strip().splitlines())

rel_path = file_path
try:
    rel_path = str(Path(file_path).relative_to(root))
except ValueError:
    pass

if rel_path not in existing:
    with tracker.open("a") as f:
        f.write(f"{rel_path}\n")

sys.exit(0)
PYEOF
exit 0
