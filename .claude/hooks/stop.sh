#!/bin/bash
# Hook: Stop — Auto-learning observation + session summary + OS notification
# Auto-portable via BASH_SOURCE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

PROJECT_NAME="claudekit"

# Logger une observation de session pour le self-improve engine (format JSON)
if command -v python3 &>/dev/null && [ -f "$PROJECT_ROOT/scripts/self-improve.py" ]; then
  python3 "$PROJECT_ROOT/scripts/self-improve.py" --log \
    '{"type": "user_validation", "detail": "session completed, claudekit"}' \
    2>/dev/null &
fi

# Check if any source files were modified this session
CHANGED=$(git -C "$PROJECT_ROOT" diff --name-only HEAD 2>/dev/null | grep -v "^$" | wc -l | tr -d ' ')
CHANGED_FILES=$(git -C "$PROJECT_ROOT" diff --name-only HEAD 2>/dev/null | head -10 || echo "")
RECENT_COMMITS=$(git -C "$PROJECT_ROOT" log --oneline -3 2>/dev/null || echo "")

# Générer un résumé structuré de session
mkdir -p "$PROJECT_ROOT/.template"
SESSION_FILE="$PROJECT_ROOT/.template/session-$(date +%Y%m%d-%H%M%S).md"

python3 -c "
import json, sys
files = sys.argv[1]
commits = sys.argv[2]
ts = sys.argv[3]
path = sys.argv[4]

content = f'# Session {ts}\n\n'
if commits.strip():
    content += f'## Commits\n{commits}\n\n'
if files.strip():
    content += f'## Fichiers modifiés\n{files}\n\n'

import pathlib
pathlib.Path(path).write_text(content)
" "$CHANGED_FILES" "$RECENT_COMMITS" "$(date '+%Y-%m-%d %H:%M')" "$SESSION_FILE" 2>/dev/null

# Log usage session
if command -v python3 &>/dev/null; then
  python3 -c "
import json, time
from pathlib import Path
log_path = Path('$PROJECT_ROOT/.template/usage.jsonl')
log_path.parent.mkdir(exist_ok=True)
entry = {
    'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
    'changed_files': $CHANGED
}
with open(log_path, 'a') as f:
    f.write(json.dumps(entry) + '\n')
" 2>/dev/null
fi

# Auto-dedup learning.md (silent, runs async)
if [ -f "$PROJECT_ROOT/scripts/auto-learn.py" ] && [ -f "$PROJECT_ROOT/learning.md" ]; then
  python3 "$PROJECT_ROOT/scripts/auto-learn.py" --deduplicate 2>/dev/null &
fi

# Notification OS (macOS / Linux)
if [ "$CHANGED" -gt "0" ] 2>/dev/null; then
  if command -v osascript &>/dev/null; then
    osascript -e "display notification \"$CHANGED fichier(s) modifié(s) — session terminée\" with title \"claudekit — $PROJECT_NAME\"" 2>/dev/null &
  elif command -v notify-send &>/dev/null; then
    notify-send "claudekit — $PROJECT_NAME" "$CHANGED fichier(s) modifié(s) — session terminée" 2>/dev/null &
  fi
fi

# Audio notification
if [ "$CHANGED" -gt "0" ] 2>/dev/null; then
  if command -v afplay &>/dev/null; then
    afplay /System/Library/Sounds/Glass.aiff 2>/dev/null &
  elif command -v paplay &>/dev/null; then
    paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null &
  fi
fi

if [ "$CHANGED" -gt 0 ]; then
    python3 -c "
import json
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'Stop',
        'additionalContext': 'Session ended with $CHANGED file(s) modified. Consider updating learning.md if patterns or decisions worth remembering were discovered.'
    }
}))
"
fi

exit 0
