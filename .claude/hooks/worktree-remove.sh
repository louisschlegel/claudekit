#!/bin/bash
# Hook: WorktreeRemove — log worktree removal and clean up temp files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)

python3 - <<PYEOF 2>/dev/null
import json, time, shutil
from pathlib import Path

data = json.loads("""$INPUT""") if """$INPUT""".strip() else {}
worktree_path = data.get("worktree_path", "")

log_path = Path("$PROJECT_ROOT/.template/agent-events.jsonl")
log_path.parent.mkdir(exist_ok=True)

entry = {
    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    "event": "WorktreeRemove",
    "worktree_path": worktree_path,
}
with open(log_path, "a") as f:
    f.write(json.dumps(entry) + "\n")

# Clean up any temp files left in the worktree's .template/ dir
if worktree_path:
    tmp_dir = Path(worktree_path) / ".template"
    if tmp_dir.exists() and tmp_dir.is_dir():
        for tmp_file in tmp_dir.glob("*.tmp"):
            try:
                tmp_file.unlink()
            except Exception:
                pass
PYEOF

exit 0
